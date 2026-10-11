/* Desktop selector uses ORION's actual, authenticated Local Brain model catalog.
   No model can bypass the existing sendGoal / backend verification path. */
(function(){
'use strict';
const app=document.getElementById('app'),bar=document.getElementById('bar'),bridge=window.ORION_BRIDGE;
if(!app||!bar||!bridge||typeof bridge.sendGoal!=='function')return;
const selector=document.createElement('select');
selector.id='orion-pc-model-choice';
selector.setAttribute('aria-label','Select ORION chat model');
selector.title='Model for the next message';
selector.style.cssText='width:116px;max-width:22vw;min-width:76px;flex:0 0 auto;background:#132434;color:#c3e8f4;border:1px solid #456073;border-radius:20px;padding:8px 5px;font:12px sans-serif;white-space:nowrap;text-overflow:ellipsis;cursor:pointer';
const label=document.createElement('label');
label.htmlFor=selector.id;label.textContent='Model';
label.style.cssText='position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)';
const sendButton=document.getElementById('send');
bar.insertBefore(label,sendButton||null);
bar.insertBefore(selector,sendButton||null);
let selected='',available=[],loading=null;
function render(models,defaultModel){
 if(!Array.isArray(models))models=[];
 available=[...new Set(models.filter(x=>typeof x==='string'&&x.trim()).map(x=>x.trim()))];
 if(!available.length){
  selector.replaceChildren(new Option('PC models unavailable',''));selector.disabled=true;selected='';return;
 }
 const preferred=available.includes(selected)?selected:available.includes(defaultModel)?defaultModel:available[0];
 selector.replaceChildren(...available.map(x=>new Option(x,x)));
 selector.disabled=false;selector.value=preferred;selected=preferred;
}
async function refresh(){
 if(loading)return loading;
 loading=(async()=>{
  try{
   const result=await bridge.call('GET','/api/models',null,{silent:true});
   if(!result?.ok||!Array.isArray(result.data?.models)){
    if(!available.length)render([], '');
    return;
   }
   render(result.data.models,result.data.default_model||'');
  }catch(_){if(!available.length)render([], '');}
 })();
 try{await loading}finally{loading=null}
}
selector.addEventListener('change',()=>{if(available.includes(selector.value))selected=selector.value});
const send=bridge.sendGoal.bind(bridge);
bridge.sendGoal=function(text,turn,model){
 const chosen=model||(available.includes(selected)?selected:'');
 return send(text,turn,chosen);
};
bridge.subscribe?.(event=>{if(event?.type==='link'&&event.link?.status==='live'&&!available.length)refresh()});
refresh();
})();