/* ======================================================================
   mock-bridge.js — DEMO / MOCK BACKEND. Loaded ONLY by demo.html. index.html (live) never loads this file, and ORION's
   static server refuses to serve it, so mock data can never be mistaken for live ORION state.
   Produces objects shaped exactly like the real Controller.view() and runs them through the SAME normalizeStatus()
   (and the same route allowlist + trusted-gesture rule) the real bridge uses.
   ====================================================================== */
const MockBridge=(function(){
 const subs=new Set(),emit=e=>subs.forEach(f=>f(e));
 const iso=(ms=0)=>new Date(Date.now()-ms).toISOString();
 const lane=o=>Object.assign({run_state:'idle',result:null,output:'',error:'',activity:'idle',evidence_path:null,started_utc:null,finished_utc:null,goal:'',
  brain_state:'idle',brain_phase:'idle',brain_started_utc:null,brain_stream_preview:'',brain_model:'demo-model',brain_conclusion:'',brain_next_script:'',
  brain_next_capability:'',brain_next_url:'',brain_next_browser:'',brain_error:'',brain_preflight:'not-run',brain_preflight_reason:'',
  brain_quality_state:'not-run',brain_quality_reason:'',brain_quality_approved_sha256:'',execution_kind:'',execution_action:''},o);
 const base=()=>({mode:'active',run_state:'idle',pending_sha:null,approved_sha:null,last_tested_sha:null,last_result:null,last_output:'',last_error:'',activity:'idle',
  checkout_sha:'0123456789abcdef0123456789abcdef01234567',runner_log:'',evidence_path:null,repo:'demo/orion',branch:'demo-branch',test_command:'demo test',active_project_link_id:'',
  manual_lane:lane({}),local_hand_lane:lane({}),project_links:[],dispatch_tasks:[],dispatch_sessions:[],
  provider_vault:{providers:[{provider_id:'demo-a',label:'Demo provider A',adapter:'demo',enabled:true,configured_free:true,secret_hint:'••••1234'},{provider_id:'demo-b',label:'Demo provider B',adapter:'demo',enabled:false,secret_hint:''}]},
  reviewer:{state:'idle',catalog:{models:[{reviewer_id:'r1',provider:'ollama',provider_label:'Local',model:'demo-model',available:true},{reviewer_id:'r2',provider:'demo',provider_label:'Demo cloud',model:'demo-big',available:false}]}},
  update_status:{},local_brain_default_model:'demo-model'});
 const G='Open Chrome and search Google for RTX 4070 Ti SUPER price Greece';
 const CAP={execution_kind:'capability',execution_action:'open_web_url'};
 const OUT=JSON.stringify({status:'launch_requested',capability:'open_web_url',launcher:'chrome',pid:4242,browser:'chrome',host:'www.google.com',url:'https://www.google.com/search?q=demo',
  proof:'browser launch request accepted by the operating system; page render/content not independently verified'},null,2);
 const READY={brain_state:'ready',brain_phase:'complete',brain_quality_state:'pass',brain_preflight:'pass'};
 const V={
  idle:r=>r,
  drafting:r=>Object.assign(r.local_hand_lane,{goal:G,brain_state:'running',brain_phase:'drafting',brain_started_utc:iso(7000),activity:'new goal; local brain drafting',brain_stream_preview:'DEMO live generated text…'}),
  verifying:r=>Object.assign(r.local_hand_lane,{goal:G,brain_state:'running',brain_phase:'verifying',brain_started_utc:iso(14000),activity:'semantic verifier running'}),
  preparing:r=>Object.assign(r.local_hand_lane,{goal:G,...READY,brain_next_capability:'open_web_url',brain_next_url:'https://www.google.com/search?q=demo',brain_next_browser:'chrome'}),
  acting:r=>Object.assign(r.local_hand_lane,{goal:G,...READY,run_state:'running',started_utc:iso(1000),activity:'deterministic capability starting',...CAP}),
  acting_powershell:r=>Object.assign(r.local_hand_lane,{goal:'Run the checks',...READY,run_state:'running',started_at:null,started_utc:iso(2000),activity:'approved and starting',execution_kind:'powershell',execution_action:'PowerShell'}),
  pass:r=>Object.assign(r.local_hand_lane,{goal:G,...READY,run_state:'passed',result:'PASS',started_utc:iso(3000),finished_utc:iso(1500),output:OUT,exit_code:0,
   brain_conclusion:'Deterministic open_web_url completed.',...CAP}),
  approval:r=>Object.assign(r.local_hand_lane,{goal:'List the files in the project folder',...READY,brain_conclusion:'Read-only listing of the project folder.',brain_quality_approved_sha256:'ab12cd34ef56ab12cd34ef56ab12cd34ef56ab12cd34ef56ab12cd34ef56ab12',
   brain_next_script:'Get-ChildItem -Path . | Select-Object Name,Length\nWrite-Output "done"\n# demo script, never executed',brain_started_utc:iso(5000)}),
  blocked_preflight:r=>Object.assign(r.local_hand_lane,{goal:'Delete everything in temp',brain_state:'blocked',brain_phase:'complete',brain_preflight:'blocked',brain_preflight_reason:'Demo: request exceeds the scope of the original instruction.',brain_error:'PREFLIGHT BLOCKED: Demo: request exceeds the scope.',brain_started_utc:iso(20000)}),
  failed_verification:r=>Object.assign(r.local_hand_lane,{goal:'Summarise the repo',brain_state:'blocked',brain_phase:'complete',brain_preflight:'pass',brain_quality_state:'blocked',brain_quality_reason:'Demo: claims not supported by evidence.',brain_quality_unsupported_claims:['Repo has 400 tests'],brain_quality_missing_evidence:['test run output'],brain_error:'QUALITY BLOCKED: unsupported claims',brain_started_utc:iso(20000)}),
  capability_blocked:r=>Object.assign(r.local_hand_lane,{goal:G,...READY,run_state:'failed',result:'FAIL',error:'Demo: Chrome launch failed',started_utc:iso(3000),finished_utc:iso(1500),...CAP,brain_error:'CAPABILITY BLOCKED: Demo: Chrome launch failed'}),
  run_failed:r=>Object.assign(r.local_hand_lane,{goal:'Run the checks',...READY,run_state:'failed',result:'FAIL',error:'',started_utc:iso(4000),finished_utc:iso(1500),execution_kind:'powershell',execution_action:'PowerShell',exit_code:1,output:'3 passed, 1 failed (demo)'}),
  stopped:r=>Object.assign(r.local_hand_lane,{goal:'Run the long script',...READY,run_state:'stopped',result:'STOPPED',started_utc:iso(5000),finished_utc:iso(2000),execution_kind:'powershell',execution_action:'PowerShell',output:'partial output…'}),
  brain_error:r=>Object.assign(r.local_hand_lane,{goal:G,brain_state:'error',brain_phase:'error',brain_error:'Demo: local model did not respond',brain_started_utc:iso(9000)}),
  github_pending:r=>Object.assign(r,{pending_sha:'3154607b10ea2f5cfea76759ad9d7a79fbc64b92',last_tested_sha:'d69dec2b0a6b7adf607663a0018ee11bd1d1b7ab',last_result:'PASS'}),
  reviewers_running:r=>Object.assign(r.reviewer,{state:'running',run_id:'demo-run',reviewers:{r1:{model:'demo-model',provider_label:'Local',state:'running',output:'Looking at the plan so far…'}}}),
  reviewers_partial:r=>Object.assign(r.reviewer,{state:'complete',run_id:'demo-run',reviewers:{r1:{model:'demo-model',provider_label:'Local',state:'complete',output:'Long analysis…\n\nConclusion: the plan is sound but the rollback step is missing.'},r2:{model:'demo-big',provider_label:'Demo cloud',state:'failed',error:'Demo: provider rate limit',output:''}}})
 };
 let name='idle',linkS='live',linkErr='',timers=[];
 const raw=()=>{const r=base();V[name](r);return r};
 const link=()=>({status:linkS,lastOk:Date.now()-(linkS==='live'?0:12000),latency:42,fails:0,error:linkErr,base:'DEMO',transport:'demo',paired:linkS!=='unpaired'});
 function push(){emit({type:'snapshot',model:normalizeStatus(raw())});emit({type:'link',link:link()})}
 const later=(ms,fn)=>timers.push(setTimeout(fn,ms));
 const LINKS=['stale','reconnecting','offline','unpaired','backend_error'];
 const trusted=g=>!!g&&g.isTrusted===true;
 async function call(method,route,body,opts){
  const info=routeInfo(method,route);
  const mk=(ok,cls,message)=>({ok,status:ok?200:0,data:{demo:true},cls,message:message||'',route,method,label:(opts&&opts.label)||route});
  let r;
  if(!info)r=mk(false,'unregistered','UI refused: '+method+' '+route+' is not an allowlisted ORION route');
  else if(info.kind==='approval'&&!trusted(opts&&opts.gesture))r=mk(false,'no_gesture','UI refused: approval routes require a real user click');
  else r=mk(true,'sent','');
  emit({type:'command',entry:{at:Date.now(),label:(opts&&opts.label)||route,route,method,status:r.status,cls:r.cls,message:r.message,ms:0}});
  return r}
 return{
  mode:'mock',
  start(){push();setInterval(()=>{if(linkS==='live')emit({type:'link',link:link()})},2000)},
  stop(){},subscribe(f){subs.add(f);return()=>subs.delete(f)},link,refresh(){push()},
  describe:()=>({transport:'demo',events:'synthetic · NOT ORION',base:'DEMO',latency:42,lastOk:Date.now(),link:linkS,blockedCalls:0}),
  setBase(){},pair:async()=>({ok:true}),forgetPairing(){},_config:{},
  demoStates:Object.keys(V).concat(LINKS),
  demoState(n){timers.forEach(clearTimeout);timers=[];
   if(LINKS.includes(n)){linkS=n;linkErr=n==='backend_error'?'Demo: unexpected /api/status payload':'';push();return}
   linkS='live';linkErr='';name=n;push()},
  /* demo conversation: backend-style phases advance on DEMO timers. These timers exist ONLY in the mock. */
  async sendGoal(){this.demoState('drafting');later(2200,()=>this.demoState('verifying'));later(4200,()=>this.demoState('acting'));later(5600,()=>this.demoState('pass'));return{ok:true,cls:'sent'}},
  approveScript:(script,gesture)=>call('POST','/api/local-hand/run',{script},{label:'Approve & Run',gesture}),
  revise:(gesture)=>call('POST','/api/local-hand/revise',{},{label:'Revise draft',gesture}),
  call,
  async getMemoryCandidates(){return normalizeCandidates({candidates:[
   {candidate_id:'demo-1',content:'DEMO candidate: prefers dark UI',classification:'PREFERENCE',source_actor:'demo',submitted_at:iso(86400000),decision:'defer'},
   {candidate_id:'demo-2',content:'DEMO candidate: PayDay uses webhook retries',classification:'WORKFLOW',source_actor:'demo',submitted_at:iso(3600000),decision:'defer'},
   {candidate_id:'demo-3',content:'DEMO candidate: verify before reporting done',classification:'WORKFLOW',source_actor:'demo',submitted_at:iso(7200000),decision:'defer'}]})}
 };
})();
window.ORION_BRIDGE=MockBridge;
