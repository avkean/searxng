# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google engine with the fix from SearXNG pull request 6892, which priv.au runs.

Google blocks the stock engine's Nokia pages. Sent two old phone User-Agent
lines, it answers with a plain HTML results page instead. Drop this file once
SearXNG merges a fix.
"""

from urllib.parse import parse_qs, urlencode, urlparse

from curl_cffi import CurlOpt
from curl_cffi.const import CurlIpResolve
from lxml import html

from searx.engines import google as _google
from searx.exceptions import SearxEngineAPIException
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

# A dict would join these into one header. Order is Opera, then Samsung.
user_agents = [
    ("User-Agent", "Mozilla/4.0 (compatible; MSIE 6.0; Symbian OS; SAMSUNG-GT-S5230) Opera 8.65"),
    ("User-Agent", "SAMSUNG-GT-S5230"),
]


def request(query, params):
    google_info = _google.get_google_info(params, traits)
    # Only the interface language. Google takes the region from the server's
    # IP. Sending a region or language filter made results noticeably worse.
    args = {"q": query, "sca_esv": "1", "hl": google_info["params"]["hl"], "ie": "utf8", "oe": "utf8"}
    if params["pageno"] > 1:
        args["start"] = (params["pageno"] - 1) * 10
    if params["time_range"] in _google.time_range_dict:
        args["tbs"] = "qdr:" + _google.time_range_dict[params["time_range"]]
    if params["safesearch"]:
        args["safe"] = _google.filter_mapping[params["safesearch"]]
    params["url"] = "https://www.google.com/search?" + urlencode(args)
    params["default_headers"] = False
    params["impersonate"] = "none"
    params["headers"] = list(user_agents)
    # Google gives the server's IPv4 address much worse results
    params["curl_options"] = {CurlOpt.FORBID_REUSE: 1, CurlOpt.IPRESOLVE: CurlIpResolve.V6}


def unwrap_url(raw_url):
    target = parse_qs(urlparse(raw_url).query).get("q", [""])[0]
    # now and then Google sends encrypted /goto links, which can't be resolved here
    if target.startswith("CAES"):
        raise SearxEngineAPIException("returned goto links")
    return target if target.startswith("http") else raw_url


def response(resp):
    _google.detect_google_sorry(resp)
    results = EngineResults()
    text = resp.text
    if text.lstrip().startswith("<?xml"):
        text = text.split("?>", 1)[-1]
    dom = html.fromstring(text)
    for card in eval_xpath_list(dom, '//div[contains(@class, "zMzFAb") and .//a[contains(@class, "fuLhoc")]]'):
        url = unwrap_url(eval_xpath_getindex(card, './/a[contains(@class, "fuLhoc")]/@href', 0))
        title = extract_text(eval_xpath_getindex(card, './/span[contains(@class, "CVA68e")]', 0, default=""))
        if not title:
            continue
        content = extract_text(
            eval_xpath_getindex(
                card,
                './/span[contains(@class, "FrIlee")]/span[contains(@class, "fYyStc") and not(contains(@class, "YVIcad"))]',
                0,
                default="",
            )
        )
        results.add(results.types.MainResult(url=url, title=title, content=content))
    for suggestion in eval_xpath_list(dom, _google.suggestion_xpath):
        results.add(results.types.LegacyResult(suggestion=extract_text(suggestion)))
    return results
