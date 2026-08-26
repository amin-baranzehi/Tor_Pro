#!/usr/bin/env python3
"""Diagnostic script for testing Tor circumvention transports in Iran.

Tests Snowflake brokers, Domain Fronting endpoints, STUN WebRTC servers,
and Pluggable Transports across Iranian ISPs.
"""

import http.client
import socket
import ssl
import sys
import time
from typing import Dict, List, Tuple

from torpro import __version__
from torpro.core.constants import AnsiColor
from torpro.core.logger import Logger


def test_tcp(host: str, port: int, timeout: float = 3.0) -> Tuple[bool, float, str]:
    """Test TCP connection and measure latency."""
    start = time.time()
    try:
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        latency = (time.time() - start) * 1000
        return True, latency, "OK"
    except socket.timeout:
        return False, 0.0, "Timeout (Filtered / Blocked)"
    except ConnectionRefusedError:
        return False, 0.0, "Connection Refused"
    except Exception as err:
        return False, 0.0, str(err)


def test_udp_stun(host: str, port: int, timeout: float = 3.0) -> Tuple[bool, float, str]:
    """Test UDP STUN server for WebRTC ICE traversal."""
    start = time.time()
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        # STUN Binding Request (RFC 5389): Message Type 0x0001, Length 0, Magic Cookie 0x2112A442
        req = b"\x00\x01\x00\x00\x21\x12\xa4\x42" + b"\x00" * 12
        sock.sendto(req, (host, port))
        data, _ = sock.recvfrom(1024)
        sock.close()
        latency = (time.time() - start) * 1000
        if len(data) >= 20:
            return True, latency, "STUN Responsive"
        return False, 0.0, "Invalid Response"
    except socket.timeout:
        return False, 0.0, "UDP Timeout (WebRTC Blocked / Dropped)"
    except Exception as err:
        return False, 0.0, str(err)


def test_fronted_https(front_domain: str, target_host: str, path: str = "/", timeout: float = 4.0) -> Tuple[bool, float, str]:
    """Test Domain Fronting TLS handshake and HTTP response."""
    start = time.time()
    try:
        context = ssl.create_default_context()
        conn = http.client.HTTPSConnection(front_domain, timeout=timeout, context=context)
        conn.request("GET", path, headers={"Host": target_host, "User-Agent": "Mozilla/5.0"})
        resp = conn.getresponse()
        latency = (time.time() - start) * 1000
        status = resp.status
        conn.close()
        return True, latency, f"HTTP {status}"
    except socket.timeout:
        return False, 0.0, "TLS Timeout (SNI Filtered)"
    except Exception as err:
        return False, 0.0, str(err)


def main():
    Logger.print_banner()
    print(f"{AnsiColor.BOLD}{AnsiColor.BRIGHT_YELLOW}Iran Network Circumvention & Transport Diagnostics{AnsiColor.RESET}\n")

    # 1. Test Snowflake Broker Domain Fronting Profiles
    print(f"{AnsiColor.BOLD}[1/3] Testing Snowflake Broker Endpoints & Domain Fronting...{AnsiColor.RESET}")

    brokers = [
        {
            "name": "Azure CDN Front (ajax.aspnetcdn.com -> snowflake-broker.azureedge.net)",
            "front": "ajax.aspnetcdn.com",
            "host": "snowflake-broker.azureedge.net",
            "path": "/",
        },
        {
            "name": "Fastly Front (fsh.criteo.com -> snowflake-broker.torproject.net.global.prod.fastly.net)",
            "front": "fsh.criteo.com",
            "host": "snowflake-broker.torproject.net.global.prod.fastly.net",
            "path": "/",
        },
        {
            "name": "Fastly Front (cdn.sstatic.net -> snowflake-broker.torproject.net.global.prod.fastly.net)",
            "front": "cdn.sstatic.net",
            "host": "snowflake-broker.torproject.net.global.prod.fastly.net",
            "path": "/",
        },
        {
            "name": "Google AMP Front (www.google.com -> cdn.ampproject.org)",
            "front": "www.google.com",
            "host": "cdn.ampproject.org",
            "path": "/amp/s/snowflake-broker.torproject.net/",
        },
    ]

    working_brokers = []
    for b in brokers:
        ok, latency, msg = test_fronted_https(b["front"], b["host"], b["path"])
        badge = f"{AnsiColor.BRIGHT_GREEN}[PASS]{AnsiColor.RESET}" if ok else f"{AnsiColor.BRIGHT_RED}[FAIL]{AnsiColor.RESET}"
        latency_str = f"({latency:.1f} ms)" if ok else ""
        print(f"  {badge} {b['name']}: {msg} {latency_str}")
        if ok:
            working_brokers.append(b)

    # 2. Test STUN Servers (UDP WebRTC for Snowflake)
    print(f"\n{AnsiColor.BOLD}[2/3] Testing STUN Servers (WebRTC UDP for Snowflake)...{AnsiColor.RESET}")
    stun_servers = [
        ("stun.l.google.com", 19302),
        ("stun.voip.blackberry.com", 3478),
        ("stun.antisip.com", 3478),
        ("stun.bluesip.net", 3478),
        ("stun.dus.net", 3478),
        ("stun.sonetel.com", 3478),
        ("stun.uls.co.za", 3478),
    ]

    working_stuns = []
    for host, port in stun_servers:
        ok, latency, msg = test_udp_stun(host, port)
        badge = f"{AnsiColor.BRIGHT_GREEN}[PASS]{AnsiColor.RESET}" if ok else f"{AnsiColor.BRIGHT_RED}[FAIL]{AnsiColor.RESET}"
        latency_str = f"({latency:.1f} ms)" if ok else ""
        print(f"  {badge} {host}:{port} -> {msg} {latency_str}")
        if ok:
            working_stuns.append(f"stun:{host}:{port}")

    # 3. Test Tor Direct Authorities / BridgeDB
    print(f"\n{AnsiColor.BOLD}[3/3] Testing BridgeDB & Tor Network Reachability...{AnsiColor.RESET}")
    direct_targets = [
        ("bridges.torproject.org", 443, "Tor BridgeDB HTTPS"),
        ("check.torproject.org", 443, "Tor Check Endpoint"),
        ("193.23.244.244", 80, "Tor Directory Authority (Moria1)"),
    ]

    for host, port, desc in direct_targets:
        ok, latency, msg = test_tcp(host, port)
        badge = f"{AnsiColor.BRIGHT_GREEN}[PASS]{AnsiColor.RESET}" if ok else f"{AnsiColor.BRIGHT_RED}[FAIL]{AnsiColor.RESET}"
        latency_str = f"({latency:.1f} ms)" if ok else ""
        print(f"  {badge} {desc} ({host}:{port}) -> {msg} {latency_str}")

    # Recommendations
    print(f"\n{AnsiColor.BOLD}{'=' * 72}{AnsiColor.RESET}")
    print(f"{AnsiColor.BOLD}{AnsiColor.BRIGHT_MAGENTA}Summary & Transport Recommendation:{AnsiColor.RESET}")

    if working_brokers and working_stuns:
        print(f"{AnsiColor.BRIGHT_GREEN}* Snowflake is VIABLE on your connection.{AnsiColor.RESET}")
        print(f"  Working Brokers: {len(working_brokers)}/{len(brokers)}")
        print(f"  Working STUNs:   {len(working_stuns)}/{len(stun_servers)}")
    elif not working_stuns:
        print(f"{AnsiColor.BRIGHT_YELLOW}* WebRTC UDP / STUN is restricted by your ISP.{AnsiColor.RESET}")
        print(f"  Snowflake might struggle with NAT traversal.")
        print(f"  Recommendation: Use WebTunnel or Obfs4 bridges.")
    else:
        print(f"{AnsiColor.BRIGHT_YELLOW}* Domain fronting brokers are filtered.{AnsiColor.RESET}")
        print(f"  Recommendation: Use WebTunnel or Obfs4 bridges from Telegram bot.")

    print(f"{AnsiColor.BOLD}{'=' * 72}{AnsiColor.RESET}\n")


if __name__ == "__main__":
    main()
