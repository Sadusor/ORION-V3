/* Desktop PC updater UI: thin wrapper around existing authenticated ORION updater.
   The backend owns the guarded update, build, restart and rollback process. */
(function(){
'use strict';
const bridge=window.ORION_BRIDGE,top=document.getElementById('top'),app=document.getElementById('app');
if(!bridge||typeof bridge.call!=='function'||!top||!app)return;
const actions=top.querySelector('.tl:last-child');if(!actions)return;
const button=document.createElement('button');
button.type='button';button.className='ib';button.id='orion-desktop-update-v1';
button.textContent='Update PC';button.title='Check and update ORION PC through the existing safe updater';
button.setAttribute('aria-label','Check for and install ORION PC update');
actions.insertBefore(button,actions.firstChild);
let working=false;
function show(msg){const notice=document.getElementById('toast');if(notice){notice.textContent=msg;notice.classList.add('on')}else window.alert?.(msg)}
button.addEventListener('click',async()=>{
 if(working)return;working=true;button.disabled=true;
 try{
  button.textContent='Checking…';
  const check=await bridge.call('GET','/api/update/check',null,{silent:true});
  if(!check.ok){show('Update check failed: '+(check.message||'connection error'));return}
  const c=check.data||{};
  if(!c.can_update){show(c.reason||'PC update unavailable.');return}
  if(!(Number(c.behind)>0)){show('ORION source is current. No update required.');return}
  const target=String(c.remote||'').slice(0,12);
  const yes=window.confirm('Update ORION PC to '+target+'? The app may restart, briefly disconnect, and run safety tests. Continue?');
  if(!yes)return;
  button.textContent='Updating…';
  const result=await bridge.call('POST','/api/update/main',{}, {label:'Update ORION PC'});
  if(!result.ok){show('Update not started: '+(result.message||'ORION refused'));return}
  show(result.data?.update?.restart_scheduled?'PC update scheduled. ORION may reconnect after testing.':'ORION PC is already current.');
 }catch(e){show('PC update failed: '+(e?.message||'unknown error'))}
 finally{working=false;button.disabled=false;button.textContent='Update PC'}
});
})();