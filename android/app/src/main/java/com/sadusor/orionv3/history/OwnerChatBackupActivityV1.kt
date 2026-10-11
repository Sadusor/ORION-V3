package com.sadusor.orionv3.history

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.util.Log
import android.widget.Toast

/** Owner-initiated document picker; never exports in the background. */
class OwnerChatBackupActivityV1 : Activity() {
    private val requestCode = 39021
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (packageName != "com.sadusor.orionv3") { finish(); return }
        val picker = Intent(Intent.ACTION_CREATE_DOCUMENT).apply {
            addCategory(Intent.CATEGORY_OPENABLE)
            type = "application/octet-stream"
            putExtra(Intent.EXTRA_TITLE, "orion-chat-history.sqlite3")
        }
        startActivityForResult(picker, requestCode)
    }
    @Deprecated("Android document picker result")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        if (requestCode != this.requestCode) return
        val uri = data?.data
        if (resultCode == RESULT_OK && uri != null) {
            Thread {
                val outcome = try {
                    val size = OwnerChatBackupV1.exportToOwnerUri(applicationContext, uri)
                    "Chat backup saved ($size bytes)"
                } catch (error: Exception) {
                    Log.e("ORION_CHAT_BACKUP", "Owner-selected export failed", error)
                    "Chat backup failed: " + error.javaClass.simpleName +
                        " — " + (error.message ?: "unknown error").take(120)
                }
                runOnUiThread {
                    Toast.makeText(this, outcome, Toast.LENGTH_LONG).show()
                    finish()
                }
            }.start()
        } else finish()
    }
}
