package com.gtasks.gtasks_app

import android.content.Intent
import android.os.Bundle
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    companion object {
        const val CHANNEL = "com.gtasks.gtasks_app/widget"
        const val ACTION_NEW_TASK = "com.gtasks.gtasks_app.ACTION_NEW_TASK"
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
        }
    }

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)
        val channel = MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
        methodChannel = channel

        channel.setMethodCallHandler { call, result ->
            when (call.method) {
                "updateWidget" -> {
                    GTasksWidgetProvider.updateAllWidgets(applicationContext)
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
