/* The UI cannot invoke an undefined capability / route, and cannot press approval boundaries without a real user click. */
const H=require('../harness');const {ok,eq,done,run,lane,view,NOW}=H;
console.log('routes & safety');
const calls=[];const fetchStub=async(url,init)=>{calls.push({url,method:init&&init.method,body:init&&init.body});
 return{ok:true,status:200,json:async()=>view({brain_state:'running',brain_phase:'drafting',goal:'g'})}};
const ctx=H.makeContext({fetch:fetchStub,storage:{orionToken:'tok'}});H.loadScripts(ctx,['config.js','bridge/routes.js','bridge/normalize.js','bridge/real-bridge.js']);
const B=run(ctx,'window.ORION_BRIDGE');
(async()=>{
 for(const [m,r] of [['POST','/api/manual/run'],['POST','/api/reviewers/run'],['POST','/api/project-links/clone'],['POST','/api/project-links/create'],['POST','/api/generate'],['POST','/api/providers/save'],['POST','/api/providers/delete'],['POST','/api/memory/candidate'],['POST','/api/made-up-capability'],['DELETE','/api/status'],['POST','/etc/passwd'],['GET','/api/../secret']]){
  const before=calls.length,res=await B.call(m,r,{});ok(res.ok===false&&res.cls==='unregistered'&&calls.length===before,m+' '+r+' => refused by the allowlist, NO network request made')}
 /* approval boundaries need a trusted gesture */
 for(const [label,g] of [['no gesture',undefined],['synthetic (untrusted) event',{isTrusted:false}],['plain object',{}]]){
  for(const r of ['/api/local-hand/run','/api/run/start']){const before=calls.length,res=await B.call('POST',r,{script:'x'},{gesture:g});ok(res.cls==='no_gesture'&&calls.length===before,r+' with '+label+' => refused, NO request')}}
 let before=calls.length;let res=await B.call('POST','/api/local-hand/run',{script:'Get-Date',publish_github:false},{gesture:{isTrusted:true}});
 ok(res.ok&&calls.length===before+1&&JSON.parse(calls.at(-1).body).script==='Get-Date','a real click (isTrusted) is the only thing that lets the approval route through; exact script forwarded');
 before=calls.length;await B.approveScript('Get-Date');ok(calls.length===before,'approveScript() without a click is refused');
 /* conversation never executes */
 calls.length=0;await B.sendGoal('Open Chrome and search Google for x');
 ok(calls.length===1&&calls[0].url.endsWith('/api/local-hand/draft')&&JSON.parse(calls[0].body).goal==='Open Chrome and search Google for x','sendGoal => exactly ONE request, to /api/local-hand/draft');
 ok(!calls.some(c=>/\/run|\/start/.test(c.url)),'conversation text never triggers run/start (ORION decides; Approve & Run stays human)');
 ok(Object.keys(JSON.parse(calls[0].body)).sort().join()==='goal,model','draft body is exactly {goal, model}');
 ok(calls[0].url.indexOf('tok')<0,'the token is never placed in a URL');
 /* descriptors only reference registered routes */
 const c=H.coreCtx();c.__ids=[];
 const mk=raw=>{c.__r=raw;run(c,'V.backend=null;V.dismissed={};V.observed={};V.t0=Date.now()-1000;dispatch({type:"snapshot",model:normalizeStatus(__r)});V.link={status:"live",lastOk:Date.now(),paired:true};');return run(c,'buildConnectors(buildUiState(V),{})')};
 const samples=[view(),view({goal:'g',brain_state:'blocked',brain_preflight:'blocked',brain_started_utc:NOW}),view({goal:'g',brain_state:'ready',brain_quality_state:'pass',brain_next_script:'x'}),
  view({goal:'g',run_state:'running',execution_kind:'powershell',started_utc:NOW}),view({},{dispatch_tasks:[{task_id:'t',label:'T'}],dispatch_sessions:[{session_id:'s',state:'running'}],project_links:[{link_id:'L',github_repo:'a/b',branch:'x',state:'ready'}],provider_vault:{providers:[{provider_id:'p',label:'P',enabled:true}]}})];
 let n=0,approvals=0;for(const s of samples){const d=mk(s);for(const a of d.active.flatMap(x=>[...(x.actions||[]),...(x.items||[]).flatMap(i=>i.actions||[])])){if(a.href||a.ui)continue;n++;
   c.__m=a.call.method;c.__rt=a.call.route;ok(run(c,'isRegistered(__m,__rt)'),'descriptor action "'+a.label+'" -> '+a.call.method+' '+a.call.route+' is allowlisted');
   if(run(c,'routeInfo(__m,__rt).kind')==='approval'){approvals++;ok(a.approval===true,'approval-kind action "'+a.label+'" is flagged approval (needs a real click)')}}}
 ok(n===0&&approvals===0,'product connector catalog is status-only before connector wiring ('+n+' call actions, '+approvals+' approval boundaries)');
 const descriptorIds=mk(view()).active.map(x=>x.id);ok(descriptorIds.includes('project')&&descriptorIds.includes('providers')&&descriptorIds.includes('memory')&&descriptorIds.includes('safety'),'product connector catalog exposes truthful status surfaces');
 ok(!mk(view()).active.some(x=>(x.actions||[]).some(a=>a.href)),'product connector catalog has no legacy/Remote navigation actions');
 const memRoute=run(c,"routeInfo('GET','/api/memory/search?q=test')");ok(memRoute&&memRoute.kind==='read','Memory Retrieval V1 search is allowlisted READ-only even with query string');
 const memCandidate=run(c,"routeInfo('POST','/api/memory/candidate')");ok(memCandidate&&memCandidate.kind==='approval','Memory candidate intake requires approval/trusted gesture');

 const kinds=run(c,'Object.values(STRATA_ROUTES).map(r=>r.kind)');ok(kinds.every(k=>['read','auth','request','approval','stop','storage','command','high'].includes(k)),'every registered route has a known kind');
 done('routes & safety')})();
