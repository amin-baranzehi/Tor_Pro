<div align="center">

<img src="image/banner.webp" alt="Tor Pro - Advanced Anonymous Routing Network" width="100%" />

# Tor Pro — Advanced Anti-Censorship Suite

**Enterprise-grade, standalone, zero-dependency Tor circumvention suite for Linux tailored for severe censorship environments.**

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg?style=for-the-badge)](https://github.com/amin-baranzehi/Tor_Pro)
[![Python](https://img.shields.io/badge/Python-3.8%2B-brightgreen.svg?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-orange.svg?style=for-the-badge&logo=linux&logoColor=white)](https://kernel.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg?style=for-the-badge)](LICENSE)
[![Zero Dependencies](https://img.shields.io/badge/Dependencies-Zero%20External%20Pip-success.svg?style=for-the-badge)]()

[Features](#what-we-have-in-tor-pro-full-feature-breakdown) • [Quick Start](#quick-start-guide) • [CLI Reference](#complete-cli-reference) • [Architecture](#project-directory-structure)

</div>

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

### 4. Dynamic Tor IP Rotator & Circuit Renewal (`TorIpRotator`)
- **Instant IP Change (One-Shot):** Sends `SIGNAL NEWNYM` via Tor's `ControlPort 9051` to cleanly tear down old circuits and issue a brand-new Exit Node IP address (`torpro rotate` / `torpro newip`).
- **Auto IP Rotator Mode:** Automatically changes your Exit IP periodically every N seconds (e.g. every 10s, 30s, 60s) with live real-time output and country resolution (`torpro autorotate 30`).

### 5. Built-in Dual Proxy Engine (SOCKS5 + HTTP/HTTPS)
- **SOCKS5 Proxy:** `127.0.0.1:9050`
- **HTTP / HTTPS Proxy:** `http://127.0.0.1:8118` (Pure Python asynchronous threaded server supporting HTTP `CONNECT` tunneling with remote DNS resolution to prevent DNS leaks).

### 6. Pre-Flight Doctor Diagnostic Health Checks (5 Core Tests)
- `[1] File & Directory Permissions:` Automatically checks and enforces `+x` on executables and write permissions on `data/` and `logs/`.
- `[2] CPU Architecture Compatibility:` Validates binary ELF headers against host CPU architecture (`x86_64` / `aarch64`).
- `[3] Binary Checksum Verification:` Cryptographic SHA256 integrity verification against `bin/checksums.sha256`.
- `[4] Missing Shared Libraries (ldd):` Inspects dynamic linker resolution and verifies execution of binaries.
- `[5] Corrupted Config Verification:` Runs `tor --verify-config` pre-flight validation before launching to catch bad bridge lines or syntax errors immediately.

### 7. Network Circumvention Diagnostics (`test_iran_bypass.py`)
- Standalone diagnostic script that probes:
  - Snowflake broker endpoints and Domain Fronting responsiveness.
  - STUN WebRTC UDP reachability.
  - Tor Directory Authorities and BridgeDB reachability.
  - Generates ISP-specific transport recommendations.

### 8. Desktop & Terminal System Proxy Integration
- **1-Click Desktop Proxy:** Toggle GNOME / desktop system proxy instantly (`torpro proxy on` / `torpro proxy off`).
- **Terminal Proxy Script:** Automatically generates `env.sh` for sourcing proxy environment variables in bash/zsh (`source env.sh on` / `source env.sh off`).

### 9. Global System-Wide CLI & Desktop Shortcut
- Installable via `./install.sh` to `/usr/local/bin/torpro` and `~/.local/bin/torpro`.
- Desktop application shortcut created at `~/.local/share/applications/torpro.desktop`.
- Callable from any folder in terminal simply by typing `torpro`.

### 10. Interactive TUI Dashboard (`menu.sh` / `torpro menu`)
- Visual terminal interface with ASCII art banner, service status indicators, live bootstrap percentage progress bar, bridge transport selector, and log viewer.

### 11. Software Engineering Standards & Unit Tests
- Implements **OOP**, **SOLID** principles, **DRY**, and strict **PEP 8** style guidelines with static type annotations.
- Includes 17 automated unit tests running in `tests/` (`python3 -m unittest discover tests/`).

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
sudo torpro
# or locally:
sudo ./menu.sh
```

---

## Complete CLI Reference

| Command | Description |
| :--- | :--- |
| `sudo torpro` | Launch the interactive TUI dashboard |
| `sudo torpro start snowflake` | Start Tor with Snowflake (Iran-optimized) |
| `sudo torpro start webtunnel` | Start Tor with WebTunnel transport |
| `sudo torpro start obfs4` | Start Tor with Obfs4 transport |
| `sudo torpro start direct` | Start Tor without bridges |
| `sudo torpro stop` | Stop Tor daemon and HTTP proxy server |
| `sudo torpro restart [mode]` | Restart Tor service with selected transport |
| `sudo torpro status` | Display status of Tor, HTTP proxy, and system proxy |
| `sudo torpro rotate` / `sudo torpro newip` | Request a new IP address / circuit right now |
| `sudo torpro autorotate [seconds]` | Periodically rotate IP address every N seconds (e.g. `sudo torpro autorotate 30`) |
| `sudo torpro doctor` | Execute 5 pre-flight diagnostic health checks |
| `sudo torpro fetch obfs4` | Auto-fetch fresh Obfs4 bridges via unblocked relay |
| `sudo torpro fetch webtunnel` | Auto-fetch fresh WebTunnel bridges |
| `sudo torpro test` | Test Tor network connectivity and display Exit IP |
| `sudo torpro proxy on` | Enable GNOME desktop system proxy |
| `sudo torpro proxy off` | Disable GNOME desktop system proxy |
| `sudo torpro logs` | Tail live Tor connection logs |

---

## Project Directory Structure

```text
Tor-Pro/
├── image/                     # Media & asset repository (Banners, Logos, Icons)
│   ├── banner.webp            # GitHub repository wide banner (2816x1536)
│   ├── logo.png               # High-resolution application icon (1024x1024)
│   ├── logo.webp              # WebP optimized logo (1024x1024)
│   └── logo.ico               # application icon
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
│   ├── service/               # Daemon process controller, tester & IP Rotator
│   └── cli/                   # CLI command dispatcher & TUI dashboard
├── tests/                     # Automated unit test suite (17 tests)
│   ├── test_diagnostics.py
│   ├── test_bridges.py
│   ├── test_proxy.py
│   └── test_service.py
├── setup.sh                   # Automated binary setup script
├── install.sh                 # Global system installer (with desktop icon setup)
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
