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
WORKER = ROOT / "scripts" / "v34_openhands_compact_coding_worker.py"
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
RUN_ID = os.environ.get("ORION_BENCHMARK_RUN_ID", "V3-RUN-032")
OLLAMA_URL = "http://127.0.0.1:11434"
RESULT_START = "---ORION_COMPACT_CODING_HAND_RESULT_START---"
RESULT_END = "---ORION_COMPACT_CODING_HAND_RESULT_END---"

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
        raise RuntimeError("OpenHands compact worker result envelope missing")
    raw = stdout[start + len(RESULT_START) : end].strip()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError("OpenHands compact worker result is not an object")
    return payload


def changed_paths(worktree: Path) -> tuple[str, ...]:
    status = git(worktree, "status", "--porcelain=v1", "--untracked-files=all")
    paths: set[str] = set()
    for line in status.splitlines():
        if not line.strip():
            continue
        raw = line[3:].strip().replace("\\", "/")
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.add(raw)
    return tuple(sorted(paths))


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
    run([sys.executable, "-c", code], cwd=worktree)


def main() -> int:
    print("V3_RUN_ID> " + RUN_ID)
    print("COMPACT_SEMANTIC_CODING_HAND_BENCHMARK> START")
    print("BENCHMARK_MODEL> " + MODEL)

    if not SDK.is_dir() or not WORKER.is_file():
        print("OPENHANDS_PINNED_SDK> MISSING")
        print("STATUS> FAIL")
        return 1

    tags = ensure_ollama()
    model_names = {
        str(item.get("name") or "")
        for item in tags.get("models", [])
        if isinstance(item, dict)
    }
    local_name = MODEL.removeprefix("ollama/")
    if local_name not in model_names:
        print("LOCAL_MODEL_AVAILABLE> FAIL " + local_name)
        print("OLLAMA_INSTALLED_MODELS> " + ",".join(sorted(model_names)))
        print("STATUS> FAIL")
        return 1

    print("OPENHANDS_PINNED_SDK> PRESENT")
    print("LLM_ENDPOINT> LOOPBACK")
    print("PAID_API_KEY_DEPENDENCY> NONE")
    print("LOCAL_MODEL_AVAILABLE> PASS " + local_name)
    print("AGENT_SYSTEM_PROMPT> ORION_COMPACT")
    print("AGENT_TOOL_POLICY> FILE_EDITOR_TERMINAL_FINISH")

    with tempfile.TemporaryDirectory(prefix="orion-v3-run-032-") as td:
        root = Path(td)
        source_repo = root / "fixture"
        candidate = root / "candidate"
        base_sha = init_fixture(source_repo)

        run(
            ["git", "worktree", "add", "--detach", str(candidate), base_sha],
            cwd=source_repo,
        )
        try:
            assert git(candidate, "rev-parse", "HEAD") == base_sha
            assert changed_paths(candidate) == ()
            print("CANDIDATE_EXACT_SHA_WORKTREE> PASS")

            request = {
                "workspace": str(candidate),
                "prompt": PROMPT,
                "model": MODEL,
                "base_url": OLLAMA_URL,
                "max_iterations": 8,
            }
            started = time.monotonic()
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
            wall = time.monotonic() - started
            worker = parse_worker(proc.stdout)
            if proc.returncode != 0 or worker.get("success") is not True:
                detail = worker.get("detail") or worker.get("error") or proc.stderr
                raise RuntimeError("OpenHands compact coding agent failed: " + str(detail)[-3000:])

            tool_calls = tuple(str(x) for x in worker.get("tool_calls") or ())
            allowed_tools = {"file_editor", "terminal", "finish"}
            unexpected_tools = sorted({name for name in tool_calls if name not in allowed_tools})
            if unexpected_tools:
                raise RuntimeError("unexpected agent tools: " + ",".join(unexpected_tools))
            if "file_editor" not in tool_calls:
                raise RuntimeError("agent never used FileEditor")
            if "terminal" not in tool_calls:
                raise RuntimeError("agent never used Terminal verification")
            if "finish" not in tool_calls:
                raise RuntimeError("agent never emitted Finish")

            print("OPENHANDS_REAL_AGENT_LOOP> PASS")
            print("OPENHANDS_FILE_EDITOR_USE> PASS")
            print("OPENHANDS_TERMINAL_USE> PASS")
            print("OPENHANDS_FINISH_USE> PASS")
            print("OPENHANDS_AGENT_ACTIONS> " + str(len(tool_calls)))
            print("OPENHANDS_AGENT_WALL_SECONDS> " + f"{wall:.3f}")
            print(
                "OPENHANDS_TERMINAL_COMMANDS> "
                + json.dumps(worker.get("terminal_commands") or [], ensure_ascii=False)
            )

            actual_paths = changed_paths(candidate)
            if actual_paths != ("src/clamp.py",):
                raise RuntimeError(
                    "unexpected candidate paths: " + ",".join(actual_paths)
                )
            if git(candidate, "rev-parse", "HEAD") != base_sha:
                raise RuntimeError("agent changed Git HEAD")
            after = (candidate / "src" / "clamp.py").read_text(encoding="utf-8")
            if after != EXPECTED:
                raise RuntimeError("agent did not produce the expected minimal fix")
            candidate_functional_check(candidate)

            patch = git(candidate, "diff", "--binary", "--no-ext-diff", "HEAD", "--")
            if not patch.strip():
                raise RuntimeError("agent produced no patch")

            print("AGENT_CHANGED_PATHS> PASS")
            print("AGENT_UNEXPECTED_MUTATIONS> 0")
            print("AGENT_FUNCTIONAL_FIX> PASS")
            print("AGENT_GIT_HEAD_UNCHANGED> PASS")

            store = OrionStateStore(root / "core.db")
            store.initialize()
            project = store.create_project("RUN-032 fixture", project_id="run032")
            task = store.create_task(
                project.project_id,
                "Fix clamp boundary semantics",
                task_id="task-openhands-compact",
            )
            attempts = AttemptAuthority(store)
            attempts.initialize()
            attempt = attempts.create_attempt(
                task.task_id,
                attempt_id="attempt-openhands-compact",
            )

            artifacts = ArtifactStore(root / "artifacts")
            factory = WorkPackageFactory(artifacts)
            patch_artifact = factory.patch_artifact(
                patch,
                target_paths=["src/clamp.py"],
            )
            package = factory.create(
                project_id=project.project_id,
                task_id=task.task_id,
                attempt_id=attempt.attempt_id,
                base_sha=base_sha,
                coder_provider="openhands-sdk-compact-orion",
                coder_model=MODEL,
                prompt_text=PROMPT,
                response_text=str(worker.get("final_content") or ""),
                artifacts=[patch_artifact],
                allowed_paths=["src"],
                forbidden_paths=[".github", "docs"],
                verifier_spec={
                    "kind": "file_sha256",
                    "path": "src/clamp.py",
                    "sha256": hashlib.sha256(EXPECTED.encode("utf-8")).hexdigest(),
                },
            )
            print("AGENT_CANDIDATE_FROZEN_WORKPACKAGE> PASS")
            print("AGENT_EXECUTION_AUTHORITY> NONE")

            board = CodingFactoryBlackboard(store, LocalEventExchange(store))
            proposal = board.submit_candidate(package)
            review = board.review_candidate(
                package,
                proposal.event_id,
                reviewer_provider="orion-deterministic",
                reviewer_model="run032-fixture",
                verdict=ReviewVerdict.ACCEPTABLE,
                findings=["compact candidate functional checks passed"],
            )
            decision = board.decide_candidate(
                package,
                review.event_id,
                verdict=DecisionVerdict.ACCEPT_CANDIDATE,
                decided_by="orion-run032-policy",
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
                authorized_by="orion-run032-policy",
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
                raise RuntimeError("ORION execution changed unexpected paths")
            if evidence.verifier.get("status") != "PASS":
                raise RuntimeError("ORION verifier did not pass")
            if attempts.get_attempt(attempt.attempt_id).status != "SUCCEEDED":
                raise RuntimeError("ORION Attempt did not finish SUCCEEDED")

            if (source_repo / "src" / "clamp.py").read_text(encoding="utf-8") != BEFORE:
                raise RuntimeError("source fixture was mutated")
            if git(source_repo, "status", "--porcelain=v1", "--untracked-files=no"):
                raise RuntimeError("source fixture became dirty")
            execution_root = root / "execution-worktrees"
            if execution_root.exists() and any(execution_root.iterdir()):
                raise RuntimeError("execution worktree cleanup failed")

            print("PACKAGE_REVIEW_DECISION_ACTION_CHAIN> PASS")
            print("ORION_EXECUTION_ENVELOPE> PASS")
            print("ORION_CHANGED_PATH_VERIFICATION> PASS")
            print("ORION_DETERMINISTIC_VERIFIER> PASS")
            print("ORION_SOURCE_REPO_UNCHANGED> PASS")
            print("ORION_EXECUTION_CLEANUP> PASS")
        finally:
            run(
                ["git", "worktree", "remove", "--force", str(candidate)],
                cwd=source_repo,
                check=False,
            )
            run(["git", "worktree", "prune"], cwd=source_repo, check=False)

    print("COMPACT_SEMANTIC_CODING_HAND_BENCHMARK> PASS")
    print("STATUS> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
