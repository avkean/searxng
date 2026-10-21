# AGENTS.md

Guidance for coding agents working in this repository.

## Overview

Config for AVKEAN Search, a public SearXNG instance. It runs the official `searxng/searxng` image. Requests go through the reverse proxy to Anubis (`searxng-anubis`), then SearXNG (`searxng`). SearXNG gets Google results from `searxng-google`. Valkey (`searxng-valkey`) backs the SearXNG limiter and Anubis.

- `Dockerfile`: official image; only changes the Source code link.
- `settings.yml`: overrides on top of the SearXNG defaults.
- `google_stateless.py`: Google engine. It asks `searxng-google` instead of Google, since Google blocks or sends a JavaScript check to every client that can't run JavaScript.
- `google_browser.py`: the `searxng-google` service. It runs each Google search in a fresh headless Chromium context and returns the results as JSON. Its Playwright image is pinned by version and digest; bump it by hand, keeping the `pip install playwright` version the same.
- `brave_web.py`: Brave web search read from the results page HTML. Brave only answers HTTP/3 without a 429.
- `anubis-policy.yml`: Anubis rules. Static files and `/autocompleter` skip the challenge.
- `limiter.toml`: SearXNG limiter.
- `branding/`: logo and icons. `index.html` is the homepage and `searxng-wordmark.min.svg` replaces the results-page logo. The reverse proxy serves the other files in place of the stock theme images.
- `update.sh`: rebuilds on the latest images and rolls back if `smoke-test.sh` fails. It runs nightly from cron.

Secrets are in `.env`, which is not committed.

## Rules

- Google is what makes the results good. Don't remove `google_stateless.py` or `google_browser.py`, or change how the browser searches, without testing real queries, and keep test query volume low.
- Prefer settings over code or template overrides. Keep changes small.
- Don't publish ports. Only Anubis is on `proxy_net`.

## Checks

Run after any change:

```
./smoke-test.sh
```

After changing `Dockerfile` or `compose.yml`, run `docker compose up -d --build` first.
