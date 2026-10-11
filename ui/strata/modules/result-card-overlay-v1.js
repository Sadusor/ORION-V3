/* Additive overflow-safe reading overlay for result cards; frozen card controls untouched. */
(function(){
'use strict';
const root=document.getElementById('rz');if(!root)return;
const style=document.createElement('style');style.textContent=`
#orion-result-overlay-v1{position:fixed;inset:0;z-index:1000;background:rgba(2,7,13,.82);display:flex;align-items:center;justify-content:center;padding:16px;box-sizing:border-box}
#orion-result-overlay-v1[hidden]{display:none!important}
#orion-result-overlay-v1 .orion-overlay-panel{position:relative;box-sizing:border-box;max-width:100%;width:min(900px,100%);max-height:calc(100dvh - 32px);overflow:auto;overflow-wrap:anywhere;min-width:0;background:#101d2b;border:1px solid #456073;border-radius:14px;padding:20px;color:#d8e4ee}
#orion-result-overlay-v1 .orion-overlay-panel pre{white-space:pre-wrap;overflow-wrap:anywhere}
#orion-result-overlay-v1 .orion-overlay-close{position:sticky;top:0;float:right;border:1px solid #58758a;background:#21384a;color:white;border-radius:8px;padding:8px 14px;cursor:pointer;z-index:2}
`;document.head.appendChild(style);
const overlay=document.createElement('section');overlay.id='orion-result-overlay-v1';overlay.hidden=true;overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label','Expanded result');
const panel=document.createElement('div');panel.className='orion-overlay-panel';
const close=document.createElement('button');close.type='button';close.className='orion-overlay-close';close.textContent='Restore ×';close.setAttribute('aria-label','Restore normal result view');
overlay.appendChild(panel);document.body.appendChild(overlay);
function dismiss(){overlay.hidden=true;panel.replaceChildren();document.body.style.overflow=''}
close.addEventListener('click',dismiss);overlay.addEventListener('click',e=>{if(e.target===overlay)dismiss()});
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!overlay.hidden)dismiss()});
root.addEventListener('click',e=>{
 const btn=e.target.closest('.orion-reading-tools button');if(!btn||!(btn.textContent==='□'||btn.textContent==='▣'))return;
 const card=btn.closest('.card.main');if(!card)return;
 e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
 card.classList.remove('orion-answer-maximized','orion-answer-minimized');
 const content=card.cloneNode(true);
 content.querySelector(':scope > .orion-reading-tools')?.remove();
 panel.replaceChildren(close,content);
 overlay.hidden=false;document.body.style.overflow='hidden';close.focus();
},true);
})();