# SPDX-License-Identifier: AGPL-3.0-or-later
"""Google engine that starts fresh for every request.

Reusing cookies, TLS sessions and connections kept getting CAPTCHAs.
"""

from curl_cffi import CurlOpt as _CurlOpt
from searx.engines import google as _google

about = _google.about
categories = _google.categories
paging = _google.paging
max_page = _google.max_page
time_range_support = _google.time_range_support
language_support = _google.language_support
safesearch = _google.safesearch
response = _google.response
fetch_traits = _google.fetch_traits

user_agent = (
    "Nokia7610/2.0 (5.0509.0) SymbianOS/7.0s Series60/2.1 "
    "Profile/MIDP-2.0 Configuration/CLDC-1.0"
)


def request(query, params):
    # For locales like en-SG, prefer local results instead of only
    # returning results from that country (cr=countrySG).
    region = traits.get_region(params["searxng_locale"], "") or ""
    _google.google_request(
        query, params, eng_traits=traits, extra_args={"cr": "", "gl": region}
    )
    params["headers"]["User-Agent"] = user_agent
    params["curl_options"] = {
        **params.get("curl_options", {}),
        _CurlOpt.FRESH_CONNECT: 1,
        _CurlOpt.FORBID_REUSE: 1,
        _CurlOpt.SSL_SESSIONID_CACHE: 0,
        _CurlOpt.COOKIELIST: "ALL",
    }
