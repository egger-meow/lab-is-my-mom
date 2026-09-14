const PAGE_TITLES = {
  today: 'Today · 今日總覽',
  tasks: 'Tasks · 工作與義務',
  meetings: 'Meetings · 會議節奏',
  research: 'Research · 研究證據鏈',
  papers: 'Papers · 論文庫',
  documents: 'Documents · 文件與簡報',
  agents: 'Agents · 背景執行',
  system: 'System · Mothership 狀態',
  help: '使用說明 · Master OS',
};
const WEEKDAY_NAMES = {mon:'週一',tue:'週二',wed:'週三',thu:'週四',fri:'週五',sat:'週六',sun:'週日'};
const state = {page:'today',cockpit:null,onboarding:null,tasks:null,meetings:null,research:null,papers:null,documents:null,agents:null,system:null,currentFocusTaskId:null,loading:false};
const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function esc(value) { return String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;'); }
function safeUrl(value) { try { const url=new URL(value); return ['http:','https:'].includes(url.protocol)?url.href:null; } catch (_) { return null; } }
function fmtDate(value) { if(!value)return'未設定'; const d=new Date(value); if(Number.isNaN(d.getTime()))return value; return new Intl.DateTimeFormat('zh-TW',{month:'numeric',day:'numeric',weekday:'short',hour:'2-digit',minute:'2-digit'}).format(d); }
function fmtFullDate(value) { if(!value)return'未設定'; const d=new Date(value); if(Number.isNaN(d.getTime()))return value; return new Intl.DateTimeFormat('zh-TW',{year:'numeric',month:'2-digit',day:'2-digit',weekday:'short',hour:'2-digit',minute:'2-digit'}).format(d); }
function remainingDaysText(value){if(!value)return null;const target=new Date(value);if(Number.isNaN(target.getTime()))return null;const now=new Date();const today=new Date(now.getFullYear(),now.getMonth(),now.getDate());const targetDay=new Date(target.getFullYear(),target.getMonth(),target.getDate());const diffDays=Math.round((targetDay.getTime()-today.getTime())/(1000*60*60*24));if(diffDays<0)return{text:`已逾期 ${Math.abs(diffDays)} 天`,tone:'red'};if(diffDays===0)return{text:'今天',tone:'red'};if(diffDays===1)return{text:'明天 (剩 1 天)',tone:'yellow'};if(diffDays===2)return{text:'後天 (剩 2 天)',tone:'yellow'};if(diffDays<=7)return{text:`剩下 ${diffDays} 天`,tone:'yellow'};return{text:`剩下 ${diffDays} 天`,tone:'blue'};}
function localInputValue(value) { const d=new Date(value); if(Number.isNaN(d.getTime()))return''; const p=(n)=>String(n).padStart(2,'0'); return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())}T${p(d.getHours())}:${p(d.getMinutes())}`; }
function badge(value,tone=''){return `<span class="badge ${tone}">${esc(value)}</span>`;}
function empty(text){return `<div class="empty">${esc(text)}</div>`;}
async function api(path,options={}){const res=await fetch(path,options);let body={};try{body=await res.json();}catch(_){}if(!res.ok)throw new Error(body.detail||`HTTP ${res.status}`);return body;}
let toastTimer=null;
function toast(message,isError=false){const el=$('#toast');el.textContent=message;el.className=`toast show${isError?' error':''}`;clearTimeout(toastTimer);toastTimer=setTimeout(()=>{el.className='toast';},3400);}
function openModal(id){document.getElementById(id)?.classList.add('open');}
function closeModal(id){document.getElementById(id)?.classList.remove('open');if(id==='text-modal'){const ib=$('#modal-ingest-btn');if(ib)ib.style.display='none';state.activeDocFilename=null;}}
function showTextModal(title,body){$('#text-modal-title').textContent=title;$('#text-modal-body').textContent=body;openModal('text-modal');}
function priorityTone(value){if(value==='critical')return'red';if(value==='high')return'yellow';if(value==='low')return'';return'blue';}
function statusTone(value){if(['completed','validated','satisfied','healthy','ready'].includes(value))return'green';if(['blocked','interrupted','failed','invalid'].includes(value))return'red';if(['running','in_progress','queued','pending','under_review'].includes(value))return'yellow';return'blue';}

function navigate(page,updateHash=true){if(!PAGE_TITLES[page])page='today';state.page=page;$$('.page').forEach((el)=>el.classList.toggle('active',el.dataset.page===page));$$('[data-nav]').forEach((el)=>el.classList.toggle('active',el.dataset.nav===page));$('#top-title').textContent=PAGE_TITLES[page];if(updateHash)history.replaceState(null,'',`#${page}`);refreshPage(page);window.scrollTo({top:0,behavior:'instant'});}
async function refreshPage(page=state.page){if(state.loading)return;state.loading=true;$('#refresh-btn')?.setAttribute('disabled','disabled');try{if(page==='today')await loadToday();else if(page==='tasks')await loadTasks();else if(page==='meetings')await loadMeetings();else if(page==='research')await loadResearch();else if(page==='papers')await loadPapers();else if(page==='documents')await loadDocuments();else if(page==='agents')await loadAgents();else if(page==='system')await loadSystem();}catch(err){console.error(err);toast(`讀取 ${PAGE_TITLES[page]} 失敗：${err.message}`,true);}finally{state.loading=false;$('#refresh-btn')?.removeAttribute('disabled');}}

async function loadToday(){const [cockpit,onboarding]=await Promise.all([api('/api/cockpit'),api('/api/onboarding')]);state.cockpit=cockpit;state.onboarding=onboarding;renderOnboarding(onboarding);renderToday(cockpit,onboarding);}
function renderOnboarding(data){const panel=$('#onboarding-panel');panel.classList.toggle('show',!data.complete);if(data.complete)return;const actionMap={advisor_meeting:['meetings','設定'],research_topic:['research','填寫'],meeting_transcript:['transcript','匯入'],slack:['system','查看']};$('#onboarding-steps').innerHTML=data.steps.map((step)=>{const [target,label]=actionMap[step.id]||['today','處理'];return `<div class="step ${step.done?'done':''}"><div class="step-title">${step.done?'✓ ':''}${esc(step.label)}</div><div class="step-state">${step.done?'已完成':(step.optional?'選用，可稍後':'尚未完成')}</div>${step.done?'':`<button class="btn small ghost" data-onboard="${esc(target)}" style="margin-top:7px">${esc(label)}</button>`}</div>`;}).join('');}
function renderToday(data,onboarding){const now=data.what_matters_now;const fa=now.focus_action||{};const needsSetup=!onboarding.complete&&!fa.task_id;state.currentFocusTaskId=needsSetup||fa.agentability!=='autonomous'?null:fa.task_id;$('#hero-title').textContent=needsSetup?'先把真實研究狀態餵進來，Planner 才不會對著空 DB 猜方向':(fa.title||'目前沒有可執行的焦點 Task');$('#hero-why').textContent=needsSetup?'完成上方必要 anchor：每週 Advisor 固定時間、研究主軸、最近 meeting 紀錄。':`${fa.why||'Planner 尚未找到下一個動作'}${fa.suggested_agent?` · 建議代理：${String(fa.suggested_agent).toUpperCase()}`:''}`;$('#hero-est').textContent=needsSetup?'First run':`預估 ~${fa.estimated_minutes??'?'} 分鐘`;$('#dispatch-focus').classList.toggle('hide',!state.currentFocusTaskId);const alert=$('#critic-alert');alert.classList.toggle('show',Boolean(now.fake_progress_warning));alert.textContent=now.warning_message||'';
  renderResearchPlanning(now); const coming=[];(data.what_is_coming.upcoming_meetings||[]).slice(0,4).forEach((m)=>{const rem=remainingDaysText(m.scheduled_at);const remBadge=rem?badge(rem.text,rem.tone):'';coming.push(`<div class="item"><div class="item-title">${esc(m.title)} ${remBadge}</div><div class="item-meta">${badge(m.recurring?'weekly':'meeting','blue')} ${fmtFullDate(m.scheduled_at)} · <code>${esc(m.id)}</code></div></div>`);});(data.what_is_coming.deadlines||[]).slice(0,5).forEach((d)=>{const rem=remainingDaysText(d.due_at||d.deadline||d.date);const remBadge=rem?badge(rem.text,rem.tone):'';coming.push(`<div class="item"><div class="item-title">${esc(d.title||d.name||d.id||'Deadline')} ${remBadge}</div><div class="item-meta">${badge(d.severity||'deadline','red')} ${fmtDate(d.due_at||d.deadline||d.date)}</div></div>`);});$('#today-coming').innerHTML=coming.join('')||empty('目前沒有 upcoming meeting 或 deadline。');
  const approvals=data.what_needs_me.pending_approvals||[];$('#today-approval-count').textContent=String(approvals.length);$('#today-approvals').innerHTML=approvals.length?approvals.slice(0,8).map((ap)=>{const preview=ap.action_payload?.text||ap.reason||ap.action_type;return `<div class="item"><div class="item-title">${esc(ap.reason||ap.action_type)}</div><div class="item-meta">${esc(String(preview).slice(0,180))}</div><div class="item-actions"><button class="btn small primary" data-approval="${esc(ap.id)}" data-decision="approved">核准</button><button class="btn small danger" data-approval="${esc(ap.id)}" data-decision="rejected">駁回</button></div></div>`;}).join(''):empty('目前沒有需要你裁量的項目。');
  const changed=[];(data.what_changed.recent_findings||[]).slice(0,4).forEach((f)=>changed.push(`<div class="item"><div class="item-title">${esc(f.statement)}</div><div class="item-meta">${badge(f.status,statusTone(f.status))} confidence ${esc(f.confidence)}</div></div>`));(data.what_changed.recent_artifacts||[]).slice(0,3).forEach((a)=>changed.push(`<div class="item"><div class="item-title">${esc(a.artifact_type)}</div><div class="artifact-path">${esc(a.path)}</div></div>`));$('#today-changed').innerHTML=changed.join('')||empty('尚未有 Experiment / Finding / Artifact 變化。');const runs=data.what_are_agents_doing.recent_runs||[];$('#today-agents').innerHTML=runs.length?runs.slice(0,6).map(runCard).join(''):empty('Agent 全部 idle，沒有歷史 run。');}

async function loadTasks(){const data=await api('/api/tasks');state.tasks=data;renderTasks(data);}
function renderTasks(data){const tasks=data.tasks||[];const active=tasks.filter((t)=>['todo','in_progress','blocked'].includes(t.status));const autonomous=active.filter((t)=>t.agentability==='autonomous');const critical=active.filter((t)=>t.priority==='critical');$('#task-stats').innerHTML=[['Active tasks',active.length],['Critical',critical.length],['Agent-ready',autonomous.length],['Obligations',(data.obligations||[]).filter((o)=>!['satisfied','cancelled'].includes(o.status)).length]].map(([label,value])=>`<div class="stat"><strong>${value}</strong><span>${label}</span></div>`).join('');$('#tasks-list').innerHTML=tasks.length?tasks.map((t)=>{const criteria=t.acceptance_criteria?.length?`<div class="item-meta">Done when: ${esc(t.acceptance_criteria.join(' · '))}</div>`:'';const rem=t.due_at?remainingDaysText(t.due_at):null;const remBadge=rem?` ${badge(rem.text,rem.tone)}`:'';return `<div class="item task-row"><div><div class="item-title">${esc(t.title)}</div><div class="item-meta">${badge(t.priority,priorityTone(t.priority))} ${badge(t.status,statusTone(t.status))}${t.due_at?` · due ${fmtDate(t.due_at)}${remBadge}`:''}</div>${t.description?`<div class="item-meta">${esc(t.description)}</div>`:''}${t.obligation_title?`<div class="item-meta">↳ ${esc(t.obligation_title)}</div>`:''}${researchWorkMeta(t)}${criteria}</div><div class="task-controls"><select data-task-status="${esc(t.id)}">${['todo','in_progress','blocked','completed','cancelled'].map((s)=>`<option value="${s}" ${s===t.status?'selected':''}>${s}</option>`).join('')}</select>${t.agentability==='autonomous'&&['todo','in_progress'].includes(t.status)&&!t.work?.waiting_for?.length?`<button class="btn small primary" data-dispatch="${esc(t.id)}">派 ${esc(t.preferred_agent||'codex')}</button>`:''}</div></div>`;}).join(''):empty('還沒有 Task。');const obligations=data.obligations||[];$('#obligations-list').innerHTML=obligations.length?obligations.map((o)=>{const rem=o.due_at?remainingDaysText(o.due_at):null;const remBadge=rem?` ${badge(rem.text,rem.tone)}`:'';return `<div class="item"><div class="item-title">${esc(o.title)}</div><div class="item-meta">${badge(o.severity,priorityTone(o.severity))} ${badge(o.status,statusTone(o.status))}${o.due_at?` · due ${fmtFullDate(o.due_at)}${remBadge}`:''}</div>${o.description?`<div class="item-meta">${esc(o.description)}</div>`:''}${o.meeting_id?`<div class="item-meta">來源 meeting: ${esc(o.meeting_id)}</div>`:''}</div>`;}).join(''):empty('還沒有 confirmed obligation。');}

async function loadMeetings(){const data=await api('/api/meetings');state.meetings=data;renderMeetings(data);}
function meetingCard(m,historical=false){const isSeminar=m.kind==='lab_seminar';const advisorLike=m.kind==='advisor'||m.kind==='advisor_adhoc';const actions=historical?'':`${!isSeminar?`<button class="btn small" data-meeting-ingest="${esc(m.id)}" data-meeting-time="${esc(m.scheduled_at)}" data-meeting-kind="${esc(m.kind)}">匯入 transcript</button>`:''}${advisorLike?`<button class="btn small accent" data-meeting-pack="${esc(m.id)}">Meeting Pack</button>`:''}`;const rem=!historical?remainingDaysText(m.scheduled_at):null;const remBadge=rem?` ${badge(rem.text,rem.tone)}`:'';return `<div class="item"><div class="item-title">${esc(m.title)}${remBadge}</div><div class="item-meta">${badge(m.kind,'blue')} ${badge(m.recurring?'weekly':m.status,statusTone(m.status))} · ${fmtFullDate(m.scheduled_at)} · <code>${esc(m.id)}</code></div>${m.recurring?`<div class="item-meta">固定週期自動推算，不需要每週重填日期。</div>`:''}${actions?`<div class="item-actions">${actions}</div>`:''}</div>`;}
function renderMeetings(data){const routines=data.routines||[];const advisor=routines.find((r)=>r.kind==='advisor');const seminar=routines.find((r)=>r.kind==='lab_seminar');if(advisor?.weekly_spec){const rem=advisor.next_occurrence?remainingDaysText(advisor.next_occurrence.scheduled_at):null;const remBadge=rem?` ${badge(rem.text,rem.tone)}`:'';$('#advisor-weekday').value=advisor.weekly_spec.day_of_week;$('#advisor-time').value=advisor.weekly_spec.start_time;$('#advisor-routine-current').innerHTML=`目前：<strong>${esc(WEEKDAY_NAMES[advisor.weekly_spec.day_of_week])} ${esc(advisor.weekly_spec.start_time)}</strong> · 下次 ${fmtFullDate(advisor.next_occurrence?.scheduled_at)}${remBadge}`;}else{$('#advisor-routine-current').textContent='尚未設定。這是唯一需要你提供的每週固定 meeting 時間。';}
  if(seminar?.next_occurrence){const rem=remainingDaysText(seminar.next_occurrence.scheduled_at);const remBadge=rem?` ${badge(rem.text,rem.tone)}`:'';$('#seminar-next').innerHTML=`<div class="item-title">下一次 Lab Seminar${remBadge}</div><div class="item-meta">${fmtFullDate(seminar.next_occurrence.scheduled_at)} · ${esc(seminar.next_occurrence.id)}</div>`;}
  const upcoming=data.upcoming||[];$('#meeting-upcoming-count').textContent=String(upcoming.length);$('#meetings-upcoming').innerHTML=upcoming.length?upcoming.map((m)=>meetingCard(m)).join(''):empty('Advisor 固定時間尚未設定；Lab Seminar 應仍會顯示。');const history=data.history||[];$('#meetings-history').innerHTML=history.length?history.map((m)=>meetingCard(m,true)).join(''):empty('目前沒有 meeting history。');}
async function saveAdvisorRoutine(event){event.preventDefault();const day=$('#advisor-weekday').value;const start=$('#advisor-time').value;if(!day||!start)return toast('請填每週星期與時間',true);try{await api('/api/meetings/routines/advisor',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({day_of_week:day,start_time:start,timezone:'Asia/Taipei'})});toast(`Advisor 固定時間已設定：${WEEKDAY_NAMES[day]} ${start}`);await Promise.all([loadMeetings(),loadToday()]);}catch(err){toast(`固定時間儲存失敗：${err.message}`,true);}}
async function saveAdhocMeeting(event){event.preventDefault();const local=$('#adhoc-time').value;if(!local)return toast('臨時 Meeting 要填日期時間',true);const d=new Date(local);if(Number.isNaN(d.getTime()))return toast('日期時間格式不正確',true);const payload={kind:$('#adhoc-kind').value,title:$('#adhoc-title').value.trim()||null,scheduled_at:d.toISOString()};try{const result=await api('/api/meetings/adhoc',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});toast(`臨時 Meeting 已新增：${result.meeting_id}`);$('#adhoc-meeting-form').reset();await Promise.all([loadMeetings(),loadToday()]);}catch(err){toast(`新增失敗：${err.message}`,true);}}
function openTranscript(meetingId='',scheduledAt='',kind='advisor'){$('#transcript-mid').value=meetingId||'';$('#transcript-kind').value=kind||'advisor';$('#transcript-time').value=scheduledAt?localInputValue(scheduledAt):'';$('#transcript-text').value='';openModal('transcript-modal');setTimeout(()=>($('#transcript-text')||$('#transcript-mid'))?.focus(),40);}
async function submitTranscript(){const meetingId=$('#transcript-mid').value.trim();const text=$('#transcript-text').value.trim();if(!meetingId||!text)return toast('Meeting ID 和 transcript 都要填',true);const localTime=$('#transcript-time').value;let scheduledAt=null;if(localTime){const d=new Date(localTime);if(Number.isNaN(d.getTime()))return toast('Meeting 日期時間格式不正確',true);scheduledAt=d.toISOString();}const payload={meeting_id:meetingId,transcript_text:text,kind:$('#transcript-kind').value,scheduled_at:scheduledAt};try{const result=await api('/api/meetings/ingest',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});closeModal('transcript-modal');const count=(result.semantic_approval_ids||[]).length;toast(`Meeting 已匯入。${count?`${count} 個高影響候選進 Needs You。`:'沒有需要你確認的高影響候選。'}`);if(state.page==='meetings')await loadMeetings();else if(state.page==='today')await loadToday();}catch(err){toast(`匯入失敗：${err.message}`,true);}}
async function generatePack(meetingId){try{const result=await api(`/api/meetings/${encodeURIComponent(meetingId)}/pack`,{method:'POST'});showTextModal(`Meeting Pack · ${meetingId}`,result.meeting_pack||'(empty)');toast('Advisor Meeting Pack 已生成並進 Artifact Registry');}catch(err){toast(`Meeting Pack 失敗：${err.message}`,true);}}

async function loadResearch(){const data=await api('/api/research');state.research=data;renderResearch(data);await fetchTopics();}
function renderResearch(data){$('#research-topic').value=data.topic||'';$('#research-exp-count').textContent=String(data.experiments?.length||0);$('#research-find-count').textContent=String(data.findings?.length||0);$('#research-decision-count').textContent=String(data.decisions?.length||0);$('#research-artifact-count').textContent=String(data.artifacts?.length||0);$('#research-experiments').innerHTML=data.experiments?.length?data.experiments.map((e)=>`<div class="item"><div class="item-title">${esc(e.title)}</div><div class="item-meta">${badge(e.status,statusTone(e.status))} ${badge(e.validity_status,statusTone(e.validity_status))} · compute ${esc(e.compute_backend)}${e.research_repo?` · ${esc(e.research_repo)}`:''}</div>${e.git_sha?`<div class="artifact-path">git ${esc(e.git_sha)}</div>`:''}</div>`).join(''):empty('還沒有 experiment。');$('#research-findings').innerHTML=data.findings?.length?data.findings.map((f)=>`<div class="item"><div class="item-title">${esc(f.statement)}</div><div class="item-meta">${badge(f.status,statusTone(f.status))} · confidence ${esc(f.confidence)}${f.experiment_id?` · ${esc(f.experiment_id)}`:''}</div></div>`).join(''):empty('還沒有 finding。Agent 產的 candidate 不等於 validated science。');$('#research-decisions').innerHTML=data.decisions?.length?data.decisions.map((d)=>`<div class="item"><div class="item-title">${esc(d.statement)}</div><div class="item-meta">${badge(d.status,statusTone(d.status))} · ${fmtDate(d.decided_at)}</div>${d.rationale?`<div class="item-meta">${esc(d.rationale)}</div>`:''}</div>`).join(''):empty('還沒有正式 research decision。');$('#research-artifacts').innerHTML=data.artifacts?.length?data.artifacts.map((a)=>`<div class="item"><div class="item-title">${esc(a.artifact_type)}</div><div class="artifact-path">${esc(a.path)}</div><div class="item-meta">${fmtDate(a.created_at)}${a.git_sha?` · git ${esc(a.git_sha)}`:''}</div></div>`).join(''):empty('還沒有 canonical artifact。');}
async function saveResearchTopic(event){event.preventDefault();const topic=$('#research-topic').value.trim();if(!topic)return toast('研究主軸不能空白',true);try{await api('/api/research/context',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({topic})});toast('研究主軸已以 User explicit assertion 儲存');await loadResearch();}catch(err){toast(`儲存失敗：${err.message}`,true);}}

async function fetchTopics(){try{const res=await api('/api/research/topics');state.topics=res.topics||[];renderTopicsKanban(state.topics);}catch(err){toast(`讀取研究題目失敗：${err.message}`,true);}}

function renderTopicsKanban(topics){
  const stages=['seed','exploring','viable','candidate','selected','killed'];
  const grouped={seed:[],exploring:[],viable:[],candidate:[],selected:[],killed:[]};
  topics.forEach(t=>{if(grouped[t.status])grouped[t.status].push(t);});
  stages.forEach(stage=>{
    const countEl=$(`#stage-count-${stage}`);
    if(countEl)countEl.textContent=String(grouped[stage].length);
    const container=$(`#cards-${stage}`);
    if(!container)return;
    if(!grouped[stage].length){container.innerHTML='<div class="item-meta" style="padding:12px 4px; text-align:center">無</div>';return;}
    container.innerHTML=grouped[stage].map(t=>{
      const pBadge=t.is_primary?'<span class="badge green" style="font-size:0.7rem">Primary</span>':'';
      const evCounts=t.evidence_counts||{};
      const evBadge=`<span class="item-meta" style="font-size:0.72rem">+${evCounts.supports||0} / -${evCounts.contradicts||0} / ?${evCounts.inconclusive||0}</span>`;
      return `<div class="topic-card" onclick="openTopicDetail('${esc(t.id)}')">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px">
          <span class="badge" style="font-size:0.7rem">rev ${t.revision}</span>
          ${pBadge}
        </div>
        <div class="topic-card-title">${esc(t.title)}</div>
        <div class="topic-card-q">${esc(t.research_question)}</div>
        <div class="topic-card-footer">
          ${evBadge}
          <span class="item-meta" style="font-size:0.72rem">${esc(t.next_action||'')}</span>
        </div>
      </div>`;
    }).join('');
  });
}

async function createTopicSeed(title,question){
  if(!title.trim()||!question.trim()){toast('標題與研究問題不能為空',true);return;}
  try{
    await api('/api/research/topics',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({title:title.trim(),research_question:question.trim(),actor:'user'})
    });
    toast('研究題目 Seed 已建立');
    closeModal('create-topic-modal');
    await fetchTopics();
  }catch(err){toast(`建立失敗：${err.message}`,true);}
}

async function openTopicDetail(topicId){
  try{
    const data=await api(`/api/research/topics/${encodeURIComponent(topicId)}`);
    const topic=data.topic;
    state.activeTopic=data;

    $('#modal-topic-title').textContent=topic.title;
    $('#modal-topic-question').textContent=topic.research_question;
    $('#modal-topic-stage').textContent=topic.status;
    $('#modal-topic-stage').className=`badge ${statusTone(topic.status)}`;
    $('#modal-topic-revision').textContent=`rev ${topic.revision}`;

    const pBadge=$('#modal-topic-primary');
    if(pBadge)pBadge.style.display=topic.is_primary?'inline-block':'none';

    const hypContent=$('#modal-topic-hyp-content');
    if(topic.current_hypothesis){
      hypContent.innerHTML=`<div style="color:var(--bright); font-weight:500; margin-bottom:4px">v${topic.current_hypothesis.version}: ${esc(topic.current_hypothesis.statement)}</div><div class="item-meta">Scope: ${esc(topic.current_hypothesis.scope||'未填寫')}</div>`;
    }else{hypContent.innerHTML='<span class="item-meta">尚未啟用核心假說版本</span>';}

    const polContent=$('#modal-topic-policy-content');
    if(data.current_policy){
      const p=data.current_policy;
      polContent.innerHTML=`<div class="item-meta">最低可行性檢查: ${esc((p.min_viable_checks||[]).join(', ')||'無')}</div><div class="item-meta">否證條件: ${esc((p.falsification_conditions||[]).length?JSON.stringify(p.falsification_conditions):'無')}</div><div class="item-meta">停損條件: ${esc((p.stop_conditions||[]).length?JSON.stringify(p.stop_conditions):'無')}</div>`;
    }else{polContent.innerHTML='<span class="item-meta">尚未設定探索政策 (進 Exploring 必填)</span>';}

    const evList=$('#modal-topic-evidence-list');
    if(data.evidence_links&&data.evidence_links.length){
      evList.innerHTML=data.evidence_links.map(e=>`
        <div class="item">
          <div style="display:flex; justify-content:space-between">
            <div>
              <span class="badge ${e.stance==='supports'?'green':(e.stance==='contradicts'?'red':'')}">${esc(e.stance)}</span>
              <span class="badge ${e.validation_status==='validated'?'green':'yellow'}">${esc(e.validation_status)}</span>
              <span style="font-size:0.84rem; margin-left:6px">${esc(e.reason||e.limitations||'無備註')}</span>
            </div>
            ${e.validation_status!=='validated'?`<button class="btn small ghost" onclick="reviewEvidence('${esc(topic.id)}','${esc(e.id)}','validated')">通過審查</button>`:''}
          </div>
        </div>
      `).join('');
    }else{evList.innerHTML='<span class="item-meta">尚無關聯證據</span>';}

    renderTransitionActions(topic,data);

    const setPrimaryBtn=$('#modal-set-primary-btn');
    if(setPrimaryBtn){
      setPrimaryBtn.onclick=async()=>{
        try{
          await api(`/api/research/topics/${encodeURIComponent(topic.id)}/primary`,{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({actor:'user'})
          });
          toast(`已將 ${topic.title} 設為 Primary 題目`);
          await fetchTopics();
          await openTopicDetail(topic.id);
        }catch(err){toast(err.message,true);}
      };
    }

    const addHypBtn=$('#modal-add-hyp-btn');
    if(addHypBtn){
      addHypBtn.onclick=async()=>{
        const stmt=prompt('請輸入核心假說陳述 (Hypothesis Statement)：');
        if(!stmt||!stmt.trim())return;
        const scp=prompt('請輸入適用範圍 (Scope，選填)：')||null;
        try{
          await api(`/api/research/topics/${encodeURIComponent(topic.id)}/hypotheses`,{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({statement:stmt.trim(),scope:scp?scp.trim():null,actor:'user',activate_immediately:true})
          });
          toast('核心假說版本已新增並啟用');
          await fetchTopics();
          await openTopicDetail(topic.id);
        }catch(err){toast(err.message,true);}
      };
    }

    const editPolBtn=$('#modal-edit-policy-btn');
    if(editPolBtn){
      editPolBtn.onclick=async()=>{
        const checks=prompt('請輸入最低可行性檢查 (逗號分隔，例如: memory_fits_16gb, loss_decreases)：');
        if(checks===null)return;
        const checksList=checks.split(',').map(s=>s.trim()).filter(Boolean);
        try{
          await api(`/api/research/topics/${encodeURIComponent(topic.id)}/policy`,{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({min_viable_checks:checksList,actor:'user'})
          });
          toast('探索政策已更新');
          await fetchTopics();
          await openTopicDetail(topic.id);
        }catch(err){toast(err.message,true);}
      };
    }

    const addEvBtn=$('#modal-add-evidence-btn');
    if(addEvBtn){
      addEvBtn.onclick=async()=>{
        const summary=prompt('請輸入證據摘要 (Summary)：');
        if(!summary||!summary.trim())return;
        const stance=prompt('立場：supports / contradicts / inconclusive (預設 supports)：')||'supports';
        try{
          await api(`/api/research/topics/${encodeURIComponent(topic.id)}/evidence`,{
            method:'POST',
            headers:{'Content-Type':'application/json'},
            body:JSON.stringify({
              stance:stance.trim().toLowerCase(),
              evidence_type:'experiment_result',
              source_ref:'manual',
              summary:summary.trim(),
              actor:'user'
            })
          });
          toast('證據已新增');
          await fetchTopics();
          await openTopicDetail(topic.id);
        }catch(err){toast(err.message,true);}
      };
    }

    openModal('topic-detail-modal');
  }catch(err){toast(`讀取題目詳情失敗：${err.message}`,true);}
}

function renderTransitionActions(topic,detail){
  const container=$('#modal-topic-transition-actions');
  const checksContainer=$('#modal-topic-transition-checks');
  if(!container||!checksContainer)return;

  const status=topic.status;
  const rev=topic.revision;
  let html='';
  let checks='';

  if(status==='seed'){
    const hasHyp=!!topic.current_hypothesis_version_id;
    const hasPol=!!detail.current_policy&&detail.current_policy.min_viable_checks.length>0;
    checks=`<div>${hasHyp?'✓':'✗'} 具備核心假說版本</div><div>${hasPol?'✓':'✗'} 具備探索政策與最低可行性檢查</div>`;
    const canExplore=hasHyp&&hasPol;
    html+=`<button class="btn primary" ${canExplore?'':'disabled'} onclick="transitionTopic('${esc(topic.id)}','exploring',${rev})">進入 Exploring</button>`;
  }else if(status==='exploring'){
    const hasValEvidence=(detail.evidence_links||[]).some(e=>e.stance==='supports'&&e.validation_status==='validated');
    checks=`<div>${hasValEvidence?'✓':'✗'} 具備至少一項經驗證的支持性證據 (Validated Supporting Evidence)</div>`;
    html+=`<button class="btn primary" ${hasValEvidence?'':'disabled'} onclick="transitionTopic('${esc(topic.id)}','viable',${rev})">推進至 Viable</button>`;
  }else if(status==='viable'){
    checks='<div>✓ Viable 條件有效；推進至 Candidate 準備選題評估</div>';
    html+=`<button class="btn primary" onclick="transitionTopic('${esc(topic.id)}','candidate',${rev})">推進至 Candidate</button>`;
  }else if(status==='candidate'){
    checks='<div>人決策門檻：需要明確的選題理由與範圍</div>';
    html+=`<button class="btn green" onclick="promptAndTransition('${esc(topic.id)}','selected',${rev},'請輸入選題決策理由：')">正式選題 (Selected)</button>`;
  }

  if(status!=='killed'){
    html+=`<button class="btn ghost red" onclick="promptAndTransition('${esc(topic.id)}','killed',${rev},'請輸入停損 / Kill 理由：')">停損淘汰 (Killed)</button>`;
  }else{
    html+=`<button class="btn yellow" onclick="promptAndTransition('${esc(topic.id)}','exploring',${rev},'請輸入重啟理由 / 新證據：')">重啟探索 (Restart)</button>`;
  }

  checksContainer.innerHTML=checks;
  container.innerHTML=html;
}

async function promptAndTransition(topicId,targetStatus,expectedRevision,promptMsg){
  const rationale=prompt(promptMsg);
  if(!rationale||!rationale.trim())return;
  await transitionTopic(topicId,targetStatus,expectedRevision,rationale.trim());
}

async function transitionTopic(topicId,targetStatus,expectedRevision,rationale=''){
  try{
    await api(`/api/research/topics/${encodeURIComponent(topicId)}/transition`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({target_status:targetStatus,expected_revision:expectedRevision,actor:'user',rationale:rationale})
    });
    toast(`狀態已更新為 ${targetStatus}`);
    await fetchTopics();
    await openTopicDetail(topicId);
  }catch(err){toast(`轉移失敗：${err.message}`,true);}
}

async function reviewEvidence(topicId,evidenceId,status){
  try{
    await api(`/api/research/topics/${encodeURIComponent(topicId)}/evidence/${encodeURIComponent(evidenceId)}/review`,{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({validation_status:status,reason:'人手動審查通過',actor:'user'})
    });
    toast(`證據審查已更新為 ${status}`);
    await fetchTopics();
    await openTopicDetail(topicId);
  }catch(err){toast(`審查失敗：${err.message}`,true);}
}


async function loadPapers(){const data=await api('/api/papers');state.papers=data;renderPapers(data);}
function renderPapers(data){$('#paper-stats').innerHTML=[['Corpus',data.count||0],['Full text',data.fulltext_count||0],['Processed',data.processed_count||0],['Status',data.available?'ready':'missing']].map(([label,value])=>`<div class="stat"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`).join('');filterPapers();}
function filterPapers(){const data=state.papers||{papers:[]};const q=($('#paper-search')?.value||'').trim().toLowerCase();const papers=(data.papers||[]).filter((p)=>!q||[p.title,p.authors,p.venue,p.category,String(p.year||'')].join(' ').toLowerCase().includes(q));$('#paper-visible-count').textContent=`${papers.length} / ${data.count||0}`;if(!data.available){$('#papers-list').innerHTML=empty(data.error?`Research OS DB 無法讀取：${data.error}`:'找不到 .research-os/research.db。');return;}$('#papers-list').innerHTML=papers.length?papers.map((p)=>{const source=safeUrl(p.arxiv_id?`https://arxiv.org/abs/${p.arxiv_id}`:p.source_url);return `<div class="paper"><div class="paper-year">${esc(p.year||'—')}</div><div><div class="paper-title">${esc(p.title)}</div><div class="paper-authors">${esc(p.authors||'')}${p.venue?` · ${esc(p.venue)}`:''}</div><div class="item-meta">${badge(p.category||'paper','blue')} ${badge(p.fulltext_status||'unresolved',p.fulltext_status==='fetched'?'green':'')}</div></div><div class="paper-actions">${source?`<a class="btn small ghost" href="${esc(source)}" target="_blank" rel="noopener">來源 ↗</a>`:''}</div></div>`;}).join(''):empty('沒有符合搜尋條件的 paper。');}

function formatBytes(bytes){if(!bytes)return'0 B';const k=1024;const sizes=['B','KB','MB','GB'];const i=Math.floor(Math.log(bytes)/Math.log(k));return `${(bytes/Math.pow(k,i)).toFixed(1)} ${sizes[i]}`;}
async function loadDocuments(){const data=await api('/api/documents');state.documents=data;renderDocuments(data);}
async function showDocumentPrompt(filename){
  try{
    state.activeDocFilename=filename;
    const data=await api(`/api/documents/prompt/${encodeURIComponent(filename)}`);
    showTextModal(`Agent 派工 Prompt · ${filename}`,data.prompt);
    const ib=$('#modal-ingest-btn');
    if(ib){
      ib.style.display='inline-block';
      ib.textContent='🚀 立即派遣 Agent 更新本地 DB';
    }
    if(navigator.clipboard){
      navigator.clipboard.writeText(data.prompt).then(()=>{
        toast('Agent Prompt 已自動複製到剪貼簿！可直接貼給 Agent。');
      }).catch(()=>{});
    }
  }catch(err){
    toast(`取得 Agent Prompt 失敗：${err.message}`,true);
  }
}
async function ingestDocument(filename){
  if(!filename)return;
  toast(`Agent 正在使用 PyMuPDF C++ 解析 ${filename} 並更新本地 DB...`);
  try{
    const result=await api(`/api/documents/ingest/${encodeURIComponent(filename)}`,{method:'POST'});
    closeModal('text-modal');
    toast(result.evidence_only?'來源已保存；研究 Planner 會依會議與進度安排工作。':`已更新 ${result.tasks_created} 個 Tasks`);
    await Promise.all([loadDocuments(),loadTasks(),loadToday()]);
  }catch(err){
    toast(`Agent 更新 DB 失敗：${err.message}`,true);
  }
}
function renderDocuments(docs){
  $('#doc-count').textContent=String(docs?.length||0);
  const list=$('#documents-list');
  if(!docs||!docs.length){
    list.innerHTML=empty('目前還沒有已存檔的文件或簡報。');
    return;
  }
  list.innerHTML=docs.map((d)=>{
    const extInfo=d.pages?`${d.pages} 頁 · ${Number(d.chars||0).toLocaleString()} 字 · ${esc(d.engine||'PyMuPDF C++')}`:'';
    return `<div class="item"><div style="display:flex;justify-content:space-between;align-items:flex-start;gap:12px;flex-wrap:wrap"><div style="flex:1;min-width:240px"><div class="item-title">${esc(d.display_name||d.filename)}</div><div class="item-meta">${badge(d.date,'blue')} · ${esc(formatBytes(d.size_bytes))}${extInfo?` · <span style="color:var(--bright)">${extInfo}</span>`:''}${d.artifact_id?` · <code>${esc(d.artifact_id)}</code>`:''}</div><div class="artifact-path">${esc(d.path)}</div></div><div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap"><button class="btn small primary" data-doc-ingest="${esc(d.filename)}">🚀 派遣 Agent 更新 DB</button><button class="btn small" data-doc-prompt="${esc(d.filename)}">📋 產生 / 複製 Prompt</button><a class="btn small ghost" href="/api/documents/download/${encodeURIComponent(d.filename)}" target="_blank" rel="noopener">下載 / 開啟 ↗</a></div></div></div>`;
  }).join('');
}
async function uploadDocument(event){
  event.preventDefault();
  const fileInput=$('#doc-file');
  const dateInput=$('#doc-date');
  if(!fileInput?.files?.length)return toast('請選擇要上傳的檔案',true);
  const file=fileInput.files[0];
  const dateVal=dateInput?.value||new Date().toISOString().slice(0,10);
  const btn=$('#doc-upload-btn');
  if(btn)btn.disabled=true;
  try{
    const url=`/api/documents/upload?filename=${encodeURIComponent(file.name)}&date=${encodeURIComponent(dateVal)}`;
    const res=await fetch(url,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});
    if(!res.ok){
      const err=await res.json().catch(()=>({}));
      throw new Error(err.detail||`HTTP ${res.status}`);
    }
    const result=await res.json();
    const extMsg=result.pages?`已由 ${result.engine} 解析 ${result.pages} 頁、${result.chars} 字。`:'';
    toast(`已存檔：${result.filename}。${extMsg}`);
    fileInput.value='';
    await loadDocuments();
    await showDocumentPrompt(result.filename);
  }catch(err){
    toast(`上傳失敗：${err.message}`,true);
  }finally{
    if(btn)btn.disabled=false;
  }
}

async function loadAgents(){const data=await api('/api/agents');state.agents=data;renderAgents(data);}
function runCard(r){return `<div class="item"><div class="item-title">${esc(String(r.agent_type||'agent').toUpperCase())} · ${esc(r.job_type||'job')}</div><div class="item-meta">${badge(r.status,statusTone(r.status))}${r.task_id?` · ${esc(r.task_id)}`:''}${r.branch?` · ${esc(r.branch)}`:''}</div></div>`;}
function renderAgents(data){const runs=data.runs||[];const counts=(name)=>runs.filter((r)=>r.status===name).length;$('#agent-stats').innerHTML=[['Queued',counts('queued')],['Running',counts('running')],['Interrupted',(data.interrupted||[]).length],['Completed',counts('completed')]].map(([label,value])=>`<div class="stat"><strong>${value}</strong><span>${label}</span></div>`).join('');const live=runs.filter((r)=>['queued','running'].includes(r.status));$('#agents-live').innerHTML=live.length?live.map(runCard).join(''):empty('目前沒有 queued / running agent。');const interrupted=data.interrupted||[];$('#agent-interrupted-count').textContent=String(interrupted.length);$('#agents-interrupted').innerHTML=interrupted.length?interrupted.map((r)=>`<div class="item"><div class="item-title">${esc(r.id)} · ${esc(r.task_title||r.task_id||'Task')}</div><div class="item-meta">${badge('interrupted','red')} · 建議 ${esc(r.recommended_action||'inspect')} · Worktree ${r.workspace_exists?'保留':'遺失'}</div><div class="item-actions"><button class="btn small" data-recovery="inspect" data-run="${esc(r.id)}">查看</button><button class="btn small primary" data-recovery="resume" data-run="${esc(r.id)}">Resume</button><button class="btn small" data-recovery="retry_fresh" data-run="${esc(r.id)}">Fresh retry</button><button class="btn small danger" data-recovery="abandon" data-run="${esc(r.id)}">Abandon</button></div></div>`).join(''):empty('沒有中斷 run。');$('#agents-history').innerHTML=runs.length?runs.slice(0,100).map(runCard).join(''):empty('還沒有 agent run history。');}
async function recoverRun(runId,action){if(action==='inspect'){try{const data=await api(`/api/agent-runs/${encodeURIComponent(runId)}/inspect`);const files=(data.workspace_files||[]).slice(0,100).join('\n')||'(沒有可列出的檔案)';showTextModal(`Interrupted run · ${runId}`,`Worktree: ${data.run?.workspace||'(none)'}\nRecommended: ${data.recommended_action}\n\nFiles:\n${files}`);}catch(err){toast(`Inspect 失敗：${err.message}`,true);}return;}const label={resume:'Resume 原 worktree',retry_fresh:'乾淨重跑',abandon:'放棄 run'}[action]||action;if(!confirm(`${label}：${runId}？\n原 worktree 不會被系統偷偷刪除。`))return;try{const result=await api(`/api/agent-runs/${encodeURIComponent(runId)}/recover`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action})});toast(`${label} 已受理${result.new_run_id?` · ${result.new_run_id}`:''}`);await loadAgents();}catch(err){toast(`Recovery 失敗：${err.message}`,true);}}

async function loadSystem(){const data=await api('/api/system');state.system=data;renderSystem(data);}
function renderSystem(data){const doctorStatus=data.doctor?.status||'unknown';$('#system-summary').innerHTML=[['Doctor',doctorStatus],['Sources',data.sources?.length||0],['Schedules',data.schedules?.length||0],['Resources',data.resources?.length||0]].map(([label,value])=>`<div class="stat"><strong>${esc(value)}</strong><span>${esc(label)}</span></div>`).join('');const checks=data.doctor?.checks||{};const healthBlocks=Object.entries(checks).map(([name,detail])=>{const status=detail?.status||(detail?.integrity_ok===true?'healthy':'check');const short=Object.entries(detail||{}).filter(([k])=>!['path','details'].includes(k)).slice(0,4).map(([k,v])=>`${k}: ${typeof v==='object'?JSON.stringify(v):v}`).join(' · ');return `<div class="health"><strong>${esc(name)}</strong><div class="item-meta">${badge(status,statusTone(status))}</div>${short?`<div class="item-meta">${esc(short)}</div>`:''}</div>`;});(data.health||[]).forEach((h)=>healthBlocks.push(`<div class="health"><strong>${esc(h.subsystem)}</strong><div class="item-meta">${badge(h.status,statusTone(h.status))} · ${fmtDate(h.last_heartbeat)}</div>${h.message?`<div class="item-meta">${esc(h.message)}</div>`:''}</div>`));$('#system-health').innerHTML=healthBlocks.join('')||empty('Doctor 尚未回報 health checks。');$('#system-sources').innerHTML=data.sources?.length?data.sources.map((s)=>`<div class="item"><div class="item-title">${esc(s.name)}</div><div class="item-meta">${badge(s.type,'blue')} · scope ${esc(s.scope)} · ${s.enabled?'enabled':'disabled'}${s.last_synced_at?` · sync ${fmtDate(s.last_synced_at)}`:''}</div></div>`).join(''):empty('還沒有 source。Slack 尚未設定也沒關係。');$('#system-schedules').innerHTML=data.schedules?.length?data.schedules.map((s)=>`<div class="item"><div class="item-title">${esc(s.name)}</div><div class="item-meta">${badge(s.trigger_type,'purple')} · ${s.enabled?'enabled':'disabled'}${s.next_run_at?` · next ${fmtDate(s.next_run_at)}`:''}</div></div>`).join(''):empty('沒有 scheduler configuration。');$('#system-resources').innerHTML=data.resources?.length?data.resources.map((r)=>`<div class="item"><div class="item-title">${esc(r.name)}</div><div class="item-meta">${badge(r.status,statusTone(r.status))} · ${esc(r.resource_type)} · quota ${esc(r.quota_used)}/${esc(r.quota_limit)} · cost ${esc(r.cost_estimate)}</div>${r.active_containers?.length?`<div class="item-meta">Active containers: ${esc(r.active_containers.join(', '))}</div>`:''}</div>`).join(''):empty('目前沒有登記 compute resource。');$('#system-paths').innerHTML=`<div class="path-box">Master DB: ${esc(data.master_database||'')}</div><div class="path-box">Research OS DB: ${esc(data.research_os_database||'')}</div><div class="item-meta" style="margin-top:10px">遠端手機入口請使用 Tailscale Serve。Master OS 本身仍只綁 127.0.0.1。</div>`;}

async function dispatchTask(taskId){try{const result=await api(`/api/tasks/${encodeURIComponent(taskId)}/dispatch`,{method:'POST'});toast(`已排隊：${result.run_id}${result.submitted?' · worker 已接手':' · Supervisor 會接手'}`);if(state.page==='tasks')await loadTasks();if(state.page==='today')await loadToday();}catch(err){toast(`派工失敗：${err.message}`,true);}}
async function changeTaskStatus(taskId,status){try{await api(`/api/tasks/${encodeURIComponent(taskId)}/status`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status})});toast(`${taskId} → ${status}`);await loadTasks();}catch(err){toast(`狀態更新失敗：${err.message}`,true);await loadTasks();}}
async function decideApproval(id,decision){try{await api(`/api/approvals/${encodeURIComponent(id)}/decide`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:decision})});toast(decision==='approved'?'已核准':'已駁回');await loadToday();}catch(err){toast(`Approval 失敗：${err.message}`,true);}}


function researchWorkMeta(t){const w=t.work||{};if(!w.scheduled_for)return '';return `<div class="item-meta">${badge(w.ready_today?'今天可做':w.waiting_for?.length?'等待前置工作':'已安排','blue')} ${esc(w.scheduled_for)} · 約 ${esc(w.estimated_minutes)} 分鐘 · ${esc(w.kind||'')}<br>交付：${esc(w.deliverable||'')}<br>來源：${esc((w.evidence_refs||[]).join(' · '))}${w.waiting_for?.length?`<br>前置：${esc(w.waiting_for.join('、'))}`:''}</div>`;}
function renderResearchPlanning(now){
 const p=now.research_planning||{}, prefs=p.preferences||{}, tasks=now.today_tasks||[];
 const total=tasks.reduce((n,t)=>n+(t.work?.estimated_minutes||0),0);
 $('#today-work-total').textContent=`${tasks.length} 項 · 約 ${total} 分鐘`;
 $('#today-research-tasks').innerHTML=tasks.length?tasks.map(t=>`<div class="item"><div class="item-title">${esc(t.title)}</div><div class="item-meta">${esc(t.description)}</div>${researchWorkMeta(t)}<div class="item-actions">${t.agentability==='autonomous'&&t.status==='todo'?`<button class="btn small primary" data-dispatch="${esc(t.id)}">派 Codex</button>`:badge('自己閱讀／判斷','yellow')}</div></div>`).join(''):empty('尚無今天可開始的研究工作。按「現在整理 OS」建立，或到 Tasks 查看等待前置的工作。');
 const run=p.latest_run;
 $('#planning-state').textContent=`每日整理：${prefs.enabled?'啟用':'暫停'} · ${prefs.daily_time||'09:00'} · ${run?`最近執行 ${run.status} (${run.id})`:'尚未執行'}`;
 // Polling must not erase an in-progress form or check-in draft.
 if(!$('#planning-preferences-form').contains(document.activeElement)){
 $('#planner-enabled').value=String(Boolean(prefs.enabled));$('#planner-time').value=prefs.daily_time||'09:00';$('#planner-heavy').value=prefs.heavy_minutes||240;$('#planner-light').value=prefs.light_minutes||60;
 }
 if(!$('#progress-form').contains(document.activeElement))$('#progress-completions').innerHTML=tasks.map(t=>`<label style="display:block"><input type="checkbox" name="progress-completed" value="${esc(t.id)}"> 我確認已完成：${esc(t.title)}</label>`).join('');
 $('#progress-history').innerHTML=(p.history||[]).slice(0,3).map(h=>`<div class="item"><div class="item-meta">${fmtFullDate(h.at)} · ${h.type==='research.progress_reported'?'你的回報':'整理結果'}</div><div class="item-meta">${esc(h.text||h.summary||h.error||'')}</div></div>`).join('');
}
async function submitProgress(event){event.preventDefault();const text=$('#progress-text').value.trim();if(!text)return;const completed_task_ids=$$('input[name="progress-completed"]:checked').map(el=>el.value);try{const r=await api('/api/research/progress',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text,completed_task_ids})});$('#progress-text').value='';toast(`進度已保存 · 整理 ${r.planning?.status||'等待中'}`);await loadToday();}catch(e){toast(e.message,true);}}
async function runDailyPlan(){try{const r=await api('/api/research/planning/run',{method:'POST'});toast(`研究整理：${r.status}${r.reason?' · '+r.reason:''}`);await loadToday();}catch(e){toast(e.message,true);}}
async function savePlanningPreferences(event){event.preventDefault();try{await api('/api/research/planning/preferences',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled:$('#planner-enabled').value==='true',daily_time:$('#planner-time').value,heavy_minutes:Number($('#planner-heavy').value),light_minutes:Number($('#planner-light').value),heavy_days:['sat','sun','mon'],timezone:'Asia/Taipei'})});toast('研究節奏已保存');await loadToday();}catch(e){toast(e.message,true);}}

function bindEvents(){document.addEventListener('click',(event)=>{const nav=event.target.closest('[data-nav]');if(nav){navigate(nav.dataset.nav);return;}const close=event.target.closest('[data-close]');if(close){closeModal(close.dataset.close);return;}const onboard=event.target.closest('[data-onboard]');if(onboard){if(onboard.dataset.onboard==='transcript')openTranscript();else navigate(onboard.dataset.onboard);return;}const dispatch=event.target.closest('[data-dispatch]');if(dispatch){dispatchTask(dispatch.dataset.dispatch);return;}const approval=event.target.closest('[data-approval]');if(approval){decideApproval(approval.dataset.approval,approval.dataset.decision);return;}const docPrompt=event.target.closest('[data-doc-prompt]');if(docPrompt){showDocumentPrompt(docPrompt.dataset.docPrompt);return;}const docIngest=event.target.closest('[data-doc-ingest]');if(docIngest){ingestDocument(docIngest.dataset.docIngest);return;}const ingest=event.target.closest('[data-meeting-ingest]');if(ingest){openTranscript(ingest.dataset.meetingIngest,ingest.dataset.meetingTime,ingest.dataset.meetingKind);return;}const pack=event.target.closest('[data-meeting-pack]');if(pack){generatePack(pack.dataset.meetingPack);return;}const recovery=event.target.closest('[data-recovery]');if(recovery){recoverRun(recovery.dataset.run,recovery.dataset.recovery);return;}if(event.target.classList.contains('modal-backdrop'))closeModal(event.target.id);});document.addEventListener('change',(event)=>{if(event.target.matches('[data-task-status]'))changeTaskStatus(event.target.dataset.taskStatus,event.target.value);});
  $('#progress-form')?.addEventListener('submit',submitProgress);$('#plan-now')?.addEventListener('click',runDailyPlan);$('#planning-preferences-form')?.addEventListener('submit',savePlanningPreferences);
  $('#create-topic-seed-btn')?.addEventListener('click',()=>{const title=$('#topic-seed-title');const q=$('#topic-seed-question');if(title)title.value='';if(q)q.value='';openModal('create-topic-modal');});
  $('#submit-topic-seed-btn')?.addEventListener('click',()=>{const title=$('#topic-seed-title')?.value||'';const q=$('#topic-seed-question')?.value||'';createTopicSeed(title,q);});
  $('#refresh-btn')?.addEventListener('click',()=>refreshPage());$('#quick-ingest')?.addEventListener('click',()=>openTranscript());$('#hero-ingest')?.addEventListener('click',()=>openTranscript());$('#meeting-ingest-top')?.addEventListener('click',()=>openTranscript());$('#dispatch-focus')?.addEventListener('click',()=>state.currentFocusTaskId&&dispatchTask(state.currentFocusTaskId));$('#submit-transcript')?.addEventListener('click',submitTranscript);$('#advisor-routine-form')?.addEventListener('submit',saveAdvisorRoutine);$('#adhoc-meeting-form')?.addEventListener('submit',saveAdhocMeeting);$('#research-topic-form')?.addEventListener('submit',saveResearchTopic);$('#paper-search')?.addEventListener('input',filterPapers);$('#document-upload-form')?.addEventListener('submit',uploadDocument);$('#copy-modal-text-btn')?.addEventListener('click',()=>{const text=$('#text-modal-body')?.textContent;if(!text)return toast('內容為空',true);navigator.clipboard.writeText(text).then(()=>{toast('Prompt 已成功複製到剪貼簿！可直接貼給 Agent。');}).catch(()=>{toast('請手動選取文字複製。',true);});});$('#modal-ingest-btn')?.addEventListener('click',()=>{if(state.activeDocFilename)ingestDocument(state.activeDocFilename);});const docDateInput=$('#doc-date');if(docDateInput&&!docDateInput.value)docDateInput.value=new Date().toISOString().slice(0,10);window.addEventListener('hashchange',()=>navigate(location.hash.slice(1)||'today',false));document.addEventListener('keydown',(event)=>{if(event.key==='Escape')$$('.modal-backdrop.open').forEach((el)=>closeModal(el.id));});}

bindEvents();navigate(location.hash.slice(1)||'today',false);setInterval(()=>{if(document.hidden)return;if(state.page==='today'||state.page==='agents')refreshPage(state.page);},12000);
