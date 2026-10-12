"""Shared query interpretation for authorized source and document retrieval."""
from orion_v3.modules.orion_understanding_v1 import interpret, rank_source_path
from orion_v3.modules.gitea_multi_repo_chat_v1 import named_repo_scope


def test_database_questions_expand_search_terms():
    understood = interpret("Do you understand my databases and SQL tables?")
    assert understood.intent == "source_lookup"
    assert {"sql", "schema", "database", "table"}.issubset(set(understood.search_query.split()))


def test_database_path_priority_does_not_erase_other_intents():
    db = interpret("where is my database schema?")
    assert rank_source_path("src/schema.sql", concepts=db.concepts) > rank_source_path("docs/notes.md", concepts=db.concepts)
    ui = interpret("where is the button?")
    assert rank_source_path("ui/button.ts", concepts=ui.concepts) > rank_source_path("src/database.py", concepts=ui.concepts)


def test_explicit_gitea_database_question_uses_authorized_catalog(tmp_path):
    request = named_repo_scope("What databases exist in MyGitea2?", state_dir=tmp_path)
    assert request is not None
    assert request["kind"] == "cross_repository"
    assert len(request["catalog"]) == 2


def test_named_orion_remains_owned_by_default_route(tmp_path):
    assert named_repo_scope("Show the ORION-V3 database schema", state_dir=tmp_path) is None
