/* ======================================================================
   shell.js — DOM wiring. Renders ONLY the canonical UiState (buildUiState) and forwards user intent to the bridge.
   No ORION knowledge, no raw backend JSON, no authorization decisions. One code path serves PC and phone (.desk vs .phone CSS).
   ====================================================================== */
const B=window.ORION_BRIDGE;
if(!B){document.body.innerHTML='<pre style="color:#d98276;padding:20px;white-space:pre-wrap">STRATA: no bridge loaded. index.html loads bridge/real-bridge.js (live); demo.html loads bridge/mock-bridge.js (demo).</pre>';throw new Error('STRATA: no bridge')}
V.mode=B.mode==='mock'?'mock':'live';
let forced=new URLSearchParams(location.search).get('view');
const el=(tag,cls,html)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(html!=null)e.innerHTML=html;return e};
const hex2=c=>c==='#c9eef5'?'#76cfe4':c;
const LEGACY=(window.STRATA_CONFIG&&window.STRATA_CONFIG.legacy)||[];

function mode(){PHONE=forced?forced==='phone':innerWidth<=760;
 app.classList.toggle('phone',PHONE);app.classList.toggle('desk',!PHONE);app.classList.toggle('framed',PHONE&&innerWidth>760);
 build();slots.card.sig='';slots.rv.sig='';paint()}
addEventListener('resize',()=>{if(!forced)mode()});

let toastT=0;
function toast(t){const e=$('toast');e.textContent=t;e.classList.add('on');clearTimeout(toastT);toastT=setTimeout(()=>e.classList.remove('on'),5200)}
function msg(role,text){const m=el('div','m '+role);m.textContent=text;$('chat').appendChild(m);$('chat').scrollTop=1e6}
function layer(id,on){$(id).classList.toggle('on',!!on);if(id==='cc'&&on){ccSig='';updateCC(true)}}
function sheet(id,on){$(id).classList.toggle('on',!!on)}
const closeSheets=()=>{sheet('evd',0);sheet('vp',0)};

/* ---------- main paint: everything on screen comes from buildUiState(V) ---------- */
const slots={card:{sig:'',el:null},rv:{sig:'',el:null}};
function paint(){
 const ui=V.ui=buildUiState(V),o=ui.orion,col=o.color||'#76cfe4';
 if(o.state!==S.state){S.state=o.state;tgt=col;wake()}
 app.style.setProperty('--accent',hex2(col));
 $('stl').textContent=o.label;$('stl').style.color=hex2(col);
 const a=$('act');a.textContent=o.activity;a.classList.toggle('live',['thinking','verifying','acting','preparing','specialist'].includes(o.state)&&!ui.stale);
 $('conn').dataset.s=ui.connection.status;$('connT').textContent=LINKTXT[ui.connection.status]||'';
 const p=$('proj');p.textContent=ui.project.label;p.hidden=!ui.project.label;
 const au=$('auth');au.textContent=ui.authChip;au.classList.toggle('on',!!ui.authChip);
 const g=$('ghchip');g.textContent=ui.ghChip;g.hidden=!ui.ghChip;
 const lv=$('lvchip');lv.hidden=!(ui.localBrain&&ui.localBrain.state==='running'&&ui.localBrain.livePreview);lv.textContent='View live output (unverified)';
 paintStop(ui);paintTimeline(ui);paintNotice(ui);mountCard(ui);mountReviewers(ui);paintPair(ui);
 if(window.ORION_PRODUCT&&ORION_PRODUCT.paint)ORION_PRODUCT.paint(ui);
 if($('evd').classList.contains('on')&&V.ev&&V.ev.live)renderEvidence();
 if($('cc').classList.contains('on'))updateCC(false);
 $('demo').hidden=V.mode!=='mock';app.classList.toggle('isdemo',V.mode==='mock');app.classList.toggle('demomode',V.mode==='mock');
 $('inp').placeholder=ui.connection.status==='unpaired'?'Pair this device first':ui.stale?'PC not fully connected · requests may fail':'Ask ORION…'}

/* Stop is ALWAYS present. Disabled when nothing stoppable runs. Every stop is targeted at one running thing. */
function paintStop(ui){const b=$('stopb'),n=ui.stops.length;b.disabled=!n;b.classList.toggle('armed',!!n);
 b.textContent=n>1?'Stop… ('+n+')':'Stop';b.title=n?'Stop '+ui.stops.map(s=>s.label).join(', '):(ui.action&&ui.action.note)||'Nothing is running that can be stopped'}
async function doStop(s){const r=await B.call('POST',s.route,s.body,{label:'Stop · '+s.label});report(r)}
$('stopb').onclick=async()=>{const st=V.ui.stops;if(!st.length)return;if(st.length===1)return doStop(st[0]);
 V.ev={title:'Stop what?',items:[],stops:true};renderEvidence();sheet('vp',0);sheet('evd',1)};

function paintTimeline(ui){const t=$('tl');t.hidden=!ui.timeline.length;
 t.innerHTML=ui.timeline.map(s=>`<span class="tls ${s.status}" title="${esc(s.basis)}"><i></i>${esc(s.label)}</span>`).join('')}

function paintNotice(ui){const n=$('notice'),c=V.cmd;let m=null;
 if(c&&c.cls&&c.cls!=='sent'&&V.noticeSeen!==c.at)m={sev:'error',text:commandMessage(c),dismiss:c.at};
 else if(['stale','reconnecting','offline','backend_error','connecting'].includes(ui.connection.status)&&ui.connection.status!=='connecting')m={sev:ui.connection.status==='stale'?'warn':'error',text:ui.orion.detail};
 else if(ui.reviewers.status==='failed')m={sev:'error',text:'Reviewer failure: every reviewer in the last run failed'};
 else if(ui.reviewers.status==='partial'&&ui.reviewers.visible)m={sev:'warn',text:'Partial reviewer result: some reviewers failed'};
 n.hidden=!m;if(m){n.className='notice '+m.sev;n.textContent=m.text;if(m.dismiss){const x=el('button','nx','✕');x.setAttribute('aria-label','Dismiss');x.onclick=()=>{V.noticeSeen=m.dismiss;paint()};n.appendChild(x)}}}

/* ---------- the single main card: approval | blocked | error | result ---------- */
function mountCard(ui){
 let kind='',sig='',data=null;
 if(ui.approval){kind='approval';sig='A'+ui.approval.sig+ui.approval.dismissedLocally;data=ui.approval}
 else if(ui.blocked){kind='blocked';sig='B'+ui.blocked.reason;data=ui.blocked}
 else if(ui.errorCard){kind='error';sig='E'+ui.errorCard.reason;data=ui.errorCard}
 else if(ui.lastResult){kind='result';sig='R'+ui.lastResult.fingerprint;data=ui.lastResult}
 const host=PHONE?$('chat'):$('rz'),c=slots.card;
 if(sig!==c.sig){
  if(c.el)c.el.remove();c.el=null;c.sig=sig;
  if(kind){c.el=buildCard(kind,data);host.appendChild(c.el);
   if(PHONE)$('chat').scrollTop=Math.max(0,c.el.offsetTop-6);else{app.classList.remove('chat');msg('or',kind==='result'?data.headline:kind==='approval'?data.title:kind==='blocked'?'Blocked by ORION: '+data.reason:'Local Brain error')}}}
 app.classList.toggle('result',!!c.el);if(c.el)c.el.classList.toggle('dim',ui.stale)}

const LADDER={established:['✓','established'],not_established:['○','not established'],not_reported:['–','not reported'],failed:['✕','failed'],pending:['…','pending']};
const ladderHTML=l=>`<ul class="ladder2">${l.map(r=>{const m=LADDER[r.status]||['?',r.status];return`<li class="${r.status}"><b>${m[0]}</b><span>${esc(r.label)}<small>${esc(m[1])}${r.basis?' · '+esc(r.basis):''}</small></span></li>`}).join('')}</ul>`;
const verdictClass=v=>({PASS:'pass',FAILED:'fail',ERROR:'fail',BLOCKED:'warn'})[v]||'none';

function buildCard(kind,d){
 const c=el('div','card main '+kind);
 if(kind==='approval'){
  V.ev={title:'Generated PowerShell',items:[{k:'Hand',v:d.hand},{k:'Preflight',v:d.checks.preflight},{k:'Semantic quality check',v:d.checks.quality},{k:'Approved script hash',v:d.checks.approvedHash||'—'},{k:'Local Brain model',v:d.model||'—'},{k:'Script (exact)',v:d.script,pre:true}]};
  if(d.dismissedLocally){c.innerHTML=`<div class="cap">REJECTED IN THIS VIEW</div><h3>You rejected this draft</h3><p>Nothing ran. ORION has no reject route, so the draft stays on the PC until a new request replaces it. It cannot run unless someone presses Approve &amp; Run.</p><div class="acts"><button class="btn" data-unreject>Review again</button></div>`}
  else c.innerHTML=`<div class="cap">APPROVAL NEEDED</div><h3>${esc(d.title)}</h3>
   <dl class="facts"><dt>Hand</dt><dd>${esc(d.hand)}</dd><dt>Target</dt><dd>${esc(d.target.project)} · ${esc(d.target.repo)} @ ${esc(d.target.branch)}</dd><dt>Working dir</dt><dd>${esc(d.target.cwd)}</dd>
   <dt>Why</dt><dd>${esc(d.why)}</dd><dt>Command</dt><dd>${esc(d.summary)}</dd><dt>Checks passed</dt><dd>Preflight ${esc(d.checks.preflight)} · Quality ${esc(d.checks.quality)}${d.checks.approvedHash?' · hash '+esc(d.checks.approvedHash)+'…':''}</dd><dt>Scope</dt><dd>${esc(d.risk)}</dd></dl>
   <div class="acts big"><button class="btn pri" data-approve>Approve &amp; Run</button><button class="btn" data-reject>Reject</button><a class="btn" href="/">Edit in Classic Remote</a></div>
   <details><summary>Technical details · view the exact script</summary><pre>${esc(d.script)}</pre></details>`}
 else if(kind==='blocked'){
  const T={preflight:"Blocked by ORION's preflight",quality:'Failed semantic verification',quality_error:'Verification could not run',other:'Blocked by ORION'}[d.kind];
  V.ev={title:T,items:[{k:'Reason',v:d.reason},{k:'Preflight',v:d.preflight.state+(d.preflight.reason?' · '+d.preflight.reason:'')},{k:'Semantic quality check',v:d.quality.state+(d.quality.reason?' · '+d.quality.reason:'')},
   ...(d.unsupported.length?[{k:'Unsupported claims',v:d.unsupported.join('\n'),pre:true}]:[]),...(d.missing.length?[{k:'Missing evidence',v:d.missing.join('\n'),pre:true}]:[])]};
  c.innerHTML=`<div class="cap">${d.kind==='preflight'?'BLOCKED':d.kind==='other'?'BLOCKED':'FAILED VERIFICATION'}</div><h3>${esc(T)}</h3><p>${esc(d.reason)}</p><div class="note">Nothing was executed.</div>
   <div class="acts"><button class="btn pri" data-revise>Ask Local Brain to revise</button></div><button class="evchip" data-ev>View evidence</button>`}
 else if(kind==='error'){V.ev={title:'Local Brain error',items:[{k:'Error',v:d.reason,pre:true}]};c.innerHTML=`<div class="cap">ERROR</div><h3>Local Brain error</h3><p>${esc(d.reason)}</p><button class="evchip" data-ev>View evidence</button>`}
 else{
  V.ev={title:d.headline,items:d.evidence,ladder:d.ladder};
  c.innerHTML=`<div class="vrow"><span class="chipv exec">EXECUTION · ${esc(d.executionState)}</span><span class="chipv ${verdictClass(d.verdict)}">VERDICT · ${esc(d.verdict||'none')}</span></div>
   <h3>${esc(d.headline)}</h3>${d.body?`<p>${esc(d.body)}</p>`:''}${d.rows.length?`<div class="rows">${d.rows.map(x=>`<div><span>${esc(x[0])}</span><b>${esc(x[1])}</b></div>`).join('')}</div>`:''}${d.note?`<div class="note">${esc(d.note)}</div>`:''}
   <details open><summary>What ORION established</summary>${ladderHTML(d.ladder)}</details><button class="evchip" data-ev>View evidence</button>`}
 c.addEventListener('click',async e=>{const t=e.target;
  if(t.closest('[data-ev]'))return openEvidence();
  if(t.closest('[data-reject]')){dispatch({type:'dismiss',sig:d.sig});return paint()}
  if(t.closest('[data-unreject]')){dispatch({type:'undismiss',sig:d.sig});return paint()}
  if(t.closest('[data-approve]')){const b=t.closest('[data-approve]');b.disabled=true;try{report(await B.approveScript(d.script,e))}catch(x){toast('Approve & Run failed: '+x.message)}b.disabled=false}
  if(t.closest('[data-revise]')){try{report(await B.revise(e))}catch(x){toast('Revise failed: '+x.message)}}});
 return c}

function report(r){const e={at:Date.now(),label:r.label||r.route,route:r.route,method:r.method,status:r.status,cls:r.cls,message:r.message};
 V.noticeSeen=null;toast(commandMessage(e));paint()}

/* ---------- reviewers: name, status, closing excerpt (verbatim, not a summary), expandable full output ---------- */
function mountReviewers(ui){const R=ui.reviewers,r=slots.rv;
 const sig=R.visible?JSON.stringify(R.items.map(i=>[i.id,i.phase,i.excerpt.length,i.output.length,i.error])):'';
 if(sig===r.sig)return;r.sig=sig;if(r.el){r.el.remove();r.el=null}
 if(!R.visible)return;
 const done=R.items.filter(i=>i.phase==='done').length;
 const c=el('div','card rvs');c.innerHTML=`<div class="cap">REVIEWERS · ${esc(R.status.toUpperCase())}</div>${R.items.map(i=>`<div class="rvi ${i.phase}"><div class="rvh"><b>${esc(i.provider)} · ${esc(i.model)}</b><span class="chipv ${i.phase==='failed'?'fail':i.phase==='done'?'pass':'none'}">${esc(i.phase.toUpperCase())}</span></div>
  <p class="ex">${i.error?'ERROR: '+esc(i.error):i.excerpt?esc(i.excerpt):'No output yet'}</p>${i.output?`<details><summary>Full output</summary><pre>${esc(i.output)}</pre></details>`:''}</div>`).join('')}
  <div class="note2">Closing excerpts are verbatim, not summaries.${done>1?' ORION does not compute agreement between reviewers: read the excerpts or open the full output.':''}</div>`;
 r.el=c;(PHONE?$('chat'):$('rvz')).appendChild(c)}

/* ---------- evidence sheet ---------- */
function openEvidence(live){V.ev=V.ev||{title:'Evidence',items:[]};V.ev={...V.ev,live:!!live,stops:false};renderEvidence();sheet('vp',0);sheet('evd',1)}
function renderEvidence(){const ui=V.ui,e=V.ev;let items=e.items||[],title=e.title;
 if(e.stops){$('evd').innerHTML=`<div class="sh"><h3>Stop what?</h3><button class="ib" data-close>Close</button></div><p style="font-size:13px;color:var(--tx2)">Each stop is targeted at one running thing.</p>${ui.stops.map((s,i)=>`<div class="ev"><button class="btn stopbtn" data-stop="${i}">Stop · ${esc(s.label)}</button></div>`).join('')}<div class="ev"><button class="btn danger" data-stopall>Stop all running (${ui.stops.length}, one by one)</button></div>`;return}
 if(e.live&&ui.localBrain&&ui.localBrain.livePreview){title='Local Brain · live (unverified)';items=[{k:'Generated so far. Not verified. May be wrong or incomplete.',v:ui.localBrain.livePreview,pre:true}]}
 const last=V.cmd?[{k:'Last command',v:commandMessage(V.cmd)}]:[];
 $('evd').innerHTML=`<div class="sh"><h3>${esc(title)}</h3><button class="ib" data-close>Close</button></div>${e.ladder?`<div class="ev"><div class="k">What ORION established</div>${ladderHTML(e.ladder)}</div>`:''}${[...items,...last].map(i=>`<div class="ev"><div class="k">${esc(i.k)}</div>${i.pre?`<pre>${esc(i.v)}</pre>`:`<div class="v">${esc(i.v)}</div>`}</div>`).join('')}`}
$('evd').addEventListener('click',async e=>{const s=e.target.closest('[data-stop]'),all=e.target.closest('[data-stopall]');
 if(s){await doStop(V.ui.stops[+s.dataset.stop]);closeSheets()}
 if(all){const list=[...V.ui.stops];for(const x of list)await doStop(x);closeSheets()}});

/* ---------- Live View: UI + states only. There is no stream and none is faked. Viewing never authorizes control. ---------- */
const VIEW_STATES=['not_configured','off','starting','live','degraded','locked','stopped'];
let vp={state:'not_configured'};
function renderVP(){
 $('vp').innerHTML=`<div class="sh"><h3>Live View</h3><button class="ib" data-close>Close</button></div>
 <div class="ladder">${VIEW_STATES.map(s=>`<span class="${vp.state===s?'on':''}">${s.replace('_',' ').toUpperCase()}</span>`).join('')}</div>
 <div id="vstage"><div><b>Live View · Not configured</b>There is no desktop stream yet, so nothing is shown. ORION will never display a fake frame or claim a stream is active when it is not.</div></div>
 <p class="vnote">Seeing the desktop never authorizes ORION or you to act on it. Planned: a separate media channel from ORION's state, view-only first, started by an explicit request, with a visible indicator on the PC, a timeout and revocation. No mouse or keyboard control.</p>
 <div class="acts"><button class="btn" disabled>Start Live View</button></div>`}
function openVP(){renderVP();sheet('evd',0);sheet('vp',1)}
window.STRATA={bridge:B,V,buildUiState,view:{states:VIEW_STATES,   /* extension point: the later media channel calls STRATA.view.set('live',{element}) */
 set(state,info){vp.state=state;const live=state==='live';app.classList.toggle('viewing',live);S.orb=live;wake();renderVP();if(live&&info&&info.element){const st=$('vstage');st.textContent='';st.appendChild(info.element)}}}};

/* ---------- pairing (same semantics as Remote V1) ---------- */
function paintPair(ui){const on=ui.connection.status==='unpaired',p=$('pair');p.classList.toggle('on',on);
 if(!on){p.dataset.built='';return}
 if(p.dataset.built)return;p.dataset.built='1';
 p.innerHTML=`<div class="gb"><div class="cap" style="margin-bottom:6px">ORION</div><h3>Pair this device</h3><p>Enter the 6-digit pairing code ORION prints on the PC. Pairing authorizes this product surface only; it does not change execution authority.</p><input id="pcode" inputmode="numeric" maxlength="6" autocomplete="one-time-code" aria-label="Pairing code"><p class="perr" id="perr"></p><button class="btn pri" id="pgo">Pair</button>${LEGACY.map(l=>`<a class="btn" href="${esc(l.href)}">${esc(l.label)}</a>`).join('')}</div>`;
 $('pgo').onclick=async()=>{const r=await B.pair($('pcode').value);if(!r.ok)$('perr').textContent=r.error;else p.dataset.built=''}}

/* ---------- Command Center (descriptor-driven; advanced detail lives here, not on the main screen) ---------- */
let ccSig='',rawSel='status';
const redact=(k,v)=>/^(api_key|token|secret|control_token)$/i.test(k)?'[redacted]':v;
function rawText(){const b=V.backend;
 const t={status:()=>b?JSON.stringify(b.raw,redact,1):'No status yet.',local:()=>b&&b.local.output,manual:()=>b&&b.manual.output,gh:()=>b&&b.gh.lastOutput,runner:()=>b&&b.gh.runnerLog,
  reviewers:()=>b&&b.reviewer.items.map(i=>'=== '+i.provider+' · '+i.model+' ['+i.phase+']\n'+(i.error?'ERROR: '+i.error+'\n':'')+i.output).join('\n\n'),
  commands:()=>V.cmdlog.map(c=>new Date(c.at).toLocaleTimeString()+'  '+(c.method||'')+' '+(c.route||'')+'  '+c.cls+'  '+(c.status||'-')+(c.message?'  '+c.message:'')).join('\n')}[rawSel]();
 return String(t||'(empty)').slice(-9000)}
function linkInfoHTML(){const i=B.describe(),ui=V.ui,c=ui.connection,L=(window.STRATA_CONFIG||{}).link||{};
 const row=(a,b)=>`<div class="kv"><span>${esc(a)}<small>${esc(b)}</small></span><span></span></div>`;
 return row('PC link',LINKTXT[c.status]||c.status)+row('Update mechanism',i.events||'')+row('Thresholds (since last good snapshot)','STALE after '+(L.staleAfterMs||6000)/1000+'s · RECONNECTING after '+(L.reconnectingAfterMs||20000)/1000+'s · DISCONNECTED after '+(L.offlineAfterMs||90000)/1000+'s')+
  row('Offline behavior','Shows DISCONNECTED; keeps last known data dimmed; never invents state; keeps retrying automatically')+row('Network path','Not reported by ORION')+
  row('Endpoint',i.base||'—')+row('Latency · last update',(c.latencyMs!=null?c.latencyMs+' ms':'—')+' · '+(c.ageMs!=null?Math.round(c.ageMs/1000)+'s ago':'never'))+row('Paired',c.paired?'yes (token stored in this browser)':'no')+(c.error?row('Last error',c.error):'')}
function updateCC(force){
 const data=buildConnectors(V.ui,{blockedCalls:(B.describe()||{}).blockedCalls}),sig=JSON.stringify(data,(k,v)=>k==='status_ts'?undefined:v)+V.ui.connection.status;
 if(force||sig!==ccSig){ccSig=sig;const keep=$('cc').scrollTop;resetActions();
  $('ccg').innerHTML=`<section class="pn cn wide" data-s="${V.ui.connection.status==='live'?'ready':'degraded'}"><h4 class="cap">Connectivity</h4><div id="cinfo" class="cinfo">${linkInfoHTML()}</div>
   <div class="eng"><button class="btn" id="refreshnow" title="Updates are automatic. This is a debug fallback.">Refresh now</button></div>
   <input id="epin" placeholder="Endpoint override (blank = same origin)" value="${esc(B.describe().base!=='(same origin)'&&B.describe().base!=='DEMO'?B.describe().base:'')}" aria-label="Endpoint"><div class="eng"><button class="btn" id="epsave">Save endpoint</button><button class="btn danger" id="forget">Forget pairing</button></div></section>
   ${data.active.map(renderConnector).join('')}${renderPlanned(data.planned)}
   <section class="pn cn wide" data-id="logs"><h4 class="cap">Logs</h4><select id="rawsel" aria-label="Log source"><option value="status">Raw /api/status</option><option value="local">Local Hands output</option><option value="manual">Manual lane output</option><option value="gh">GitHub run output</option><option value="runner">Runner log</option><option value="reviewers">Reviewer outputs</option><option value="commands">Commands sent by this UI</option></select><pre id="rawpre"></pre></section>`;
  $('rawsel').value=rawSel;$('cc').scrollTop=keep}
 const ci=$('cinfo');if(ci)ci.innerHTML=linkInfoHTML();const rp=$('rawpre');if(rp)rp.textContent=rawText()}
async function runAct(id,evt){const a=ACT[id];if(!a)return;
 if(a.ui==='memory')return openMemory();
 if(a.confirm&&!confirm(a.confirm))return;
 try{const r=a.fn==='revise'?await B.revise(evt):await B.call(a.call.method,a.call.route,a.call.body,{label:a.label,gesture:evt});report(r)}catch(e){toast(a.label+' failed: '+e.message)}}
$('ccg').addEventListener('click',e=>{
 const b=e.target.closest('[data-act]');if(b)return runAct(b.dataset.act,e);
 if(e.target.id==='refreshnow'){B.refresh();toast('Refreshing now')}
 if(e.target.id==='epsave'){B.setBase($('epin').value.trim());toast('Endpoint saved')}
 if(e.target.id==='forget'&&confirm('Forget this device pairing? You will need a new pairing code.'))B.forgetPairing()});
$('ccg').addEventListener('change',e=>{if(e.target.id==='rawsel'){rawSel=e.target.value;$('rawpre').textContent=rawText()}});
$('legacy').innerHTML='';$('legacy').hidden=true;

/* ---------- wiring ---------- */
$('bar').onsubmit=async e=>{e.preventDefault();const t=$('inp').value.trim();if(!t)return;
 if(V.ui.connection.status==='unpaired'){toast('Pair this device first');return}
 $('inp').value='';
 if(window.ORION_CHAT_HISTORY?.resumeLive)ORION_CHAT_HISTORY.resumeLive();
 const turn={conversation_id:V.convId,turn_id:'t'+Date.now().toString(36),text:t,source:PHONE?'phone-text':'pc-text'};V.turns.push(turn);   // client-side only; the PC-owned turn journal is a later backend slice
 msg('you',t);if(!PHONE)app.classList.add('chat');
 const cur=V.ui.lastResult;if(cur)dispatch({type:'ignoreResult',sig:cur.fingerprint});
 msg('sys','Sent to ORION. I will show only what it reports.');
 try{const r=await B.sendGoal(t,turn);if(!r.ok)msg('err',({timeout:'No answer in time. ORION may still be working: watch the state. ',unreachable:'Could not reach the PC. ',rejected:'ORION rejected this request: '})[r.cls]+(r.error||''))}catch(x){msg('err','Request failed: '+x.message)}
 paint()};
$('histb').onclick=()=>app.classList.toggle('chat');
$('ccb').onclick=()=>layer('cc',1);$('ccx').onclick=()=>layer('cc',0);$('ccm').onclick=()=>openMemory();
$('viewb').onclick=$('viewb2').onclick=openVP;
$('conn').onclick=()=>layer('cc',1);$('ghchip').onclick=()=>layer('cc',1);
$('gear').onclick=()=>{S.low=!S.low;$('gear').style.color=S.low?'var(--ion)':'';build()};
app.addEventListener('click',e=>{if(e.target.closest('[data-close]'))closeSheets()});
$('lvchip').onclick=()=>openEvidence(true);
addEventListener('keydown',e=>{if(e.key==='Escape'){if(app.classList.contains('mem'))closeMemory();else{layer('cc',0);closeSheets()}}});
function tick(){const d=new Date();$('clk').textContent=d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});$('dt').textContent=d.toLocaleDateString([],{weekday:'long',day:'numeric',month:'long'})}

/* demo-only state picker (mock bridge only) */
if(B.mode==='mock'){const sel=el('select');sel.setAttribute('aria-label','Demo state');sel.id='demosel';sel.innerHTML=B.demoStates.map(s=>`<option>${s}</option>`).join('');sel.onchange=()=>B.demoState(sel.value);$('demo').appendChild(sel)}

let shownBrainReply='';
B.subscribe(ev=>{
 if(ev.type==='snapshot'){
  dispatch({type:'snapshot',model:ev.model});
  const L=ev.model&&ev.model.local;
  const live=window.ORION_LIVE_BRAIN_CHAT;
  if(L&&L.conversationId&&window.ORION_CHAT_HISTORY&&ORION_CHAT_HISTORY.load&&!ORION_CHAT_HISTORY.browsing&&L.conversationId!==V.convId){
   ORION_CHAT_HISTORY.load(L.conversationId);
  }
  if(live&&L&&!window.ORION_CHAT_HISTORY?.browsing){
   live.update(L,$('chat'));
   if((L.brainState==='running'&&L.preview)||L.brainState==='ready'){
    if(!PHONE)app.classList.add('chat');
   }
  }else if(!window.ORION_CHAT_HISTORY?.browsing){
   const replyKey=L&&L.brainStartedUtc||'';
   if(L&&L.brainState==='ready'&&L.conclusion&&replyKey&&replyKey!==shownBrainReply){
    shownBrainReply=replyKey;
    msg('or',L.conclusion);
    if(!PHONE)app.classList.add('chat');
   }
  }
 }else if(ev.type==='link')dispatch({type:'link',link:ev.link});
 else if(ev.type==='lists')dispatch({type:'lists',lists:ev.lists});
 else if(ev.type==='command'){dispatch({type:'command',entry:ev.entry});if(ev.entry.cls!=='sent'||ev.entry.label!=='Ask ORION')toast(commandMessage(ev.entry))}
 paint()});
tick();setInterval(tick,15000);setInterval(()=>{if(!document.hidden)paint()},1000);
/* watchdog: if the poll loop ever stops (it should not), restart it. Updates must never depend on pressing Refresh. */
setInterval(()=>{const d=B.describe&&B.describe();if(B.mode==='live'&&!document.hidden&&V.link.lastPollAt&&Date.now()-V.link.lastPollAt>30000)B.refresh()},10000);
mode();wake();B.start();
