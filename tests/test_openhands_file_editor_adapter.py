from __future__ import annotations

from pathlib import Path

import pytest

from orion_v3.authority import AuthorityDenied, AuthorityGateway, LeaseAuthority
from orion_v3.evidence import Outcome
from orion_v3.substrates.openhands_file_editor import execute_openhands_file_replace


class FakeWorker:
    def __init__(self, *, mutate_correctly: bool = True) -> None:
        self.calls = []
        self.mutate_correctly = mutate_correctly

    def __call__(self, payload):
        self.calls.append(dict(payload))
        target = Path(payload["target_path"])
        before = target.read_text(encoding="utf-8")
        if self.mutate_correctly:
            after = before.replace(payload["old_str"], payload["new_str"], 1)
        else:
            after = before + "\nUNAUTHORIZED = True\n"
        target.write_text(after, encoding="utf-8")
        return {"success": True, "command": "str_replace", "changed": True}


def build(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    target = project / "example.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    leases = LeaseAuthority(token_factory=lambda: "edit-token")
    gateway = AuthorityGateway(leases)
    issued = leases.issue(
        task_id="edit-task",
        operation_id="file.edit.replace",
        principal="owner",
        scope={
            "locations": ["project"],
            "relative_paths": ["example.py"],
            "max_replacement_chars": 100,
        },
        ttl_seconds=60,
    )
    return project, target, gateway, issued


def test_openhands_adapter_verifies_exact_authorized_change(tmp_path):
    project, target, gateway, issued = build(tmp_path)
    worker = FakeWorker()

    evidence = execute_openhands_file_replace(
        gateway=gateway,
        lease_token=issued.token,
        arguments={
            "location": "project",
            "relative_path": "example.py",
            "old_str": "VALUE = 1",
            "new_str": "VALUE = 2",
        },
        trusted_roots={"project": project},
        worker=worker,
    )

    assert evidence.outcome == Outcome.CONFIRMED
    assert target.read_text(encoding="utf-8") == "VALUE = 2\n"
    assert evidence.result["relative_path"] == "example.py"
    assert evidence.result["changed"] is True
    assert str(project) not in str(evidence.result)
    assert len(worker.calls) == 1


def test_openhands_adapter_denies_unleased_file_before_worker(tmp_path):
    project, _, gateway, issued = build(tmp_path)
    other = project / "other.py"
    other.write_text("VALUE = 1\n", encoding="utf-8")
    worker = FakeWorker()

    with pytest.raises(AuthorityDenied) as exc:
        execute_openhands_file_replace(
            gateway=gateway,
            lease_token=issued.token,
            arguments={
                "location": "project",
                "relative_path": "other.py",
                "old_str": "VALUE = 1",
                "new_str": "VALUE = 2",
            },
            trusted_roots={"project": project},
            worker=worker,
        )

    assert exc.value.code == "scope_violation"
    assert worker.calls == []


def test_openhands_adapter_rejects_wrong_post_edit_bytes(tmp_path):
    project, _, gateway, issued = build(tmp_path)
    worker = FakeWorker(mutate_correctly=False)

    evidence = execute_openhands_file_replace(
        gateway=gateway,
        lease_token=issued.token,
        arguments={
            "location": "project",
            "relative_path": "example.py",
            "old_str": "VALUE = 1",
            "new_str": "VALUE = 2",
        },
        trusted_roots={"project": project},
        worker=worker,
    )

    assert evidence.outcome == Outcome.UNVERIFIABLE
    assert "do not match" in (evidence.error or "")
