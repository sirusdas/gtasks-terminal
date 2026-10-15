package com.gtasks.gtasks_app

import android.content.Context
import android.content.Intent
import android.database.sqlite.SQLiteDatabase
import android.graphics.Color
import android.util.Log
import android.view.View
import android.widget.RemoteViews
import android.widget.RemoteViewsService
import org.json.JSONObject

class GTasksWidgetService : RemoteViewsService() {
    override fun onGetViewFactory(intent: Intent): RemoteViewsFactory {
        return GTasksRemoteViewsFactory(applicationContext)
    }
}

class GTasksRemoteViewsFactory(private val context: Context) : RemoteViewsService.RemoteViewsFactory {

    companion object {
        private const val TAG = "GTasksWidgetService"
    }

    data class WidgetTaskItem(
        val id: String,
        val title: String,
        val priority: String,
        val due: String?,
        val listTitle: String?,
        val spacesJson: String?
    )

    private val tasks = mutableListOf<WidgetTaskItem>()

    override fun onCreate() {}

    override fun onDataSetChanged() {
        tasks.clear()
        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (!dbFile.exists()) return

            SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                val checkCursor = db.rawQuery(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'",
                    null
                )
                val tableExists = checkCursor.use { it.moveToFirst() }
                if (!tableExists) return

                val cursor = db.rawQuery(
                    """
                    SELECT id, title, priority, due, list_title, spaces 
                    FROM tasks 
                    WHERE status != 'completed' AND sync_status != 'pending_delete'
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
                    LIMIT 40
                    """.trimIndent(),
                    null
                )

                cursor.use {
                    while (it.moveToNext()) {
                        val id = it.getString(0) ?: ""
                        val title = it.getString(1) ?: "Untitled Task"
                        val priority = it.getString(2) ?: "normal"
                        val due = it.getString(3)
                        val listTitle = it.getString(4)
                        val spacesJson = it.getString(5)
                        tasks.add(WidgetTaskItem(id, title, priority, due, listTitle, spacesJson))
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

            // Subtitle: format Space › Subspace | List | Due
            val parts = mutableListOf<String>()

            // Extract primary space if present
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

            // Fill-in Intent for clicking this item (handled by MainActivity)
            val fillInIntent = Intent().apply {
                putExtra("task_id", item.id)
                putExtra("task_title", item.title)
            }
            views.setOnClickFillInIntent(R.id.widget_item_container, fillInIntent)

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
