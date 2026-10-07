package com.sadusor.orionv3.history

import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.database.sqlite.SQLiteOpenHelper
import android.webkit.JavascriptInterface
import org.json.JSONArray
import org.json.JSONObject

private const val DB_NAME = "orion_chat_history.db"
private const val DB_VERSION = 1
private const val MAX_CONVERSATIONS = 50
private const val MAX_MESSAGES_PER_CONVERSATION = 100
private const val MAX_TEXT_CHARS = 8_000
private const val MAX_TITLE_CHARS = 160

class ChatHistoryStore(context: Context) :
    SQLiteOpenHelper(context.applicationContext, DB_NAME, null, DB_VERSION) {

    override fun onCreate(db: SQLiteDatabase) {
        db.execSQL(
            """
            CREATE TABLE conversations(
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                project_id TEXT NOT NULL DEFAULT '',
                pinned INTEGER NOT NULL DEFAULT 0,
                archived INTEGER NOT NULL DEFAULT 0,
                deleted INTEGER NOT NULL DEFAULT 0,
                created_at_ms INTEGER NOT NULL,
                updated_at_ms INTEGER NOT NULL
            )
            """.trimIndent(),
        )
        db.execSQL(
            """
            CREATE TABLE messages(
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT '',
                created_at_ms INTEGER NOT NULL
            )
            """.trimIndent(),
        )
        db.execSQL("CREATE INDEX idx_conv_updated ON conversations(updated_at_ms DESC)")
        db.execSQL("CREATE INDEX idx_msg_conv_created ON messages(conversation_id, created_at_ms ASC)")
    }

    override fun onUpgrade(db: SQLiteDatabase, oldVersion: Int, newVersion: Int) = Unit

    @Synchronized
    fun merge(payloadJson: String): JSONObject {
        val payload = try {
            JSONObject(payloadJson)
        } catch (_: Throwable) {
            JSONObject()
        }
        val db = writableDatabase
        db.beginTransaction()
        try {
            val conversations = payload.optJSONArray("conversations") ?: JSONArray()
            for (i in 0 until minOf(conversations.length(), MAX_CONVERSATIONS * 2)) {
                val c = conversations.optJSONObject(i) ?: continue
                mergeConversation(db, c)
            }

            val messages = payload.optJSONArray("messages") ?: JSONArray()
            val messageLimit = MAX_CONVERSATIONS * MAX_MESSAGES_PER_CONVERSATION * 2
            for (i in 0 until minOf(messages.length(), messageLimit)) {
                val m = messages.optJSONObject(i) ?: continue
                mergeMessage(db, m)
            }
            prune(db)
            db.setTransactionSuccessful()
        } finally {
            db.endTransaction()
        }
        return snapshot()
    }

    private fun mergeConversation(db: SQLiteDatabase, raw: JSONObject) {
        val id = clean(raw.optString("id"), 120)
        if (id.isEmpty()) return
        val now = System.currentTimeMillis()
        val created = raw.optLong("created_at_ms", now)
        val updated = raw.optLong("updated_at_ms", created)
        val current = db.rawQuery(
            "SELECT updated_at_ms FROM conversations WHERE id=?",
            arrayOf(id),
        ).use { cursor -> if (cursor.moveToFirst()) cursor.getLong(0) else null }

        if (current != null && updated < current) return

        val title = clean(raw.optString("title"), MAX_TITLE_CHARS)
        val projectId = clean(raw.optString("project_id"), 160)
        val pinned = boolInt(raw, "pinned")
        val archived = boolInt(raw, "archived")
        val deleted = boolInt(raw, "deleted")

        if (current == null) {
            db.execSQL(
                """
                INSERT INTO conversations(id,title,project_id,pinned,archived,deleted,created_at_ms,updated_at_ms)
                VALUES(?,?,?,?,?,?,?,?)
                """.trimIndent(),
                arrayOf(id, title, projectId, pinned, archived, deleted, created, updated),
            )
        } else {
            db.execSQL(
                """
                UPDATE conversations SET
                    title=?, project_id=?, pinned=?, archived=?, deleted=?,
                    created_at_ms=min(created_at_ms,?), updated_at_ms=?
                WHERE id=?
                """.trimIndent(),
                arrayOf(title, projectId, pinned, archived, deleted, created, updated, id),
            )
        }
    }

    private fun mergeMessage(db: SQLiteDatabase, raw: JSONObject) {
        val id = clean(raw.optString("id"), 160)
        val conversationId = clean(raw.optString("conversation_id"), 120)
        val role = clean(raw.optString("role"), 20).lowercase()
        val text = clean(raw.optString("text"), MAX_TEXT_CHARS)
        if (id.isEmpty() || conversationId.isEmpty() || text.isEmpty()) return
        if (role !in setOf("user", "assistant", "system")) return

        val created = raw.optLong("created_at_ms", System.currentTimeMillis())
        val source = clean(raw.optString("source"), 80)
        ensureConversation(db, conversationId, created)

        // CHAT_SYNC_V1 parity with the PC store: the same completed ORION
        // assistant reply can arrive once from the live bridge and once from
        // shared-history sync with different message ids. Collapse only exact
        // ORION assistant duplicates inside a short window; user turns remain
        // strictly id-based.
        var duplicateAssistant = false
        if (role == "assistant" && source.startsWith("orion")) {
            duplicateAssistant = db.rawQuery(
                """
                SELECT 1 FROM messages
                WHERE conversation_id=?
                  AND role='assistant'
                  AND text=?
                  AND source LIKE 'orion%'
                  AND ABS(created_at_ms-?) <= 30000
                LIMIT 1
                """.trimIndent(),
                arrayOf(conversationId, text, created.toString()),
            ).use { cursor -> cursor.moveToFirst() }
        }

        if (!duplicateAssistant) {
            db.execSQL(
                """
                INSERT OR IGNORE INTO messages(id,conversation_id,role,text,source,created_at_ms)
                VALUES(?,?,?,?,?,?)
                """.trimIndent(),
                arrayOf(
                    id,
                    conversationId,
                    role,
                    text,
                    source,
                    created,
                ),
            )
        }
        db.execSQL(
            "UPDATE conversations SET updated_at_ms=max(updated_at_ms,?) WHERE id=?",
            arrayOf(created, conversationId),
        )
    }

    private fun ensureConversation(db: SQLiteDatabase, id: String, timestamp: Long) {
        db.execSQL(
            """
            INSERT OR IGNORE INTO conversations(
                id,title,project_id,pinned,archived,deleted,created_at_ms,updated_at_ms
            ) VALUES(?,?,?,?,?,?,?,?)
            """.trimIndent(),
            arrayOf(id, "", "", 0, 0, 0, timestamp, timestamp),
        )
    }

    private fun prune(db: SQLiteDatabase) {
        val removeConversations = mutableListOf<String>()
        db.rawQuery(
            """
            SELECT id FROM conversations
            ORDER BY pinned DESC, updated_at_ms DESC
            LIMIT -1 OFFSET ?
            """.trimIndent(),
            arrayOf(MAX_CONVERSATIONS.toString()),
        ).use { cursor ->
            while (cursor.moveToNext()) removeConversations += cursor.getString(0)
        }
        removeConversations.forEach { id ->
            db.delete("messages", "conversation_id=?", arrayOf(id))
            db.delete("conversations", "id=?", arrayOf(id))
        }

        val ids = mutableListOf<String>()
        db.rawQuery("SELECT id FROM conversations", null).use { cursor ->
            while (cursor.moveToNext()) ids += cursor.getString(0)
        }
        ids.forEach { conversationId ->
            val oldMessages = mutableListOf<String>()
            db.rawQuery(
                """
                SELECT id FROM messages WHERE conversation_id=?
                ORDER BY created_at_ms DESC
                LIMIT -1 OFFSET ?
                """.trimIndent(),
                arrayOf(conversationId, MAX_MESSAGES_PER_CONVERSATION.toString()),
            ).use { cursor ->
                while (cursor.moveToNext()) oldMessages += cursor.getString(0)
            }
            oldMessages.forEach { messageId ->
                db.delete("messages", "id=?", arrayOf(messageId))
            }
        }
    }

    @Synchronized
    fun snapshot(): JSONObject {
        val out = JSONObject()
        out.put("schema", "orion.chat-history/1")
        val conversations = JSONArray()
        val messages = JSONArray()
        val db = readableDatabase

        db.rawQuery(
            """
            SELECT id,title,project_id,pinned,archived,deleted,created_at_ms,updated_at_ms
            FROM conversations
            ORDER BY pinned DESC, updated_at_ms DESC
            LIMIT ?
            """.trimIndent(),
            arrayOf(MAX_CONVERSATIONS.toString()),
        ).use { cursor ->
            while (cursor.moveToNext()) {
                conversations.put(
                    JSONObject()
                        .put("id", cursor.getString(0))
                        .put("title", cursor.getString(1))
                        .put("project_id", cursor.getString(2))
                        .put("pinned", cursor.getInt(3))
                        .put("archived", cursor.getInt(4))
                        .put("deleted", cursor.getInt(5))
                        .put("created_at_ms", cursor.getLong(6))
                        .put("updated_at_ms", cursor.getLong(7)),
                )
            }
        }

        db.rawQuery(
            """
            SELECT id,conversation_id,role,text,source,created_at_ms
            FROM messages
            ORDER BY created_at_ms ASC
            """.trimIndent(),
            null,
        ).use { cursor ->
            while (cursor.moveToNext()) {
                messages.put(
                    JSONObject()
                        .put("id", cursor.getString(0))
                        .put("conversation_id", cursor.getString(1))
                        .put("role", cursor.getString(2))
                        .put("text", cursor.getString(3))
                        .put("source", cursor.getString(4))
                        .put("created_at_ms", cursor.getLong(5)),
                )
            }
        }

        out.put("conversations", conversations)
        out.put("messages", messages)
        out.put(
            "limits",
            JSONObject()
                .put("conversations", MAX_CONVERSATIONS)
                .put("messages_per_conversation", MAX_MESSAGES_PER_CONVERSATION),
        )
        return out
    }

    @Synchronized
    fun contextFor(
        conversationId: String,
        query: String,
        maxCurrentMessages: Int = 10,
        maxRelatedMessages: Int = 4,
        maxChars: Int = 6_000,
    ): String {
        if (conversationId.isBlank()) return ""
        val db = readableDatabase
        val scope = db.rawQuery(
            "SELECT project_id FROM conversations WHERE id=?",
            arrayOf(conversationId),
        ).use { cursor -> if (cursor.moveToFirst()) cursor.getString(0) else "" }

        val current = mutableListOf<Pair<String, String>>()
        db.rawQuery(
            """
            SELECT role,text FROM messages
            WHERE conversation_id=? AND role IN ('user','assistant')
            ORDER BY created_at_ms DESC
            LIMIT ?
            """.trimIndent(),
            arrayOf(conversationId, maxCurrentMessages.toString()),
        ).use { cursor ->
            while (cursor.moveToNext()) current += cursor.getString(0) to cursor.getString(1)
        }

        val builder = StringBuilder("Current conversation:\n")
        for ((role, text) in current.asReversed()) {
            val label = if (role == "user") "User" else "Assistant"
            val line = "$label: $text\n"
            if (builder.length + line.length > maxChars) break
            builder.append(line)
        }

        val terms = query
            .lowercase()
            .split(Regex("[^\\p{L}\\p{N}]+"))
            .filter { it.length >= 3 }
            .distinct()
            .take(8)
        if (terms.isEmpty() || builder.length >= maxChars) return builder.toString().trim()

        data class Candidate(val role: String, val text: String, val score: Int, val createdAt: Long)
        val candidates = mutableListOf<Candidate>()
        db.rawQuery(
            """
            SELECT m.role,m.text,m.created_at_ms
            FROM messages m
            JOIN conversations c ON c.id=m.conversation_id
            WHERE m.conversation_id<>?
              AND c.project_id=?
              AND c.deleted=0
              AND c.archived=0
              AND m.role IN ('user','assistant')
            ORDER BY c.pinned DESC, m.created_at_ms DESC
            LIMIT 240
            """.trimIndent(),
            arrayOf(conversationId, scope),
        ).use { cursor ->
            while (cursor.moveToNext()) {
                val text = cursor.getString(1)
                val lower = text.lowercase()
                val score = terms.count { lower.contains(it) }
                if (score > 0) {
                    candidates += Candidate(
                        role = cursor.getString(0),
                        text = text,
                        score = score,
                        createdAt = cursor.getLong(2),
                    )
                }
            }
        }

        val related = candidates
            .sortedWith(compareByDescending<Candidate> { it.score }.thenByDescending { it.createdAt })
            .take(maxRelatedMessages)
        if (related.isNotEmpty()) {
            builder.append("\nRelevant prior chat context (same scope):\n")
            for (item in related.asReversed()) {
                val label = if (item.role == "user") "User" else "Assistant"
                val line = "[Prior chat] $label: ${item.text}\n"
                if (builder.length + line.length > maxChars) break
                builder.append(line)
            }
        }
        return builder.toString().trim()
    }

    private fun clean(value: String?, limit: Int): String =
        (value ?: "").trim().take(limit)

    private fun boolInt(o: JSONObject, key: String): Int {
        val value = o.opt(key)
        return when (value) {
            is Boolean -> if (value) 1 else 0
            is Number -> if (value.toInt() != 0) 1 else 0
            is String -> if (value == "1" || value.equals("true", ignoreCase = true)) 1 else 0
            else -> 0
        }
    }
}

class ChatHistoryBridge(private val store: ChatHistoryStore) {
    @JavascriptInterface
    fun snapshot(): String = store.snapshot().toString()

    @JavascriptInterface
    fun merge(payloadJson: String): String = store.merge(payloadJson).toString()
}
