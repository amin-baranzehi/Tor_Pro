#!/bin/bash
# Usage: source env.sh on  |  source env.sh off
ACTION="${1:-on}"

if [ "$ACTION" = "on" ]; then
    export http_proxy="http://127.0.0.1:8118"
    export https_proxy="http://127.0.0.1:8118"
    export HTTP_PROXY="http://127.0.0.1:8118"
    export HTTPS_PROXY="http://127.0.0.1:8118"
    export all_proxy="socks5h://127.0.0.1:9050"
    export ALL_PROXY="socks5h://127.0.0.1:9050"
    echo "[Tor Pro] Terminal proxy ENABLED (HTTP: 8118, SOCKS5: 9050)"
else
    unset http_proxy https_proxy HTTP_PROXY HTTPS_PROXY all_proxy ALL_PROXY
    echo "[Tor Pro] Terminal proxy DISABLED"
fi
