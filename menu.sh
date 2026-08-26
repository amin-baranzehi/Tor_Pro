#!/usr/bin/env bash
# ==============================================================================
# Tor Pro - Interactive TUI Menu Launcher
# ==============================================================================
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
exec python3 -m torpro.cli.main menu
