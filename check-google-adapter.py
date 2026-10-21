"""Offline checks for google_stateless.py. Doesn't send anything to Google."""

from urllib.parse import urlsplit, parse_qs
from searx import settings
from searx.engines import load_engines, engines
from searx.engines import google as upstream
from searx.search.processors.online import default_request_params

load_engines([entry for entry in settings["engines"] if entry["name"] == "google"])
engine = engines["google"]
assert engine.engine == "google_stateless"

for locale, page, time_range, safe in (
    ("all", 1, None, 0),
    ("en", 2, "week", 1),
    ("en-SG", 1, "month", 2),
):
    params = default_request_params()
    params.update(searxng_locale=locale, pageno=page, time_range=time_range, safesearch=safe)
    expected = {**params, "headers": {}}
    upstream.google_request("searxng documentation", expected, eng_traits=engine.traits)
    engine.request("searxng documentation", params)
    actual_url = urlsplit(params["url"])
    assert (actual_url.netloc, actual_url.path) == ("searxng-google:8080", "/search")
    actual_query = parse_qs(actual_url.query)
    expected_query = parse_qs(urlsplit(expected["url"]).query)
    for key in ("q", "hl", "start", "tbs", "safe"):
        assert actual_query.pop(key, None) == expected_query.get(key), key + " changed"
    assert not actual_query, actual_query

print("Google adapter compatibility checks passed (no upstream queries)")
