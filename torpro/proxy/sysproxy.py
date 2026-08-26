"""System-wide proxy management for GNOME, KDE, and Shell environments."""

import os
from pathlib import Path
import shutil
from typing import Dict, Optional

from torpro.core.constants import BASE_DIR, HTTP_HOST, HTTP_PORT, SOCKS5_HOST, SOCKS5_PORT
from torpro.core.exceptions import SystemProxyError
from torpro.core.logger import Logger
from torpro.core.process import CommandRunner


class SystemProxyManager:
    """Manages OS desktop and terminal proxy configurations."""

    @staticmethod
    def is_gnome_available() -> bool:
        """Check if gsettings (GNOME/Cinnamon/MATE) is available."""
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
            return False

        try:
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "'manual'"], check=True)
            # SOCKS
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy.socks", "host", f"'{socks_host}'"], check=True)
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy.socks", "port", str(socks_port)], check=True)
            # HTTP
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy.http", "host", f"'{http_host}'"], check=True)
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy.http", "port", str(http_port)], check=True)
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy.http", "enabled", "true"], check=True)
            # HTTPS
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy.https", "host", f"'{http_host}'"], check=True)
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy.https", "port", str(http_port)], check=True)
            return True
        except Exception as err:
            raise SystemProxyError("Failed to set GNOME system proxy", details=str(err))

    @classmethod
    def disable_gnome_proxy(cls) -> bool:
        """Reset GNOME system proxy mode to none."""
        if not cls.is_gnome_available():
            return False

        try:
            CommandRunner.run(["gsettings", "set", "org.gnome.system.proxy", "mode", "'none'"], check=True)
            return True
        except Exception as err:
            raise SystemProxyError("Failed to disable GNOME system proxy", details=str(err))

    @classmethod
    def is_gnome_proxy_enabled(cls) -> bool:
        """Check if GNOME proxy mode is currently manual."""
        if not cls.is_gnome_available():
            return False
        res = CommandRunner.run(["gsettings", "get", "org.gnome.system.proxy", "mode"])
        return "manual" in res.stdout.lower()

    @classmethod
    def generate_env_script(cls) -> Path:
        """Generate/update env.sh for terminal proxy exports."""
        env_file = BASE_DIR / "env.sh"
        content = (
            "#!/bin/bash\n"
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
