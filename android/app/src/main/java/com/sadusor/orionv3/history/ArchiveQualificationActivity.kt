package com.sadusor.orionv3.history

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.database.sqlite.SQLiteDatabase
import android.os.Bundle
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.io.File

/** Isolated-package-only, disposable on-device SQLite qualification. */
class ArchiveQualificationActivity : Activity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (packageName != "com.sadusor.orionv3.archivequal") {
            Log.e("ORION2_DB_QUAL", "FAIL: wrong package")
            finish()
            return
        }
        val base = applicationContext
        val isolated = object : ContextWrapper(base) {
            override fun getApplicationContext(): Context = this
            override fun getDatabasePath(name: String): File {
                require(name == "orion_chat_history.db")
                return base.getDatabasePath("orion2_disposable_qualification.db")
            }
        }
        Thread {
            val file = base.getDatabasePath("orion2_disposable_qualification.db")
            try {
                file.parentFile?.mkdirs()
                check(!file.exists()) { "Old qualification database exists; refusing overwrite" }
                val original = SQLiteDatabase.openOrCreateDatabase(file, null)
                try {
                    original.execSQL("CREATE TABLE conversations(id TEXT PRIMARY KEY,title TEXT NOT NULL DEFAULT '',project_id TEXT NOT NULL DEFAULT '',pinned INTEGER NOT NULL DEFAULT 0,archived INTEGER NOT NULL DEFAULT 0,deleted INTEGER NOT NULL DEFAULT 0,created_at_ms INTEGER NOT NULL,updated_at_ms INTEGER NOT NULL)")
                    original.execSQL("CREATE TABLE messages(id TEXT PRIMARY KEY,conversation_id TEXT NOT NULL,role TEXT NOT NULL,text TEXT NOT NULL,source TEXT NOT NULL DEFAULT '',created_at_ms INTEGER NOT NULL)")
                    original.execSQL("INSERT INTO conversations(id,title,project_id,created_at_ms,updated_at_ms) VALUES('qualification-1','original Ελληνικά','qual-project',1,2)")
                    original.execSQL("INSERT INTO messages(id,conversation_id,role,text,created_at_ms) VALUES('qualification-m','qualification-1','user','preserved message',1)")
                    original.version = 1
                } finally { original.close() }
                val store = ChatHistoryStore(isolated)
                try {
                    val upgraded = store.snapshot()
                    check(upgraded.getJSONArray("conversations").length() == 1)
                    check(upgraded.getJSONArray("conversations").getJSONObject(0).getString("title") == "original Ελληνικά")
                    check(upgraded.getJSONArray("messages").length() == 1)
                    check(store.readableDatabase.version == 2)
                    Log.i("ORION2_DB_QUAL", "MIGRATION_PASS")
                    store.applyArchiveTombstones("qual-project", setOf("qualification-1"))
                    check(store.snapshot().getJSONArray("conversations").length() == 0)
                    check(store.snapshot().getJSONArray("messages").length() == 0)
                } finally { store.close() }
                val restarted = ChatHistoryStore(isolated)
                try {
                    val replay = JSONObject().put("conversations", JSONArray().put(
                        JSONObject().put("id","qualification-1").put("title","replay")
                            .put("project_id","qual-project").put("created_at_ms",3).put("updated_at_ms",4)))
                        .put("messages", JSONArray().put(JSONObject().put("id","replay-m")
                            .put("conversation_id","qualification-1").put("role","user")
                            .put("text","offline stale").put("created_at_ms",4)))
                    restarted.merge(replay.toString())
                    check(restarted.snapshot().getJSONArray("conversations").length() == 0)
                    check(restarted.snapshot().getJSONArray("messages").length() == 0)
                    Log.i("ORION2_DB_QUAL", "DELETE_REPLAY_RESTART_PASS")
                } finally { restarted.close() }
                Log.i("ORION2_DB_QUAL", "PASS")
            } catch (t: Throwable) {
                Log.e("ORION2_DB_QUAL", "FAIL: " + (t.message ?: t.javaClass.name), t)
            } finally { runOnUiThread { finish() } }
        }.start()
    }
}
