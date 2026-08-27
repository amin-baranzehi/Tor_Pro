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

# 1. Root check
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}${BOLD}[ERROR] This script must be run as root.${RESET}"
    echo -e "Please run: ${YELLOW}sudo ./install.sh${RESET}"
    exit 1
fi

echo -e "${BOLD}[1/4] Installing Tor Pro to /opt/torpro...${RESET}"

# Identify calling user to clean up their old local installation
REAL_USER="${SUDO_USER:-$USER}"
REAL_HOME=$(getent passwd "$REAL_USER" 2>/dev/null | cut -d: -f6 || echo "$HOME")

# Cleanup old local installation if it exists
rm -f "$REAL_HOME/.local/bin/torpro"
rm -f "$REAL_HOME/.local/share/applications/torpro.desktop"
rm -f "$REAL_HOME/.local/share/icons/torpro.png"
rm -f "$REAL_HOME/.local/share/pixmaps/torpro.png"

mkdir -p /opt/torpro
cp -r "$DIR/"* /opt/torpro/

# Ensure permissions & user ownership on data and logs directories
mkdir -p /opt/torpro/data /opt/torpro/logs /opt/torpro/config
chmod 700 /opt/torpro/data /opt/torpro/logs 2>/dev/null || true

echo -e "${GREEN}[OK] Files copied to /opt/torpro${RESET}"

echo -e "\n${BOLD}[2/4] Creating global CLI executable 'torpro'...${RESET}"

cat << EOF > /usr/local/bin/torpro
#!/usr/bin/env bash
TOR_PRO_DIR="/opt/torpro"
export LD_LIBRARY_PATH="\$TOR_PRO_DIR/bin/lib:\$LD_LIBRARY_PATH"
cd "\$TOR_PRO_DIR"
exec python3 -m torpro.cli.main "\$@"
EOF
chmod +x /usr/local/bin/torpro

echo -e "${GREEN}[OK] Installed system-wide: /usr/local/bin/torpro${RESET}"

echo -e "\n${BOLD}[3/4] Creating Desktop Application Shortcut & Icon Theme Integration...${RESET}"
ICON_DIR="/usr/share/icons"
DESKTOP_DIR="/usr/share/applications"
PIXMAPS_DIR="/usr/share/pixmaps"

LOGO_FILE=""
if [ -f "/opt/torpro/image/logo.png" ]; then
    LOGO_FILE="/opt/torpro/image/logo.png"
elif [ -f "/opt/torpro/logo.png" ]; then
    LOGO_FILE="/opt/torpro/logo.png"
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
    gtk-update-icon-cache -f -t "$ICON_DIR/hicolor" 2>/dev/null || true
fi

cat << EOF > "$DESKTOP_DIR/torpro.desktop"
[Desktop Entry]
Name=Tor Pro
Comment=Professional Standalone Tor Suite
Exec=sudo torpro menu
Icon=torpro
Terminal=true
Type=Application
Categories=Network;Security;
EOF

chmod +x "$DESKTOP_DIR/torpro.desktop"
update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
touch "$DESKTOP_DIR/torpro.desktop"
echo -e "${GREEN}[OK] Created desktop shortcut with custom logo: $DESKTOP_DIR/torpro.desktop${RESET}"

echo -e "\n${GREEN}${BOLD}========================================================================${RESET}"
echo -e "${GREEN}${BOLD}Tor Pro has been successfully installed globally!${RESET}"
echo -e "You can now run ${CYAN}${BOLD}sudo torpro${RESET} from ANY directory in your terminal:"
echo -e "  * ${CYAN}sudo torpro${RESET}             -> Open Interactive TUI Dashboard"
echo -e "  * ${CYAN}sudo torpro start${RESET}       -> Start Tor with Snowflake"
echo -e "  * ${CYAN}sudo torpro stop${RESET}        -> Stop Tor and Proxies"
echo -e "  * ${CYAN}sudo torpro rotate${RESET}      -> Request New IP Address"
echo -e "  * ${CYAN}sudo torpro autorotate${RESET}  -> Continuously Rotate IP Address"
echo -e "  * ${CYAN}sudo torpro doctor${RESET}      -> Run 5 Diagnostic Health Checks"
echo -e "  * ${CYAN}sudo torpro test${RESET}        -> Test Tor Connection & Check IP"
echo -e "  * ${CYAN}sudo torpro proxy on/off${RESET} -> Toggle Desktop System Proxy"
echo -e "${GREEN}${BOLD}========================================================================${RESET}\n"
