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
    FileOperation,
    ReviewVerdict,
    WorkPackageExecutor,
    WorkPackageFactory,
)
from orion_v3.state import AttemptAuthority, LocalEventExchange, OrionStateStore


MODEL = os.environ.get("ORION_BENCHMARK_MODEL", "ollama/qwen3.6:35b-a3b")
RUN_ID = "V3-RUN-035"
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
- when the work is complete, report the result.
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


def changed_paths(worktree: Path) -> tuple[str, ...]:
    raw = git_raw(
        worktree,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    records = raw.split("\0")
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
        paths.add(path)
        if "R" in status or "C" in status:
            i += 1
            if i >= len(records) or not records[i]:
                raise RuntimeError("missing rename/copy source path")
        i += 1
    return tuple(sorted(paths))


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
        raise RuntimeError("RUN-035 worker result envelope missing")
    payload = json.loads(stdout[start + len(RESULT_START) : end].strip())
    if not isinstance(payload, dict):
        raise RuntimeError("RUN-035 worker result is not an object")
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


def terminal_success(worker: dict) -> bool:
    for item in worker.get("event_trace") or []:
        if item.get("type") != "ObservationEvent":
            continue
        if item.get("tool_name") != "terminal":
            continue
        obs = item.get("observation")
        if isinstance(obs, dict):
            if obs.get("exit_code") == 0 and obs.get("is_error") is False:
                return True
            metadata = obs.get("metadata")
            if (
                isinstance(metadata, dict)
                and metadata.get("exit_code") == 0
                and obs.get("is_error") is False
            ):
                return True
        encoded = json.dumps(obs, ensure_ascii=False, sort_keys=True)
        if "All tests passed." in encoded and "exit code 0" in encoded.lower():
            return True
    return False


def main() -> int:
    print("V3_RUN_ID> " + RUN_ID)
    print("OPENHANDS_RUNTIME_QUALIFICATION> START")

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

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-035-") as td:
        root = Path(td)
        source_repo = root / "fixture"
        candidate = root / "candidate"
        base_sha = init_fixture(source_repo)

        run(
            ["git", "worktree", "add", "--detach", str(candidate), base_sha],
            cwd=source_repo,
        )

        store: OrionStateStore | None = None
        try:
            if git(candidate, "rev-parse", "HEAD") != base_sha:
                raise RuntimeError("candidate wrong base SHA")
            if changed_paths(candidate):
                raise RuntimeError("candidate did not start clean")
            print("CANDIDATE_EXACT_SHA_WORKTREE> PASS")

            request = {
                "workspace": str(candidate),
                "prompt": PROMPT,
                "model": MODEL,
                "base_url": OLLAMA_URL,
                "max_iterations": 8,
                "stuck_detection": False,
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
                    "worker failed: "
                    + str(worker.get("detail") or worker.get("error") or proc.stderr)[-4000:]
                )

            tool_calls = tuple(str(x) for x in worker.get("tool_calls") or ())
            allowed = {"file_editor", "terminal", "finish"}
            unexpected = sorted({name for name in tool_calls if name not in allowed})
            if unexpected:
                raise RuntimeError("unexpected tools: " + ",".join(unexpected))
            if "file_editor" not in tool_calls:
                raise RuntimeError("FileEditor was not used")
            if "terminal" not in tool_calls:
                raise RuntimeError("Terminal was not used")

            execution_status = str(worker.get("execution_status") or "")
            finish_used = "finish" in tool_calls
            terminal_ok = terminal_success(worker)

            print("OPENHANDS_EXECUTION_STATUS> " + execution_status)
            print("OPENHANDS_TOOL_CALLS> " + json.dumps(tool_calls))
            print("OPENHANDS_FINISH_TOOL> " + ("PASS" if finish_used else "NOT_USED_ADVISORY"))
            print("OPENHANDS_TERMINAL_OBSERVATION> " + ("PASS" if terminal_ok else "FAIL"))
            print(
                "OPENHANDS_FINAL_CONTENT> "
                + str(worker.get("final_content") or "")[-2000:].replace("\n", " ")
            )

            if "FINISHED" not in execution_status.upper():
                raise RuntimeError("OpenHands did not terminate FINISHED")
            if not terminal_ok:
                raise RuntimeError("Terminal verification did not prove exit code 0")

            paths = changed_paths(candidate)
            if paths != ("src/clamp.py",):
                raise RuntimeError("unexpected candidate paths: " + ",".join(paths))
            if git(candidate, "rev-parse", "HEAD") != base_sha:
                raise RuntimeError("candidate changed Git HEAD")

            candidate_path = candidate / "src" / "clamp.py"
            candidate_bytes = candidate_path.read_bytes()
            candidate_text = candidate_bytes.decode("utf-8")
            normalized = candidate_text.replace("\r\n", "\n")
            if normalized != EXPECTED:
                raise RuntimeError("candidate bytes do not contain exact expected source")
            candidate_functional_check(candidate)
            candidate_sha = hashlib.sha256(candidate_bytes).hexdigest()

            print("AGENT_CHANGED_PATHS> PASS")
            print("AGENT_GIT_HEAD_UNCHANGED> PASS")
            print("AGENT_EXACT_SOURCE> PASS")
            print("AGENT_DETERMINISTIC_FUNCTIONAL_CHECK> PASS")
            print("AGENT_CANDIDATE_RAW_SHA256> " + candidate_sha)

            store = OrionStateStore(root / "core.db")
            store.initialize()
            project = store.create_project("RUN-035 fixture", project_id="run035")
            task = store.create_task(
                project.project_id,
                "Fix clamp boundary semantics",
                task_id="task-run035",
            )
            attempts = AttemptAuthority(store)
            attempts.initialize()
            attempt = attempts.create_attempt(
                task.task_id,
                attempt_id="attempt-run035",
            )

            artifacts = ArtifactStore(root / "artifacts")
            factory = WorkPackageFactory(artifacts)
            file_artifact = factory.file_artifact(
                "src/clamp.py",
                candidate_text,
                operation=FileOperation.REPLACE,
            )
            if file_artifact.sha256 != candidate_sha:
                raise RuntimeError("FILE artifact bytes differ from candidate bytes")

            package = factory.create(
                project_id=project.project_id,
                task_id=task.task_id,
                attempt_id=attempt.attempt_id,
                base_sha=base_sha,
                coder_provider="openhands-sdk-compact-orion",
                coder_model=MODEL,
                prompt_text=PROMPT,
                response_text=str(worker.get("final_content") or ""),
                artifacts=[file_artifact],
                allowed_paths=["src"],
                forbidden_paths=[".github", "docs"],
                verifier_spec={
                    "kind": "file_sha256",
                    "path": "src/clamp.py",
                    "sha256": candidate_sha,
                },
            )
            print("EXACT_CANDIDATE_FILE_ARTIFACT> PASS")
            print("AGENT_EXECUTION_AUTHORITY> NONE")

            board = CodingFactoryBlackboard(store, LocalEventExchange(store))
            proposal = board.submit_candidate(package)
            review = board.review_candidate(
                package,
                proposal.event_id,
                reviewer_provider="orion-deterministic",
                reviewer_model="run035-fixture",
                verdict=ReviewVerdict.ACCEPTABLE,
                findings=["exact candidate bytes and deterministic checks passed"],
            )
            decision = board.decide_candidate(
                package,
                review.event_id,
                verdict=DecisionVerdict.ACCEPT_CANDIDATE,
                decided_by="orion-run035-policy",
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
                authorized_by="orion-run035-policy",
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

            if evidence.changed_paths != ("src/clamp.py",):
                raise RuntimeError("ORION executor changed unexpected paths")
            if evidence.verifier.get("status") != "PASS":
                raise RuntimeError("ORION deterministic verifier did not pass")
            if evidence.verifier.get("sha256") != candidate_sha:
                raise RuntimeError("ORION verifier hash differs from candidate bytes")
            if attempts.get_attempt(attempt.attempt_id).status != "SUCCEEDED":
                raise RuntimeError("ORION Attempt did not finish SUCCEEDED")

            if git(source_repo, "rev-parse", "HEAD") != base_sha:
                raise RuntimeError("source repo HEAD changed")
            if git(source_repo, "status", "--porcelain=v1", "--untracked-files=no"):
                raise RuntimeError("source repo became dirty")
            execution_root = root / "execution-worktrees"
            if execution_root.exists() and any(execution_root.iterdir()):
                raise RuntimeError("execution worktree cleanup failed")

            print("WORKPACKAGE_FILE_REPLACE> PASS")
            print("PACKAGE_REVIEW_DECISION_ACTION_CHAIN> PASS")
            print("ORION_EXECUTION_ENVELOPE> PASS")
            print("ORION_DETERMINISTIC_VERIFIER> PASS")
            print("ORION_SOURCE_REPO_UNCHANGED> PASS")
            print("ORION_EXECUTION_CLEANUP> PASS")
            print("OPENHANDS_AGENT_RUNTIME_QUALIFIED> PASS")
        finally:
            if store is not None:
                store.close()
            run(
                ["git", "worktree", "remove", "--force", str(candidate)],
                cwd=source_repo,
                check=False,
            )
            run(["git", "worktree", "prune"], cwd=source_repo, check=False)

    print("OPENHANDS_RUNTIME_QUALIFICATION> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
