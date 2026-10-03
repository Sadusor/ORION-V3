from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SDK = ROOT / "external" / "OpenHands-software-agent-sdk"
WORKER = ROOT / "scripts" / "v34_openhands_run034_worker.py"
sys.path.insert(0, str(ROOT / "src"))

from orion_v3.coding_factory import (
    ArtifactStore,
    CodingFactoryBlackboard,
    DecisionVerdict,
    ReviewVerdict,
    WorkPackageExecutor,
    WorkPackageFactory,
)
from orion_v3.state import AttemptAuthority, LocalEventExchange, OrionStateStore


MODEL = os.environ.get("ORION_BENCHMARK_MODEL", "ollama/qwen3.6:35b-a3b")
RUN_ID = "V3-RUN-034"
OLLAMA_URL = "http://127.0.0.1:11434"
RESULT_START = "---ORION_RUN034_WORKER_RESULT_START---"
RESULT_END = "---ORION_RUN034_WORKER_RESULT_END---"

BEFORE = '''def clamp(value: int, low: int, high: int) -> int:
    """Return value bounded to the inclusive range [low, high].

    Precondition: low <= high.
    """
    return min(low, max(high, value))
'''

EXPECTED = '''def clamp(value: int, low: int, high: int) -> int:
    """Return value bounded to the inclusive range [low, high].

    Precondition: low <= high.
    """
    return max(low, min(high, value))
'''

PROMPT = """Fix the bug in src/clamp.py.

The clamp() function must return value bounded to the inclusive [low, high]
range described by its docstring. Inspect the existing file and make the
smallest correct edit using FileEditor.

After editing, use Terminal to run a small project-local verification that
checks below-range, in-range, above-range, and equal-bound behavior.

Constraints:
- modify only src/clamp.py;
- do not create files;
- do not rename files;
- do not commit or push;
- finish only after the verification succeeds.
"""


def run(
    args: list[str],
    *,
    cwd: Path,
    input_text: str | None = None,
    timeout: float = 60,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if check and proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "command failed").strip()
        raise RuntimeError(detail[-4000:])
    return proc


def git(cwd: Path, *args: str) -> str:
    return run(["git", *args], cwd=cwd).stdout.strip()


def git_raw(cwd: Path, *args: str) -> str:
    return run(["git", *args], cwd=cwd).stdout


def porcelain_z_records(worktree: Path) -> tuple[str, ...]:
    raw = git_raw(
        worktree,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    return tuple(raw.split("\0"))


def changed_paths_from_porcelain_z(records: tuple[str, ...]) -> tuple[str, ...]:
    paths: set[str] = set()
    i = 0
    while i < len(records):
        record = records[i]
        if not record:
            i += 1
            continue
        if len(record) < 4 or record[2] != " ":
            raise RuntimeError("malformed porcelain-v1-z record: " + repr(record))
        status = record[:2]
        path = record[3:].replace("\\", "/")
        if not path:
            raise RuntimeError("empty porcelain path")
        paths.add(path)

        # In -z mode rename/copy entries carry the second pathname as a separate
        # NUL-delimited field. The first record's path is the destination path,
        # which is the changed path ORION cares about.
        if "R" in status or "C" in status:
            i += 1
            if i >= len(records) or not records[i]:
                raise RuntimeError("missing rename/copy source path")
        i += 1
    return tuple(sorted(paths))


def changed_paths(worktree: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    records = porcelain_z_records(worktree)
    return changed_paths_from_porcelain_z(records), records


def ollama_tags() -> dict:
    with urllib.request.urlopen(OLLAMA_URL + "/api/tags", timeout=1.5) as response:
        return json.loads(response.read().decode("utf-8"))


def find_ollama() -> str | None:
    candidates: list[str] = []
    for name in ("ollama.exe", "ollama"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    local_app = os.environ.get("LOCALAPPDATA")
    program_files = os.environ.get("ProgramFiles")
    if local_app:
        candidates.extend(
            [
                str(Path(local_app) / "Programs" / "Ollama" / "ollama.exe"),
                str(Path(local_app) / "Ollama" / "ollama.exe"),
            ]
        )
    if program_files:
        candidates.append(str(Path(program_files) / "Ollama" / "ollama.exe"))
    for candidate in candidates:
        if Path(candidate).is_file():
            return candidate
    return None


def ensure_ollama() -> dict:
    try:
        return ollama_tags()
    except Exception:
        executable = find_ollama()
        if not executable:
            raise RuntimeError("Ollama is not running and ollama.exe was not found")
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0
        subprocess.Popen(
            [executable, "serve"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
        deadline = time.time() + 15
        last_error: Exception | None = None
        while time.time() < deadline:
            try:
                return ollama_tags()
            except Exception as exc:
                last_error = exc
                time.sleep(0.25)
        raise RuntimeError("Ollama did not become ready") from last_error


def parse_worker(stdout: str) -> dict:
    start = stdout.rfind(RESULT_START)
    end = stdout.rfind(RESULT_END)
    if start < 0 or end < 0 or end <= start:
        raise RuntimeError("RUN-034 worker result envelope missing")
    payload = json.loads(stdout[start + len(RESULT_START) : end].strip())
    if not isinstance(payload, dict):
        raise RuntimeError("RUN-034 worker result is not an object")
    return payload


def init_fixture(repo: Path) -> str:
    repo.mkdir(parents=True)
    run(["git", "init"], cwd=repo)
    run(["git", "config", "user.name", "ORION Benchmark"], cwd=repo)
    run(["git", "config", "user.email", "orion-benchmark@local"], cwd=repo)
    (repo / "src").mkdir()
    (repo / "src" / "clamp.py").write_text(BEFORE, encoding="utf-8")
    run(["git", "add", "src/clamp.py"], cwd=repo)
    run(["git", "commit", "-m", "fixture: broken clamp"], cwd=repo)
    return git(repo, "rev-parse", "HEAD")


def candidate_functional_check(worktree: Path) -> None:
    code = (
        "from src.clamp import clamp; "
        "assert clamp(-5, 0, 10) == 0; "
        "assert clamp(5, 0, 10) == 5; "
        "assert clamp(15, 0, 10) == 10; "
        "assert clamp(7, 7, 7) == 7"
    )
    run([sys.executable, "-B", "-c", code], cwd=worktree)


def terminal_observation_summary(worker: dict) -> tuple[bool, list[dict]]:
    observations: list[dict] = []
    successful = False
    for item in worker.get("event_trace") or []:
        if item.get("type") != "ObservationEvent":
            continue
        if item.get("tool_name") != "terminal":
            continue
        obs = item.get("observation")
        observations.append(obs if isinstance(obs, dict) else {"raw": obs})
        encoded = json.dumps(obs, ensure_ascii=False, sort_keys=True)
        if '"exit_code": 0' in encoded or '"exit_code":0' in encoded:
            successful = True
        if "All tests passed." in encoded and "exit code 0" in encoded.lower():
            successful = True
    return successful, observations


def run_case(
    *,
    source_repo: Path,
    root: Path,
    base_sha: str,
    label: str,
    stuck_detection: bool,
) -> dict:
    candidate = root / ("candidate-" + label.lower())
    run(["git", "worktree", "add", "--detach", str(candidate), base_sha], cwd=source_repo)
    try:
        initial_paths, initial_records = changed_paths(candidate)
        if initial_paths:
            raise RuntimeError(label + " candidate did not start clean")
        if git(candidate, "rev-parse", "HEAD") != base_sha:
            raise RuntimeError(label + " candidate wrong base SHA")

        request = {
            "workspace": str(candidate),
            "prompt": PROMPT,
            "model": MODEL,
            "base_url": OLLAMA_URL,
            "max_iterations": 8,
            "stuck_detection": stuck_detection,
        }
        proc = run(
            [
                "uv",
                "run",
                "--project",
                str(SDK),
                "--package",
                "openhands-tools",
                "python",
                str(WORKER),
            ],
            cwd=ROOT,
            input_text=json.dumps(request),
            timeout=300,
            check=False,
        )
        worker = parse_worker(proc.stdout)
        if proc.returncode != 0 or worker.get("success") is not True:
            raise RuntimeError(
                label + " worker failed: "
                + str(worker.get("detail") or worker.get("error") or proc.stderr)[-4000:]
            )

        tool_calls = tuple(str(x) for x in worker.get("tool_calls") or ())
        allowed_tools = {"file_editor", "terminal", "finish"}
        unexpected = sorted({name for name in tool_calls if name not in allowed_tools})
        if unexpected:
            raise RuntimeError(label + " unexpected tools: " + ",".join(unexpected))

        paths, raw_records = changed_paths(candidate)
        after = (candidate / "src" / "clamp.py").read_text(encoding="utf-8")
        terminal_ok, terminal_observations = terminal_observation_summary(worker)
        head_ok = git(candidate, "rev-parse", "HEAD") == base_sha

        deterministic_ok = False
        functional_error = ""
        if after == EXPECTED and paths == ("src/clamp.py",) and head_ok:
            try:
                candidate_functional_check(candidate)
                deterministic_ok = True
            except Exception as exc:
                functional_error = str(exc)[-2000:]

        patch = git_raw(candidate, "diff", "--binary", "--no-ext-diff", "HEAD", "--")

        print(label + "_STUCK_DETECTION> " + ("ON" if stuck_detection else "OFF"))
        print(label + "_EXECUTION_STATUS> " + str(worker.get("execution_status")))
        print(label + "_TOOL_CALLS> " + json.dumps(tool_calls))
        print(label + "_FINISH> " + ("PASS" if "finish" in tool_calls else "FAIL"))
        print(label + "_TERMINAL_OBSERVATION_OK> " + ("PASS" if terminal_ok else "FAIL"))
        print(label + "_RAW_PORCELAIN_Z_RECORDS> " + json.dumps(raw_records))
        print(label + "_CHANGED_PATHS> " + json.dumps(paths))
        print(label + "_HEAD_UNCHANGED> " + ("PASS" if head_ok else "FAIL"))
        print(label + "_EXACT_FILE_BYTES> " + ("PASS" if after == EXPECTED else "FAIL"))
        print(label + "_DETERMINISTIC_FUNCTIONAL_CHECK> " + ("PASS" if deterministic_ok else "FAIL"))
        if functional_error:
            print(label + "_FUNCTIONAL_ERROR> " + functional_error.replace("\n", " "))
        print(
            label + "_STUCK_DIAGNOSTICS> "
            + json.dumps(worker.get("stuck_diagnostics") or {}, ensure_ascii=False, sort_keys=True)
        )
        print(
            label + "_TERMINAL_OBSERVATIONS> "
            + json.dumps(terminal_observations, ensure_ascii=False, sort_keys=True)
        )
        print(
            label + "_EVENT_TRACE> "
            + json.dumps(worker.get("event_trace") or [], ensure_ascii=False, sort_keys=True)
        )

        return {
            "label": label,
            "worker": worker,
            "tool_calls": tool_calls,
            "paths": paths,
            "after": after,
            "head_ok": head_ok,
            "terminal_ok": terminal_ok,
            "deterministic_ok": deterministic_ok,
            "patch": patch,
        }
    finally:
        run(
            ["git", "worktree", "remove", "--force", str(candidate)],
            cwd=source_repo,
            check=False,
        )
        run(["git", "worktree", "prune"], cwd=source_repo, check=False)


def execute_verified_patch(root: Path, source_repo: Path, base_sha: str, case: dict) -> bool:
    if not case["deterministic_ok"] or not case["patch"].strip():
        print("VERIFIED_CANDIDATE_WORKPACKAGE> SKIPPED")
        return False

    store = OrionStateStore(root / "core.db")
    store.initialize()
    project = store.create_project("RUN-034 fixture", project_id="run034")
    task = store.create_task(
        project.project_id,
        "Fix clamp boundary semantics",
        task_id="task-run034",
    )
    attempts = AttemptAuthority(store)
    attempts.initialize()
    attempt = attempts.create_attempt(task.task_id, attempt_id="attempt-run034")

    artifacts = ArtifactStore(root / "artifacts")
    factory = WorkPackageFactory(artifacts)
    patch_artifact = factory.patch_artifact(
        case["patch"],
        target_paths=["src/clamp.py"],
    )
    package = factory.create(
        project_id=project.project_id,
        task_id=task.task_id,
        attempt_id=attempt.attempt_id,
        base_sha=base_sha,
        coder_provider="openhands-sdk-run034",
        coder_model=MODEL,
        prompt_text=PROMPT,
        response_text=str(case["worker"].get("final_content") or ""),
        artifacts=[patch_artifact],
        allowed_paths=["src"],
        forbidden_paths=[".github", "docs"],
        verifier_spec={
            "kind": "file_sha256",
            "path": "src/clamp.py",
            "sha256": hashlib.sha256(EXPECTED.encode("utf-8")).hexdigest(),
        },
    )

    board = CodingFactoryBlackboard(store, LocalEventExchange(store))
    proposal = board.submit_candidate(package)
    review = board.review_candidate(
        package,
        proposal.event_id,
        reviewer_provider="orion-deterministic",
        reviewer_model="run034-fixture",
        verdict=ReviewVerdict.ACCEPTABLE,
        findings=["RUN-034 deterministic candidate checks passed"],
    )
    decision = board.decide_candidate(
        package,
        review.event_id,
        verdict=DecisionVerdict.ACCEPT_CANDIDATE,
        decided_by="orion-run034-policy",
    )
    issued = attempts.claim(
        attempt.attempt_id,
        worker_id="workpackage-executor",
        ttl_seconds=60,
    )
    action = board.authorize_execution(
        package,
        decision.event_id,
        lease=issued.lease,
        authorized_by="orion-run034-policy",
    )
    executor = WorkPackageExecutor(
        store=store,
        attempts=attempts,
        factory=factory,
        source_repo=source_repo,
        worktree_root=root / "execution-worktrees",
    )
    evidence = executor.run(
        manifest_artifact_id=package.manifest_artifact_id,
        expected_package_sha256=package.package_sha256,
        action_event_id=action.event_id,
        lease_token=issued.token,
    )
    ok = (
        evidence.changed_paths == ("src/clamp.py",)
        and evidence.verifier.get("status") == "PASS"
        and attempts.get_attempt(attempt.attempt_id).status == "SUCCEEDED"
    )
    print("VERIFIED_CANDIDATE_WORKPACKAGE> " + ("PASS" if ok else "FAIL"))
    print("ORION_RUN020_EXECUTION_ENVELOPE> " + ("PASS" if ok else "FAIL"))
    return ok


def main() -> int:
    print("V3_RUN_ID> " + RUN_ID)
    print("OPENHANDS_STUCK_CHARACTERIZATION> START")

    if not SDK.is_dir() or not WORKER.is_file():
        print("HARNESS_STATUS> FAIL missing SDK/worker")
        print("STATUS> FAIL")
        return 1

    tags = ensure_ollama()
    names = {
        str(item.get("name") or "")
        for item in tags.get("models", [])
        if isinstance(item, dict)
    }
    local_name = MODEL.removeprefix("ollama/")
    if local_name not in names:
        print("LOCAL_MODEL_AVAILABLE> FAIL " + local_name)
        print("STATUS> FAIL")
        return 1

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-034-") as td:
        root = Path(td)
        source_repo = root / "fixture"
        base_sha = init_fixture(source_repo)

        case_a = run_case(
            source_repo=source_repo,
            root=root,
            base_sha=base_sha,
            label="CASE_A",
            stuck_detection=True,
        )
        case_b = run_case(
            source_repo=source_repo,
            root=root,
            base_sha=base_sha,
            label="CASE_B",
            stuck_detection=False,
        )

        selected = case_b if case_b["deterministic_ok"] else case_a
        envelope_ok = execute_verified_patch(root, source_repo, base_sha, selected)

        case_a_candidate = bool(case_a["deterministic_ok"])
        case_b_candidate = bool(case_b["deterministic_ok"])
        case_b_status = str(case_b["worker"].get("execution_status") or "")
        case_b_clean_termination = (
            "FINISHED" in case_b_status.upper()
            and "finish" in case_b["tool_calls"]
        )

        runtime_qualified = (
            case_a_candidate
            and case_b_candidate
            and case_b_clean_termination
            and envelope_ok
        )

        print("CASE_A_CANDIDATE> " + ("PASS" if case_a_candidate else "FAIL"))
        print("CASE_B_CANDIDATE> " + ("PASS" if case_b_candidate else "FAIL"))
        print(
            "CASE_B_CLEAN_TERMINATION> "
            + ("PASS" if case_b_clean_termination else "FAIL")
        )
        print(
            "OPENHANDS_AGENT_RUNTIME_QUALIFIED> "
            + ("PASS" if runtime_qualified else "FAIL")
        )
        print("DIAGNOSTIC_STATUS> PASS")

    print("OPENHANDS_STUCK_CHARACTERIZATION> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
