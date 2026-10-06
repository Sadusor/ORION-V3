package com.sadusor.orionv3

import android.annotation.SuppressLint
import android.app.Activity
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Bundle
import android.util.Log
import android.view.Gravity
import android.view.View
import android.widget.FrameLayout
import android.widget.TextView
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import com.sadusor.orionv3.history.ChatHistoryBridge
import com.sadusor.orionv3.history.ChatHistoryStore
import com.sadusor.orionv3.offline.OfflineChatBridge
import com.sadusor.orionv3.online.OrionPcBridge

private const val PHONE_BASE_URL = "https://orion.local/phone/"
private const val TAG = "ORIONV3"

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var statusView: TextView
    private lateinit var historyStore: ChatHistoryStore
    private lateinit var historyBridge: ChatHistoryBridge
    private var offlineChatBridge: OfflineChatBridge? = null
    private var pcBridge: OrionPcBridge? = null

    @SuppressLint("SetJavaScriptEnabled", "JavascriptInterface")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        historyStore = ChatHistoryStore(this)
        historyBridge = ChatHistoryBridge(historyStore)

        val root = FrameLayout(this).apply {
            setBackgroundColor(Color.rgb(5, 7, 11))
        }

        webView = WebView(this).apply {
            setBackgroundColor(Color.rgb(5, 7, 11))

            // Huawei / older Android WebView compatibility:
            // hardware compositing can produce an all-black surface on this device.
            setLayerType(View.LAYER_TYPE_SOFTWARE, null)

            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.allowFileAccess = false
            settings.allowContentAccess = false
            settings.setSupportZoom(false)
            settings.useWideViewPort = true
            settings.loadWithOverviewMode = false
            settings.cacheMode = WebSettings.LOAD_NO_CACHE
            settings.mediaPlaybackRequiresUserGesture = true

            addJavascriptInterface(historyBridge, "ORION_NATIVE_HISTORY")
            WebView.setWebContentsDebuggingEnabled(true)

            webChromeClient = object : WebChromeClient() {
                override fun onConsoleMessage(message: ConsoleMessage): Boolean {
                    Log.e(
                        TAG,
                        "JS " + message.message() +
                            " @" + message.sourceId() +
                            ":" + message.lineNumber(),
                    )
                    return true
                }
            }

            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(
                    view: WebView,
                    request: WebResourceRequest,
                ): Boolean {
                    return !request.url.toString().startsWith(PHONE_BASE_URL)
                }

                override fun onPageStarted(
                    view: WebView,
                    url: String,
                    favicon: Bitmap?,
                ) {
                    Log.i(TAG, "phone shell started: $url")
                    statusView.text = "Loading ORION…"
                    statusView.visibility = View.VISIBLE
                }

                override fun onPageFinished(
                    view: WebView,
                    url: String,
                ) {
                    Log.i(TAG, "phone shell finished: $url")
                    view.evaluateJavascript(
                        "Boolean(document.getElementById('app')&&document.getElementById('inp'))",
                    ) { ok ->
                        if (ok == "true") {
                            statusView.visibility = View.GONE
                            Log.i(TAG, "phone shell ready")
                        } else {
                            statusView.text = "ORION phone UI failed to render"
                            statusView.visibility = View.VISIBLE
                            Log.e(TAG, "required phone shell DOM missing")
                        }
                    }
                }

                override fun onReceivedError(
                    view: WebView,
                    request: WebResourceRequest,
                    error: WebResourceError,
                ) {
                    Log.e(TAG, "web error: " + error.description)
                    if (request.isForMainFrame) {
                        statusView.text = "ORION phone UI failed to load"
                        statusView.visibility = View.VISIBLE
                    }
                }
            }
        }

        offlineChatBridge = OfflineChatBridge(
            activity = this,
            webView = webView,
            historyStore = historyStore,
            onReconnect = {},
        )
        pcBridge = OrionPcBridge(
            activity = this,
            webView = webView,
            historyStore = historyStore,
        )
        webView.addJavascriptInterface(offlineChatBridge!!, "ORION_NATIVE_CHAT")
        webView.addJavascriptInterface(pcBridge!!, "ORION_NATIVE_PC")

        statusView = TextView(this).apply {
            text = "Loading ORION…"
            setTextColor(Color.rgb(114, 131, 148))
            textSize = 13f
            gravity = Gravity.CENTER
            setBackgroundColor(Color.TRANSPARENT)
        }

        root.addView(
            webView,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT,
            ),
        )
        root.addView(
            statusView,
            FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT,
            ),
        )

        setContentView(root)
        loadPhoneShell()
    }

    private fun loadPhoneShell() {
        val html = assets.open("offline/index.html").bufferedReader(Charsets.UTF_8).use { it.readText() }
        webView.loadDataWithBaseURL(
            PHONE_BASE_URL,
            html,
            "text/html",
            "utf-8",
            null,
        )
    }

    override fun onBackPressed() {
        webView.evaluateJavascript(
            "(function(){if(window.ORION_PHONE_BACK){return window.ORION_PHONE_BACK()?'handled':'close'}return 'close';})()",
        ) { result ->
            if (result != "\"handled\"") {
                moveTaskToBack(true)
            }
        }
    }

    override fun onDestroy() {
        pcBridge?.close()
        pcBridge = null
        offlineChatBridge?.close()
        offlineChatBridge = null
        if (::historyStore.isInitialized) {
            historyStore.close()
        }
        if (::webView.isInitialized) {
            webView.stopLoading()
            webView.webChromeClient = null
            webView.webViewClient = WebViewClient()
            webView.destroy()
        }
        super.onDestroy()
    }
}
