package com.sadusor.orionv3

import android.annotation.SuppressLint
import android.content.ActivityNotFoundException
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.navigationBarsPadding
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.statusBarsPadding
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.net.HttpURLConnection
import java.net.URL

private const val ORION_BASE_URL = "http://10.109.233.27:8890/"
private const val ORION_UI_URL = ORION_BASE_URL + "v3/"
private const val ZEROTIER_PACKAGE = "com.zerotier.one"

private val Bg = Color(0xFF05070B)
private val SurfaceDark = Color(0xFF0B1118)
private val SurfaceLift = Color(0xFF101A26)
private val Line = Color(0xFF223246)
private val Ion = Color(0xFF76CFE4)
private val TextPrimary = Color(0xFFC9EEF5)
private val Muted = Color(0xFF728394)
private val Green = Color(0xFF49D99A)
private val Amber = Color(0xFFF5B942)
private val Red = Color(0xFFD98276)

private enum class PcState { Offline, Connecting, Online }

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { OrionApp() }
    }
}

@Composable
private fun OrionApp() {
    val context = LocalContext.current
    var state by rememberSaveable { mutableStateOf(PcState.Offline) }
    var showOrion by rememberSaveable { mutableStateOf(false) }
    var message by rememberSaveable { mutableStateOf("Connect ZeroTier when you want ORION away from the PC.") }

    MaterialTheme(
        colorScheme = darkColorScheme(
            background = Bg,
            surface = SurfaceDark,
            primary = Ion,
            onBackground = TextPrimary,
            onSurface = TextPrimary
        )
    ) {
        Surface(modifier = Modifier.fillMaxSize(), color = Bg) {
            if (showOrion) {
                OrionWebSurface(
                    onClose = { showOrion = false },
                    onError = {
                        message = it
                        showOrion = false
                        state = PcState.Offline
                    }
                )
            } else {
                Dashboard(
                    state = state,
                    message = message,
                    onOpen = {
                        state = PcState.Connecting
                        message = "Checking ORION V3 on your private network…"
                        kotlinx.coroutines.CoroutineScope(Dispatchers.Main).launch {
                            val connected = withContext(Dispatchers.IO) { isReachable() }
                            if (connected) {
                                state = PcState.Online
                                message = "ORION V3 is online."
                                showOrion = true
                            } else {
                                state = PcState.Offline
                                message = "ORION V3 not reachable. Connect ZeroTier and try again."
                            }
                        }
                    },
                    onZeroTier = {
                        message = if (launchZeroTier(context)) {
                            "ZeroTier opened. Connect, return, then press CHECK ORION."
                        } else {
                            "ZeroTier is not installed."
                        }
                    }
                )
            }
        }
    }
}

@Composable
private fun Dashboard(
    state: PcState,
    message: String,
    onOpen: () -> Unit,
    onZeroTier: () -> Unit,
) {
    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.radialGradient(
                    listOf(
                        Color(0xFF0F2230),
                        Bg,
                        Color(0xFF020407)
                    )
                )
            )
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .statusBarsPadding()
                .navigationBarsPadding()
                .padding(horizontal = 22.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Spacer(Modifier.height(28.dp))

            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("ORION", color = TextPrimary, fontSize = 20.sp, fontWeight = FontWeight.Black, letterSpacing = 2.sp)
                    Text("V3 · PERSONAL AI CONTROL PLANE", color = Muted, fontSize = 9.sp, fontWeight = FontWeight.Bold, letterSpacing = 1.2.sp)
                }
                StatusChip(state)
            }

            Spacer(Modifier.weight(.72f))

            Box(
                modifier = Modifier
                    .size(176.dp)
                    .background(Ion.copy(alpha = .07f), CircleShape)
                    .border(1.dp, Ion.copy(alpha = .34f), CircleShape),
                contentAlignment = Alignment.Center
            ) {
                Box(
                    modifier = Modifier
                        .size(118.dp)
                        .background(Ion.copy(alpha = .08f), CircleShape)
                        .border(1.dp, Ion.copy(alpha = .55f), CircleShape),
                    contentAlignment = Alignment.Center
                ) {
                    Text("O", color = TextPrimary, fontSize = 62.sp, fontWeight = FontWeight.ExtraLight)
                }
            }

            Spacer(Modifier.height(30.dp))

            Text(
                when (state) {
                    PcState.Online -> "ORION is ready"
                    PcState.Connecting -> "Connecting to ORION"
                    PcState.Offline -> "Private connection"
                },
                color = TextPrimary,
                fontSize = 29.sp,
                fontWeight = FontWeight.ExtraBold
            )

            Spacer(Modifier.height(8.dp))

            Text(
                "Claude STRATA interface · PC authority stays with ORION",
                color = Muted,
                fontSize = 12.sp,
                textAlign = TextAlign.Center
            )

            Spacer(Modifier.height(10.dp))

            Text(
                message,
                color = when (state) {
                    PcState.Online -> Green
                    PcState.Connecting -> Amber
                    PcState.Offline -> Muted
                },
                fontSize = 11.sp,
                textAlign = TextAlign.Center,
                fontWeight = FontWeight.SemiBold
            )

            Spacer(Modifier.height(34.dp))

            Button(
                onClick = onOpen,
                modifier = Modifier.fillMaxWidth().height(58.dp),
                colors = ButtonDefaults.buttonColors(containerColor = Ion, contentColor = Color(0xFF061016)),
                shape = RoundedCornerShape(15.dp)
            ) {
                Text(
                    if (state == PcState.Online) "OPEN ORION" else "CHECK ORION",
                    fontWeight = FontWeight.ExtraBold,
                    letterSpacing = .7.sp,
                    fontSize = 14.sp
                )
            }

            Spacer(Modifier.height(10.dp))

            OutlinedButton(
                onClick = onZeroTier,
                modifier = Modifier.fillMaxWidth().height(50.dp),
                border = BorderStroke(1.dp, Line),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = TextPrimary),
                shape = RoundedCornerShape(14.dp)
            ) {
                Text("OPEN ZEROTIER", fontWeight = FontWeight.Bold, fontSize = 12.sp, letterSpacing = .5.sp)
            }

            Spacer(Modifier.weight(1f))

            Text(
                "10.109.233.27:8890  ·  ORION V3 0.1",
                color = Color(0xFF536474),
                fontSize = 9.sp,
                letterSpacing = .5.sp
            )
            Spacer(Modifier.height(20.dp))
        }
    }
}

@Composable
private fun StatusChip(state: PcState) {
    val accent = when (state) {
        PcState.Online -> Green
        PcState.Connecting -> Amber
        PcState.Offline -> Red
    }
    Row(
        modifier = Modifier
            .background(SurfaceDark, RoundedCornerShape(999.dp))
            .border(1.dp, Line, RoundedCornerShape(999.dp))
            .padding(horizontal = 10.dp, vertical = 7.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Box(Modifier.size(7.dp).background(accent, CircleShape))
        Spacer(Modifier.size(7.dp))
        Text(
            when (state) {
                PcState.Online -> "ONLINE"
                PcState.Connecting -> "CONNECTING"
                PcState.Offline -> "OFFLINE"
            },
            color = TextPrimary,
            fontSize = 9.sp,
            fontWeight = FontWeight.ExtraBold
        )
    }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
private fun OrionWebSurface(
    onClose: () -> Unit,
    onError: (String) -> Unit,
) {
    BackHandler(onBack = onClose)

    AndroidView(
        modifier = Modifier
            .fillMaxSize()
            .statusBarsPadding()
            .navigationBarsPadding(),
        factory = { context ->
            WebView(context).apply {
                setBackgroundColor(android.graphics.Color.rgb(5, 7, 11))
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.databaseEnabled = true
                settings.allowFileAccess = false
                settings.allowContentAccess = false
                settings.setSupportZoom(false)

                webViewClient = object : WebViewClient() {
                    override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                        val url = request.url.toString()
                        return if (url.startsWith(ORION_BASE_URL)) {
                            false
                        } else {
                            try {
                                context.startActivity(Intent(Intent.ACTION_VIEW, request.url))
                            } catch (_: Exception) {}
                            true
                        }
                    }

                    override fun onReceivedError(
                        view: WebView,
                        request: WebResourceRequest,
                        error: WebResourceError,
                    ) {
                        if (request.isForMainFrame) onError("ORION V3 page could not be reached.")
                    }
                }

                loadUrl(ORION_UI_URL)
            }
        }
    )
}

private fun isReachable(): Boolean {
    return try {
        val conn = URL(ORION_BASE_URL + "api/health").openConnection() as HttpURLConnection
        conn.connectTimeout = 1500
        conn.readTimeout = 1500
        conn.requestMethod = "GET"
        conn.useCaches = false
        val ok = conn.responseCode in 200..299
        conn.disconnect()
        ok
    } catch (_: Exception) {
        false
    }
}

private fun launchZeroTier(context: Context): Boolean {
    val pm = context.packageManager
    val launchIntent = pm.getLaunchIntentForPackage(ZEROTIER_PACKAGE)
    if (launchIntent != null) {
        launchIntent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(launchIntent)
        return true
    }
    return try {
        context.startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse("market://details?id=$ZEROTIER_PACKAGE"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )
        false
    } catch (_: ActivityNotFoundException) {
        context.startActivity(
            Intent(Intent.ACTION_VIEW, Uri.parse("https://play.google.com/store/apps/details?id=$ZEROTIER_PACKAGE"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        )
        false
    }
}
