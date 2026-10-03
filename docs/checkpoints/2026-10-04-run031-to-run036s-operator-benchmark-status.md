# ORION operator benchmark status — RUN-031 through RUN-036S

Date: 2026-10-04

This checkpoint consolidates the full OpenHands qualification and first mixed-tool
ORION Operator benchmark sequence.

## RUN-031 — compact OpenHands Agent path

Status: **PHYSICAL PASS**

Proved:
- compact ORION-owned prompt was loaded exactly;
- real OpenHands Agent/Conversation loop ran;
- Qwen3.6 emitted a structured Terminal action;
- exact harmless command executed;
- real observation returned;
- Agent emitted a completion action;
- no AgentError events.

Conclusion:
the stock OpenHands prompt was the compatibility problem, not the Qwen/Ollama/
LiteLLM/OpenHands tool path.

## RUN-032 — first compact coding task

Status: **PHYSICAL FAIL**

Observed:
- FileEditor used;
- Terminal used;
- benchmark aborted because FinishTool was not emitted.

Classification:
the harness incorrectly treated donor FinishTool as canonical completion truth.

## RUN-033 — completion-aware coding retry

Status: **PHYSICAL FAIL**

Observed:
- FileEditor -> FileEditor -> Terminal;
- candidate work proceeded;
- OpenHands ended STUCK;
- changed-path parser reported `rc/clamp.py`;
- Python verification created `__pycache__`.

Classification:
- `rc/clamp.py` was an ORION harness parsing bug:
  generic `.strip()` removed the leading porcelain status-space before
  `line[3:]`;
- bytecode was verification pollution, not a model scope violation;
- candidate correctness still needed direct proof.

## RUN-034 — stuck characterization

Status: **PROCESS FAIL, CANDIDATE PHYSICALLY PROVEN CORRECT**

Proved:
- with stuck detection disabled, Qwen used FileEditor + Terminal;
- Terminal observation returned `All tests passed.`;
- exit code 0;
- final Qwen content correctly described the clamp fix;
- candidate passed exact-path, exact-source, unchanged-HEAD and independent
  deterministic functional checks.

Failure:
the candidate was converted into a PATCH artifact and replayed in a second
worktree; raw-byte file SHA verification then failed.

New ORION core gap:
RUN-020 had physically proven FILE artifact execution, not this exact
PATCH -> git apply -> raw-byte verifier path.

Also found:
RUN-034 forgot to close OrionStateStore after verifier failure, leaving core.db
locked on Windows.

## RUN-035 — OpenHands runtime qualification

Status: **PHYSICAL PASS**

Session:
`2d9baf57bc54`

Proved:
- execution status FINISHED;
- FileEditor + Terminal tool use;
- real Terminal verification PASS;
- exact candidate path/source/functionality PASS;
- exact candidate bytes frozen as FILE REPLACE;
- candidate retained zero execution authority;
- review/decision/action chain PASS;
- WorkPackage execution envelope PASS;
- deterministic verifier PASS;
- source repo unchanged;
- cleanup PASS.

Final:
`OPENHANDS_AGENT_RUNTIME_QUALIFIED> PASS`

Decision:
stop isolated OpenHands Agent benchmarking. OpenHands Agent is one qualified
optional runtime inside ORION under:
- compact ORION prompt;
- ORION-controlled tool exposure;
- disposable workspace;
- ORION authority/evidence/verifier boundary.

## RUN-036 — first mixed-tool operator smoke

Status: **PHYSICAL FAIL — OPERATOR NOT TESTED**

Failure:
`ModuleNotFoundError: openjarvis_rust`

Cause:
RUN-036 instantiated OpenJarvis CapabilityPolicy inside the OpenHands Python
environment. That optional donor policy imports the compiled Rust bridge which
was not installed in that environment.

Classification:
environment-composition bug. Qwen did not receive a benchmark case.

Correction:
keep the real OpenJarvis ToolRegistry/ToolExecutor and ORION Action
Lease/AuthorityGateway, but omit the optional donor CapabilityPolicy object from
this combined benchmark process.

## RUN-036R — mixed-tool retry

Status: **PHYSICAL FAIL — QWEN REACHED THE BENCHMARK**

Session:
`90afa1902ab6`

Proved:
- mixed Agent loaded 3 tools;
- Qwen reached SEARCH_CASE;
- Qwen selected the OpenJarvis-backed search tool family correctly.

Failure:
search evidence did not contain both expected files.

Problem:
RUN-036R raised before printing the exact action/observation, so model argument
error vs donor result was ambiguous.

## RUN-036S — instrumented mixed-tool retry

Status: **PHYSICAL FAIL — BRIDGE SERIALIZATION BUG IDENTIFIED**

Session:
`790eeede9623`

Deterministic control:
`DIRECT_OPENJARVIS_CONTROL> PASS`

The same OpenJarvis search, called deterministically with:
- exact_names = [pyproject.toml, gateway.py];
- locations = [active_project];
- recursive = true;
- max_depth = 4;
- max_results = 10;

returned:
- all expected pyproject.toml matches;
- `src/orion_v3/authority/gateway.py`;
- no absolute trusted-root leak.

Qwen action:
- selected `search_exact_files`;
- exact_names = [pyproject.toml, gateway.py];
- locations = [active_project];
- recursive = true;
- max_depth = 4;
- max_results = 10.

Therefore Qwen's tool-family selection and semantic arguments were correct.

Observed denial:
`orion_denial_code = unknown_argument`

Exact cause:
OpenHands/Pydantic serialized the Action model with its framework discriminator:

`kind = SearchExactFilesAction`

The mixed adapter forwarded the entire `action.model_dump()` object into the
OpenJarvis/ORION tool call.

ORION AuthorityGateway correctly rejects unknown filesystem.search arguments.
The deterministic direct control did not include `kind`, so it passed.

Classification:
**adapter serialization bug**.

This is not:
- a Qwen reasoning failure;
- an OpenJarvis search failure;
- an ORION AuthorityGateway failure.

## Required bridge rule promoted from RUN-036S

Cross-runtime adapters must use an explicit allowlist mapping from model-facing
Action objects to ORION capability arguments.

Never forward framework-internal model fields by dumping the complete Action
object.

For filesystem.search the adapter may forward only:
- exact_names;
- locations;
- recursive;
- max_depth;
- max_results.

Framework fields such as `kind` must never cross the ORION authority boundary.

## Denial-case correction

The model-facing search schema must allow both:
- `active_project`;
- `desktop`.

The Action Lease continues to allow only:
- `active_project`.

This is intentional.

The DENIED_CASE must let Qwen express a valid request for `desktop`, then let
ORION AuthorityGateway reject it with `scope_violation`.

Do not prevent the denied request at the schema layer, because then the test
would no longer prove the authority boundary.

## Current architectural status

Qualified:
- Qwen3.6 native structured tool calling;
- compact OpenHands Agent runtime;
- OpenHands FileEditor;
- OpenHands Terminal;
- OpenJarvis exact-name filesystem search donor;
- ORION semantic Capability Registry;
- ORION Action Lease/AuthorityGateway;
- WorkPackage execution envelope for FILE artifacts.

Not yet qualified:
- mixed-tool ORION Operator benchmark as a whole;
- PATCH artifact replay portability;
- Qwen3.8-27B operator comparison.

Important:
no RUN-036-series physical evidence currently shows Qwen choosing the wrong
tool family. The latest physical evidence shows correct search-tool selection
and correct search arguments before an adapter bug caused ORION denial.
