/* Chat alert controls V1: DOM-only enhancement; no verifier or authority changes. */
(function(){
 'use strict';
 const chat=document.getElementById('chat');
 if(!chat)return;
 function isVerification(node){
  if(node.querySelector('.orion-alert-tools'))return false;
  const text=(node.textContent||'').slice(0,900).toLowerCase();
  return text.includes('failed semantic verification') || text.includes('failed verification');
 }
 function enhance(node){
  if(!isVerification(node))return;
  const body=document.createElement('div');
  body.className='orion-alert-body';
  while(node.firstChild)body.appendChild(node.firstChild);
  const tools=document.createElement('div');tools.className='orion-alert-tools';
  const min=document.createElement('button');min.type='button';min.textContent='−';min.title='Minimize alert';min.setAttribute('aria-label','Minimize verification alert');
  const max=document.createElement('button');max.type='button';max.textContent='□';max.title='Expand alert';max.setAttribute('aria-label','Maximize verification alert');
  const close=document.createElement('button');close.type='button';close.textContent='×';close.title='Dismiss alert';close.setAttribute('aria-label','Close verification alert');
  min.addEventListener('click',()=>{const state=node.classList.toggle('orion-alert-minimized');min.textContent=state?'+':'−';min.title=state?'Restore alert':'Minimize alert';});
  max.addEventListener('click',()=>{const state=node.classList.toggle('orion-alert-maximized');max.textContent=state?'▣':'□';max.title=state?'Restore alert size':'Expand alert';});
  close.addEventListener('click',()=>node.remove());
  tools.append(min,max,close);node.append(tools,body);
 }
 function scan(){chat.querySelectorAll('.m.or').forEach(enhance);}
 let busy=false;
 new MutationObserver(()=>{if(busy)return;busy=true;try{scan();}finally{busy=false;}})
  .observe(chat,{subtree:true,childList:true,characterData:true});
 scan();
})();
