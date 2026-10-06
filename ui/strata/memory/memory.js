const escH=v=>String(v==null?'':v).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
/* Memory Universe (visual concept kept). Data comes ONLY from B.getMemory(); empty => honest empty state. */
/* --- memory universe: camera flies through ORION into the constellation --- */
const muc=$("muc"),mctx=muc.getContext("2d");let MU={nodes:[],sel:null,q:"",old:false,t0:0,hover:null};
const KC={fact:"#c9eef5",lesson:"#e0b867",evidence:"#9d90e8",candidate:"#9d90e8"};
async function openMemory(q){layer("cc",0);MU.q=q||"";const mem=await MemoryAdapters.load(B,MU.q);MU.nodes=mem.nodes;MU.sources=mem.sources;$("mq").value=MU.q;MU.sel=null;$("mud").classList.remove("on");
 app.classList.add("mem");S.mem=true;wake();setTimeout(()=>{layer("mu",1);MU.t0=performance.now();muLayout();muLoop()},650)}
function closeMemory(){layer("mu",0);app.classList.remove("mem");S.mem=false;wake()}
$("mux").onclick=closeMemory;$("sch").onkeydown=e=>{if(e.key==="Enter")openMemory(e.target.value)};
function muLayout(){const w=muc.clientWidth,h=muc.clientHeight,d=Math.min(devicePixelRatio||1,2);muc.width=w*d;muc.height=h*d;mctx.setTransform(d,0,0,d,0,0);
 const P=[...new Set(MU.nodes.map(n=>n.project))],R0=Math.min(w,h)*.27;
 P.forEach((p,i)=>{const a=-1.57+i*6.283/P.length,px=w/2+Math.cos(a)*R0*1.1,py=h/2+Math.sin(a)*R0*.85;let k=0;MU.nodes.filter(n=>n.project===p).forEach(n=>{const b=k++*2.399,r=24+Math.sqrt(k)*19;n.x=px+Math.cos(b)*r;n.y=py+Math.sin(b)*r*.8});
  MU.nodes.filter(n=>n.project===p).label=[px,py,p];(MU.labels=MU.labels||{})[p]=[px,py]})}
function visible(n){return MU.old||n.status!=="superseded"||MU.sel===n}
function muLoop(){if(!S.mem)return;muDraw();if(performance.now()-MU.t0<1100)requestAnimationFrame(muLoop)}
function muDraw(){const w=muc.clientWidth,h=muc.clientHeight,p=Math.min((performance.now()-MU.t0)/1000,1),e=1-Math.pow(1-p,3),sc=.35+.65*e,cx=w/2,cy=h/2;
 mctx.clearRect(0,0,w,h);$("msrc").innerHTML=(MU.sources||[]).map(x=>`<span class="srcchip ${x.available?"on":""}" title="${escH(x.note||"")}">${escH(x.label)} · ${x.available?(x.count==null?"?":x.count):"unavailable"}${x.authoritative?" · authoritative":""}</span>`).join("");if(!MU.nodes.length){mctx.fillStyle="#9fb0bf";mctx.font="14px sans-serif";mctx.textAlign="center";mctx.fillText("No Memory data available from ORION yet. The canonical Memory Explorer is not connected.",w/2,h/2);mctx.textAlign="left";return}const N=MU.nodes,by=id=>N.find(n=>n.id===id),q=MU.q.toLowerCase(),match=n=>!q||n.t.toLowerCase().includes(q)||n.project.toLowerCase().includes(q);
 const X=n=>cx+(n.x-cx)*sc,Y=n=>cy+(n.y-cy)*sc;mctx.globalAlpha=e;
 const link=(a,b,c,dash)=>{if(!a||!b||!visible(a)||!visible(b))return;mctx.strokeStyle=c;mctx.setLineDash(dash?[4,4]:[]);mctx.beginPath();mctx.moveTo(X(a),Y(a));mctx.lineTo(X(b),Y(b));mctx.stroke()};
 N.forEach(n=>{if(n.by)link(n,by(n.by),"rgba(201,238,245,.3)",1);if(n.from)link(by(n.from),n,"rgba(224,184,103,.55)");(n.links||[]).forEach(l=>link(n,by(l),"rgba(157,144,232,.4)"))});mctx.setLineDash([]);
 for(const p in MU.labels){const [px,py]=MU.labels[p];mctx.fillStyle="rgba(118,207,228,.9)";mctx.beginPath();mctx.arc(cx+(px-cx)*sc,cy+(py-cy)*sc,5,0,6.283);mctx.fill();mctx.fillStyle="#9fb0bf";mctx.font="500 11px "+getComputedStyle(document.body).getPropertyValue("--mono");mctx.fillText(p.toUpperCase(),cx+(px-cx)*sc+10,cy+(py-cy)*sc+4)}
 N.forEach(n=>{if(!visible(n))return;const sup=n.status==="superseded",a=(match(n)?1:.15)*(sup?.4:1),x=X(n),y=Y(n),r=sup?4:6.5;mctx.globalAlpha=a*e;mctx.fillStyle=sup?"#6f8092":KC[n.kind];
  if(!sup){const g=mctx.createRadialGradient(x,y,0,x,y,r*3);g.addColorStop(0,KC[n.kind]+"66");g.addColorStop(1,"transparent");mctx.fillStyle=g;mctx.beginPath();mctx.arc(x,y,r*3,0,6.283);mctx.fill();mctx.fillStyle=KC[n.kind]}
  mctx.beginPath();if(n.kind==="lesson"){mctx.moveTo(x,y-r);mctx.lineTo(x+r,y);mctx.lineTo(x,y+r);mctx.lineTo(x-r,y);mctx.closePath()}else if(n.kind==="evidence")mctx.rect(x-r*.7,y-r*.7,r*1.4,r*1.4);else mctx.arc(x,y,r,0,6.283);mctx.fill();
  if(MU.sel===n||MU.hover===n){mctx.globalAlpha=e;mctx.strokeStyle="#f4f2ec";mctx.beginPath();mctx.arc(x,y,r+5,0,6.283);mctx.stroke();mctx.fillStyle="#e7ebef";mctx.font="13px sans-serif";mctx.fillText(n.t,x+r+8,y+4)}});
 mctx.globalAlpha=1;$("mcount").textContent=N.filter(visible).length+" nodes";$("msrc").innerHTML=(MU.sources||[]).map(x=>`<span class="srcchip ${x.available?"on":""}" title="${escH(x.note||"")}">${escH(x.label)} · ${x.available?(x.count==null?"?":x.count):"unavailable"}${x.authoritative?" · authoritative":""}</span>`).join("")}
function hit(ev){const r=muc.getBoundingClientRect();const x=ev.clientX-r.left,y=ev.clientY-r.top;return MU.nodes.filter(visible).find(n=>Math.hypot(n.x-x,n.y-y)<14)}
muc.onmousemove=e=>{const n=hit(e)||null;if(n!==MU.hover){MU.hover=n;muc.style.cursor=n?"pointer":"";muDraw()}};
muc.onclick=e=>{const n=hit(e);MU.sel=n||null;const d=$("mud");d.classList.toggle("on",!!n);if(n){const by=MU.nodes.find(x=>x.id===n.by),ft=MU.nodes.find(x=>x.by===n.id);
 const decision=n.meta&&n.meta.decision||"pending";
 const cap=n.source==="orion-accepted"?"canonical memory · context only":n.meta&&n.meta.authority==="context_only"?"context only · not authority":n.status==="candidate"?("CANDIDATE · "+(decision==="promote"?"promoted":decision==="revoke"?"revoked":decision==="reject"?"rejected":decision==="defer"?"deferred":"pending review")):"superseded";
 const meta=n.meta&&n.meta.authority==="context_only"?`<p>Context: canonical=${n.meta.canonical?"yes":"no"}${n.meta.trust?" · trust "+escH(n.meta.trust):""}</p>`:(n.meta?`<p>Decision: ${escH(decision)}${n.meta.confidence!=null?" · confidence "+escH(n.meta.confidence):""}${n.meta.trust?" · trust "+escH(n.meta.trust):""}</p>${n.meta.reason?`<p>Why proposed: ${escH(n.meta.reason)}</p>`:""}${n.meta.decisionEventHash?`<p class="cap">Decision evidence: ${escH(n.meta.decisionEventHash.slice(0,16))}…</p>`:""}`:"");
 const canPropose=n.source==="orion-history"&&n.meta&&n.meta.messageId;
 const canReview=n.source==="orion-candidates"&&n.meta&&(decision==="pending"||decision==="defer");
 const assistantPrior=canReview&&n.meta.sourceRole==="assistant";
 const promotionEligible=canReview&&n.meta.promotionEligible===true;
 const canRevoke=n.source==="orion-candidates"&&n.meta&&decision==="promote";
 const blockReason=n.meta&&n.meta.promotionBlockReason||"";
 const reviewButtons=canReview?`<div class="tl">${promotionEligible?'<button id="muPromote" type="button">PROMOTE</button>':""}<button id="muReject" type="button">REJECT</button><button id="muDefer" type="button">DEFER</button></div><p class="cap">${promotionEligible?"Owner decision only · canonical Memory remains context, never execution authority":assistantPrior?"Assistant prior cannot be promoted in V1 · owner may restate a verified fact":blockReason==="instruction_like"?"Instruction-like owner message cannot be canonical Memory in V1 · restate declaratively":"Not eligible for canonical promotion"}</p>`:"";
 const revokeButton=canRevoke?`<button id="muRevoke" type="button">REVOKE canonical memory</button><p class="cap">Append-only revocation · original promotion evidence remains</p>`:"";
 d.innerHTML=`<span class="cap">${escH(n.kind)} · ${escH(cap)}</span><h3>${escH(n.t)}</h3><p>${escH(n.project)} · ${escH(n.date)}${n.src?" · source: "+escH(n.src):""}</p>${meta}${by?`<p>Replaced by: ${escH(by.t)}</p>`:""}${ft?`<p>Supersedes: ${escH(ft.t)}</p>`:""}${canPropose?`<button id="muPropose" type="button">Propose as memory candidate</button><p class="cap">Queues exact source only · does not promote canonical Memory</p>`:""}${reviewButtons}${revokeButton}`;
 if(canPropose){const b=$("muPropose");b.onclick=async ev=>{b.disabled=true;const r=await B.proposeMemoryCandidate(n,ev);if(r.ok){b.textContent=r.data&&r.data.created===false?"Already queued":"Queued as candidate";const mem=await MemoryAdapters.load(B,MU.q);MU.nodes=mem.nodes;MU.sources=mem.sources;muLayout();muDraw()}else{b.disabled=false;b.textContent="Could not queue · "+escH(r.message||"rejected")}}}
 if(canReview){const defs=[["muReject","reject"],["muDefer","defer"]];if(promotionEligible)defs.unshift(["muPromote","promote"]);for(const [id,dec] of defs){const b=$(id);b.onclick=async ev=>{if(dec==="promote"&&!confirm("Promote this exact owner message to canonical Memory? It remains context only and cannot authorize actions."))return;defs.forEach(([x])=>{const z=$(x);if(z)z.disabled=true});const r=await B.reviewMemoryCandidate(n,dec,ev);if(r.ok){const mem=await MemoryAdapters.load(B,MU.q);MU.nodes=mem.nodes;MU.sources=mem.sources;MU.sel=null;$("mud").classList.remove("on");muLayout();muDraw()}else{defs.forEach(([x])=>{const z=$(x);if(z)z.disabled=false});b.textContent="FAILED · "+escH(r.message||"rejected")}}}}
 if(canRevoke){const b=$("muRevoke");b.onclick=async ev=>{if(!confirm("Revoke this canonical memory? The promotion evidence remains append-only, but the memory becomes inactive."))return;b.disabled=true;const r=await B.reviewMemoryCandidate(n,"revoke",ev);if(r.ok){const mem=await MemoryAdapters.load(B,MU.q);MU.nodes=mem.nodes;MU.sources=mem.sources;MU.sel=null;$("mud").classList.remove("on");muLayout();muDraw()}else{b.disabled=false;b.textContent="FAILED · "+escH(r.message||"rejected")}}}
 muDraw()}};
$("mq").oninput=e=>{MU.q=e.target.value;muDraw()};
$("mq").onkeydown=async e=>{if(e.key!=="Enter")return;MU.q=e.target.value;const mem=await MemoryAdapters.load(B,MU.q);MU.nodes=mem.nodes;MU.sources=mem.sources;MU.sel=null;$("mud").classList.remove("on");muLayout();muDraw()};
$("tgOld").onclick=e=>{MU.old=!MU.old;e.target.classList.toggle("on",MU.old);muDraw()};
addEventListener("resize",()=>{if(S.mem){muLayout();muDraw()}});

