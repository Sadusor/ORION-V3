/* History Integrity V1 — advisory read-only presentation classifier.
 * Does not mutate historical records, canonical memory, or runtime authority.
 */
window.ORION_HISTORY_INTEGRITY_V1=(function(){
 'use strict';
 const placeholderLabels=new Set(['copied','copy response','verified','live · unverified','blocked by verifier']);
 function isPlaceholder(role,text){
  return role==='assistant'&&placeholderLabels.has(String(text||'').trim().toLocaleLowerCase());
 }
 function renderStoredMessage(message){
  const damaged=isPlaceholder(message.role,message.text);
  const el=document.createElement('div');
  el.className='m '+(message.role==='user'?'you':'or');
  el.dataset.historyLoaded='1';
  el.dataset.historyId=message.id;
  if(damaged){
   el.dataset.historyIntegrity='placeholder';
   el.textContent='Historical answer unavailable — saved record contains a UI status label.';
   el.title='Original record preserved unchanged; original response not verified or recovered.';
  }else{
   el.textContent=String(message.text||'');
  }
  return el;
 }
 return Object.freeze({isPlaceholder,renderStoredMessage});
})();
