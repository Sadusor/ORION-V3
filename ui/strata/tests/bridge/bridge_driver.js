/* Drives the REAL real-bridge.js against tests/fake_orion.py over real HTTP. usage: node bridge_driver.js <pkgRoot> <baseUrl> <token> <code> */
const H=require('../harness');const {ok,eq,done,run}=H;
const [,, ,base,TOKEN,CODE]=process.argv;
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const ctl=p=>fetch(base+'/__ctl/'+p).then(r=>r.json());
const storage={};const ctx=H.makeContext({fetch,storage});
H.loadScripts(ctx,['config.js','bridge/routes.js','bridge/normalize.js','bridge/real-bridge.js']);
const B=run(ctx,'window.ORION_BRIDGE');
Object.assign(B._config,{idleMs:60,activeMs:50,hiddenMs:60,statusTimeoutMs:400,commandTimeoutMs:500,staleAfterMs:150,reconnectingAfterMs:500,offlineAfterMs:1100});
B.setBase(base);
const links=[],snaps=[],cmds=[];B.subscribe(e=>{if(e.type==='link')links.push(e.link.status);if(e.type==='snapshot')snaps.push(e.model);if(e.type==='command')cmds.push(e.entry)});
const last=()=>links[links.length-1];
let refreshCalls=0;const _r=B.refresh;B.refresh=()=>{refreshCalls++;return _r()};
console.log('bridge (real HTTP)');
(async()=>{
 await ctl('reset');B.start();await sleep(200);
 ok(last()==='unpaired','no token => NOT PAIRED; no status request is made without a token');
 let r=await B.pair('000000');ok(!r.ok&&/Invalid pairing code/.test(r.error),'wrong pairing code => backend error shown: '+r.error);
 r=await B.pair(CODE);ok(r.ok&&ctx.__ls.orionToken===TOKEN,'pairing stores the token under orionToken (the Remote V1 key)');
 await sleep(300);ok(last()==='live'&&snaps.length>0,'paired => live + first snapshot');
 /* automatic updates (the "Refresh regression"): state changes arrive with NO refresh call */
 const seen=new Set();B.subscribe(e=>{if(e.type==='snapshot')seen.add(e.model.local.brainPhase+'/'+e.model.local.brainState)});
 await ctl('scenario/drafting');await sleep(250);await ctl('scenario/verifying');await sleep(250);await ctl('scenario/acting');await sleep(250);await ctl('scenario/pass');await sleep(250);
 ok(seen.has('drafting/running')&&seen.has('verifying/running')&&seen.has('complete/ready'),'live updates arrive automatically as the backend changes ('+[...seen].join(', ')+')');
 eq(refreshCalls,0,'manual Refresh was never needed (0 calls)');
 ok(B.getModel().local.verdict==='PASS'&&B.getModel().local.executionState==='completed','final model: execution completed, verdict PASS');
 /* malformed / error bodies => BACKEND ERROR, no new snapshot, never fake idle */
 for(const m of ['html','array','partial','truncated','e500']){const n=snaps.length,linkStart=links.length;await ctl('mode/'+m);await B.refresh();await sleep(40);
  ok(links.slice(linkStart).includes('backend_error')&&snaps.length===n,'mode '+m+' => BACKEND ERROR, no snapshot emitted');ok(/./.test(run(ctx,'RealBridge.link().error')),'  error text kept: '+run(ctx,'RealBridge.link().error'))}
 await ctl('mode/ok');await B.refresh();await sleep(40);ok(last()==='live','malformed bodies stop => live again');
 /* offline -> reconnect */
 links.length=0;const n0=snaps.length;await ctl('mode/drop');await sleep(1500);
 const order=[...new Set(links)];ok(order.includes('stale')&&order.includes('reconnecting')&&order.includes('offline'),'dropped connection walks STALE -> RECONNECTING -> DISCONNECTED ('+order.join(' > ')+')');
 ok(order.indexOf('stale')<order.indexOf('reconnecting')&&order.indexOf('reconnecting')<order.indexOf('offline'),'in that order');
 ok(snaps.length===n0,'no snapshot while the backend is unreachable (nothing invented)');
 await ctl('mode/ok');await sleep(400);ok(last()==='live'&&snaps.length>n0,'backend returns => reconnect: LIVE + a fresh real snapshot');
 /* hang => timeout classification for commands */
 await ctl('mode/hang_post');r=await B.sendGoal('hello');ok(!r.ok&&r.cls==='timeout'&&/No answer within/.test(r.error),'hung command => TIMEOUT (distinct class): '+r.error);await ctl('mode/ok');await sleep(3200);
 /* rejection vs success */
 r=await B.sendGoal('   ');ok(!r.ok&&r.cls==='rejected'&&/Enter a goal/.test(r.error),'ORION 409 => REJECTED with its own message: '+r.error);
 r=await B.call('POST','/api/run/stop',{},{label:'Stop'});ok(!r.ok&&r.cls==='rejected'&&r.message==='No active run.','Stop with nothing running => rejected, message verbatim');
 r=await B.sendGoal('Open Chrome and search Google for RTX 4070 Ti SUPER price Greece');ok(r.ok,'valid request accepted via POST /api/local-hand/draft');
 await sleep(200);ok(B.getModel().local.brainState==='running','draft response absorbed immediately as a real snapshot (brain running)');
 /* approval boundary reaches the server only with a trusted click */
 let log=await ctl('log');const runsBefore=log.filter(x=>x.path==='/api/local-hand/run').length;
 await ctl('scenario/approval');await sleep(150);const script=B.getModel().local.nextScript;ok(script.length>0,'approval scenario exposes the exact script');
 await B.approveScript(script);await B.approveScript(script,{isTrusted:false});log=await ctl('log');eq(log.filter(x=>x.path==='/api/local-hand/run').length,runsBefore,'approve without a real click => server never received /run');
 r=await B.approveScript(script,{isTrusted:true});log=await ctl('log');const runs=log.filter(x=>x.path==='/api/local-hand/run');ok(r.ok&&runs.length===runsBefore+1&&runs.at(-1).body.script===script&&runs.at(-1).body.publish_github===false,'trusted click => server received /run with the exact script');
 ok(!log.some(x=>x.path==='/api/mode/enter'||x.path==='/api/manual/run'),'no other command was ever sent');
 const dr=log.filter(x=>x.path==='/api/local-hand/draft').map(x=>Object.keys(x.body).sort().join());ok(dr.every(k=>k==='goal,model'),'every draft body is exactly {goal, model}');
 /* revoked/invalid token => NOT PAIRED */
 ctx.__ls.orionToken='bad-token';await sleep(300);ok(last()==='unpaired','invalid token (401) => NOT PAIRED, not "offline"');
 B.stop();done('bridge (real HTTP)')})();
