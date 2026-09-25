#!/usr/bin/env python3
"""Watch LiveFootballTickets for Arsenal v Everton seats below block 100 under a
fee-inclusive price cap.

Prints a JSON report to stdout. Exit code 0 = no deal, 10 = deal(s) found,
1 = the site could not be checked.

Emirates block numbering: lower tier = 1-32, club level = C41-C84 (both under
100). Upper tier is 91-134, so blocks 91-99 are upper tier and excluded.
"""
import json
import re
import sys
import urllib.parse
import urllib.request

MAX_TOTAL_USD = 350.0
BASE = "https://www.livefootballtickets.com"
PAGE = BASE + "/us/fixtures/arsenal-v-everton-tickets-english-premier-league.html"
EVENT_CODE = "arsenal-v-everton"
EVENT_TYPE = "english-premier-league"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/128.0 Safari/537.36")
# Categories whose blocks are all under 100. Away section excluded (Everton
# members only).
WANTED = re.compile(r"LOWER TIER|CLUB LEVEL|CANNON CLUB|DIAMOND|BOX SEATS")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def load_page_state():
    html = get(PAGE).replace('\\"', '"')
    show = re.search(r'"showData":\{"id":(\d+).*?"showDate":"([^"]+)"', html)
    i = html.find('"categories":[{')
    cats, _ = json.JSONDecoder().raw_decode(html[i + len('"categories":'):])
    wanted = [c for c in cats if WANTED.search(c["name"]) and c.get("tickets")]
    return int(show.group(1)), show.group(2), wanted


def listings(show_id, cat_id):
    page = 1
    while True:
        q = urllib.parse.urlencode({
            "eventCode": EVENT_CODE, "eventTypeCode": EVENT_TYPE,
            "locale": "en-US", "currency": "usd", "pageNumber": page,
            "category": cat_id,
            # Seller price excludes the ~30% service fee, so this is a loose
            # pre-filter; the real check uses the calculated total.
            "maxprice": int(MAX_TOTAL_USD),
        })
        t = json.loads(get(f"{BASE}/api/fixtures/{show_id}?{q}"))["tickets"]
        yield from t.get("items", [])
        if not t.get("hasNextPage"):
            return
        page += 1


def total_per_ticket(ticket_id, qty):
    d = json.loads(get(f"{BASE}/api/tickets/{ticket_id}/calculate?qty={qty}"))["ticket"]
    return round(d["total"]["usd"] / qty, 2), d


def block_ok(section):
    # Some listings name a specific block, e.g. "106 - SHORTSIDE UPPER TIER".
    m = re.match(r"\s*C?(\d+)\b", section)
    return m is None or int(m.group(1)) < 100


def main():
    report = {"site": "livefootballtickets.com", "url": PAGE, "cap_usd": MAX_TOTAL_USD}
    try:
        show_id, show_date, cats = load_page_state()
        report["show_date"] = show_date
        deals, cheapest = [], None
        for c in cats:
            cat_id = c["id"].removeprefix("C_")
            for item in listings(show_id, cat_id):
                if not block_ok(item["section"]) or "UPPER" in item["section"].upper():
                    continue
                qty = min(item["quantities"])
                per, _ = total_per_ticket(item["ticketId"], qty)
                row = {
                    "ticket_id": item["ticketId"], "category": c["name"],
                    "section": item["section"], "row": item["row"],
                    "min_qty": qty, "seller_price_usd": item["price"]["usd"],
                    "total_per_ticket_usd_incl_fees": per,
                    "seating": [o["name"] for t in item.get("ticketOptions", [])
                                for o in t["options"]],
                }
                if cheapest is None or per < cheapest["total_per_ticket_usd_incl_fees"]:
                    cheapest = row
                if per <= MAX_TOTAL_USD:
                    deals.append(row)
        report["deals"] = sorted(deals, key=lambda r: r["total_per_ticket_usd_incl_fees"])
        report["cheapest_checked_under_seller_cap"] = cheapest
    except Exception as e:  # noqa: BLE001 - report any failure to the caller
        report["error"] = f"{type(e).__name__}: {e}"
        print(json.dumps(report, indent=2))
        return 1
    print(json.dumps(report, indent=2))
    return 10 if report["deals"] else 0


if __name__ == "__main__":
    sys.exit(main())
