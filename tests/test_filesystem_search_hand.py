from pathlib import Path

import pytest

from orion_v3.authority import AuthorityGateway, LeaseAuthority
from orion_v3.hands import (
    FilesystemSearchHand,
    TrustedFilesystemRoots,
    normalize_search_evidence,
)


def authorize(tmp_path: Path, *, recursive=True, max_depth=4, max_results=10, names=None):
    leases = LeaseAuthority()
    issued = leases.issue(
        task_id="test-task",
        operation_id="filesystem.search",
        principal="owner",
        scope={
            "locations": ["project"],
            "recursive": recursive,
            "max_depth": max_depth,
            "max_results": max_results,
        },
        ttl_seconds=60,
    )
    gateway = AuthorityGateway(leases)
    op = gateway.authorize(
        lease_token=issued.token,
        operation_id="filesystem.search",
        arguments={
            "exact_names": names or ["target.txt"],
            "locations": ["project"],
            "recursive": recursive,
            "max_depth": max_depth,
            "max_results": max_results,
        },
    )
    hand = FilesystemSearchHand(TrustedFilesystemRoots({"project": tmp_path}))
    return op, hand


def test_searches_real_root_without_revealing_absolute_root(tmp_path: Path):
    (tmp_path / "target.txt").write_text("hello", encoding="utf-8")
    op, hand = authorize(tmp_path)

    result = hand.execute(op)

    assert result["match_count"] == 1
    assert result["matches"][0]["relative_path"] == "target.txt"
    assert str(tmp_path) not in str(result)


def test_nonrecursive_search_does_not_descend(tmp_path: Path):
    nested = tmp_path / "nested"
    nested.mkdir()
    (nested / "target.txt").write_text("hello", encoding="utf-8")
    op, hand = authorize(tmp_path, recursive=False, max_depth=0)

    result = hand.execute(op)

    assert result["matches"] == []


def test_recursive_search_respects_depth(tmp_path: Path):
    level1 = tmp_path / "one"
    level2 = level1 / "two"
    level2.mkdir(parents=True)
    (level1 / "target.txt").write_text("one", encoding="utf-8")
    (level2 / "target.txt").write_text("two", encoding="utf-8")

    op, hand = authorize(tmp_path, recursive=True, max_depth=1)
    result = hand.execute(op)

    paths = [m["relative_path"] for m in result["matches"]]
    assert "one/target.txt" in paths
    assert "one/two/target.txt" not in paths


def test_search_is_deterministic_and_bounded(tmp_path: Path):
    for folder in ["b", "a", "c"]:
        p = tmp_path / folder
        p.mkdir()
        (p / "target.txt").write_text(folder, encoding="utf-8")

    op, hand = authorize(tmp_path, recursive=True, max_depth=2, max_results=2)
    result = hand.execute(op)

    assert [m["relative_path"] for m in result["matches"]] == [
        "a/target.txt",
        "b/target.txt",
    ]
    assert result["truncated"] is True


def test_normalizes_confirmed_evidence(tmp_path: Path):
    (tmp_path / "target.txt").write_text("hello", encoding="utf-8")
    op, hand = authorize(tmp_path)
    result = hand.execute(op)

    evidence = normalize_search_evidence(op, result)

    assert evidence.task_id == "test-task"
    assert evidence.operation_id == "filesystem.search"
    assert evidence.implementation_id == "orion.filesystem.search.v1"
    assert evidence.outcome.value == "confirmed"
    assert evidence.result["match_count"] == 1
