/* Live Local Brain chat renderer.
   Owns only the progressive chat bubble. It does not authorize or execute anything. */
window.ORION_LIVE_BRAIN_CHAT=(function(){
 let key='',bubble=null,textNode=null,last='';

 function reset(nextKey){
  key=nextKey||'';
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
  tag.style.fontSize='10px';
  tag.style.opacity='.58';
  tag.style.marginBottom='6px';
  tag.style.letterSpacing='.08em';

  const body=document.createElement('div');
  body.style.whiteSpace='pre-wrap';

  m.appendChild(tag);
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
   if(preview!==last){
    textNode.textContent=preview;
    last=preview;
    chat.scrollTop=1e6;
   }
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
   const tag=bubble.firstChild;
   if(tag)tag.textContent='VERIFIED';
   if(conclusion!==last){
    textNode.textContent=conclusion;
    last=conclusion;
   }
   chat.scrollTop=1e6;
   return;
  }

  if(local.brainState==='blocked'&&bubble&&nextKey===key){
   const tag=bubble.firstChild;
   if(tag)tag.textContent='BLOCKED BY VERIFIER';
   bubble.dataset.liveBrain='blocked';
  }
 }

 return{update,reset};
})();
