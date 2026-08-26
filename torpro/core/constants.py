"""Project-wide constants, paths, and default configurations.

This module centralizes all directory paths, binary targets, network ports,
and ANSI styling codes following the DRY (Don't Repeat Yourself) principle.
"""

from pathlib import Path
import sys

# Directory Structure
CORE_DIR = Path(__file__).resolve().parent
PACKAGE_DIR = CORE_DIR.parent
BASE_DIR = PACKAGE_DIR.parent

BIN_DIR = BASE_DIR / "bin"
LIB_DIR = BIN_DIR / "lib"
CONFIG_DIR = BASE_DIR / "config"
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Binary Executables
TOR_BIN = BIN_DIR / "tor"
SNOWFLAKE_BIN = BIN_DIR / "snowflake-client"
LYREBIRD_BIN = BIN_DIR / "lyrebird"
CHECKSUMS_FILE = BIN_DIR / "checksums.sha256"

# Configuration Files
TORRC_PATH = BASE_DIR / "torrc"
TORRC_BASE = CONFIG_DIR / "torrc.base"
CUSTOM_BRIDGES_FILE = CONFIG_DIR / "custom_bridges.txt"

# Process & State Files
TOR_PID_FILE = BASE_DIR / ".tor.pid"
HTTP_PID_FILE = BASE_DIR / ".http_bridge.pid"
TOR_LOG_FILE = LOGS_DIR / "tor.log"
HTTP_LOG_FILE = LOGS_DIR / "http_bridge.log"

# Default Network Ports
SOCKS5_HOST = "127.0.0.1"
SOCKS5_PORT = 9050

HTTP_HOST = "127.0.0.1"
HTTP_PORT = 8118

CONTROL_HOST = "127.0.0.1"
CONTROL_PORT = 9051

# Default Connection Test Endpoints
TOR_CHECK_API_URL = "https://check.torproject.org/api/ip"
IP_API_URL = "https://api.ipify.org?format=json"

# Timeout Defaults (in seconds)
BOOTSTRAP_TIMEOUT_SECONDS = 60
COMMAND_TIMEOUT_SECONDS = 15
HTTP_PROXY_TIMEOUT_SECONDS = 30

# ANSI Terminal Color & Style Codes
class AnsiColor:
    """ANSI Escape Codes for rich terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"

    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"

    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"
    BRIGHT_WHITE = "\033[97m"
