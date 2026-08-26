"""Interactive Terminal User Interface (TUI) Dashboard for Tor Pro.

Provides an ASCII banner and clean menu for controlling Tor, switching bridges,
rotating IP addresses, fetching fresh bridges, running diagnostics, toggling proxy,
and inspecting logs.
"""

import os
import sys
import time
from typing import Optional

from torpro import __app_name__, __version__
from torpro.bridges.fetcher import BridgeFetcher
from torpro.bridges.manager import BridgeManager
from torpro.core.constants import (
    AnsiColor,
    CUSTOM_BRIDGES_FILE,
    HTTP_HOST,
    HTTP_PORT,
    SOCKS5_HOST,
    SOCKS5_PORT,
    TOR_LOG_FILE,
)
from torpro.core.exceptions import ConfigError
from torpro.core.logger import Logger
from torpro.diagnostics.engine import DiagnosticEngine
from torpro.proxy.http_bridge import HttpBridgeService
from torpro.proxy.sysproxy import SystemProxyManager
from torpro.service.connection_tester import ConnectionTester
from torpro.service.ip_rotator import TorIpRotator
from torpro.service.tor_service import BootstrapStatus, TorService


class TuiDashboard:
    """Terminal interactive menu manager."""

    def __init__(self) -> None:
        self.service = TorService()
        self.bridge_manager = BridgeManager()
        self.diagnostics = DiagnosticEngine()

    @staticmethod
    def clear_screen() -> None:
        """Clear terminal screen."""
        os.system("clear" if os.name == "posix" else "cls")

    @staticmethod
    def pause() -> None:
        """Wait for user to press Enter before returning to menu."""
        print(f"\n{AnsiColor.DIM}Press Enter to return to main menu...{AnsiColor.RESET}", end="")
        try:
            input()
        except (KeyboardInterrupt, EOFError):
            pass

    def render_banner(self) -> None:
        """Render ASCII banner with author information."""
        Logger.print_banner()

    def render_status(self) -> None:
        """Render service status summary."""
        tor_running = TorService.is_running()
        tor_pid = TorService.get_pid()
        http_running = HttpBridgeService.is_running()
        sysproxy_on = SystemProxyManager.is_gnome_proxy_enabled()

        tor_badge = (
            f"{AnsiColor.BRIGHT_GREEN}[RUNNING - PID {tor_pid}]{AnsiColor.RESET}"
            if tor_running
            else f"{AnsiColor.BRIGHT_RED}[STOPPED]{AnsiColor.RESET}"
        )
        http_badge = (
            f"{AnsiColor.BRIGHT_GREEN}[PORT {HTTP_PORT}]{AnsiColor.RESET}"
            if http_running
            else f"{AnsiColor.DIM}[STOPPED]{AnsiColor.RESET}"
        )
        proxy_badge = (
            f"{AnsiColor.BRIGHT_CYAN}[ENABLED]{AnsiColor.RESET}"
            if sysproxy_on
            else f"{AnsiColor.DIM}[DISABLED]{AnsiColor.RESET}"
        )

        print(f"  Tor Core: {tor_badge} | HTTP Proxy: {http_badge} | SysProxy: {proxy_badge}")
        print(f"  {AnsiColor.DIM}SOCKS5: {SOCKS5_HOST}:{SOCKS5_PORT} | HTTP: http://{HTTP_HOST}:{HTTP_PORT}{AnsiColor.RESET}")
        print(f"  {AnsiColor.DIM}{'-' * 70}{AnsiColor.RESET}")

    def render_menu(self) -> None:
        """Render menu options without emojis."""
        print(f"  {AnsiColor.BOLD}{AnsiColor.BRIGHT_YELLOW}MAIN MENU / MENU ASLI:{AnsiColor.RESET}")
        print(f"   {AnsiColor.BRIGHT_GREEN}{AnsiColor.BOLD}[1]{AnsiColor.RESET}  Start Tor with Snowflake (Default Anti-Censorship)")
        print(f"   {AnsiColor.BRIGHT_CYAN}{AnsiColor.BOLD}[2]{AnsiColor.RESET}  Start Tor with other Bridge (WebTunnel / Obfs4 / Direct)")
        print(f"   {AnsiColor.BRIGHT_RED}{AnsiColor.BOLD}[3]{AnsiColor.RESET}  Stop Tor & Proxy Services")
        print(f"   {AnsiColor.GREEN}{AnsiColor.BOLD}[4]{AnsiColor.RESET}  Request New IP Address / تغییر فوری آی‌پی (New Circuit)")
        print(f"   {AnsiColor.MAGENTA}{AnsiColor.BOLD}[5]{AnsiColor.RESET}  Auto IP Rotator Mode / چرخش خودکار آی‌پی بر حسب زمان")
        print(f"   {AnsiColor.BRIGHT_BLUE}{AnsiColor.BOLD}[6]{AnsiColor.RESET}  Test Tor Connection & Check Exit IP")
        print(f"   {AnsiColor.BRIGHT_MAGENTA}{AnsiColor.BOLD}[7]{AnsiColor.RESET}  Run Doctor Health Diagnostics (5 Diagnostic Tests)")
        print(f"   {AnsiColor.BRIGHT_YELLOW}{AnsiColor.BOLD}[8]{AnsiColor.RESET}  Toggle Desktop System Proxy (Enable / Disable)")
        print(f"   {AnsiColor.CYAN}{AnsiColor.BOLD}[9]{AnsiColor.RESET}  Auto-Fetch Fresh Obfs4 / WebTunnel Bridges (Bypass BridgeDB)")
        print(f"   {AnsiColor.WHITE}{AnsiColor.BOLD}[10]{AnsiColor.RESET} Manage / Paste Custom Bridges (config/custom_bridges.txt)")
        print(f"   {AnsiColor.DIM}{AnsiColor.BOLD}[11]{AnsiColor.RESET} View Live Connection Logs")
        print(f"   {AnsiColor.DIM}{AnsiColor.BOLD}[0]{AnsiColor.RESET}  Exit")
        print(f"  {AnsiColor.DIM}{'-' * 70}{AnsiColor.RESET}")

    def run(self) -> None:
        """Main interaction loop."""
        while True:
            self.clear_screen()
            self.render_banner()
            self.render_status()
            self.render_menu()

            try:
                choice = input(f"  {AnsiColor.BOLD}Select an option [0-11]: {AnsiColor.RESET}").strip()
            except (KeyboardInterrupt, EOFError):
                print(f"\n{AnsiColor.DIM}Exiting Tor Pro.{AnsiColor.RESET}")
                break

            if choice == "1":
                self._handle_start_snowflake()
            elif choice == "2":
                self._handle_select_bridge()
            elif choice == "3":
                self._handle_stop()
            elif choice == "4":
                self._handle_rotate_ip()
            elif choice == "5":
                self._handle_autorotate_ip()
            elif choice == "6":
                self._handle_test()
            elif choice == "7":
                self._handle_doctor()
            elif choice == "8":
                self._handle_toggle_proxy()
            elif choice == "9":
                self._handle_auto_fetch()
            elif choice == "10":
                self._handle_custom_bridges()
            elif choice == "11":
                self._handle_logs()
            elif choice == "0" or choice.lower() in ("q", "exit"):
                print(f"\n{AnsiColor.DIM}Goodbye!{AnsiColor.RESET}")
                break

    def _handle_start_snowflake(self) -> None:
        """Start Tor with default Snowflake transport."""
        self.clear_screen()
        Logger.print_banner()
        self.service.start(mode="snowflake", enable_http_bridge=True)
        self.pause()

    def _handle_select_bridge(self) -> None:
        """Prompt user for bridge selection."""
        self.clear_screen()
        Logger.print_banner()
        print("  [1] Snowflake   (WebRTC Ephemeral Proxies - Recommended for Iran)")
        print("  [2] WebTunnel   (HTTPS Traffic Masking - Requires WebTunnel bridge)")
        print("  [3] Obfs4       (Obfuscated Bridge IPs - Requires Obfs4 bridge)")
        print("  [4] Direct      (No Bridge / Direct Tor Network)")
        print("  [0] Back")

        sub_choice = input(f"\n  {AnsiColor.BOLD}Choice [1-4]: {AnsiColor.RESET}").strip()
        modes = {"1": "snowflake", "2": "webtunnel", "3": "obfs4", "4": "direct"}
        selected_mode = modes.get(sub_choice)

        if not selected_mode:
            return

        if selected_mode in ("webtunnel", "obfs4"):
            has_bridges = False
            if CUSTOM_BRIDGES_FILE.exists():
                content = CUSTOM_BRIDGES_FILE.read_text(encoding="utf-8")
                has_bridges = any(selected_mode in line.lower() for line in content.splitlines() if line.strip() and not line.startswith("#"))

            if not has_bridges:
                print(f"\n{AnsiColor.BRIGHT_YELLOW}Notice: No {selected_mode.upper()} bridge lines found in config/custom_bridges.txt.{AnsiColor.RESET}")
                print(f"Would you like to fetch fresh {selected_mode.upper()} bridges automatically via unblocked relay?")
                auto = input(f"{AnsiColor.BOLD}Auto-fetch fresh bridges now? [Y/n]: {AnsiColor.RESET}").strip().lower()
                if auto in ("", "y", "yes"):
                    fetch_res = BridgeFetcher.fetch_via_httpdebugger(transport=selected_mode)
                    if fetch_res.success and fetch_res.bridges:
                        BridgeFetcher.update_custom_bridges_file(fetch_res.bridges)
                        Logger.success(f"Successfully fetched and saved {len(fetch_res.bridges)} {selected_mode.upper()} bridges!")
                    else:
                        Logger.error(f"Auto-fetch failed: {fetch_res.error}")
                        print(f"You can paste your own bridges or use Snowflake (Option [1]).")
                        self.pause()
                        return
                else:
                    print(f"\n{AnsiColor.BOLD}Paste your bridge lines below (Press Enter on an empty line when done):{AnsiColor.RESET}")
                    new_lines = []
                    while True:
                        try:
                            l = input()
                            if not l.strip():
                                break
                            new_lines.append(l.strip())
                        except (KeyboardInterrupt, EOFError):
                            break
                    if new_lines:
                        BridgeManager.save_custom_bridges(new_lines)
                    else:
                        print(f"{AnsiColor.DIM}No bridges entered. Returning.{AnsiColor.RESET}")
                        self.pause()
                        return

        try:
            self.service.start(mode=selected_mode, enable_http_bridge=True)
        except ConfigError as err:
            Logger.error(str(err))
        self.pause()

    def _handle_rotate_ip(self) -> None:
        """Request new IP circuit now."""
        self.clear_screen()
        Logger.print_banner()
        Logger.info("Requesting new Tor identity circuit (SIGNAL NEWNYM)...")
        res = TorIpRotator.rotate_now(cooldown=2.0)
        if res.success:
            print(f"\n{AnsiColor.BRIGHT_GREEN}{AnsiColor.BOLD}[OK] IP Rotation Succeeded!{AnsiColor.RESET}")
            print(f"  New Exit IP: {AnsiColor.BRIGHT_CYAN}{res.new_ip}{AnsiColor.RESET}")
            print(f"  Location:   {res.country}\n")
        else:
            Logger.error("Failed to rotate IP", res.message)
        self.pause()

    def _handle_autorotate_ip(self) -> None:
        """Run periodic auto IP rotator."""
        self.clear_screen()
        Logger.print_banner()
        print("  Auto IP Rotator Configuration\n")
        raw_sec = input(f"  {AnsiColor.BOLD}Enter rotation interval in seconds (default: 30): {AnsiColor.RESET}").strip()
        interval = int(raw_sec) if raw_sec.isdigit() and int(raw_sec) >= 5 else 30
        TorIpRotator.run_auto_rotator(interval_seconds=interval)
        self.pause()

    def _handle_auto_fetch(self) -> None:
        """Fetch fresh Obfs4 or WebTunnel bridges via relay."""
        self.clear_screen()
        Logger.print_banner()
        print("  Auto-Fetch Fresh Bridges (Bypasses BridgeDB Blocking)\n")
        print("  [1] Fetch Obfs4 Bridges")
        print("  [2] Fetch WebTunnel Bridges")
        print("  [0] Back")

        sub = input(f"\n  {AnsiColor.BOLD}Choice [1-2]: {AnsiColor.RESET}").strip()
        if sub == "1":
            t = "obfs4"
        elif sub == "2":
            t = "webtunnel"
        else:
            return

        Logger.info(f"Connecting to unblocked HTTP relay to fetch {t.upper()} bridges...")
        res = BridgeFetcher.fetch_via_httpdebugger(transport=t)
        if res.success and res.bridges:
            saved_file = BridgeFetcher.update_custom_bridges_file(res.bridges, append=False)
            Logger.success(f"Fetched {len(res.bridges)} fresh {t.upper()} bridge(s) from {res.source}!")
            print(f"\n{AnsiColor.BOLD}New Bridges:{AnsiColor.RESET}")
            for b in res.bridges:
                print(f"  {AnsiColor.BRIGHT_CYAN}-> {b}{AnsiColor.RESET}")
            print(f"\n{AnsiColor.GREEN}[OK] Saved to {saved_file.name}{AnsiColor.RESET}")
        else:
            Logger.error(f"Fetch failed: {res.error}")
            print(f"\n{AnsiColor.DIM}Tip: You can also get bridges from Telegram bot: @GetBridgesBot{AnsiColor.RESET}")
        self.pause()

    def _handle_stop(self) -> None:
        """Stop all processes."""
        self.clear_screen()
        Logger.print_banner()
        self.service.stop()
        self.pause()

    def _handle_test(self) -> None:
        """Test connection and display IP."""
        self.clear_screen()
        ConnectionTester.print_report()
        self.pause()

    def _handle_doctor(self) -> None:
        """Execute diagnostic checks."""
        self.clear_screen()
        self.diagnostics.run_all(print_report=True)
        self.pause()

    def _handle_toggle_proxy(self) -> None:
        """Toggle system proxy."""
        self.clear_screen()
        Logger.print_banner()
        current_state = SystemProxyManager.is_gnome_proxy_enabled()
        if current_state:
            SystemProxyManager.disable_gnome_proxy()
            SystemProxyManager.generate_env_script()
            Logger.info("System proxy has been DISABLED.")
        else:
            SystemProxyManager.enable_gnome_proxy()
            SystemProxyManager.generate_env_script()
            Logger.success("System proxy has been ENABLED (SOCKS5: 9050, HTTP: 8118).")
        self.pause()

    def _handle_custom_bridges(self) -> None:
        """Manage custom bridges file."""
        self.clear_screen()
        Logger.print_banner()
        print("  Manage Custom Bridges (config/custom_bridges.txt)\n")
        if CUSTOM_BRIDGES_FILE.exists():
            print(f"{AnsiColor.BOLD}Current Bridge Lines:{AnsiColor.RESET}")
            content = CUSTOM_BRIDGES_FILE.read_text(encoding="utf-8").strip()
            print(content if content else f"{AnsiColor.DIM}(Empty){AnsiColor.RESET}")
        else:
            print(f"{AnsiColor.DIM}No custom bridges added yet.{AnsiColor.RESET}")

        print(f"\n{AnsiColor.BOLD}Enter new bridge lines (Paste and press Enter on an empty line when done):{AnsiColor.RESET}")
        lines = []
        while True:
            try:
                line = input()
                if not line.strip():
                    break
                lines.append(line.strip())
            except (KeyboardInterrupt, EOFError):
                break

        if lines:
            BridgeManager.save_custom_bridges(lines)
        self.pause()

    def _handle_logs(self) -> None:
        """View Tor logs."""
        self.clear_screen()
        Logger.print_banner()
        print("  Tor Connection Logs (Press Ctrl+C to exit)\n")
        if not TOR_LOG_FILE.exists():
            Logger.warning("Log file does not exist yet.")
            self.pause()
            return

        import subprocess
        try:
            subprocess.run(["tail", "-n", "30", "-f", str(TOR_LOG_FILE)])
        except KeyboardInterrupt:
            pass
