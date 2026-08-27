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

# Identify calling user
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6 || echo "$HOME")

# Ensure permissions & user ownership on data and logs directories
mkdir -p "$DIR/data" "$DIR/logs" "$DIR/config"
chown -R "$REAL_USER:$REAL_USER" "$DIR/data" "$DIR/logs" "$DIR/config" 2>/dev/null || true
chmod 700 "$DIR/data" "$DIR/logs" 2>/dev/null || true

create_wrapper() {
    local target_path="$1"
    mkdir -p "$(dirname "$target_path")"
    cat << EOF > "$target_path"
#!/usr/bin/env bash
TOR_PRO_DIR="$DIR"
export LD_LIBRARY_PATH="\$TOR_PRO_DIR/bin/lib:\$LD_LIBRARY_PATH"
cd "\$TOR_PRO_DIR"
exec python3 -m torpro.cli.main "\$@"
EOF
    chmod +x "$target_path"
}

echo -e "${BOLD}[1/3] Creating global CLI executable 'torpro'...${RESET}"

# If running as root / sudo, install into /usr/local/bin for immediate system PATH availability
if [ "$EUID" -eq 0 ] || [ -w "/usr/local/bin" ]; then
    create_wrapper "/usr/local/bin/torpro"
    echo -e "${GREEN}[OK] Installed system-wide: /usr/local/bin/torpro${RESET}"
fi

# Always install to real user's ~/.local/bin
USER_LOCAL_BIN="$REAL_HOME/.local/bin"
mkdir -p "$USER_LOCAL_BIN"
create_wrapper "$USER_LOCAL_BIN/torpro"
chown -R "$REAL_USER:$REAL_USER" "$USER_LOCAL_BIN/torpro" 2>/dev/null || true
echo -e "${GREEN}[OK] Installed for user $REAL_USER: $USER_LOCAL_BIN/torpro${RESET}"

# 2. PATH Verification
echo -e "\n${BOLD}[2/3] Checking PATH environment...${RESET}"
for rc in "$REAL_HOME/.bashrc" "$REAL_HOME/.profile" "$REAL_HOME/.zshrc"; do
    if [ -f "$rc" ]; then
        if ! grep -q 'HOME/.local/bin' "$rc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$rc"
            chown "$REAL_USER:$REAL_USER" "$rc" 2>/dev/null || true
            echo -e "${GREEN}[OK] Added ~/.local/bin to $rc${RESET}"
        fi
    fi
done

# 3. Desktop Application Entry & Multi-Resolution Icon Set
echo -e "\n${BOLD}[3/3] Creating Desktop Application Shortcut & Icon Theme Integration...${RESET}"
ICON_DIR="$REAL_HOME/.local/share/icons"
DESKTOP_DIR="$REAL_HOME/.local/share/applications"
PIXMAPS_DIR="$REAL_HOME/.local/share/pixmaps"
mkdir -p "$ICON_DIR" "$DESKTOP_DIR" "$PIXMAPS_DIR"

LOGO_FILE=""
if [ -f "$DIR/image/logo.png" ]; then
    LOGO_FILE="$DIR/image/logo.png"
elif [ -f "$DIR/logo.png" ]; then
    LOGO_FILE="$DIR/logo.png"
fi

if [ -n "$LOGO_FILE" ]; then
    # Generate standard icon sizes for GNOME / GTK theme engine
    python3 -c "
import os
try:
    from PIL import Image
    src = '$LOGO_FILE'
    base = '$ICON_DIR/hicolor'
    sizes = [16, 24, 32, 48, 64, 96, 128, 256, 512]
    img = Image.open(src)
    for s in sizes:
        td = os.path.join(base, f'{s}x{s}', 'apps')
        os.makedirs(td, exist_ok=True)
        img.resize((s, s), Image.Resampling.LANCZOS).save(os.path.join(td, 'torpro.png'), 'PNG')
except Exception:
    pass
" 2>/dev/null || true

    cp "$LOGO_FILE" "$ICON_DIR/torpro.png" 2>/dev/null || true
    cp "$LOGO_FILE" "$PIXMAPS_DIR/torpro.png" 2>/dev/null || true
    chown -R "$REAL_USER:$REAL_USER" "$ICON_DIR" "$PIXMAPS_DIR" 2>/dev/null || true
    gtk-update-icon-cache -f -t "$ICON_DIR/hicolor" 2>/dev/null || true
fi

cat << EOF > "$DESKTOP_DIR/torpro.desktop"
[Desktop Entry]
Name=Tor Pro
Comment=Professional Standalone Tor Suite
Exec=$USER_LOCAL_BIN/torpro menu
Icon=torpro
Terminal=true
Type=Application
Categories=Network;Security;
EOF

chmod +x "$DESKTOP_DIR/torpro.desktop"
chown -R "$REAL_USER:$REAL_USER" "$DESKTOP_DIR/torpro.desktop" 2>/dev/null || true
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
touch "$DESKTOP_DIR/torpro.desktop"
echo -e "${GREEN}[OK] Created desktop shortcut with custom logo: $DESKTOP_DIR/torpro.desktop${RESET}"

echo -e "\n${GREEN}${BOLD}========================================================================${RESET}"
echo -e "${GREEN}${BOLD}Tor Pro has been successfully installed globally!${RESET}"
echo -e "You can now run ${CYAN}${BOLD}torpro${RESET} from ANY directory in your terminal:"
echo -e "  * ${CYAN}torpro${RESET}             -> Open Interactive TUI Dashboard"
echo -e "  * ${CYAN}torpro start${RESET}       -> Start Tor with Snowflake"
echo -e "  * ${CYAN}torpro stop${RESET}        -> Stop Tor and Proxies"
echo -e "  * ${CYAN}torpro rotate${RESET}      -> Request New IP Address"
echo -e "  * ${CYAN}torpro autorotate${RESET}  -> Continuously Rotate IP Address"
echo -e "  * ${CYAN}torpro doctor${RESET}      -> Run 5 Diagnostic Health Checks"
echo -e "  * ${CYAN}torpro test${RESET}        -> Test Tor Connection & Check IP"
echo -e "  * ${CYAN}torpro proxy on/off${RESET} -> Toggle Desktop System Proxy"
echo -e "${GREEN}${BOLD}========================================================================${RESET}\n"
