"""Offline checks for google_dual_ua.py. Doesn't send anything to Google."""

from urllib.parse import urlsplit, parse_qs
from curl_cffi import CurlOpt
from curl_cffi.const import CurlIpResolve
from searx import settings
from searx.engines import load_engines, engines
from searx.search.processors.online import default_request_params

load_engines([entry for entry in settings["engines"] if entry["name"] == "google"])
engine = engines["google"]
assert engine.engine == "google_dual_ua"

for locale, page, time_range, safe in (
    ("all", 1, None, 0),
    ("en", 2, "week", 1),
    ("en-SG", 1, "month", 2),
):
    params = default_request_params()
    params.update(searxng_locale=locale, pageno=page, time_range=time_range, safesearch=safe)
    engine.request("searxng documentation", params)
    url = urlsplit(params["url"])
    assert (url.netloc, url.path) == ("www.google.com", "/search")
    query = parse_qs(url.query)
    assert query["q"] == ["searxng documentation"]
    # only the interface language, no region or language filter
    assert not {"lr", "cr", "gl"} & query.keys(), query
    assert query.get("start") == (["10"] if page == 2 else None)
    assert ("tbs" in query) == bool(time_range)
    assert ("safe" in query) == bool(safe)
    assert [name for name, _ in params["headers"]] == ["User-Agent", "User-Agent"]
    assert params["curl_options"][CurlOpt.IPRESOLVE] == CurlIpResolve.V6

print("Google engine checks passed (no upstream queries)")
