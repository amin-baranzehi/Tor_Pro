"""System-wide proxy management for GNOME, KDE, and Shell environments."""

import os
from pathlib import Path
import pwd
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from torpro.core.constants import BASE_DIR, HTTP_HOST, HTTP_PORT, SOCKS5_HOST, SOCKS5_PORT
from torpro.core.exceptions import SystemProxyError
from torpro.core.logger import Logger


class SystemProxyManager:
    """Manages OS desktop and terminal proxy configurations."""

    @staticmethod
    def _get_target_user_and_bus() -> Tuple[str, int, Optional[str]]:
        """Resolve the desktop user, UID, and DBUS session bus address."""
        # 1. Determine user
        sudo_user = os.environ.get("SUDO_USER")
        if sudo_user and os.geteuid() == 0:
            target_user = sudo_user
        else:
            target_user = os.environ.get("USER") or os.environ.get("LOGNAME") or "amin"

        try:
            user_info = pwd.getpwnam(target_user)
            uid = user_info.pw_uid
        except Exception:
            uid = os.geteuid()

        # 2. Determine DBUS address
        dbus_addr = os.environ.get("DBUS_SESSION_BUS_ADDRESS")
        if not dbus_addr or os.geteuid() == 0:
            user_bus = Path(f"/run/user/{uid}/bus")
            if user_bus.exists():
                dbus_addr = f"unix:path={user_bus}"

        return target_user, uid, dbus_addr

    @classmethod
    def _run_gsettings(cls, args: List[str]) -> subprocess.CompletedProcess:
        """Execute gsettings command targeting the desktop user's session bus."""
        target_user, uid, dbus_addr = cls._get_target_user_and_bus()
        env = os.environ.copy()
        if dbus_addr:
            env["DBUS_SESSION_BUS_ADDRESS"] = dbus_addr

        if os.geteuid() == 0 and target_user != "root":
            # Run as target desktop user
            cmd = ["sudo", "-u", target_user]
            if dbus_addr:
                cmd.append(f"DBUS_SESSION_BUS_ADDRESS={dbus_addr}")
            cmd.append("gsettings")
            cmd.extend(args)
            return subprocess.run(" ".join(cmd), shell=True, capture_output=True, text=True)

        cmd = ["gsettings"] + args
        return subprocess.run(cmd, env=env, capture_output=True, text=True)

    @classmethod
    def is_gnome_available(cls) -> bool:
        """Check if gsettings is available on the system."""
        return shutil.which("gsettings") is not None

    @classmethod
    def enable_gnome_proxy(
        cls,
        http_host: str = HTTP_HOST,
        http_port: int = HTTP_PORT,
        socks_host: str = SOCKS5_HOST,
        socks_port: int = SOCKS5_PORT,
    ) -> bool:
        """Configure GNOME system proxy via gsettings."""
        if not cls.is_gnome_available():
            Logger.warning("gsettings not found on system.")
            return False

        commands = [
            ["set", "org.gnome.system.proxy", "mode", "manual"],
            ["set", "org.gnome.system.proxy.socks", "host", socks_host],
            ["set", "org.gnome.system.proxy.socks", "port", str(socks_port)],
            ["set", "org.gnome.system.proxy.http", "host", http_host],
            ["set", "org.gnome.system.proxy.http", "port", str(http_port)],
            ["set", "org.gnome.system.proxy.http", "enabled", "true"],
            ["set", "org.gnome.system.proxy.https", "host", http_host],
            ["set", "org.gnome.system.proxy.https", "port", str(http_port)],
        ]

        for args in commands:
            res = cls._run_gsettings(args)
            if res.returncode != 0:
                Logger.debug(f"gsettings {' '.join(args)} stderr: {res.stderr}")

        # Always generate env.sh
        cls.generate_env_script()
        return True

    @classmethod
    def disable_gnome_proxy(cls) -> bool:
        """Reset GNOME system proxy mode to none."""
        if not cls.is_gnome_available():
            return False

        res = cls._run_gsettings(["set", "org.gnome.system.proxy", "mode", "none"])
        if res.returncode != 0:
            Logger.debug(f"gsettings disable stderr: {res.stderr}")

        cls.generate_env_script()
        return True

    @classmethod
    def is_gnome_proxy_enabled(cls) -> bool:
        """Check if GNOME proxy mode is currently manual."""
        if not cls.is_gnome_available():
            return False
        res = cls._run_gsettings(["get", "org.gnome.system.proxy", "mode"])
        return "manual" in res.stdout.lower()

    @classmethod
    def generate_env_script(cls) -> Path:
        """Generate/update env.sh for terminal proxy exports."""
        env_file = BASE_DIR / "env.sh"
        content = (
            "#!/bin/bash\n"
            "# Tor Pro Terminal Proxy Environment\n"
            "# Usage: source env.sh on  |  source env.sh off\n"
            'ACTION="${1:-on}"\n\n'
            'if [ "$ACTION" = "on" ]; then\n'
            f'    export http_proxy="http://{HTTP_HOST}:{HTTP_PORT}"\n'
            f'    export https_proxy="http://{HTTP_HOST}:{HTTP_PORT}"\n'
            f'    export HTTP_PROXY="http://{HTTP_HOST}:{HTTP_PORT}"\n'
            f'    export HTTPS_PROXY="http://{HTTP_HOST}:{HTTP_PORT}"\n'
            f'    export all_proxy="socks5h://{SOCKS5_HOST}:{SOCKS5_PORT}"\n'
            f'    export ALL_PROXY="socks5h://{SOCKS5_HOST}:{SOCKS5_PORT}"\n'
            '    echo "[Tor Pro] Terminal proxy ENABLED (HTTP: 8118, SOCKS5: 9050)"\n'
            'else\n'
            '    unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY\n'
            '    echo "[Tor Pro] Terminal proxy DISABLED"\n'
            'fi\n'
        )
        env_file.write_text(content, encoding="utf-8")
        env_file.chmod(0o755)
        return env_file
