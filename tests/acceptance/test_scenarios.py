import json
from pathlib import Path
import pytest
from relay_api.evaluation.scenarios import run_scenario


@pytest.mark.parametrize("number", range(1, 9))
def test_mandatory_scenario(stack, number):
    result = run_scenario(stack[0], f"SCN-{number:03}")
    evidence = Path("evidence/current")
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / f"SCN-{number:03}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    assert result["status"] == "PASS", result["checks"]
    assert result["events"]
