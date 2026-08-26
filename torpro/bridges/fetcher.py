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

from torpro.core.constants import CUSTOM_BRIDGES_FILE
from torpro.core.exceptions import ConfigError
from torpro.core.logger import Logger


@dataclass
class FetchResult:
    """Outcome of an automated bridge fetch attempt."""
    success: bool
    transport: str
    bridges: List[str]
    source: str
    error: Optional[str] = None


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
    def _parse_bridgelines(cls, raw_html: str, transport: str) -> List[str]:
        """Extract clean bridge lines from HTML response."""
        bridges: List[str] = []

        # 1. First level: Extract <pre> content if present
        pre_match = re.search(r"<pre[^>]*>(.*?)</pre>", raw_html, re.DOTALL | re.IGNORECASE)
        content_to_decode = pre_match.group(1) if pre_match else raw_html

        # 2. Decode HTML entities (handles &lt;div id=&quot;bridgelines&quot;&gt;, etc.)
        decoded = html.unescape(content_to_decode)
        # Second pass in case of double-encoding
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
            # Strip tags and spaces
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

        # Fallback regex over whole decoded text if lines split missed anything
        if not bridges:
            regex = cls.WEBTUNNEL_REGEX if transport.lower() == "webtunnel" else cls.OBFS4_REGEX
            for match in regex.finditer(decoded):
                b_str = match.group(1).strip()
                if not b_str.startswith("Bridge "):
                    b_str = f"Bridge {b_str}"
                if b_str not in bridges:
                    bridges.append(b_str)

        return bridges

    @classmethod
    def fetch_via_httpdebugger(cls, transport: str = "obfs4", timeout: int = 20) -> FetchResult:
        """Fetch bridges through httpdebugger.com relay."""
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
                raw_html = response.read().decode("utf-8", errors="ignore")

            bridges = cls._parse_bridgelines(raw_html, transport)

            if bridges:
                return FetchResult(
                    success=True,
                    transport=transport,
                    bridges=bridges,
                    source="httpdebugger.com Relay",
                )

            # Check if Captcha challenge was returned
            decoded_preview = html.unescape(raw_html[:2000]).lower()
            if "captcha" in decoded_preview:
                return FetchResult(
                    success=False,
                    transport=transport,
                    bridges=[],
                    source="httpdebugger.com",
                    error="Captcha requested by Tor BridgeDB (Server rate limited). Try again in a few minutes.",
                )

            return FetchResult(
                success=False,
                transport=transport,
                bridges=[],
                source="httpdebugger.com",
                error="No bridge lines found in response body (BridgeDB might be temporarily empty or rate-limited).",
            )

        except urllib.error.URLError as err:
            return FetchResult(
                success=False,
                transport=transport,
                bridges=[],
                source="httpdebugger.com",
                error=f"Connection to relay failed: {err.reason}",
            )
        except Exception as err:
            return FetchResult(
                success=False,
                transport=transport,
                bridges=[],
                source="httpdebugger.com",
                error=str(err),
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
