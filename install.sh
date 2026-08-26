#!/usr/bin/env bash
# ==============================================================================
# Tor Pro - System-wide Global Installer
# ==============================================================================
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

GREEN="\033[92m"
CYAN="\033[96m"
YELLOW="\033[93m"
RED="\033[91m"
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

# Determine target directories
# If run as root or sudo, install to /usr/local/bin (available in system-wide PATH)
if [ "$EUID" -eq 0 ] || [ -n "$SUDO_USER" ]; then
    SYSTEM_BIN="/usr/local/bin"
    WRAPPER_PATH="$SYSTEM_BIN/torpro"
    
    # Also resolve real user home
    REAL_USER="${SUDO_USER:-$USER}"
    REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)
else
    SYSTEM_BIN=""
    REAL_USER="$USER"
    REAL_HOME="$HOME"
    WRAPPER_PATH="$REAL_HOME/.local/bin/torpro"
fi

echo -e "${BOLD}[1/3] Creating global CLI executable 'torpro'...${RESET}"

# Create launcher script
create_wrapper() {
    local target="$1"
    mkdir -p "$(dirname "$target")"
    cat << EOF > "$target"
#!/usr/bin/env bash
TOR_PRO_DIR="$DIR"
cd "\$TOR_PRO_DIR"
exec python3 -m torpro.cli.main "\$@"
EOF
    chmod +x "$target"
}

# Install to /usr/local/bin if root/sudo, and ~/.local/bin for current user
if [ -n "$SYSTEM_BIN" ] && [ -w "$SYSTEM_BIN" ]; then
    create_wrapper "/usr/local/bin/torpro"
    echo -e "${GREEN}[OK] Installed system-wide: /usr/local/bin/torpro${RESET}"
fi

# Always install to user's local bin as well
USER_LOCAL_BIN="$REAL_HOME/.local/bin"
mkdir -p "$USER_LOCAL_BIN"
create_wrapper "$USER_LOCAL_BIN/torpro"
chown -R "$REAL_USER:$REAL_USER" "$USER_LOCAL_BIN/torpro" 2>/dev/null || true
echo -e "${GREEN}[OK] Installed for user $REAL_USER: $USER_LOCAL_BIN/torpro${RESET}"

# 2. PATH Verification
echo -e "\n${BOLD}[2/3] Checking PATH environment...${RESET}"
if [[ ":$PATH:" != *":$USER_LOCAL_BIN:"* ]] && [[ ":$PATH:" != *":/usr/local/bin:"* ]]; then
    echo -e "${YELLOW}[NOTICE] $USER_LOCAL_BIN is not in current PATH. Adding to shell rc files...${RESET}"
    
    for rc in "$REAL_HOME/.bashrc" "$REAL_HOME/.zshrc"; do
        if [ -f "$rc" ]; then
            if ! grep -q '.local/bin' "$rc"; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
                echo -e "${GREEN}[OK] Added ~/.local/bin to $rc${RESET}"
            fi
        fi
    done
else
    echo -e "${GREEN}[OK] PATH environment verified.${RESET}"
fi

# 3. Desktop Application Entry
echo -e "\n${BOLD}[3/3] Creating Desktop Application Shortcut...${RESET}"
DESKTOP_DIR="$REAL_HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat << EOF > "$DESKTOP_DIR/torpro.desktop"
[Desktop Entry]
Name=Tor Pro
Comment=Professional Standalone Tor Suite
Exec=$USER_LOCAL_BIN/torpro menu
Icon=security-high
Terminal=true
Type=Application
Categories=Network;Security;
EOF

chmod +x "$DESKTOP_DIR/torpro.desktop"
chown -R "$REAL_USER:$REAL_USER" "$DESKTOP_DIR/torpro.desktop" 2>/dev/null || true
echo -e "${GREEN}[OK] Created desktop shortcut: $DESKTOP_DIR/torpro.desktop${RESET}"

echo -e "\n${GREEN}${BOLD}========================================================================${RESET}"
echo -e "${GREEN}${BOLD}Tor Pro has been successfully installed globally!${RESET}"
echo -e "You can now run ${CYAN}${BOLD}torpro${RESET} from ANY directory in your terminal:"
echo -e "  * ${CYAN}torpro${RESET}             -> Open Interactive TUI Dashboard"
echo -e "  * ${CYAN}torpro start${RESET}       -> Start Tor with Snowflake"
echo -e "  * ${CYAN}torpro stop${RESET}        -> Stop Tor and Proxies"
echo -e "  * ${CYAN}torpro doctor${RESET}      -> Run 5 Diagnostic Health Checks"
echo -e "  * ${CYAN}torpro test${RESET}        -> Test Tor Connection & Check IP"
echo -e "  * ${CYAN}torpro proxy on/off${RESET} -> Toggle Desktop System Proxy"
echo -e "${GREEN}${BOLD}========================================================================${RESET}\n"
