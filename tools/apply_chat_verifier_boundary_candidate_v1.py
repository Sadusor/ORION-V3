"""Apply candidate chat verifier integration only in an isolated clean checkout."""
from pathlib import Path
import sys

def main():
    root=Path(__file__).resolve().parents[1]
    path=root/"src/orion_v3/product_server.py"
    before=path.read_text(encoding="utf-8")
    old_import="from modules.history_archive_delete_guard_v1 import OwnerDeleteLedgerV1"
    new_import="from modules.owner_question_verifier_boundary_v1 import OwnerQuestionVerifierBoundaryV1\n"+old_import
    old="brain=RepoAwareChatBrain(verifier=VerifierReliabilityV1()),"
    new="brain=RepoAwareChatBrain(verifier=OwnerQuestionVerifierBoundaryV1()),"
    if before.count(old_import)!=1 or before.count(old)!=1:
        raise SystemExit("Integration anchors mismatch; no files changed")
    updated=before.replace(old_import,new_import,1).replace(old,new,1)
    compile(updated,str(path),"exec")
    path.write_text(updated,encoding="utf-8")
    print("CHAT_BOUNDARY_CANDIDATE_INTEGRATION> APPLIED_IN_ISOLATED_CHECKOUT")
if __name__=="__main__":
    main()
