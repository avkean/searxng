"""Search quality checks, with and without Google."""
import urllib.parse
import urllib.request
from lxml import html


def search(**params):
    url = 'http://127.0.0.1:8080/search?' + urllib.parse.urlencode(params)
    body = urllib.request.urlopen(url, timeout=25).read()
    dom = html.fromstring(body)
    return dom.xpath('//article[contains(@class,"result")]')


results = search(q='chinese character count', language='en-SG', safesearch=0)
assert len(results) >= 5, 'Default search returned fewer than five results'
urls = [r.xpath('string(.//h3/a/@href)').lower() for r in results[:2]]
assert any('char' in url and 'count' in url for url in urls), (
    'No character-counting tool in the first two results: ' + repr(urls)
)
print('Regional character-count search passed')

results = search(q='docker compose healthcheck', language='en', safesearch=0,
                 engines='duckduckgo web,brave')
assert len(results) >= 5, 'Search without Google returned fewer than five results'
providers = {name for r in results for name in r.xpath('.//*[contains(@class,"engines")]/span/text()')}
assert providers and providers <= {'duckduckgo web', 'brave'}, providers
assert any('docs.docker.com/reference/compose-file/services' in r.xpath('string(.//h3/a/@href)')
           for r in results[:5]), 'Docker reference missing from fallback top five'
print('Search without Google passed; contributing engines: ' + ', '.join(sorted(providers)))
