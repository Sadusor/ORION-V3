/* ======================================================================
   real-bridge.js — LIVE mode. The ONLY module that talks to the ORION PC. Assigns window.ORION_BRIDGE.
   Pipeline:  backend --(this file: transport, auth, validation, error classes)--> normalize.js --> store.js --> shell/components
   - Existing routes only (see routes.js allowlist). There is NO /api/intent: conversation = POST /api/local-hand/draft {goal, model}.
   - Auth = the existing one: token from POST /api/pair, kept by Remote V1 in localStorage['orionToken'], sent as X-Orion-Token.
     STRATA is served from the SAME ORIGIN (/v3/), so it reuses that pairing. The long-lived token is never placed in a URL.
   - Live updates: polling GET /api/status. idle 2s, 0.8s while ORION is working / just got a command, 8s in a hidden tab.
     A later header-authenticated fetch-stream replaces/supplements TRANSPORTS.poll without touching anything else.
   - Never fakes anything: a failed or malformed response becomes a link state (stale / reconnecting / offline / backend_error), not a result.
   Events: {type:'snapshot',model} {type:'link',link} {type:'command',entry} {type:'lists',lists}
   ====================================================================== */
const RealBridge=(function(){
 const CFG=window.STRATA_CONFIG||{},P=CFG.poll||{},LK=CFG.link||{};
 const LS=(k,v)=>{try{if(v===undefined)return localStorage.getItem(k)||'';v===null?localStorage.removeItem(k):localStorage.setItem(k,v)}catch(e){return''}};
 const C={base:LS('strata.endpoint'),idleMs:P.idleMs||2000,activeMs:P.activeMs||800,hiddenMs:P.hiddenMs||8000,statusTimeoutMs:P.statusTimeoutMs||8000,commandTimeoutMs:P.commandTimeoutMs||30000,
  staleAfterMs:LK.staleAfterMs||6000,reconnectingAfterMs:LK.reconnectingAfterMs||20000,offlineAfterMs:LK.offlineAfterMs||90000,transport:'poll'};
 const subs=new Set(),emit=e=>subs.forEach(f=>{try{f(e)}catch(x){console.error('[strata] subscriber error',x)}});
 const st={lastOk:0,fails:0,latency:null,link:'connecting',error:'',timer:0,running:false,model:null,burstUntil:0,lastPollAt:0,blockedCalls:0};
 const token=()=>LS('orionToken');

 /* ---- low-level request. Never throws for HTTP/network problems: returns a classified result. ---- */
 async function request(method,route,body,timeoutMs){
  const t0=performance.now(),ac=new AbortController(),to=setTimeout(()=>ac.abort(),timeoutMs);
  try{
   const h={};if(token())h['X-Orion-Token']=token();if(method!=='GET')h['Content-Type']='application/json';
   const r=await fetch(C.base+route,{method,headers:h,body:method==='GET'?undefined:JSON.stringify(body||{}),signal:ac.signal,cache:'no-store'});
   let data,parsed=true;try{data=await r.json()}catch(e){data={};parsed=false}
   const ms=Math.round(performance.now()-t0);
   if(r.status===401)setLink('unpaired');
   return{ok:r.ok,status:r.status,data,parsed,ms,route,method,
    cls:r.ok?(parsed?'sent':'bad_response'):r.status===401?'unauthorized':r.status>=500?'server_error':'rejected',   // 4xx = ORION refused (409 {error}) 
    message:r.ok?'':str(data&&data.error)||('HTTP '+r.status)};
  }catch(e){
   const timeout=e&&e.name==='AbortError';
   return{ok:false,status:0,data:{},parsed:false,ms:Math.round(performance.now()-t0),route,method,cls:timeout?'timeout':'unreachable',message:timeout?'No answer within '+(+(timeoutMs/1000).toFixed(1))+'s':(e&&e.message)||'network error'};
  }finally{clearTimeout(to)}}

 function link(){return{status:st.link,lastOk:st.lastOk,latency:st.latency,fails:st.fails,error:st.error,base:C.base||'(same origin)',transport:C.transport,paired:!!token(),lastPollAt:st.lastPollAt}}
 function setLink(s,err){st.link=s;st.error=err||(s==='live'?'':st.error);emit({type:'link',link:link()})}

 /* Most POST routes return Controller.view(); absorb it as a fresh snapshot, but only if it passes the contract check. */
 function absorb(data){if(!looksLikeView(data))return false;try{st.model=normalizeStatus(data);st.lastOk=Date.now();emit({type:'snapshot',model:st.model});return true}catch(e){return false}}

 /* ---- polling transport ---- */
 const TRANSPORTS={poll:{start(){poll()},stop(){clearTimeout(st.timer)}}
  /* stream: header-authenticated fetch() reader -> absorb(); on gap/error fall back to poll(). LATER; same events, no UI change. */};
 function busy(){const m=st.model;if(!m)return false;const L=m.local;
  return L.brainState==='running'||L.runState==='running'||m.manual.runState==='running'||m.gh.runState==='running'||m.reviewer.status==='running'||
   (L.brainState==='ready'&&L.qualityState==='pass'&&!!L.nextCapability)||Date.now()<st.burstUntil}
 function schedule(){if(!st.running)return;clearTimeout(st.timer);st.timer=setTimeout(poll,(typeof document!=='undefined'&&document.hidden)?C.hiddenMs:busy()?C.activeMs:C.idleMs)}
 async function poll(){
  clearTimeout(st.timer);st.lastPollAt=Date.now();
  try{
   if(!token()){setLink('unpaired');return}
   const r=await request('GET','/api/status',null,C.statusTimeoutMs);
   if(r.cls==='unauthorized')return;
   if(r.ok&&r.parsed&&looksLikeView(r.data)){st.fails=0;st.latency=r.ms;st.lastOk=Date.now();st.model=normalizeStatus(r.data);emit({type:'snapshot',model:st.model});setLink('live');return}
   if(r.status>0){            // ORION answered, but not with a usable status: a BACKEND ERROR, not offline, and never a fake idle
    st.fails++;setLink('backend_error',r.ok?'Unexpected /api/status payload ('+validateStatus(r.data).problems.join(', ')+')':'ORION answered HTTP '+r.status+(r.message?': '+r.message:''));return}
   throw new Error(r.message);
  }catch(e){
   st.fails++;const age=st.lastOk?Date.now()-st.lastOk:Infinity;
   setLink(!st.lastOk?(st.fails<3?'connecting':'offline'):age>=C.offlineAfterMs?'offline':age>=C.reconnectingAfterMs?'reconnecting':(st.fails>=2||age>=C.staleAfterMs)?'stale':'live',e&&e.message);
  }finally{schedule()}}
 if(typeof document!=='undefined')document.addEventListener('visibilitychange',()=>{if(st.running&&!document.hidden)poll()});

 /* ---- the single guarded entry for every command ---- */
 const trusted=g=>!!g&&g.isTrusted===true;
 async function call(method,route,body,opts){
  const info=routeInfo(method,route);
  if(!info){st.blockedCalls++;const r={ok:false,status:0,data:{},cls:'unregistered',message:'UI refused: '+method+' '+route+' is not an allowlisted ORION route',route,method,label:(opts&&opts.label)||route};log(r,opts);return r}
  if(info.kind==='approval'&&!trusted(opts&&opts.gesture)){st.blockedCalls++;const r={ok:false,status:0,data:{},cls:'no_gesture',message:'UI refused: approval routes require a real user click',route,method,label:(opts&&opts.label)||route};log(r,opts);return r}
  const r=await request(method,route,body,method==='GET'?C.statusTimeoutMs:C.commandTimeoutMs);
  if(method!=='GET'){st.burstUntil=Date.now()+4000;absorb(r.data);setTimeout(poll,350)}
  r.label=(opts&&opts.label)||route;if(method!=='GET'||!r.ok)log(r,opts);return r}
 function log(r,opts){emit({type:'command',entry:{at:Date.now(),label:(opts&&opts.label)||r.route,route:r.route,method:r.method,status:r.status,cls:r.cls,message:r.message,ms:r.ms}})}

 return{
  mode:'live',
  start(){if(st.running)return;st.running=true;TRANSPORTS[C.transport].start()},
  stop(){st.running=false;TRANSPORTS[C.transport].stop()},
  subscribe(f){subs.add(f);return()=>subs.delete(f)},
  link,getModel:()=>st.model,refresh:()=>poll(),
  describe:()=>({transport:C.transport,events:'polling · idle '+C.idleMs+'ms · active '+C.activeMs+'ms · hidden '+C.hiddenMs+'ms',base:C.base||'(same origin)',latency:st.latency,lastOk:st.lastOk,link:st.link,blockedCalls:st.blockedCalls}),
  setBase(url){C.base=(url||'').replace(/\/+$/,'');LS('strata.endpoint',C.base||null);st.lastOk=0;st.fails=0;poll()},
  _config:C,                                   // test hook: lets tests shrink the stale/offline thresholds
  async pair(code){const r=await request('POST','/api/pair',{code:String(code||'').trim()},C.commandTimeoutMs);
   if(r.ok&&r.data&&r.data.token){LS('orionToken',r.data.token);poll();return{ok:true}}
   return{ok:false,error:r.message||'Pairing failed'}},
  forgetPairing(){LS('orionToken',null);setLink('unpaired')},
  call,
  /* conversation: the real entry is the Local Brain draft route. Text never executes by itself; ORION's backend decides. */
  async sendGoal(text,turn,model){const r=await call('POST','/api/local-hand/draft',{goal:text,model:model||pickModel()},{label:'Ask ORION'});return{ok:r.ok,cls:r.cls,error:r.ok?'':r.message,turn}},
  revise:(gesture)=>call('POST','/api/local-hand/revise',{model:pickModel()},{label:'Revise draft',gesture}),
  /* Approve & Run for generated PowerShell. Requires a trusted click. Sends exactly the script ORION proposed. */
  approveScript:(script,gesture)=>call('POST','/api/local-hand/run',{script,publish_github:false},{label:'Approve & Run',gesture}),
  async getMemoryCandidates(){const r=await call('GET','/api/memory/candidates');return r.ok?normalizeCandidates(r.data):[]}
 };
 function pickModel(){const m=st.model;if(!m)return'';const saved=LS('orion.phone.localbrain.model'),loc=m.reviewer.ollama;
  return saved&&loc.includes(saved)?saved:loc.includes(m.defaultModel)?m.defaultModel:(loc[0]||'')}
})();
window.ORION_BRIDGE=RealBridge;
