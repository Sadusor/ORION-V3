# V3 UI state contract (`schema: "strata.ui-state/1"`)
`buildUiState(V)` (state/store.js) returns this object. **Components read only this**, never raw backend JSON. It is pure: same input ⇒ same output.
`✔ backend` = comes from ORION; `▫ client` = known only to the browser; `∅` = ORION does not report it, so it is `null`/`"not_reported"`.

| Key | Shape | Source |
|---|---|---|
| `schema` | `"strata.ui-state/1"` | contract |
| `source` | `{mode:'live'|'mock', bridge:'real'|'mock', transport}` | ▫ |
| `connection` | `{status:'live'|'stale'|'reconnecting'|'connecting'|'offline'|'unpaired'|'backend_error', lastOkAt, ageMs, latencyMs, failures, endpoint, transport, paired, error}` | ▫ measured |
| `stale` | `boolean` (connection ≠ live; last data is dimmed) | ▫ |
| `orion` | `{state, label, detail, activity, color}` — state ∈ `idle thinking verifying preparing acting specialist permission pass completed failed error stopped blocked verif_failed` or link states `reconnecting stale offline backend_error` (`listening understanding memory clarify` exist but are **never derived**) | ✔ derived |
| `project` | `{label, activeLinkId, linkState, scope, links[]}` | ✔ `project_links`, `active_project_link_id` |
| `repo` | `{repo, branch, sha:{pending,approved,lastTested,checkout,runner}, dirty:'not_reported', cwd}` | ✔ (`dirty` ∅) |
| `localBrain` | `{state, phase, model, goal, conclusion, preflight:{state,reason}, quality:{state,reason,unsupported[],missing[]}, next:{kind:'capability'|'powershell'|'none',capability,url,browser}, error, startedAt, revision, defaultModel, livePreview}` | ✔ `local_hand_lane.brain_*` |
| `task` | `{kind, label, startedAt}` or `null` | ✔ |
| `timeline` | `[{id,label,status:'done'|'active'|'pending'|'failed',basis}]` draft · verify · preflight · approval/authorization · hand · verdict — each step names the backend field it comes from | ✔ derived |
| `approval` | `null` or `{sig, kind:'powershell', title, hand, target:{project,repo,branch,cwd}, why, summary, checks:{preflight,quality,approvedHash}, risk, script, model, dismissedLocally}` | ✔ (`dismissedLocally` ▫) |
| `action` | `null` or `{hand, label, executionState:'running', stoppable, note}` — the running Hand/action | ✔ |
| `lastResult` | `null` or `{source, hand, executionState:'running|completed|stopped|error', verdict:'PASS|FAILED|BLOCKED|ERROR'|null, headline, body, rows[], ladder[], evidence[], note, startedAt, finishedAt, fingerprint}` | ✔ |
| `lastResult.ladder` | `[{id,label,status:'established'|'not_established'|'not_reported'|'failed'|'pending',basis}]` — request/acceptance/launch/process/**detected/loaded/verified** for web launches; authorized/started/exited/output/verdict/effects for PowerShell; authorized/exact-SHA/exit/verdict/published for GitHub runs | ✔ |
| `blocked` | `null` or `{kind:'preflight'|'quality'|'quality_error'|'other', reason, preflight, quality, unsupported[], missing[], canRevise, goal}` | ✔ |
| `errorCard` | `null` or `{reason, phase}` (Local Brain error/interrupted) | ✔ |
| `github` | `{mode, executionState, verdict, pendingSha, approvedSha, lastTestedSha, checkoutSha, repo, branch, testCommand, update:{phase,detail,error,targetSha}, publishState, evidencePath, activity}` | ✔ |
| `sessions` | `{tasks[], sessions[]}` (`dispatch_tasks`, `dispatch_sessions`) | ✔ |
| `reviewers` | `{status:'idle|running|complete|partial|failed', items:[{id,provider,model,state,phase:'idle|running|done|failed',error,output,excerpt,usage}], models:{total,available}, runId, visible}` — `excerpt` is the **verbatim closing text**, not a summary; agreement is not computed | ✔ (`phase` classification INFERRED) |
| `providers` | `{status:'none|ready|unavailable', items:[{id,label,adapter,enabled,freeConfigured,hint}]}` | ✔ |
| `memory` | `{candidates:null}` — memory sources are described by `MemoryAdapters` (only *candidates* exist) | ✔ |
| `pcView` | `{state:'not_configured', controlAuthorized:false, note}` — viewing never authorizes control | ▫ planned |
| `client` | `{kind:'phone'|'pc', paired, transport}` | ▫ |
| `hands`, `runtime` | Local Hands/manual execution + verdict; runner pid/cwd/sha, update status, default model, local models | ✔ |
| `lanes` | `[{id,label,kind,state,detail,model,reasoningMode}]` — first-class Personal / Project / Specialists / Background lanes. Reasoning mode remains `not_reported` until the backend owns that fact. | ✔ derived from reported lane facts |
| `stops` | `[{id,label,route,body}]` every currently stoppable thing (each stop is targeted) | ✔ |
| `errors` / `warnings` | `[{code,message,severity:'error'|'warn'|'info'}]` — codes: `connection_*`, `action_*`, `reviewer_failure`, `reviewer_partial`, `providers_*`, `coding_mode`, `update_error`, `repo_dirty` | mixed |
| `authChip`, `ghChip` | strings; `authChip` only when backend facts justify "Authorized by your instruction" | ✔ |
| `command` | last command outcome `{at,label,route,method,status,cls,message,ms}` | ▫ |
| `timestamps` | `{snapshotAt, localBrainStartedAt, lastResultFinishedAt, now}` | mixed |

**Mapping rules (normalize.js):** `run_state` running/passed/failed/stopped/error/idle → `executionState` running/**completed**/**completed**/stopped/error/idle; `result` PASS/FAIL/ERROR/STOPPED → `verdict` PASS/**FAILED**/ERROR/**null**. A capability that ends FAIL with `brain_error` starting `CAPABILITY BLOCKED` is shown as verdict **BLOCKED**. `brain_quality_state` `blocked|error` ⇒ **Failed verification**; `brain_preflight=blocked` ⇒ **Blocked**.
