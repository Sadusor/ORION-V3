package com.sadusor.orionv3.history

import android.app.Activity
import android.os.Bundle
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Isolated ORION2-only USB-reversed HTTP qualification. Never compiled into a live action. */
class ArchiveSyncQualificationActivity : Activity() {
    private val tag = "ORION2_SYNC_QUAL"
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (packageName != "com.sadusor.orionv3.archivequal") {
            Log.e(tag, "FAIL wrong package")
            finish()
            return
        }
        val credential = intent.getStringExtra("test_device_credential") ?: ""
        if (credential.length < 32) {
            Log.e(tag, "FAIL missing test credential")
            finish()
            return
        }
        Thread {
            try {
                val project = "orion2-usb-qualification"
                val conversation = "orion2-usb-conversation"
                val store = ChatHistoryStore(this)
                try {
                    val local = JSONObject().put("conversations", JSONArray().put(
                        JSONObject().put("id", conversation).put("project_id", project)
                            .put("title", "USB sync test").put("created_at_ms", 10)
                            .put("updated_at_ms", 11)))
                        .put("messages", JSONArray().put(
                            JSONObject().put("id", "orion2-usb-message")
                                .put("conversation_id", conversation).put("role", "user")
                                .put("text", "USB archive qualification").put("created_at_ms", 11)))
                    store.merge(local.toString())
                    check(store.snapshot().getJSONArray("conversations")
                        .toString().contains(conversation)) { "seed missing" }
                    fun sync(): JSONObject {
                        val body = ArchiveDeviceReconcileV1.prepare(project, store.snapshot())
                        val conn = URL("http://127.0.0.1:18765/api/history-archive/device-sync")
                            .openConnection() as HttpURLConnection
                        try {
                            conn.requestMethod = "POST"
                            conn.connectTimeout = 5000
                            conn.readTimeout = 5000
                            conn.doOutput = true
                            conn.setRequestProperty("Content-Type", "application/json")
                            conn.setRequestProperty("X-Orion-Archive-Device", credential)
                            conn.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
                            check(conn.responseCode == 200) { "sync HTTP " + conn.responseCode }
                            return JSONObject(conn.inputStream.bufferedReader().use { it.readText() })
                        } finally { conn.disconnect() }
                    }
                    val first = sync()
                    check(first.optBoolean("ok")) { "initial sync rejected" }
                    check(ArchiveDeviceReconcileV1.removedIds(first).isEmpty()) { "unexpected early tombstone" }
                    Log.i(tag, "DEVICE_TO_PC_SYNC_PASS")
                    // Test server issues owner-authorized deletion after accepting first sync.
                    val second = sync()
                    check(second.optBoolean("ok")) { "reconciliation denied" }
                    val removed = ArchiveDeviceReconcileV1.removedIds(second)
                    check(conversation in removed) { "owner tombstone not returned" }
                    store.applyArchiveTombstones(project, removed)
                    check(!store.snapshot().getJSONArray("conversations").toString().contains(conversation))
                    Log.i(tag, "PC_TO_DEVICE_DELETE_PASS")
                    // Old offline phone content must not resurrect after a restart.
                    store.merge(local.toString())
                    check(!store.snapshot().getJSONArray("conversations").toString().contains(conversation))
                } finally { store.close() }
                val reopened = ChatHistoryStore(this)
                try {
                    check(!reopened.snapshot().getJSONArray("conversations")
                        .toString().contains("orion2-usb-conversation"))
                } finally { reopened.close() }
                Log.i(tag, "REPLAY_AFTER_RESTART_PASS")
                Log.i(tag, "PASS")
            } catch (t: Throwable) {
                Log.e(tag, "FAIL " + (t.message ?: t.javaClass.simpleName), t)
            } finally { runOnUiThread { finish() } }
        }.start()
    }
}
