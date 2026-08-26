#!/usr/bin/env bash
# ==============================================================================
# Tor Pro - Automated Setup & Binary Downloader
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Color helpers
GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
CYAN="\033[96m"
BLUE="\033[94m"
MAGENTA="\033[95m"
WHITE="\033[97m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${RED}${BOLD}"
cat << "EOF"
  _______ ____  _____    _____  _____   ____  
 |__   __/ __ \|  __ \  |  __ \|  __ \ / __ \ 
    | | | |  | | |__) | | |__) | |__) | |  | |
    | | | |  | |  _  /  |  ___/|  _  /| |  | |
    | | | |__| | | \ \  | |    | | \ \| |__| |
    |_|  \____/|_|  \_\ |_|    |_|  \_\\____/ 
EOF
echo -e "${WHITE}========================================================================${RESET}"
echo -e "  ${BLUE}Tor Pro - Professional Anti-Censorship Tor Suite${RESET} ${YELLOW}[v2.0.0]${RESET}"
echo -e "  ${GREEN}Author: ${YELLOW}amin.baranzehi_${RESET} | ${MAGENTA}Advanced Privacy & Security Framework${RESET}"
echo -e "${WHITE}========================================================================${RESET}\n"

# 1. Architecture Check
ARCH="$(uname -m)"
echo -e "${BOLD}[1/5] Checking CPU Architecture...${RESET}"
if [ "$ARCH" != "x86_64" ] && [ "$ARCH" != "amd64" ]; then
    echo -e "${YELLOW}[WARN] Current architecture is $ARCH. Standard x86_64 binaries may need compilation.${RESET}"
else
    echo -e "${GREEN}[OK] Architecture verified: $ARCH${RESET}"
fi

# 2. Directory Creation
echo -e "\n${BOLD}[2/5] Initializing Directory Structure...${RESET}"
mkdir -p bin bin/lib config data logs
touch data/.gitkeep logs/.gitkeep
echo -e "${GREEN}[OK] Directories initialized (bin/, bin/lib/, config/, data/, logs/)${RESET}"

# 3. Binary Setup (Check or Download)
echo -e "\n${BOLD}[3/5] Checking & Downloading Standalone Binaries...${RESET}"

NEED_DOWNLOAD=0
if [ ! -f "bin/tor" ] || [ ! -f "bin/snowflake-client" ] || [ ! -f "bin/lyrebird" ] || [ "$1" == "--force" ]; then
    NEED_DOWNLOAD=1
fi

if [ "$NEED_DOWNLOAD" -eq 1 ]; then
    echo -e "${CYAN}Downloading Tor Standalone Bundle for Linux ($ARCH)...${RESET}"
    
    TMP_DIR=$(mktemp -d)
    TOR_VERSION="14.0.7"
    URL="https://archive.torproject.org/tor-package-archive/torbrowser/${TOR_VERSION}/tor-expert-bundle-linux-x86_64-${TOR_VERSION}.tar.gz"
    
    echo -e "Fetching from: ${YELLOW}$URL${RESET}"
    if curl -sL --connect-timeout 15 "$URL" -o "$TMP_DIR/tor-bundle.tar.gz"; then
        echo -e "${GREEN}[OK] Download complete. Extracting standalone binaries...${RESET}"
        tar -zxf "$TMP_DIR/tor-bundle.tar.gz" -C "$TMP_DIR"
        
        # Move binaries into bin/
        if [ -f "$TMP_DIR/tor/tor" ]; then
            cp "$TMP_DIR/tor/tor" bin/tor
        elif [ -f "$TMP_DIR/tor" ]; then
            cp "$TMP_DIR/tor" bin/tor
        fi
        
        if [ -f "$TMP_DIR/tor/pluggable_transports/snowflake-client" ]; then
            cp "$TMP_DIR/tor/pluggable_transports/snowflake-client" bin/snowflake-client
        elif [ -f "$TMP_DIR/snowflake-client" ]; then
            cp "$TMP_DIR/snowflake-client" bin/snowflake-client
        fi
        
        if [ -f "$TMP_DIR/tor/pluggable_transports/lyrebird" ]; then
            cp "$TMP_DIR/tor/pluggable_transports/lyrebird" bin/lyrebird
        elif [ -f "$TMP_DIR/lyrebird" ]; then
            cp "$TMP_DIR/lyrebird" bin/lyrebird
        fi
        
        rm -rf "$TMP_DIR"
    else
        echo -e "${RED}[FAIL] Failed to download bundle automatically.${RESET}"
        echo -e "${YELLOW}You can manually place 'tor', 'snowflake-client', and 'lyrebird' into the bin/ directory.${RESET}"
    fi
else
    echo -e "${GREEN}[OK] All binaries already present in bin/.${RESET}"
fi

# Ensure bundled libevent exists
if [ ! -f "bin/lib/libevent-2.1.so.7" ]; then
    echo -e "${CYAN}Fetching runtime shared library libevent-2.1.so.7...${RESET}"
    TMP_LIB=$(mktemp -d)
    (
        cd "$TMP_LIB"
        apt-get download libevent-2.1-7t64 2>/dev/null || apt-get download libevent-2.1-7 2>/dev/null || true
        dpkg -x *.deb . 2>/dev/null || true
    )
    if [ -f "$TMP_LIB/usr/lib/x86_64-linux-gnu/libevent-2.1.so.7" ]; then
        cp -a "$TMP_LIB"/usr/lib/x86_64-linux-gnu/libevent* bin/lib/
        echo -e "${GREEN}[OK] libevent runtime library bundled into bin/lib/${RESET}"
    fi
    rm -rf "$TMP_LIB"
fi

# 4. Permissions & Checksums
echo -e "\n${BOLD}[4/5] Setting Permissions & Calculating Integrity Checksums...${RESET}"
chmod +x bin/* 2>/dev/null || true
chmod -R 755 data logs 2>/dev/null || true

# Generate checksums file
if [ -f "bin/tor" ]; then
    (cd bin && sha256sum tor $([ -f snowflake-client ] && echo "snowflake-client") $([ -f lyrebird ] && echo "lyrebird") > checksums.sha256 2>/dev/null || true)
    echo -e "${GREEN}[OK] SHA256 checksums updated in bin/checksums.sha256${RESET}"
fi

# 5. Run Doctor Diagnostic Checks
echo -e "\n${BOLD}[5/5] Running Pre-flight Health Check (Doctor)...${RESET}"
export LD_LIBRARY_PATH="$DIR/bin/lib:$LD_LIBRARY_PATH"
python3 -m torpro.cli.main doctor || true

echo -e "\n${GREEN}${BOLD}========================================================================${RESET}"
echo -e "${GREEN}${BOLD}Tor Pro Setup Complete!${RESET}"
echo -e "  * Global Installation:      ${CYAN}./install.sh${RESET}"
echo -e "  * Interactive Dashboard:    ${CYAN}./tor.sh menu${RESET} (or ${CYAN}./menu.sh${RESET})"
echo -e "  * Immediate Start:          ${CYAN}./tor.sh start snowflake${RESET}"
echo -e "${GREEN}${BOLD}========================================================================${RESET}\n"
