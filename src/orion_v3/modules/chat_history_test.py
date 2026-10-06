from __future__ import annotations

import pathlib
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
PARENT = HERE.parent
import sys
if str(PARENT) not in sys.path:
    sys.path.insert(0, str(PARENT))

from modules.chat_history import ChatHistoryStore


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        store = ChatHistoryStore(pathlib.Path(tmp) / "history.sqlite3")
        first = store.sync(
            {
                "conversations": [
                    {
                        "id": "c1",
                        "title": "First",
                        "project_id": "orion-v3",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 1000,
                    }
                ],
                "messages": [
                    {
                        "id": "m1",
                        "conversation_id": "c1",
                        "role": "user",
                        "text": "hello",
                        "source": "phone",
                        "created_at_ms": 1001,
                    }
                ],
            }
        )
        assert len(first["conversations"]) == 1
        assert len(first["messages"]) == 1

        # Re-sending a message is idempotent, and newer metadata wins.
        second = store.sync(
            {
                "conversations": [
                    {
                        "id": "c1",
                        "title": "Renamed",
                        "project_id": "orion-v3",
                        "pinned": 1,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 2000,
                    }
                ],
                "messages": [
                    {
                        "id": "m1",
                        "conversation_id": "c1",
                        "role": "user",
                        "text": "hello",
                        "source": "phone",
                        "created_at_ms": 1001,
                    },
                    {
                        "id": "m2",
                        "conversation_id": "c1",
                        "role": "assistant",
                        "text": "hi",
                        "source": "pc",
                        "created_at_ms": 2001,
                    },
                ],
            }
        )
        assert second["conversations"][0]["title"] == "Renamed"
        assert second["conversations"][0]["pinned"] == 1
        assert [m["id"] for m in second["messages"]] == ["m1", "m2"]

        # Older metadata cannot resurrect a newer tombstone.
        store.sync(
            {
                "conversations": [
                    {
                        "id": "c1",
                        "title": "Renamed",
                        "project_id": "orion-v3",
                        "pinned": 1,
                        "archived": 0,
                        "deleted": 1,
                        "created_at_ms": 1000,
                        "updated_at_ms": 3000,
                    }
                ]
            }
        )
        final = store.sync(
            {
                "conversations": [
                    {
                        "id": "c1",
                        "title": "Old copy",
                        "project_id": "",
                        "pinned": 0,
                        "archived": 0,
                        "deleted": 0,
                        "created_at_ms": 1000,
                        "updated_at_ms": 2500,
                    }
                ]
            }
        )
        assert final["conversations"][0]["deleted"] == 1
        assert final["conversations"][0]["title"] == "Renamed"

    print("CHAT_HISTORY_MODULE> PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
