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

**Tor Pro** is a modern, standalone, zero-dependency Tor circumvention suite for Linux designed for heavy censorship environments. It provides out-of-the-box pluggable transport support (**Snowflake**, **WebTunnel**, **Obfs4**), a pure Python **HTTP-to-SOCKS5** dual proxy bridge, 5 pre-flight diagnostic health checks (**Doctor Suite**), and an interactive **TUI Dashboard**.

---

## Key Features

1. **Standalone & Truly Portable:**
   - Runs directly from the project directory without requiring root access or conflicting with systemd.
   - Zero external Python pip dependencies (uses 100% standard library).

2. **Multi-Mode Anti-Censorship Transports (Strategy Pattern):**
   - **Snowflake (Default):** Bypasses blocking via WebRTC ephemeral browser proxies.
   - **WebTunnel:** Disguises Tor traffic as standard HTTPS web browsing.
   - **Obfs4:** Obfuscated bridge transport with custom credentials.
   - **Direct:** Direct Tor network connection for unrestricted networks.

3. **Built-in Dual Proxy Engine:**
   - **SOCKS5 Proxy:** `127.0.0.1:9050`
   - **HTTP/HTTPS Proxy:** `http://127.0.0.1:8118` (Pure Python asynchronous bridge with remote DNS leak prevention).

4. **Doctor Health Diagnostic Suite (5 Core Checks):**
   - `test binary checksum`: Cryptographic SHA256 integrity verification.
   - `test permissions`: Automatic verification and enforcement of executable (`+x`) and write permissions.
   - `test architecture`: Validates ELF binary headers against host CPU architecture (`x86_64` / `aarch64`).
   - `test missing dependencies`: Dynamic library analysis via `ldd` and execution tests.
   - `test corrupted config`: Pre-flight configuration validation with `tor --verify-config`.

5. **Desktop & Terminal Proxy Integration:**
   - 1-Click GNOME / Desktop proxy toggle (`torpro proxy on` / `torpro proxy off`).
   - Automatic `env.sh` generator for terminal proxy exports (`source env.sh on`).

6. **Global CLI & Desktop App:**
   - Run `torpro` from any directory in your terminal or launch it from your Linux application menu.

---

## Quick Start & Installation

### 1. Download & Initialize Standalone Binaries
```bash
./setup.sh
```

### 2. Install Globally (Callable from anywhere)
```bash
./install.sh
```
After installation, you can run `torpro` from any terminal session:
```bash
torpro
```

### 3. Interactive TUI Menu
```bash
torpro menu
# or locally:
./menu.sh
```

---

## CLI Usage Reference

```bash
# Start Tor with Snowflake transport (Default)
torpro start snowflake

# Start Tor with WebTunnel / Obfs4 / Direct
torpro start webtunnel
torpro start obfs4
torpro start direct

# Stop Tor and all proxy bridges
torpro stop

# Restart Tor service
torpro restart snowflake

# View active status and ports
torpro status

# Run 5 diagnostic health checks (Doctor)
torpro doctor

# Test connection & inspect Exit Node IP
torpro test

# Toggle desktop system proxy
torpro proxy on
torpro proxy off

# Tail live connection logs
torpro logs
```

---

## Software Architecture & Design Principles

The project strictly follows software engineering best practices:
- **OOP (Object-Oriented Programming):** Clean class encapsulation across `torpro/core`, `torpro/diagnostics`, `torpro/bridges`, `torpro/proxy`, `torpro/service`, and `torpro/cli`.
- **SOLID Principles:**
  - **Single Responsibility:** Distinct modules for process control, diagnostics, bridge strategies, and proxy tunneling.
  - **Open/Closed:** Diagnostic tests and bridge transports implement abstract base classes (`BaseDiagnosticTest`, `BaseBridgeStrategy`) and can be extended without altering existing code.
  - **Liskov Substitution & Interface Segregation:** Subclasses are fully interchangeable in the engine registries.
  - **Dependency Inversion:** High-level CLI dispatchers depend on abstract strategies and service controllers.
- **DRY (Don't Repeat Yourself):** Centralized paths, constants, logging formatters, and process execution utilities.
- **PEP 8 & Type Safety:** 100% compliant with standard Python style guides and explicit type annotations.

---

## Project Structure

```text
Portable-Tor/
├── bin/                       # Standalone binaries & SHA256 checksums
│   ├── tor
│   ├── snowflake-client
│   ├── lyrebird
│   └── checksums.sha256
├── config/                    # Base configuration and custom bridge files
│   ├── torrc.base
│   └── custom_bridges.txt
├── data/                      # Tor session cache and keys
├── logs/                      # Tor and HTTP proxy log files
├── torpro/              # Core Python package
│   ├── core/                  # Constants, exceptions, logger, subprocess runner
│   ├── diagnostics/           # 5 Diagnostic tests & Doctor engine
│   ├── bridges/               # Snowflake, Obfs4, WebTunnel, Direct strategies
│   ├── proxy/                 # HTTP-to-SOCKS5 server & System proxy manager
│   ├── service/               # Process controller & connection tester
│   └── cli/                   # Command-line dispatcher & TUI dashboard
├── tests/                     # Automated unit test suite
│   ├── test_diagnostics.py
│   ├── test_bridges.py
│   └── test_proxy.py
├── setup.sh                   # Automated binary setup script
├── install.sh                 # System-wide global installer
├── uninstall.sh               # Global uninstaller
├── tor.sh                     # CLI launcher
├── menu.sh                    # TUI menu launcher
├── env.sh                     # Terminal proxy environment script
└── README.md                  # Documentation
```

---

## Author & License

- **Author:** `amin.baranzehi_`
- **Framework:** Laboratory & Security Framework
- **License:** MIT License
