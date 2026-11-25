"""Search quality checks. Each sends one query to the engines it names."""
import urllib.parse
import urllib.request
from curl_cffi import requests
from lxml import html


def search(**params):
    url = 'http://127.0.0.1:8080/search?' + urllib.parse.urlencode(params)
    body = urllib.request.urlopen(url, timeout=25).read()
    dom = html.fromstring(body)
    return dom.xpath('//article[contains(@class,"result")]')


def links(results):
    return [r.xpath('string(.//h3/a/@href)') for r in results]


results = search(q='chinese character count', language='en-SG', safesearch=0)
assert len(results) >= 5, 'Default search returned fewer than five results'
urls = [url.lower() for url in links(results)[:2]]
assert any('char' in url and 'count' in url for url in urls), (
    'No character-counting tool in the first two results: ' + repr(urls)
)
print('Regional character-count search passed')

# MetaCrawler is where the Google results come from. System1 runs sites on
# Yahoo too, so check it still serves Google's block.
page = requests.get('https://search.metacrawler.com/serp?q=docker+compose+healthcheck',
                    impersonate='chrome', timeout=15).text
assert 'web-google' in page, 'MetaCrawler no longer serves Google results'
results = search(q='docker compose healthcheck', language='en', safesearch=0, engines='metacrawler')
assert len(results) >= 5, 'MetaCrawler returned fewer than five results'
assert any('docs.docker.com/reference/compose-file/services' in url for url in links(results)[:3]), (
    'Docker reference missing from the MetaCrawler top three'
)
print('MetaCrawler search passed')

results = search(q='docker compose healthcheck', language='en', safesearch=0, engines='duckduckgo web')
assert len(results) >= 5, 'DuckDuckGo returned fewer than five results'
assert any('docs.docker.com/reference/compose-file/services' in url for url in links(results)[:5]), (
    'Docker reference missing from the DuckDuckGo top five'
)
print('DuckDuckGo search passed')
