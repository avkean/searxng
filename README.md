# searxng

Config for [AVKEAN Search](https://searxng.avkean.com), my public SearXNG instance.

It runs the official SearXNG image, with a few changes. Parts of the setup are adapted from [priv.au](https://priv.au) ([privau/searxng](https://github.com/privau/searxng)).

- a Google engine (`google_stateless.py`) that asks for Google's Opera Mini page and doesn't reuse connections, cookies or TLS sessions, since the default one kept hitting CAPTCHAs on my server and Google has since blocked the page it uses
- a Brave engine (`brave_web.py`) that reads the results page HTML over HTTP/3, since Brave changed the page data the default one reads and rate limits HTTP/2
- [Anubis](https://github.com/TecharoHQ/anubis) in front of SearXNG
- my logo and icons in place of the SearXNG ones

## Running it

Set `SEARXNG_SECRET` and `ANUBIS_ED25519_KEY` in `.env`, then:

```
docker compose up -d --build
```

Anubis is the only service on `proxy_net`, which is where the reverse proxy reaches it. The favicons and the homepage and preferences logos are served by the reverse proxy from `branding/`, so drop the `branding/` mounts if you use this elsewhere.

`update.sh` rebuilds on the latest SearXNG image and rolls back if `smoke-test.sh` fails.

## Issues

Open them on the [GitHub mirror](https://github.com/avkean/searxng/issues). The main repo is on [git.avkean.com](https://git.avkean.com/avkean/searxng).

## License

AGPL-3.0, same as SearXNG.
