"""Shared constants and helpers for the Arsenal v Everton ticket watcher.

Every source module exposes ``fetch() -> list[Listing]``. The runner merges
them, keeps listings that qualify, and prints a JSON report.
"""
import json
import re
import time
import urllib.request
from dataclasses import asdict, dataclass, field

MAX_TOTAL_USD = 350.0
MATCH = "Arsenal v Everton, Emirates Stadium, 24 Oct 2026"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")

# Emirates: lower tier blocks 1-32, club level C41-C84, upper tier 91-134.
# Away fans sit in lower-tier blocks 20-23 (Clock End, Everton members only).
LOWER = "lower"
CLUB = "club"
UPPER = "upper"
AWAY = "away"
UNKNOWN = "unknown"
WANTED_TIERS = {LOWER, CLUB}


@dataclass
class Listing:
    site: str
    tier: str                      # one of LOWER/CLUB/UPPER/AWAY/UNKNOWN
    section: str                   # site's own label, e.g. "Shortside Lower Tier"
    price_usd_all_in: float | None  # per ticket, fees included; None if unknown
    url: str
    block: str | None = None       # e.g. "11" or "C45" when the site names it
    row: str = ""
    min_qty: int = 1
    note: str = ""
    extra: dict = field(default_factory=dict)

    def qualifies(self) -> bool:
        return (self.tier in WANTED_TIERS
                and self.price_usd_all_in is not None
                and self.price_usd_all_in <= MAX_TOTAL_USD)

    def to_dict(self):
        return asdict(self)


def tier_from_text(text: str) -> str:
    """Classify a site's section label into a tier."""
    t = text.upper()
    if "AWAY" in t:
        return AWAY
    m = re.search(r"\b(?:BLOCK\s*)?(C?)(\d{1,3})\b", t)
    if m and m.group(1) == "C":
        return CLUB
    if "UPPER" in t or "LEVEL 2" in t:
        return UPPER
    if any(k in t for k in ("CLUB", "DIAMOND", "BOX", "CANNON")):
        return CLUB
    if "LOWER" in t or "LEVEL 1" in t:
        return LOWER
    if m:
        n = int(m.group(2))
        if 1 <= n <= 32:
            return AWAY if 20 <= n <= 23 else LOWER
        if 41 <= n <= 84:
            return CLUB
        if 91 <= n <= 134:
            return UPPER
    return UNKNOWN


def get(url, headers=None, timeout=30, retries=2):
    """GET with a browser UA and a couple of retries on transient errors."""
    h = {"User-Agent": UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9"}
    h.update(headers or {})
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=h)
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            last = e
            if e.code not in (429, 500, 502, 503, 504):
                raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
        time.sleep(2 * (attempt + 1))
    raise last


def get_json(url, headers=None, **kw):
    return json.loads(get(url, headers=headers, **kw))
