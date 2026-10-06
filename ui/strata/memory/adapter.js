/* ======================================================================
   adapter.js — MEMORY ADAPTER LAYER. The Memory Universe never talks to a memory implementation directly: it consumes the
   normalized model produced here:   {nodes:[{id,t,kind,status,source,project,date,src,meta}], sources:[{id,label,available,authoritative,count,note}]}
   kinds: candidate | accepted | project | task | evidence   status: candidate | current | superseded
   To plug in a new memory system, register one adapter (id,label,authoritative, load(bridge)->nodes). The visual layer is untouched.
   Today ORION exposes only Memory CANDIDATES; every other source is listed as unavailable so nothing is implied.
   ====================================================================== */
const MemoryAdapters=(function(){
 const reg=[];
 function register(a){reg.push(a)}
 async function load(bridge,query){const nodes=[],sources=[];
  for(const a of reg){
   const info={id:a.id,label:a.label,authoritative:!!a.authoritative,available:a.available!==false,count:null,note:a.note||''};
   if(info.available&&typeof a.load==='function'){try{const n=await a.load(bridge,query||'');info.count=n.length;nodes.push(...n)}catch(e){info.available=false;info.note='Failed to load: '+(e&&e.message)}}
   sources.push(info)}
  return{nodes,sources}}
 register({id:'orion-candidates',label:'Memory candidates (proposals)',authoritative:false,load:b=>b.getMemoryCandidates?b.getMemoryCandidates():[]});
 register({id:'orion-accepted',label:'Canonical memory (context only)',authoritative:true,load:b=>b.getCanonicalMemory?b.getCanonicalMemory():[],note:'Owner-promoted durable context. Canonical does not grant execution authority.'});
 register({id:'orion-project',label:'Project memory',authoritative:true,available:false,note:'Not exposed by the ORION backend yet'});
 register({id:'orion-history',label:'Conversation recall (context only)',authoritative:false,load:(b,q)=>b.getMemoryRecall?b.getMemoryRecall(q):[],note:'Read-only chat-history retrieval with provenance; never canonical authority'});
 return{register,load,describe:()=>reg.map(a=>({id:a.id,label:a.label,available:a.available!==false,authoritative:!!a.authoritative}))}})();
