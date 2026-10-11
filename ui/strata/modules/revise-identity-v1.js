/* Additive compatibility shim: use real current backend turn identity for existing Revise button. */
(function(){
'use strict';
const bridge=window.ORION_BRIDGE;
if(!bridge||typeof bridge.revise!=='function'||typeof bridge.getModel!=='function')return;
const original=bridge.revise.bind(bridge);
bridge.revise=function(target,gesture){
  // Legacy shell calls revise(clickEvent). Do not synthesize IDs or permit stale calls.
  const event=target&&typeof target==='object'&&'isTrusted' in target?target:gesture;
  const requested=(event===target)?null:target;
  const local=bridge.getModel()?.local||{};
  const current={conversationId:String(local.conversationId||''),turnId:String(local.brainStartedUtc||'')};
  const id=requested&&requested.conversationId&&requested.turnId?requested:current;
  if(!id.conversationId||!id.turnId||local.brainState!=='ready'){
    return Promise.resolve({ok:false,cls:'rejected',message:'Revision unavailable: no completed conversation and turn identity.',label:'Revise draft',route:'/api/local-hand/revise',method:'POST',status:409});
  }
  return original(id,event);
};
})();