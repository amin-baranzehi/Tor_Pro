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

    # Regex patterns for obfs4 and webtunnel
    OBFS4_REGEX = re.compile(
        r"(?:Bridge\s+)?(obfs4\s+\d+\.\d+\.\d+\.\d+:\d+\s+[A-F0-9]{40}\s+cert=[^\s]+(?:\s+iat-mode=\d)?)",
        re.IGNORECASE,
    )
    WEBTUNNEL_REGEX = re.compile(
        r"(?:Bridge\s+)?(webtunnel\s+[^<\r\n]+)",
        re.IGNORECASE,
    )

    @classmethod
    def fetch_via_httpdebugger(cls, transport: str = "obfs4", timeout: int = 15) -> FetchResult:
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
        }

        req = urllib.request.Request(cls.HTTP_DEBUGGER_URL, data=post_data, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw_html = response.read().decode("utf-8", errors="ignore")

            # Decode HTML entities
            decoded = html.unescape(raw_html)

            # Extract bridges
            bridges: List[str] = []
            if transport.lower() == "webtunnel":
                matches = cls.WEBTUNNEL_REGEX.findall(decoded)
            else:
                matches = cls.OBFS4_REGEX.findall(decoded)

            for match in matches:
                clean = match.strip()
                # Remove any leftover HTML tags
                clean = re.sub(r"<[^>]+>", "", clean).strip()
                if clean:
                    if not clean.startswith("Bridge "):
                        clean = f"Bridge {clean}"
                    if clean not in bridges:
                        bridges.append(clean)

            if bridges:
                return FetchResult(
                    success=True,
                    transport=transport,
                    bridges=bridges,
                    source="httpdebugger.com Relay",
                )

            # Check if captcha or empty
            if "captcha" in decoded.lower():
                return FetchResult(
                    success=False,
                    transport=transport,
                    bridges=[],
                    source="httpdebugger.com",
                    error="Captcha requested by BridgeDB. Try again shortly.",
                )

            return FetchResult(
                success=False,
                transport=transport,
                bridges=[],
                source="httpdebugger.com",
                error="No bridge lines found in response body.",
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
