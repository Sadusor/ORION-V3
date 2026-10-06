/* Compatibility layer: raw ORION JSON -> canonical backend slice. Includes malformed input. */
const H=require('../harness');const {ok,eq,done,run,lane,view,NOW}=H;const c=H.coreCtx();c.__v=view;c.__lane=lane;
console.log('normalize');
const N=(o)=>{c.__o=o;return run(c,'normalizeStatus(__o)')};
let m=N(view({run_state:'failed',result:'FAIL',started_utc:NOW,finished_utc:NOW,execution_kind:'powershell',exit_code:1}));
eq([m.local.executionState,m.local.verdict],['completed','FAILED'],'run_state failed + result FAIL => execution completed, verdict FAILED (two separate facts)');
m=N(view({run_state:'passed',result:'PASS',execution_kind:'capability',execution_action:'open_web_url',output:JSON.stringify({status:'launch_requested',pid:7})}));
eq([m.local.executionState,m.local.verdict,m.local.capOutput.status,m.local.capOutput.pid],['completed','PASS','launch_requested',7],'capability PASS + parsed capability output');
m=N(view({run_state:'stopped',result:'STOPPED'}));eq([m.local.executionState,m.local.verdict],['stopped',null],'STOPPED has NO verdict');
m=N(view({run_state:'error',result:'ERROR'}));eq([m.local.executionState,m.local.verdict],['error','ERROR'],'ERROR');
m=N(view({run_state:'running'}));eq(m.local.executionState,'running','running');
ok(N(view({run_state:'idle',execution_kind:'capability',output:'not json'})).local.capOutput&&Object.keys(N(view({execution_kind:'capability',output:'not json'})).local.capOutput).length===0,'non-JSON capability output => {} (no crash)');
m=N(view({brain_state:'ready',brain_quality_state:'pass',brain_next_script:'Get-Date',brain_quality_approved_sha256:'ab'.repeat(32)}));
eq([m.local.brainState,m.local.qualityState,m.local.nextScript,m.local.approvedSha256.length],['ready','pass','Get-Date',64],'Local Brain fields mapped from local_hand_lane');
eq([m.repo.dirty,m.gh.repo,m.gh.branch],[null,'Sadusor/Orion','agent/x'],'repo dirty state is null ("not reported"), never guessed');
m=N(view({},{pending_sha:'3154607',mode:'active',last_result:'PASS',run_state:'passed',runner_exit_code:0,runner_cwd:'C:/w'}));
eq([m.gh.pendingSha,m.gh.verdict,m.gh.executionState,m.gh.runnerExit,m.gh.runnerCwd],['3154607','PASS','completed',0,'C:/w'],'GitHub fields from real root names');
m=N(view({},{dispatch_sessions:[{session_id:'s1',state:'running'}],dispatch_tasks:[{task_id:'t'}],project_links:[{link_id:'L',github_repo:'a/b',branch:'x',state:'ready',scope:'.'}],active_project_link_id:'L'}));
eq([m.sessions.length,m.tasks.length,m.project.active&&m.project.active.link_id],[1,1,'L'],'dispatch_sessions / dispatch_tasks / project links');
/* reviewers */
const rv=(items,state)=>N(view({},{reviewer:{state:state||'complete',run_id:'r',catalog:{models:[]},reviewers:items}})).reviewer;
let r=rv({a:{model:'m',provider_label:'P',state:'complete',output:'x\n\nConclusion: ship it.'},b:{model:'n',provider_label:'Q',state:'failed',error:'rate limit'}});
eq([r.status,r.failed,r.done],['partial',1,1],'one answered + one failed => PARTIAL result');
ok(/Conclusion: ship it/.test(r.items[0].excerpt)&&r.items[1].error==='rate limit','closing excerpt is verbatim; error preserved');
eq(rv({a:{state:'failed',error:'e'}}).status,'failed','all failed => failed');eq(rv({a:{state:'complete',output:'ok'}}).status,'complete','all answered => complete');
eq(rv({a:{state:'running',output:'..'}},'running').status,'running','running');eq(rv({}).status,'idle','no items => idle');
ok(N(view({},{reviewer:{state:'idle',reviewers:{a:{state:'complete',output:'x'.repeat(2000)}}}})).reviewer.items[0].excerpt.length<=330,'excerpt is bounded');
/* providers */
m=N(view({},{provider_vault:{providers:[{provider_id:'p',label:'P',adapter:'x',enabled:true,secret_hint:'••1'}]}}));eq([m.providers[0].id,m.providers[0].enabled,m.providers[0].hint],['p',true,'••1'],'providers normalized');
/* malformed bodies must throw (never become a fake idle) */
for(const [n,bad] of [['null',null],['string','<html>'],['array',[]],['empty object',{}],['missing lane',{run_state:'idle'}],['lane not object',{run_state:'idle',local_hand_lane:'x'}],['number',5]]){
 c.__bad=bad;let threw=false;try{run(c,'normalizeStatus(__bad)')}catch(e){threw=true}ok(threw,'malformed status ('+n+') is rejected, not turned into idle');
 ok(run(c,'validateStatus(__bad).ok')===false,'validateStatus('+n+') = not ok')}
ok(run(c,'validateStatus(__v()).ok')===true,'validateStatus accepts a real-shaped view');
/* memory candidates (real field names) */
c.__cand={candidates:[{candidate_id:'c1',content:'<b>x</b>',classification:'WORKFLOW',confidence:.7,submitted_at:NOW,source_actor:'a',source_ref:'r',decision:'defer',reason_for_candidate:'why'}]};
const cand=run(c,'normalizeCandidates(__cand)');eq([cand[0].id,cand[0].kind,cand[0].status,cand[0].project,cand[0].meta.decision,cand[0].t],['c1','candidate','candidate','personal','defer','<b>x</b>'],'legacy-shaped memory candidate => labelled candidate, explicit default scope, text kept raw (escaped at render)');
c.__bc={nope:1};eq(run(c,'normalizeCandidates(__bc)'),[],'malformed candidates => empty');
c.__cm={memories:[{memory_id:'cm1',candidate_id:'c1',content:'GREEN 842',project_id:'',created_at_ms:1234,trust_tier:'owner_message_unverified',authority:'context_only',content_sha256:'f'.repeat(64),promoted_decision_id:'d1',promoted_event_hash:'e'.repeat(64)}]};
const cm=run(c,'normalizeCanonicalMemory(__cm)');eq([cm[0].id,cm[0].kind,cm[0].status,cm[0].source,cm[0].project,cm[0].meta.canonical,cm[0].meta.authority],['cm1','fact','current','orion-accepted','personal',true,'context_only'],'canonical memory => current fact-shaped context, never execution authority');
done('normalize');
