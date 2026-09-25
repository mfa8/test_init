"""LiveFootballTickets: listing API plus the site's own fee calculator."""
import json
import re
import urllib.parse

from common import MAX_TOTAL_USD, Listing, get, get_json, tier_from_text

NAME = "livefootballtickets.com"
BASE = "https://www.livefootballtickets.com"
PAGE = BASE + "/us/fixtures/arsenal-v-everton-tickets-english-premier-league.html"
EVENT_CODE = "arsenal-v-everton"
EVENT_TYPE = "english-premier-league"
# Categories whose blocks are all under 100. Away section excluded.
WANTED = re.compile(r"LOWER TIER|CLUB LEVEL|CANNON CLUB|DIAMOND|BOX SEATS")


def _page_state():
    html = get(PAGE).replace('\\"', '"')
    show = re.search(r'"showData":\{"id":(\d+)', html)
    i = html.find('"categories":[{')
    cats, _ = json.JSONDecoder().raw_decode(html[i + len('"categories":'):])
    return int(show.group(1)), [c for c in cats if WANTED.search(c["name"]) and c.get("tickets")]


def _listings(show_id, cat_id):
    page = 1
    while True:
        q = urllib.parse.urlencode({
            "eventCode": EVENT_CODE, "eventTypeCode": EVENT_TYPE,
            "locale": "en-US", "currency": "usd", "pageNumber": page,
            "category": cat_id,
            # Seller price excludes the ~30% fee, so this only pre-filters;
            # the real check uses the calculated total.
            "maxprice": int(MAX_TOTAL_USD),
        })
        t = get_json(f"{BASE}/api/fixtures/{show_id}?{q}")["tickets"]
        yield from t.get("items", [])
        if not t.get("hasNextPage"):
            return
        page += 1


def fetch():
    show_id, cats = _page_state()
    out = []
    for c in cats:
        for item in _listings(show_id, c["id"].removeprefix("C_")):
            label = f'{item["section"]} ({c["name"]})'
            tier = tier_from_text(item["section"]) if re.match(r"\s*C?\d", item["section"]) \
                else tier_from_text(c["name"])
            qty = min(item["quantities"])
            calc = get_json(f'{BASE}/api/tickets/{item["ticketId"]}/calculate?qty={qty}')["ticket"]
            block = re.match(r"\s*(C?\d+)", item["section"])
            out.append(Listing(
                site=NAME, tier=tier, section=label,
                price_usd_all_in=round(calc["total"]["usd"] / qty, 2),
                url=PAGE, block=block.group(1) if block else None,
                row=item["row"], min_qty=qty,
                note=", ".join(o["name"] for t in item.get("ticketOptions", [])
                               for o in t["options"]),
                extra={"ticket_id": item["ticketId"],
                       "seller_price_usd": item["price"]["usd"]},
            ))
    return out
