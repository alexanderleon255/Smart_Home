# HomeHub Free API Reference — Rev 2
_Last Updated: 2026-03-03 UTC_

This is a practical “what can I call for free?” cheat-sheet, with:
- Auth method (None vs API key vs OAuth)
- Published free-tier limits (when providers publish them)
- Local vs Cloud classification
- Example request snippets
- ASCII architecture diagrams

> Notes:
> - “Free” often means **personal/dev use** with quotas.
> - Limits change. Treat this as a starting point, not a contract.

---

## Section 10 (Data / Storage / Sync) — what those do

“Data / Storage / Sync” services (Supabase, Firebase, etc.) are basically **hosted backends** for your projects.

They give you, in one package:
- **Database** (store structured data: sensors, logs, config, history)
- **File storage** (images, clips, exports, backups)
- **Auth** (login, users, permissions)
- **Realtime sync** (push updates to your UI without you polling)
- **APIs/SDKs** (easy access from your Pi, phone app, or web dashboard)

Why you’d use them (even if you “forget the homehub”):
- Turn your Raspberry Pi projects into **real apps** (web UI + accounts + persistence)
- Store time-series logs (temps, power usage, uptime, motion events)
- Sync between devices (Pi ↔ phone ↔ laptop)
- Remote access without exposing your Pi directly to the internet (often safer)

If you want *pure local* (no cloud), you can replace these with:
- PostgreSQL / SQLite on the Pi
- File shares (SMB/NFS)
- A local web app + local auth

---

# 1) Quick Reference Table (Free / Free-tier)

Legend:
- **Local** = stays inside your LAN (no internet required after setup)
- **Cloud** = you’re calling a service on the internet
- **Hybrid** = local software + optional cloud

| API / Service | Local/Cloud | Auth | Published free-tier limits (summary) | Best for |
|---|---|---|---|---|
| Open‑Meteo | Cloud | None | Fair-use: 10,000/day; 5,000/hour; 600/min (non-commercial) | Weather widgets w/ no key |
| NWS api.weather.gov | Cloud | None | Rate limit exists but not public; “generous for typical use” | US forecasts + alerts |
| WeatherAPI.com | Cloud | API key | Monthly call quota by plan; resets monthly | Weather + extra endpoints |
| Mapbox | Cloud | API token | Free tiers vary by product/SKU; check pricing calculator | Maps + routing |
| Google Maps Platform | Cloud | API key + billing | Since Mar 1, 2025: free usage thresholds replace prior $200 credit; varies by SKU/tier | Traffic/ETA (metered) |
| Alpha Vantage | Cloud | API key | Free: 25/day and 5/min | Stocks/FX/crypto basics |
| Finnhub | Cloud | API key | Plan-based; docs note global cap + 30 calls/sec cap | Market data |
| CoinGecko | Cloud | None (public) | Public plan: ~5–15 calls/min (variable) | Crypto prices |
| NASA Open APIs | Cloud | API key (optional) | Default: 1,000/hour per key | Space/ISS/fun widgets |
| NewsAPI.org | Cloud | API key | Free dev plan: 100 requests/day (dev only) | Headlines (dev) |
| GNews | Cloud | API key | Free: 100 requests/day (dev/testing) | Headlines (dev) |
| ipify (public IP) | Cloud | None | “No limit” stated for ipify API | Get public IP |
| ExchangeRate‑API (open access endpoint) | Cloud | None | Rate-limited; recommends caching; once/hour is typically fine | Currency widget |
| Home Assistant REST API | Local | Token (local) | Local; you control it | Control local devices |
| MQTT (Mosquitto) | Local | None / user+pass | Local; you control it | Local messaging bus |
| Uptime Kuma | Local | None | Local; you control it | Status dashboards |
| Prometheus | Local | None | Local; you control it | Metrics/time-series |
| Pi-hole API | Local | Token (optional) | Local; you control it | DNS stats |
| Supabase | Cloud | API keys + JWT | Free tier limits vary; auth endpoints have rate-limits | DB + auth + sync |
| Firebase | Cloud | API keys + OAuth/JWT | Spark plan quotas vary by product; auth has published limits | DB + auth + hosting |

---

# 2) Example Request Snippets (Copy/Paste)

## Open‑Meteo (no key)
```bash
curl "https://api.open-meteo.com/v1/forecast?latitude=34.0522&longitude=-118.2437&current=temperature_2m,wind_speed_10m&hourly=temperature_2m"
```

## NWS api.weather.gov (no key, US only)
```bash
# 1) Get metadata for a lat/lon (find forecast URL)
curl "https://api.weather.gov/points/34.0522,-118.2437"

# 2) Then call the returned forecast URL (example will differ)
# curl "https://api.weather.gov/gridpoints/XXX/YYY,ZZZ/forecast"
```

## Alpha Vantage (API key)
```bash
curl "https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=MSFT&apikey=YOUR_KEY"
```

## CoinGecko (public)
```bash
curl "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
```

## NASA APOD (API key optional; DEMO_KEY works but lower limits)
```bash
curl "https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY"
```

## NewsAPI (API key)
```bash
curl -H "X-Api-Key: YOUR_KEY" "https://newsapi.org/v2/top-headlines?country=us&pageSize=5"
```

## ipify (no key)
```bash
curl "https://api.ipify.org?format=json"
```

## ExchangeRate-API (open access; cache it)
```bash
curl "https://open.er-api.com/v6/latest/USD"
```

---

# 3) Architecture Integration Diagrams (ASCII)

## A) Pure Local (best reliability)
```text
[Phone/Laptop UI]──HTTP──┐
                         │
                    [Raspberry Pi]
                    ├─ MQTT (Mosquitto)
                    ├─ Home Assistant API
                    ├─ Local DB (SQLite/Postgres)
                    └─ Dashboards (Uptime Kuma / Grafana)
                         │
                         └──LAN──[Devices]
```

## B) Cloud API Widget (weather/news/finance)
```text
[Raspberry Pi]──HTTPS──>[Cloud API Provider]
     │                     │
     ├─ cache results <─────┘
     └─ serve UI locally (browser/dashboard)
```

## C) Hybrid App Backend (Supabase/Firebase style)
```text
[Phone Web App]──HTTPS──┐
                         ├──>[Supabase/Firebase]
[Raspberry Pi]──HTTPS───┘        ├─ Auth (users)
                                 ├─ Database (history/config)
                                 └─ Storage (files)
```

## D) Safe Remote Access (recommended pattern)
```text
(Internet)
   │
[VPN: Tailscale/WireGuard]
   │
[Phone/Laptop]──VPN──[Raspberry Pi LAN]
                     └─ No port-forwarding needed
```

---

# 4) Practical Design Rules

- **Cache** every cloud call (SQLite table, Redis, or flat files).
- Refresh via **cron/systemd timer** every N minutes.
- UI reads from **local cache**, not the internet directly.
- Treat “news” APIs as **dev-only** unless you upgrade.

