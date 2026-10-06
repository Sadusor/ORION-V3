/* ======================================================================
   normalize.js — COMPATIBILITY LAYER: raw ORION JSON  ->  canonical backend slice (see STATE_CONTRACT.md).
   Raw backend names are VERIFIED against spikes/coding_mode_github_loop/server.py (Controller.view()).
   Anything not verified is tagged  // INFERRED.  Nothing outside this file reads raw backend JSON.
   Vocabulary mapping (backend -> canonical):
     run_state  running|passed|failed|stopped|error|idle   ->  executionState running|completed|stopped|error|idle
     result     PASS|FAIL|ERROR|STOPPED                    ->  verdict       PASS|FAILED|ERROR|null   (stopped has NO verdict)
   Execution state and verdict are DIFFERENT facts: a run can be 'completed' with verdict 'FAILED'.
   ====================================================================== */
const SCHEMA='strata.ui-state/1';
const str=v=>typeof v==='string'?v:(v==null?'':String(v));
const arr=v=>Array.isArray(v)?v:[];
const num=v=>typeof v==='number'&&isFinite(v)?v:null;
const EXEC={running:'running',passed:'completed',failed:'completed',stopped:'stopped',error:'error',idle:'idle'};
const VERDICT={PASS:'PASS',FAIL:'FAILED',ERROR:'ERROR'};
const excerpt=(t,n)=>{t=str(t).trim();if(t.length<=n)return t;return '…'+t.slice(-n).replace(/^\S*\s/,'')};

/* One execution lane: raw.local_hand_lane (Local Brain -> Hands) or raw.manual_lane (Manual / External AI). */
function normLane(l){l=l&&typeof l==='object'?l:{};const run=str(l.run_state)||'idle',res=str(l.result);
 return{runState:run,executionState:EXEC[run]||'unknown',result:res,verdict:VERDICT[res]||null,output:str(l.output),error:str(l.error),activity:str(l.activity),
 evidencePath:str(l.evidence_path),startedUtc:str(l.started_utc),finishedUtc:str(l.finished_utc),exitCode:num(l.exit_code),pid:num(l.pid),
 goal:str(l.goal),brainState:str(l.brain_state)||'idle',brainPhase:str(l.brain_phase)||'idle',brainStartedUtc:str(l.brain_started_utc),
 preview:str(l.brain_stream_preview),model:str(l.brain_model),conclusion:str(l.brain_conclusion),brainError:str(l.brain_error),
 nextScript:str(l.brain_next_script),nextCapability:str(l.brain_next_capability),nextArtifactPath:str(l.brain_next_artifact_path),nextUrl:str(l.brain_next_url),nextBrowser:str(l.brain_next_browser),
 preflight:str(l.brain_preflight),preflightReason:str(l.brain_preflight_reason),
 qualityState:str(l.brain_quality_state),qualityReason:str(l.brain_quality_reason),            // not-run|running|pass|blocked|error
 qualityUnsupported:arr(l.brain_quality_unsupported_claims),qualityMissing:arr(l.brain_quality_missing_evidence),approvedSha256:str(l.brain_quality_approved_sha256),
 needsEscalation:!!l.brain_needs_escalation,revision:num(l.brain_revision)||0,latency:num(l.brain_latency_seconds),
 execKind:str(l.execution_kind),execAction:str(l.execution_action),execLink:str(l.execution_target_project_link),
 execRepo:str(l.execution_target_repo),execBranch:str(l.execution_target_branch),execScope:str(l.execution_target_scope),
 publishState:str(l.publish_state),publishError:str(l.publish_error),
 memory:l.brain_memory&&typeof l.brain_memory==='object'?l.brain_memory:{state:'idle',authority:'context_only',count:0,items:[],trace:{}},
 capOutput:str(l.execution_kind)==='capability'?parseCapOutput(l.output):{}}}

/* reviewer = raw.reviewer. Shape verified from Remote V1's own rendering code; reviewer_connector.py was not available. */
function normReviewer(rev){rev=rev&&typeof rev==='object'?rev:{};
 const models=arr(rev.catalog&&rev.catalog.models).map(m=>({id:str(m.reviewer_id),provider:str(m.provider_label||m.provider),adapter:str(m.provider),model:str(m.model),available:!!m.available}));
 const items=Object.entries(rev.reviewers&&typeof rev.reviewers==='object'?rev.reviewers:{}).map(([id,it])=>{it=it&&typeof it==='object'?it:{};
  const state=str(it.state)||'idle',err=str(it.error),out=str(it.output);
  const phase=err||/fail|error/i.test(state)?'failed':/run|stream|start|pending|queue/i.test(state)?'running':out?'done':'idle';                       // INFERRED state vocabulary
  return{id,provider:str(it.provider_label||it.provider),model:str(it.model)||id,state,phase,error:err,output:out,excerpt:excerpt(out,320),
   usage:{total:num(it.run_usage&&it.run_usage.total_tokens)}}});
 const run=str(rev.state)||'idle',anyRun=items.some(i=>i.phase==='running')||/^(running|starting|streaming|active)/i.test(run);
 const failed=items.filter(i=>i.phase==='failed').length,done=items.filter(i=>i.phase==='done').length;
 const status=anyRun?'running':!items.length?'idle':failed&&done?'partial':failed?'failed':'complete';
 return{state:run,runId:str(rev.run_id),evidencePath:str(rev.evidence_path),models,ollama:arrOllama(rev),items,status,failed,done,inboxStatus:str(rev.inbox&&rev.inbox.status)}}
const arrOllama=rev=>arr(rev.catalog&&rev.catalog.models).filter(x=>x.provider==='ollama'&&x.available).map(x=>x.model);

/* Contract check for GET /api/status (and every POST that returns Controller.view()). A body that fails this is a BACKEND ERROR, never "idle". */
function validateStatus(raw){const p=[];
 if(!raw||typeof raw!=='object'||Array.isArray(raw))return{ok:false,problems:['body is not a JSON object']};
 if(typeof raw.run_state!=='string')p.push('run_state missing');
 if(!raw.local_hand_lane||typeof raw.local_hand_lane!=='object')p.push('local_hand_lane missing');
 return{ok:!p.length,problems:p}}
const looksLikeView=d=>validateStatus(d).ok;

function normalizeStatus(raw){const v=validateStatus(raw);if(!v.ok)throw new Error('Unexpected status payload: '+v.problems.join(', '));
 const links=arr(raw.project_links),activeId=str(raw.active_project_link_id),us=raw.update_status&&typeof raw.update_status==='object'?raw.update_status:{};
 const rev=normReviewer(raw.reviewer);
 return{raw,
  gh:{mode:str(raw.mode)||'normal',runState:str(raw.run_state)||'idle',executionState:EXEC[str(raw.run_state)]||'unknown',pendingSha:str(raw.pending_sha),approvedSha:str(raw.approved_sha),
   lastTestedSha:str(raw.last_tested_sha),checkoutSha:str(raw.checkout_sha),lastResult:str(raw.last_result),verdict:VERDICT[str(raw.last_result)]||null,lastOutput:str(raw.last_output),lastError:str(raw.last_error),
   runnerLog:str(raw.runner_log),evidencePath:str(raw.evidence_path),runnerSha:str(raw.runner_sha),runnerCwd:str(raw.runner_cwd),runnerPid:num(raw.runner_pid),runnerExit:num(raw.runner_exit_code),
   runnerStartedUtc:str(raw.runner_started_utc),runnerFinishedUtc:str(raw.runner_finished_utc),activity:str(raw.activity),repo:str(raw.repo),branch:str(raw.branch),testCommand:str(raw.test_command),
   publishState:str(raw.publish_state),publishedCommit:str(raw.published_commit),attempt:num(raw.attempt)||0,
   update:{phase:str(us.phase),detail:str(us.detail),error:str(us.error),targetSha:str(us.target_sha)}},
  project:{activeId,links,active:links.find(x=>x.link_id===activeId)||null},
  local:normLane(raw.local_hand_lane),manual:normLane(raw.manual_lane),
  sessions:arr(raw.dispatch_sessions),tasks:arr(raw.dispatch_tasks),
  reviewer:rev,
  providers:arr(raw.provider_vault&&raw.provider_vault.providers).map(p=>({id:str(p.provider_id),label:str(p.label||p.provider_id),adapter:str(p.adapter),enabled:!!p.enabled,freeConfigured:!!p.configured_free,hint:str(p.secret_hint)})),
  defaultModel:str(raw.local_brain_default_model),
  repo:{branch:str(raw.branch),sha:{pending:str(raw.pending_sha),approved:str(raw.approved_sha),lastTested:str(raw.last_tested_sha),checkout:str(raw.checkout_sha),runner:str(raw.runner_sha)},
   dirty:null /* not exposed by /api/status: reported as "not reported", never guessed */,cwd:str(raw.runner_cwd)}}}

/* GET /api/memory/candidates -> {candidates:[...]}. Memory CANDIDATES (decision defaults to "defer"), never promoted Memory. */
function normalizeCandidates(d){return arr(d&&d.candidates).map((c,i)=>({
 id:str(c.candidate_id)||'c'+i,t:str(c.content)||'(empty candidate)',kind:'candidate',status:'candidate',source:'orion-candidates',
 project:str(c.classification)||'UNCLASSIFIED',date:str(c.submitted_at),src:[str(c.source_actor),str(c.source_ref)].filter(Boolean).join(' · '),
 meta:{trust:str(c.trust_origin),confidence:c.confidence,decision:str(c.decision)||'defer',decisionReason:str(c.decision_reason),reason:str(c.reason_for_candidate),task:str(c.task_id)}}))}

/* GET /api/memory/search -> read-only retrieval results. Conversation recall is CONTEXT, never canonical authority. */
function normalizeMemoryRecall(d){return arr(d&&d.items).map((m,i)=>{
 const p=m&&m.provenance&&typeof m.provenance==='object'?m.provenance:{},ts=num(p.created_at_ms);
 return{
  id:str(m&&m.id)||'memory-recall-'+i,
  t:str(m&&m.preview)||str(m&&m.content)||'(empty recall)',
  kind:'evidence',
  status:'current',
  source:'orion-history',
  project:str(p.project_id)||'personal',
  date:ts?new Date(ts).toISOString():'',
  src:[str(p.message_source),str(p.conversation_id),str(p.message_id)].filter(Boolean).join(' · '),
  meta:{authority:'context_only',trust:str(m&&m.trust_tier)||str(p.trust_tier)||'unverified',score:num(m&&m.score),layer:str(m&&m.layer)||'message',role:str(p.role),title:str(m&&m.title),riskFlags:arr(m&&m.risk_flags),contextEligible:m&&m.context_eligible!==false}
 }})}

/* open_web_url etc. write JSON into lane.output. Returns {} when it is not JSON. */
function parseCapOutput(text){try{const v=JSON.parse(text);return v&&typeof v==='object'&&!Array.isArray(v)?v:{}}catch(e){return{}}}
