"""Stand-alone V2 index security and correctness gates (no production state)."""
import pathlib
import tempfile
from .memory_indexed_retrieval_v2 import IndexedRecord, IndexedRetrievalV2

def main():
    with tempfile.TemporaryDirectory(prefix="orion-indexed-v2-test-") as d:
        index = IndexedRetrievalV2(pathlib.Path(d) / "derived.sqlite")
        index.rebuild([
            IndexedRecord("a1", "project-a", "ATLAS blue folders", "user:msg-1"),
            IndexedRecord("b1", "project-b", "ATLAS red folders", "user:msg-2"),
            IndexedRecord("inactive", "project-a", "ATLAS retired", "user:msg-3", active=False),
        ])
        a = index.candidates("ATLAS blue", project_id="project-a")
        assert a and a[0].memory_id == "a1"
        assert all(h.project_id == "project-a" for h in a)
        assert not index.candidates("retired", project_id="project-a")
        assert not index.candidates("red", project_id="project-a")
        try:
            index.candidates("ATLAS", project_id="")
        except ValueError:
            pass
        else:
            raise AssertionError("Missing project must fail closed")
        assert index.candidates('ATLAS" OR "red', project_id="project-a")
        index.rebuild([IndexedRecord("b2", "project-b", "NOVA green", "user:msg-4")])
        assert not index.candidates("ATLAS", project_id="project-a")
    print("ORION_INDEXED_RETRIEVAL_V2> PASS")
if __name__ == "__main__":
    main()
