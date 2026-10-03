from __future__ import annotations

import json

import pytest

from orion_v3.authoring import AuthoringPreflightError, preflight_paths, require_preflight


def test_python_syntax_preflight_rejects_literal_escaped_newline_import(tmp_path):
    path = tmp_path / "broken.py"
    path.write_text(
        "from math import (\\n    sqrt,\\n)\\n",
        encoding="utf-8",
    )

    findings = preflight_paths(tmp_path, ["broken.py"])

    assert len(findings) == 1
    assert findings[0].code == "python_syntax_error"
    assert findings[0].path == "broken.py"


def test_python_syntax_preflight_accepts_valid_source(tmp_path):
    path = tmp_path / "valid.py"
    path.write_text(
        "from math import (\n    sqrt,\n)\n\nVALUE = sqrt(9)\n",
        encoding="utf-8",
    )

    assert preflight_paths(tmp_path, ["valid.py"]) == ()


def test_json_preflight_rejects_invalid_json(tmp_path):
    path = tmp_path / "broken.json"
    path.write_text('{"ok": true,,}', encoding="utf-8")

    with pytest.raises(AuthoringPreflightError) as exc:
        require_preflight(tmp_path, ["broken.json"])

    assert exc.value.findings[0].code == "json_syntax_error"


def test_json_preflight_accepts_valid_json(tmp_path):
    path = tmp_path / "valid.json"
    path.write_text(json.dumps({"ok": True}), encoding="utf-8")

    require_preflight(tmp_path, ["valid.json"])


def test_preflight_rejects_path_escape(tmp_path):
    with pytest.raises(ValueError):
        require_preflight(tmp_path, ["../outside.py"])
