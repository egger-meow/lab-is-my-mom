(() => {
  const data = window.RESEARCH_OS_DATA;
  const $ = (selector) => document.querySelector(selector);
  const list = $("#paper-list");
  const template = $("#paper-template");
  const dialog = $("#paper-dialog");
  const state = { status: "all", year: "all", savedOnly: false, saved: new Set(JSON.parse(localStorage.getItem("research-os-saved") || "[]")) };

  const internalHref = (path) => `../${String(path).replaceAll("\\", "/")}`;
  const externalLink = (href) => /^https?:\/\//.test(href);
  const resourceLink = (href, text, className = "") => {
    const anchor = document.createElement("a");
    const external = externalLink(href);
    anchor.href = external ? href : internalHref(href);
    anchor.textContent = text;
    anchor.className = className;
    if (external) { anchor.target = "_blank"; anchor.rel = "noreferrer"; }
    return anchor;
  };
  const saveState = () => {
    localStorage.setItem("research-os-saved", JSON.stringify([...state.saved]));
    $("#saved-count").textContent = state.saved.size;
  };
  const setSavedButton = (button, paper) => {
    const saved = state.saved.has(paper.id);
    button.textContent = saved ? "▣" : "⌑";
    button.classList.toggle("is-saved", saved);
    button.setAttribute("aria-label", `${saved ? "Remove" : "Save"} ${paper.title} ${saved ? "from" : "to"} reading list`);
  };
  function toggleSaved(paper, button) {
    state.saved.has(paper.id) ? state.saved.delete(paper.id) : state.saved.add(paper.id);
    saveState();
    if (button) setSavedButton(button, paper);
    render();
  }
  function yearFilters() {
    const years = [...new Set(data.papers.map((paper) => paper.year).filter(Boolean))].sort((a, b) => b - a);
    const container = $("#year-filters");
    container.replaceChildren();
    ["all", ...years].forEach((year) => {
      const button = document.createElement("button");
      button.type = "button"; button.className = `year-filter ${String(year) === String(state.year) ? "active" : ""}`;
      button.textContent = year === "all" ? "Any year" : year;
      button.addEventListener("click", () => { state.year = year; render(); });
      container.append(button);
    });
  }
  function filteredPapers() {
    const query = $("#search").value.trim().toLowerCase();
    const sort = $("#sort").value;
    return data.papers.filter((paper) => {
      const haystack = [paper.title, paper.authors, paper.venue, paper.doi, paper.arxiv_id].filter(Boolean).join(" ").toLowerCase();
      return (state.status === "all" || paper.status === state.status) && (state.year === "all" || paper.year === state.year) && (!state.savedOnly || state.saved.has(paper.id)) && (!query || haystack.includes(query));
    }).sort((a, b) => sort === "title" ? a.title.localeCompare(b.title) : sort === "oldest" ? (a.year || 0) - (b.year || 0) : (b.year || 0) - (a.year || 0));
  }
  function render() {
    const papers = filteredPapers();
    list.replaceChildren(); yearFilters();
    $("#results-count").textContent = `${papers.length} ${papers.length === 1 ? "paper" : "papers"}${state.savedOnly ? " in your reading list" : " in this collection"}`;
    for (const paper of papers) {
      const fragment = template.content.cloneNode(true);
      fragment.querySelector(".year").textContent = paper.year || "Year unknown";
      const badge = fragment.querySelector(".status");
      badge.textContent = paper.status === "fetched" ? "Ready to read" : "Source gap";
      badge.classList.add(`status--${paper.status}`);
      fragment.querySelector("h3").textContent = paper.title;
      fragment.querySelector(".authors").textContent = paper.authors;
      fragment.querySelector(".venue").textContent = paper.venue || "Venue not yet resolved";
      const ids = fragment.querySelector(".identifiers");
      if (paper.arxiv_id) ids.append(resourceLink(`https://arxiv.org/abs/${paper.arxiv_id}`, `arXiv ${paper.arxiv_id}`, "tag"));
      if (paper.doi) ids.append(resourceLink(`https://doi.org/${paper.doi}`, "DOI", "tag"));
      const save = fragment.querySelector(".save-paper"); setSavedButton(save, paper);
      save.addEventListener("click", () => toggleSaved(paper, save));
      fragment.querySelector(".open-paper").addEventListener("click", () => openPaper(paper));
      list.append(fragment);
    }
    if (!papers.length) {
      list.innerHTML = `<section class="empty"><p class="eyebrow">Nothing here yet</p><h3>No papers match this view.</h3><p>Try removing a filter or searching for a different author, topic, or venue.</p><button type="button" class="text-button" id="clear-filters">Clear all filters →</button></section>`;
      $("#clear-filters").addEventListener("click", () => { state.status = "all"; state.year = "all"; state.savedOnly = false; $("#search").value = ""; $("#saved-toggle").setAttribute("aria-pressed", "false"); document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item.dataset.status === "all")); render(); });
    }
  }
  function openPaper(paper) {
    $("#dialog-meta").textContent = `${paper.year || "Undated"} · ${paper.status === "fetched" ? "full text available" : "source still unresolved"}`;
    $("#dialog-title").textContent = paper.title;
    $("#dialog-authors").textContent = paper.authors;
    $("#dialog-venue").textContent = paper.venue || "Venue not yet resolved";
    const actions = $("#dialog-actions"); actions.replaceChildren();
    if (paper.pdf_path) actions.append(resourceLink(paper.pdf_path, "Open local PDF", "button button--primary"));
    paper.links.forEach((link) => actions.append(resourceLink(link.url, link.kind === "pdf" ? "Open published PDF" : link.label || "Open source", "button")));
    actions.append(resourceLink(paper.source_url, "View source evidence", "button"));
    const save = document.createElement("button"); save.type = "button"; save.className = "button"; save.textContent = state.saved.has(paper.id) ? "Remove from list" : "Save to reading list";
    save.addEventListener("click", () => { toggleSaved(paper); save.textContent = state.saved.has(paper.id) ? "Remove from list" : "Save to reading list"; }); actions.append(save);
    const notes = $("#dialog-notes"); notes.replaceChildren();
    if (paper.notes.length) paper.notes.forEach((note) => notes.append(resourceLink(note, note.split(/[\\/]/).pop().replace(".md", "").replaceAll("-", " "), "note-link")));
    else notes.append(Object.assign(document.createElement("p"), { textContent: "No committed reading notes yet. The source record remains visible so this gap can be tracked." }));
    dialog.showModal();
  }
  $("#professor-name")?.remove();
  $("#affiliation").textContent = data.professor.affiliation;
  $("#lab-link").href = data.professor.url;
  $("#total-count").textContent = data.summary.total;
  $("#fetched-count").textContent = data.summary.fetched;
  $("#unresolved-count").textContent = data.summary.unresolved;
  saveState();
  $("#search").addEventListener("input", render);
  $("#sort").addEventListener("change", render);
  document.querySelectorAll(".filter").forEach((button) => button.addEventListener("click", () => { state.status = button.dataset.status; document.querySelectorAll(".filter").forEach((item) => item.classList.toggle("active", item === button)); render(); }));
  $("#saved-toggle").addEventListener("click", (event) => { state.savedOnly = !state.savedOnly; event.currentTarget.setAttribute("aria-pressed", String(state.savedOnly)); render(); });
  $("#dialog-close").addEventListener("click", () => dialog.close());
  dialog.addEventListener("click", (event) => { if (event.target === dialog) dialog.close(); });
  document.addEventListener("keydown", (event) => { if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") { event.preventDefault(); $("#search").focus(); } });
  render();
})();
