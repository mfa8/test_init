# Ticket watch: Arsenal v Everton (Emirates, 24 Oct 2026)

`arsenal_everton.py` checks LiveFootballTickets for seats in blocks under 100
(lower tier 1-32, club level C41-C84) whose **total per ticket including the
service fee** is at or below $350 USD. The fee (~30%) comes from the site's own
`/api/tickets/{id}/calculate` endpoint, so the total matches checkout.

```
python3 ticket_watch/arsenal_everton.py   # exit 0 = no deal, 10 = deal, 1 = error
```

It runs on a schedule from a Claude Code Routine, which also checks SeatPick,
StubHub and viagogo by hand when those sites can be reached, and sends a push
notification when a deal turns up.
