package com.sadusor.orionv3.history

import android.content.Context
import android.net.Uri
import android.database.sqlite.SQLiteDatabase
import java.io.File

/**
 * Owner-selected backup for the production Android chat SQLite database.
 * Caller must obtain URI with ACTION_CREATE_DOCUMENT; never exports silently.
 * Uses SQLite VACUUM INTO to make a transactionally consistent copy.
 * Not wired into UI or invoked by background sync.
 */
object OwnerChatBackupV1 {
    fun exportToOwnerUri(context: Context, ownerSelectedUri: Uri): Long {
        require(context.packageName == "com.sadusor.orionv3")
        require(ownerSelectedUri.scheme == "content")
        val source = context.getDatabasePath("orion_chat_history.db")
        require(source.isFile && source.length() > 0)
        val temp = File.createTempFile("orion-owner-chat-", ".sqlite3", context.cacheDir)
        temp.delete()
        try {
            val escaped = temp.absolutePath.replace("'", "''")
            SQLiteDatabase.openDatabase(source.absolutePath, null, SQLiteDatabase.OPEN_READWRITE).use { db ->
                db.execSQL("VACUUM INTO '$escaped'")
            }
            SQLiteDatabase.openDatabase(temp.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { check ->
                val cursor = check.rawQuery("PRAGMA integrity_check", null)
                cursor.use {
                    require(it.moveToFirst() && it.getString(0) == "ok") {
                        "Backup integrity verification failed"
                    }
                }
            }
            val output = context.contentResolver.openOutputStream(ownerSelectedUri, "w")
                ?: error("Owner destination not writable")
            output.use { stream -> temp.inputStream().use { it.copyTo(stream) } }
            return temp.length()
        } finally {
            temp.delete()
        }
    }
}
