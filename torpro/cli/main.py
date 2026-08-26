"""Command-line interface (CLI) dispatcher for Tor Pro."""

import argparse
import sys
import time

from torpro import __app_name__, __version__
from torpro.bridges.manager import BridgeManager
from torpro.core.constants import (
    AnsiColor,
    HTTP_HOST,
    HTTP_PORT,
    SOCKS5_HOST,
    SOCKS5_PORT,
    TOR_LOG_FILE,
)
from torpro.core.logger import Logger
from torpro.diagnostics.engine import DiagnosticEngine
from torpro.proxy.http_bridge import HttpBridgeService
from torpro.proxy.sysproxy import SystemProxyManager
from torpro.service.connection_tester import ConnectionTester
from torpro.service.tor_service import BootstrapStatus, TorService


def render_progress_bar(status: BootstrapStatus) -> None:
    """Render a visual terminal progress bar for Tor bootstrap."""
    bar_width = 30
    filled = int(bar_width * (status.percent / 100))
    bar = "#" * filled + "-" * (bar_width - filled)
    color = AnsiColor.BRIGHT_GREEN if status.percent == 100 else AnsiColor.BRIGHT_CYAN

    sys.stdout.write(
        f"\r{color}{AnsiColor.BOLD}[{bar}] {status.percent:3d}%{AnsiColor.RESET} "
        f"{AnsiColor.DIM}{status.summary[:40]:<40}{AnsiColor.RESET}"
    )
    sys.stdout.flush()
    if status.percent == 100:
        print()


def cmd_start(args) -> int:
    """Handle start command."""
    service = TorService()
    mode = getattr(args, "mode", "snowflake") or "snowflake"

    Logger.header(f"{__app_name__} v{__version__} - Starting Service")
    print(f" {AnsiColor.BOLD}* Transport Mode:{AnsiColor.RESET} {mode.upper()}")
    print(f" {AnsiColor.BOLD}* SOCKS5 Target:{AnsiColor.RESET}  {SOCKS5_HOST}:{SOCKS5_PORT}")
    print(f" {AnsiColor.BOLD}* HTTP Target:{AnsiColor.RESET}    {HTTP_HOST}:{HTTP_PORT}\n")

    success = service.start(
        mode=mode,
        enable_http_bridge=True,
        on_progress=render_progress_bar,
    )
    if success:
        print(f"\n{AnsiColor.BRIGHT_GREEN}{AnsiColor.BOLD}[OK] Tor Pro is ready for use!{AnsiColor.RESET}")
        print(f"  SOCKS5 Proxy: {SOCKS5_HOST}:{SOCKS5_PORT}")
        print(f"  HTTP Proxy:   http://{HTTP_HOST}:{HTTP_PORT}\n")
        return 0
    return 1


def cmd_stop(args) -> int:
    """Handle stop command."""
    service = TorService()
    service.stop()
    return 0


def cmd_restart(args) -> int:
    """Handle restart command."""
    service = TorService()
    mode = getattr(args, "mode", "snowflake") or "snowflake"
    success = service.restart(mode=mode)
    return 0 if success else 1


def cmd_status(args) -> int:
    """Display comprehensive status of Tor Pro processes and ports."""
    tor_pid = TorService.get_pid()
    tor_running = TorService.is_running()
    http_pid = HttpBridgeService.get_pid()
    http_running = HttpBridgeService.is_running()
    gnome_proxy = SystemProxyManager.is_gnome_proxy_enabled()

    Logger.header(f"{__app_name__} System Status")
    print(f" {AnsiColor.BOLD}* Tor Core Daemon:{AnsiColor.RESET}     " + (
        f"{AnsiColor.BRIGHT_GREEN}RUNNING (PID: {tor_pid}){AnsiColor.RESET}" if tor_running
        else f"{AnsiColor.DIM}STOPPED{AnsiColor.RESET}"
    ))
    print(f" {AnsiColor.BOLD}* HTTP-to-SOCKS5:{AnsiColor.RESET}      " + (
        f"{AnsiColor.BRIGHT_GREEN}RUNNING (PID: {http_pid}){AnsiColor.RESET}" if http_running
        else f"{AnsiColor.DIM}STOPPED{AnsiColor.RESET}"
    ))
    print(f" {AnsiColor.BOLD}* Desktop System Proxy:{AnsiColor.RESET} " + (
        f"{AnsiColor.BRIGHT_CYAN}ENABLED{AnsiColor.RESET}" if gnome_proxy
        else f"{AnsiColor.DIM}DISABLED{AnsiColor.RESET}"
    ))

    if tor_running:
        bootstrap = TorService.parse_current_bootstrap()
        if bootstrap:
            print(f" {AnsiColor.BOLD}* Bootstrap State:{AnsiColor.RESET}     {bootstrap.percent}% ({bootstrap.summary})")

    print()
    return 0


def cmd_doctor(args) -> int:
    """Run all 5 diagnostic tests."""
    engine = DiagnosticEngine()
    results = engine.run_all(print_report=True)
    all_ok = all(r.is_passed for r in results)
    return 0 if all_ok else 1


def cmd_test(args) -> int:
    """Test connection and show exit IP."""
    ConnectionTester.print_report()
    return 0


def cmd_proxy(args) -> int:
    """Handle system proxy toggle."""
    action = getattr(args, "action", "status")
    if action == "on":
        SystemProxyManager.enable_gnome_proxy()
        SystemProxyManager.generate_env_script()
        Logger.success("System proxy ENABLED (GNOME & env.sh).")
    elif action == "off":
        SystemProxyManager.disable_gnome_proxy()
        SystemProxyManager.generate_env_script()
        Logger.info("System proxy DISABLED.")
    else:
        enabled = SystemProxyManager.is_gnome_proxy_enabled()
        state = f"{AnsiColor.BRIGHT_GREEN}ENABLED{AnsiColor.RESET}" if enabled else f"{AnsiColor.DIM}DISABLED{AnsiColor.RESET}"
        print(f"System Proxy is {state}")
    return 0


def cmd_logs(args) -> int:
    """Tail log file."""
    if not TOR_LOG_FILE.exists():
        Logger.warning("No log file found yet.")
        return 0
    import subprocess
    subprocess.run(["tail", "-n", "50", "-f", str(TOR_LOG_FILE)])
    return 0


def cmd_menu(args) -> int:
    """Launch interactive TUI dashboard."""
    from torpro.cli.tui import TuiDashboard
    dashboard = TuiDashboard()
    dashboard.run()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Construct CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="torpro",
        description=f"{__app_name__} v{__version__} - Professional Tor Suite for Linux",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logs")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # start
    p_start = subparsers.add_parser("start", help="Start Tor service")
    p_start.add_argument(
        "mode",
        nargs="?",
        default="snowflake",
        choices=["snowflake", "obfs4", "webtunnel", "direct"],
        help="Bridge transport mode (default: snowflake)",
    )
    p_start.set_defaults(func=cmd_start)

    # stop
    p_stop = subparsers.add_parser("stop", help="Stop Tor service and HTTP bridge")
    p_stop.set_defaults(func=cmd_stop)

    # restart
    p_restart = subparsers.add_parser("restart", help="Restart Tor service")
    p_restart.add_argument("mode", nargs="?", default="snowflake", help="Bridge mode")
    p_restart.set_defaults(func=cmd_restart)

    # status
    p_status = subparsers.add_parser("status", help="Show running status and ports")
    p_status.set_defaults(func=cmd_status)

    # doctor
    p_doctor = subparsers.add_parser("doctor", help="Run 5 diagnostic health checks")
    p_doctor.set_defaults(func=cmd_doctor)

    # test
    p_test = subparsers.add_parser("test", help="Test Tor network connection & IP")
    p_test.set_defaults(func=cmd_test)

    # proxy
    p_proxy = subparsers.add_parser("proxy", help="Manage system-wide desktop proxy")
    p_proxy.add_argument("action", choices=["on", "off", "status"], default="status", nargs="?")
    p_proxy.set_defaults(func=cmd_proxy)

    # logs
    p_logs = subparsers.add_parser("logs", help="Tail Tor live connection logs")
    p_logs.set_defaults(func=cmd_logs)

    # menu
    p_menu = subparsers.add_parser("menu", help="Launch interactive TUI dashboard")
    p_menu.set_defaults(func=cmd_menu)

    return parser


def main() -> int:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        Logger.set_verbose(True)

    if not args.command:
        # If no arguments given, launch the interactive menu by default!
        from torpro.cli.tui import TuiDashboard
        dashboard = TuiDashboard()
        dashboard.run()
        return 0

    if hasattr(args, "func"):
        return args.func(args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
