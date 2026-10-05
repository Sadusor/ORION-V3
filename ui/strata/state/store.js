/* ======================================================================
   store.js — canonical state + the ONE reducer/selector set (PC and phone share it; components never read raw backend JSON).
     bridge --> normalize.js --> dispatch(action) --> V (store) --> buildUiState(V) --> UiState (STATE_CONTRACT.md) --> components
   TRUTH RULES (enforced here and nowhere else):
   - No timer ever advances operational state. A state exists only if a backend field establishes it.
   - request != execution != verification. Execution state (running/completed/stopped) and verdict (PASS/FAILED/BLOCKED/ERROR) are separate facts.
   - Evidence ladders list what the backend PROVED; everything else is "not established" or "not reported".
   - Never derived (no backend signal today): listening, understanding, memory, clarify, PC locked.
   - "Authorized by your instruction" appears only when execution_kind==='capability' (set by the backend after the original-request
     authorization path) or a quality-passed registered capability is about to start. The UI never decides authorization.
   ====================================================================== */
const $=id=>document.getElementById(id),app=$('app');
const RM=matchMedia('(prefers-reduced-motion:reduce)').matches;
let PHONE=false;
const S={state:'idle',detail:'',voice:'off',level:0,mem:false,low:false,camZ:1,orb:false};   // renderer-facing (sky-planet.js)
const DIM=['offline','stale','reconnecting'],HALT=['blocked','permission','stopped','failed','error','verif_failed','backend_error'];
const LABEL={idle:'Idle',listening:'Listening',understanding:'Understanding',memory:'Retrieving memory',clarify:'Needs clarification',
 thinking:'Thinking locally',verifying:'Verifying',preparing:'Preparing action',acting:'Acting',specialist:'Consulting specialist',
 permission:'Approval needed',pass:'PASS',completed:'Execution complete',failed:'FAILED',error:'ERROR',stopped:'Stopped',blocked:'BLOCKED',verif_failed:'Failed verification',
 reconnecting:'Reconnecting',stale:'Stale data',offline:'Disconnected',backend_error:'Backend error'};
const COLOR={idle:'#76cfe4',listening:'#76cfe4',understanding:'#76cfe4',thinking:'#76cfe4',verifying:'#c9eef5',preparing:'#76cfe4',acting:'#76cfe4',completed:'#76cfe4',
 specialist:'#9d90e8',memory:'#9d90e8',clarify:'#9d90e8',pass:'#76cea3',stopped:'#e0b867',permission:'#e0b867',verif_failed:'#e0956a',
 failed:'#d98276',error:'#d98276',blocked:'#d98276',backend_error:'#d98276',reconnecting:'#e0b867',stale:'#6f8092',offline:'#6f8092'};
const LINKTXT={live:'PC CONNECTED',stale:'STALE DATA',reconnecting:'RECONNECTING',connecting:'CONNECTING',offline:'DISCONNECTED',unpaired:'NOT PAIRED',backend_error:'BACKEND ERROR'};
const CAP_LABEL={open_web_url:'Open web page',publish_exact_artifact:'Publish exact file'};   // presentation names only
const capName=id=>CAP_LABEL[id]||id||'capability';

const CFG=window.STRATA_CONFIG||{},FRESH=CFG.freshWindowMs||900000;
const V={mode:'live',link:{status:'connecting',lastOk:0,latency:null,paired:true,fails:0,error:''},backend:null,lists:{},t0:Date.now(),
 observed:{},dismissed:{},ignore:{},cmd:null,cmdlog:[],convId:'local-'+Date.now().toString(36),turns:[],ui:null};   // convId/turns: placeholders for the future PC-owned turn journal (not shared today)

function dispatch(a){switch(a.type){
 case'snapshot':V.backend=a.model;observe(a.model);break;
 case'link':V.link=a.link;break;
 case'lists':V.lists=a.lists;break;
 case'command':V.cmd=a.entry;V.cmdlog.push(a.entry);if(V.cmdlog.length>40)V.cmdlog.shift();break;
 case'dismiss':V.dismissed[a.sig]=true;break;
 case'undismiss':delete V.dismissed[a.sig];break;
 case'ignoreResult':V.ignore.sig=a.sig;break;}}

const ms=x=>x?(Date.parse(x)||0):0,secs=(u,now)=>{const t=ms(u);return t?Math.max(0,Math.floor(((now||Date.now())-t)/1000)):null};
const tail=(t,n)=>{t=String(t||'').trim();return t.length>n?'…'+t.slice(-n):t};
const pretty=s=>{s=String(s||'').replace(/_/g,' ');return s.charAt(0).toUpperCase()+s.slice(1)};
const short=(sha,n=12)=>String(sha||'').slice(0,n);
const hostOf=u=>{try{return new URL(u).hostname}catch(e){return''}};
const PHASE={drafting:'Local Brain is drafting',verifying:'Verifying the draft',revising:'Revising the draft',repairing:'Repairing the draft',reviewing:'Reviewing'};

/* Remembers runs this page actually watched, so their result is shown even if the PC's clock and the browser's differ. */
function observe(m){if(!m)return;
 [['local',m.local,m.local.startedUtc],['manual',m.manual,m.manual.startedUtc],['gh',m.gh,m.gh.runnerStartedUtc]].forEach(([k,o,st])=>{if(o.runState==='running')V.observed[k]=st});
 if(m.local.brainState==='running')V.observed.brain=m.local.brainStartedUtc;
 if(m.reviewer.status==='running')V.observed.rev=true}
const isFresh=(key,startedUtc,finishedUtc)=>V.observed[key]===startedUtc||ms(finishedUtc)>=V.t0-FRESH;

/* ---------- evidence ladders: request != execution != verification ---------- */
const rung=(id,label,status,basis)=>({id,label,status,basis:basis||''});   // status: established | not_established | not_reported | failed | pending
function ladderCapability(L){const o=L.capOutput||{},started=L.executionState!=='idle',bad=L.verdict&&L.verdict!=='PASS',isWeb=L.execAction==='open_web_url';
 const R=[rung('authorized','Authorized by your original instruction',L.execKind==='capability'?'established':'pending','Backend started a registered capability (execution_kind=capability)'),
  rung('accepted','Hand accepted the request',started?'established':'pending','Capability run started')];
 if(isWeb)R.push(rung('requested','Launch request issued to the OS',o.status==='launch_requested'?'established':bad?'failed':'pending',o.proof||L.error),
  rung('process','Browser process launched',typeof o.pid==='number'?'established':o.status==='launch_requested'?'not_reported':'pending',typeof o.pid==='number'?'pid '+o.pid:'The default-browser launcher does not report a process'),
  rung('detected','Browser window / tab detected','not_established','ORION does not observe the desktop yet'),
  rung('loaded','Target page loaded','not_established','Not checked'),
  rung('verified','Target page read / verified','not_established','Not checked: ORION has not read any page content'));
 else R.push(rung('returned','Capability returned',L.verdict==='PASS'?'established':bad?'failed':'pending',str(o.status)||L.error),
  rung('verified','Outcome independently verified','not_established','ORION reports what the capability returned'));
 return R}
function ladderPowerShell(L){const done=L.executionState!=='running'&&L.executionState!=='idle';
 return[rung('authorized','Approved by you (Approve & Run)',L.executionState!=='idle'?'established':'pending','Exact script; server re-checks the approved hash'),
  rung('started','Hand started the script',L.executionState!=='idle'?'established':'pending'),
  rung('exited','Process exited',L.exitCode!=null?'established':done?'not_reported':'pending',L.exitCode!=null?'exit code '+L.exitCode:''),
  rung('output','Output captured',L.output?'established':done?'not_reported':'pending'),
  rung('verdict','Backend verdict',L.verdict?(L.verdict==='PASS'?'established':'failed'):done?'not_reported':'pending',L.verdict||''),
  rung('effects','Side effects independently verified','not_established','ORION reports exit status and output only')]}
function ladderGithub(G){const done=G.executionState!=='running'&&G.executionState!=='idle';
 return[rung('authorized','Approved by you (Approve & Run, exact SHA)',G.runnerStartedUtc?'established':'pending',short(G.runnerSha||G.approvedSha)),
  rung('exact','Ran against the exact approved SHA',G.runnerSha?'established':'pending',short(G.runnerSha)),
  rung('exited','Test command exited',G.runnerExit!=null?'established':done?'not_reported':'pending',G.runnerExit!=null?'exit code '+G.runnerExit:''),
  rung('verdict','Backend verdict',G.verdict?(G.verdict==='PASS'?'established':'failed'):done?'not_reported':'pending',G.verdict||''),
  rung('published','Evidence published',G.publishState&&G.publishState!=='not-requested'?'established':'not_reported',G.publishState||'')]}

/* ---------- lane/run -> canonical lastResult ---------- */
function resultOfLane(L,key,handName){
 if(!L.verdict&&L.executionState!=='stopped'&&L.executionState!=='error')return null;
 const cap=L.execKind==='capability',name=cap?capName(L.execAction):handName,exec=L.executionState;
 const capBlocked=cap&&/^CAPABILITY BLOCKED/i.test(L.brainError)&&L.verdict==='FAILED';
 const verdict=capBlocked?'BLOCKED':L.verdict;
 let headline,body;const rows=[];
 if(verdict==='PASS'){headline=cap?name+' · '+pretty(L.capOutput.status||'completed'):name+' · PASS';body=cap?(L.capOutput.proof||L.conclusion):tail(L.output,500);
  if(cap){if(L.capOutput.browser)rows.push(['Browser',L.capOutput.browser]);if(L.capOutput.host)rows.push(['Site',L.capOutput.host]);if(L.capOutput.url)rows.push(['URL',L.capOutput.url])}}
 else{headline=name+' · '+(verdict||exec.toUpperCase());body=L.error||L.brainError||tail(L.output,500)}
 const ev=[{k:'Execution state',v:exec},{k:'Verdict',v:verdict||'none (execution '+exec+')'}];
 if(L.exitCode!=null)ev.push({k:'Exit code',v:String(L.exitCode)});
 if(cap)ev.push({k:'Authorization',v:'Original human request (backend set execution_kind=capability)'});
 ev.push({k:'Preflight',v:L.preflight+(L.preflightReason?' · '+L.preflightReason:'')},{k:'Semantic quality check',v:L.qualityState+(L.qualityReason?' · '+L.qualityReason:'')});
 if(L.conclusion)ev.push({k:'Backend conclusion',v:L.conclusion});
 if(L.goal)ev.push({k:'Your request',v:L.goal});
 if(L.model)ev.push({k:'Local Brain model',v:L.model+(L.latency!=null?' · '+L.latency+'s':'')});
 if(L.evidencePath)ev.push({k:'Evidence folder (on PC)',v:L.evidencePath});
 if(L.output)ev.push({k:'Raw output',v:tail(L.output,6000),pre:true});
 if(L.error)ev.push({k:'Error',v:L.error,pre:true});
 return{key,source:key,hand:name,executionState:exec,verdict,headline,body,rows,ladder:cap?ladderCapability(L):ladderPowerShell(L),evidence:ev,
  note:cap&&verdict==='PASS'&&L.execAction==='open_web_url'?'Launch only. ORION has not read, compared or verified any page content.':'',
  startedAt:ms(L.startedUtc)||null,finishedAt:ms(L.finishedUtc)||null,fingerprint:key+L.finishedUtc+headline}}
function resultOfGithub(G){
 if(!G.verdict&&G.executionState!=='stopped'&&G.executionState!=='error')return null;
 const ev=[{k:'Execution state',v:G.executionState},{k:'Verdict',v:G.verdict||'none'},{k:'Exact SHA',v:G.runnerSha||G.lastTestedSha||'—'},{k:'Branch',v:G.repo+' @ '+G.branch},{k:'Publish',v:G.publishState+(G.publishedCommit?' · '+short(G.publishedCommit):'')}];
 if(G.evidencePath)ev.push({k:'Evidence folder (on PC)',v:G.evidencePath});if(G.lastOutput)ev.push({k:'Output tail',v:tail(G.lastOutput,6000),pre:true});
 if(G.runnerLog)ev.push({k:'Runner log',v:tail(G.runnerLog,4000),pre:true});if(G.lastError)ev.push({k:'Error',v:G.lastError,pre:true});
 return{key:'gh',source:'github-run',hand:'GitHub exact-SHA lane',executionState:G.executionState,verdict:G.verdict,headline:'Exact-SHA run · '+(G.verdict||G.executionState.toUpperCase()),
  body:G.lastError||tail(G.lastOutput,400),rows:[['SHA',short(G.runnerSha||G.lastTestedSha)]],ladder:ladderGithub(G),evidence:ev,note:'',
  startedAt:ms(G.runnerStartedUtc)||null,finishedAt:ms(G.runnerFinishedUtc)||null,fingerprint:'gh'+G.runnerFinishedUtc+G.lastResult}}

/* ---------- task timeline (Local Brain pipeline). Each step is backed by a named backend field. ---------- */
function timelineOf(L,awaiting){
 const T_=(id,label,status,basis)=>({id,label,status,basis});          // done | active | pending | failed
 const drafting=L.brainState==='running'&&L.brainPhase!=='verifying',verifying=L.brainState==='running'&&L.brainPhase==='verifying';
 const drafted=L.brainPhase==='complete'||L.brainState==='ready'||L.brainState==='blocked',started=L.executionState!=='idle';
 return[T_('draft','Draft',L.brainState==='error'?'failed':drafting?'active':drafted?'done':'pending','brain_state/brain_phase'),
  T_('verify','Verify',L.qualityState==='pass'?'done':L.qualityState==='blocked'||L.qualityState==='error'?'failed':verifying||L.qualityState==='running'?'active':'pending','brain_quality_state'),
  T_('preflight','Preflight',L.preflight==='pass'||L.preflight==='not-required'?'done':L.preflight==='blocked'?'failed':'pending','brain_preflight'),
  T_('approval',L.execKind==='powershell'||awaiting?'Approval':'Authorization',started?'done':awaiting?'active':'pending',started?'execution started':'waiting'),
  T_('hand','Hand',L.executionState==='running'?'active':L.executionState==='completed'?'done':L.executionState==='stopped'||L.executionState==='error'?'failed':'pending','run_state'),
  T_('verdict','Verdict',L.verdict==='PASS'?'done':L.verdict?'failed':'pending','result')]}

/* ---------- connection ---------- */
function connectionOf(now){const L=V.link,hidden=typeof document!=='undefined'&&document.hidden;let status=L.status;
 const staleMs=Math.max((CFG.link&&CFG.link.staleAfterMs)||6000,3*((CFG.poll&&CFG.poll.idleMs)||2000));
 if(status==='live'&&L.lastOk&&!hidden&&now-L.lastOk>staleMs)status='stale';
 return{status,lastOkAt:L.lastOk||null,ageMs:L.lastOk?now-L.lastOk:null,latencyMs:L.latency,failures:L.fails||0,endpoint:L.base||'',transport:L.transport||'',paired:L.paired!==false,error:L.error||''}}

/* ---------- THE state contract. Pure: same input -> same output. ---------- */
function buildUiState(V,now){now=now||Date.now();
 const conn=connectionOf(now),B=V.backend;
 const ui={schema:SCHEMA,source:{mode:V.mode,bridge:V.mode==='mock'?'mock':'real',transport:conn.transport||'poll'},connection:conn,stale:false,
  orion:{state:'idle',label:LABEL.idle,detail:'',activity:'',color:COLOR.idle},
  project:{label:'',activeLinkId:'',linkState:'',scope:'',links:[]},hands:null,runtime:null,repo:{repo:'',branch:'',sha:{},dirty:'not_reported',cwd:''},
  localBrain:null,task:null,timeline:[],approval:null,action:null,lastResult:null,blocked:null,errorCard:null,
  github:null,sessions:{tasks:[],sessions:[]},reviewers:{status:'idle',items:[],visible:false,models:{total:0,available:0}},
  providers:{status:'none',items:[]},memory:{candidates:null},pcView:{state:'not_configured',controlAuthorized:false,note:'No desktop stream exists yet. Viewing never authorizes control.'},
  client:{kind:PHONE?'phone':'pc',paired:conn.paired,transport:conn.transport},
  lanes:[],stops:[],errors:[],warnings:[],authChip:'',ghChip:'',command:V.cmd,
  timestamps:{snapshotAt:conn.lastOkAt,localBrainStartedAt:null,lastResultFinishedAt:null,now}};
 const err=(code,message,severity)=>ui.errors.push({code,message,severity:severity||'error'}),warn=(code,message,sev)=>ui.warnings.push({code,message,severity:sev||'warn'});
 if(B){
  const L=B.local,G=B.gh,M=B.manual,R=B.reviewer,a=B.project.active;
  ui.project={label:a?(String(a.github_repo||'').split('/').pop()+(a.scope&&a.scope!=='.'?' · '+a.scope:'')):'',activeLinkId:B.project.activeId,linkState:a?String(a.state||''):'',scope:a?a.scope:''};
  ui.repo={repo:G.repo,branch:G.branch,sha:B.repo.sha,dirty:'not_reported',cwd:G.runnerCwd};
  ui.localBrain={state:L.brainState,phase:L.brainPhase,model:L.model,goal:L.goal,conclusion:L.conclusion,preflight:{state:L.preflight,reason:L.preflightReason},
   quality:{state:L.qualityState,reason:L.qualityReason,unsupported:L.qualityUnsupported,missing:L.qualityMissing},
   next:{kind:L.nextCapability?'capability':L.nextScript?'powershell':'none',capability:L.nextCapability,url:L.nextUrl,browser:L.nextBrowser},error:L.brainError,startedAt:ms(L.brainStartedUtc)||null,revision:L.revision,defaultModel:B.defaultModel,livePreview:L.preview};
  ui.timestamps.localBrainStartedAt=ui.localBrain.startedAt;
  ui.github={mode:G.mode,executionState:G.executionState,verdict:G.verdict,pendingSha:G.pendingSha,approvedSha:G.approvedSha,lastTestedSha:G.lastTestedSha,checkoutSha:G.checkoutSha,repo:G.repo,branch:G.branch,
   testCommand:G.testCommand,update:G.update,publishState:G.publishState,evidencePath:G.evidencePath,activity:G.activity};
  ui.project.links=B.project.links;
  ui.hands={local:{executionState:L.executionState,verdict:L.verdict,action:L.execAction,kind:L.execKind},manual:{executionState:M.executionState,verdict:M.verdict}};
  ui.runtime={mode:G.mode,runnerPid:B.gh.runnerPid,runnerCwd:G.runnerCwd,runnerSha:G.runnerSha,update:G.update,defaultModel:B.defaultModel,ollamaModels:R.ollama};
  ui.sessions={tasks:B.tasks,sessions:B.sessions};ui.providers={items:B.providers,status:!B.providers.length?'none':B.providers.some(p=>p.enabled)?'ready':'unavailable'};
  ui.reviewers={status:R.status,items:R.items,models:{total:R.models.length,available:R.models.filter(m=>m.available).length},runId:R.runId,visible:R.status==='running'||(!!V.observed.rev&&R.items.length>0)};
  const runningSession=B.sessions.find(x=>x.state==='running'||x.state==='stopping');
  /* stoppable things: every stop is TARGETED at one running thing */
  if(L.executionState==='running'&&L.execKind==='powershell')ui.stops.push({id:'local',label:'Local Hands (PowerShell)',route:'/api/local-hand/stop',body:{}});
  if(M.executionState==='running')ui.stops.push({id:'manual',label:'Manual / External AI run',route:'/api/manual/stop',body:{}});
  if(G.executionState==='running')ui.stops.push({id:'gh',label:'Exact-SHA run',route:'/api/run/stop',body:{}});
  B.sessions.filter(x=>x.state==='running'||x.state==='stopping').forEach(x=>ui.stops.push({id:'s:'+x.session_id,label:'Session · '+(x.label||x.task_id||'task'),route:'/api/session/stop',body:{session_id:x.session_id}}));
  if(R.status==='running')ui.stops.push({id:'rev',label:'Reviewer run',route:'/api/reviewers/stop',body:{}});
  const awaiting=L.brainState==='ready'&&L.qualityState==='pass'&&!!L.nextScript&&!L.nextCapability&&L.executionState==='idle';
  const brainFresh=V.observed.brain===L.brainStartedUtc||ms(L.brainStartedUtc)>=V.t0-FRESH;
  const o=ui.orion;let st='idle',detail='',activity='';
  if(L.brainState==='running'){const el=secs(L.brainStartedUtc,now);st=L.brainPhase==='verifying'?'verifying':'thinking';detail=PHASE[L.brainPhase]||('Local Brain · '+L.brainPhase);activity=detail+(el!=null?' · '+el+'s':'');
   ui.task={kind:'local-hand',label:L.goal,startedAt:ms(L.brainStartedUtc)||null}}
  else if(L.executionState==='running'){const cap=L.execKind==='capability';st='acting';detail=cap?capName(L.execAction):'Approved PowerShell';activity=cap?'Running '+capName(L.execAction).toLowerCase():'Running approved PowerShell';
   ui.action={hand:cap?'Registered capability':'Local Hands · PowerShell',label:detail,executionState:'running',stoppable:!cap,note:cap?'Registered capabilities run to completion; ORION cannot stop them.':''};ui.task={kind:'local-hand',label:L.goal,startedAt:ms(L.startedUtc)||null};
   if(cap)ui.authChip='Authorized by your instruction · '+capName(L.execAction)}
  else if(M.executionState==='running'){st='acting';detail='Manual / External AI script';activity='Running manual script';ui.action={hand:'Local Hands · Manual',label:detail,executionState:'running',stoppable:true,note:''}}
  else if(G.executionState==='running'){st='acting';detail='Exact-SHA run';activity=G.activity||'Running exact-SHA verification';ui.action={hand:'GitHub exact-SHA lane',label:detail,executionState:'running',stoppable:true,note:''}}
  else if(runningSession){st='acting';detail='Task session';activity=(runningSession.label||runningSession.task_id||'Task')+' · '+runningSession.state;ui.action={hand:'Task session',label:detail,executionState:'running',stoppable:true,note:''}}
  else if(R.status==='running'){st='specialist';detail='Reviewer run';activity='Reviewers are running ('+R.items.filter(i=>i.phase==='running').length+' of '+R.items.length+')'}
  else if(L.brainState==='ready'&&L.qualityState==='pass'&&L.nextCapability){st='preparing';detail=capName(L.nextCapability);activity='Starting '+capName(L.nextCapability).toLowerCase()+(L.nextUrl?' · '+hostOf(L.nextUrl):'');ui.authChip='Authorized by your instruction · '+capName(L.nextCapability)}
  else if(awaiting){
   const ls=L.nextScript.split(/\r?\n/).filter(x=>x.trim()),first=(ls[0]||'').trim();
   const sig='A'+L.nextScript.length+L.nextScript.slice(0,60)+L.approvedSha256.slice(0,8);
   ui.approval={sig,kind:'powershell',title:'ORION wants to run generated PowerShell',hand:'Local Hands · PowerShell',
    target:{project:ui.project.label||'ORION default repo',repo:G.repo,branch:G.branch,cwd:'the configured ORION repo path (not exposed by status)'},
    why:L.conclusion||'(no conclusion provided)',summary:ls.length+' line'+(ls.length===1?'':'s')+' · starts with: '+tail(first,110),
    checks:{preflight:L.preflight,quality:L.qualityState,approvedHash:short(L.approvedSha256)},
    risk:'Runs exactly this script once. The server re-checks the approved hash and refuses if it changed.',script:L.nextScript,model:L.model,dismissedLocally:!!V.dismissed[sig]};
   st=ui.approval.dismissedLocally?'idle':'permission';detail=ui.approval.dismissedLocally?'You rejected this draft in this view':'Generated PowerShell is waiting for your Approve & Run';
   activity=ui.approval.dismissedLocally?'Draft rejected here. Nothing ran. It stays on the PC until a new request replaces it.':detail}
  else if(L.brainState==='blocked'&&brainFresh&&!L.verdict){
   const kind=L.preflight==='blocked'?'preflight':L.qualityState==='blocked'?'quality':L.qualityState==='error'?'quality_error':'other';
   const why=L.brainError||L.preflightReason||L.qualityReason||'Blocked by ORION';
   ui.blocked={kind,reason:why,preflight:{state:L.preflight,reason:L.preflightReason},quality:{state:L.qualityState,reason:L.qualityReason},unsupported:L.qualityUnsupported,missing:L.qualityMissing,canRevise:true,goal:L.goal};
   st=kind==='quality'||kind==='quality_error'?'verif_failed':'blocked';detail=why}
  else if(L.brainState==='error'&&brainFresh){st='error';detail=L.brainPhase==='interrupted'?'Interrupted by an ORION restart':'Local Brain error';ui.errorCard={reason:L.brainError||'Local Brain error',phase:L.brainPhase}}
  else{
   const c=[];const rl=resultOfLane(L,'local-hand','Local Hands · PowerShell');if(rl&&isFresh('local',L.startedUtc,L.finishedUtc))c.push(rl);
   const rm=resultOfLane(M,'manual','Manual / External AI');if(rm&&isFresh('manual',M.startedUtc,M.finishedUtc))c.push(rm);
   const rg=resultOfGithub(G);if(rg&&isFresh('gh',G.runnerStartedUtc,G.runnerFinishedUtc))c.push(rg);
   c.sort((x,y)=>(y.finishedAt||0)-(x.finishedAt||0));const r=c[0]||null;
   if(r&&V.ignore.sig!==r.fingerprint){ui.lastResult=r;ui.timestamps.lastResultFinishedAt=r.finishedAt;
    st=r.executionState==='stopped'?'stopped':r.executionState==='error'?'error':r.verdict==='PASS'?'pass':r.verdict==='BLOCKED'?'blocked':r.verdict==='ERROR'?'error':r.verdict==='FAILED'?'failed':'completed';
    detail=r.headline;if(r.source==='local-hand'&&L.execKind==='capability')ui.authChip='Authorized by your instruction · '+capName(L.execAction)}}
  o.state=st;o.detail=detail;o.activity=activity;
  if(L.goal&&(st!=='idle'||ui.lastResult))ui.timeline=timelineOf(L,!!ui.approval&&!ui.approval.dismissedLocally);
  if(G.mode==='active'&&G.pendingSha&&G.executionState!=='running')ui.ghChip='GitHub update pending · '+short(G.pendingSha,8);
  /* warnings / errors: explicit, never collapsed into a generic "Failed" */
  if(G.mode!=='active')warn('coding_mode','Coding Mode is "'+G.mode+'": Check / Sync / Run need it active');
  if(!B.providers.length)warn('providers_none','No saved cloud providers');else if(ui.providers.status==='unavailable')warn('providers_disabled','All saved providers are disabled');
  if(R.models.length&&!R.models.some(m=>m.available))warn('providers_unavailable','No reviewer model is currently available');
  if(R.status==='failed')err('reviewer_failure','Every reviewer in the last run failed');else if(R.status==='partial')warn('reviewer_partial','Partial reviewer result: '+R.failed+' failed, '+R.done+' answered');
  if(G.update.error)err('update_error','Update: '+G.update.error);
  warn('repo_dirty','Repo clean/dirty state is not reported by ORION','info');
 }
 /* link health overrides the planet; last known cards stay visible but are marked stale */
 const o=ui.orion,ls=conn.status;ui.stale=ls!=='live';
 if(ls!=='live'){const age=conn.ageMs!=null?Math.floor(conn.ageMs/1000):null;
  const m={stale:['stale',age!=null?'No update for '+age+'s · showing last known state':'No update yet'],reconnecting:['reconnecting','Retrying the PC link…'],connecting:['reconnecting','Contacting PC…'],
   offline:['offline','Disconnected from the PC'],unpaired:['offline','Pair this device with ORION'],backend_error:['backend_error',conn.error||'ORION answered, but not with a usable status']}[ls];
  o.state=m[0];o.detail=m[1];o.activity=m[1];ui.stops=[];ui.authChip='';
  err('connection_'+ls,m[1],ls==='stale'||ls==='reconnecting'?'warn':'error')}
 o.label=LABEL[o.state];o.color=COLOR[o.state];
 ui.lanes=productLanes(ui);
 const c=V.cmd;if(c&&c.cls&&c.cls!=='sent')err('action_'+c.cls,commandMessage(c));
 return ui}


function productLanes(ui){
 const L=ui.localBrain,R=ui.reviewers,Ss=ui.sessions||{sessions:[]};
 const personalState=!L?'not_connected':L.state==='running'?'thinking':(ui.hands&&ui.hands.local.executionState==='running')?'acting':L.state==='blocked'?'blocked':L.state==='error'?'error':'ready';
 const projectState=ui.project&&ui.project.label?(ui.action&&/GitHub|Task session/.test(ui.action.hand||'')?'active':'ready'):'not_selected';
 const reviewState=R&&R.status==='running'?'thinking':R&&R.status==='failed'?'error':R&&R.status==='partial'?'degraded':R&&R.models&&R.models.total?'ready':'not_connected';
 const bg=(Ss.sessions||[]).filter(x=>x.state==='running'||x.state==='stopping').length;
 return [
  {id:'personal',label:'Personal',kind:'assistant',state:personalState,detail:L?(L.goal||L.phase||'Ready'):'Backend not connected',model:L&&L.model||L&&L.defaultModel||'',reasoningMode:'not_reported'},
  {id:'project',label:'Project',kind:'project',state:projectState,detail:ui.project&&ui.project.label||'No project selected',model:'',reasoningMode:'not_reported'},
  {id:'specialists',label:'Specialists',kind:'reviewers',state:reviewState,detail:R&&R.models?(R.models.available+' / '+R.models.total+' available'):'Not connected',model:'',reasoningMode:'not_reported'},
  {id:'background',label:'Background',kind:'sessions',state:bg?'active':'idle',detail:bg?bg+' running session'+(bg===1?'':'s'):'No active background work',model:'',reasoningMode:'not_reported'}
 ];
}

/* human wording for a classified command outcome (shared by toast, notice and logs) */
function commandMessage(c){const l=c.label||c.route;
 return({sent:l+' · sent to ORION (HTTP '+c.status+')',rejected:l+' · rejected by ORION: '+c.message,timeout:l+' · timed out ('+c.message+'). ORION may still be processing: watch the state.',
  unreachable:l+' · could not reach the PC: '+c.message,unauthorized:l+' · not authorized: pair this device again',server_error:l+' · backend error: '+c.message,bad_response:l+' · ORION replied with something unreadable',
  unregistered:c.message,no_gesture:c.message})[c.cls]||(l+' · '+c.message)}
