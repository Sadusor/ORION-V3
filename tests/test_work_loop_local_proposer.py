from orion_v3.work_loop.contracts import WorkState
from orion_v3.work_loop.local_proposer import propose_from_local_qwen
from orion_v3.work_loop.vault import ProjectVault

class FakeBrain:
    def _available_models(self):
        return ["qwen3.5-9b-orion"]
    def _choose_model(self, requested, models):
        return models[0]
    def _request_json(self, method, path, body, timeout):
        assert method == "POST" and path == "/api/generate"
        assert body["think"] is False
        return {"done": True, "response": '{"operation":"git.status","args":{}}'}

def test_qwen_proposal_is_canonical_and_read_only(tmp_path):
    vault = ProjectVault(tmp_path / "project")
    vault.initialize(WorkState(project_id="canonical", objective="inspect",
                               checkpoint="start", current_task="status"))
    p = propose_from_local_qwen(vault, brain=FakeBrain())
    assert p.project_id == "canonical"
    assert p.task_id == "status"
    assert p.workspace == str(vault.repo_path.resolve())
    assert p.operation == "git.status"
    assert vault.load().last_verified_result == "none"
    assert not list(vault.repo_path.iterdir())
