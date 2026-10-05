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

private const val ORION_BASE_URL = "http://10.109.233.27:8890/"
private const val ORION_UI_URL = ORION_BASE_URL + "v3/?view=phone"
private const val TAG = "ORIONV3"

class MainActivity : Activity() {
    private lateinit var webView: WebView
    private lateinit var statusView: TextView

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = FrameLayout(this).apply {
            setBackgroundColor(Color.rgb(5, 7, 11))
        }

        webView = WebView(this).apply {
            setBackgroundColor(Color.rgb(5, 7, 11))

            // Huawei / older Android WebView compatibility:
            // STRATA's DOM loads correctly on this device, but hardware
            // compositing can produce an all-black surface.
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

            WebView.setWebContentsDebuggingEnabled(true)

            webChromeClient = object : WebChromeClient() {
                override fun onConsoleMessage(message: ConsoleMessage): Boolean {
                    Log.e(
                        TAG,
                        "JS " + message.message() +
                            " @" + message.sourceId() +
                            ":" + message.lineNumber()
                    )
                    return true
                }
            }

            webViewClient = object : WebViewClient() {
                override fun shouldOverrideUrlLoading(
                    view: WebView,
                    request: WebResourceRequest,
                ): Boolean {
                    return !request.url.toString().startsWith(ORION_BASE_URL)
                }

                override fun onPageStarted(
                    view: WebView,
                    url: String,
                    favicon: Bitmap?,
                ) {
                    Log.i(TAG, "page started: $url")
                    statusView.text = "Loading ORION…"
                    statusView.visibility = View.VISIBLE
                }

                override fun onPageFinished(
                    view: WebView,
                    url: String,
                ) {
                    Log.i(TAG, "page finished: $url")

                    view.evaluateJavascript(
                        "(function(){return JSON.stringify({title:document.title,ready:document.readyState,app:!!document.getElementById('app'),core:!!document.getElementById('core'),composer:!!document.getElementById('inp'),scripts:document.scripts.length,styles:document.styleSheets.length,ua:navigator.userAgent,body:document.body&&document.body.innerText.slice(0,220)});})()"
                    ) { result ->
                        Log.i(TAG, "DOM probe: $result")
                    }

                    view.evaluateJavascript(
                        "Boolean(document.getElementById('app')&&document.getElementById('core')&&document.getElementById('inp'))"
                    ) { ok ->
                        if (ok == "true") {
                            statusView.visibility = View.GONE
                            Log.i(TAG, "visual shell ready")
                        } else {
                            statusView.text = "ORION UI failed to render"
                            statusView.visibility = View.VISIBLE
                            Log.e(TAG, "required STRATA DOM missing")
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
                        statusView.text = "ORION unavailable · " + error.description
                        statusView.visibility = View.VISIBLE
                    }
                }
            }
        }

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
        webView.loadUrl(ORION_UI_URL)
    }

    override fun onBackPressed() {
        if (::webView.isInitialized && webView.canGoBack()) {
            webView.goBack()
        } else {
            moveTaskToBack(true)
        }
    }

    override fun onDestroy() {
        if (::webView.isInitialized) {
            webView.stopLoading()
            webView.webChromeClient = null
            webView.webViewClient = WebViewClient()
            webView.destroy()
        }
        super.onDestroy()
    }
}
