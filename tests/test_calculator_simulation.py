from orion_v3.work_loop.calculator_simulation import simulate_calculator_milestone


def test_calculator_simulation_is_blocked_until_real_executor():
    result = simulate_calculator_milestone()
    assert result == {
        "status": "dry_run",
        "evidence_verdict": "indeterminate",
        "last_verified_result": "execution:indeterminate",
        "blocked": "true",
        "source_written": "false",
    }
