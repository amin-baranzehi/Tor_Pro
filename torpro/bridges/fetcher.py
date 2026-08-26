"""Automated Anti-Censorship Bridge Fetcher for Tor Pro.

Fetches fresh Obfs4 and WebTunnel bridges through external unblocked HTTP proxy
relays (e.g. httpdebugger.com) to bypass ISP-level blocking of bridges.torproject.org.
Follows zero-dependency standards (Pure Python 3 standard library).
"""

from dataclasses import dataclass
import html
from pathlib import Path
import re
from typing import List, Optional, Tuple
import urllib.parse
import urllib.request

from torpro.core.constants import CUSTOM_BRIDGES_FILE, LOGS_DIR
from torpro.core.exceptions import ConfigError
from torpro.core.logger import Logger

FETCH_DEBUG_LOG = LOGS_DIR / "bridge_fetch_debug.html"


@dataclass
class FetchResult:
    """Outcome of an automated bridge fetch attempt."""
    success: bool
    transport: str
    bridges: List[str]
    source: str
    error: Optional[str] = None
    debug_log_path: Optional[Path] = None


class BridgeFetcher:
    """Fetches and parses fresh Tor bridges using unblocked HTTP debug relays."""

    HTTP_DEBUGGER_URL = "https://www.httpdebugger.com/Tools/ViewHttpHeaders.aspx"
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

    # Regex patterns for bridge lines
    OBFS4_REGEX = re.compile(
        r"(?:Bridge\s+)?(obfs4\s+\d+\.\d+\.\d+\.\d+:\d+\s+[A-F0-9]{40}\s+cert=[A-Za-z0-9+/=]+(?:\s+iat-mode=\d)?)",
        re.IGNORECASE,
    )
    WEBTUNNEL_REGEX = re.compile(
        r"(?:Bridge\s+)?(webtunnel\s+\d+\.\d+\.\d+\.\d+:\d+\s+[A-F0-9]{40}\s+url=https?://[^\s<]+(?:\s+ver=\d\.\d\.\d)?)",
        re.IGNORECASE,
    )

    @classmethod
    def _parse_bridgelines(cls, raw_html: str, transport: str) -> Tuple[List[str], str]:
        """Extract clean bridge lines from HTML response and return parsed text."""
        bridges: List[str] = []

        # 1. First level: Extract <pre> content if present
        pre_match = re.search(r"<pre[^>]*>(.*?)</pre>", raw_html, re.DOTALL | re.IGNORECASE)
        content_to_decode = pre_match.group(1) if pre_match else raw_html

        # 2. Decode HTML entities (handles &lt;div id=&quot;bridgelines&quot;&gt;, etc.)
        decoded = html.unescape(content_to_decode)
        if "&lt;" in decoded or "&gt;" in decoded or "&#" in decoded:
            decoded = html.unescape(decoded)

        # 3. Try to locate <div id="bridgelines"> or <div class="bridge-lines">
        div_match = re.search(
            r'<div[^>]*id=["\']bridgelines["\'][^>]*>(.*?)</div>',
            decoded,
            re.DOTALL | re.IGNORECASE,
        )
        search_scope = div_match.group(1) if div_match else decoded

        # 4. Split by <br>, <br/>, <br /> or newlines
        raw_lines = re.split(r"<br\s*/?>|\r?\n", search_scope, flags=re.IGNORECASE)

        for line in raw_lines:
            clean = re.sub(r"<[^>]+>", "", line).strip()
            if not clean:
                continue

            if transport.lower() == "webtunnel":
                m = cls.WEBTUNNEL_REGEX.search(clean)
            else:
                m = cls.OBFS4_REGEX.search(clean)

            if m:
                bridge_str = m.group(1).strip()
                if not bridge_str.startswith("Bridge "):
                    bridge_str = f"Bridge {bridge_str}"
                if bridge_str not in bridges:
                    bridges.append(bridge_str)

        # Fallback regex over whole decoded text
        if not bridges:
            regex = cls.WEBTUNNEL_REGEX if transport.lower() == "webtunnel" else cls.OBFS4_REGEX
            for match in regex.finditer(decoded):
                b_str = match.group(1).strip()
                if not b_str.startswith("Bridge "):
                    b_str = f"Bridge {b_str}"
                if b_str not in bridges:
                    bridges.append(b_str)

        return bridges, decoded

    @classmethod
    def fetch_via_httpdebugger(cls, transport: str = "obfs4", timeout: int = 20) -> FetchResult:
        """Fetch bridges through httpdebugger.com relay with comprehensive debug logging."""
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        target_url = f"https://bridges.torproject.org/bridges?transport={transport}"

        post_data = urllib.parse.urlencode({
            "UrlBox": target_url,
            "AgentList": "Mozilla Firefox",
            "VersionsList": "HTTP/1.1",
            "MethodList": "GET",
        }).encode("utf-8")

        headers = {
            "User-Agent": cls.USER_AGENT,
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://www.httpdebugger.com/tools/viewhttpheaders.aspx",
            "Origin": "https://www.httpdebugger.com",
        }

        req = urllib.request.Request(cls.HTTP_DEBUGGER_URL, data=post_data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status_code = response.status
                raw_html = response.read().decode("utf-8", errors="ignore")

            # Save debug response to file
            FETCH_DEBUG_LOG.write_text(raw_html, encoding="utf-8")

            bridges, decoded_text = cls._parse_bridgelines(raw_html, transport)

            # Debug log details
            Logger.debug(f"HTTP Debugger Response: HTTP {status_code} ({len(raw_html)} bytes)")
            Logger.debug(f"Saved raw HTML to: {FETCH_DEBUG_LOG}")

            if bridges:
                return FetchResult(
                    success=True,
                    transport=transport,
                    bridges=bridges,
                    source="httpdebugger.com Relay",
                    debug_log_path=FETCH_DEBUG_LOG,
                )

            # Diagnostic checks on decoded text
            lower_decoded = decoded_text.lower()
            if "captcha" in lower_decoded or "recaptcha" in lower_decoded or "challenge" in lower_decoded:
                error_msg = (
                    "Tor BridgeDB returned a Captcha challenge (Shared IP rate limit).\n"
                    "  -> BridgeDB requires solving a Captcha when queried frequently from shared proxy IPs.\n"
                    "  -> To get instant fresh bridges without Captcha, use Telegram bot: @GetBridgesBot."
                )
                return FetchResult(
                    success=False,
                    transport=transport,
                    bridges=[],
                    source="httpdebugger.com",
                    error=error_msg,
                    debug_log_path=FETCH_DEBUG_LOG,
                )

            if "403 forbidden" in lower_decoded or "access denied" in lower_decoded or "blocked" in lower_decoded:
                error_msg = "BridgeDB or Relay returned Access Denied / 403 Forbidden."
                return FetchResult(
                    success=False,
                    transport=transport,
                    bridges=[],
                    source="httpdebugger.com",
                    error=error_msg,
                    debug_log_path=FETCH_DEBUG_LOG,
                )

            # Extract snippet of decoded text for user visibility
            preview_snippet = "\n".join([line.strip() for line in decoded_text.splitlines() if line.strip()][:10])
            error_msg = (
                f"No bridge lines parsed from response ({len(raw_html)} bytes received).\n"
                f"  Debug log saved to: {FETCH_DEBUG_LOG}\n"
                f"  Response preview:\n{preview_snippet}"
            )

            return FetchResult(
                success=False,
                transport=transport,
                bridges=[],
                source="httpdebugger.com",
                error=error_msg,
                debug_log_path=FETCH_DEBUG_LOG,
            )

        except urllib.error.URLError as err:
            return FetchResult(
                success=False,
                transport=transport,
                bridges=[],
                source="httpdebugger.com",
                error=f"Network error connecting to relay: {err.reason}",
                debug_log_path=FETCH_DEBUG_LOG,
            )
        except Exception as err:
            return FetchResult(
                success=False,
                transport=transport,
                bridges=[],
                source="httpdebugger.com",
                error=f"Unexpected fetch error: {err}",
                debug_log_path=FETCH_DEBUG_LOG,
            )

    @classmethod
    def update_custom_bridges_file(cls, bridges: List[str], append: bool = False) -> Path:
        """Save fetched bridges to config/custom_bridges.txt."""
        CUSTOM_BRIDGES_FILE.parent.mkdir(parents=True, exist_ok=True)

        existing_lines = []
        if append and CUSTOM_BRIDGES_FILE.exists():
            content = CUSTOM_BRIDGES_FILE.read_text(encoding="utf-8")
            existing_lines = [l.strip() for l in content.splitlines() if l.strip()]

        combined = existing_lines[:]
        for b in bridges:
            b = b.strip()
            if b and b not in combined:
                combined.append(b)

        CUSTOM_BRIDGES_FILE.write_text("\n".join(combined) + "\n", encoding="utf-8")
        return CUSTOM_BRIDGES_FILE
