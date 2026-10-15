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
                    }
                }

                queryBuilder.append(
                    """
                     ORDER BY 
                        CASE priority 
                            WHEN 'critical' THEN 1 
                            WHEN 'high' THEN 2 
                            WHEN 'medium' THEN 3 
                            WHEN 'low' THEN 4 
                            ELSE 5 
                        END, 
                        CASE WHEN due IS NOT NULL AND due != '' THEN 0 ELSE 1 END,
                        due ASC 
                    LIMIT 50
                    """.trimIndent()
                )

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

    override fun getCount(): Int = tasks.size

    override fun getViewAt(position: Int): RemoteViews {
        try {
            val views = RemoteViews(context.packageName, R.layout.gtasks_widget_item)
            if (position < 0 || position >= tasks.size) return views

            val item = tasks[position]
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

            // Extract primary space & subspace if present
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
            val prefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
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

            // Fill-in Intent for completing task directly from widget
            val completeFillInIntent = Intent().apply {
                action = GTasksWidgetProvider.ACTION_COMPLETE_TASK
                putExtra("task_id", item.id)
            }
            views.setOnClickFillInIntent(R.id.widget_item_check, completeFillInIntent)

            // Fill-in Intent for expanding/collapsing details
            val toggleExpandFillInIntent = Intent().apply {
                action = GTasksWidgetProvider.ACTION_TOGGLE_EXPAND
                putExtra("task_id", item.id)
            }
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

    override fun getViewTypeCount(): Int = 1

    override fun getItemId(position: Int): Long = position.toLong()

    override fun hasStableIds(): Boolean = false
}
