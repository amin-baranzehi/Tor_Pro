#!/usr/bin/env bash
# ==============================================================================
# Tor Pro - System-wide Global Uninstaller
# ==============================================================================
set -e

GREEN="\033[92m"
YELLOW="\033[93m"
RED="\033[91m"
BOLD="\033[1m"
RESET="\033[0m"

# 1. Root check
if [ "$EUID" -ne 0 ]; then
    echo -e "${RED}${BOLD}[ERROR] This script must be run as root.${RESET}"
    echo -e "Please run: ${YELLOW}sudo ./uninstall.sh${RESET}"
    exit 1
fi

echo -e "${YELLOW}${BOLD}Uninstalling Tor Pro global launcher and files...${RESET}"

rm -rf /opt/torpro
rm -f /usr/local/bin/torpro
rm -f /usr/share/applications/torpro.desktop
rm -f /usr/share/icons/torpro.png
rm -f /usr/share/icons/hicolor/*/apps/torpro.png 2>/dev/null || true
rm -f /usr/share/pixmaps/torpro.png

gtk-update-icon-cache -f -t /usr/share/icons/hicolor 2>/dev/null || true
update-desktop-database /usr/share/applications 2>/dev/null || true

echo -e "${GREEN}[OK] Removed /opt/torpro${RESET}"
echo -e "${GREEN}[OK] Removed /usr/local/bin/torpro${RESET}"
echo -e "${GREEN}[OK] Removed /usr/share/applications/torpro.desktop and system icons${RESET}"
echo -e "\nTor Pro has been fully uninstalled from the system."
