/* Live Local Brain chat renderer.
   Owns only the progressive chat bubble. It does not authorize or execute anything. */
window.ORION_LIVE_BRAIN_CHAT=(function(){
 let key='',bubble=null,textNode=null,last='',target='',frame=0;
 function cancelReveal(){if(frame){cancelAnimationFrame(frame);frame=0;}}
 function reveal(chat){
  frame=0;
  if(!textNode||!bubble||!bubble.isConnected)return;
  if(!target.startsWith(last)){last='';textNode.textContent='';}
  if(last.length>=target.length)return;
  const atBottom=nearBottom(chat);
  // Display only text already received; catch up quickly if polling delivers large batches.
  const pending=target.length-last.length;
  const step=Math.max(1,Math.ceil(pending/8));
  last=target.slice(0,last.length+step);
  textNode.textContent=last;
  follow(chat,atBottom);
  if(last.length<target.length)frame=requestAnimationFrame(()=>reveal(chat));
 }
 function queueReveal(preview,chat){
  target=preview;
  if(!frame&&last!==target)frame=requestAnimationFrame(()=>reveal(chat));
 }
 function nearBottom(chat){return chat.scrollHeight-chat.scrollTop-chat.clientHeight<100;}
 function follow(chat,shouldFollow){if(shouldFollow)chat.scrollTop=chat.scrollHeight;}

 function reset(nextKey){
  cancelReveal();
  key=nextKey||'';
  target='';
  bubble=null;
  textNode=null;
  last='';
 }

 function make(chat){
  const m=document.createElement('div');
  m.className='m or';
  m.dataset.liveBrain='unverified';

  const tag=document.createElement('div');
  tag.textContent='LIVE · UNVERIFIED';
  tag.dataset.liveBrainLabel='1';
  tag.style.fontSize='10px';
  tag.style.opacity='.58';
  tag.style.marginBottom='6px';
  tag.style.letterSpacing='.08em';

  const tools=document.createElement('div');
  tools.className='orion-reading-tools';
  const min=document.createElement('button');
  const max=document.createElement('button');
  min.type=max.type='button';
  min.textContent='−';max.textContent='□';
  min.title='Minimize or restore answer';max.title='Maximize or restore answer';
  min.setAttribute('aria-label','Minimize or restore answer');
  max.setAttribute('aria-label','Maximize or restore answer');
  min.addEventListener('click',()=>{
   const reduced=m.classList.toggle('orion-answer-minimized');
   m.classList.remove('orion-answer-maximized');
   min.textContent=reduced?'Restore':'−';max.textContent='□';
  });
  max.addEventListener('click',()=>{
   m.classList.remove('orion-answer-minimized');min.textContent='−';
   const expanded=m.classList.toggle('orion-answer-maximized');
   max.textContent=expanded?'▣':'□';
  });
  tools.append(min,max);

  const body=document.createElement('div');
  body.style.whiteSpace='pre-wrap';

  const copy=document.createElement('button');
  copy.type='button';
  copy.className='orion-copy-response';
  copy.textContent='Copy response';
  copy.title='Copy all response text, including while streaming';
  copy.addEventListener('click',async()=>{
   const value=target||body.textContent||'';
   try{await navigator.clipboard.writeText(value);copy.textContent='Copied';}
   catch(_){const selection=window.getSelection();const range=document.createRange();range.selectNodeContents(body);selection.removeAllRanges();selection.addRange(range);copy.textContent='Select text to copy';}
  });
  const revise=document.createElement('button');
  revise.type='button';
  revise.className='orion-copy-response orion-revise-response';
  revise.textContent='Revise';
  revise.title='Ask Local Brain to revise this completed answer; no actions executed';
  revise.hidden=true;
  revise.addEventListener('click',async(event)=>{
   if(m.dataset.liveBrain!=='verified'||!window.ORION_BRIDGE?.revise)return;
   const identity={conversationId:m.dataset.conversationId||'',turnId:m.dataset.turnId||''};
   if(!identity.conversationId||!identity.turnId){revise.textContent='Unavailable';return;}
   revise.disabled=true;
   revise.textContent='Revising…';
   try{
    const response=await window.ORION_BRIDGE.revise(identity,event);
    if(!response?.ok){
     revise.textContent='Revise failed';
     revise.title=String(response?.message||response?.error||'Revision unavailable');
    }else{
     revise.textContent='Revision requested';
    }
   }catch(error){
    revise.textContent='Revise failed';
    revise.title=String(error?.message||'Revision unavailable');
   }finally{revise.disabled=false}
  });
  m.appendChild(tools);
  m.appendChild(tag);
  m.appendChild(copy);
  m.appendChild(revise);
  m.appendChild(body);
  chat.appendChild(m);
  bubble=m;
  textNode=body;
  return m;
 }

 function ensure(chat,nextKey){
  if(nextKey!==key)reset(nextKey);
  if(!bubble)make(chat);
 }

 function update(local,chat){
  if(!local||!chat)return;
  const nextKey=local.brainStartedUtc||'';
  if(!nextKey)return;

  const preview=local.preview||'';
  const conclusion=local.conclusion||'';

  if(local.brainState==='running'&&preview){
   ensure(chat,nextKey);
   if(preview!==target)queueReveal(preview,chat);
   return;
  }

  if(local.brainState==='ready'&&conclusion){
   const alreadyStored=[...chat.querySelectorAll('.m.or[data-history-loaded="1"]')].some(
    n=>String(n.textContent||'').trim()===String(conclusion||'').trim()
   );
   if(alreadyStored){
    reset(nextKey);
    last=conclusion;
    return;
   }
   ensure(chat,nextKey);
   bubble.dataset.liveBrain='verified';
   bubble.dataset.conversationId=String(local.conversationId||'');
   bubble.dataset.turnId=String(nextKey);
   const revise=bubble.querySelector('.orion-revise-response');if(revise)revise.hidden=false;
   const tag=bubble.querySelector('[data-live-brain-label]');
   if(tag)tag.textContent='REVIEWED · FACTS UNVERIFIED';
   const atBottom=nearBottom(chat);
   cancelReveal();
   target=conclusion;
   if(conclusion!==last){
    textNode.textContent=conclusion;
    last=conclusion;
   }
   follow(chat,atBottom);
   return;
  }

  if(local.brainState==='blocked'&&bubble&&nextKey===key){
   cancelReveal();
   const tag=bubble.firstChild;
   if(tag)tag.textContent='BLOCKED BY VERIFIER';
   bubble.dataset.liveBrain='blocked';
  }
 }

 return{update,reset};
})();
