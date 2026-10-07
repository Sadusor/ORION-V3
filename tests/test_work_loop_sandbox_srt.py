from orion_v3.work_loop.sandbox_srt import work_hand_plan


def test_srt_plan_is_write_allowlist_and_network_deny_by_default(tmp_path):
    workspace = tmp_path / "work"
    plan = work_hand_plan(workspace)
    config = plan.as_config()
    assert config["filesystem"]["allowWrite"] == [str(workspace.resolve())]
    assert config["network"]["allowedDomains"] == []
    assert config["filesystem"]["allowGitConfig"] is False
    assert str(workspace.resolve() / ".git" / "hooks") in config["filesystem"]["denyWrite"]


def test_srt_network_requires_explicit_domains(tmp_path):
    plan = work_hand_plan(tmp_path / "work", network_domains=("github.com", "api.github.com"))
    assert plan.as_config()["network"]["allowedDomains"] == ["github.com", "api.github.com"]
