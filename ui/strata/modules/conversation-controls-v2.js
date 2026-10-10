/* Single conversation controls; history remains owned by the existing history module. */
(function(){
 'use strict';
 const chat=document.getElementById('chat'),app=document.getElementById('app');
 if(!chat||!app)return;
 const bar=document.createElement('div');
 bar.className='orion-conversation-tools';
 bar.setAttribute('role','toolbar');
 bar.setAttribute('aria-label','Conversation controls');
 const button=(text,label)=>{
  const el=document.createElement('button');
  el.type='button';el.textContent=text;el.setAttribute('aria-label',label);el.title=label;
  bar.appendChild(el);return el;
 };
 const history=button('History','Open chat history');
 const min=button('−','Minimize conversation');
 const max=button('□','Maximize conversation');
 history.onclick=()=>window.ORION_CHAT_HISTORY?.open?.();
 min.onclick=()=>{
  const closed=app.classList.toggle('orion-conversation-minimized');
  app.classList.remove('orion-conversation-maximized');
  min.textContent=closed?'Restore':'−';
  min.setAttribute('aria-label',closed?'Restore conversation':'Minimize conversation');
  max.textContent='□';
 };
 max.onclick=()=>{
  app.classList.remove('orion-conversation-minimized');min.textContent='−';
  const expanded=app.classList.toggle('orion-conversation-maximized');
  max.textContent=expanded?'▣':'□';
  max.setAttribute('aria-label',expanded?'Restore conversation size':'Maximize conversation');
 };
 function attach(){if(bar.parentNode!==chat)chat.insertBefore(bar,chat.firstChild)}
 attach();
 if(typeof MutationObserver!=='undefined')new MutationObserver(attach).observe(chat,{childList:true});
})();
