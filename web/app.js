(() => {
  const data = window.RESEARCH_OS_DATA;
  const $ = (selector) => document.querySelector(selector);
  const list = $("#paper-list");
  const template = $("#paper-template");
  let status = "all";

  function resourceLink(href, text, external = false) {
    const anchor = document.createElement("a");
    anchor.href = `../${href}`;
    anchor.textContent = text;
    if (external) { anchor.href = href; anchor.target = "_blank"; anchor.rel = "noreferrer"; }
    return anchor;
  }
  function render() {
    const query = $("#search").value.trim().toLowerCase();
    const papers = data.papers.filter((paper) => {
      const haystack = [paper.title, paper.authors, paper.venue, paper.doi, paper.arxiv_id].filter(Boolean).join(" ").toLowerCase();
      return (status === "all" || paper.status === status) && (!query || haystack.includes(query));
    });
    list.replaceChildren();
    $("#results-count").textContent = `${papers.length} work${papers.length === 1 ? "" : "s"}`;
    for (const paper of papers) {
      const fragment = template.content.cloneNode(true);
      fragment.querySelector(".year").textContent = paper.year || "—";
      const badge = fragment.querySelector(".status"); badge.textContent = paper.status === "fetched" ? "full text" : "unresolved"; badge.classList.add(`status--${paper.status}`);
      fragment.querySelector("h2").textContent = paper.title;
      fragment.querySelector(".authors").textContent = paper.authors;
      fragment.querySelector(".venue").textContent = paper.venue || "Venue not yet resolved";
      const ids = fragment.querySelector(".identifiers");
      if (paper.arxiv_id) ids.append(resourceLink(`https://arxiv.org/abs/${paper.arxiv_id}`, `arXiv:${paper.arxiv_id}`, true));
      if (paper.doi) ids.append(resourceLink(`https://doi.org/${paper.doi}`, `doi:${paper.doi}`, true));
      const resources = fragment.querySelector(".resources");
      resources.append(resourceLink(paper.source_url, "source evidence ↗", true));
      if (paper.pdf_path) resources.append(resourceLink(paper.pdf_path, "source PDF"));
      for (const note of paper.notes) resources.append(resourceLink(note, note.split("/").pop().replace(".md", "")));
      list.append(fragment);
    }
    if (!papers.length) list.innerHTML = '<p class="empty">No papers match those filters.</p>';
  }
  $("#professor-name").textContent = data.professor.name;
  $("#affiliation").textContent = data.professor.affiliation;
  $("#lab-link").href = data.professor.url;
  $("#total-count").textContent = data.summary.total;
  $("#fetched-count").textContent = data.summary.fetched;
  $("#unresolved-count").textContent = data.summary.unresolved;
  $("#search").addEventListener("input", render);
  document.querySelectorAll(".filter").forEach((button) => button.addEventListener("click", () => { status = button.dataset.status; document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button)); render(); }));
  render();
})();
