package com.sadusor.orionv3.online

import android.app.Activity
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Environment
import android.provider.Settings
import android.webkit.JavascriptInterface
import android.webkit.WebView
import androidx.core.content.FileProvider
import com.sadusor.orionv3.history.ChatHistoryStore
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.util.UUID

private const val ORION_BASE_URL = "http://10.109.233.27:8890"
private const val PREFS = "orion_phone"
private const val TOKEN_KEY = "orion_pc_token"
private const val ZEROTIER_PACKAGE = "com.zerotier.one"

class OrionPcBridge(
    private val activity: Activity,
    private val webView: WebView,
    private val historyStore: ChatHistoryStore,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    private val prefs = activity.getSharedPreferences(PREFS, Context.MODE_PRIVATE)

    @JavascriptInterface
    fun refresh(requestId: String): String {
        val id = requestId.ifBlank { UUID.randomUUID().toString() }
        scope.launch {
            val payload = withContext(Dispatchers.IO) { refreshNow() }
            emit("ORION_PC_STATUS_RESULT", id, payload)
        }
        return id
    }

    @JavascriptInterface
    fun pair(code: String, requestId: String): String {
        val id = requestId.ifBlank { UUID.randomUUID().toString() }
        scope.launch {
            val payload = withContext(Dispatchers.IO) {
                try {
                    val response = request(
                        "POST",
                        "/api/pair",
                        JSONObject().put("code", code.trim()),
                        authenticated = false,
                        timeoutMs = 6000,
                    )
                    val token = response.body.optString("token")
                    if (!response.ok || token.isBlank()) {
                        JSONObject()
                            .put("ok", false)
                            .put("error", response.error.ifBlank { "Pairing failed." })
                    } else {
                        prefs.edit().putString(TOKEN_KEY, token).apply()
                        JSONObject().put("ok", true)
                    }
                } catch (t: Throwable) {
                    JSONObject().put("ok", false).put("error", t.message ?: "Pairing failed.")
                }
            }
            emit("ORION_PC_ACTION_RESULT", id, payload)
            if (payload.optBoolean("ok")) {
                val status = withContext(Dispatchers.IO) { refreshNow() }
                emit("ORION_PC_STATUS_RESULT", "auto", status)
                syncHistory("auto-sync")
            }
        }
        return id
    }

    @JavascriptInterface
    fun forgetPairing(requestId: String): String {
        val id = requestId.ifBlank { UUID.randomUUID().toString() }
        prefs.edit().remove(TOKEN_KEY).apply()
        val payload = JSONObject().put("ok", true)
        emit("ORION_PC_ACTION_RESULT", id, payload)
        refresh("auto")
        return id
    }

    @JavascriptInterface
    fun syncHistory(requestId: String): String {
        val id = requestId.ifBlank { UUID.randomUUID().toString() }
        scope.launch {
            val payload = withContext(Dispatchers.IO) {
                val token = token()
                if (token.isBlank()) {
                    JSONObject().put("ok", false).put("error", "Pair with ORION PC first.")
                } else {
                    try {
                        val local = historyStore.snapshot()
                        val response = request(
                            "POST",
                            "/api/chat-history/sync",
                            local,
                            authenticated = true,
                            timeoutMs = 8000,
                        )
                        if (!response.ok) {
                            JSONObject().put("ok", false).put("error", response.error)
                        } else {
                            historyStore.merge(response.body.toString())
                            JSONObject().put("ok", true).put("history", historyStore.snapshot())
                        }
                    } catch (t: Throwable) {
                        JSONObject().put("ok", false).put("error", t.message ?: "History sync failed.")
                    }
                }
            }
            emit("ORION_PC_HISTORY_RESULT", id, payload)
        }
        return id
    }

    @JavascriptInterface
    fun ask(requestJson: String): String {
        val request = try {
            JSONObject(requestJson)
        } catch (_: Throwable) {
            JSONObject()
        }
        val id = request.optString("id").ifBlank { UUID.randomUUID().toString() }
        val conversationId = request.optString("conversation_id").trim()
        val text = request.optString("text").trim()
        val model = request.optString("model").trim()

        if (text.isBlank() || model.isBlank()) {
            emitChat(id, "", true, "Missing text or PC model.")
            return id
        }

        scope.launch {
            withContext(Dispatchers.IO) {
                try {
                    val context = if (conversationId.isBlank()) {
                        ""
                    } else {
                        historyStore.contextFor(conversationId, text)
                    }
                    val goal = if (context.isBlank()) {
                        text
                    } else {
                        "Conversation context from the owner's local chat memory:\n" +
                            context +
                            "\n\nAnswer the latest user message in that context."
                    }
                    val start = request(
                        "POST",
                        "/api/local-hand/draft",
                        JSONObject()
                            .put("goal", goal)
                            .put("model", model)
                            .put("memory_query", text)
                            .put("conversation_id", conversationId),
                        authenticated = true,
                        timeoutMs = 10000,
                    )
                    if (!start.ok) {
                        emitChat(id, "", true, start.error.ifBlank { "ORION PC rejected the request." })
                        return@withContext
                    }

                    var last = ""
                    val deadline = System.currentTimeMillis() + 150_000L
                    while (System.currentTimeMillis() < deadline) {
                        val status = request(
                            "GET",
                            "/api/status",
                            null,
                            authenticated = true,
                            timeoutMs = 5000,
                        )
                        if (!status.ok) {
                            emitChat(id, last, true, status.error.ifBlank { "Lost connection to ORION PC." })
                            return@withContext
                        }

                        val lane = status.body.optJSONObject("local_hand_lane") ?: JSONObject()
                        val state = lane.optString("brain_state")
                        val preview = lane.optString("brain_stream_preview")
                        if (preview.isNotBlank() && preview != last) {
                            last = preview
                            emitChat(id, preview, false, null)
                        }

                        when (state) {
                            "ready" -> {
                                val answer = lane.optString("brain_conclusion").ifBlank { last }
                                emitChat(id, answer, true, null)
                                syncHistory("after-pc-chat")
                                return@withContext
                            }
                            "blocked", "error" -> {
                                emitChat(
                                    id,
                                    last,
                                    true,
                                    lane.optString("brain_error").ifBlank { "ORION verifier blocked the reply." },
                                )
                                return@withContext
                            }
                        }
                        delay(250)
                    }
                    emitChat(id, last, true, "ORION PC timed out.")
                } catch (t: Throwable) {
                    emitChat(id, "", true, t.message ?: "ORION PC request failed.")
                }
            }
        }
        return id
    }

    @JavascriptInterface
    fun openZeroTier(): Boolean {
        return try {
            val launchIntent = activity.packageManager.getLaunchIntentForPackage(ZEROTIER_PACKAGE)
            if (launchIntent != null) {
                launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                activity.startActivity(launchIntent)
                true
            } else {
                activity.startActivity(
                    Intent(
                        Intent.ACTION_VIEW,
                        Uri.parse("market://details?id=$ZEROTIER_PACKAGE"),
                    ).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                )
                false
            }
        } catch (_: ActivityNotFoundException) {
            false
        }
    }

    @JavascriptInterface
    fun updateOrion(requestId: String): String {
        val id = requestId.ifBlank { UUID.randomUUID().toString() }
        scope.launch {
            val payload = withContext(Dispatchers.IO) {
                try {
                    val response = request(
                        "POST",
                        "/api/update/main",
                        JSONObject(),
                        authenticated = true,
                        timeoutMs = 30000,
                    )
                    if (!response.ok) {
                        JSONObject().put("ok", false).put("error", response.error)
                    } else {
                        JSONObject().put("ok", true).put("update", response.body.optJSONObject("update"))
                    }
                } catch (t: Throwable) {
                    JSONObject().put("ok", false).put("error", t.message ?: "Update request failed.")
                }
            }
            emit("ORION_PC_ACTION_RESULT", id, payload)
        }
        return id
    }

    @JavascriptInterface
    fun installLatestApk(requestId: String): String {
        val id = requestId.ifBlank { UUID.randomUUID().toString() }
        scope.launch {
            val payload = withContext(Dispatchers.IO) {
                try {
                    if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O &&
                        !activity.packageManager.canRequestPackageInstalls()
                    ) {
                        activity.runOnUiThread {
                            activity.startActivity(
                                Intent(
                                    Settings.ACTION_MANAGE_UNKNOWN_APP_SOURCES,
                                    Uri.parse("package:${activity.packageName}"),
                                ),
                            )
                        }
                        return@withContext JSONObject()
                            .put("ok", false)
                            .put("permission", true)
                            .put("error", "Allow ORION to install updates, then tap Install latest APK again.")
                    }

                    val response = rawRequest(
                        "GET",
                        "/apk",
                        authenticated = true,
                        timeoutMs = 120_000,
                    )
                    if (response.code !in 200..299) {
                        response.connection.disconnect()
                        return@withContext JSONObject().put("ok", false).put("error", response.error)
                    }

                    val dir = activity.getExternalFilesDir(Environment.DIRECTORY_DOWNLOADS)
                        ?: activity.cacheDir
                    dir.mkdirs()
                    val apk = File(dir, "ORION-V3-update.apk")
                    FileOutputStream(apk).use { out ->
                        response.connection.inputStream.use { input ->
                            input.copyTo(out, 1024 * 1024)
                            out.fd.sync()
                        }
                    }
                    response.connection.disconnect()

                    activity.runOnUiThread {
                        val uri = FileProvider.getUriForFile(
                            activity,
                            activity.packageName + ".files",
                            apk,
                        )
                        val intent = Intent(Intent.ACTION_VIEW).apply {
                            setDataAndType(uri, "application/vnd.android.package-archive")
                            addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
                            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                        }
                        activity.startActivity(intent)
                    }
                    JSONObject().put("ok", true)
                } catch (t: Throwable) {
                    JSONObject().put("ok", false).put("error", t.message ?: "APK install failed.")
                }
            }
            emit("ORION_PC_ACTION_RESULT", id, payload)
        }
        return id
    }

    fun close() {
        scope.cancel()
    }

    private fun token(): String = prefs.getString(TOKEN_KEY, "") ?: ""

    private fun refreshNow(): JSONObject {
        return try {
            val health = request(
                "GET",
                "/api/health",
                null,
                authenticated = false,
                timeoutMs = 1800,
            )
            if (!health.ok) {
                return JSONObject()
                    .put("ok", true)
                    .put("reachable", false)
                    .put("paired", token().isNotBlank())
                    .put("connected", false)
                    .put("models", JSONObject.NULL)
                    .put("update", JSONObject.NULL)
            }

            if (token().isBlank()) {
                return JSONObject()
                    .put("ok", true)
                    .put("reachable", true)
                    .put("paired", false)
                    .put("connected", false)
                    .put("running_commit", health.body.optString("running_commit"))
                    .put("models", JSONObject.NULL)
                    .put("update", JSONObject.NULL)
            }

            val status = request(
                "GET",
                "/api/status",
                null,
                authenticated = true,
                timeoutMs = 3500,
            )
            if (!status.ok) {
                if (status.code == 401) prefs.edit().remove(TOKEN_KEY).apply()
                return JSONObject()
                    .put("ok", true)
                    .put("reachable", true)
                    .put("paired", false)
                    .put("connected", false)
                    .put("error", status.error)
            }

            val models = request(
                "GET",
                "/api/models",
                null,
                authenticated = true,
                timeoutMs = 3500,
            )
            val update = request(
                "GET",
                "/api/update/status",
                null,
                authenticated = true,
                timeoutMs = 3500,
            )

            JSONObject()
                .put("ok", true)
                .put("reachable", true)
                .put("paired", true)
                .put("connected", true)
                .put("running_commit", health.body.optString("running_commit"))
                .put(
                    "models",
                    if (models.ok) models.body.optJSONArray("models") else JSONObject.NULL,
                )
                .put(
                    "default_model",
                    if (models.ok) models.body.optString("default_model") else "",
                )
                .put("update", if (update.ok) update.body else JSONObject.NULL)
        } catch (_: Throwable) {
            JSONObject()
                .put("ok", true)
                .put("reachable", false)
                .put("paired", token().isNotBlank())
                .put("connected", false)
                .put("models", JSONObject.NULL)
                .put("update", JSONObject.NULL)
        }
    }

    private data class JsonResponse(
        val ok: Boolean,
        val code: Int,
        val body: JSONObject,
        val error: String,
    )

    private data class RawResponse(
        val code: Int,
        val connection: HttpURLConnection,
        val error: String,
    )

    private fun request(
        method: String,
        path: String,
        body: JSONObject?,
        authenticated: Boolean,
        timeoutMs: Int,
    ): JsonResponse {
        val raw = rawRequest(method, path, authenticated, timeoutMs, body)
        val text = try {
            val stream = if (raw.code in 200..299) raw.connection.inputStream else raw.connection.errorStream
            stream?.bufferedReader(Charsets.UTF_8)?.use { it.readText() } ?: "{}"
        } finally {
            raw.connection.disconnect()
        }
        val parsed = try {
            JSONObject(text.ifBlank { "{}" })
        } catch (_: Throwable) {
            JSONObject()
        }
        val error = parsed.optString("error").ifBlank { raw.error }
        return JsonResponse(raw.code in 200..299, raw.code, parsed, error)
    }

    private fun rawRequest(
        method: String,
        path: String,
        authenticated: Boolean,
        timeoutMs: Int,
        body: JSONObject? = null,
    ): RawResponse {
        val conn = URL(ORION_BASE_URL + path).openConnection() as HttpURLConnection
        conn.connectTimeout = timeoutMs
        conn.readTimeout = timeoutMs
        conn.requestMethod = method
        conn.useCaches = false
        conn.setRequestProperty("Accept", "application/json")
        if (authenticated) {
            val token = token()
            if (token.isBlank()) {
                conn.disconnect()
                throw IllegalStateException("Pair with ORION PC first.")
            }
            conn.setRequestProperty("X-Orion-Token", token)
        }
        if (body != null && method != "GET") {
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json")
            conn.outputStream.use { it.write(body.toString().toByteArray(Charsets.UTF_8)) }
        }
        val code = conn.responseCode
        return RawResponse(
            code = code,
            connection = conn,
            error = if (code in 200..299) "" else "ORION PC returned HTTP $code",
        )
    }

    private fun emit(function: String, requestId: String, payload: JSONObject) {
        activity.runOnUiThread {
            val js =
                "window.$function&&window.$function(" +
                    JSONObject.quote(requestId) + "," +
                    payload.toString() +
                    ")"
            webView.evaluateJavascript(js, null)
        }
    }

    private fun emitChat(requestId: String, text: String, done: Boolean, error: String?) {
        activity.runOnUiThread {
            val js =
                "window.ORION_PC_CHAT_EVENT&&window.ORION_PC_CHAT_EVENT(" +
                    JSONObject.quote(requestId) + "," +
                    JSONObject.quote(text) + "," +
                    done + "," +
                    (error?.let(JSONObject::quote) ?: "null") +
                    ")"
            webView.evaluateJavascript(js, null)
        }
    }
}
