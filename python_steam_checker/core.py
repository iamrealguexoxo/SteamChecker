import re
import html as htmllib
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import requests


@dataclass
class CheckResult:
    id: str
    status: str  # OK | GELÖSCHT | NO_TITLE | FEHLER | TIMEOUT
    title_with_mod: Optional[str]
    warning: Optional[str]
    error: Optional[str]
    mod_ids: Optional[List[str]]


class SteamWorkshopCore:
    def __init__(self, timeout: float = 12.0, delay_seconds: float = 0.6):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.timeout = timeout
        self.delay_seconds = delay_seconds
        self.workshop_results: Dict[str, List[str]] = {}  # workshopId -> [modIds]

    def check_many(self, ids: List[str]) -> List[CheckResult]:
        self.workshop_results.clear()
        results: List[CheckResult] = []

        for wid in ids:
            res = self._check_one(wid)
            if res.mod_ids:
                # keep mapping for later comparisons
                self.workshop_results[wid] = res.mod_ids
            results.append(res)
            time.sleep(self.delay_seconds)

        return results

    def check_many_iter(self, ids: List[str]):
        """Generator that yields (index, total, CheckResult) for streaming UIs."""
        self.workshop_results.clear()
        total = len(ids)
        for idx, wid in enumerate(ids, 1):
            res = self._check_one(wid)
            if res.mod_ids:
                self.workshop_results[wid] = res.mod_ids
            yield idx, total, res
            time.sleep(self.delay_seconds)

    def _check_one(self, workshop_id: str) -> CheckResult:
        url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={workshop_id}"
        try:
            r = self.session.get(url, timeout=self.timeout)

            if r.status_code == 404:
                return CheckResult(workshop_id, "GELÖSCHT", None, None, None, None)

            html = r.text

            if "This item has been deleted" in html or "removed from the workshop" in html:
                return CheckResult(workshop_id, "GELÖSCHT", None, None, None, None)

            title = self._extract_title(html)
            if not title:
                return CheckResult(workshop_id, "NO_TITLE", None, None, None, None)

            # Some deleted/private items render a generic title that should not be treated as OK
            title = htmllib.unescape(title.strip())
            low_title = title.lower()
            if "project zomboid :: steam community" in low_title:
                return CheckResult(workshop_id, "GELÖSCHT", None, None, None, None)

            mod_ids = self._extract_mod_ids(html)
            if mod_ids:
                # Decode entities and trim whitespace; keep original order and uniqueness
                cleaned: List[str] = []
                for m in mod_ids:
                    mm = htmllib.unescape(m).strip()
                    if mm and mm not in cleaned:
                        cleaned.append(mm)
                mod_ids = cleaned or None

            final_title = title
            if mod_ids:
                final_title = f"{title} [ID: {';'.join(mod_ids)}]"

            warning = None
            low_title = title.lower()
            if ("outdated" in low_title) or ("working outdated" in low_title):
                warning = "[ACHTUNG OUTDATE]"
            # B42 but not B41
            if ("B42" in title) and ("B41" not in title):
                warning = "[ANDERE VERSION]"

            return CheckResult(workshop_id, "OK", final_title, warning, None, mod_ids)

        except requests.exceptions.Timeout:
            return CheckResult(workshop_id, "TIMEOUT", None, None, "Anfrage hat zu lange gedauert", None)
        except requests.RequestException as e:
            return CheckResult(workshop_id, "FEHLER", None, None, str(e), None)
        except Exception as e:
            return CheckResult(workshop_id, "FEHLER", None, None, str(e), None)

    @staticmethod
    def _extract_title(html: str) -> Optional[str]:
        # Primary: div.workshopItemTitle
        m = re.search(r'<div\s+class="workshopItemTitle">(.*?)</div>', html, re.IGNORECASE | re.DOTALL)
        if m:
            t = m.group(1).strip()
            if t:
                return t

        # Fallback: og:title
        m = re.search(r'<meta\s+property="og:title"\s+content="(.*?)"', html, re.IGNORECASE)
        if m:
            t = m.group(1).strip()
            if t:
                return t

        return None

    @staticmethod
    def _extract_mod_ids(html: str) -> Optional[List[str]]:
        # Strategy:
        # 1. Prefer quoted Mod IDs (single or double quotes) – take full content between quotes.
        # 2. For unquoted lines, avoid grabbing entire descriptive sentences; extract tokens that look like IDs.
        # 3. Tokens considered IDs: letters/numbers/_, -, ., brackets (), [] (no spaces). If a quoted ID has spaces we keep them.
        # 4. Collect unique while preserving order.

        quoted_pat = re.compile(r'(?:<b>\s*Mod\s*ID:\s*</b>\s*=\s*|Mod\s*ID\s*:?\s*)("([^"]+)"|\'([^\']+)\')', re.IGNORECASE | re.DOTALL)
        # Capture unquoted value; we'll trim to the first ID segment and decode HTML entities.
        unquoted_pat = re.compile(
            r'(?:<b>\s*Mod\s*ID:\s*</b>\s*=\s*|Mod\s*ID\s*:?\s*)([A-Za-z0-9_\-\.\[\]\(\)&][^<\r\n]*)',
            re.IGNORECASE,
        )

        results: List[str] = []

        # 1) Quoted IDs
        for m in quoted_pat.finditer(html):
            # group(2) or group(3) depending on which quote matched
            val = m.group(2) or m.group(3) or ""
            v = val.strip()
            if v and v not in results:
                results.append(v)

        # 2) Unquoted candidates (may contain multiple tokens)
        for m in unquoted_pat.finditer(html):
            candidate = m.group(1).strip()
            if not candidate:
                continue
            # Decode HTML entities (e.g., &amp; -> &)
            candidate = htmllib.unescape(candidate)
            # Stop at known subsequent field labels to reduce over-capture
            for stopper in ["Workshop ID:", "Map Folder:", "Version:", "Mod ID:"]:
                pos = candidate.find(stopper)
                if pos > 0:
                    candidate = candidate[:pos].strip()
            # Normalize whitespace
            normalized = re.sub(r'\s+', ' ', candidate).strip()

            # Try to capture short multi-word IDs (e.g., "More Gloves") while avoiding sentences.
            words_split = normalized.split(' ')
            if 1 < len(words_split) <= 4:
                multi_match = re.fullmatch(r'[A-Za-z0-9_\-\.\[\]\(\)&]+(?:\s+[A-Za-z0-9_\-\.\[\]\(\)&]+){1,3}', normalized)
                if multi_match:
                    def _word_ok(w: str) -> bool:
                        first = w[0]
                        return first.isupper() or first.isdigit() or first in "[(&"
                    if all(_word_ok(w) for w in words_split):
                        if normalized not in results:
                            results.append(normalized)
                        continue

            if ' ' in normalized and not any(sep in normalized for sep in [';', ',', '/']):
                # Contains spaces but didn't qualify as a multi-word ID and no separators → likely descriptive text.
                continue

            # Keep only the first contiguous ID segment (may contain ';', ',', '/')
            seg_match = re.search(r'([A-Za-z0-9_\-\.\[\]\(\)&]+(?:[;,\/]\s*[A-Za-z0-9_\-\.\[\]\(\)&]+)*)', candidate)
            if not seg_match:
                continue
            segment = seg_match.group(1)
            # Split by common separators to support multiple IDs on one line
            tokens = re.split(r'[;,\/]+\s*', segment)
            for t in tokens:
                t = t.strip()
                if t and t not in results:
                    results.append(t)

        return results if results else None


def compare_mod_ids(config_ids: List[str], workshop_map: Dict[str, List[str]]) -> Tuple[List[str], List[str], List[Tuple[str, str]]]:
    """
    Returns (found, missing, extra) where:
      - found: list of config mod IDs that were present in workshop results
      - missing: list of config mod IDs that were NOT present
      - extra: list of (workshopId, modId) from workshop results that are not in config_ids
    """
    found: List[str] = []
    missing: List[str] = []
    extra: List[Tuple[str, str]] = []

    # Flatten workshop values
    workshop_values: List[str] = []
    for mids in workshop_map.values():
        for mid in mids:
            workshop_values.append(mid)

    for cid in config_ids:
        if cid in workshop_values:
            found.append(cid)
        else:
            missing.append(cid)

    for wid, mids in workshop_map.items():
        for mid in mids:
            if mid not in config_ids:
                extra.append((wid, mid))

    return found, missing, extra
