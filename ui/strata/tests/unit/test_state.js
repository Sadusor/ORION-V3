/* The reducer/selector: buildUiState(V) is the canonical V3 state contract. Truth rules are tested here. */
const H=require('../harness');const {ok,eq,done,run,lane,view,NOW}=H;const c=H.coreCtx();
console.log('state reducer');
const UI=(raw,o)=>{o=o||{};c.__r=raw;
 run(c,`V.backend=null;V.cmd=null;V.dismissed={};V.observed={};V.ignore={};V.t0=Date.now()-1000;dispatch({type:'snapshot',model:normalizeStatus(__r)});
  V.link=Object.assign({status:'live',lastOk:Date.now(),latency:5,paired:true,fails:0,error:''},${JSON.stringify(o.link||{})});${o.cmd?`V.cmd=${JSON.stringify(o.cmd)};`:''}`);
 return run(c,'buildUiState(V,'+(o.now?'Date.now()+'+o.now:'Date.now()')+')')};
const READY={brain_state:'ready',brain_phase:'complete',brain_quality_state:'pass',brain_preflight:'pass'};
const CAP={execution_kind:'capability',execution_action:'open_web_url'};
const OUT=JSON.stringify({status:'launch_requested',pid:4242,browser:'chrome',host:'www.google.com',url:'https://www.google.com/search?q=x',proof:'browser launch request accepted by the operating system; page render/content not independently verified'});
const st=u=>u.orion.state;
/* ---- states backed by backend fields ---- */
eq(st(UI(view())),'idle','idle');
let u=UI(view({goal:'g',brain_state:'running',brain_phase:'drafting',brain_started_utc:NOW}));eq([st(u),u.orion.label],['thinking','Thinking locally'],'brain running/drafting => THINKING (only because the backend says so)');
eq(st(UI(view({goal:'g',brain_state:'running',brain_phase:'verifying',brain_started_utc:NOW}))),'verifying','brain verifying => VERIFYING');
u=UI(view({goal:'g',...READY,brain_next_capability:'open_web_url',brain_next_url:'https://www.google.com/x'}));eq(st(u),'preparing','ready+quality pass+capability => PREPARING');ok(/Authorized by your instruction/.test(u.authChip),'authorization chip only because a quality-passed capability is pending');
u=UI(view({goal:'g',...READY,run_state:'running',started_utc:NOW,...CAP}));eq(st(u),'acting','capability running => ACTING');eq(u.stops.length,0,'a registered capability run offers NO stop (backend cannot stop it)');ok(u.action&&u.action.stoppable===false&&/cannot stop/.test(u.action.note),'action explains why there is no Stop');
u=UI(view({goal:'g',...READY,run_state:'running',started_utc:NOW,execution_kind:'powershell',execution_action:'PowerShell'}));eq([st(u),u.stops.length,u.stops[0].route],['acting',1,'/api/local-hand/stop'],'PowerShell run => ACTING with a TARGETED stop');
/* ---- execution state vs verdict ---- */
u=UI(view({goal:'g',...READY,run_state:'passed',result:'PASS',started_utc:NOW,finished_utc:NOW,exit_code:0,output:OUT,...CAP}));
eq([st(u),u.orion.label,u.lastResult.executionState,u.lastResult.verdict],['pass','PASS','completed','PASS'],'capability: execution COMPLETED, verdict PASS (separate fields)');
const L=Object.fromEntries(u.lastResult.ladder.map(r=>[r.id,r.status]));
eq([L.authorized,L.accepted,L.requested,L.process],['established','established','established','established'],'ladder: authorized, accepted, launch requested and process (pid) are ESTABLISHED');
eq([L.detected,L.loaded,L.verified],['not_established','not_established','not_established'],'ladder: browser detected / page loaded / page verified are NOT established (request != verification)');
ok(/not read, compared or verified any page content/.test(u.lastResult.note),'result states page content was never read');
ok(!/verified/i.test(u.orion.label)&&!/verified/i.test(u.lastResult.headline),'no "verified" wording for a launch-only capability');
ok(/Authorized by your instruction/.test(u.authChip),'authorization chip because backend set execution_kind=capability');
u=UI(view({goal:'g',...READY,run_state:'passed',result:'PASS',started_utc:NOW,finished_utc:NOW,output:JSON.stringify({status:'launch_requested',launcher:'windows-default-browser',pid:null}),...CAP}));
eq(Object.fromEntries(u.lastResult.ladder.map(r=>[r.id,r.status])).process,'not_reported','default-browser launcher (pid null) => process "not reported", not claimed');
u=UI(view({goal:'g',...READY,run_state:'failed',result:'FAIL',started_utc:NOW,finished_utc:NOW,exit_code:1,execution_kind:'powershell',execution_action:'PowerShell',output:'1 failed'}));
eq([st(u),u.lastResult.executionState,u.lastResult.verdict],['failed','completed','FAILED'],'PowerShell: execution COMPLETED but verdict FAILED');
u=UI(view({goal:'g',...READY,run_state:'failed',result:'FAIL',error:'x',started_utc:NOW,finished_utc:NOW,...CAP,brain_error:'CAPABILITY BLOCKED: x'}));
eq([st(u),u.lastResult.verdict],['blocked','BLOCKED'],'CAPABILITY BLOCKED at execution => BLOCKED (not generic FAILED)');
u=UI(view({goal:'g',...READY,run_state:'stopped',result:'STOPPED',started_utc:NOW,finished_utc:NOW,execution_kind:'powershell'}));eq([st(u),u.lastResult.executionState,u.lastResult.verdict],['stopped','stopped',null],'STOPPED: execution stopped, no verdict');
u=UI(view({goal:'g',run_state:'error',result:'ERROR',started_utc:NOW,finished_utc:NOW,execution_kind:'powershell'}));eq([st(u),u.lastResult.verdict],['error','ERROR'],'ERROR');
/* ---- approval (generated PowerShell) ---- */
const SCRIPT='Get-ChildItem . | Select Name\nWrite-Output done';
u=UI(view({goal:'list files',...READY,brain_next_script:SCRIPT,brain_conclusion:'Read-only listing.',brain_quality_approved_sha256:'ab'.repeat(32),brain_started_utc:NOW}));
eq(st(u),'permission','generated PowerShell => APPROVAL NEEDED');const A=u.approval;
ok(A&&A.hand==='Local Hands · PowerShell'&&A.target.repo==='Sadusor/Orion'&&A.target.branch==='agent/x'&&A.why==='Read-only listing.'&&/2 lines/.test(A.summary)&&A.checks.preflight==='pass'&&A.checks.approvedHash.length===12&&A.risk&&A.script===SCRIPT,'approval shows hand, target, why, command summary, checks, scope and the exact script');
ok(!/Write-Output/.test(A.summary),'summary does not dump the script body');
eq(u.timeline.find(s=>s.id==='approval').status,'active','timeline: approval step is ACTIVE while waiting');
c.__sig=A.sig;run(c,'dispatch({type:"dismiss",sig:__sig})');u=run(c,'buildUiState(V)');eq([st(u),u.approval.dismissedLocally],['idle',true],'Reject => nothing runs, state returns to idle, draft flagged "rejected in this view"');
ok(/Nothing ran/.test(u.orion.activity),'reject message says nothing ran');
/* ---- blocked vs failed verification ---- */
u=UI(view({goal:'g',brain_state:'blocked',brain_phase:'complete',brain_preflight:'blocked',brain_preflight_reason:'scope',brain_error:'PREFLIGHT BLOCKED: scope',brain_started_utc:NOW}));eq([st(u),u.blocked.kind],['blocked','preflight'],'preflight refusal => BLOCKED');
u=UI(view({goal:'g',brain_state:'blocked',brain_phase:'complete',brain_preflight:'pass',brain_quality_state:'blocked',brain_quality_reason:'unsupported',brain_quality_unsupported_claims:['x'],brain_error:'QUALITY BLOCKED',brain_started_utc:NOW}));eq([st(u),u.blocked.kind,u.orion.label],['verif_failed','quality','Failed verification'],'semantic verification refusal => FAILED VERIFICATION (distinct from BLOCKED)');
u=UI(view({goal:'g',brain_state:'blocked',brain_preflight:'pass',brain_quality_state:'error',brain_started_utc:NOW}));eq([st(u),u.blocked.kind],['verif_failed','quality_error'],'verifier error => its own kind');
u=UI(view({goal:'g',brain_state:'error',brain_phase:'error',brain_error:'model down',brain_started_utc:NOW}));eq(st(u),'error','Local Brain error => ERROR');
/* ---- reviewers / providers ---- */
u=UI(view({},{reviewer:{state:'complete',run_id:'r',catalog:{models:[]},reviewers:{a:{state:'complete',output:'ok',model:'m'},b:{state:'failed',error:'rate',model:'n'}}}}));
ok(u.warnings.some(w=>w.code==='reviewer_partial'),'PARTIAL reviewer result is an explicit warning');
u=UI(view({},{reviewer:{state:'complete',reviewers:{a:{state:'failed',error:'x',model:'n'}},catalog:{models:[]}}}));ok(u.errors.some(e=>e.code==='reviewer_failure'),'REVIEWER FAILURE is an explicit error');
u=UI(view({},{reviewer:{state:'running',catalog:{models:[]},reviewers:{a:{state:'running',model:'m',output:'..'}}}}));eq([st(u),u.reviewers.visible],['specialist',true],'reviewers running => SPECIALIST + reviewer strip visible; stop target present');ok(u.stops.some(s=>s.route==='/api/reviewers/stop'),'reviewer run is stoppable (targeted)');
u=UI(view({},{reviewer:{state:'idle',catalog:{models:[{reviewer_id:'x',provider:'p',available:false,model:'m'}]}}}));ok(u.warnings.some(w=>w.code==='providers_unavailable'),'UNAVAILABLE PROVIDER is an explicit warning');
/* ---- connection ---- */
const CS=(s,extra)=>UI(view({goal:'g',...READY,run_state:'passed',result:'PASS',started_utc:NOW,finished_utc:NOW,output:OUT,...CAP}),{link:Object.assign({status:s},extra||{lastOk:0})});
for(const [s,want] of [['stale','stale'],['reconnecting','reconnecting'],['offline','offline'],['backend_error','backend_error'],['unpaired','offline'],['connecting','reconnecting']]){u=CS(s);eq(st(u),want,'link '+s+' => planet state '+want);ok(u.stale&&u.errors.some(e=>e.code==='connection_'+s),'link '+s+' is an explicit error/warning, not "Failed"')}
ok(CS('stale').lastResult!==null,'stale link keeps the last known result (marked stale), never invents a new one');
eq(CS('live',{lastOk:Date.now()-60000}).orion.state,'stale','a "live" link with a 60s-old snapshot is shown STALE (hung polling cannot look healthy)');
eq(CS('backend_error',{error:'Unexpected /api/status payload (run_state missing)'}).orion.detail,'Unexpected /api/status payload (run_state missing)','backend error text is shown verbatim');
/* ---- commands: each failure class stays distinct ---- */
for(const cls of ['timeout','rejected','unreachable','server_error','unregistered','no_gesture','unauthorized','bad_response']){u=UI(view(),{cmd:{at:1,label:'X',route:'/api/x',status:0,cls,message:'m'}});ok(u.errors.some(e=>e.code==='action_'+cls),'command class '+cls+' => its own error code (action_'+cls+')')}
ok(!UI(view(),{cmd:{at:1,label:'X',route:'/api/x',status:200,cls:'sent',message:''}}).errors.some(e=>e.code.startsWith('action_')),'a successful command is not an error');
/* ---- truth rules ---- */
const everyState=new Set();for(const r of [view(),view({brain_state:'running',brain_phase:'drafting',goal:'g',brain_started_utc:NOW}),view({goal:'g',...READY,brain_next_script:SCRIPT})])everyState.add(st(UI(r)));
ok(!['listening','understanding','memory','clarify'].some(s=>everyState.has(s)),'never derives listening / understanding / memory / clarify (no backend signal)');
const t1=UI(view({goal:'g',...READY,run_state:'running',started_utc:NOW,execution_kind:'powershell'}),{now:0}),t2=UI(view({goal:'g',...READY,run_state:'running',started_utc:NOW,execution_kind:'powershell'}),{now:3600*1000,link:{lastOk:Date.now()+3600*1000}});
eq([st(t1),st(t2)],['acting','acting'],'a long-running action stays ACTING for an hour: no timer ever completes it');
const cu=UI(view());for(const k of ['schema','source','connection','orion','project','repo','localBrain','task','timeline','approval','action','lastResult','blocked','github','sessions','reviewers','providers','memory','pcView','client','stops','errors','warnings','timestamps','command'])ok(k in cu,'state contract has "'+k+'"');
eq([cu.repo.dirty,cu.pcView.state,cu.pcView.controlAuthorized],['not_reported','not_configured',false],'repo dirty = not_reported; PC view = not_configured; viewing never authorizes control');
ok(UI(view({},{update_status:{phase:'failed',error:'boom'}})).errors.some(e=>e.code==='update_error'),'update error surfaced');
done('state reducer');
