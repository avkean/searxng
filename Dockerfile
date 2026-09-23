FROM docker.io/searxng/searxng:latest

RUN sed -i \
    -e 's|^GIT_URL = .*|GIT_URL = "https://git.avkean.com/avkean/searxng"|' \
    -e 's|^GIT_BRANCH = .*|GIT_BRANCH = "main"|' \
    searx/version_frozen.py
