# AGENTS.md

Guidance for coding agents working in this repository.

## Overview

Config for AVKEAN Search, a public SearXNG instance. It runs the official `searxng/searxng` image. Requests go through the reverse proxy to Anubis (`searxng-anubis`), then SearXNG (`searxng`). Valkey (`searxng-valkey`) backs the SearXNG limiter and Anubis.

- `Dockerfile`: official image; only changes the Source code link.
- `settings.yml`: overrides on top of the SearXNG defaults.
- `google_dual_ua.py`: Google engine with the fix priv.au runs, from SearXNG pull request 6892. It sends two old phone User-Agent lines and gets a plain HTML results page. Drop it once SearXNG merges a fix. If Google stops answering it, the headless browser version is in git history (commit 036ac51).
- `brave_web.py`: Brave web search read from the results page HTML. Brave only answers HTTP/3 without a 429.
- `anubis-policy.yml`: Anubis rules. Static files and `/autocompleter` skip the challenge.
- `limiter.toml`: SearXNG limiter.
- `branding/`: logo and icons. `index.html` is the homepage and `searxng-wordmark.min.svg` replaces the results-page logo. The reverse proxy serves the other files in place of the stock theme images.
- `update.sh`: rebuilds on the latest images and rolls back if `smoke-test.sh` fails. It runs nightly from cron.

Secrets are in `.env`, which is not committed.

## Rules

- Google is what makes the results good. Don't change the Google engine without testing real queries, and keep test query volume low.
- Prefer settings over code or template overrides. Keep changes small.
- Don't publish ports. Only Anubis is on `proxy_net`.
- Google must go out over IPv6. That's why `google_dual_ua.py` forces IPv6, and why `searxng_net` uses a slice of the server's IPv6 range, which `limiter.toml` trusts. Google gives the server's IPv4 address much worse results.

## Checks

Run after any change:

```
./smoke-test.sh
```

After changing `Dockerfile` or `compose.yml`, run `docker compose up -d --build` first.
