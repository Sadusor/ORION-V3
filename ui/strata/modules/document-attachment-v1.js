/* Separate document attachment control; preserves the existing composer and chat. */
(function(){
  function setup(){
    const bar=document.getElementById('bar'),send=document.getElementById('send');
    if(!bar||!send)return;
    const btn=document.createElement('button');
    btn.type='button';btn.className='rb';btn.textContent='📎';
    btn.title='Index a text document for ORION chat';btn.setAttribute('aria-label','Index a document');
    const picker=document.createElement('input');
    picker.type='file';picker.accept='.txt,.md,.csv,.json,.log';picker.hidden=true;
    bar.insertBefore(btn,send);bar.appendChild(picker);
    const status=document.createElement('span');
    status.setAttribute('role','status');status.style.cssText='font-size:11px;max-width:180px;white-space:normal';
    status.hidden=true;bar.insertBefore(status,send);
    btn.addEventListener('click',()=>picker.click());
    picker.addEventListener('change',async()=>{
      const file=picker.files&&picker.files[0];
      picker.value='';if(!file)return;
      status.hidden=false;status.textContent='Indexing '+file.name+'…';
      if(file.size===0||file.size>2000000){
        status.textContent='Only non-empty text files up to 2 MB';return;
      }
      btn.disabled=true;
      try{
        const bytes=new Uint8Array(await file.arrayBuffer());
        let encoded='';
        for(let i=0;i<bytes.length;i+=0x8000){
          encoded+=String.fromCharCode(...bytes.subarray(i,i+0x8000));
        }
        const token=localStorage.getItem('orionToken')||'';
        const reply=await fetch('/api/documents/index',{
          method:'POST',headers:{'Content-Type':'application/json','X-Orion-Token':token},
          body:JSON.stringify({project_id:'orion-v3',filename:file.name,data_base64:btoa(encoded)})
        });
        const result=await reply.json();
        if(!reply.ok||!result.ok)throw Error(result.error||'Index failed');
        status.textContent='Indexed '+file.name+' · ask ORION about it';
      }catch(err){status.textContent='Document import failed: '+(err.message||'unknown error');}
      finally{btn.disabled=false;}
    });
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup);
  else setup();
})();
