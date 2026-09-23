# searxng

Config for [AVKEAN Search](https://searxng.avkean.com), my public SearXNG instance.

It runs the official SearXNG image, with a few changes. Parts of the setup are adapted from [priv.au](https://priv.au) ([privau/searxng](https://github.com/privau/searxng)).

- a Google engine (`google_stateless.py`) that doesn't reuse connections, cookies or TLS sessions, since the default one kept hitting CAPTCHAs on my server
- [Anubis](https://github.com/TecharoHQ/anubis) in front of SearXNG
- my logo on the homepage

## Running it

Set `SEARXNG_SECRET` and `ANUBIS_ED25519_KEY` in `.env`, then:

```
docker compose up -d --build
```

Anubis is the only service on `proxy_net`, which is where the reverse proxy reaches it. The homepage logo is mounted from `../../infra/anubis-assets`, so change or remove that mount if you use this elsewhere.

`update.sh` rebuilds on the latest SearXNG image and rolls back if `smoke-test.sh` fails.

## Issues

Open them on the [GitHub mirror](https://github.com/avkean/searxng/issues). The main repo is on [git.avkean.com](https://git.avkean.com/avkean/searxng).

## License

AGPL-3.0, same as SearXNG.
