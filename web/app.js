(() => {
  const data = window.RESEARCH_OS_DATA;
  const $ = (s, root = document) => root.querySelector(s);
  const esc = (s = "") => String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const href = p => `../${String(p).replaceAll("\\", "/")}`;
  const artifact = key => data.artifacts?.[key]?.content || "";
  const paperByPath = path => data.papers.find(p => path.includes(p.id));
  const clean = s => String(s || "").replace(/^[#*\s-]+/, "").trim();
  const lines = md => md.split(/\r?\n/).filter(x => x.trim());
  const inline = text => esc(text)
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, (_, label, url) => `<a href="${esc(url.startsWith("http") ? url : href(url))}">${label}</a>`)
    .replace(/`([^`]+)`/g, "<code>$1</code>").replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  function markdown(md = "") {
    const out = []; let list = null, table = false;
    for (const raw of md.split(/\r?\n/)) {
      const t = raw.trim();
      if (!t) { if (list) { out.push(`</${list}>`); list=null; } if(table){out.push("</tbody></table>");table=false;} continue; }
      if (/^\|.+\|$/.test(t)) {
        if (/^\|[\s:|-]+\|$/.test(t)) continue;
        const cells=t.slice(1,-1).split("|").map(x=>`<td>${inline(x.trim())}</td>`).join("");
        if(!table){out.push(`<table><tbody>`);table=true;} out.push(`<tr>${cells}</tr>`); continue;
      }
      if(table){out.push("</tbody></table>");table=false;}
      const h=t.match(/^(#{1,3})\s+(.+)/); if(h){out.push(`<h${h[1].length}>${inline(h[2])}</h${h[1].length}>`);continue;}
      const li=t.match(/^(?:[-*]|\d+\.)\s+(.+)/); if(li){const kind=/^\d/.test(t)?"ol":"ul";if(list!==kind){if(list)out.push(`</${list}>`);out.push(`<${kind}>`);list=kind;}out.push(`<li>${inline(li[1])}</li>`);continue;}
      if(list){out.push(`</${list}>`);list=null;} out.push(`<p>${inline(t)}</p>`);
    }
    if(list)out.push(`</${list}>`);if(table)out.push("</tbody></table>");return out.join("");
  }
  const evidenceLinks = (text, limit=3) => {
    const found = data.papers.filter(p => text.toLowerCase().includes(p.title.toLowerCase().split(":")[0]) || text.toLowerCase().includes(p.id.split("-")[0]));
    return (found.length ? found : data.papers.filter(p=>p.status==="fetched").slice(0,limit)).slice(0,limit).map(p=>`<button class="text-button open-paper" data-paper="${p.id}">${esc(p.title)}</button>`).join("");
  };
  function overview(){
    const dirs=lines(artifact("research-directions")).filter(x=>/^\d+\./.test(x));
    const recent=[...data.papers].sort((a,b)=>(b.year||0)-(a.year||0)).slice(0,4);
    $("#view-overview").innerHTML=`<div class="hero-grid"><article class="panel"><p class="eyebrow">研究者總覽 · Corpus 驅動</p><h1>${esc(data.professor.name)} 的研究脈絡，一眼開始。</h1><p class="lede">從個人知識庫與資訊回憶，延伸到教育回饋、可信任 AI、事實查核與人機協作。每一項整理都可回到已提交的研究證據。</p><div class="chips"><span class="chip">自然語言處理</span><span class="chip">以人為本 AI</span><span class="chip">教育科技</span><span class="chip">可信任 AI</span></div></article><aside class="panel dark"><p class="eyebrow">教授與實驗室</p><h2>${esc(data.professor.name)}</h2><p>${esc(data.professor.affiliation)}</p><p class="muted">以碩士生的進入順序組織：先辨認研究方向，再建立閱讀路徑，最後形成可追溯的研究問題。</p><a class="button" href="${esc(data.professor.url)}" target="_blank" rel="noreferrer">教授網站</a></aside></div>
    <div class="metric-grid section-head"><div class="metric"><strong>${data.summary.total}</strong><span>收錄著作</span></div><div class="metric"><strong>${data.summary.fetched}</strong><span>全文與筆記就緒</span></div><div class="metric"><strong>${data.summary.unresolved}</strong><span>待補來源缺口</span></div></div>
    <div class="section-head"><div><p class="eyebrow">Research directions</p><h2>實驗室研究方向</h2></div><button class="text-button goto" data-view="map">開啟研究地圖</button></div><div class="grid-2">${dirs.map((d,i)=>`<article class="panel direction"><span class="eyebrow">0${i+1}</span><h3>${inline(clean(d.replace(/^\d+\.\s*/,"")))}</h3><div>${evidenceLinks(d,2)}</div></article>`).join("")}</div>
    <div class="section-head"><div><p class="eyebrow">Corpus pulse</p><h2>最近加入與待處理</h2></div></div><div class="paper-list">${recent.map(p=>paperCard(p)).join("")}</div>`;
  }
  function paperCard(p){return `<article class="paper-card"><div><span class="badge ${p.status==="fetched"?"good":"warn"}">${p.status==="fetched"?"可閱讀":"來源待補"}</span> <span class="paper-meta">${p.year||"年份未明"}</span></div><h3>${esc(p.title)}</h3><p class="paper-meta">${esc(p.authors)}</p><button class="text-button open-paper" data-paper="${p.id}">進入論文工作台</button></article>`}
  function researchMap(){
    const topics=["教育與學習支持","可信任 AI 與查核","個人知識與生命日誌","多語言與模型效率"];
    const fetched=data.papers.filter(p=>p.status==="fetched").slice(0,12); const W=1000,H=560,cx=500,cy=280;
    const nodes=topics.map((t,i)=>({id:`t${i}`,label:t,x:170+i%2*660,y:125+Math.floor(i/2)*310,type:"topic"}));
    fetched.forEach((p,i)=>{const a=(i/fetched.length)*Math.PI*2;nodes.push({id:p.id,label:p.title.slice(0,22)+(p.title.length>22?"…":""),x:cx+260*Math.cos(a),y:cy+190*Math.sin(a),type:"paper",paper:p})});
    const edges=fetched.map((p,i)=>({a:nodes[i%4],b:nodes[4+i]}));
    $("#view-map").innerHTML=`<p class="eyebrow">Evidence-linked graph</p><h1>研究地圖</h1><p class="lede">節點與連線由已提交的方向、方法、資料集與論文產生。選取論文節點即可查看支援文件與原文證據。</p><div class="legend"><span>深色：研究主題</span><span>淺色：已取得全文論文</span></div><div class="graph"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="研究主題與論文關係圖">${edges.map(e=>`<line x1="${e.a.x}" y1="${e.a.y}" x2="${e.b.x}" y2="${e.b.y}"/>`).join("")}${nodes.map(n=>`<g class="graph-node ${n.type}" data-paper="${n.paper?.id||""}" tabindex="0" transform="translate(${n.x} ${n.y})"><circle r="${n.type==="topic"?54:38}"/><text text-anchor="middle" dy="4">${esc(n.label)}</text></g>`).join("")}</svg></div><div class="grid-2 section-head"><article class="panel markdown">${markdown(artifact("method-map"))}</article><article class="panel markdown">${markdown(artifact("dataset-map"))}</article></div>`;
  }
  function readingPath(){
    const items=[...artifact("reading-order").matchAll(/\d+\. \[([^\]]+)\]\(([^)]+)\)\s*-\s*(.+)/g)];
    $("#view-path").innerHTML=`<p class="eyebrow">Guided curriculum</p><h1>從基礎到研究前沿的閱讀路徑</h1><p class="lede">每篇都有「為什麼現在讀」、先備概念與本機閱讀狀態。狀態與筆記只儲存在你的瀏覽器。</p>${items.map((m,i)=>{const p=paperByPath(m[2]);return `<article class="path-card"><div class="path-index">${String(i+1).padStart(2,"0")}</div><div><span class="badge">${i<2?"基礎":i<4?"核心研究":"當前方向"}</span><h3>${esc(m[1])}</h3><p>${inline(m[3])}</p><p class="paper-meta">難度：${i<2?"入門":i<4?"中階":"進階"} · 先備：${i<2?"NLP 與 Transformer 基礎":"前一階段閱讀"}</p><textarea class="local-note" data-id="${p?.id||i}" placeholder="我的閱讀筆記…" aria-label="${esc(m[1])} 的閱讀筆記"></textarea></div><select class="status-select" data-id="${p?.id||i}" aria-label="閱讀狀態"><option>尚未開始</option><option>閱讀中</option><option>已完成</option></select></article>`}).join("")}`;
    document.querySelectorAll(".status-select,.local-note").forEach(el=>{const k=`research-os-${el.classList.contains("local-note")?"note":"status"}-${el.dataset.id}`;el.value=localStorage.getItem(k)||el.value;el.addEventListener("change",()=>localStorage.setItem(k,el.value));el.addEventListener("input",()=>localStorage.setItem(k,el.value))});
  }
  let currentPaper=data.papers.find(p=>p.status==="fetched")||data.papers[0];
  function workspace(p=currentPaper, tab="README"){
    currentPaper=p; const docs=p.documents||{}; const tabs=[["README","摘要"],["reading-guide-zh","寶寶導讀"],["method","方法"],["experiments-and-results","實驗與結果"],["limitations-and-critique","限制與批判"],["prerequisites","先備知識"],["seminar-questions","討論問題"],["diagrams","Mermaid 圖"]];
    const content=tab==="diagrams"?(p.diagrams?.map(d=>`<section><h2>${esc(d.path.split(/[\\/]/).pop())}</h2><div class="mermaid-code">${esc(d.content)}</div></section>`).join("")||`<p class="empty">尚無圖表。</p>`):markdown(docs[tab]?.content||"# 尚待整理\n\n這份研究產物尚未提交；來源狀態仍保留在 corpus 中。");
    $("#view-workspace").innerHTML=`<p class="eyebrow">Paper workspace</p><h1>論文工作台</h1><div class="workspace-layout"><aside class="panel"><label>選擇論文<input class="workspace-filter" placeholder="篩選論文"></label><div class="paper-nav">${data.papers.map(x=>`<button class="${x.id===p.id?"active":""}" data-paper="${x.id}">${esc(x.title)}</button>`).join("")}</div></aside><article class="panel"><span class="badge ${p.status==="fetched"?"good":"warn"}">${p.status==="fetched"?"全文已取得":"來源待補"}</span><h2>${esc(p.title)}</h2><p class="paper-meta">${esc(p.authors)} · ${p.year||"年份未明"}</p><div class="tabs">${tabs.map(t=>`<button class="tab ${t[0]===tab?"active":""}" data-tab="${t[0]}">${t[1]}</button>`).join("")}</div><div class="markdown">${content}</div><div class="section-head"><div><h3>原文證據</h3><p class="paper-meta">頁碼錨點來自 PDF 擷取結果。</p></div>${p.pdf_path?`<a class="button primary" href="${href(p.pdf_path)}">開啟 PDF</a>`:""}</div><div class="chips">${(p.sections||[]).slice(0,12).map(s=>`<a class="chip" href="${p.pdf_path?href(p.pdf_path)+"#page="+s.page:"#"}">${esc(s.heading)} · p. ${s.page}</a>`).join("")}</div></article></div>`;
  }
  function opportunities(){
    const qs=lines(artifact("open-questions")).filter(x=>x.startsWith("- "));
    $("#view-opportunities").innerHTML=`<p class="eyebrow">Thesis entry points</p><h1>研究機會</h1><p class="lede">以下將「來源支持的觀察」與「建置者的研究詮釋」明確分開；它們是論文題目的入口，不代表教授已核准或承諾指導。</p><div class="evidence-list">${qs.map((q,i)=>`<article class="evidence-item ${i%2?"interpretation":""}"><span class="badge">${i%2?"建置者詮釋":"來源支持"}</span><h3>${inline(clean(q))}</h3><p>${i%2?"可作為訪談教授與檢查可行性的起點；仍需驗證資料、評估方式與指導意願。":"由已提交的限制、研究方向或 corpus 缺口歸納。"}</p><div>${evidenceLinks(q)}</div></article>`).join("")}</div>`;
  }
  function library(query=""){const ps=data.papers.filter(p=>[p.title,p.authors,p.venue].join(" ").toLowerCase().includes(query.toLowerCase()));$("#view-library").innerHTML=`<p class="eyebrow">Corpus index</p><h1>論文庫</h1><p class="lede">完整索引保留在此；它是研究工作台的證據底層，不再是產品首頁。</p><div class="paper-list">${ps.map(paperCard).join("")||`<p class="empty">找不到相符論文。</p>`}</div>`}
  let discoveryTab="web";
  function discovery(query="") {
    const candidates=(data.discovery?.candidates||[]).filter(c=>[c.title,(c.authors||[]).join(" "),c.venue,c.abstract,(c.topics||[]).join(" ")].join(" ").toLowerCase().includes(query.toLowerCase()));
    const local=data.papers.filter(p=>[p.title,p.authors,p.venue].join(" ").toLowerCase().includes(query.toLowerCase()));
    const card=c=>`<article class="paper-card discovery-card"><div><span class="badge">${c.state==="imported"?"已匯入語料庫":c.state==="saved"?"已儲存候選":"Web 候選"}</span> <span class="paper-meta">${c.year||"年份未知"} · ${esc(c.venue||"場域未知")}</span></div><h3>${esc(c.title)}</h3><p class="paper-meta">${esc((c.authors||[]).join(", "))}</p><p>${esc((c.abstract||"無摘要 metadata").slice(0,280))}</p><div class="chips">${c.doi?`<span class="chip">DOI ${esc(c.doi)}</span>`:""}${c.arxiv_id?`<span class="chip">arXiv ${esc(c.arxiv_id)}</span>`:""}${c.acl_id?`<span class="chip">ACL ${esc(c.acl_id)}</span>`:""}</div><p class="paper-meta">來源：${esc((c.providers||[]).join(" · "))} · ${c.open_access?"開放取用位置可用（尚未抓取全文）":"未確認開放全文"}</p><ul>${(c.ranking_explanation||[]).map(x=>`<li>${esc(x)}</li>`).join("")}</ul><div class="candidate-actions"><button class="text-button cli-action" data-command="research-os save-candidate ${c.id}">儲存候選</button><button class="text-button cli-action" data-command="research-os import ${c.id}">加入語料庫</button><button class="text-button cli-action" data-command="research-os expand ${c.id} --similar">找相似論文</button><button class="text-button cli-action" data-command="research-os expand ${c.id} --references">探索參考文獻</button><button class="text-button cli-action" data-command="research-os expand ${c.id} --citations">探索引用</button></div></article>`;
    const failures=data.discovery?.runs?.[0]?.failures||{};
    $("#view-discovery").innerHTML=`<p class="eyebrow">Federated academic metadata</p><h1>全球學術探索</h1><p class="lede">Web 結果是暫存候選；本地語料庫是永久記錄；只有明確執行 import 才會轉換狀態。探索不會下載或消化全文。</p><form id="discovery-form" class="discovery-search"><input id="discovery-query" value="${esc(query)}" placeholder="例如：LLM confidence routing"><button class="button primary">搜尋已產生的資料</button><code>research-os discover &quot;${esc(query||"LLM confidence routing")}&quot;</code></form><div class="tabs"><button class="tab discovery-tab ${discoveryTab==="web"?"active":""}" data-discovery-tab="web">Web 結果 (${candidates.length})</button><button class="tab discovery-tab ${discoveryTab==="local"?"active":""}" data-discovery-tab="local">本地語料庫 (${local.length})</button></div>${Object.keys(failures).length?`<p class="provider-warning">部分來源暫時失敗：${esc(Object.keys(failures).join("、"))}；其他來源結果仍可使用。</p>`:""}<div class="paper-list">${discoveryTab==="web"?(candidates.map(card).join("")||`<p class="empty">尚無符合的 Web 候選。先執行 discover，再執行 dashboard 重新產生資料。</p>`):local.map(paperCard).join("")}</div>`;
  }
  const renderers={overview,researchMap,path:readingPath,workspace,opportunities,library,discovery};
  function go(view){document.querySelectorAll(".view,.nav-item").forEach(x=>x.classList.remove("active"));$(`#view-${view}`).classList.add("active");$(`.nav-item[data-view="${view}"]`).classList.add("active");renderers[view]?.();$("#breadcrumb").textContent=$(`.nav-item[data-view="${view}"]`).textContent;location.hash=view;$(".sidebar").classList.remove("open");}
  document.addEventListener("click",e=>{const nav=e.target.closest("[data-view]");if(nav)go(nav.dataset.view);const op=e.target.closest(".open-paper,[data-paper]");if(op?.dataset.paper){const p=data.papers.find(x=>x.id===op.dataset.paper);if(p){go("workspace");workspace(p);}}const tab=e.target.closest("[data-tab]");if(tab)workspace(currentPaper,tab.dataset.tab);const dt=e.target.closest("[data-discovery-tab]");if(dt){discoveryTab=dt.dataset.discoveryTab;discovery($("#discovery-query")?.value||"");}const action=e.target.closest(".cli-action");if(action){navigator.clipboard?.writeText(action.dataset.command);action.textContent="命令已複製";}if(e.target.matches(".dialog-close"))$("#evidence-dialog").close()});
  document.addEventListener("submit",e=>{if(e.target.id==="discovery-form"){e.preventDefault();discovery($("#discovery-query").value);}});
  $("#menu").addEventListener("click",()=>$(".sidebar").classList.toggle("open"));$("#search").addEventListener("input",e=>{go("library");library(e.target.value)});
  $("#generated-at").textContent=new Date(data.generated_at).toLocaleString("zh-TW");overview();if(location.hash&&renderers[location.hash.slice(1)])go(location.hash.slice(1));
})();
