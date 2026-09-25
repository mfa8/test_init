# Ticket watch: Arsenal v Everton (Emirates, 24 Oct 2026)

`watch.py` checks every module in `sources/` for seats in blocks under 100
(lower tier 1-32, club level C41-C84; away blocks 20-23 excluded) whose **total
per ticket including fees** is at or below $350 USD.

```
python3 ticket_watch/watch.py        # all sources
python3 ticket_watch/watch.py lft    # just one
# exit 10 = deal found, 0 = no deal, 1 = every source failed
```

It prints a JSON report with the deals, and per source whether it ran and the
cheapest fee-inclusive price it saw under block 100. One broken site never
stops the others.

## Adding a source

Drop a module in `sources/` with a `NAME` and a `fetch() -> list[Listing]`
(see `common.py`). Only fill `price_usd_all_in` when the fees are known; a
listing without a fee-inclusive price never counts as a deal.

| Source | How |
|---|---|
| `lft` | LiveFootballTickets listing API, with fees from the site's own `/api/tickets/{id}/calculate` endpoint so the total matches checkout |

A Claude Code Routine runs this hourly and sends a push notification when a
deal turns up.
