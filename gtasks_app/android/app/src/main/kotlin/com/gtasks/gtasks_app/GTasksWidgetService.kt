package com.gtasks.gtasks_app

import android.appwidget.AppWidgetManager
import android.content.Context
import android.content.Intent
import android.database.sqlite.SQLiteDatabase
import android.graphics.Color
import android.util.Log
import android.view.View
import android.widget.RemoteViews
import android.widget.RemoteViewsService
import org.json.JSONArray
import org.json.JSONObject

class GTasksWidgetService : RemoteViewsService() {
    override fun onGetViewFactory(intent: Intent): RemoteViewsFactory {
        val appWidgetId = intent.getIntExtra(
            AppWidgetManager.EXTRA_APPWIDGET_ID,
            AppWidgetManager.INVALID_APPWIDGET_ID
        )
        return GTasksRemoteViewsFactory(applicationContext, appWidgetId)
    }
}

class GTasksRemoteViewsFactory(
    private val context: Context,
    private val appWidgetId: Int
) : RemoteViewsService.RemoteViewsFactory {

    companion object {
        private const val TAG = "GTasksWidgetService"
    }

    data class WidgetTaskItem(
        val id: String,
        val title: String,
        val description: String?,
        val priority: String,
        val due: String?,
        val listTitle: String?,
        val spacesJson: String?,
        val tagsJson: String?,
        val account: String?
    )

    private val tasks = mutableListOf<WidgetTaskItem>()

    override fun onCreate() {}

    override fun onDataSetChanged() {
        tasks.clear()
        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (!dbFile.exists()) return

            val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
            val filterType = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                prefs.getString("filter_type_$appWidgetId", null)
            } else null
            val filterVal = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                prefs.getString("filter_val_$appWidgetId", null)
            } else null
            val sortBy = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                prefs.getString("sort_by_$appWidgetId", "priority")
            } else "priority"
            val hideRecurring = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                prefs.getBoolean("hide_recurring_$appWidgetId", false)
            } else false
            val hiddenListsJson = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                prefs.getString("hidden_lists_$appWidgetId", null)
            } else null
            val hiddenTagsJson = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                prefs.getString("hidden_tags_$appWidgetId", null)
            } else null

            SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                val checkCursor = db.rawQuery(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'",
                    null
                )
                val tableExists = checkCursor.use { it.moveToFirst() }
                if (!tableExists) return

                val queryBuilder = StringBuilder(
                    """
                    SELECT id, title, description, priority, due, list_title, spaces, tags, account 
                    FROM tasks 
                    WHERE status != 'completed' AND sync_status != 'pending_delete'
                    """.trimIndent()
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

                val orderByClause = when (sortBy) {
                    "due_asc" -> """
                        CASE WHEN due IS NOT NULL AND due != '' THEN 0 ELSE 1 END,
                        due ASC,
                        CASE priority 
                            WHEN 'critical' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                            ELSE 5 
                        END
                    """.trimIndent()
                    "due_desc" -> """
                        CASE WHEN due IS NOT NULL AND due != '' THEN 0 ELSE 1 END,
                        due DESC
                    """.trimIndent()
                    "modified" -> "modified_at DESC"
                    "created" -> "created_at DESC"
                    "title" -> "title COLLATE NOCASE ASC"
                    else -> """
                        CASE priority 
                            WHEN 'critical' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                            ELSE 5 
                        END, 
                        CASE WHEN due IS NOT NULL AND due != '' THEN 0 ELSE 1 END,
                        due ASC
                    """.trimIndent()
                }

                queryBuilder.append(" ORDER BY $orderByClause LIMIT 60")

                val cursor = db.rawQuery(queryBuilder.toString(), args.toTypedArray())
                cursor.use {
                    while (it.moveToNext()) {
                        val id = it.getString(0) ?: ""
                        val title = it.getString(1) ?: "Untitled Task"
                        val desc = it.getString(2)
                        val priority = it.getString(3) ?: "normal"
                        val due = it.getString(4)
                        val listTitle = it.getString(5)
                        val spacesJson = it.getString(6)
                        val tagsJson = it.getString(7)
                        val account = it.getString(8)
                        tasks.add(WidgetTaskItem(id, title, desc, priority, due, listTitle, spacesJson, tagsJson, account))
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in onDataSetChanged", e)
        }
    }

    override fun onDestroy() {
        tasks.clear()
    }

    override fun getCount(): Int {
        val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
        val viewMode = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
            prefs.getString("view_mode_$appWidgetId", "detailed") ?: "detailed"
        } else "detailed"
        return if (viewMode == "two_column" || viewMode == "two_column_compact") (tasks.size + 1) / 2 else tasks.size
    }

    override fun getViewAt(position: Int): RemoteViews {
        try {
            val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
            val viewMode = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                prefs.getString("view_mode_$appWidgetId", "detailed") ?: "detailed"
            } else "detailed"

            if (viewMode == "two_column" || viewMode == "two_column_compact") {
                // 2-COLUMN VIEW (Cards or Compact One-Liners)
                val layoutRes = if (viewMode == "two_column_compact") {
                    R.layout.gtasks_widget_item_2col_compact_row
                } else {
                    R.layout.gtasks_widget_item_2col_row
                }
                val leftIdx = position * 2
                val rightIdx = position * 2 + 1
                if (leftIdx < 0 || leftIdx >= tasks.size) {
                    return RemoteViews(context.packageName, layoutRes)
                }

                val itemLeft = tasks[leftIdx]
                val views = RemoteViews(context.packageName, layoutRes)

                // Fill-in Intent for completing left task directly from widget
                val completeLeftIntent = Intent().apply {
                    action = GTasksWidgetProvider.ACTION_COMPLETE_TASK
                    putExtra("task_id", itemLeft.id)
                }
                val clickLeftIntent = Intent().apply {
                    action = GTasksWidgetProvider.ACTION_TOGGLE_EXPAND
                    putExtra("task_id", itemLeft.id)
                }

                // Bind Left Column
                views.setTextViewText(R.id.widget_item_title_left, itemLeft.title)

                val priorityLeft = itemLeft.priority.lowercase()
                when (priorityLeft) {
                    "critical" -> {
                        views.setViewVisibility(R.id.widget_item_priority_left, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_priority_left, "CRIT")
                        views.setTextColor(R.id.widget_item_priority_left, Color.parseColor("#EF4444"))
                    }
                    "high" -> {
                        views.setViewVisibility(R.id.widget_item_priority_left, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_priority_left, "HIGH")
                        views.setTextColor(R.id.widget_item_priority_left, Color.parseColor("#F97316"))
                    }
                    "medium" -> {
                        views.setViewVisibility(R.id.widget_item_priority_left, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_priority_left, "MED")
                        views.setTextColor(R.id.widget_item_priority_left, Color.parseColor("#EAB308"))
                    }
                    else -> {
                        views.setViewVisibility(R.id.widget_item_priority_left, View.GONE)
                    }
                }

                val subLeftParts = mutableListOf<String>()
                if (!itemLeft.due.isNullOrBlank()) {
                    val d = itemLeft.due
                    subLeftParts.add(if (d.length >= 10) d.substring(5, 10) else d)
                }
                if (!itemLeft.spacesJson.isNullOrBlank() && itemLeft.spacesJson != "{}") {
                    try {
                        val json = JSONObject(itemLeft.spacesJson)
                        val keys = json.keys()
                        if (keys.hasNext()) subLeftParts.add(keys.next())
                    } catch (_: Exception) {}
                }
                if (subLeftParts.isNotEmpty()) {
                    views.setViewVisibility(R.id.widget_item_subtitle_left, View.VISIBLE)
                    views.setTextViewText(R.id.widget_item_subtitle_left, subLeftParts.joinToString(" • "))
                } else {
                    views.setViewVisibility(R.id.widget_item_subtitle_left, View.GONE)
                }

                views.setOnClickFillInIntent(R.id.widget_item_check_left, completeLeftIntent)
                views.setOnClickFillInIntent(R.id.widget_col_left, clickLeftIntent)
                views.setOnClickFillInIntent(R.id.widget_item_title_left, clickLeftIntent)

                // Bind Right Column (if available in this pair)
                if (rightIdx < tasks.size) {
                    val itemRight = tasks[rightIdx]
                    views.setViewVisibility(R.id.widget_col_right, View.VISIBLE)
                    views.setTextViewText(R.id.widget_item_title_right, itemRight.title)

                    val priorityRight = itemRight.priority.lowercase()
                    when (priorityRight) {
                        "critical" -> {
                            views.setViewVisibility(R.id.widget_item_priority_right, View.VISIBLE)
                            views.setTextViewText(R.id.widget_item_priority_right, "CRIT")
                            views.setTextColor(R.id.widget_item_priority_right, Color.parseColor("#EF4444"))
                        }
                        "high" -> {
                            views.setViewVisibility(R.id.widget_item_priority_right, View.VISIBLE)
                            views.setTextViewText(R.id.widget_item_priority_right, "HIGH")
                            views.setTextColor(R.id.widget_item_priority_right, Color.parseColor("#F97316"))
                        }
                        "medium" -> {
                            views.setViewVisibility(R.id.widget_item_priority_right, View.VISIBLE)
                            views.setTextViewText(R.id.widget_item_priority_right, "MED")
                            views.setTextColor(R.id.widget_item_priority_right, Color.parseColor("#EAB308"))
                        }
                        else -> {
                            views.setViewVisibility(R.id.widget_item_priority_right, View.GONE)
                        }
                    }

                    val subRightParts = mutableListOf<String>()
                    if (!itemRight.due.isNullOrBlank()) {
                        val d = itemRight.due
                        subRightParts.add(if (d.length >= 10) d.substring(5, 10) else d)
                    }
                    if (!itemRight.spacesJson.isNullOrBlank() && itemRight.spacesJson != "{}") {
                        try {
                            val json = JSONObject(itemRight.spacesJson)
                            val keys = json.keys()
                            if (keys.hasNext()) subRightParts.add(keys.next())
                        } catch (_: Exception) {}
                    }
                    if (subRightParts.isNotEmpty()) {
                        views.setViewVisibility(R.id.widget_item_subtitle_right, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_subtitle_right, subRightParts.joinToString(" • "))
                    } else {
                        views.setViewVisibility(R.id.widget_item_subtitle_right, View.GONE)
                    }

                    val completeRightIntent = Intent().apply {
                        action = GTasksWidgetProvider.ACTION_COMPLETE_TASK
                        putExtra("task_id", itemRight.id)
                    }
                    val clickRightIntent = Intent().apply {
                        action = GTasksWidgetProvider.ACTION_TOGGLE_EXPAND
                        putExtra("task_id", itemRight.id)
                    }
                    views.setOnClickFillInIntent(R.id.widget_item_check_right, completeRightIntent)
                    views.setOnClickFillInIntent(R.id.widget_col_right, clickRightIntent)
                    views.setOnClickFillInIntent(R.id.widget_item_title_right, clickRightIntent)
                } else {
                    // Hide right column cleanly to keep left column 50% width without blank content
                    views.setViewVisibility(R.id.widget_col_right, View.INVISIBLE)
                }

                return views
            }

            if (position < 0 || position >= tasks.size) {
                return RemoteViews(context.packageName, R.layout.gtasks_widget_item)
            }

            val item = tasks[position]

            // Fill-in Intent for completing task directly from widget
            val completeFillInIntent = Intent().apply {
                action = GTasksWidgetProvider.ACTION_COMPLETE_TASK
                putExtra("task_id", item.id)
            }

            // Fill-in Intent for expanding/collapsing or opening task
            val toggleExpandFillInIntent = Intent().apply {
                action = GTasksWidgetProvider.ACTION_TOGGLE_EXPAND
                putExtra("task_id", item.id)
            }

            if (viewMode == "compact") {
                // ONE-LINER VIEW
                val views = RemoteViews(context.packageName, R.layout.gtasks_widget_item_compact)
                views.setTextViewText(R.id.widget_item_title, item.title)

                // Priority
                val priority = item.priority.lowercase()
                when (priority) {
                    "critical" -> {
                        views.setViewVisibility(R.id.widget_item_priority, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_priority, "CRIT")
                        views.setTextColor(R.id.widget_item_priority, Color.parseColor("#EF4444"))
                    }
                    "high" -> {
                        views.setViewVisibility(R.id.widget_item_priority, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_priority, "HIGH")
                        views.setTextColor(R.id.widget_item_priority, Color.parseColor("#F97316"))
                    }
                    "medium" -> {
                        views.setViewVisibility(R.id.widget_item_priority, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_priority, "MED")
                        views.setTextColor(R.id.widget_item_priority, Color.parseColor("#EAB308"))
                    }
                    else -> {
                        views.setViewVisibility(R.id.widget_item_priority, View.GONE)
                    }
                }

                // Compact right-side label: Due date or Space or List
                val rightLabel = when {
                    !item.due.isNullOrBlank() -> {
                        val d = item.due
                        if (d.length >= 10) d.substring(5, 10) else d
                    }
                    !item.spacesJson.isNullOrBlank() && item.spacesJson != "{}" -> {
                        try {
                            val json = JSONObject(item.spacesJson)
                            val keys = json.keys()
                            if (keys.hasNext()) keys.next() else null
                        } catch (_: Exception) { null }
                    }
                    !item.listTitle.isNullOrBlank() && item.listTitle != "My Tasks" -> item.listTitle
                    else -> null
                }

                if (rightLabel != null) {
                    views.setViewVisibility(R.id.widget_item_subtitle, View.VISIBLE)
                    views.setTextViewText(R.id.widget_item_subtitle, rightLabel)
                } else {
                    views.setViewVisibility(R.id.widget_item_subtitle, View.GONE)
                }

                views.setOnClickFillInIntent(R.id.widget_item_check, completeFillInIntent)
                views.setOnClickFillInIntent(R.id.widget_item_container, toggleExpandFillInIntent)
                views.setOnClickFillInIntent(R.id.widget_item_title, toggleExpandFillInIntent)

                return views
            }

            // DETAILED CARD VIEW
            val views = RemoteViews(context.packageName, R.layout.gtasks_widget_item)
            views.setTextViewText(R.id.widget_item_title, item.title)

                    // Priority badge styling
                    val priority = item.priority.lowercase()
                    when (priority) {
                        "critical" -> {
                            views.setViewVisibility(R.id.widget_item_priority, View.VISIBLE)
                            views.setTextViewText(R.id.widget_item_priority, "CRITICAL")
                            views.setTextColor(R.id.widget_item_priority, Color.parseColor("#EF4444"))
                        }
                        "high" -> {
                            views.setViewVisibility(R.id.widget_item_priority, View.VISIBLE)
                            views.setTextViewText(R.id.widget_item_priority, "HIGH")
                            views.setTextColor(R.id.widget_item_priority, Color.parseColor("#F97316"))
                        }
                        "medium" -> {
                            views.setViewVisibility(R.id.widget_item_priority, View.VISIBLE)
                            views.setTextViewText(R.id.widget_item_priority, "MED")
                            views.setTextColor(R.id.widget_item_priority, Color.parseColor("#EAB308"))
                        }
                        else -> {
                            views.setViewVisibility(R.id.widget_item_priority, View.GONE)
                        }
                    }

                    // Subtitle: Space › Subspace • Due • List
                    val parts = mutableListOf<String>()

                    if (!item.spacesJson.isNullOrBlank() && item.spacesJson != "{}") {
                        try {
                            val json = JSONObject(item.spacesJson)
                            val keys = json.keys()
                            if (keys.hasNext()) {
                                val space = keys.next()
                                val subs = json.optJSONArray(space)
                                if (subs != null && subs.length() > 0) {
                                    parts.add("$space › ${subs.getString(0)}")
                                } else {
                                    parts.add(space)
                                }
                            }
                        } catch (_: Exception) {}
                    }

                    if (!item.listTitle.isNullOrBlank() && item.listTitle != "My Tasks") {
                        parts.add(item.listTitle)
                    }

                    if (!item.due.isNullOrBlank()) {
                        val dueFormatted = if (item.due.length >= 10) item.due.substring(0, 10) else item.due
                        parts.add("Due $dueFormatted")
                    }

                    if (parts.isNotEmpty()) {
                        views.setViewVisibility(R.id.widget_item_subtitle, View.VISIBLE)
                        views.setTextViewText(R.id.widget_item_subtitle, parts.joinToString(" • "))
                    } else {
                        views.setViewVisibility(R.id.widget_item_subtitle, View.GONE)
                    }

                    // Expand / Collapse details logic
                    val isExpanded = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                        prefs.getBoolean("expand_${appWidgetId}_${item.id}", false)
                    } else false

                    if (isExpanded) {
                        views.setViewVisibility(R.id.widget_item_notes, View.VISIBLE)
                        views.setImageViewResource(R.id.widget_item_chevron, R.drawable.ic_widget_chevron_up)

                        val detailBuilder = StringBuilder()
                        if (!item.description.isNullOrBlank()) {
                            detailBuilder.append(item.description.trim())
                        }
                        if (!item.tagsJson.isNullOrBlank() && item.tagsJson != "[]") {
                            try {
                                val tagArray = JSONArray(item.tagsJson)
                                val tagList = mutableListOf<String>()
                                for (i in 0 until tagArray.length()) {
                                    val tag = tagArray.getString(i).trim()
                                    if (tag.isNotEmpty()) tagList.add("#$tag")
                                }
                                if (tagList.isNotEmpty()) {
                                    if (detailBuilder.isNotEmpty()) detailBuilder.append("\n")
                                    detailBuilder.append(tagList.joinToString(" "))
                                }
                            } catch (_: Exception) {}
                        }
                        if (detailBuilder.isEmpty()) {
                            detailBuilder.append("No additional details")
                        }
                        views.setTextViewText(R.id.widget_item_notes, detailBuilder.toString())
                    } else {
                        views.setViewVisibility(R.id.widget_item_notes, View.GONE)
                        views.setImageViewResource(R.id.widget_item_chevron, R.drawable.ic_widget_chevron)
                    }

                    views.setOnClickFillInIntent(R.id.widget_item_check, completeFillInIntent)
                    views.setOnClickFillInIntent(R.id.widget_item_container, toggleExpandFillInIntent)
                    views.setOnClickFillInIntent(R.id.widget_item_chevron, toggleExpandFillInIntent)
                    views.setOnClickFillInIntent(R.id.widget_item_title, toggleExpandFillInIntent)
                    views.setOnClickFillInIntent(R.id.widget_item_subtitle, toggleExpandFillInIntent)
                    views.setOnClickFillInIntent(R.id.widget_item_notes, toggleExpandFillInIntent)

            return views
        } catch (e: Exception) {
            Log.e(TAG, "Error in getViewAt for position $position", e)
            return RemoteViews(context.packageName, R.layout.gtasks_widget_item)
        }
    }

    override fun getLoadingView(): RemoteViews? = null

    override fun getViewTypeCount(): Int = 4

    override fun getItemId(position: Int): Long = position.toLong()

    override fun hasStableIds(): Boolean = false
}
