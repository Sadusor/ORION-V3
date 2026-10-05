/* Shared test harness (Node, no dependencies). Loads the REAL frontend scripts, in the order each HTML page loads them, into a VM with a stub DOM. */
const vm=require('vm'),fs=require('fs'),path=require('path');
const ROOT=path.join(__dirname,'..');
function stubEl(){const store={};return new Proxy(function(){},{get:(t,k)=>{if(k in store)return store[k];
 if(k==='classList')return{toggle(){},add(){},remove(){},contains:()=>false};if(k==='style')return store.style||(store.style={setProperty(){},cssText:''});
 if(k==='dataset')return store.dataset||(store.dataset={});if(k==='children'||k==='length')return[];if(k==='clientWidth'||k==='clientHeight')return 600;
 if(k==='getContext')return()=>stubEl();if(k===Symbol.toPrimitive)return()=>0;if(k==='then')return undefined;return stubEl()},
 set:(t,k,v)=>{store[k]=v;return true},apply:()=>stubEl()})}
const scriptsOf=html=>[...fs.readFileSync(path.join(ROOT,html),'utf8').matchAll(/<script src="([^"]+)"/g)].map(m=>m[1]);
function makeContext(o){o=o||{};const ids={};
 const doc={getElementById:id=>ids[id]||(ids[id]=stubEl()),createElement:()=>stubEl(),addEventListener(){},hidden:false,body:stubEl()};
 const ls=Object.assign({},o.storage||{});
 const ctx={console,document:doc,matchMedia:()=>({matches:false}),
  localStorage:{getItem:k=>ls[k]||'',setItem:(k,v)=>{ls[k]=String(v)},removeItem:k=>{delete ls[k]}},
  performance,setTimeout:o.setTimeout||setTimeout,clearTimeout,setInterval:()=>0,requestAnimationFrame:()=>0,addEventListener(){},innerWidth:1280,devicePixelRatio:1,
  location:{search:''},URLSearchParams,URL,AbortController,Date,JSON,Math,Promise,getComputedStyle:()=>({getPropertyValue:()=>''}),confirm:()=>true,
  fetch:o.fetch||(()=>{throw new Error('network disabled in unit tests')}),__ids:ids,__ls:ls};
 ctx.window=ctx;vm.createContext(ctx);return ctx}
function loadScripts(ctx,files){for(const f of files)vm.runInContext(fs.readFileSync(path.join(ROOT,f),'utf8'),ctx,{filename:f});return ctx}
function loadPage(html,o){const ctx=makeContext(o);loadScripts(ctx,scriptsOf(html));return ctx}
const run=(ctx,code)=>vm.runInContext(code,ctx);
let fails=0,passes=0;
const ok=(c,m)=>{if(c){passes++;console.log('  ok   '+m)}else{fails++;console.log('  FAIL '+m)}};
const eq=(a,b,m)=>ok(JSON.stringify(a)===JSON.stringify(b),m+(JSON.stringify(a)===JSON.stringify(b)?'':'  (got '+JSON.stringify(a)+', want '+JSON.stringify(b)+')'));
function done(name){console.log(`${name}: ${passes} passed, ${fails} failed`);process.exit(fails?1:0)}
/* core scripts only (no DOM wiring): enough for normalize / reducer / routes / descriptors tests */
const CORE=['config.js','bridge/routes.js','bridge/normalize.js','state/store.js','connectors/descriptors.js','connectors/render.js'];
function coreCtx(){const c=makeContext();loadScripts(c,CORE);return c}
/* real-shaped backend payload builder */
const NOW=new Date().toISOString();
const lane=o=>({run_state:'idle',result:null,output:'',error:'',activity:'idle',goal:'',brain_state:'idle',brain_phase:'idle',brain_next_script:'',brain_next_capability:'',brain_next_url:'',brain_error:'',
 brain_preflight:'not-run',brain_preflight_reason:'',brain_quality_state:'not-run',brain_quality_reason:'',brain_quality_approved_sha256:'',execution_kind:'',execution_action:'',brain_started_utc:null,started_utc:null,finished_utc:null,...o});
const view=(l,extra)=>({mode:'active',run_state:'idle',pending_sha:null,activity:'idle',checkout_sha:'abc',repo:'Sadusor/Orion',branch:'agent/x',project_links:[],dispatch_sessions:[],dispatch_tasks:[],
 provider_vault:{providers:[]},reviewer:{state:'idle',catalog:{models:[{reviewer_id:'r1',provider:'ollama',available:true,model:'qwen35-9b-orion:latest'}]}},local_brain_default_model:'qwen35-9b-orion:latest',
 update_status:{},manual_lane:lane({}),local_hand_lane:lane(l||{}),...(extra||{})});
module.exports={ROOT,vm,fs,path,makeContext,loadScripts,loadPage,scriptsOf,run,ok,eq,done,coreCtx,CORE,lane,view,NOW,stubEl};
