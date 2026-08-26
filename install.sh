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

# 1. Target directory
TARGET_DIR="$HOME/.local/bin"
mkdir -p "$TARGET_DIR"

WRAPPER_PATH="$TARGET_DIR/torpro"

echo -e "${BOLD}[1/3] Creating global CLI command 'torpro'...${RESET}"

cat << 'EOF' > "$WRAPPER_PATH"
#!/usr/bin/env bash
TOR_PRO_DIR="REPLACE_DIR"
cd "$TOR_PRO_DIR"
exec python3 -m torpro.cli.main "$@"
EOF

# Substitute actual directory path
sed -i "s|REPLACE_DIR|$DIR|g" "$WRAPPER_PATH"
chmod +x "$WRAPPER_PATH"

echo -e "${GREEN}[OK] Created executable: $WRAPPER_PATH${RESET}"

# 2. PATH Verification
echo -e "\n${BOLD}[2/3] Checking user PATH environment...${RESET}"
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo -e "${YELLOW}[NOTICE] $HOME/.local/bin is not in your current PATH.${RESET}"
    
    # Append to .bashrc
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q 'HOME/.local/bin' "$HOME/.bashrc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo -e "${GREEN}[OK] Added ~/.local/bin to ~/.bashrc${RESET}"
        fi
    fi
    
    # Append to .zshrc
    if [ -f "$HOME/.zshrc" ]; then
        if ! grep -q 'HOME/.local/bin' "$HOME/.zshrc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
            echo -e "${GREEN}[OK] Added ~/.local/bin to ~/.zshrc${RESET}"
        fi
    fi
else
    echo -e "${GREEN}[OK] ~/.local/bin is already in PATH.${RESET}"
fi

# 3. Desktop Application Entry
echo -e "\n${BOLD}[3/3] Creating Desktop Application Shortcut...${RESET}"
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat << EOF > "$DESKTOP_DIR/torpro.desktop"
[Desktop Entry]
Name=Tor Pro
Comment=Professional Standalone Tor Suite
Exec=$WRAPPER_PATH menu
Icon=security-high
Terminal=true
Type=Application
Categories=Network;Security;
EOF

chmod +x "$DESKTOP_DIR/torpro.desktop"
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
