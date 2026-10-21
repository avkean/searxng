# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google engine that reads results through the searxng-google service.

Google now blocks or sends a JavaScript check to every client that can't run
JavaScript, including the Nokia and Opera Mini pages. searxng-google
(google_browser.py) runs each search in a fresh headless Chromium context, so
nothing carries over between searches.
"""

from urllib.parse import urlencode

from searx.engines import google as _google
from searx.exceptions import SearxEngineCaptchaException
from searx.result_types import EngineResults

about = _google.about
categories = _google.categories
paging = _google.paging
max_page = _google.max_page
time_range_support = _google.time_range_support
language_support = _google.language_support
safesearch = _google.safesearch
fetch_traits = _google.fetch_traits

base_url = "http://searxng-google:8080/search?"


def request(query, params):
    google_info = _google.get_google_info(params, traits)
    # For locales like en-SG, prefer local results instead of only
    # returning results from that country (cr=countrySG).
    region = traits.get_region(params["searxng_locale"], "") or ""
    args = {
        "q": query,
        "hl": google_info["params"]["hl"],
        "lr": google_info["params"]["lr"],
        "gl": region,
    }
    if params["pageno"] > 1:
        args["start"] = (params["pageno"] - 1) * 10
    if params["time_range"] in _google.time_range_dict:
        args["tbs"] = "qdr:" + _google.time_range_dict[params["time_range"]]
    if params["safesearch"]:
        args["safe"] = _google.filter_mapping[params["safesearch"]]
    params["url"] = base_url + urlencode(args)


def response(resp):
    results = EngineResults()
    data = resp.json()
    if data.get("captcha"):
        raise SearxEngineCaptchaException()
    for item in data["results"]:
        results.add(results.types.MainResult(url=item["url"], title=item["title"], content=item["content"]))
    for suggestion in data["suggestions"]:
        results.add(results.types.LegacyResult(suggestion=suggestion))
    return results
