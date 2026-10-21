"""Small HTTP service that runs Google searches in headless Chromium.

Google only serves results to clients that pass its JavaScript check, so the
Google engine asks this service instead of Google. Every search gets a fresh
browser context, so no cookies or storage carry over between searches.

GET /search?q=...&hl=...&lr=...&gl=...&start=...&tbs=...&safe=...
returns {"results": [{"url", "title", "content"}], "suggestions": [...]}
or {"captcha": true} when Google answers with its CAPTCHA page.
"""

import asyncio
import json
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from playwright.async_api import async_playwright

PARAMS = ("q", "hl", "lr", "cr", "gl", "start", "tbs", "safe")
MAX_PAGES = 4
TIMEOUT_MS = 8000

EXTRACT = """() => {
  const results = [...document.querySelectorAll('#rso a h3')].map(h => {
    const a = h.closest('a');
    let box = a;
    while (box.parentElement && box.parentElement.id !== 'rso' && !box.matches('.MjjYud')) box = box.parentElement;
    const snippet = box.querySelector('.VwiC3b, [data-sncf]');
    return {href: a.getAttribute('href'), title: h.innerText, content: snippet ? snippet.innerText : ''};
  });
  const suggestions = [...document.querySelectorAll('#bres a[href^="/search?"]')].map(a => a.innerText);
  return {results, suggestions};
}"""

playwright = None
browser = None
user_agent = None
slots = asyncio.Semaphore(MAX_PAGES)


async def get_browser():
    global browser, user_agent
    if browser is None or not browser.is_connected():
        browser = await playwright.chromium.launch(
            channel="chromium", args=["--disable-blink-features=AutomationControlled"]
        )
        # headless Chromium says HeadlessChrome, which Google sends to its CAPTCHA
        major = browser.version.split(".")[0]
        user_agent = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            f"(KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"
        )
    return browser


def clean_url(url):
    # Google adds a tracking parameter to some links, YouTube ones in particular
    parts = urlsplit(url)
    query = [(k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True) if k != "xstg"]
    return urlunsplit(parts._replace(query=urlencode(query)))


async def search(args):
    async with slots:
        context = await (await get_browser()).new_context(
            locale="en-US", user_agent=user_agent, viewport={"width": 1366, "height": 800}
        )
        try:
            page = await context.new_page()
            await page.goto("https://www.google.com/search?" + urlencode(args), wait_until="domcontentloaded")
            if "/sorry/" in page.url:
                return {"captcha": True}
            # the JavaScript check reloads the page; #botstuff closes the results page
            await page.wait_for_selector("#botstuff", state="attached", timeout=TIMEOUT_MS)
            if "/sorry/" in page.url:
                return {"captcha": True}
            found = await page.evaluate(EXTRACT)

            # result links point at google.com/goto, which redirects to the page
            async def resolve(href):
                if href and href.startswith("/goto?"):
                    try:
                        r = await context.request.get("https://www.google.com" + href, max_redirects=0, timeout=3000)
                        href = r.headers.get("location")
                    except Exception:  # pylint: disable=broad-except
                        return None
                return clean_url(href) if href and href.startswith("http") else None

            urls = await asyncio.gather(*(resolve(r["href"]) for r in found["results"]))
            results, seen = [], set()
            for r, url in zip(found["results"], urls):
                if url and url not in seen:
                    seen.add(url)
                    results.append({"url": url, "title": r["title"], "content": r["content"]})
            return {"results": results, "suggestions": found["suggestions"]}
        finally:
            await context.close()


async def handle(reader, writer):
    status, body = 500, {}
    try:
        line = (await reader.readline()).decode()
        while (await reader.readline()) not in (b"\r\n", b"\n", b""):
            pass
        target = urlsplit(line.split(" ")[1])
        if target.path == "/healthz":
            await get_browser()
            status, body = 200, {"ok": True}
        elif target.path == "/search":
            args = {k: v for k, v in parse_qsl(target.query) if k in PARAMS and v}
            status, body = 200, await search(args)
        else:
            status = 404
    except Exception as e:  # pylint: disable=broad-except
        # log the error type only, never the query
        print(f"search failed: {type(e).__name__}", file=sys.stderr, flush=True)
        status, body = 502, {}
    data = json.dumps(body).encode()
    writer.write(
        f"HTTP/1.1 {status} X\r\nContent-Type: application/json\r\n"
        f"Content-Length: {len(data)}\r\nConnection: close\r\n\r\n".encode() + data
    )
    await writer.drain()
    writer.close()


async def main():
    global playwright
    playwright = await async_playwright().start()
    await get_browser()
    server = await asyncio.start_server(handle, None, 8080)
    async with server:
        await server.serve_forever()


asyncio.run(main())
