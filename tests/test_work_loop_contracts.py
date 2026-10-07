from orion_v3.work_loop.contracts import Proposal


def test_proposal_hash_is_deterministic_and_content_bound():
    first = Proposal("p", "t", "filesystem.write", r"E:\\Work", {"path": "a.txt", "text": "one"})
    same = Proposal("p", "t", "filesystem.write", r"E:\\Work", {"text": "one", "path": "a.txt"})
    changed = Proposal("p", "t", "filesystem.write", r"E:\\Work", {"path": "a.txt", "text": "two"})
    assert first.proposal_hash == same.proposal_hash
    assert first.proposal_hash != changed.proposal_hash
