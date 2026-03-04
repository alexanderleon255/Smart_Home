# HomeHub Free API Reference

*Last Updated: 2026-03-03 UTC*

This document lists free (or generous free-tier) APIs useful for a
Raspberry Pi--based HomeHub system.

------------------------------------------------------------------------

# 1. Weather APIs

## Open-Meteo

-   Free, no API key required
-   Global coverage
-   Forecast, historical weather, air quality
-   https://open-meteo.com/

## NOAA Weather API (US)

-   Free
-   Official US government data
-   Alerts, forecasts
-   https://www.weather.gov/documentation/services-web-api

## WeatherAPI (Free Tier)

-   1M calls/month free tier
-   Forecast + current
-   https://www.weatherapi.com/

------------------------------------------------------------------------

# 2. Traffic / Maps / Location

## OpenStreetMap (OSM)

-   Free, open-source map data
-   Use with Overpass API
-   https://overpass-api.de/

## Mapbox (Free Tier)

-   Free monthly map loads
-   Directions API
-   https://www.mapbox.com/

## Google Maps API (Limited Free)

-   \$200/month free credit
-   Traffic + ETA
-   https://developers.google.com/maps

------------------------------------------------------------------------

# 3. Finance / Markets

## Alpha Vantage

-   Free API key
-   Stock, crypto, forex
-   25 calls/day free
-   https://www.alphavantage.co/

## Finnhub

-   Free tier available
-   Stocks + news
-   https://finnhub.io/

## CoinGecko API

-   Free
-   Crypto pricing
-   https://www.coingecko.com/en/api

------------------------------------------------------------------------

# 4. System Monitoring / Infrastructure

## Uptime Kuma (Self-hosted)

-   Free open-source
-   Monitor services
-   https://github.com/louislam/uptime-kuma

## Prometheus (Self-hosted)

-   Metrics + monitoring
-   Free
-   https://prometheus.io/

## Pi-hole API

-   Built-in JSON API
-   DNS stats
-   https://docs.pi-hole.net/

------------------------------------------------------------------------

# 5. News / Information

## NewsAPI (Free Tier)

-   Free dev tier
-   News headlines
-   https://newsapi.org/

## GNews API

-   Free tier available
-   https://gnews.io/

------------------------------------------------------------------------

# 6. Smart Home / IoT Integration

## Home Assistant REST API

-   Local, free
-   Control devices
-   https://developers.home-assistant.io/

## MQTT (Mosquitto Broker)

-   Free, local messaging protocol
-   https://mosquitto.org/

## TP-Link Kasa Local API (Unofficial)

-   Free
-   Local control
-   Community libraries

------------------------------------------------------------------------

# 7. Astronomy / Space

## NASA Open APIs

-   Free
-   ISS location, astronomy picture, etc.
-   https://api.nasa.gov/

## Open Notify

-   Free
-   ISS location
-   http://open-notify.org/

------------------------------------------------------------------------

# 8. AI / Local Compute

## Ollama (Local LLM)

-   Free
-   Runs LLM locally
-   https://ollama.com/

## OpenRouter (Free credits sometimes)

-   AI API gateway
-   https://openrouter.ai/

------------------------------------------------------------------------

# 9. Utilities

## IPify

-   Free public IP lookup
-   https://www.ipify.org/

## OpenWeather Air Pollution API (via Open-Meteo alt)

-   Air quality data

## ExchangeRate API (Free Tier)

-   Currency conversion
-   https://www.exchangerate-api.com/

------------------------------------------------------------------------

# 10. Data / Storage / Sync

## Supabase (Free Tier)

-   Database + Auth
-   https://supabase.com/

## Firebase (Free Tier)

-   Realtime DB
-   https://firebase.google.com/

------------------------------------------------------------------------

# Suggested High-Value Stack for HomeHub

-   Weather: Open-Meteo
-   Traffic ETA: Mapbox or Google (free credit)
-   Finance Widget: Alpha Vantage
-   DNS Monitoring: Pi-hole API
-   System Metrics: Prometheus
-   Messaging: MQTT
-   AI Assistant: Ollama (local)

------------------------------------------------------------------------

# Notes

-   Always review API rate limits.
-   Prefer local APIs when possible.
-   Avoid cloud dependency for critical home functions.
-   Store API keys securely (environment variables).
