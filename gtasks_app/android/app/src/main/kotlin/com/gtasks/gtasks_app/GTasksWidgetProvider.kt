package com.gtasks.gtasks_app

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.database.sqlite.SQLiteDatabase
import android.net.Uri
import android.util.Log
import android.widget.RemoteViews

class GTasksWidgetProvider : AppWidgetProvider() {

    companion object {
        private const val TAG = "GTasksWidgetProvider"
        const val ACTION_REFRESH = "com.gtasks.gtasks_app.ACTION_REFRESH_WIDGET"
        const val ACTION_ADD_TASK = "com.gtasks.gtasks_app.ACTION_ADD_TASK"

        fun updateAllWidgets(context: Context) {
            try {
                val appWidgetManager = AppWidgetManager.getInstance(context) ?: return
                val thisWidget = ComponentName(context, GTasksWidgetProvider::class.java)
                val appWidgetIds = appWidgetManager.getAppWidgetIds(thisWidget) ?: intArrayOf()
                if (appWidgetIds.isNotEmpty()) {
                    appWidgetManager.notifyAppWidgetViewDataChanged(appWidgetIds, R.id.widget_list_view)
                    val intent = Intent(context, GTasksWidgetProvider::class.java).apply {
                        action = AppWidgetManager.ACTION_APPWIDGET_UPDATE
                        putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, appWidgetIds)
                    }
                    context.sendBroadcast(intent)
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error in updateAllWidgets", e)
            }
        }

        fun getPendingTaskCount(context: Context): Int {
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

                    val cursor = db.rawQuery(
                        "SELECT COUNT(*) FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete'",
                        null
                    )
                    cursor.use {
                        if (it.moveToFirst()) it.getInt(0) else 0
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error reading pending task count", e)
                0
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
            if (intent.action == ACTION_REFRESH || intent.action == AppWidgetManager.ACTION_APPWIDGET_UPDATE) {
                val appWidgetManager = AppWidgetManager.getInstance(context) ?: return
                val thisWidget = ComponentName(context, GTasksWidgetProvider::class.java)
                val appWidgetIds = appWidgetManager.getAppWidgetIds(thisWidget) ?: intArrayOf()
                appWidgetManager.notifyAppWidgetViewDataChanged(appWidgetIds, R.id.widget_list_view)
                for (appWidgetId in appWidgetIds) {
                    updateAppWidget(context, appWidgetManager, appWidgetId)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error in onReceive", e)
        }
    }

    private fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
        val views = RemoteViews(context.packageName, R.layout.gtasks_widget_layout)

        // Count pending tasks
        val count = getPendingTaskCount(context)
        views.setTextViewText(R.id.widget_task_count, if (count == 0) "All caught up" else "$count pending tasks")

        // Explicitly set visibility so the widget is never blank on fresh install/empty list
        if (count == 0) {
            views.setViewVisibility(R.id.widget_empty_view, android.view.View.VISIBLE)
            views.setViewVisibility(R.id.widget_list_view, android.view.View.GONE)
        } else {
            views.setViewVisibility(R.id.widget_empty_view, android.view.View.GONE)
            views.setViewVisibility(R.id.widget_list_view, android.view.View.VISIBLE)
        }

        // Set up service adapter for the ListView
        val serviceIntent = Intent(context, GTasksWidgetService::class.java).apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
            data = Uri.parse("gtasks-widget://widget/id/$appWidgetId")
        }
        views.setRemoteAdapter(R.id.widget_list_view, serviceIntent)
        views.setEmptyView(R.id.widget_list_view, R.id.widget_empty_view)

        // PendingIntent for clicking anywhere on the widget (opens app)
        val openAppIntent = Intent(context, MainActivity::class.java).apply {
            action = Intent.ACTION_MAIN
            addCategory(Intent.CATEGORY_LAUNCHER)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openAppPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 10 + 0,
            openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_root, openAppPendingIntent)
        views.setOnClickPendingIntent(R.id.widget_header, openAppPendingIntent)
        views.setOnClickPendingIntent(R.id.widget_empty_view, openAppPendingIntent)

        // PendingIntent for Add Task button
        val addTaskIntent = Intent(context, MainActivity::class.java).apply {
            action = ACTION_ADD_TASK
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val addTaskPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 10 + 1,
            addTaskIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_add, addTaskPendingIntent)

        // PendingIntent for Refresh button
        val refreshIntent = Intent(context, GTasksWidgetProvider::class.java).apply {
            action = ACTION_REFRESH
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_IDS, intArrayOf(appWidgetId))
        }
        val refreshPendingIntent = PendingIntent.getBroadcast(
            context,
            appWidgetId * 10 + 2,
            refreshIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_btn_refresh, refreshPendingIntent)

        // PendingIntent template for clicking list items
        val clickItemIntent = Intent(context, MainActivity::class.java).apply {
            action = Intent.ACTION_VIEW
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val clickItemPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 10 + 3,
            clickItemIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_MUTABLE
        )
        views.setPendingIntentTemplate(R.id.widget_list_view, clickItemPendingIntent)

        appWidgetManager.updateAppWidget(appWidgetId, views)
    }
}
