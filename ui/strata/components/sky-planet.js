/* Canvas 2D sky + ORION planet. State names come from state/store.js. Drawing only; no backend access. */
/* ===================== 6. RENDERER (Canvas 2D: sky + ORION planet) ===================== */
const sk=$("sky"),skx=sk.getContext("2d"),cv=$("core"),cx0=cv.getContext("2d");
let tgt="#76cfe4",rgb=[118,207,228],rot=0,ring=0,spread=1,VERTS=[],EDGES=[],stars=[];
const hex=h=>[1,3,5].map(i=>parseInt(h.slice(i,i+2),16));
const fit=(c,x)=>{const d=Math.min(devicePixelRatio||1,PHONE?1:S.low?1.25:2),w=c.clientWidth,h=c.clientHeight;if(c.width!==Math.round(w*d)||c.height!==Math.round(h*d)){c.width=Math.round(w*d);c.height=Math.round(h*d)}x.setTransform(d,0,0,d,0,0);return[w,h]};
function build(){const N=PHONE?96:S.low?150:260;VERTS=[];EDGES=[];for(let i=0;i<N;i++){const y=1-2*(i+.5)/N,r=Math.sqrt(1-y*y),th=i*2.39996;VERTS.push([Math.cos(th)*r,y,Math.sin(th)*r])}
 const th=PHONE||S.low?.93:.945;for(let i=0;i<N;i++)for(let j=i+1;j<N;j++)if(VERTS[i][0]*VERTS[j][0]+VERTS[i][1]*VERTS[j][1]+VERTS[i][2]*VERTS[j][2]>th)EDGES.push([i,j]);
 const n=PHONE?88:S.low?160:320;stars=[];
 for(let g=0;g<7;g++){const gx=.08+Math.random()*.84,gy=.08+Math.random()*.84;for(let k=0;k<5;k++)stars.push({x:gx+(Math.random()-.5)*.1,y:gy+(Math.random()-.5)*.12,r:1+Math.random()*.9,ph:Math.random()*6,sp:.5+Math.random(),v:0,g})}
 while(stars.length<n)stars.push({x:Math.random(),y:Math.random(),r:Math.random()<.05?1.6:.3+Math.random()*.9,ph:Math.random()*6,sp:.4+Math.random()*1.2,v:.2+Math.random()*.8,g:-1});wake()}
function sky(t,col){const [w,h]=fit(sk,skx);skx.clearRect(0,0,w,h);const cx=w/2,cy=h*.46,z=S.camZ,P=stars.map(s=>{const x=((s.x*w+(RM?0:t*s.v*3))%w);return[cx+(x-cx)*z,cy+(s.y*h-cy)*z,s]});
 skx.lineWidth=.6;skx.strokeStyle="rgba(201,238,245,.09)";for(let i=0;i<35;i++){if(i%5&&P[i][2].g===P[i-1][2].g){skx.beginPath();skx.moveTo(P[i-1][0],P[i-1][1]);skx.lineTo(P[i][0],P[i][1]);skx.stroke()}}
 for(const [x,y,s] of P){if(x<-4||y<-4||x>w+4||y>h+4)continue;const tw=RM?.8:.55+.45*Math.sin(t*s.sp+s.ph);skx.fillStyle=s.r>1.4?`rgba(${col},${.5+.4*tw})`:`rgba(231,235,239,${.2+.5*tw})`;skx.beginPath();skx.arc(x,y,s.r*Math.min(z,2),0,6.283);skx.fill()}}
function planet(t,col){const [w,h]=fit(cv,cx0),c=cx0;c.clearRect(0,0,w,h);const st=S.state,cx=w/2,cy=h/2,R=w*.34*(1+(RM?0:Math.sin(t*1.05)*.012)),
 sharp=(["preparing","acting","verifying","completed","pass"].includes(st)||HALT.includes(st)),RX=R*1.42,RY=R*.34,RA=-.38;
 const target=st==="verifying"||(st==="completed"||st==="pass")?1:0;ring+=(target-ring)*(st==="verifying"?.015:.06);
 const arc=front=>{const prog=st==="verifying"||(st==="completed"||st==="pass")?ring:HALT.includes(st)?.88:0;for(let k=0;k<100;k++){const a0=-1.5708+k/100*6.283,a1=a0+.0628;if((Math.sin(a0+.031)>0)!==front)continue;const dn=k/100<prog;
  if(DIM.includes(st)){if(k%4>1)continue;c.strokeStyle="rgba(111,128,146,.45)"}else c.strokeStyle=dn?((st==="completed"||st==="pass")?"rgba(231,235,239,.9)":`rgba(${col},.95)`):"rgba(231,235,239,.12)";c.lineWidth=dn?1.3:1;c.beginPath();c.ellipse(cx,cy,RX,RY,RA,a0,a1+.01);c.stroke()}};
 let g=c.createRadialGradient(cx,cy,R*.95,cx,cy,w*.5);g.addColorStop(0,`rgba(${col},${sharp?.15:.25})`);g.addColorStop(.4,`rgba(${col},.05)`);g.addColorStop(1,`rgba(${col},0)`);c.fillStyle=g;c.beginPath();c.arc(cx,cy,w*.5,0,6.283);c.fill();
 arc(false);
 g=c.createRadialGradient(cx-R*.38,cy-R*.42,R*.05,cx+R*.08,cy+R*.06,R*1.08);g.addColorStop(0,`rgba(${col},.4)`);g.addColorStop(.35,"#10202f");g.addColorStop(.75,"#09111b");g.addColorStop(1,"#04060a");c.fillStyle=g;c.beginPath();c.arc(cx,cy,R,0,6.283);c.fill();
 g=c.createRadialGradient(cx,cy,R*.9,cx,cy,R*1.06);g.addColorStop(0,`rgba(${col},0)`);g.addColorStop(.7,`rgba(${col},${sharp?.18:.32})`);g.addColorStop(1,`rgba(${col},0)`);c.fillStyle=g;c.beginPath();c.arc(cx,cy,R*1.06,0,6.283);c.fill();
 const cr=Math.cos(rot),sr=Math.sin(rot),ct=.9107,stt=.4121,k=spread;
 const P=VERTS.map(([x,y,z])=>{const x1=x*cr+z*sr,z1=-x*sr+z*cr;return[cx+x1*R*k,cy+(y*ct-z1*stt)*R*k,y*stt+z1*ct]});
 c.lineWidth=.6;EDGES.forEach(([i,j],n)=>{const z=Math.min(P[i][2],P[j][2]);if(z<-.05)return;let al=(.08+z*.34)*(sharp?1.1:.7);if(st==="thinking"&&!RM)al*=1+.9*Math.max(0,Math.sin(t*1.6-n*.07));c.strokeStyle=`rgba(${col},${al})`;c.beginPath();c.moveTo(P[i][0],P[i][1]);c.lineTo(P[j][0],P[j][1]);c.stroke()});
 P.forEach(([x,y,z],i)=>{if(z<-.05)return;const fl=st==="memory"&&Math.sin(t*1.3+i)>.93;c.fillStyle=`rgba(${col},${(.25+.55*z)*(sharp?.7:1)+(fl?.4:0)})`;c.beginPath();c.arc(x,y,fl?2.8:1+z*.9,0,6.283);c.fill()});
 const AP=[[-.34,-.26],[0,0],[.34,.26]].map(([a,b])=>[cx+a*R*1.7,cy+b*R*1.7]);
 if(st==="memory"){c.strokeStyle=`rgba(${col},.55)`;c.setLineDash([2,4]);c.beginPath();c.moveTo(...AP[0]);c.lineTo(...AP[1]);c.stroke();c.setLineDash([])}
 if(st==="preparing"||st==="acting"){c.strokeStyle=`rgba(${col},.75)`;c.beginPath();c.moveTo(...AP[0]);c.lineTo(...AP[2]);c.stroke()}
 AP.forEach(([x,y],i)=>{let l=.4;if(["understanding","thinking","clarify","listening"].includes(st))l=i===0?.6+.4*Math.sin(t*2):.3;if(st==="memory")l=i===1?1:i===0?.7:.3;if(st==="preparing")l=i===1?.3:.8;if(st==="acting")l=i===2?1:.35;if((st==="completed"||st==="pass")||st==="verifying")l=.95;if(DIM.includes(st)||(HALT.includes(st)&&st!=="permission"))l=.12;
  const gg=c.createRadialGradient(x,y,0,x,y,R*.1);gg.addColorStop(0,`rgba(${col},${l})`);gg.addColorStop(1,`rgba(${col},0)`);c.fillStyle=gg;c.beginPath();c.arc(x,y,R*.1,0,6.283);c.fill();c.fillStyle=`rgba(231,235,239,${.4+l*.6})`;c.beginPath();c.arc(x,y,2.8,0,6.283);c.fill()});
 if(st==="specialist"){const x=cx+R*1.3,y=cy-R*1.15;c.strokeStyle=`rgba(${col},.6)`;c.beginPath();c.moveTo(...AP[0]);c.lineTo(x,y);c.stroke();c.fillStyle=`rgba(${col},1)`;c.beginPath();c.arc(x,y,3.4,0,6.283);c.fill()}
 if(S.voice!=="off"){c.strokeStyle=`rgba(${col},.8)`;c.lineWidth=1.4;c.beginPath();for(let i=0;i<=72;i++){const a=i/72*6.283,r=R*1.12+Math.sin(a*7+t*6)*R*.045*S.level+Math.sin(a*3-t*3)*R*.02*S.level;i?c.lineTo(cx+Math.cos(a)*r,cy+Math.sin(a)*r):c.moveTo(cx+Math.cos(a)*r,cy+Math.sin(a)*r)}c.closePath();c.stroke()}
 arc(true);
 if(st==="acting"&&!RM){const a=-1.5708+t*1.4,ex=Math.cos(a)*RX,ey=Math.sin(a)*RY;c.fillStyle=`rgba(${col},1)`;c.beginPath();c.arc(cx+ex*Math.cos(RA)-ey*Math.sin(RA),cy+ex*Math.sin(RA)+ey*Math.cos(RA),3,0,6.283);c.fill()}}
let last=0,raf=0;
function loop(now){if(document.hidden){raf=0;return}raf=requestAnimationFrame(loop);
 const idle=(["idle","completed","pass","stopped","failed","error","blocked","verif_failed"].includes(S.state))&&S.voice==="off"&&!S.mem;const cap=S.orb?250:RM?400:PHONE?(S.low?100:50):S.low?66:idle?50:16;if(now-last<cap)return;const dt=Math.min((now-last)/1000,.1);last=now;
 const a=hex(tgt);rgb=rgb.map((v,i)=>v+(a[i]-v)*.06);const col=rgb.map(v=>v|0).join(",");
 S.camZ+=((S.mem?3.2:1)-S.camZ)*.04;spread+=((DIM.includes(S.state)?1.05:1)-spread)*.04;
 if(!RM&&!(["acting","completed","pass"].includes(S.state)||HALT.includes(S.state)))rot+=dt*(S.state==="thinking"?.2:DIM.includes(S.state)?.01:.09);
 const t=now/1000;sky(t,col);planet(t,col)}
function wake(){last=0;if(!raf&&!document.hidden)raf=requestAnimationFrame(loop)}
document.addEventListener("visibilitychange",wake);

