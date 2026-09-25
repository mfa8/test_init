#!/usr/bin/env python3
"""Check every source for Arsenal v Everton seats in blocks under 100 at or
below the fee-inclusive price cap.

Prints a JSON report. Exit code 10 = at least one deal, 0 = none,
1 = every source failed.
"""
import importlib
import json
import pkgutil
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common import MATCH, MAX_TOTAL_USD, WANTED_TIERS  # noqa: E402
import sources  # noqa: E402


def main(only=None):
    report = {"match": MATCH, "cap_usd_all_in": MAX_TOTAL_USD,
              "deals": [], "sources": {}}
    ok = 0
    for mod_info in pkgutil.iter_modules(sources.__path__):
        if only and mod_info.name not in only:
            continue
        mod = importlib.import_module(f"sources.{mod_info.name}")
        name = getattr(mod, "NAME", mod_info.name)
        try:
            listings = mod.fetch()
        except Exception as e:  # noqa: BLE001 - one broken site must not stop the rest
            report["sources"][name] = {"status": "error",
                                       "error": f"{type(e).__name__}: {e}"[:300]}
            traceback.print_exc(file=sys.stderr)
            continue
        ok += 1
        wanted = [l for l in listings if l.tier in WANTED_TIERS
                  and l.price_usd_all_in is not None]
        cheapest = min(wanted, key=lambda l: l.price_usd_all_in, default=None)
        report["sources"][name] = {
            "status": "ok", "listings_seen": len(listings),
            "cheapest_under_100_all_in_usd": cheapest.price_usd_all_in if cheapest else None,
        }
        report["deals"] += [l.to_dict() for l in listings if l.qualifies()]
    report["deals"].sort(key=lambda d: d["price_usd_all_in"])
    print(json.dumps(report, indent=2))
    if report["deals"]:
        return 10
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(set(sys.argv[1:]) or None))
