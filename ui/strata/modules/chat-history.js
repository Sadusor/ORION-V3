/* Bounded chat-history UI + phone/PC sync.
   Storage only: this module never authorizes or executes ORION actions. */
window.ORION_CHAT_HISTORY=(function(){
 const SCHEMA='orion.chat-history/1';
 const native=window.ORION_NATIVE_HISTORY||null;
 const nativeApp=window.ORION_NATIVE_APP||null;
 let state={schema:SCHEMA,conversations:[],messages:[]},ready=false,syncTimer=0,actionTarget='';
 const escH=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 const now=()=>Date.now(),uid=p=>p+'-'+now().toString(36)+'-'+Math.random().toString(36).slice(2,9);
 const asBool=v=>v===true||v===1||v==='1';
 const chat=()=>document.getElementById('chat');

 function normalize(x){
  x=x&&typeof x==='object'?x:{};
  return{schema:SCHEMA,conversations:Array.isArray(x.conversations)?x.conversations:[],messages:Array.isArray(x.messages)?x.messages:[]}
 }
 function nativeSnapshot(){
  if(!native||typeof native.snapshot!=='function')return null;
  try{return normalize(JSON.parse(native.snapshot()))}catch(e){console.warn('[history] native snapshot',e);return null}
 }
 function nativeMerge(payload){
  if(!native||typeof native.merge!=='function')return null;
  try{return normalize(JSON.parse(native.merge(JSON.stringify(payload))))}catch(e){console.warn('[history] native merge',e);return null}
 }
 function mergeMemory(a,b){
  const cm=new Map();
  [...normalize(a).conversations,...normalize(b).conversations].forEach(c=>{
   if(!c||!c.id)return;const old=cm.get(c.id);
   if(!old||+(c.updated_at_ms||0)>=+(old.updated_at_ms||0))cm.set(c.id,c)
  });
  const mm=new Map();
  [...normalize(a).messages,...normalize(b).messages].forEach(m=>{if(m&&m.id&&!mm.has(m.id))mm.set(m.id,m)});
  return{schema:SCHEMA,conversations:[...cm.values()],messages:[...mm.values()]}
 }
 function activeConversations(){return state.conversations.filter(c=>!asBool(c.deleted)&&!asBool(c.archived))}
 function getConversation(id){return state.conversations.find(c=>c.id===id)}
 function conversationMessages(id){return state.messages.filter(m=>m.conversation_id===id).sort((a,b)=>+a.created_at_ms-+b.created_at_ms)}
 function currentId(){return (typeof V!=='undefined'&&V.convId)||''}
 function setCurrent(id){if(typeof V!=='undefined'){V.convId=id;V.turns=[]}}
 function ensureConversation(id){
  if(!id)return;
  if(getConversation(id))return;
  const t=now(),c={id,title:'New chat',project_id:'',pinned:0,archived:0,deleted:0,created_at_ms:t,updated_at_ms:t};
  applyLocal({conversations:[c],messages:[]},false)
 }
 function applyLocal(delta,triggerSync=true){
  const mergedNative=nativeMerge(delta);
  state=mergedNative||mergeMemory(state,delta);
  if(triggerSync)scheduleSync(250);
  renderHistory();
 }
 async function syncNow(){
  clearTimeout(syncTimer);
  const n=nativeSnapshot();if(n)state=mergeMemory(state,n);
  if(!window.ORION_BRIDGE||typeof ORION_BRIDGE.call!=='function'){renderHistory();return}
  const link=ORION_BRIDGE.link&&ORION_BRIDGE.link();
  if(link&&['offline','unpaired'].includes(link.status)){renderHistory();return}
  try{
   const r=await ORION_BRIDGE.call('POST','/api/chat-history/sync',state,{label:'Chat history sync',silent:true});
   if(r&&r.ok&&r.data){
    state=normalize(r.data);
    const merged=nativeMerge(state);if(merged)state=merged;
    renderHistory()
   }
  }catch(e){console.warn('[history] sync',e)}
 }
 function scheduleSync(ms=600){clearTimeout(syncTimer);syncTimer=setTimeout(syncNow,ms)}

 function record(role,text,source,node){
  text=String(text||'').trim();if(!text||!['user','assistant'].includes(role))return;
  const cid=currentId()||uid('c');if(!currentId())setCurrent(cid);
  ensureConversation(cid);
  const c=getConversation(cid),t=now();
  const title=(c&&c.title&&c.title!=='New chat')?c.title:(role==='user'?text.slice(0,58):'New chat');
  const mid=(node&&node.dataset.historyId)||uid('m');if(node)node.dataset.historyId=mid;
  if(state.messages.some(m=>m.id===mid))return;
  applyLocal({
   conversations:[{...c,id:cid,title,updated_at_ms:t}],
   messages:[{id:mid,conversation_id:cid,role,text,source:source||'',created_at_ms:t}]
  })
 }
 function textOfNode(n){
  if(!n||!n.classList||!n.classList.contains('m'))return null;
  if(n.dataset.historyLoaded==='1')return null;
  if(n.classList.contains('you'))return{role:'user',text:n.textContent,source:PHONE?'phone-text':'pc-text'};
  if(n.classList.contains('or')){
   if(n.dataset.liveBrain==='unverified')return null;
   const body=n.dataset.liveBrain?n.lastElementChild:null;
   return{role:'assistant',text:body?body.textContent:n.textContent,source:PHONE?'orion-live-phone':'orion-live-pc'}
  }
  return null
 }
 function observeChat(){
  const host=chat();if(!host||typeof MutationObserver==='undefined')return;
  const scan=n=>{
   if(n&&n.nodeType===1){
    const item=textOfNode(n);if(item)record(item.role,item.text,item.source,n);
    if(n.querySelectorAll)n.querySelectorAll('.m').forEach(x=>{const it=textOfNode(x);if(it)record(it.role,it.text,it.source,x)})
   }
  };
  host.childNodes.forEach(scan);
  new MutationObserver(ms=>{
   ms.forEach(m=>{
    if(m.type==='childList')m.addedNodes.forEach(scan);
    else if(m.type==='attributes')scan(m.target)
   })
  }).observe(host,{childList:true,subtree:true,attributes:true,attributeFilter:['data-live-brain']})
 }

 function loadConversation(id){
  const c=getConversation(id);if(!c)return;
  setCurrent(id);
  if(window.ORION_LIVE_BRAIN_CHAT&&ORION_LIVE_BRAIN_CHAT.reset)ORION_LIVE_BRAIN_CHAT.reset('');
  const host=chat();if(host){
   host.textContent='';
   conversationMessages(id).forEach(m=>{
    if(!['user','assistant'].includes(m.role))return;
    const el=document.createElement('div');el.className='m '+(m.role==='user'?'you':'or');el.textContent=m.text;
    el.dataset.historyLoaded='1';el.dataset.historyId=m.id;host.appendChild(el)
   });
   host.scrollTop=host.scrollHeight
  }
  if(typeof app!=='undefined')app.classList.toggle('has-chat',conversationMessages(id).length>0);
  closeAction();closeDrawer();renderHistory()
 }
 function newConversation(){
  const id=uid('c'),t=now();setCurrent(id);
  applyLocal({conversations:[{id,title:'New chat',project_id:'',pinned:0,archived:0,deleted:0,created_at_ms:t,updated_at_ms:t}],messages:[]});
  if(chat())chat().textContent='';
  if(window.ORION_LIVE_BRAIN_CHAT&&ORION_LIVE_BRAIN_CHAT.reset)ORION_LIVE_BRAIN_CHAT.reset('');
  if(typeof app!=='undefined')app.classList.remove('has-chat');
  closeDrawer();const i=document.getElementById('inp');if(i)i.focus()
 }
 function patchConversation(id,patch){
  const c=getConversation(id);if(!c)return;
  applyLocal({conversations:[{...c,...patch,updated_at_ms:now()}],messages:[]})
 }
 function group(ts){const d=(now()-Number(ts||0))/86400000;return d<=7?'7 Days':d<=30?'30 Days':'Older'}
 function renderHistory(){
  const host=document.getElementById('orionHistoryList'),deskHost=document.getElementById('orionHistoryDesktopList');if(!host&&!deskHost)return;
  const rawQ=(document.activeElement&&document.activeElement.id==='orionHistoryDesktopSearch'?document.getElementById('orionHistoryDesktopSearch')?.value:document.getElementById('orionHistorySearch')?.value)||'';const q=String(rawQ).trim().toLowerCase();
  const items=activeConversations().filter(c=>{
   if(!q)return true;if(String(c.title||'').toLowerCase().includes(q))return true;
   return state.messages.some(m=>m.conversation_id===c.id&&String(m.text||'').toLowerCase().includes(q))
  }).sort((a,b)=>{const p=Number(b.pinned)-Number(a.pinned);return p||Number(b.updated_at_ms)-Number(a.updated_at_ms)});
  const groups={};items.forEach(c=>(groups[group(c.updated_at_ms)]??=[]).push(c));
  const html=['7 Days','30 Days','Older'].filter(k=>groups[k]).map(k=>
   '<section class="oh-group"><h4>'+k+'</h4>'+groups[k].map(c=>
    '<div class="oh-row '+(c.id===currentId()?'on':'')+'"><button data-oh-open="'+escH(c.id)+'">'+(asBool(c.pinned)?'📌 ':'')+escH(c.title||'New chat')+'</button><button class="oh-more" data-oh-more="'+escH(c.id)+'" aria-label="Chat actions">•••</button></div>'
   ).join('')+'</section>'
  ).join('')||'<p class="oh-empty">No chats yet.</p>';if(host)host.innerHTML=html;if(deskHost)deskHost.innerHTML=html
 }
 function openDrawer(){
  if(typeof app!=='undefined'&&app.classList.contains('phone')){app.classList.add('mobile-menu-open');app.classList.remove('mobile-quick-open')}
  else document.getElementById('orionHistoryDesktop')?.classList.add('on');
  renderHistory()
 }
 function closeDrawer(){if(typeof app!=='undefined')app.classList.remove('mobile-menu-open');document.getElementById('orionHistoryDesktop')?.classList.remove('on')}
 function openAction(id){actionTarget=id;document.getElementById('orionHistoryActions')?.classList.add('on')}
 function closeAction(){document.getElementById('orionHistoryActions')?.classList.remove('on');actionTarget=''}
 async function share(id){
  const c=getConversation(id);if(!c)return;
  const text=conversationMessages(id).filter(m=>['user','assistant'].includes(m.role)).map(m=>(m.role==='user'?'You: ':'ORION: ')+m.text).join('\n\n');
  try{if(navigator.share)await navigator.share({title:c.title||'ORION chat',text});else if(navigator.clipboard){await navigator.clipboard.writeText(text);if(typeof toast==='function')toast('Chat copied')}}catch(_){}
 }
 function installUi(){
  if(document.getElementById('orionHistoryList'))return true;
  const nav=document.getElementById('product-nav'),head=nav&&nav.querySelector('.mobile-nav-head');if(!nav||!head)return false;
  const section=document.createElement('section');section.id='orionHistoryBlock';section.innerHTML=
   '<button id="orionNewChat" type="button">＋ New chat</button>'+
   '<div class="oh-searchrow"><input id="orionHistorySearch" placeholder="Search chat content…" aria-label="Search chats"><button id="orionHistoryRefresh" title="Refresh history">↻</button></div>'+
   '<div id="orionHistoryList"></div>';
  head.insertAdjacentElement('afterend',section);

  const desk=document.createElement('aside');desk.id='orionHistoryDesktop';desk.innerHTML='<header><b>Chat history</b><button data-oh-close>×</button></header><div class="oh-deskbody"><button id="orionDesktopNewChat" type="button">＋ New chat</button><div class="oh-searchrow"><input id="orionHistoryDesktopSearch" placeholder="Search chat content…" aria-label="Search chats"><button id="orionHistoryDesktopRefresh" title="Refresh history">↻</button></div><div id="orionHistoryDesktopList"></div></div>';document.body.appendChild(desk);
  const actions=document.createElement('section');actions.id='orionHistoryActions';actions.innerHTML=
   '<button data-oh-act="share">Share</button><button data-oh-act="pin">Pin</button><button data-oh-act="project">Add to project</button>'+
   '<button disabled>Uploaded files<small>planned</small></button><button data-oh-act="find">Find in chat</button><button disabled>Add to home<small>planned</small></button>'+
   '<button data-oh-act="archive">Archive</button><button class="danger" data-oh-act="delete">Delete</button><button data-oh-act="close">Close</button>';
  document.body.appendChild(actions);

  const style=document.createElement('style');style.textContent=
   '#orionHistoryBlock{display:none}.phone #orionHistoryBlock{display:block;padding:8px 10px 4px;border-bottom:1px solid rgba(255,255,255,.07)}'+
   '#orionNewChat{width:100%;height:44px;border:0;border-radius:12px;background:#24272b;color:#eef1f4;font-weight:600}.oh-searchrow{display:grid;grid-template-columns:1fr 38px;gap:6px;margin-top:8px}.oh-searchrow input{min-width:0;height:40px;border:1px solid rgba(255,255,255,.08);border-radius:20px;background:#202328;color:#eef1f4;padding:0 13px;outline:0}.oh-searchrow button{border:0;border-radius:50%;background:transparent;color:#9aa3ad;font-size:18px}#orionHistoryList{max-height:42vh;overflow:auto;padding:5px 0}.oh-group h4{margin:10px 8px 3px;color:#89939f;font-size:11px}.oh-row{display:grid;grid-template-columns:1fr 34px;align-items:center;border-radius:10px}.oh-row.on{background:#25292e}.oh-row>button:first-child{min-width:0;border:0;background:transparent;color:#edf0f3;text-align:left;padding:9px 8px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.oh-more{border:0;background:transparent;color:#8c96a2;height:34px}.oh-empty{color:#7f8995;padding:10px;font-size:12px}'+
   '#orionHistoryActions{display:none;position:fixed;z-index:50;left:14px;right:14px;bottom:calc(14px + env(safe-area-inset-bottom));grid-template-columns:repeat(3,1fr);gap:7px;padding:10px;border-radius:20px;background:#292d32;border:1px solid rgba(255,255,255,.1);box-shadow:0 16px 50px #000b}#orionHistoryActions.on{display:grid}#orionHistoryActions button{min-height:58px;border:0;border-radius:13px;background:#34383d;color:#edf0f3}#orionHistoryActions button:disabled{opacity:.35}#orionHistoryActions small{display:block;font-size:9px}#orionHistoryActions .danger{color:#ff8585}'+
   '#orionHistoryDesktop{display:none;position:fixed;z-index:45;left:50%;top:50%;width:min(620px,90vw);height:min(700px,82vh);transform:translate(-50%,-50%);background:#11151a;border:1px solid rgba(255,255,255,.1);border-radius:22px;box-shadow:0 24px 80px #000c;padding:12px}#orionHistoryDesktop.on{display:block}#orionHistoryDesktop header{display:flex;justify-content:space-between;align-items:center;padding:8px}#orionHistoryDesktop header button{border:0;background:transparent;color:#eee;font-size:24px}#orionHistoryDesktop .oh-deskbody{height:calc(100% - 48px);overflow:auto;padding:4px 8px}#orionDesktopNewChat{width:100%;height:44px;border:0;border-radius:12px;background:#24272b;color:#eef1f4;font-weight:600}#orionHistoryDesktopList{padding-top:6px}';
  document.head.appendChild(style);

  const settings=document.getElementById('mobileSettings');
  if(settings){
   const memory=document.createElement('button');memory.type='button';memory.className='mobile-connection';memory.id='orionMemoryInfo';
   memory.textContent='Local chat memory · 50 chats max';memory.onclick=openDrawer;settings.appendChild(memory);
   if(nativeApp&&typeof nativeApp.openOffline==='function'){
    const offline=document.createElement('button');offline.type='button';offline.className='mobile-connection';offline.id='orionUseOffline';
    offline.textContent='Use offline bot · Qwen3-0.6B';offline.onclick=()=>nativeApp.openOffline();settings.appendChild(offline)
   }
  }

  document.getElementById('orionNewChat').onclick=newConversation;
  document.getElementById('orionHistorySearch').oninput=renderHistory;
  document.getElementById('orionHistoryRefresh').onclick=syncNow;
  document.getElementById('orionDesktopNewChat').onclick=newConversation;
  document.getElementById('orionHistoryDesktopSearch').oninput=renderHistory;
  document.getElementById('orionHistoryDesktopRefresh').onclick=syncNow;
  const historyClick=e=>{const a=e.target.closest('[data-oh-open]'),m=e.target.closest('[data-oh-more]');if(a)loadConversation(a.dataset.ohOpen);else if(m)openAction(m.dataset.ohMore)};
  section.addEventListener('click',historyClick);document.getElementById('orionHistoryDesktopList').addEventListener('click',historyClick);
  actions.addEventListener('click',e=>{const b=e.target.closest('[data-oh-act]');if(!b)return;const a=b.dataset.ohAct,c=getConversation(actionTarget);if(a==='close')return closeAction();if(!c)return;
   if(a==='share')share(c.id);
   if(a==='pin')patchConversation(c.id,{pinned:asBool(c.pinned)?0:1});
   if(a==='project'){const pid=(typeof V!=='undefined'&&V.ui&&V.ui.project&&V.ui.project.activeLinkId)||'';if(pid)patchConversation(c.id,{project_id:pid});else if(typeof toast==='function')toast('No active project reported by ORION')}
   if(a==='find'){loadConversation(c.id);setTimeout(()=>{const q=prompt('Find in this chat');if(q&&typeof window.find==='function'&&typeof toast==='function')toast(window.find(q)?'Found':'Not found')},60)}
   if(a==='archive'){patchConversation(c.id,{archived:1});if(c.id===currentId())newConversation()}
   if(a==='delete'){patchConversation(c.id,{deleted:1});if(c.id===currentId())newConversation()}
   closeAction()
  });
  desk.querySelector('[data-oh-close]').onclick=closeDrawer;
  const hist=document.getElementById('histb');if(hist)hist.onclick=openDrawer;
  renderHistory();return true
 }
 function init(){
  const n=nativeSnapshot();if(n)state=mergeMemory(state,n);
  ensureConversation(currentId());
  observeChat();
  let tries=0;const t=setInterval(()=>{if(installUi()||++tries>40)clearInterval(t)},125);
  scheduleSync(700);setInterval(()=>{if(!document.hidden)syncNow()},15000);
  setInterval(()=>{if(document.hidden||!nativeApp||typeof nativeApp.openOffline!=='function'||!ORION_BRIDGE.link)return;const l=ORION_BRIDGE.link();if(l&&l.status==='offline')nativeApp.openOffline()},10000);
  ready=true
 }
 return{init,sync:syncNow,newChat:newConversation,open:openDrawer,load:loadConversation,get snapshot(){return state}};
})();
setTimeout(()=>window.ORION_CHAT_HISTORY.init(),0);
