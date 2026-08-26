# Tor Pro

```text
  _______ ____  _____    _____  _____   ____  
 |__   __/ __ \|  __ \  |  __ \|  __ \ / __ \ 
    | | | |  | | |__) | | |__) | |__) | |  | |
    | | | |  | |  _  /  |  ___/|  _  /| |  | |
    | | | |__| | | \ \  | |    | | \ \| |__| |
    |_|  \____/|_|  \_\ |_|    |_|  \_\\____/ 
========================================================================
  Tor Pro - Professional Anti-Censorship Tor Suite [v2.0.0]
  Author: amin.baranzehi_ | Advanced Privacy & Security Framework
========================================================================
```

**Tor Pro** is an enterprise-grade, standalone, zero-dependency Tor circumvention suite for Linux tailored for severe censorship environments. It provides out-of-the-box support for modern pluggable transports (**Snowflake**, **WebTunnel**, **Obfs4**), an automated online **Bridge Fetcher** that bypasses BridgeDB domain censorship, a built-in **HTTP-to-SOCKS5** dual proxy engine, 5 pre-flight diagnostic health checks (**Doctor Suite**), and an interactive **TUI Dashboard**.

---

## What We Have in Tor Pro (Full Feature Breakdown)

### 1. 100% Standalone & Truly Portable Core
- Runs directly from the project directory without requiring root access or conflicting with systemd services.
- **Zero External Python Dependencies:** The entire suite (proxies, bridges, CLI, diagnostics, tests) runs purely on the standard Python 3 library (`socket`, `socketserver`, `select`, `urllib`, `re`, `unittest`). No `pip install` required.
- **Bundled Runtime Libraries:** Automatically bundles dynamic shared libraries (such as `libevent-2.1.so.7` in `bin/lib/`) and manages `LD_LIBRARY_PATH` seamlessly so it runs on any Linux distribution (Ubuntu 20.04/22.04/24.04, Debian, Fedora, Arch, etc.).

### 2. Multi-Mode Pluggable Transports (Strategy Pattern)
- **Snowflake (Iran Optimized - Recommended):** Routes traffic via ephemeral WebRTC browser proxies with Azure Edge CDN Domain Fronting (`ajax.aspnetcdn.com -> snowflake-broker.azureedge.net`) and low-latency, responsive STUN servers (`antisip.com`, `dus.net`, `blackberry.com`, `sonetel.com`).
- **WebTunnel:** Disguises Tor traffic as standard encrypted HTTPS web traffic to bypass Deep Packet Inspection (DPI).
- **Obfs4:** Scrambles network traffic into random-looking bytes using custom credentials.
- **Direct Mode:** Direct Tor network connection for servers or unrestricted networks.

### 3. Automated Online Bridge Fetcher (`BridgeFetcher`)
- **Bypasses BridgeDB Blocking:** Since `bridges.torproject.org` is blocked by Iranian ISPs, `BridgeFetcher` routes requests through unblocked HTTP debug relays (`httpdebugger.com`) to extract fresh Obfs4 and WebTunnel bridges without requiring an active VPN.
- **Interactive Auto-Fetch:** Integrated into both the CLI (`torpro fetch obfs4`) and the interactive TUI menu.
- **Diagnostic Logging:** Automatically logs raw response previews into `logs/bridge_fetch_debug.html` for complete transparency.

### 4. Built-in Dual Proxy Engine (SOCKS5 + HTTP/HTTPS)
- **SOCKS5 Proxy:** `127.0.0.1:9050`
- **HTTP / HTTPS Proxy:** `http://127.0.0.1:8118` (Pure Python asynchronous threaded server supporting HTTP `CONNECT` tunneling with remote DNS resolution to prevent DNS leaks).

### 5. Pre-Flight Doctor Diagnostic Health Checks (5 Core Tests)
- `[1] File & Directory Permissions:` Automatically checks and enforces `+x` on executables and write permissions on `data/` and `logs/`.
- `[2] CPU Architecture Compatibility:` Validates binary ELF headers against host CPU architecture (`x86_64` / `aarch64`).
- `[3] Binary Checksum Verification:` Cryptographic SHA256 integrity verification against `bin/checksums.sha256`.
- `[4] Missing Shared Libraries (ldd):` Inspects dynamic linker resolution and verifies execution of binaries.
- `[5] Corrupted Config Verification:` Runs `tor --verify-config` pre-flight validation before launching to catch bad bridge lines or syntax errors immediately.

### 6. Network Circumvention Diagnostics (`test_iran_bypass.py`)
- Standalone diagnostic script that probes:
  - Snowflake broker endpoints and Domain Fronting responsiveness.
  - STUN WebRTC UDP reachability.
  - Tor Directory Authorities and BridgeDB reachability.
  - Generates ISP-specific transport recommendations.

### 7. Desktop & Terminal System Proxy Integration
- **1-Click Desktop Proxy:** Toggle GNOME / desktop system proxy instantly (`torpro proxy on` / `torpro proxy off`).
- **Terminal Proxy Script:** Automatically generates `env.sh` for sourcing proxy environment variables in bash/zsh (`source env.sh on` / `source env.sh off`).

### 8. Global System-Wide CLI & Desktop Shortcut
- Installable via `./install.sh` to `/usr/local/bin/torpro` and `~/.local/bin/torpro`.
- Desktop application shortcut created at `~/.local/share/applications/torpro.desktop`.
- Callable from any folder in terminal simply by typing `torpro`.

### 9. Interactive TUI Dashboard (`menu.sh` / `torpro menu`)
- Visual terminal interface with ASCII art banner, service status indicators, live bootstrap percentage progress bar, bridge transport selector, and log viewer.

### 10. Software Engineering Standards & Unit Tests
- Implements **OOP**, **SOLID** principles, **DRY**, and strict **PEP 8** style guidelines with static type annotations.
- Includes 14 automated unit tests running in `tests/` (`python3 -m unittest discover tests/`).

---

## Quick Start Guide

### 1. Download & Initialize Binaries
```bash
./setup.sh
```

### 2. Install Globally on System
```bash
sudo ./install.sh
```

### 3. Launch Interactive Menu
```bash
torpro
# or locally:
./menu.sh
```

---

## Complete CLI Reference

| Command | Description |
| :--- | :--- |
| `torpro` | Launch the interactive TUI dashboard |
| `torpro start snowflake` | Start Tor with Snowflake (Iran-optimized) |
| `torpro start webtunnel` | Start Tor with WebTunnel transport |
| `torpro start obfs4` | Start Tor with Obfs4 transport |
| `torpro start direct` | Start Tor without bridges |
| `torpro stop` | Stop Tor daemon and HTTP proxy server |
| `torpro restart [mode]` | Restart Tor service with selected transport |
| `torpro status` | Display status of Tor, HTTP proxy, and system proxy |
| `torpro doctor` | Execute 5 pre-flight diagnostic health checks |
| `torpro fetch obfs4` | Auto-fetch fresh Obfs4 bridges via unblocked relay |
| `torpro fetch webtunnel` | Auto-fetch fresh WebTunnel bridges |
| `torpro test` | Test Tor network connectivity and display Exit IP |
| `torpro proxy on` | Enable GNOME desktop system proxy |
| `torpro proxy off` | Disable GNOME desktop system proxy |
| `torpro logs` | Tail live Tor connection logs |

---

## Project Directory Structure

```text
Portable-Tor/
├── bin/                       # Standalone binaries & shared libraries
│   ├── tor                    # Tor core binary
│   ├── snowflake-client       # Snowflake pluggable transport
│   ├── lyrebird               # Lyrebird (Obfs4 & WebTunnel transport)
│   ├── lib/                   # Bundled shared libraries (libevent-2.1.so.7)
│   └── checksums.sha256       # SHA256 cryptographic references
├── config/                    # Configuration directory (ignored by git)
│   ├── torrc.base             # Base Tor directives with absolute paths
│   └── custom_bridges.txt     # Custom / fetched bridge lines
├── data/                      # Tor session cache and keys
├── logs/                      # Tor, HTTP proxy, and bridge fetch logs
├── torpro/                    # Core Python Package (OOP + SOLID + PEP8)
│   ├── core/                  # Constants, exceptions, logger, subprocess runner
│   ├── diagnostics/           # 5 Diagnostic health tests & Doctor engine
│   ├── bridges/               # Snowflake, Obfs4, WebTunnel, Direct, BridgeFetcher
│   ├── proxy/                 # HTTP-to-SOCKS5 server & System proxy manager
│   ├── service/               # Daemon process controller & connection tester
│   └── cli/                   # CLI command dispatcher & TUI dashboard
├── tests/                     # Automated unit test suite
│   ├── test_diagnostics.py
│   ├── test_bridges.py
│   └── test_proxy.py
├── setup.sh                   # Automated binary setup script
├── install.sh                 # Global system installer
├── uninstall.sh               # Global uninstaller
├── tor.sh                     # CLI launcher script
├── menu.sh                    # TUI menu launcher script
├── test_iran_bypass.py        # Network & transport diagnostics tool
├── env.sh                     # Terminal proxy environment script
├── .gitignore                 # Git ignore file
└── README.md                  # Documentation
```

---

## Author & Framework

- **Author:** `amin.baranzehi_`
- **Framework:** Advanced Privacy & Security Framework
- **License:** MIT License
