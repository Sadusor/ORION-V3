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
        if (intent.getBooleanExtra("usb_sync_qualification", false)) {
            Thread {
                try {
                    val project = "orion2-usb-qualification"
                    val token = intent.getStringExtra("device_secret") ?: ""
                    check(token.length >= 32)
                    val store = ChatHistoryStore(this)
                    try {
                        val payload = JSONObject().put("conversations", JSONArray().put(
                            JSONObject().put("id", "usb-q-1").put("project_id", project)
                                .put("title", "USB qualification").put("created_at_ms", 1)
                                .put("updated_at_ms", 2))).put("messages", JSONArray().put(
                            JSONObject().put("id", "usb-m-1").put("conversation_id", "usb-q-1")
                                .put("role", "user").put("text", "hello").put("created_at_ms", 2)))
                        store.merge(payload.toString())
                        fun sync(): JSONObject {
                            val body = ArchiveDeviceReconcileV1.prepare(project, store.snapshot())
                            val conn = java.net.URL("http://127.0.0.1:18765/api/history-archive/device-sync")
                                .openConnection() as java.net.HttpURLConnection
                            try {
                                conn.requestMethod = "POST"
                                conn.connectTimeout = 5000
                                conn.readTimeout = 5000
                                conn.doOutput = true
                                conn.setRequestProperty("Content-Type", "application/json")
                                conn.setRequestProperty("X-Orion-Archive-Device", token)
                                conn.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
                                check(conn.responseCode == 200)
                                return JSONObject(conn.inputStream.bufferedReader().use { it.readText() })
                            } finally { conn.disconnect() }
                        }
                        val first = sync()
                        check(first.optBoolean("ok"))
                        check(ArchiveDeviceReconcileV1.removedIds(first).isEmpty())
                        Log.i("ORION2_USB_QUAL", "SYNC_PASS")
                        val second = sync()
                        val removed = ArchiveDeviceReconcileV1.removedIds(second)
                        check("usb-q-1" in removed)
                        store.applyArchiveTombstones(project, removed)
                        store.merge(payload.toString())
                        check(!store.snapshot().getJSONArray("conversations").toString().contains("usb-q-1"))
                    } finally { store.close() }
                    val again = ChatHistoryStore(this)
                    try {
                        check(!again.snapshot().getJSONArray("conversations").toString().contains("usb-q-1"))
                    } finally { again.close() }
                    Log.i("ORION2_USB_QUAL", "DELETE_REPLAY_PASS")
                    Log.i("ORION2_USB_QUAL", "PASS")
                } catch (t: Throwable) {
                    Log.e("ORION2_USB_QUAL", "FAIL " + (t.message ?: t.javaClass.simpleName), t)
                } finally { runOnUiThread { finish() } }
            }.start()
            return
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
