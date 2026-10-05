/* Boot both pages with their real scripts in a stub DOM: main page loads, JS resolves, mock mode works, live never falls back to mock,
   malformed/offline/reconnect states render without crashing. */
const H=require('../harness');const {ok,eq,done,run,view,lane,NOW}=H;
console.log('boot');
(async()=>{
 /* ---- demo.html (mock) ---- */
 const d=H.loadPage('demo.html');
 ok(run(d,'window.ORION_BRIDGE.mode')==='mock'&&run(d,'V.mode')==='mock','demo.html: mock bridge active, V.mode = mock (banner shown)');
 ok(run(d,'typeof RealBridge')==='undefined','demo.html: real bridge not loaded');
 let n=0;for(const s of run(d,'ORION_BRIDGE.demoStates')){run(d,`ORION_BRIDGE.demoState(${JSON.stringify(s)});paint();layer("cc",1);updateCC(true);layer("cc",0);if(V.ev)openEvidence();openVP();closeSheets()`);n++}
 ok(n>=20,'demo.html: painted '+n+' demo states (incl. Command Center / evidence / Live View) without error');
 run(d,'forced="phone";mode();paint();forced="desktop";mode();paint()');ok(true,'demo.html: phone <-> desktop layout switch');
 await run(d,'openMemory()');run(d,'closeMemory()');ok(true,'demo.html: Memory Universe opens (adapter layer) and closes');
 /* mock respects the same safety rules */
 const r1=await run(d,'ORION_BRIDGE.call("POST","/api/manual/run",{})'),r2=await run(d,'ORION_BRIDGE.approveScript("x")');
 ok(r1.cls==='unregistered'&&r2.cls==='no_gesture','mock bridge enforces the same allowlist + approval-gesture rules');
 /* ---- index.html (live): valid backend ---- */
 let calls=[];const good=async(url,init)=>{calls.push(url);return{ok:true,status:200,json:async()=>view({goal:'g',brain_state:'running',brain_phase:'drafting',brain_started_utc:NOW})}};
 let l=H.loadPage('index.html',{fetch:good,storage:{orionToken:'tok'}});
 ok(run(l,'typeof MockBridge')==='undefined'&&run(l,'window.ORION_BRIDGE.mode')==='live'&&run(l,'V.mode')==='live','index.html: LIVE bridge only; MockBridge does not exist');
 await new Promise(r=>setTimeout(r,150));
 eq(run(l,'V.ui.orion.state'),'thinking','live page: valid backend response => state THINKING from the backend');
 ok(calls.every(u=>u.endsWith('/api/status')),'live page: only GET /api/status was requested at boot (no commands)');
 run(l,'ORION_BRIDGE.stop()');
 /* ---- malformed backend responses never crash and never become "idle" ---- */
 for(const [name,resp] of [['HTML page',{ok:true,status:200,json:async()=>{throw new SyntaxError('x')}}],['array',{ok:true,status:200,json:async()=>[]}],['partial object',{ok:true,status:200,json:async()=>({run_state:'idle'})}],['HTTP 500',{ok:false,status:500,json:async()=>({error:'boom'})}],['null',{ok:true,status:200,json:async()=>null}]]){
  const m=H.loadPage('index.html',{fetch:async()=>resp,storage:{orionToken:'tok'}});await new Promise(r=>setTimeout(r,120));
  const ui=run(m,'V.ui');ok(ui.orion.state==='backend_error'&&ui.stale&&ui.errors.some(e=>e.code==='connection_backend_error')&&!ui.lastResult,'malformed ('+name+') => BACKEND ERROR shown; no fake idle/result; UI still alive');run(m,'ORION_BRIDGE.stop()')}
 /* ---- offline ---- */
 const off=H.loadPage('index.html',{fetch:async()=>{throw new TypeError('Failed to fetch')},storage:{orionToken:'tok'}});await new Promise(r=>setTimeout(r,120));
 ok(['reconnecting','offline'].includes(run(off,'V.ui.orion.state')),'unreachable backend => RECONNECTING/DISCONNECTED (never a fake result, never mock fallback)');ok(run(off,'typeof MockBridge')==='undefined','offline live page did not fall back to mock');run(off,'ORION_BRIDGE.stop()');
 /* ---- unpaired ---- */
 const un=H.loadPage('index.html',{fetch:good});await new Promise(r=>setTimeout(r,80));eq(run(un,'V.ui.connection.status'),'unpaired','no stored token => NOT PAIRED (pairing overlay), no request without a token');run(un,'ORION_BRIDGE.stop()');
 /* ---- reconnect: failing then recovering ---- */
 let up=false;const flaky=async()=>{if(!up)throw new TypeError('down');return{ok:true,status:200,json:async()=>view({})}};
 const rc=H.loadPage('index.html',{fetch:flaky,storage:{orionToken:'tok'}});await new Promise(r=>setTimeout(r,100));const before=run(rc,'V.ui.orion.state');up=true;run(rc,'ORION_BRIDGE.refresh()');await new Promise(r=>setTimeout(r,120));
 ok(before!=='idle'&&run(rc,'V.ui.connection.status')==='live'&&run(rc,'V.ui.orion.state')==='idle','reconnect: down => not idle; recovered => live + real idle');run(rc,'ORION_BRIDGE.stop()');
 done('boot')})();
