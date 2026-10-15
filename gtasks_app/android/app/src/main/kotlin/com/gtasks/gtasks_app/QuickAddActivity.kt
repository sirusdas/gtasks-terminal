package com.gtasks.gtasks_app

import android.app.Activity
import android.content.ContentValues
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.os.Bundle
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.Spinner
import android.widget.Toast
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID

class QuickAddActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_quick_add)

        val etTitle = findViewById<EditText>(R.id.et_quick_add_title)
        val etNotes = findViewById<EditText>(R.id.et_quick_add_notes)
        val spDue = findViewById<Spinner>(R.id.spinner_quick_add_due)
        val spPriority = findViewById<Spinner>(R.id.spinner_quick_add_priority)
        val btnSave = findViewById<Button>(R.id.btn_quick_add_save)
        val btnCancel = findViewById<Button>(R.id.btn_quick_add_cancel)
        val btnClose = findViewById<ImageView>(R.id.btn_quick_add_close)

        // Set up Due Date Spinner
        val dueOptions = arrayOf("No Due Date", "Today", "Tomorrow", "In 3 Days", "Next Week")
        val dueAdapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, dueOptions)
        spDue.adapter = dueAdapter

        // Set up Priority Spinner
        val priorityOptions = arrayOf("Normal", "Medium", "High", "Critical", "Low")
        val priorityAdapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, priorityOptions)
        spPriority.adapter = priorityAdapter

        // Focus title and open soft keyboard
        etTitle.requestFocus()
        etTitle.postDelayed({
            val imm = getSystemService(Context.INPUT_METHOD_SERVICE) as? InputMethodManager
            imm?.showSoftInput(etTitle, InputMethodManager.SHOW_IMPLICIT)
        }, 200)

        btnClose.setOnClickListener { finish() }
        btnCancel.setOnClickListener { finish() }

        btnSave.setOnClickListener {
            val title = etTitle.text.toString().trim()
            if (title.isEmpty()) {
                etTitle.error = "Title cannot be empty"
                return@setOnClickListener
            }

            val notes = etNotes.text.toString().trim()
            val priority = spPriority.selectedItem.toString().lowercase()

            val calendar = Calendar.getInstance()
            val dueStr: String? = when (spDue.selectedItemPosition) {
                1 -> { // Today
                    SimpleDateFormat("yyyy-MM-dd", Locale.US).format(calendar.time)
                }
                2 -> { // Tomorrow
                    calendar.add(Calendar.DAY_OF_YEAR, 1)
                    SimpleDateFormat("yyyy-MM-dd", Locale.US).format(calendar.time)
                }
                3 -> { // In 3 days
                    calendar.add(Calendar.DAY_OF_YEAR, 3)
                    SimpleDateFormat("yyyy-MM-dd", Locale.US).format(calendar.time)
                }
                4 -> { // Next week
                    calendar.add(Calendar.DAY_OF_YEAR, 7)
                    SimpleDateFormat("yyyy-MM-dd", Locale.US).format(calendar.time)
                }
                else -> null
            }

            saveTaskToLocalDb(title, notes, priority, dueStr)
            Toast.makeText(this, "Task created! 🎉", Toast.LENGTH_SHORT).show()
            GTasksWidgetProvider.updateAllWidgets(applicationContext)
            finish()
        }
    }

    private fun saveTaskToLocalDb(title: String, notes: String, priority: String, due: String?) {
        try {
            val dbFile = getDatabasePath("gtasks_local.db")
            if (!dbFile.parentFile.exists()) {
                dbFile.parentFile.mkdirs()
            }
            SQLiteDatabase.openOrCreateDatabase(dbFile, null).use { db ->
                // Ensure table exists
                db.execSQL(
                    """
                    CREATE TABLE IF NOT EXISTS tasks (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        description TEXT,
                        due TEXT,
                        priority TEXT,
                        status TEXT NOT NULL DEFAULT 'pending',
                        tags TEXT,
                        spaces TEXT,
                        list_id TEXT,
                        list_title TEXT,
                        account TEXT NOT NULL DEFAULT 'default',
                        created_at TEXT,
                        modified_at TEXT,
                        completed_at TEXT,
                        is_recurring INTEGER DEFAULT 0,
                        recurrence_type TEXT,
                        sync_status TEXT DEFAULT 'pending_insert'
                    )
                    """.trimIndent()
                )

                val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
                    timeZone = TimeZone.getTimeZone("UTC")
                }
                val nowStr = isoFormat.format(Date())

                val cv = ContentValues().apply {
                    put("id", UUID.randomUUID().toString())
                    put("title", title)
                    put("description", if (notes.isNotEmpty()) notes else "")
                    put("priority", priority)
                    put("status", "pending")
                    put("due", due)
                    put("account", "default")
                    put("created_at", nowStr)
                    put("modified_at", nowStr)
                    put("sync_status", "pending_insert")
                }
                db.insertWithOnConflict("tasks", null, cv, SQLiteDatabase.CONFLICT_REPLACE)
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }
}
