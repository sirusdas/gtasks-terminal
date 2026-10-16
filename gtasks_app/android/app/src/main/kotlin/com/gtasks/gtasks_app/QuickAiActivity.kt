package com.gtasks.gtasks_app

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.database.sqlite.SQLiteDatabase
import android.os.Bundle
import android.view.View
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import java.util.UUID

class QuickAiActivity : Activity() {

    private data class TaskRecord(
        val id: String,
        val title: String,
        val priority: String,
        val due: String?,
        val status: String,
        val spaces: String?
    )

    private var filterType: String? = null
    private var filterVal: String? = null
    private var appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID

    private lateinit var tvScope: TextView
    private lateinit var btnClose: ImageView
    private lateinit var tvMessage: TextView
    private lateinit var cardTask: LinearLayout
    private lateinit var btnTaskCheck: ImageView
    private lateinit var tvTaskTitle: TextView
    private lateinit var tvTaskPriority: TextView
    private lateinit var tvTaskDue: TextView
    private lateinit var btnTaskMarkDone: TextView
    private lateinit var llConfirmBox: LinearLayout
    private lateinit var btnConfirmCancel: Button
    private lateinit var btnConfirmYes: Button
    private lateinit var etPrompt: EditText
    private lateinit var btnSend: Button

    private var currentHighlightedTask: TaskRecord? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_quick_ai)

        filterType = intent.getStringExtra("widget_filter_type")
        filterVal = intent.getStringExtra("widget_filter_val")
        appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)

        initViews()
        setupListeners()
        loadInitialState()
    }

    private fun initViews() {
        tvScope = findViewById(R.id.tv_quick_ai_scope)
        btnClose = findViewById(R.id.btn_quick_ai_close)
        tvMessage = findViewById(R.id.tv_quick_ai_message)
        cardTask = findViewById(R.id.ll_quick_ai_task_card)
        btnTaskCheck = findViewById(R.id.btn_task_check)
        tvTaskTitle = findViewById(R.id.tv_task_title)
        tvTaskPriority = findViewById(R.id.tv_task_priority)
        tvTaskDue = findViewById(R.id.tv_task_due)
        btnTaskMarkDone = findViewById(R.id.btn_task_mark_done)
        llConfirmBox = findViewById(R.id.ll_quick_ai_confirm_box)
        btnConfirmCancel = findViewById(R.id.btn_confirm_cancel)
        btnConfirmYes = findViewById(R.id.btn_confirm_yes)
        etPrompt = findViewById(R.id.et_quick_ai_prompt)
        btnSend = findViewById(R.id.btn_quick_ai_send)
    }

    private fun setupListeners() {
        btnClose.setOnClickListener { finish() }

        findViewById<TextView>(R.id.btn_chip_urgent).setOnClickListener {
            handleMostUrgent()
        }

        findViewById<TextView>(R.id.btn_chip_earliest).setOnClickListener {
            handleEarliestDue()
        }

        findViewById<TextView>(R.id.btn_chip_summary).setOnClickListener {
            handleSummary()
        }

        findViewById<TextView>(R.id.btn_chip_doneall).setOnClickListener {
            handleDoneAllConfirmation()
        }

        findViewById<TextView>(R.id.btn_chip_full_chat).setOnClickListener {
            launchFullChat()
        }

        btnSend.setOnClickListener {
            val q = etPrompt.text.toString().trim()
            if (q.isNotEmpty()) {
                handleUserQuery(q)
                etPrompt.text.clear()
            }
        }

        etPrompt.setOnEditorActionListener { _, _, _ ->
            val q = etPrompt.text.toString().trim()
            if (q.isNotEmpty()) {
                handleUserQuery(q)
                etPrompt.text.clear()
            }
            true
        }

        btnTaskCheck.setOnClickListener {
            currentHighlightedTask?.let { completeTask(it.id) }
        }

        btnTaskMarkDone.setOnClickListener {
            currentHighlightedTask?.let { completeTask(it.id) }
        }

        btnConfirmCancel.setOnClickListener {
            llConfirmBox.visibility = View.GONE
            tvMessage.text = "🚫 Bulk completion cancelled."
        }

        btnConfirmYes.setOnClickListener {
            executeBulkComplete()
        }
    }

    private fun getScopeLabel(): String {
        return when (filterType) {
            "space" -> "Space: $filterVal"
            "subspace" -> "Subspace: $filterVal"
            "tag" -> "#$filterVal"
            "list" -> "List: $filterVal"
            "account" -> "@$filterVal"
            "date" -> "Due: $filterVal"
            else -> "All Tasks"
        }
    }

    private fun loadInitialState() {
        val tasks = queryTasksFromLocalDb()
        val pendingCount = tasks.count { it.status != "completed" }
        val scopeLabel = getScopeLabel()
        tvScope.text = "$scopeLabel • $pendingCount tasks"

        val todayStr = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
        val overdueCount = tasks.count { it.status != "completed" && it.due != null && it.due.take(10) < todayStr }
        val dueTodayCount = tasks.count { it.status != "completed" && it.due != null && it.due.take(10) == todayStr }
        val highPrioCount = tasks.count { it.status != "completed" && (it.priority.lowercase() == "high" || it.priority.lowercase() == "critical") }

        tvMessage.text = "🎯 Scoped to $scopeLabel:\n" +
                "• $pendingCount pending tasks\n" +
                (if (dueTodayCount > 0) "• $dueTodayCount due today ⏰\n" else "") +
                (if (overdueCount > 0) "• $overdueCount overdue ⚠️\n" else "") +
                (if (highPrioCount > 0) "• $highPrioCount high priority ⚡\n" else "") +
                "Tap a quick action above or ask AI below:"
    }

    private fun handleMostUrgent() {
        llConfirmBox.visibility = View.GONE
        val tasks = queryTasksFromLocalDb().filter { it.status != "completed" }
        if (tasks.isEmpty()) {
            cardTask.visibility = View.GONE
            tvMessage.text = "✨ No pending tasks found in this view!"
            return
        }

        val prioWeight = mapOf("critical" to 4, "high" to 3, "medium" to 2, "low" to 1)
        val sorted = tasks.sortedWith(compareByDescending<TaskRecord> { prioWeight[it.priority.lowercase()] ?: 2 }
            .thenBy { it.due ?: "9999-99-99" })

        val urgent = sorted.first()
        currentHighlightedTask = urgent

        tvMessage.text = "⚡ Most Urgent Task in ${getScopeLabel()}:"
        displayTaskCard(urgent)
    }

    private fun handleEarliestDue() {
        llConfirmBox.visibility = View.GONE
        val tasks = queryTasksFromLocalDb().filter { it.status != "completed" && !it.due.isNullOrBlank() }
        if (tasks.isEmpty()) {
            cardTask.visibility = View.GONE
            tvMessage.text = "ℹ️ No pending tasks with due dates in this view."
            return
        }

        val sorted = tasks.sortedBy { it.due }
        val earliest = sorted.first()
        currentHighlightedTask = earliest

        val dueDisplay = earliest.due?.take(10) ?: "None"
        tvMessage.text = "⏰ Earliest Due Task in ${getScopeLabel()}:\nDue: $dueDisplay"
        displayTaskCard(earliest)
    }

    private fun handleSummary() {
        cardTask.visibility = View.GONE
        llConfirmBox.visibility = View.GONE
        val tasks = queryTasksFromLocalDb()
        val pending = tasks.filter { it.status != "completed" }
        val completed = tasks.filter { it.status == "completed" }

        val todayStr = SimpleDateFormat("yyyy-MM-dd", Locale.US).format(Date())
        val overdue = pending.filter { it.due != null && it.due.take(10) < todayStr }
        val dueToday = pending.filter { it.due != null && it.due.take(10) == todayStr }
        val high = pending.filter { it.priority.lowercase() == "high" || it.priority.lowercase() == "critical" }

        tvMessage.text = "📊 Summary for ${getScopeLabel()}:\n" +
                "• Total Tasks: ${tasks.size}\n" +
                "• Pending: ${pending.size} | Completed: ${completed.size}\n" +
                "• Due Today: ${dueToday.size} | Overdue: ${overdue.size}\n" +
                "• High/Critical Priority: ${high.size}"
    }

    private fun handleDoneAllConfirmation() {
        cardTask.visibility = View.GONE
        val tasks = queryTasksFromLocalDb().filter { it.status != "completed" }
        if (tasks.isEmpty()) {
            tvMessage.text = "✨ No pending tasks to complete in this view!"
            llConfirmBox.visibility = View.GONE
            return
        }

        tvMessage.text = "⚠️ Confirm Bulk Complete:\nMark all ${tasks.size} visible pending tasks as completed?"
        llConfirmBox.visibility = View.VISIBLE
    }

    private fun executeBulkComplete() {
        llConfirmBox.visibility = View.GONE
        val tasks = queryTasksFromLocalDb().filter { it.status != "completed" }
        var count = 0
        tasks.forEach { t ->
            if (markTaskCompletedInDb(t.id)) count++
        }

        GTasksWidgetProvider.updateAllWidgets(applicationContext)
        tvMessage.text = "🎉 Completed $count task${if (count == 1) "" else "s"}!"
        tvScope.text = "${getScopeLabel()} • 0 tasks"
        Toast.makeText(this, "Completed $count tasks! 🎉", Toast.LENGTH_SHORT).show()
    }

    private fun displayTaskCard(task: TaskRecord) {
        cardTask.visibility = View.VISIBLE
        tvTaskTitle.text = task.title
        tvTaskPriority.text = task.priority.uppercase()
        tvTaskDue.text = if (!task.due.isNullOrBlank()) "Due: ${task.due.take(10)}" else "No Due Date"
        btnTaskCheck.setImageResource(R.drawable.ic_widget_unchecked)
    }

    private fun completeTask(taskId: String) {
        markTaskCompletedInDb(taskId)
        btnTaskCheck.setImageResource(R.drawable.ic_widget_checked)
        tvMessage.text = "🎉 Marked task as completed!"
        GTasksWidgetProvider.updateAllWidgets(applicationContext)
        Toast.makeText(this, "Task completed! 🎉", Toast.LENGTH_SHORT).show()
        cardTask.postDelayed({
            cardTask.visibility = View.GONE
            loadInitialState()
        }, 1200)
    }

    private fun handleUserQuery(query: String) {
        val qLower = query.lowercase().trim()
        llConfirmBox.visibility = View.GONE

        // 1. Quick Add Task
        if (qLower.startsWith("add ") || qLower.startsWith("new ") || qLower.startsWith("+")) {
            val title = query.replaceFirst(Regex("^(?:add|new|\\+)\\s*", RegexOption.IGNORE_CASE), "").trim()
            if (title.isNotEmpty()) {
                createTaskDirectly(title)
                return
            }
        }

        // 2. Shortcut commands
        when {
            qLower == "urgent" || qLower == "most urgent" || qLower == "/urgent" -> handleMostUrgent()
            qLower == "earliest" || qLower == "earliest due" || qLower == "/earliest" -> handleEarliestDue()
            qLower == "summary" || qLower == "stats" || qLower == "/summary" -> handleSummary()
            qLower == "done all" || qLower == "complete all" || qLower == "/doneall" -> handleDoneAllConfirmation()
            qLower == "chat" || qLower == "full chat" || qLower == "/chat" -> launchFullChat()
            else -> {
                // Search or match tasks in view
                val matches = queryTasksFromLocalDb().filter { it.title.lowercase().contains(qLower) }
                if (matches.isNotEmpty()) {
                    tvMessage.text = "🔍 Found ${matches.size} task${if (matches.size == 1) "" else "s"} matching \"$query\":\n" +
                            matches.take(3).joinToString("\n") { "• ${it.title} (${it.priority.uppercase()})" }
                    displayTaskCard(matches.first())
                } else {
                    tvMessage.text = "🤖 Query: \"$query\"\n\n" +
                            "• Tap '⚡ Most Urgent' or '⏰ Earliest Due'\n" +
                            "• Type 'add <task name>' to quick add to this space\n" +
                            "• Tap '💬 Full Chat ↗' for conversational AI"
                    cardTask.visibility = View.GONE
                }
            }
        }
    }

    private fun createTaskDirectly(title: String) {
        try {
            val dbFile = getDatabasePath("gtasks_local.db")
            if (!dbFile.exists()) return

            SQLiteDatabase.openOrCreateDatabase(dbFile, null).use { db ->
                val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
                    timeZone = TimeZone.getTimeZone("UTC")
                }
                val nowStr = isoFormat.format(Date())

                val spaceJson = if (filterType == "space" && !filterVal.isNullOrBlank()) {
                    "{\"$filterVal\":[]}"
                } else null

                val cv = ContentValues().apply {
                    put("id", UUID.randomUUID().toString())
                    put("title", title)
                    put("priority", "medium")
                    put("status", "pending")
                    put("account", "default")
                    put("created_at", nowStr)
                    put("modified_at", nowStr)
                    put("sync_status", "pending_insert")
                    if (spaceJson != null) put("spaces", spaceJson)
                }
                db.insertWithOnConflict("tasks", null, cv, SQLiteDatabase.CONFLICT_REPLACE)
            }

            GTasksWidgetProvider.updateAllWidgets(applicationContext)
            tvMessage.text = "🎉 Created task: \"$title\" in ${getScopeLabel()}!"
            cardTask.visibility = View.GONE
            Toast.makeText(this, "Task created! 🎉", Toast.LENGTH_SHORT).show()
            loadInitialState()
        } catch (e: Exception) {
            tvMessage.text = "⚠️ Error creating task: ${e.message}"
        }
    }

    private fun markTaskCompletedInDb(taskId: String): Boolean {
        return try {
            val dbFile = getDatabasePath("gtasks_local.db")
            if (!dbFile.exists()) return false

            SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READWRITE).use { db ->
                val isoFormat = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
                    timeZone = TimeZone.getTimeZone("UTC")
                }
                val nowStr = isoFormat.format(Date())
                val cv = ContentValues().apply {
                    put("status", "completed")
                    put("completed_at", nowStr)
                    put("modified_at", nowStr)
                    put("sync_status", "pending_update")
                }
                db.update("tasks", cv, "id = ?", arrayOf(taskId)) > 0
            }
        } catch (e: Exception) {
            false
        }
    }

    private fun queryTasksFromLocalDb(): List<TaskRecord> {
        val list = mutableListOf<TaskRecord>()
        try {
            val dbFile = getDatabasePath("gtasks_local.db")
            if (!dbFile.exists()) return list

            SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                val queryBuilder = StringBuilder("SELECT id, title, priority, due, status, spaces FROM tasks WHERE (sync_status IS NULL OR sync_status != 'pending_delete')")
                val args = mutableListOf<String>()

                if (!filterType.isNullOrBlank() && !filterVal.isNullOrBlank()) {
                    when (filterType) {
                        "space" -> {
                            queryBuilder.append(" AND spaces LIKE ?")
                            args.add("%\"$filterVal\"%")
                        }
                        "subspace" -> {
                            val parts = filterVal!!.split(" › ")
                            if (parts.size >= 2) {
                                queryBuilder.append(" AND spaces LIKE ? AND spaces LIKE ?")
                                args.add("%\"${parts[0]}\"%")
                                args.add("%\"${parts[1]}\"%")
                            } else {
                                queryBuilder.append(" AND spaces LIKE ?")
                                args.add("%\"$filterVal\"%")
                            }
                        }
                        "tag" -> {
                            queryBuilder.append(" AND tags LIKE ?")
                            args.add("%\"$filterVal\"%")
                        }
                        "list" -> {
                            queryBuilder.append(" AND list_title = ?")
                            args.add(filterVal!!)
                        }
                        "account" -> {
                            queryBuilder.append(" AND account = ?")
                            args.add(filterVal!!)
                        }
                        "date" -> {
                            when (filterVal!!.lowercase()) {
                                "today" -> queryBuilder.append(" AND substr(due, 1, 10) = date('now', 'localtime')")
                                "tomorrow" -> queryBuilder.append(" AND substr(due, 1, 10) = date('now', 'localtime', '+1 day')")
                                "overdue" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) < date('now', 'localtime')")
                            }
                        }
                    }
                }

                queryBuilder.append(" ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, due ASC")

                db.rawQuery(queryBuilder.toString(), args.toTypedArray()).use { cursor ->
                    while (cursor.moveToNext()) {
                        list.add(
                            TaskRecord(
                                id = cursor.getString(0),
                                title = cursor.getString(1) ?: "Untitled",
                                priority = cursor.getString(2) ?: "medium",
                                due = cursor.getString(3),
                                status = cursor.getString(4) ?: "pending",
                                spaces = cursor.getString(5)
                            )
                        )
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
        return list
    }

    private fun launchFullChat() {
        val intent = Intent(this, MainActivity::class.java).apply {
            action = "com.gtasks.gtasks_app.ACTION_OPEN_AI"
            putExtra("open_ai_chat", true)
            putExtra("is_from_widget", true)
            if (!filterType.isNullOrBlank() && !filterVal.isNullOrBlank()) {
                putExtra("widget_filter_type", filterType)
                putExtra("widget_filter_val", filterVal)
            }
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        startActivity(intent)
        finish()
    }
}
