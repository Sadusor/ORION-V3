"""Cursor's Repair: FTS content must outrank filename-only matches."""
from unittest.mock import patch
from orion_v3.modules.gitea_relevance_v2 import search_relevant_context


def test_content_evidence_first_when_filename_matches_compete(tmp_path):
    import sqlite3
    db = tmp_path / "index.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("create table code_revision(project text, repository text, commit_sha text)")
        conn.execute("create table code_fts(project text, repository text, commit_sha text, path text, part text, text text)")
        conn.execute("insert into code_revision values ('orion-v3','MyGitea/ORION-V3',?)", ("a" * 40,))
        for i in range(8):
            conn.execute("insert into code_fts values ('orion-v3','MyGitea/ORION-V3',?,?,?,?)",
                         ("a" * 40, f"docs/database_schema_{i}.md", "0", "filename-only"))
    primary = {"path": "src/schema_reader.py", "part": 0, "source_commit": "a" * 40, "text": "CREATE TABLE actual_data(id INTEGER);"}
    with patch("orion_v3.modules.gitea_search_context_v1.search_code_context", return_value={"results": [primary]}):
        # The relevance module imports the function directly; patch that binding.
        with patch("orion_v3.modules.gitea_relevance_v2.search_code_context", return_value={"results": [primary]}):
            result = search_relevant_context(db, query="database schema", project="orion-v3",
                                             repository="MyGitea/ORION-V3", commit_sha="a" * 40, max_chars=150)
    assert result["results"][0]["path"] == primary["path"]
    assert result["results"][0]["text"] == primary["text"]


def test_index_revision_mismatch_fails_closed(tmp_path):
    import sqlite3
    db = tmp_path / "index.sqlite3"
    with sqlite3.connect(db) as conn:
        conn.execute("create table code_revision(project text, repository text, commit_sha text)")
        conn.execute("create table code_fts(project text, repository text, commit_sha text, path text, part text, text text)")
        conn.execute("insert into code_revision values ('orion-v3','MyGitea/ORION-V3',?)", ("b" * 40,))
    with patch("orion_v3.modules.gitea_relevance_v2.search_code_context", return_value={"results": []}):
        try:
            search_relevant_context(db, query="database schema", project="orion-v3",
                                    repository="MyGitea/ORION-V3", commit_sha="a" * 40)
        except ValueError as exc:
            assert "revision mismatch" in str(exc).lower()
        else:
            raise AssertionError("Stale index revision accepted")
