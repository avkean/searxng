# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google engine that starts fresh for every request.

Reusing cookies, TLS sessions and connections kept getting CAPTCHAs.

Google stopped serving the Nokia /wml/search page that upstream uses, so this
asks for the plain HTML page Google sends to Opera Mini instead. Adapted from
priv.au's fork (https://github.com/vojkovic/searxng, commit d8980533).
"""

from urllib.parse import unquote, urlencode

from curl_cffi import CurlOpt as _CurlOpt
from lxml import html
from searx.engines import google as _google
from searx.result_types import EngineResults
from searx.utils import eval_xpath_getindex, eval_xpath_list, extract_text

about = _google.about
categories = _google.categories
paging = _google.paging
max_page = _google.max_page
time_range_support = _google.time_range_support
language_support = _google.language_support
safesearch = _google.safesearch
fetch_traits = _google.fetch_traits

user_agent = "Opera/9.80 (Android; Opera Mini/72.0.2254/191.249; U; en) Presto/2.12.423 Version/12.16"


def request(query, params):
    google_info = _google.get_google_info(params, traits)
    # For locales like en-SG, prefer local results instead of only
    # returning results from that country (cr=countrySG).
    region = traits.get_region(params["searxng_locale"], "") or ""
    args = {
        "q": query,
        "client": "ms-opera",
        "sca_esv": "1",
        **google_info["params"],
        "cr": "",
        "gl": region,
    }
    if params["pageno"] > 1:
        args["start"] = (params["pageno"] - 1) * 10
    if params["time_range"] in _google.time_range_dict:
        args["tbs"] = "qdr:" + _google.time_range_dict[params["time_range"]]
    if params["safesearch"]:
        args["safe"] = _google.filter_mapping[params["safesearch"]]

    params["url"] = "https://www.google.com/search?" + urlencode(args)
    params["cookies"].update(google_info["cookies"])
    params["headers"].update(google_info["headers"])
    params["headers"]["User-Agent"] = user_agent
    # a Chrome TLS fingerprint doesn't match the Opera Mini user agent
    params["impersonate"] = "none"
    params["curl_options"] = {
        **params.get("curl_options", {}),
        _CurlOpt.FRESH_CONNECT: 1,
        _CurlOpt.FORBID_REUSE: 1,
        _CurlOpt.SSL_SESSIONID_CACHE: 0,
        _CurlOpt.COOKIELIST: "ALL",
    }


def _unwrap_url(raw_url):
    if raw_url.startswith("/url?") and "q=" in raw_url:
        return unquote(raw_url.split("q=", 1)[1].split("&", 1)[0])
    return raw_url


def response(resp):
    results = EngineResults()
    _google.detect_google_sorry(resp)
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[contains(@class, "Gx5Zad")]'):
        title = eval_xpath_getindex(result, './/h3[contains(@class, "zBAuLc")]', 0, default=None)
        raw_url = eval_xpath_getindex(
            result, './/a[contains(@href, "/url?") and .//h3[contains(@class, "zBAuLc")]]/@href', 0, default=None
        )
        if title is None or raw_url is None:
            continue
        url = _unwrap_url(raw_url)
        if not url.startswith("http"):
            continue
        content = eval_xpath_getindex(result, './/div[contains(@class, "H66NU")]', 0, default=None)
        results.add(
            results.types.MainResult(
                url=url,
                title=extract_text(title) or "",
                content=extract_text(content, allow_none=True) or "",
            )
        )

    for suggestion in eval_xpath_list(dom, '//a[contains(@class, "HA0EX")]'):
        results.add(results.types.LegacyResult(suggestion=extract_text(suggestion)))

    return results
