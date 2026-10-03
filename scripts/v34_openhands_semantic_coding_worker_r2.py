from __future__ import annotations

from types import SimpleNamespace

from openhands.sdk.conversation.impl.local_conversation import LocalConversation
from openhands.sdk.conversation.response_utils import get_agent_final_response

import v34_openhands_semantic_coding_worker as original


def _get_messages_compat(self: LocalConversation):
    final = get_agent_final_response(self.state.events)
    if not final:
        return []
    return [SimpleNamespace(content=final)]


if not hasattr(LocalConversation, "get_messages"):
    setattr(LocalConversation, "get_messages", _get_messages_compat)


if __name__ == "__main__":
    raise SystemExit(original.main())
