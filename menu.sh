#!/usr/bin/env bash
# ==============================================================================
# Tor Pro - Interactive TUI Menu Launcher
# ==============================================================================
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
export LD_LIBRARY_PATH="$DIR/bin/lib:$LD_LIBRARY_PATH"
cd "$DIR"
exec python3 -m torpro.cli.main menu
