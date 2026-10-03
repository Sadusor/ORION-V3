from __future__ import annotations

import pytest

from orion_v3.authority import AuthorityDenied, AuthorityGateway, LeaseAuthority


class Clock:
    def __init__(self, value: float = 1000.0) -> None:
        self.value = value

    def __call__(self) -> float:
        return self.value


def build_gate():
    clock = Clock()
    tokens = iter(["token-a", "token-b", "token-c"])
    leases = LeaseAuthority(clock=clock, token_factory=lambda: next(tokens))
    gateway = AuthorityGateway(leases)
    issued = leases.issue(
        task_id="task-1",
        operation_id="filesystem.search",
        principal="owner",
        scope={
            "locations": ["documents", "downloads"],
            "recursive": True,
            "max_depth": 3,
            "max_results": 10,
        },
        ttl_seconds=60,
    )
    return clock, leases, gateway, issued


def request(**overrides):
    value = {
        "exact_names": ["report.txt"],
        "locations": ["documents"],
        "recursive": True,
        "max_depth": 2,
        "max_results": 5,
    }
    value.update(overrides)
    return value


def assert_denied(code, fn):
    with pytest.raises(AuthorityDenied) as exc:
        fn()
    assert exc.value.code == code


def test_valid_lease_authorizes_bounded_search():
    _, _, gateway, issued = build_gate()
    authorized = gateway.authorize(
        lease_token=issued.token,
        operation_id="filesystem.search",
        arguments=request(),
    )
    assert authorized.operation_id == "filesystem.search"
    assert authorized.lease.lease_id == issued.lease.lease_id
    assert authorized.arguments["locations"] == ["documents"]
    assert authorized.arguments["reveal_containing_folders"] is False
    assert "roots" not in authorized.arguments


def test_missing_lease_fails_closed():
    _, _, gateway, _ = build_gate()
    assert_denied(
        "missing_action_lease",
        lambda: gateway.authorize(
            lease_token=None, operation_id="filesystem.search", arguments=request()
        ),
    )


def test_forged_lease_fails_closed():
    _, _, gateway, _ = build_gate()
    assert_denied(
        "unknown_action_lease",
        lambda: gateway.authorize(
            lease_token="forged", operation_id="filesystem.search", arguments=request()
        ),
    )


def test_expired_lease_fails_closed():
    clock, _, gateway, issued = build_gate()
    clock.value = issued.lease.expires_at
    assert_denied(
        "expired_action_lease",
        lambda: gateway.authorize(
            lease_token=issued.token, operation_id="filesystem.search", arguments=request()
        ),
    )


def test_revoked_lease_fails_closed():
    _, leases, gateway, issued = build_gate()
    leases.revoke(issued.token)
    assert_denied(
        "revoked_action_lease",
        lambda: gateway.authorize(
            lease_token=issued.token, operation_id="filesystem.search", arguments=request()
        ),
    )


def test_wrong_operation_fails_closed():
    _, _, gateway, issued = build_gate()
    assert_denied(
        "wrong_operation",
        lambda: gateway.authorize(
            lease_token=issued.token, operation_id="filesystem.list", arguments=request()
        ),
    )


def test_location_cannot_exceed_lease_scope():
    _, _, gateway, issued = build_gate()
    assert_denied(
        "scope_violation",
        lambda: gateway.authorize(
            lease_token=issued.token,
            operation_id="filesystem.search",
            arguments=request(locations=["desktop"]),
        ),
    )


def test_depth_cannot_exceed_lease_scope():
    _, _, gateway, issued = build_gate()
    assert_denied(
        "scope_violation",
        lambda: gateway.authorize(
            lease_token=issued.token,
            operation_id="filesystem.search",
            arguments=request(max_depth=6),
        ),
    )


def test_search_cannot_widen_into_reveal():
    _, _, gateway, issued = build_gate()
    assert_denied(
        "operation_widening",
        lambda: gateway.authorize(
            lease_token=issued.token,
            operation_id="filesystem.search",
            arguments=request(reveal_containing_folders=True),
        ),
    )


@pytest.mark.parametrize(
    "field",
    ["roots", "local_roots", "repo_root", "expected_repo", "expected_branch", "credential", "opener"],
)
def test_model_arguments_cannot_supply_trust_anchors(field):
    _, _, gateway, issued = build_gate()
    args = request()
    args[field] = "attacker-controlled"
    assert_denied(
        "trusted_binding_override",
        lambda: gateway.authorize(
            lease_token=issued.token, operation_id="filesystem.search", arguments=args
        ),
    )


def build_file_edit_gate():
    clock = Clock()
    leases = LeaseAuthority(clock=clock, token_factory=lambda: "edit-token")
    gateway = AuthorityGateway(leases)
    issued = leases.issue(
        task_id="edit-task",
        operation_id="file.edit.replace",
        principal="owner",
        scope={
            "locations": ["project"],
            "relative_paths": ["src/example.py"],
            "max_replacement_chars": 100,
        },
        ttl_seconds=60,
    )
    return gateway, issued


def edit_request(**overrides):
    value = {
        "location": "project",
        "relative_path": "src/example.py",
        "old_str": "VALUE = 1",
        "new_str": "VALUE = 2",
    }
    value.update(overrides)
    return value


def test_file_edit_replace_authorizes_exact_scoped_file():
    gateway, issued = build_file_edit_gate()

    authorized = gateway.authorize(
        lease_token=issued.token,
        operation_id="file.edit.replace",
        arguments=edit_request(),
    )

    assert authorized.arguments["location"] == "project"
    assert authorized.arguments["relative_path"] == "src/example.py"
    assert authorized.arguments["old_str"] == "VALUE = 1"
    assert authorized.arguments["new_str"] == "VALUE = 2"


@pytest.mark.parametrize(
    "relative_path",
    [
        "../outside.py",
        "/absolute.py",
        "C:/absolute.py",
        "src/../outside.py",
    ],
)
def test_file_edit_replace_rejects_unsafe_paths(relative_path):
    gateway, issued = build_file_edit_gate()

    assert_denied(
        "invalid_argument",
        lambda: gateway.authorize(
            lease_token=issued.token,
            operation_id="file.edit.replace",
            arguments=edit_request(relative_path=relative_path),
        ),
    )


def test_file_edit_replace_cannot_edit_unleased_file():
    gateway, issued = build_file_edit_gate()

    assert_denied(
        "scope_violation",
        lambda: gateway.authorize(
            lease_token=issued.token,
            operation_id="file.edit.replace",
            arguments=edit_request(relative_path="src/other.py"),
        ),
    )


@pytest.mark.parametrize("field", ["roots", "repo_root", "credential", "opener"])
def test_file_edit_replace_cannot_supply_trust_anchor(field):
    gateway, issued = build_file_edit_gate()
    args = edit_request()
    args[field] = "attacker-controlled"

    assert_denied(
        "trusted_binding_override",
        lambda: gateway.authorize(
            lease_token=issued.token,
            operation_id="file.edit.replace",
            arguments=args,
        ),
    )


def test_file_edit_replace_respects_text_bound():
    gateway, issued = build_file_edit_gate()

    assert_denied(
        "scope_violation",
        lambda: gateway.authorize(
            lease_token=issued.token,
            operation_id="file.edit.replace",
            arguments=edit_request(new_str="x" * 101),
        ),
    )
