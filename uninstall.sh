#!/usr/bin/env bash
# ==============================================================================
# Tor Pro - System-wide Global Uninstaller
# ==============================================================================
set -e

GREEN="\033[92m"
YELLOW="\033[93m"
BOLD="\033[1m"
RESET="\033[0m"

echo -e "${YELLOW}${BOLD}Uninstalling Tor Pro global launcher...${RESET}"

rm -f "$HOME/.local/bin/torpro"
rm -f "$HOME/.local/share/applications/torpro.desktop"

echo -e "${GREEN}[OK] Removed ~/.local/bin/torpro${RESET}"
echo -e "${GREEN}[OK] Removed ~/.local/share/applications/torpro.desktop${RESET}"
echo -e "\nTor Pro project folder was not deleted and remains intact."
