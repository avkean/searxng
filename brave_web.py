# SPDX-License-Identifier: AGPL-3.0-or-later
"""Brave web search, read from the results page HTML.

Brave now wraps the page data upstream reads in JavaScript functions, and
answers 429 to anything but HTTP/3. The results are still plain HTML.
"""

from urllib.parse import urlencode

from curl_cffi import CurlHttpVersion, CurlOpt
from lxml import html
from searx import locales
from searx.engines import brave as _brave
from searx.result_types import EngineResults
from searx.utils import eval_xpath_getindex, eval_xpath_list, extract_text

about = _brave.about
categories = ["general", "web"]
paging = True
max_page = _brave.max_page
time_range_support = True
safesearch = True
fetch_traits = _brave.fetch_traits


def request(query, params):
    args = {"q": query, "source": "web"}
    if params["pageno"] > 1:
        args["offset"] = params["pageno"] - 1
    if params["time_range"] in _brave.time_range_map:
        args["tf"] = _brave.time_range_map[params["time_range"]]
    params["url"] = "https://search.brave.com/search?" + urlencode(args)

    region = traits.get_region(params["searxng_locale"], "all")
    params["cookies"].update(
        {
            "safesearch": _brave.safesearch_map.get(params["safesearch"], "off"),
            "useLocation": "0",
            "summarizer": "0",
            "country": region.split("-")[-1].lower(),
            "ui_lang": locales.get_engine_locale(params["searxng_locale"], traits.custom["ui_lang"], "en-us"),
        }
    )
    params["curl_options"] = {
        CurlOpt.HTTP_VERSION: CurlHttpVersion.V3ONLY,
        CurlOpt.FORBID_REUSE: 1,
    }


def response(resp):
    results = EngineResults()
    dom = html.fromstring(resp.text)

    for result in eval_xpath_list(dom, '//div[contains(@class, "snippet") and @data-type="web"]'):
        url = eval_xpath_getindex(result, ".//a/@href", 0, default="")
        title = eval_xpath_getindex(result, './/*[contains(@class, "search-snippet-title")]', 0, default=None)
        if not url.startswith("http") or title is None:
            continue
        content = eval_xpath_getindex(
            result, './/*[contains(@class, "generic-snippet")]//*[contains(@class, "content")]', 0, default=None
        )
        results.add(
            results.types.MainResult(
                url=url,
                title=extract_text(title) or "",
                content=extract_text(content, allow_none=True) or "",
            )
        )

    return results
