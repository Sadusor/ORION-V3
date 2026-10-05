/* render.js — one generic renderer for every connector descriptor (no per-connector UI code). All text is escaped. */
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let ACT={},_n=0;
const resetActions=()=>{ACT={};_n=0};
function renderActions(list){return(list||[]).map(a=>{
 if(a.href)return`<a class="btn" href="${esc(a.href)}">${esc(a.label)}</a>`;
 const id='a'+(++_n);ACT[id]=a;
 return`<button class="btn${a.danger?' danger':''}${a.approval?' approve':''}" data-act="${id}"${a.disabled?' disabled title="PC not connected"':a.hint?` title="${esc(a.hint)}"`:''}>${esc(a.label)}</button>`}).join('')}
function renderConnector(d){
 const caps=(d.capabilities||[]).map(c=>`<span class="chp" title="${esc(c.note||'')}">${esc(c.label||c.id)}</span>`).join('');
 const items=(d.items||[]).map(i=>`<div class="kv"><span>${esc(i.label)}<small>${esc(i.detail||'')}</small></span><span class="ia">${renderActions(i.actions)}</span></div>`).join('');
 const acts=renderActions(d.actions);
 return`<section class="pn cn" data-s="${esc(d.status)}" data-id="${esc(d.id)}"><h4 class="cap">${esc(d.label)}<span class="st">${esc(d.status)}</span></h4>
  <p class="sd">${esc(d.status_detail||'')}</p>${caps?`<div class="chps">${caps}</div>`:''}${items}${acts?`<div class="eng">${acts}</div>`:''}</section>`}
function renderPlanned(list){return`<section class="pn cn" data-s="planned" data-id="planned"><h4 class="cap">Coming later</h4>${list.map(p=>`<div class="kv"><span>${esc(p[1])}<small>${esc(p[2])}</small></span><span class="st">planned</span></div>`).join('')}</section>`}
