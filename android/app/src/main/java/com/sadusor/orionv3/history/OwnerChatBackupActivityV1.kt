package com.sadusor.orionv3.history

import android.app.Activity
import android.content.Intent
import android.os.Bundle
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
                val success = try {
                    OwnerChatBackupV1.exportToOwnerUri(applicationContext, uri)
                    true
                } catch (_: Exception) { false }
                runOnUiThread {
                    Toast.makeText(this, if (success) "Chat backup saved" else "Chat backup failed", Toast.LENGTH_LONG).show()
                    finish()
                }
            }.start()
        } else finish()
    }
}
