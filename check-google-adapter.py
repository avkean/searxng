"""Offline checks for google_stateless.py. Doesn't send anything to Google."""

from urllib.parse import urlsplit, parse_qs
from curl_cffi import CurlOpt
from searx import settings, network
from searx.engines import load_engines, engines
from searx.engines import google as upstream
from searx.search.processors.online import default_request_params

load_engines([entry for entry in settings["engines"] if entry["name"] == "google"])
network.initialize()
engine = engines["google"]
transport = network.get_network("google")
assert engine.engine == "google_stateless"
assert transport.verify is True, "TLS certificate verification must remain enabled"
assert transport.enable_http2 is True and transport.enable_http3 is False
assert transport.local_addresses == "::" and transport.retries == 0

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
    actual_query = parse_qs(urlsplit(params["url"]).query, keep_blank_values=True)
    expected_query = parse_qs(urlsplit(expected["url"]).query, keep_blank_values=True)
    assert actual_query.pop("cr") == [""], "Country must not restrict search results"
    assert actual_query.pop("gl") == [engine.traits.get_region(locale, "") or ""]
    expected_query.pop("cr", None)
    assert actual_query == expected_query, "Query, language, paging or filters changed"
    assert params["curl_options"][CurlOpt.FRESH_CONNECT] == 1
    assert params["curl_options"][CurlOpt.FORBID_REUSE] == 1
    assert params["curl_options"][CurlOpt.SSL_SESSIONID_CACHE] == 0
    assert params["curl_options"][CurlOpt.COOKIELIST] == "ALL"

print("Google adapter compatibility checks passed (no upstream queries)")
