"""Pure Python HTTP/HTTPS-to-SOCKS5 Proxy Server.

Follows Single Responsibility Principle (SRP) by tunneling incoming HTTP/HTTPS
proxy requests into Tor's local SOCKS5 proxy (port 9050) with zero external dependencies.
"""

import os
from pathlib import Path
import select
import socket
import socketserver
import struct
import sys
import threading
import time
from typing import Optional, Tuple

from torpro.core.constants import (
    HTTP_HOST,
    HTTP_LOG_FILE,
    HTTP_PID_FILE,
    HTTP_PORT,
    HTTP_PROXY_TIMEOUT_SECONDS,
    LOGS_DIR,
    SOCKS5_HOST,
    SOCKS5_PORT,
)
from torpro.core.exceptions import ProxyError
from torpro.core.logger import Logger


class Socks5Client:
    """Helper to establish SOCKS5 connections with remote DNS resolution (no DNS leak)."""

    @staticmethod
    def connect(
        target_host: str,
        target_port: int,
        socks_host: str = SOCKS5_HOST,
        socks_port: int = SOCKS5_PORT,
        timeout: int = HTTP_PROXY_TIMEOUT_SECONDS,
    ) -> socket.socket:
        """Establish a SOCKS5 tunnel to target_host:target_port via Tor."""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((socks_host, socks_port))

        # 1. Greeting / Auth Negotiation (Method 0x00 = No Auth)
        sock.sendall(b"\x05\x01\x00")
        resp = sock.recv(2)
        if len(resp) < 2 or resp[0] != 0x05 or resp[1] != 0x00:
            sock.close()
            raise ProxyError("SOCKS5 authentication negotiation failed.")

        # 2. Connection Request (CMD 0x01 = CONNECT, ATYP 0x03 = Domain Name)
        host_bytes = target_host.encode("utf-8")
        req = (
            b"\x05\x01\x00\x03"
            + struct.pack("!B", len(host_bytes))
            + host_bytes
            + struct.pack("!H", target_port)
        )
        sock.sendall(req)

        # 3. Connection Response
        resp = sock.recv(4)
        if len(resp) < 4 or resp[0] != 0x05 or resp[1] != 0x00:
            err_code = resp[1] if len(resp) >= 2 else "Unknown"
            sock.close()
            raise ProxyError(f"SOCKS5 connection failed with code {err_code}")

        # Consume remaining bound address
        atyp = resp[3]
        if atyp == 0x01:  # IPv4
            sock.recv(4 + 2)
        elif atyp == 0x03:  # Domain
            dlen = sock.recv(1)[0]
            sock.recv(dlen + 2)
        elif atyp == 0x04:  # IPv6
            sock.recv(16 + 2)

        return sock


class HttpProxyHandler(socketserver.BaseRequestHandler):
    """Handles HTTP and HTTPS CONNECT requests and tunnels them through SOCKS5."""

    def handle(self) -> None:
        client_sock = self.request
        client_sock.settimeout(HTTP_PROXY_TIMEOUT_SECONDS)

        try:
            raw_request = b""
            while b"\r\n\r\n" not in raw_request and b"\n\n" not in raw_request:
                chunk = client_sock.recv(4096)
                if not chunk:
                    return
                raw_request += chunk

            first_line = raw_request.splitlines()[0].decode("utf-8", errors="ignore")
            parts = first_line.split()
            if len(parts) < 2:
                return

            method, target = parts[0].upper(), parts[1]

            if method == "CONNECT":
                # HTTPS Tunneling: host:port
                if ":" in target:
                    host, port_str = target.split(":", 1)
                    port = int(port_str)
                else:
                    host = target
                    port = 443

                try:
                    socks_sock = Socks5Client.connect(host, port)
                except Exception as err:
                    client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    return

                client_sock.sendall(b"HTTP/1.1 200 Connection Established\r\n\r\n")
                self._bi_directional_forward(client_sock, socks_sock)

            else:
                # Plain HTTP Proxying
                # parse http://host[:port]/path
                if target.startswith("http://"):
                    target_no_schema = target[7:]
                else:
                    target_no_schema = target

                path_slash = target_no_schema.find("/")
                host_port = target_no_schema[:path_slash] if path_slash != -1 else target_no_schema

                if ":" in host_port:
                    host, port_str = host_port.split(":", 1)
                    port = int(port_str)
                else:
                    host = host_port
                    port = 80

                try:
                    socks_sock = Socks5Client.connect(host, port)
                except Exception:
                    client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
                    return

                socks_sock.sendall(raw_request)
                self._bi_directional_forward(client_sock, socks_sock)

        except (socket.timeout, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as err:
            pass

    @staticmethod
    def _bi_directional_forward(sock_a: socket.socket, sock_b: socket.socket) -> None:
        """Stream bytes bi-directionally between two sockets using select."""
        sockets = [sock_a, sock_b]
        while True:
            rlist, _, xlist = select.select(sockets, [], sockets, 20)
            if xlist:
                break
            if not rlist:
                break

            for s in rlist:
                other = sock_b if s is sock_a else sock_a
                try:
                    data = s.recv(16384)
                    if not data:
                        return
                    other.sendall(data)
                except Exception:
                    return


class ThreadedHttpProxyServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP Server that allows immediate port reuse."""
    allow_reuse_address = True
    daemon_threads = True


class HttpBridgeService:
    """Manages lifecycle of the HTTP-to-SOCKS5 Bridge process."""

    @staticmethod
    def start_foreground(host: str = HTTP_HOST, port: int = HTTP_PORT) -> None:
        """Start proxy server in the foreground."""
        server = ThreadedHttpProxyServer((host, port), HttpProxyHandler)
        Logger.info(f"HTTP-to-SOCKS5 Bridge listening on http://{host}:{port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            server.shutdown()

    @classmethod
    def start_background(cls, host: str = HTTP_HOST, port: int = HTTP_PORT) -> int:
        """Fork or launch proxy server as a daemon process."""
        if cls.is_running():
            pid = cls.get_pid()
            Logger.info(f"HTTP Bridge is already running (PID: {pid})")
            return pid or 0

        LOGS_DIR.mkdir(parents=True, exist_ok=True)

        # Run as detached child process
        import subprocess

        cmd = [
            sys.executable,
            "-c",
            f"from torpro.proxy.http_bridge import HttpBridgeService; "
            f"HttpBridgeService.start_foreground('{host}', {port})",
        ]

        with open(HTTP_LOG_FILE, "a", encoding="utf-8") as log_file:
            proc = subprocess.Popen(
                cmd,
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )

        HTTP_PID_FILE.write_text(str(proc.pid), encoding="utf-8")
        time.sleep(0.5)
        Logger.success(f"HTTP-to-SOCKS5 Proxy started on port {port} (PID: {proc.pid})")
        return proc.pid

    @classmethod
    def stop(cls) -> bool:
        """Stop the running HTTP Bridge process."""
        pid = cls.get_pid()
        if not pid:
            return False

        try:
            os.kill(pid, 15)  # SIGTERM
            time.sleep(0.3)
            if cls.is_running():
                os.kill(pid, 9)  # SIGKILL
        except ProcessLookupError:
            pass
        except Exception as err:
            Logger.error(f"Failed to kill HTTP bridge PID {pid}", str(err))

        if HTTP_PID_FILE.exists():
            HTTP_PID_FILE.unlink(missing_ok=True)
        Logger.info("HTTP Bridge stopped.")
        return True

    @classmethod
    def get_pid(cls) -> Optional[int]:
        """Read active PID from pid file."""
        if not HTTP_PID_FILE.exists():
            return None
        try:
            pid = int(HTTP_PID_FILE.read_text(encoding="utf-8").strip())
            return pid
        except ValueError:
            return None

    @classmethod
    def is_running(cls) -> bool:
        """Check if HTTP Bridge process is currently alive."""
        pid = cls.get_pid()
        if not pid:
            return False
        try:
            os.kill(pid, 0)
            return True
        except (ProcessLookupError, PermissionError):
            if HTTP_PID_FILE.exists():
                HTTP_PID_FILE.unlink(missing_ok=True)
            return False
