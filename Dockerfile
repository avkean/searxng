FROM docker.io/searxng/searxng:latest

RUN sed -i \
    -e 's|^GIT_URL = .*|GIT_URL = "https://git.avkean.com/avkean/searxng"|' \
    -e 's|^GIT_BRANCH = .*|GIT_BRANCH = "main"|' \
    searx/version_frozen.py

# avkean.css restyles the stock theme. It loads after SearXNG's own CSS.
# avkean.js nests results from the same site.
COPY branding/avkean.css branding/avkean.js searx/static/themes/simple/
RUN sed -i \
    -e "/filename='sxng-ltr.min.css'/a\\  <link rel=\"stylesheet\" href=\"{{ url_for('static', filename='avkean.css') }}\" type=\"text/css\" media=\"screen\">" \
    -e "/filename='sxng-core.min.js'/a\\  <script src=\"{{ url_for('static', filename='avkean.js') }}\" defer></script>" \
    searx/templates/simple/base.html \
 && grep -q "filename='avkean.css'" searx/templates/simple/base.html \
 && grep -q "filename='avkean.js'" searx/templates/simple/base.html
