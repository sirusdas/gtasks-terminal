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
import org.json.JSONObject
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
        const val ACTION_OPEN_TASK_PREVIEW = "com.gtasks.gtasks_app.ACTION_OPEN_TASK_PREVIEW"
        const val ACTION_PREV_TAB = "com.gtasks.gtasks_app.ACTION_PREV_TAB"
        const val ACTION_NEXT_TAB = "com.gtasks.gtasks_app.ACTION_NEXT_TAB"
        const val ACTION_OPEN_TAB = "com.gtasks.gtasks_app.ACTION_OPEN_TAB"

        private var isSyncing = false
        private var lastSyncTimestamp = 0L

        data class WidgetTab(
            val id: String,
            val title: String,
            val filterType: String?,
            val filterVal: String?,
            val account: String? = null
        )

        fun getAvailableTabs(context: Context): List<WidgetTab> {
            val tabs = mutableListOf<WidgetTab>()

            // Try reading user-configured browser tabs from app SharedPreferences
            try {
                val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                val tabsJson = prefs.getString("tabs_json", null)
                if (!tabsJson.isNullOrEmpty()) {
                    val arr = JSONArray(tabsJson)
                    for (i in 0 until arr.length()) {
                        val obj = arr.getJSONObject(i)
                        val id = obj.optString("id", "tab_$i")
                        val title = obj.optString("title", "Tab ${i + 1}")
                        val filterType = obj.optString("filterType").ifEmpty { null }
                        val filterVal = obj.optString("filterVal").ifEmpty { null }
                        val account = obj.optString("account").ifEmpty { null }
                        tabs.add(WidgetTab(id, title, filterType, filterVal, account))
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error parsing tabs_json in widget", e)
            }

            if (tabs.isNotEmpty()) {
                return tabs
            }

            // Fallback default tabs if not yet synced from app
            tabs.add(WidgetTab("all", "✦ All Tasks", null, null))
            tabs.add(WidgetTab("today", "⏰ Today & Due", "date", "today"))
            tabs.add(WidgetTab("priority", "🔥 High Priority", "priority", "high"))

            try {
                val dbFile = context.getDatabasePath("gtasks_local.db")
                if (dbFile.exists()) {
                    SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                        val checkCursor = db.rawQuery(
                            "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'",
                            null
                        )
                        if (checkCursor.use { it.moveToFirst() }) {
                            val cursor = db.rawQuery(
                                "SELECT spaces FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete' AND spaces IS NOT NULL AND spaces != '' AND spaces != '{}'",
                                null
                            )
                            val discoveredSpaces = sortedSetOf<String>()
                            cursor.use {
                                while (it.moveToNext()) {
                                    val spacesJson = it.getString(0) ?: continue
                                    try {
                                        val json = JSONObject(spacesJson)
                                        val keys = json.keys()
                                        while (keys.hasNext()) {
                                            val spaceName = keys.next().trim()
                                            if (spaceName.isNotEmpty()) {
                                                discoveredSpaces.add(spaceName)
                                            }
                                        }
                                    } catch (_: Exception) {}
                                }
                            }
                            for (space in discoveredSpaces) {
                                tabs.add(WidgetTab("space:$space", "🚀 $space", "space", space))
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error discovering spaces for tabs", e)
            }

            return tabs
        }

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

                    val filter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId)
                    val queryBuilder = StringBuilder(
                        "SELECT COUNT(*) FROM tasks WHERE sync_status != 'pending_delete'"
                    )
                    val args = mutableListOf<String>()
                    WidgetTabFilter.applyFilterToQuery(filter, queryBuilder, args)

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
                    val now = System.currentTimeMillis()
                    if (isSyncing || (now - lastSyncTimestamp < 4000L)) {
                        Toast.makeText(context, "Sync is already in progress...", Toast.LENGTH_SHORT).show()
                    } else {
                        isSyncing = true
                        lastSyncTimestamp = now
                        Toast.makeText(context, "Syncing tasks...", Toast.LENGTH_SHORT).show()
                        updateAllWidgets(context)
                        android.os.Handler(android.os.Looper.getMainLooper()).postDelayed({
                            isSyncing = false
                        }, 3500L)
                    }
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
                ACTION_PREV_TAB -> {
                    val appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
                    if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                        val tabs = WidgetTabFilter.getAvailableTabs(context)
                        val currentIndex = prefs.getInt("tab_index_$appWidgetId", 0)
                        val newIndex = (currentIndex - 1 + tabs.size) % tabs.size
                        val tab = tabs[newIndex]
                        prefs.edit().putInt("tab_index_$appWidgetId", newIndex).apply()
                        Toast.makeText(context, "${tab.title} (${newIndex + 1}/${tabs.size})", Toast.LENGTH_SHORT).show()
                        updateAllWidgets(context)
                    }
                }
                ACTION_NEXT_TAB -> {
                    val appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
                    if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                        val tabs = WidgetTabFilter.getAvailableTabs(context)
                        val currentIndex = prefs.getInt("tab_index_$appWidgetId", 0)
                        val newIndex = (currentIndex + 1) % tabs.size
                        val tab = tabs[newIndex]
                        prefs.edit().putInt("tab_index_$appWidgetId", newIndex).apply()
                        Toast.makeText(context, "${tab.title} (${newIndex + 1}/${tabs.size})", Toast.LENGTH_SHORT).show()
                        updateAllWidgets(context)
                    }
                }
                ACTION_OPEN_TASK_PREVIEW -> {
                    val taskId = intent.getStringExtra("task_id")
                    if (!taskId.isNullOrEmpty()) {
                        val openTaskIntent = Intent(context, MainActivity::class.java).apply {
                            action = ACTION_OPEN_TASK_PREVIEW
                            putExtra("open_task_id", taskId)
                            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
                        }
                        context.startActivity(openTaskIntent)
                    }
                }
                ACTION_CLEAR_FILTER -> {
                    val appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
                    if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                        prefs.edit()
                            .remove("tab_index_$appWidgetId")
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

        // Read active filter, sort & exclusions via WidgetTabFilter
        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
        val filter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId)
        val sortBy = prefs.getString("sort_by_$appWidgetId", filter.sortBy) ?: filter.sortBy
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

        // ----------------------------------------------------
        // Tab Navigation Strip (Next & Prev buttons & active tab pill)
        // ----------------------------------------------------
        views.setTextViewText(R.id.widget_tab_title, filter.title)
        views.setTextViewText(R.id.widget_tab_badge, "($count) • ${filter.tabIndex + 1}/${filter.totalTabs}")

        // Prev Tab Button ◀
        val prevTabIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            action = ACTION_PREV_TAB
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        val prevTabPendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + 41,
            prevTabIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_tab_prev, prevTabPendingIntent)

        // Next Tab Button ▶
        val nextTabIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            action = ACTION_NEXT_TAB
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        val nextTabPendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + 42,
            nextTabIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_tab_next, nextTabPendingIntent)

        // Center Tab Pill -> Opens In-App scoped to this Tab
        val openTabIntent = Intent(context, MainActivity::class.java).apply {
            action = ACTION_OPEN_TAB
            putExtra("open_tab_id", filter.id)
            if (!filter.filterType.isNullOrBlank() && !filter.filterVal.isNullOrBlank()) {
                putExtra("tab_filter_type", filter.filterType)
                putExtra("tab_filter_val", filter.filterVal)
            }
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openTabPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 100 + 43,
            openTabIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_tab_center, openTabPendingIntent)

        // Format active filter, exclusions & sort badge pill
        val filterLabel = when (filter.filterType) {
            "space" -> "Space: ${filter.filterVal}"
            "subspace" -> filter.filterVal
            "tag" -> "#${filter.filterVal}"
            "list" -> "List: ${filter.filterVal}"
            "account" -> "@${filter.filterVal}"
            "date" -> "📅 ${filter.filterVal}"
            else -> if (filter.selectedSpace != null) "Space: ${filter.selectedSpace}" else null
        }
        val sortLabel = when (sortBy) {
            "due_asc" -> "Due ↑"
            "due_desc" -> "Due ↓"
            "modified" -> "Modified"
            "created" -> "Created"
            "title" -> "Title A-Z"
            else -> null
        }

        val pillParts = mutableListOf<String>()
        if (!filterLabel.isNullOrBlank()) pillParts.add(filterLabel)
        if (filter.hideRecurring) pillParts.add("No Recurring")
        if (filter.hiddenLists.isNotEmpty()) {
            val hLists = filter.hiddenLists.toList()
            pillParts.add(if (hLists.size == 1) "Hide: ${hLists[0]}" else "Hide: ${hLists.size} lists")
        }
        if (filter.hiddenTags.isNotEmpty()) {
            val hTags = filter.hiddenTags.toList()
            pillParts.add(if (hTags.size == 1) "Hide: #${hTags[0]}" else "Hide: ${hTags.size} tags")
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
        // App Icon click -> only clicking the GTasks icon opens the full app (no accidental opens from background/header)
        views.setOnClickPendingIntent(R.id.widget_app_icon, openAppPendingIntent)

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

        // AI Assistant Button -> Opens AI Chat Screen directly as fullscreen popup with widget context
        val aiIntent = Intent(context, MainActivity::class.java).apply {
            action = "com.gtasks.gtasks_app.ACTION_OPEN_AI"
            putExtra("open_ai_chat", true)
            putExtra("is_from_widget", true)
            if (!filter.filterType.isNullOrBlank() && !filter.filterVal.isNullOrBlank()) {
                putExtra("widget_filter_type", filter.filterType)
                putExtra("widget_filter_val", filter.filterVal)
            }
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val aiPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 100 + 7,
            aiIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_ai, aiPendingIntent)

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
