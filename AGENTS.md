# AGENTS.md

Guidance for coding agents working in this repository.

## Overview

Config for AVKEAN Search, a public SearXNG instance. It runs the official `searxng/searxng` image. Requests go through the reverse proxy to Anubis (`searxng-anubis`), then SearXNG (`searxng`). Valkey (`searxng-valkey`) backs the SearXNG limiter and Anubis.

- `Dockerfile`: official image; changes the Source code link and links `branding/avkean.css` into the stock theme's `base.html`.
- `settings.yml`: overrides on top of the SearXNG defaults.
- `anubis-policy.yml`: Anubis rules. Static files and `/autocompleter` skip the challenge.
- `limiter.toml`: SearXNG limiter.
- `favicons.toml`: keeps the site icon cache on the cache volume, since `/tmp` is a small tmpfs.
- `branding/`: the look. `avkean.css` restyles SearXNG's stock theme (colours through its CSS variables, light and dark follow the device), `index.html` is the homepage and `searxng-wordmark.min.svg` is the header logo. The reverse proxy serves the other files in place of the stock theme images.
- `update.sh`: rebuilds on the latest images and rolls back if `smoke-test.sh` fails. It runs nightly from cron. If searches already fail before the update, only the local checks decide it.
- `check-search-quality.py`: real searches through MetaCrawler and the default engines. `smoke-test.sh` runs it.

Secrets are in `.env`, which is not committed.

## Rules

- Google's results are what make the results good. They come from MetaCrawler (System1), plus Google's Programmable Search until its whole-web search ends on 1 Jan 2027. Google itself blocks almost every request from anything that isn't a full browser; the stock engine stays on so an upstream fix arrives with the nightly update.
- Test real queries after changing engines, and keep test query volume low. Never test Google from a home connection.
- Prefer settings over code or template overrides. Keep changes small.
- Style through `avkean.css`, not by copying templates: copied templates break when SearXNG updates. Check light, dark and phone width after a change.
- Don't publish ports. Only Anubis is on `proxy_net`.
- Google must go out over IPv6. That's why the Google engine uses SearXNG's `ipv6` network, and why `searxng_net` uses a slice of the server's IPv6 range, which `limiter.toml` trusts. Google gives the server's IPv4 address much worse results.

## Checks

Run after any change:

```
./smoke-test.sh
```

After changing `Dockerfile` or `compose.yml`, run `docker compose up -d --build` first.
