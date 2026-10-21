package com.gtasks.gtasks_app

import android.content.Context
import android.content.Intent
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object {
        const val CHANNEL = "com.gtasks.gtasks_app/widget"
        const val ACTION_NEW_TASK = "com.gtasks.gtasks_app.ACTION_NEW_TASK"
        const val ACTION_OPEN_AI = "com.gtasks.gtasks_app.ACTION_OPEN_AI"
        const val ACTION_OPEN_TASK_PREVIEW = "com.gtasks.gtasks_app.ACTION_OPEN_TASK_PREVIEW"
        const val ACTION_OPEN_TAB = "com.gtasks.gtasks_app.ACTION_OPEN_TAB"
        const val ACTION_OPEN_MANDALA = "com.gtasks.gtasks_app.ACTION_OPEN_MANDALA"
    }

    private var pendingAction: String? = null
    private var methodChannel: MethodChannel? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        handleIntent(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIntent(intent)
    }

    private fun handleIntent(intent: Intent?) {
        if (intent == null) return
        if (intent.action == ACTION_NEW_TASK || intent.getBooleanExtra("open_task_editor", false)) {
            pendingAction = "open_task_editor"
            methodChannel?.invokeMethod("onActionReceived", "open_task_editor")
        } else if (intent.action == ACTION_OPEN_AI || intent.getBooleanExtra("open_ai_chat", false)) {
            val filterType = intent.getStringExtra("widget_filter_type")
            val filterVal = intent.getStringExtra("widget_filter_val")
            val action = if (!filterType.isNullOrBlank() && !filterVal.isNullOrBlank()) {
                "open_ai_chat:$filterType:$filterVal"
            } else {
                "open_ai_chat"
            }
            pendingAction = action
            methodChannel?.invokeMethod("onActionReceived", action)
        } else if (intent.action == ACTION_OPEN_TASK_PREVIEW || intent.hasExtra("open_task_id")) {
            val taskId = intent.getStringExtra("open_task_id") ?: ""
            val action = "open_task_preview:$taskId"
            pendingAction = action
            methodChannel?.invokeMethod("onActionReceived", action)
        } else if (intent.action == ACTION_OPEN_TAB || intent.hasExtra("open_tab_id")) {
            val tabId = intent.getStringExtra("open_tab_id") ?: ""
            val filterType = intent.getStringExtra("tab_filter_type") ?: ""
            val filterVal = intent.getStringExtra("tab_filter_val") ?: ""
            val action = "open_tab:$tabId:$filterType:$filterVal"
            pendingAction = action
            methodChannel?.invokeMethod("onActionReceived", action)
        } else if (intent.action == ACTION_OPEN_MANDALA || intent.getBooleanExtra("open_mandala", false)) {
            val mode = intent.getStringExtra("mandala_mode") ?: "spaces"
            val geom = intent.getStringExtra("mandala_geometry") ?: "PADMA"
            val focusedItem = intent.getStringExtra("focused_item") ?: ""
            val mandalaId = intent.getStringExtra("mandala_id") ?: ""
            val action = "open_mandala:$mode:$geom:$focusedItem:$mandalaId"
            pendingAction = action
            methodChannel?.invokeMethod("onActionReceived", action)
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        val channel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
        methodChannel = channel

        channel.setMethodCallHandler { call, result ->
            when (call.method) {
                "updateWidget" -> {
                    val tabsJson = call.argument<String>("tabsJson")
                    if (!tabsJson.isNullOrEmpty()) {
                        val prefs = applicationContext.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                        prefs.edit().putString("tabs_json", tabsJson).apply()
                    }
                    GTasksWidgetProvider.updateAllWidgets(applicationContext)
                    MandalaWidgetProvider.updateAllMandalaWidgets(applicationContext)
                    result.success(true)
                }
                "updateMandalaWidget" -> {
                    MandalaWidgetProvider.updateAllMandalaWidgets(applicationContext)
                    result.success(true)
                }
                "getInitialAction" -> {
                    val action = pendingAction
                    pendingAction = null
                    result.success(action)
                }
                else -> result.notImplemented()
            }
        }

        if (pendingAction != null) {
            channel.invokeMethod("onActionReceived", pendingAction)
            pendingAction = null
        }
    }
}
