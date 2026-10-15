package com.gtasks.gtasks_app

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.database.sqlite.SQLiteDatabase
import android.net.Uri
import android.util.Log
import android.view.View
import android.widget.RemoteViews
import android.widget.Toast
import org.json.JSONArray
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone

class GTasksWidgetProvider : AppWidgetProvider() {

    companion object {
        private const val TAG = "GTasksWidgetProvider"
        const val ACTION_REFRESH = "com.gtasks.gtasks_app.ACTION_REFRESH_WIDGET"
        const val ACTION_QUICK_SYNC = "com.gtasks.gtasks_app.ACTION_QUICK_SYNC_WIDGET"
        const val ACTION_COMPLETE_TASK = "com.gtasks.gtasks_app.ACTION_COMPLETE_TASK"
        const val ACTION_TOGGLE_EXPAND = "com.gtasks.gtasks_app.ACTION_TOGGLE_EXPAND"
        const val ACTION_CLEAR_FILTER = "com.gtasks.gtasks_app.ACTION_CLEAR_FILTER"
        const val ACTION_TOGGLE_VIEW_MODE = "com.gtasks.gtasks_app.ACTION_TOGGLE_VIEW_MODE"

        fun updateAllWidgets(context: Context) {
            try {
                val appWidgetManager = AppWidgetManager.getInstance(context) ?: return
                val thisWidget = ComponentName(context, GTasksWidgetProvider::class.java)
                val appWidgetIds = appWidgetManager.getAppWidgetIds(thisWidget) ?: intArrayOf()
                if (appWidgetIds.isNotEmpty()) {
                    appWidgetManager.notifyAppWidgetViewDataChanged(appWidgetIds, R.id.widget_list_view)
                    for (appWidgetId in appWidgetIds) {
                        val provider = GTasksWidgetProvider()
                        provider.updateAppWidget(context, appWidgetManager, appWidgetId)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error in updateAllWidgets", e)
            }
        }

        fun getFilteredTaskCount(context: Context, appWidgetId: Int): Int {
            return try {
                val dbFile = context.getDatabasePath("gtasks_local.db")
                if (!dbFile.exists()) return 0
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val checkCursor = db.rawQuery(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'",
                        null
                    )
                    val tableExists = checkCursor.use { it.moveToFirst() }
                    if (!tableExists) return 0

                    val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                    val filterType = prefs.getString("filter_type_$appWidgetId", null)
                    val filterVal = prefs.getString("filter_val_$appWidgetId", null)
                    val hideRecurring = prefs.getBoolean("hide_recurring_$appWidgetId", false)
                    val hiddenListsJson = prefs.getString("hidden_lists_$appWidgetId", null)
                    val hiddenTagsJson = prefs.getString("hidden_tags_$appWidgetId", null)

                    val queryBuilder = StringBuilder(
                        "SELECT COUNT(*) FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete'"
                    )
                    val args = mutableListOf<String>()

                    if (!filterType.isNullOrBlank() && !filterVal.isNullOrBlank()) {
                        when (filterType) {
                            "list" -> {
                                queryBuilder.append(" AND list_title = ?")
                                args.add(filterVal)
                            }
                            "account" -> {
                                queryBuilder.append(" AND account = ?")
                                args.add(filterVal)
                            }
                            "tag" -> {
                                queryBuilder.append(" AND tags LIKE ?")
                                args.add("%\"$filterVal\"%")
                            }
                            "space" -> {
                                queryBuilder.append(" AND spaces LIKE ?")
                                args.add("%\"$filterVal\"%")
                            }
                            "subspace" -> {
                                val parts = filterVal.split(" › ")
                                if (parts.size >= 2) {
                                    queryBuilder.append(" AND spaces LIKE ? AND spaces LIKE ?")
                                    args.add("%\"${parts[0]}\"%")
                                    args.add("%\"${parts[1]}\"%")
                                } else {
                                    queryBuilder.append(" AND spaces LIKE ?")
                                    args.add("%\"$filterVal\"%")
                                }
                            }
                            "date" -> {
                                when (filterVal.lowercase()) {
                                    "today" -> queryBuilder.append(" AND substr(due, 1, 10) = date('now', 'localtime')")
                                    "tomorrow" -> queryBuilder.append(" AND substr(due, 1, 10) = date('now', 'localtime', '+1 day')")
                                    "overdue" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) < date('now', 'localtime')")
                                    "next 7 days" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) >= date('now', 'localtime') AND substr(due, 1, 10) <= date('now', 'localtime', '+7 days')")
                                    "upcoming" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) >= date('now', 'localtime')")
                                    "no due date" -> queryBuilder.append(" AND (due IS NULL OR due = '')")
                                }
                            }
                        }
                    }

                    // Exclusion: Recurring tasks
                    if (hideRecurring) {
                        queryBuilder.append(" AND (is_recurring = 0 OR is_recurring IS NULL) AND (recurrence_type IS NULL OR recurrence_type = '')")
                    }

                    // Exclusion: Hidden lists
                    if (!hiddenListsJson.isNullOrBlank()) {
                        try {
                            val arr = JSONArray(hiddenListsJson)
                            val hiddenLists = mutableListOf<String>()
                            for (i in 0 until arr.length()) {
                                val s = arr.getString(i).trim()
                                if (s.isNotEmpty()) hiddenLists.add(s)
                            }
                            if (hiddenLists.isNotEmpty()) {
                                val placeholders = hiddenLists.map { "?" }.joinToString(",")
                                queryBuilder.append(" AND (list_title IS NULL OR list_title NOT IN ($placeholders))")
                                args.addAll(hiddenLists)
                            }
                        } catch (_: Exception) {}
                    }

                    // Exclusion: Hidden tags
                    if (!hiddenTagsJson.isNullOrBlank()) {
                        try {
                            val arr = JSONArray(hiddenTagsJson)
                            for (i in 0 until arr.length()) {
                                val t = arr.getString(i).trim()
                                if (t.isNotEmpty()) {
                                    queryBuilder.append(" AND (tags IS NULL OR tags NOT LIKE ?)")
                                    args.add("%\"$t\"%")
                                }
                            }
                        } catch (_: Exception) {}
                    }

                    val cursor = db.rawQuery(queryBuilder.toString(), args.toTypedArray())
                    cursor.use {
                        if (it.moveToFirst()) it.getInt(0) else 0
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error reading filtered task count", e)
                0
            }
        }

        private fun completeTaskInDb(context: Context, taskId: String) {
            try {
                val dbFile = context.getDatabasePath("gtasks_local.db")
                if (!dbFile.exists()) return

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
                    db.update("tasks", cv, "id = ?", arrayOf(taskId))
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error completing task $taskId", e)
            }
        }
    }

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (appWidgetId in appWidgetIds) {
            try {
                updateAppWidget(context, appWidgetManager, appWidgetId)
            } catch (e: Exception) {
                Log.e(TAG, "Error updating widget $appWidgetId", e)
            }
        }
        super.onUpdate(context, appWidgetManager, appWidgetIds)
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        try {
            when (intent.action) {
                ACTION_REFRESH, AppWidgetManager.ACTION_APPWIDGET_UPDATE -> {
                    updateAllWidgets(context)
                }
                ACTION_QUICK_SYNC -> {
                    Toast.makeText(context, "Syncing tasks...", Toast.LENGTH_SHORT).show()
                    updateAllWidgets(context)
                }
                ACTION_COMPLETE_TASK -> {
                    val taskId = intent.getStringExtra("task_id")
                    if (!taskId.isNullOrEmpty()) {
                        completeTaskInDb(context, taskId)
                        Toast.makeText(context, "Task completed! ✓", Toast.LENGTH_SHORT).show()
                        updateAllWidgets(context)
                    }
                }
                ACTION_TOGGLE_EXPAND -> {
                    val taskId = intent.getStringExtra("task_id")
                    val appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
                    if (!taskId.isNullOrEmpty() && appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                        val key = "expand_${appWidgetId}_$taskId"
                        val isExpanded = prefs.getBoolean(key, false)
                        prefs.edit().putBoolean(key, !isExpanded).apply()

                        val appWidgetManager = AppWidgetManager.getInstance(context) ?: return
                        appWidgetManager.notifyAppWidgetViewDataChanged(appWidgetId, R.id.widget_list_view)
                    }
                }
                ACTION_TOGGLE_VIEW_MODE -> {
                    val appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
                    if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                        val currentMode = prefs.getString("view_mode_$appWidgetId", "detailed") ?: "detailed"
                        val nextMode = when (currentMode) {
                            "detailed" -> "compact"
                            "compact" -> "two_column"
                            "two_column" -> "two_column_compact"
                            else -> "detailed"
                        }
                        prefs.edit().putString("view_mode_$appWidgetId", nextMode).apply()
                        val label = when (nextMode) {
                            "compact" -> "Compact View (One-liner) ☰"
                            "two_column" -> "2-Column Grid Cards ⊞"
                            "two_column_compact" -> "2-Column Compact Grid ▤"
                            else -> "Detailed Card View 📄"
                        }
                        Toast.makeText(context, label, Toast.LENGTH_SHORT).show()
                        updateAllWidgets(context)
                    }
                }
                ACTION_CLEAR_FILTER -> {
                    val appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
                    if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                        prefs.edit()
                            .remove("filter_type_$appWidgetId")
                            .remove("filter_val_$appWidgetId")
                            .remove("sort_by_$appWidgetId")
                            .remove("hide_recurring_$appWidgetId")
                            .remove("hidden_lists_$appWidgetId")
                            .remove("hidden_tags_$appWidgetId")
                            .apply()
                        updateAllWidgets(context)
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in onReceive", e)
        }
    }

    private fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
        val views = RemoteViews(context.packageName, R.layout.gtasks_widget_layout)

        // Read active filter, sort & exclusions
        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
        val filterType = prefs.getString("filter_type_$appWidgetId", null)
        val filterVal = prefs.getString("filter_val_$appWidgetId", null)
        val sortBy = prefs.getString("sort_by_$appWidgetId", "priority")
        val hideRecurring = prefs.getBoolean("hide_recurring_$appWidgetId", false)
        val hiddenListsJson = prefs.getString("hidden_lists_$appWidgetId", null)
        val hiddenTagsJson = prefs.getString("hidden_tags_$appWidgetId", null)
        val viewMode = prefs.getString("view_mode_$appWidgetId", "detailed") ?: "detailed"

        val count = getFilteredTaskCount(context, appWidgetId)

        // Update view mode icon
        val viewIconRes = when (viewMode) {
            "compact" -> R.drawable.ic_widget_view_compact
            "two_column" -> R.drawable.ic_widget_view_grid
            "two_column_compact" -> R.drawable.ic_widget_view_grid_compact
            else -> R.drawable.ic_widget_view_detailed
        }
        views.setImageViewResource(R.id.widget_btn_view_mode, viewIconRes)

        // Format active filter, exclusions & sort badge pill
        val filterLabel = when (filterType) {
            "space" -> "Space: $filterVal"
            "subspace" -> filterVal
            "tag" -> "#$filterVal"
            "list" -> "List: $filterVal"
            "account" -> "@$filterVal"
            "date" -> "📅 $filterVal"
            else -> null
        }
        val sortLabel = when (sortBy) {
            "due_asc" -> "Due ↑"
            "due_desc" -> "Due ↓"
            "modified" -> "Modified"
            "created" -> "Created"
            "title" -> "Title A-Z"
            else -> null
        }

        val hiddenLists = mutableListOf<String>()
        if (!hiddenListsJson.isNullOrBlank()) {
            try {
                val arr = JSONArray(hiddenListsJson)
                for (i in 0 until arr.length()) {
                    val s = arr.getString(i).trim()
                    if (s.isNotEmpty()) hiddenLists.add(s)
                }
            } catch (_: Exception) {}
        }

        val hiddenTags = mutableListOf<String>()
        if (!hiddenTagsJson.isNullOrBlank()) {
            try {
                val arr = JSONArray(hiddenTagsJson)
                for (i in 0 until arr.length()) {
                    val s = arr.getString(i).trim()
                    if (s.isNotEmpty()) hiddenTags.add(s)
                }
            } catch (_: Exception) {}
        }

        val pillParts = mutableListOf<String>()
        if (!filterLabel.isNullOrBlank()) pillParts.add(filterLabel)
        if (hideRecurring) pillParts.add("No Recurring")
        if (hiddenLists.isNotEmpty()) {
            pillParts.add(if (hiddenLists.size == 1) "Hide: ${hiddenLists[0]}" else "Hide: ${hiddenLists.size} lists")
        }
        if (hiddenTags.isNotEmpty()) {
            pillParts.add(if (hiddenTags.size == 1) "Hide: #${hiddenTags[0]}" else "Hide: ${hiddenTags.size} tags")
        }
        if (!sortLabel.isNullOrBlank()) pillParts.add("Sort: $sortLabel")
        if (viewMode == "compact") pillParts.add("1-Line")
        if (viewMode == "two_column") pillParts.add("2-Col")
        if (viewMode == "two_column_compact") pillParts.add("2-Col Compact")

        val pillText = if (pillParts.isNotEmpty()) pillParts.joinToString(" • ") else null

        if (pillText != null) {
            views.setViewVisibility(R.id.widget_active_filter_container, View.VISIBLE)
            views.setTextViewText(R.id.widget_active_filter_text, pillText)
            views.setTextViewText(R.id.widget_task_count, "$count tasks")
        } else {
            views.setViewVisibility(R.id.widget_active_filter_container, View.GONE)
            views.setTextViewText(R.id.widget_task_count, if (count == 0) "All caught up" else "$count pending tasks")
        }

        // Set up service adapter for ListView and GridView
        val serviceIntent = Intent(context, GTasksWidgetService::class.java).apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
            data = Uri.parse("gtasks-widget://widget/id/$appWidgetId?mode=$viewMode&t=${System.currentTimeMillis()}")
        }

        // Item click template (Broadcasts to provider to handle complete, expand, or open)
        val itemTemplateIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        val itemTemplatePendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + 20,
            itemTemplateIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )

        // Toggle Empty View vs List View
        if (count == 0) {
            views.setViewVisibility(R.id.widget_empty_view, View.VISIBLE)
            views.setViewVisibility(R.id.widget_list_view, View.GONE)
        } else {
            views.setViewVisibility(R.id.widget_empty_view, View.GONE)
            views.setViewVisibility(R.id.widget_list_view, View.VISIBLE)
            views.setRemoteAdapter(R.id.widget_list_view, serviceIntent)
            views.setEmptyView(R.id.widget_list_view, R.id.widget_empty_view)
            views.setPendingIntentTemplate(R.id.widget_list_view, itemTemplatePendingIntent)
        }

        // Header click -> opens MainActivity
        val openAppIntent = Intent(context, MainActivity::class.java).apply {
            action = Intent.ACTION_MAIN
            addCategory(Intent.CATEGORY_LAUNCHER)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openAppPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 100 + 0,
            openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_root, openAppPendingIntent)
        views.setOnClickPendingIntent(R.id.widget_header, openAppPendingIntent)

        // View Mode Button
        val toggleViewIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            action = ACTION_TOGGLE_VIEW_MODE
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        val toggleViewPendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + 5,
            toggleViewIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_view_mode, toggleViewPendingIntent)

        // Add Task Button -> Opens Full Screen In-App Task Editor with all features
        val addTaskIntent = Intent(context, MainActivity::class.java).apply {
            action = "com.gtasks.gtasks_app.ACTION_NEW_TASK"
            putExtra("open_task_editor", true)
            putExtra("is_from_widget", true)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val addTaskPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 100 + 1,
            addTaskIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_add, addTaskPendingIntent)
        views.setOnClickPendingIntent(R.id.widget_empty_view, addTaskPendingIntent)

        // Refresh Button
        val refreshIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            action = ACTION_REFRESH
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, intArrayOf(appWidgetId))
        }
        val refreshPendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + 2,
            refreshIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_refresh, refreshPendingIntent)

        // Quick Sync Button
        val syncIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            action = ACTION_QUICK_SYNC
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, intArrayOf(appWidgetId))
        }
        val syncPendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + 3,
            syncIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_sync, syncPendingIntent)

        // Clear Filter Button on Active Filter Pill
        val clearFilterIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            action = ACTION_CLEAR_FILTER
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        val clearFilterPendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + 4,
            clearFilterIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_clear_filter, clearFilterPendingIntent)

        // Filter Buttons -> Open WidgetFilterActivity
        fun setupFilterButton(viewId: Int, filterTypeStr: String, reqCodeOffset: Int) {
            val filterIntent = Intent(context, WidgetFilterActivity::class.java).apply {
                putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
                putExtra("filter_type", filterTypeStr)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            val filterPendingIntent = PendingIntent.getActivity(
                context,
                appWidgetId * 100 + reqCodeOffset,
                filterIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(viewId, filterPendingIntent)
        }

        setupFilterButton(R.id.widget_filter_list, "list", 10)
        setupFilterButton(R.id.widget_filter_tag, "tag", 11)
        setupFilterButton(R.id.widget_filter_space, "space", 12)
        setupFilterButton(R.id.widget_filter_subspace, "subspace", 13)
        setupFilterButton(R.id.widget_filter_account, "account", 14)
        setupFilterButton(R.id.widget_filter_date, "date", 15)
        setupFilterButton(R.id.widget_filter_recurring, "recurring", 16)
        setupFilterButton(R.id.widget_filter_sort, "sort", 17)
        setupFilterButton(R.id.widget_filter_hide, "hide", 18)

        appWidgetManager.updateAppWidget(appWidgetId, views)
    }
}
