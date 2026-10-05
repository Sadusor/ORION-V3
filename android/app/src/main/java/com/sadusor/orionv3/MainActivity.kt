package com.sadusor.orionv3

import android.annotation.SuppressLint
import android.graphics.Bitmap
import android.os.Bundle
import android.util.Log
import android.webkit.ConsoleMessage
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView

private const val ORION_BASE_URL = "http://10.109.233.27:8890/"
private const val ORION_UI_URL = ORION_BASE_URL + "v3/?view=phone"
private const val TAG = "ORIONV3"

private val Bg = Color(0xFF05070B)
private val Text = Color(0xFFC9EEF5)
private val Muted = Color(0xFF728394)

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { OrionApp() }
    }
}

@Composable
private fun OrionApp() {
    var status by remember { mutableStateOf("Loading ORION…") }
    var failed by remember { mutableStateOf(false) }

    MaterialTheme(
        colorScheme = darkColorScheme(
            background = Bg,
            surface = Bg,
            onBackground = Text,
            onSurface = Text
        )
    ) {
        Surface(modifier = Modifier.fillMaxSize(), color = Bg) {
            Box(
                modifier = Modifier
                    .fillMaxSize()
                    .background(Bg)
                    .statusBarsPadding()
                    .navigationBarsPadding()
            ) {
                OrionWebSurface(
                    onLoaded = {
                        status = ""
                        failed = false
                    },
                    onError = {
                        status = it
                        failed = true
                    }
                )

                if (status.isNotBlank()) {
                    Text(
                        text = status,
                        color = if (failed) Text else Muted,
                        fontSize = 11.sp,
                        modifier = Modifier.align(Alignment.Center)
                    )
                }
            }
        }
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun OrionWebSurface(
    onLoaded: () -> Unit,
    onError: (String) -> Unit,
) {
    var webView: WebView? = null

    BackHandler {
        val w = webView
        if (w != null && w.canGoBack()) {
            w.goBack()
        } else {
            // ORION is the app. Back does not reveal a launcher/dashboard.
        }
    }

    AndroidView(
        modifier = Modifier.fillMaxSize(),
        factory = { context ->
            WebView(context).apply {
                webView = this
                setBackgroundColor(android.graphics.Color.rgb(5, 7, 11))

                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.databaseEnabled = true
                settings.allowFileAccess = false
                settings.allowContentAccess = false
                settings.setSupportZoom(false)
                settings.useWideViewPort = true
                settings.loadWithOverviewMode = false
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
                                onLoaded()
                            } else {
                                onError("ORION UI failed to render")
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
                            onError("ORION unavailable · " + error.description)
                        }
                    }
                }

                loadUrl(ORION_UI_URL)
            }
        },
        update = { webView = it }
    )
}
