/* ORION chat presentation controls. No backend, verifier or execution changes. */
(function(){
 'use strict';
 const app=document.getElementById('app');
 const chat=document.getElementById('chat');
 const top=document.getElementById('top');
 if(!app||!chat||!top)return;
 const stop=document.getElementById('stopb');
 const actions=top.querySelector('.tl:last-child');
 if(stop&&actions&&stop.parentElement!==actions)actions.insertBefore(stop,actions.firstChild);

 const lanes=document.getElementById('lane-strip');
 if(lanes&&actions){
   const toggle=document.createElement('button');
   toggle.type='button';toggle.className='ib orion-lanes-toggle';
   toggle.textContent='Status';toggle.setAttribute('aria-label','Show project status panels');
   toggle.setAttribute('aria-expanded','false');
   toggle.addEventListener('click',()=>{
     const open=app.classList.toggle('orion-show-status');
     toggle.setAttribute('aria-expanded',String(open));
   });
   actions.insertBefore(toggle,actions.firstChild);
 }
 function controls(node){
   if(node.querySelector(':scope > .orion-reading-tools'))return;
   const tools=document.createElement('div');
   tools.className='orion-reading-tools';
   const min=document.createElement('button'), max=document.createElement('button');
   min.type=max.type='button';
   min.textContent='−';max.textContent='□';
   min.title='Minimize answer';max.title='Maximize answer';
   min.setAttribute('aria-label','Minimize or restore answer');
   max.setAttribute('aria-label','Maximize or restore answer');
   min.onclick=()=>{
     const collapsed=node.classList.toggle('orion-answer-minimized');
     node.classList.remove('orion-answer-maximized');
     if(collapsed)node.classList.remove('orion-answer-maximized');
     min.textContent=collapsed?'Restore':'−';
     min.setAttribute('aria-label',collapsed?'Restore answer':'Minimize answer');
   };
   max.onclick=()=>{
     node.classList.remove('orion-answer-minimized');
     min.textContent='−';
     const expanded=node.classList.toggle('orion-answer-maximized');
     max.textContent=expanded?'▣':'□';
     max.setAttribute('aria-label',expanded?'Restore answer size':'Maximize answer');
   };
   tools.append(min,max);
   const value=(node.textContent||'').toLowerCase();
   if(value.includes('failed semantic verification')||value.includes('failed verification')){
     const close=document.createElement('button');
     close.type='button';close.textContent='×';
     close.title='Dismiss verification alert';
     close.setAttribute('aria-label','Close verification alert');
     close.onclick=()=>node.remove();
     tools.appendChild(close);
   }
   node.insertBefore(tools,node.firstChild);
 }
 function scan(){
   chat.querySelectorAll('.m.or').forEach(controls);
 }
 let scheduled=false;
 const observer=new MutationObserver(()=>{
   if(scheduled)return;
   scheduled=true;
   requestAnimationFrame(()=>{scheduled=false;scan();});
 });
 observer.observe(chat,{childList:true,subtree:false});
 scan();

 // Result and verification cards are rendered in #rz, outside #chat.
 // Enhance them without modifying the frozen shell renderer.
 const results=document.getElementById('rz');
 function decorateResult(card){
   if(card.querySelector(':scope > .orion-reading-tools'))return;
   const tools=document.createElement('div');
   tools.className='orion-reading-tools';
   const min=document.createElement('button'),max=document.createElement('button'),close=document.createElement('button');
   min.type=max.type=close.type='button';
   min.textContent='−';max.textContent='□';close.textContent='×';
   min.title='Minimize panel';max.title='Maximize panel';close.title='Dismiss panel in this view';
   min.setAttribute('aria-label','Minimize or restore panel');
   max.setAttribute('aria-label','Maximize or restore panel');
   close.setAttribute('aria-label','Close panel in this view');
   min.onclick=()=>{const collapsed=card.classList.toggle('orion-answer-minimized');card.classList.remove('orion-answer-maximized');min.textContent=collapsed?'Restore':'−';};
   max.onclick=()=>{card.classList.remove('orion-answer-minimized');min.textContent='−';max.textContent=card.classList.toggle('orion-answer-maximized')?'▣':'□';};
   close.onclick=()=>{card.style.display='none';};
   tools.append(min,max,close);card.insertBefore(tools,card.firstChild);
 }
 if(results){
   const scanResults=()=>results.querySelectorAll('.card.main').forEach(decorateResult);
   new MutationObserver(scanResults).observe(results,{childList:true});
   scanResults();
 }
})();
