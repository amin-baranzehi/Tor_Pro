#!/usr/bin/env bash
# ==============================================================================
# Tor Pro - CLI Executable Wrapper
# ==============================================================================
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
exec python3 -m torpro.cli.main "$@"
