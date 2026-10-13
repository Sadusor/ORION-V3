"""Offline protocol compatibility gate for lossless chat candidate.

No Android runtime is started. This checks the Android JSON wire shape against
the Python candidate and documents remaining legacy Android limits explicitly.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"/"orion_v3"))
from modules.chat_history_lossless_candidate_v2 import LosslessHistoryCandidate


def conv(cid, ts, deleted=0):
    return {"id":cid,"title":"Conversation "+cid,"project_id":"orion-v3",
            "pinned":0,"archived":0,"deleted":deleted,
            "created_at_ms":ts,"updated_at_ms":ts}

def message(mid, cid, text, ts, role="user"):
    return {"id":mid,"conversation_id":cid,"role":role,
            "text":text,"source":"orion-pc","created_at_ms":ts}


class AndroidPcWireCompatibility(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="orion-wire-")
        self.addCleanup(temp.cleanup)
        self.store=LosslessHistoryCandidate(Path(temp.name)/"wire.sqlite3")

    def test_android_json_round_trip_and_persistence(self):
        phone={"schema":"orion.chat-history/1",
               "conversations":[conv("c-phone",1000)],
               "messages":[message("m-phone","c-phone","Γεια σου",1001)]}
        response=self.store.sync(json.loads(json.dumps(phone,ensure_ascii=False)))
        self.assertEqual(response["schema"],phone["schema"])
        self.assertTrue({"conversations","messages"}.issubset(response))
        self.assertEqual(response["messages"][0]["text"],"Γεια σου")
        pc={"conversations":[conv("c-pc",2000)],
            "messages":[message("m-pc","c-pc","Hello from PC",2001,"assistant")]}
        self.store.sync(pc)
        reopen=LosslessHistoryCandidate(self.store.path)
        self.assertEqual({m["id"] for m in reopen.snapshot()["messages"]},
                         {"m-phone","m-pc"})

    def test_repeated_sync_is_idempotent(self):
        payload={"conversations":[conv("c1",1000)],
                 "messages":[message("m1","c1","Hello",1001)]}
        self.store.sync(payload)
        self.store.sync(self.store.snapshot())
        self.assertEqual(len(self.store.snapshot()["messages"]),1)

    def test_tombstone_propagates_without_resurrection(self):
        self.store.sync({"conversations":[conv("c1",1000)]})
        self.store.sync({"conversations":[conv("c1",2000,deleted=1)]})
        self.store.sync({"conversations":[conv("c1",3000,deleted=0)]})
        self.assertEqual(self.store.snapshot()["conversations"][0]["deleted"],1)

    def test_existing_android_source_still_prunes_and_truncates(self):
        """Legacy incompatibilities must stay visible until Android is repaired."""
        src=(ROOT/"android/app/src/main/java/com/sadusor/orionv3/history/ChatHistoryStore.kt").read_text(encoding="utf-8")
        self.assertIn("MAX_CONVERSATIONS = 50",src)
        self.assertIn("MAX_TEXT_CHARS = 8_000",src)
        self.assertIn("prune(db)",src)
        self.assertIn("clean(raw.optString(\"text\"), MAX_TEXT_CHARS)",src)
        print("ANDROID_LEGACY_LIMITS> PRESENT; NO CROSS_DEVICE_LOSSLESS_CLAIM")

    def test_existing_http_wire_route_is_legacy_store(self):
        src=(ROOT/"src/orion_v3/product_server.py").read_text(encoding="utf-8")
        self.assertIn('if path == "/api/chat-history/sync":',src)
        self.assertIn("CHAT_HISTORY.sync(body)",src)
        self.assertIn("from modules.chat_history import ChatHistoryStore",src)
        print("SERVER_LEGACY_ROUTE> ACTIVE IN SOURCE; CANDIDATE NOT WIRED")


if __name__=="__main__":
    unittest.main(verbosity=2)
