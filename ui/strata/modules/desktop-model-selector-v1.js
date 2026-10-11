/* PC-only, replaceable model choice. Backend remains the authority for model availability. */
(function(){
'use strict';
const app=document.getElementById('app'), bar=document.getElementById('bar');
const bridge=window.ORION_BRIDGE;
if(!app||!bar||!bridge||app.classList.contains('phone')||typeof bridge.sendGoal!=='function')return;
const selector=document.createElement('select');
selector.id='orion-pc-model-choice';selector.setAttribute('aria-label','Select ORION chat model');selector.title='Model for the next message';
selector.style.cssText='max-width:210px;min-width:110px;flex:0 1 210px;background:#132434;color:#c3e8f4;border:1px solid #456073;border-radius:20px;padding:9px;font:13px sans-serif';
const label=document.createElement('label');label.htmlFor=selector.id;label.textContent='Model';label.style.cssText='position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)';
bar.insertBefore(label,bar.firstChild);bar.insertBefore(selector,bar.firstChild);
let selected='';
function update(){
 const data=bridge.getModel?.();
 const models=data?.reviewer?.ollama;
 if(!Array.isArray(models)||!models.length){selector.replaceChildren(new Option('PC models unavailable',''));selector.disabled=true;selected='';return}
 const previous=selected||selector.value;
 selector.replaceChildren(...models.filter(x=>typeof x==='string'&&x.trim()).map(x=>new Option('Local · '+x,x)));
 selector.disabled=false;
 if(models.includes(previous))selector.value=previous;
 else selector.selectedIndex=0;
 selected=selector.value;
}
selector.addEventListener('change',()=>{selected=selector.value});
const send=bridge.sendGoal.bind(bridge);
bridge.sendGoal=function(text,turn,model){
 const available=bridge.getModel?.()?.reviewer?.ollama||[];
 const chosen=model||(available.includes(selected)?selected:'');
 return send(text,turn,chosen);
};
bridge.subscribe?.(event=>{if(event?.type==='snapshot')update()});
update();
})();