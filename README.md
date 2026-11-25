# searxng

Config for [AVKEAN Search](https://searxng.avkean.com), my public SearXNG instance.

It runs the official SearXNG image, with a few changes. Parts of the setup are adapted from [priv.au](https://priv.au) ([privau/searxng](https://github.com/privau/searxng)).

- Google's results through MetaCrawler and Google's Programmable Search, since Google blocks SearXNG's own Google engine almost every time
- [Anubis](https://github.com/TecharoHQ/anubis) in front of SearXNG
- a compact look (`branding/avkean.css`) on top of the stock theme, with my logo and icons

## Running it

Set `SEARXNG_SECRET` and `ANUBIS_ED25519_KEY` in `.env`, then:

```
docker compose up -d --build
```

Anubis is the only service on `proxy_net`, which is where the reverse proxy reaches it. The favicons and the homepage and preferences logos are served by the reverse proxy from `branding/`, so drop the `branding/` mounts if you use this elsewhere.

`update.sh` rebuilds on the latest SearXNG image and rolls back if `smoke-test.sh` fails. If searches already fail before the update, only the local checks decide it, so an outside outage doesn't hold back updates.

## Issues

Open them on the [GitHub mirror](https://github.com/avkean/searxng/issues). The main repo is on [git.avkean.com](https://git.avkean.com/avkean/searxng).

## License

AGPL-3.0, same as SearXNG.
