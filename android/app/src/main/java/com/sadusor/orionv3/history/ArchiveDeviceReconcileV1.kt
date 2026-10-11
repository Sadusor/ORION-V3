package com.sadusor.orionv3.history

import org.json.JSONArray
import org.json.JSONObject

/**
 * Stage C experimental reconciliation preparation. Not called by the frozen
 * online bridge. Never interprets local deleted flags as owner authorization.
 * It prepares a project-scoped snapshot before authenticated archive sync.
 */
object ArchiveDeviceReconcileV1 {
    fun prepare(projectId: String, snapshot: JSONObject): JSONObject {
        require(projectId.isNotBlank() && projectId.length <= 160)
        val rawConversations = snapshot.optJSONArray("conversations")
            ?: throw IllegalArgumentException("Missing conversations")
        val rawMessages = snapshot.optJSONArray("messages")
            ?: throw IllegalArgumentException("Missing messages")
        require(rawConversations.length() <= 100 && rawMessages.length() <= 10000)

        val allowed = mutableSetOf<String>()
        val conversations = JSONArray()
        for (i in 0 until rawConversations.length()) {
            val row = rawConversations.optJSONObject(i)
                ?: throw IllegalArgumentException("Invalid conversation")
            val id = row.optString("id").trim()
            require(id.isNotEmpty() && id.length <= 120)
            require(row.optString("project_id") == projectId)
            require(allowed.add(id))
            conversations.put(JSONObject(row.toString()))
        }
        val messages = JSONArray()
        for (i in 0 until rawMessages.length()) {
            val row = rawMessages.optJSONObject(i)
                ?: throw IllegalArgumentException("Invalid message")
            val conversation = row.optString("conversation_id")
            require(conversation in allowed)
            messages.put(JSONObject(row.toString()))
        }
        return JSONObject().put("project_id", projectId).put(
            "snapshot", JSONObject().put("conversations", conversations)
                .put("messages", messages).put("schema", "orion.chat-history/1"))
    }

    /** Server response is advisory until independently authenticated by transport. */
    fun removedIds(response: JSONObject): Set<String> {
        require(response.optBoolean("ok", false))
        val values = response.optJSONArray("removed_conversation_ids")
            ?: throw IllegalArgumentException("Missing reconciliation result")
        require(values.length() <= 100)
        val ids = mutableSetOf<String>()
        for (i in 0 until values.length()) {
            val id = values.optString(i)
            require(id.isNotBlank() && id.length <= 120)
            require(ids.add(id))
        }
        return ids
    }
}
