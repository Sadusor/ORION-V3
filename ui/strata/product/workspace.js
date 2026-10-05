/* ======================================================================
   workspace.js — ORION product navigation and high-level surfaces.
   Reads ONLY canonical UiState. No raw backend JSON, no authority decisions.
   Desktop and phone share the same information architecture.
   ====================================================================== */
const ORION_PRODUCT=(function(){
 let current='home',lastUi=null,built=false;
 const escP=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const nav=[['home','Home','⌂'],['work','Work','◇'],['ai','AI','✦'],['memory','Memory','◌'],['connectors','Connectors','⛓'],['system','System','◎']];
 function init(){if(built)return;built=true;
  const a=document.getElementById('app'),top=document.getElementById('top');
  const n=document.createElement('nav');n.id='product-nav';n.setAttribute('aria-label','ORION sections');
  n.innerHTML=nav.map(([id,label,icon])=>`<button data-view="${id}" title="${label}" aria-label="${label}"><i>${icon}</i><span>${label}</span></button>`).join('');
  a.appendChild(n);
  const lanes=document.createElement('section');lanes.id='lane-strip';lanes.setAttribute('aria-label','Active ORION lanes');top.insertAdjacentElement('afterend',lanes);
  const ws=document.createElement('section');ws.id='workspace';ws.className='layer product-workspace';ws.setAttribute('aria-label','ORION workspace');
  ws.innerHTML='<header class="ws-head"><div><span class="cap" id="ws-kicker">ORION</span><h2 id="ws-title">Workspace</h2></div><button class="ib" id="ws-close">Close</button></header><div id="ws-body"></div>';
  a.appendChild(ws);
  n.addEventListener('click',e=>{const b=e.target.closest('[data-view]');if(b)open(b.dataset.view)});
  document.getElementById('ws-close').onclick=()=>open('home');
  markNav();
 }
 function open(view){
  init();current=view||'home';
  if(current==='memory'){current='home';if(typeof openMemory==='function')openMemory();markNav('memory');return}
  const ws=document.getElementById('workspace');ws.classList.toggle('on',current!=='home');
  document.getElementById('app').classList.toggle('workspace-open',current!=='home');markNav();if(lastUi)renderView(lastUi);
 }
 function markNav(temp){const n=document.getElementById('product-nav');if(!n||typeof n.querySelectorAll!=='function')return;n.querySelectorAll('[data-view]').forEach(b=>b.classList.toggle('on',b.dataset.view===(temp||current)))}
 const laneTone=s=>({thinking:'live',acting:'live',active:'live',ready:'ready',idle:'idle',not_selected:'muted',not_connected:'muted',degraded:'warn',blocked:'bad',error:'bad'}[s]||'muted');
 function paintLanes(ui){const h=document.getElementById('lane-strip');if(!h)return;const lanes=ui.lanes||[];
  h.innerHTML=lanes.map(x=>`<article class="lane ${laneTone(x.state)}"><div><span class="lane-dot"></span><b>${escP(x.label)}</b></div><strong>${escP(String(x.state).replaceAll('_',' '))}</strong><p>${escP(x.detail||'')}</p>${x.model?`<small>${escP(x.model)} · mode ${escP(String(x.reasoningMode||'not reported').replaceAll('_',' '))}</small>`:''}</article>`).join('')}
 const fact=(k,v)=>`<div class="ws-fact"><span>${escP(k)}</span><b>${escP(v||'—')}</b></div>`;
 const card=(title,kicker,body,cls='')=>`<article class="ws-card ${cls}"><span class="cap">${escP(kicker)}</span><h3>${escP(title)}</h3>${body}</article>`;
 function work(ui){const sessions=ui.sessions||{tasks:[],sessions:[]};return `<div class="ws-grid">
  ${card(ui.project.label||'No project selected','ACTIVE WORKSPACE',fact('Repository',ui.github&&ui.github.repo)+fact('Branch',ui.github&&ui.github.branch)+fact('Scope',ui.project.scope||'not reported'))}
  ${card(ui.task&&ui.task.label||'No foreground task','CURRENT TASK',fact('Kind',ui.task&&ui.task.kind||'idle')+fact('ORION state',ui.orion.label)+fact('Execution',ui.action&&ui.action.executionState||'idle'))}
  ${card('Background work','SESSIONS',fact('Available tasks',String(sessions.tasks.length))+fact('Sessions',String(sessions.sessions.length))+fact('Running',String(sessions.sessions.filter(x=>x.state==='running'||x.state==='stopping').length)),'wide')}
  </div>`}
 function ai(ui){const ps=(ui.providers.items||[]).slice(0,5),rs=ui.reviewers||{models:{total:0,available:0},items:[]};let slots='';for(let i=0;i<5;i++){const p=ps[i];slots+=`<article class="ai-slot ${p&&p.enabled?'ready':''}"><span>${i+1}</span><div><b>${escP(p?p.label:'Cloud AI slot')}</b><small>${escP(p?[p.adapter,p.enabled?'enabled':'disabled'].filter(Boolean).join(' · '):'not connected')}</small></div></article>`}
 return `<div class="ai-hero"><span class="cap">REASONING LAYER</span><h3>Cloud specialists stay separate from PC authority.</h3><p>ORION can ask specialists to reason and critique. They never receive execution authority merely because a provider is connected.</p></div><div class="ai-slots">${slots}</div><div class="ws-grid">${card('Council status','AI COUNCIL',fact('State',rs.status)+fact('Models available',rs.models.available+' / '+rs.models.total)+fact('Current run',rs.runId||'none'))}${card('Local governor','LOCAL BRAIN',fact('Model',ui.localBrain&&ui.localBrain.model||ui.localBrain&&ui.localBrain.defaultModel||'not reported')+fact('State',ui.localBrain&&ui.localBrain.state||'not connected')+fact('Reasoning mode','not reported by backend'))}</div>`}
 function connectors(ui){const d=buildConnectors(ui);return `<div class="connector-intro"><span class="cap">REPLACEABLE CONNECTORS</span><h3>Connection is capability, not authority.</h3><p>Each connector reports what exists. ORION policy, approvals, evidence and STOP remain separate.</p></div><div class="connector-cards">${d.active.map(x=>`<article class="connector-card" data-status="${escP(x.status)}"><header><div><span class="c-dot"></span><b>${escP(x.label)}</b></div><strong>${escP(x.status)}</strong></header><p>${escP(x.status_detail||'')}</p>${(x.items||[]).slice(0,3).map(i=>fact(i.label,i.detail)).join('')}</article>`).join('')}</div>`}
 function system(ui){return `<div class="ws-grid">${card('Connection','SYSTEM',fact('Status',ui.connection.status)+fact('Transport',ui.connection.transport||'not reported')+fact('Last good update',ui.connection.ageMs==null?'never':Math.round(ui.connection.ageMs/1000)+'s ago'))}${card('Authority','SAFETY',fact('V1 Remote','frozen / separate')+fact('Stoppable work',String(ui.stops.length))+fact('PC control',ui.pcView.controlAuthorized?'authorized':'not authorized'))}${card('Runtime','COMPUTE',fact('Default model',ui.runtime&&ui.runtime.defaultModel||'not reported')+fact('Local models',ui.runtime&&ui.runtime.ollamaModels?String(ui.runtime.ollamaModels.length):'not reported')+fact('Client',ui.client.kind))}${card('Evidence','TRUTH',fact('Last result',ui.lastResult&&ui.lastResult.verdict||'none')+fact('Warnings',String(ui.warnings.length))+fact('Errors',String(ui.errors.length)),'wide')}</div>`}
 function renderView(ui){if(current==='home')return;const title={work:'Work',ai:'AI',connectors:'Connectors',system:'System'}[current]||'ORION';document.getElementById('ws-title').textContent=title;document.getElementById('ws-kicker').textContent=current==='connectors'?'ORION FABRIC':'ORION';const body=document.getElementById('ws-body');body.innerHTML=current==='work'?work(ui):current==='ai'?ai(ui):current==='connectors'?connectors(ui):system(ui)}
 function paint(ui){init();lastUi=ui;paintLanes(ui);renderView(ui)}
 return{init,paint,open,get view(){return current}};
})();
window.ORION_PRODUCT=ORION_PRODUCT;ORION_PRODUCT.init();
