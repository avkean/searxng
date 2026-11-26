// Nests web results from the same site under the first one. It works on one
// loaded page of results at a time, so infinite scroll never moves what is
// already on screen. The results stay direct children of #urls, and the last
// one of each page stays put, because infinite scroll watches it to load more.
(() => {
  const MAX = 3;
  const host = (link) => {
    try {
      return new URL(link.href).hostname.replace(/^www\./, "");
    } catch {
      return "";
    }
  };

  function group(articles) {
    // moving a result counts as adding it, so mark what has been handled
    for (const article of articles) article.dataset.avkSeen = "1";
    const sites = new Map();
    for (const article of articles.slice(0, -1)) {
      if (!article.matches(".result-default.category-general")) continue;
      const link = article.querySelector("h3 a");
      const site = link && host(link);
      if (!site) continue;
      if (sites.has(site)) sites.get(site).more.push(article);
      else sites.set(site, { lead: article, more: [] });
    }

    const query = document.querySelector("#q")?.value || "";
    for (const [site, { lead, more }] of sites) {
      if (!more.length) continue;
      const shown = more.slice(0, MAX);
      let previous = lead;
      for (const article of shown) {
        article.classList.add("avk-sub");
        previous.after(article);
        previous = article;
      }
      shown[0].classList.add("avk-sub-first");
      previous.classList.add("avk-sub-last");

      if (more.length > MAX) {
        for (const article of more.slice(MAX)) article.remove();
        const link = document.createElement("a");
        link.className = "avk-more";
        link.href = "/search?q=" + encodeURIComponent(`site:${site} ${query}`.trim());
        link.textContent = `More from ${site}`;
        (previous.querySelector(".result_inner") || previous).append(link);
      }
    }
  }

  function start() {
    const urls = document.querySelector("#urls");
    if (!urls) return;
    group([...urls.querySelectorAll(":scope > article.result")]);
    new MutationObserver((records) => {
      const added = records.flatMap((record) => [...record.addedNodes]);
      const articles = added.filter((node) => node.matches?.("article.result") && !node.dataset.avkSeen);
      if (articles.length) group(articles);
    }).observe(urls, { childList: true });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
