package com.sadusor.orionv3.offline

import android.app.Activity
import android.content.Context
import android.content.res.AssetManager
import android.webkit.JavascriptInterface
import android.webkit.WebView
import com.sadusor.orionv3.history.ChatHistoryStore
import dev.ffmpegkit.llama.Llama
import dev.ffmpegkit.llama.LlamaConfig
import dev.ffmpegkit.llama.LlamaModel
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import org.json.JSONArray
import org.json.JSONObject
import java.io.File
import java.io.FileOutputStream
import java.util.UUID

private const val MODEL_ASSET = "models/Qwen3-0.6B-Q4_0.gguf"
private const val MODEL_FILE = "Qwen3-0.6B-Q4_0.gguf"

class OfflineChatBridge(
    private val activity: Activity,
    private val webView: WebView,
    private val historyStore: ChatHistoryStore,
    private val onReconnect: () -> Unit,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)
    @Volatile private var model: LlamaModel? = null

    @JavascriptInterface
    fun ask(requestJson: String): String {
        val request = try {
            JSONObject(requestJson)
        } catch (_: Throwable) {
            JSONObject()
        }
        val requestId = request.optString("id").ifBlank { UUID.randomUUID().toString() }
        val conversationId = request.optString("conversation_id").trim()
        val text = request.optString("text").trim()
        if (conversationId.isEmpty() || text.isEmpty()) {
            emit(requestId, null, "Missing conversation or message.")
            return requestId
        }

        scope.launch {
            try {
                val context = historyStore.contextFor(conversationId, text)
                val prompt = buildPrompt(context.ifBlank { "User: $text" })
                val loaded = ensureModel()
                val result = Llama.complete(
                    loaded,
                    prompt = prompt,
                    systemPrompt = "You are ORION Pocket, a concise private offline assistant. Use the supplied current conversation and relevant same-scope prior chat context. Never claim to be connected to the PC or internet when offline.",
                    maxTokens = 256,
                )
                val answer = result.text.trim()
                if (answer.isEmpty()) throw IllegalStateException("Offline model returned no text.")
                historyStore.merge(
                    JSONObject()
                        .put(
                            "messages",
                            JSONArray().put(
                                JSONObject()
                                    .put("id", "m-" + UUID.randomUUID())
                                    .put("conversation_id", conversationId)
                                    .put("role", "assistant")
                                    .put("text", answer)
                                    .put("source", "phone-offline-qwen3-0.6b")
                                    .put("created_at_ms", System.currentTimeMillis()),
                            ),
                        )
                        .toString(),
                )
                emit(requestId, answer, null)
            } catch (t: Throwable) {
                emit(requestId, null, t.message ?: t.javaClass.simpleName)
            }
        }
        return requestId
    }

    @JavascriptInterface
    fun modelInfo(): String =
        JSONObject()
            .put("name", "Qwen3-0.6B")
            .put("quant", "Q4_0")
            .put("asset", MODEL_ASSET)
            .put("offline", true)
            .put("loaded", model != null)
            .toString()

    @JavascriptInterface
    fun reconnect() {
        activity.runOnUiThread(onReconnect)
    }

    fun close() {
        scope.cancel()
        model?.let { Llama.releaseModel(it) }
        model = null
    }

    private suspend fun ensureModel(): LlamaModel {
        model?.let { return it }
        val modelFile = withContext(Dispatchers.IO) { materializeModel(activity) }
        val threads = Runtime.getRuntime().availableProcessors().coerceIn(2, 4)
        val loaded = Llama.loadModel(
            modelFile.absolutePath,
            LlamaConfig(
                contextSize = 2048,
                threads = threads,
                gpuLayers = 0,
                temperature = 0.55f,
                topP = 0.9f,
                topK = 40,
            ),
        )
        model = loaded
        return loaded
    }

    private fun materializeModel(context: Context): File {
        val dir = File(context.filesDir, "models").apply { mkdirs() }
        val dst = File(dir, MODEL_FILE)
        if (dst.isFile && dst.length() > 300_000_000L) return dst

        val tmp = File(dir, "$MODEL_FILE.partial")
        if (tmp.exists()) tmp.delete()
        context.assets.open(MODEL_ASSET, AssetManager.ACCESS_STREAMING).use { input ->
            FileOutputStream(tmp).use { output ->
                input.copyTo(output, bufferSize = 1024 * 1024)
                output.fd.sync()
            }
        }
        if (!tmp.renameTo(dst)) {
            tmp.copyTo(dst, overwrite = true)
            tmp.delete()
        }
        return dst
    }

    private fun buildPrompt(context: String): String =
        """
        /no_think
        Conversation so far:
        $context

        Answer the latest User message. Be concise and useful. If the context does not contain enough information, say what is missing.
        """.trimIndent()

    private fun emit(requestId: String, answer: String?, error: String?) {
        activity.runOnUiThread {
            val js =
                "window.ORION_OFFLINE_RESULT&&window.ORION_OFFLINE_RESULT(" +
                    JSONObject.quote(requestId) + "," +
                    (answer?.let(JSONObject::quote) ?: "null") + "," +
                    (error?.let(JSONObject::quote) ?: "null") +
                    ")"
            webView.evaluateJavascript(js, null)
        }
    }
}
