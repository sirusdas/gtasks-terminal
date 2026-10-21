package com.gtasks.gtasks_app

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.database.sqlite.SQLiteDatabase
import android.graphics.Color
import android.util.Log
import android.widget.RemoteViews
import org.json.JSONArray
import org.json.JSONObject

class MandalaWidgetProvider : AppWidgetProvider() {

    companion object {
        private const val TAG = "MandalaWidgetProvider"
        const val PREFS_NAME = "gtasks_mandala_widget_prefs"

        const val ACTION_CYCLE_MODE = "com.gtasks.gtasks_app.mandala.ACTION_CYCLE_MODE"
        const val ACTION_CYCLE_GEOMETRY = "com.gtasks.gtasks_app.mandala.ACTION_CYCLE_GEOMETRY"
        const val ACTION_CYCLE_THEME = "com.gtasks.gtasks_app.mandala.ACTION_CYCLE_THEME"
        const val ACTION_PREV_PILLAR = "com.gtasks.gtasks_app.mandala.ACTION_PREV_PILLAR"
        const val ACTION_NEXT_PILLAR = "com.gtasks.gtasks_app.mandala.ACTION_NEXT_PILLAR"
        const val ACTION_REFRESH_MANDALA = "com.gtasks.gtasks_app.mandala.ACTION_REFRESH_MANDALA"
        const val ACTION_DRILL_DOWN = "com.gtasks.gtasks_app.mandala.ACTION_DRILL_DOWN"
        const val ACTION_DRILL_UP = "com.gtasks.gtasks_app.mandala.ACTION_DRILL_UP"
        const val ACTION_CANVAS_CLICK = "com.gtasks.gtasks_app.mandala.ACTION_CANVAS_CLICK"
        const val ACTION_OPEN_MANDALA = "com.gtasks.gtasks_app.ACTION_OPEN_MANDALA"

        val MODES = listOf("spaces", "harada_9x9", "priorities", "lists", "tags", "custom")
        val GEOMETRIES = listOf(
            MandalaWidgetRenderer.GeometryType.PADMA,
            MandalaWidgetRenderer.GeometryType.CHAKRA,
            MandalaWidgetRenderer.GeometryType.BHUPURA,
            MandalaWidgetRenderer.GeometryType.SRIYANTRA
        )
        val THEMES = listOf(
            MandalaWidgetRenderer.ThemeType.GOLD,
            MandalaWidgetRenderer.ThemeType.CYBERPUNK,
            MandalaWidgetRenderer.ThemeType.EMERALD,
            MandalaWidgetRenderer.ThemeType.SAPPHIRE,
            MandalaWidgetRenderer.ThemeType.OBSIDIAN
        )

        fun updateAllMandalaWidgets(context: Context) {
            try {
                val appWidgetManager = AppWidgetManager.getInstance(context) ?: return
                val thisWidget = ComponentName(context, MandalaWidgetProvider::class.java)
                val appWidgetIds = appWidgetManager.getAppWidgetIds(thisWidget) ?: intArrayOf()
                if (appWidgetIds.isNotEmpty()) {
                    for (appWidgetId in appWidgetIds) {
                        val provider = MandalaWidgetProvider()
                        provider.updateAppWidget(context, appWidgetManager, appWidgetId)
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error in updateAllMandalaWidgets", e)
            }
        }
    }

    override fun onUpdate(context: Context, appWidgetManager: AppWidgetManager, appWidgetIds: IntArray) {
        for (appWidgetId in appWidgetIds) {
            try {
                updateAppWidget(context, appWidgetManager, appWidgetId)
            } catch (e: Exception) {
                Log.e(TAG, "Error updating mandala widget $appWidgetId", e)
            }
        }
        super.onUpdate(context, appWidgetManager, appWidgetIds)
    }

    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        val appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        when (intent.action) {
            ACTION_CYCLE_MODE -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val currentMode = prefs.getString("mode_$appWidgetId", "spaces") ?: "spaces"
                    val nextIdx = (MODES.indexOf(currentMode) + 1) % MODES.size
                    prefs.edit()
                        .putString("mode_$appWidgetId", MODES[nextIdx])
                        .remove("drill_parent_$appWidgetId") // reset drill state when switching modes
                        .putInt("focus_$appWidgetId", -1) // reset focused slice
                        .apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_DRILL_DOWN -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val modeStr = prefs.getString("mode_$appWidgetId", "spaces") ?: "spaces"
                    val focusIndex = prefs.getInt("focus_$appWidgetId", -1)
                    val data = loadMandalaData(context, modeStr)
                    if (focusIndex in data.slices.indices) {
                        val target = data.slices[focusIndex]
                        prefs.edit()
                            .putString("drill_parent_$appWidgetId", target.label)
                            .putInt("focus_$appWidgetId", -1)
                            .apply()
                        updateWidgetById(context, appWidgetId)
                    }
                }
            }
            ACTION_DRILL_UP -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    prefs.edit()
                        .remove("drill_parent_$appWidgetId")
                        .putInt("focus_$appWidgetId", -1)
                        .apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_CANVAS_CLICK -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val drillParent = prefs.getString("drill_parent_$appWidgetId", null)
                    if (!drillParent.isNullOrEmpty()) {
                        // Already inside sub-mandala -> canvas tap zooms back out!
                        prefs.edit()
                            .remove("drill_parent_$appWidgetId")
                            .putInt("focus_$appWidgetId", -1)
                            .apply()
                        updateWidgetById(context, appWidgetId)
                    } else {
                        val focusIndex = prefs.getInt("focus_$appWidgetId", -1)
                        val modeStr = prefs.getString("mode_$appWidgetId", "spaces") ?: "spaces"
                        val data = loadMandalaData(context, modeStr)
                        if (focusIndex in data.slices.indices) {
                            // A slice is focused -> dive down into that sub-mandala!
                            val target = data.slices[focusIndex]
                            prefs.edit()
                                .putString("drill_parent_$appWidgetId", target.label)
                                .putInt("focus_$appWidgetId", -1)
                                .apply()
                            updateWidgetById(context, appWidgetId)
                        } else if (data.slices.isNotEmpty()) {
                            // Nothing focused yet -> select/focus the first sector!
                            prefs.edit()
                                .putInt("focus_$appWidgetId", 0)
                                .apply()
                            updateWidgetById(context, appWidgetId)
                        }
                    }
                }
            }
            ACTION_CYCLE_GEOMETRY -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val currentGeom = prefs.getString("geom_$appWidgetId", GEOMETRIES[0].name)
                    val geomNames = GEOMETRIES.map { it.name }
                    val nextIdx = (geomNames.indexOf(currentGeom) + 1) % geomNames.size
                    prefs.edit().putString("geom_$appWidgetId", geomNames[nextIdx]).apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_CYCLE_THEME -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val currentTheme = prefs.getString("theme_$appWidgetId", THEMES[0].name)
                    val themeNames = THEMES.map { it.name }
                    val nextIdx = (themeNames.indexOf(currentTheme) + 1) % themeNames.size
                    prefs.edit().putString("theme_$appWidgetId", themeNames[nextIdx]).apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_PREV_PILLAR -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val count = prefs.getInt("slice_count_$appWidgetId", 4)
                    val curFocus = prefs.getInt("focus_$appWidgetId", -1)
                    val nextFocus = if (curFocus <= -1) count - 1 else curFocus - 1
                    prefs.edit().putInt("focus_$appWidgetId", nextFocus).apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_NEXT_PILLAR -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val count = prefs.getInt("slice_count_$appWidgetId", 4)
                    val curFocus = prefs.getInt("focus_$appWidgetId", -1)
                    val nextFocus = if (curFocus >= count - 1) -1 else curFocus + 1
                    prefs.edit().putInt("focus_$appWidgetId", nextFocus).apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_REFRESH_MANDALA, AppWidgetManager.ACTION_APPWIDGET_UPDATE -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    updateWidgetById(context, appWidgetId)
                } else {
                    updateAllMandalaWidgets(context)
                }
            }
        }
    }

    private fun updateWidgetById(context: Context, appWidgetId: Int) {
        val appWidgetManager = AppWidgetManager.getInstance(context) ?: return
        updateAppWidget(context, appWidgetManager, appWidgetId)
    }

    fun updateAppWidget(context: Context, appWidgetManager: AppWidgetManager, appWidgetId: Int) {
        val views = RemoteViews(context.packageName, R.layout.gtasks_mandala_widget_layout)
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)

        val modeStr = prefs.getString("mode_$appWidgetId", "spaces") ?: "spaces"
        val geomStr = prefs.getString("geom_$appWidgetId", GEOMETRIES[0].name)
        val themeStr = prefs.getString("theme_$appWidgetId", THEMES[0].name)
        var focusIndex = prefs.getInt("focus_$appWidgetId", -1)

        val geometry = try {
            MandalaWidgetRenderer.GeometryType.valueOf(geomStr ?: GEOMETRIES[0].name)
        } catch (e: Exception) {
            GEOMETRIES[0]
        }

        val theme = try {
            MandalaWidgetRenderer.ThemeType.valueOf(themeStr ?: THEMES[0].name)
        } catch (e: Exception) {
            THEMES[0]
        }

        // Check if widget is drilled down into a sub-mandala
        val drillParent = prefs.getString("drill_parent_$appWidgetId", null)

        // Fetch data
        val data = if (!drillParent.isNullOrEmpty()) {
            loadDrilledData(context, modeStr, drillParent)
        } else {
            loadMandalaData(context, modeStr)
        }

        // Validate focusIndex
        if (data.slices.isNotEmpty()) {
            if (focusIndex >= data.slices.size) {
                focusIndex = -1
            }
            prefs.edit().putInt("slice_count_$appWidgetId", data.slices.size).apply()
        }

        // Render Canvas Bitmap (540x540 for sharp rendering)
        val bitmap = MandalaWidgetRenderer.render(
            width = 540,
            height = 540,
            data = data,
            geometry = geometry,
            theme = theme,
            focusedIndex = focusIndex
        )
        views.setImageViewBitmap(R.id.mandala_canvas_image, bitmap)

        // Update Mode text
        val modeDisplay = if (!drillParent.isNullOrEmpty()) {
            "⬅️ $drillParent"
        } else {
            when (modeStr) {
                "spaces" -> "☸ Spaces"
                "harada_9x9" -> "🎯 9×9 Harada"
                "priorities" -> "⚡ Priorities"
                "lists" -> "📋 Lists"
                "tags" -> "🏷️ Tags"
                "custom" -> "✨ Custom"
                else -> "Mandala"
            }
        }
        views.setTextViewText(R.id.mandala_mode_text, modeDisplay)

        // Update Pillar info text & pending intents
        val focusedSlice = if (focusIndex in data.slices.indices) data.slices[focusIndex] else null
        val pillarText: String
        val pillPendingIntent: PendingIntent

        if (!drillParent.isNullOrEmpty()) {
            pillarText = if (focusedSlice != null) {
                "⬅️ ${focusedSlice.label} • Tap to Zoom Out"
            } else {
                "⬅️ $drillParent • Tap to Return Up"
            }
            pillPendingIntent = createBroadcastPendingIntent(context, ACTION_DRILL_UP, appWidgetId, 9)
            views.setOnClickPendingIntent(
                R.id.mandala_btn_mode,
                createBroadcastPendingIntent(context, ACTION_DRILL_UP, appWidgetId, 10)
            )
        } else if (focusedSlice != null) {
            val subCount = if (focusedSlice.subLabels.isNotEmpty()) " [${focusedSlice.subLabels.size} sub]" else ""
            pillarText = "⤵ Drill: ${focusedSlice.label} (${focusedSlice.count})$subCount • Tap to Enter"
            pillPendingIntent = createBroadcastPendingIntent(context, ACTION_DRILL_DOWN, appWidgetId, 11)
            views.setOnClickPendingIntent(
                R.id.mandala_btn_mode,
                createBroadcastPendingIntent(context, ACTION_CYCLE_MODE, appWidgetId, 1)
            )
        } else {
            pillarText = "Total: ${data.totalCount} tasks • Tap Canvas or ◀ / ▶ to Focus"
            pillPendingIntent = createBroadcastPendingIntent(context, ACTION_CANVAS_CLICK, appWidgetId, 12)
            views.setOnClickPendingIntent(
                R.id.mandala_btn_mode,
                createBroadcastPendingIntent(context, ACTION_CYCLE_MODE, appWidgetId, 1)
            )
        }
        views.setTextViewText(R.id.mandala_pillar_text, pillarText)
        views.setOnClickPendingIntent(R.id.mandala_pillar_pill, pillPendingIntent)

        // Setup PendingIntents
        // 2. Cycle Geometry
        views.setOnClickPendingIntent(
            R.id.mandala_btn_geom,
            createBroadcastPendingIntent(context, ACTION_CYCLE_GEOMETRY, appWidgetId, 2)
        )

        // 3. Cycle Theme
        views.setOnClickPendingIntent(
            R.id.mandala_btn_theme,
            createBroadcastPendingIntent(context, ACTION_CYCLE_THEME, appWidgetId, 3)
        )

        // 4. Prev Pillar
        views.setOnClickPendingIntent(
            R.id.mandala_btn_prev,
            createBroadcastPendingIntent(context, ACTION_PREV_PILLAR, appWidgetId, 4)
        )

        // 5. Next Pillar
        views.setOnClickPendingIntent(
            R.id.mandala_btn_next,
            createBroadcastPendingIntent(context, ACTION_NEXT_PILLAR, appWidgetId, 5)
        )

        // 6. Refresh
        views.setOnClickPendingIntent(
            R.id.mandala_btn_refresh,
            createBroadcastPendingIntent(context, ACTION_REFRESH_MANDALA, appWidgetId, 6)
        )

        // 7. Quick Add Task
        val addTaskIntent = Intent(context, MainActivity::class.java).apply {
            action = "com.gtasks.gtasks_app.ACTION_NEW_TASK"
            putExtra("open_task_editor", true)
            putExtra("is_from_widget", true)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        views.setOnClickPendingIntent(
            R.id.mandala_btn_add,
            PendingIntent.getActivity(
                context,
                appWidgetId * 100 + 7,
                addTaskIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
        )

        // 8. Open In App (Mandala Screen)
        val openMandalaIntent = Intent(context, MainActivity::class.java).apply {
            action = ACTION_OPEN_MANDALA
            putExtra("open_mandala", true)
            putExtra("mandala_mode", modeStr)
            putExtra("mandala_geometry", geometry.name)
            putExtra("mandala_theme", theme.name)
            val targetFocus = if (!drillParent.isNullOrEmpty()) {
                drillParent
            } else if (focusedSlice != null) {
                focusedSlice.label
            } else {
                null
            }
            if (targetFocus != null) {
                putExtra("focused_item", targetFocus)
            }
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 100 + 8,
            openMandalaIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.mandala_btn_open, openPendingIntent)

        // Canvas Click: interactive drilling / focusing directly on widget!
        val canvasPendingIntent = createBroadcastPendingIntent(context, ACTION_CANVAS_CLICK, appWidgetId, 14)
        views.setOnClickPendingIntent(R.id.mandala_canvas_container, canvasPendingIntent)
        views.setOnClickPendingIntent(R.id.mandala_canvas_image, canvasPendingIntent)

        appWidgetManager.updateAppWidget(appWidgetId, views)
    }

    private fun createBroadcastPendingIntent(context: Context, action: String, appWidgetId: Int, requestCodeOffset: Int): PendingIntent {
        val intent = Intent(context, MandalaWidgetProvider::class.java).apply {
            this.action = action
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        return PendingIntent.getBroadcast(
            context,
            appWidgetId * 100 + requestCodeOffset,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
    }

    // --- DATA LOADING LOGIC ---
    private fun loadDrilledData(context: Context, mode: String, parentName: String): MandalaWidgetRenderer.MandalaRenderData {
        val slices = mutableListOf<MandalaWidgetRenderer.MandalaSlice>()
        var total = 0
        var completed = 0

        // Strip leading symbols and trailing counts: e.g. "Work (5)" -> "Work", "🔥 Critical" -> "Critical", "#Urgent" -> "Urgent"
        val cleanParent = parentName
            .replace(Regex("""^[⬅️⤵️⚡🔥📌☕📋🏷️#\s]+"""), "")
            .replace(Regex("""\s*\(\d+\)$"""), "")
            .trim()

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    when (mode) {
                        "priorities" -> {
                            val prioTarget = when {
                                cleanParent.contains("critical", ignoreCase = true) -> "critical"
                                cleanParent.contains("high", ignoreCase = true) -> "high"
                                cleanParent.contains("med", ignoreCase = true) -> "medium"
                                cleanParent.contains("low", ignoreCase = true) -> "low"
                                else -> cleanParent.lowercase()
                            }
                            val pColor = when (prioTarget) {
                                "critical" -> Color.parseColor("#EF4444")
                                "high" -> Color.parseColor("#F59E0B")
                                "medium" -> Color.parseColor("#3B82F6")
                                else -> Color.parseColor("#10B981")
                            }
                            val cursor = db.rawQuery(
                                "SELECT title, status FROM tasks WHERE sync_status != 'pending_delete' AND lower(priority) = ? ORDER BY id DESC LIMIT 16",
                                arrayOf(prioTarget)
                            )
                            cursor.use {
                                while (it.moveToNext()) {
                                    val title = it.getString(0) ?: "Task"
                                    val status = it.getString(1) ?: "pending"
                                    if (status == "completed") {
                                        completed++
                                    } else {
                                        total++
                                        slices.add(
                                            MandalaWidgetRenderer.MandalaSlice(
                                                id = "prio_${slices.size}",
                                                label = title,
                                                count = 1,
                                                completedCount = 0,
                                                color = pColor
                                            )
                                        )
                                    }
                                }
                            }
                        }
                        "lists" -> {
                            val cursor = db.rawQuery(
                                "SELECT title, priority, status FROM tasks WHERE sync_status != 'pending_delete' AND lower(trim(list_title)) = lower(trim(?)) ORDER BY id DESC LIMIT 16",
                                arrayOf(cleanParent)
                            )
                            cursor.use {
                                while (it.moveToNext()) {
                                    val title = it.getString(0) ?: "Task"
                                    val prio = it.getString(1) ?: "medium"
                                    val status = it.getString(2) ?: "pending"
                                    val pColor = when (prio.lowercase()) {
                                        "critical" -> Color.parseColor("#EF4444")
                                        "high" -> Color.parseColor("#F59E0B")
                                        "low" -> Color.parseColor("#10B981")
                                        else -> Color.parseColor("#3B82F6")
                                    }
                                    if (status == "completed") {
                                        completed++
                                    } else {
                                        total++
                                        slices.add(
                                            MandalaWidgetRenderer.MandalaSlice(
                                                id = "list_${slices.size}",
                                                label = title,
                                                count = 1,
                                                completedCount = 0,
                                                color = pColor
                                            )
                                        )
                                    }
                                }
                            }
                        }
                        "tags" -> {
                            val cleanTag = cleanParent.replace("#", "").trim().lowercase()
                            val cursor = db.rawQuery(
                                "SELECT title, tags, priority, status FROM tasks WHERE sync_status != 'pending_delete' ORDER BY id DESC",
                                null
                            )
                            cursor.use {
                                while (it.moveToNext()) {
                                    val title = it.getString(0) ?: "Task"
                                    val tagsJson = it.getString(1) ?: ""
                                    val prio = it.getString(2) ?: "medium"
                                    val status = it.getString(3) ?: "pending"
                                    var hasTag = false
                                    if (tagsJson.isNotBlank() && tagsJson != "[]") {
                                        try {
                                            val arr = JSONArray(tagsJson)
                                            for (k in 0 until arr.length()) {
                                                if (arr.getString(k).trim().equals(cleanTag, ignoreCase = true)) {
                                                    hasTag = true
                                                    break
                                                }
                                            }
                                        } catch (e: Exception) {}
                                    }
                                    if (hasTag) {
                                        if (status == "completed") {
                                            completed++
                                        } else {
                                            total++
                                            if (slices.size < 16) {
                                                val pColor = when (prio.lowercase()) {
                                                    "critical" -> Color.parseColor("#EF4444")
                                                    "high" -> Color.parseColor("#F59E0B")
                                                    "low" -> Color.parseColor("#10B981")
                                                    else -> Color.parseColor("#3B82F6")
                                                }
                                                slices.add(
                                                    MandalaWidgetRenderer.MandalaSlice(
                                                        id = "tag_${slices.size}",
                                                        label = title,
                                                        count = 1,
                                                        completedCount = 0,
                                                        color = pColor
                                                    )
                                                )
                                            }
                                        }
                                    }
                                }
                            }
                        }
                        else -> { // "spaces", "harada_9x9", "custom", etc.
                            val cursor = db.rawQuery(
                                "SELECT title, spaces, status, priority FROM tasks WHERE sync_status != 'pending_delete' ORDER BY id DESC",
                                null
                            )
                            val subSpaceCounts = mutableMapOf<String, Int>()
                            val directTasks = mutableListOf<Pair<String, String>>()

                            cursor.use {
                                while (it.moveToNext()) {
                                    val taskTitle = it.getString(0) ?: "Task"
                                    val spacesJson = it.getString(1) ?: ""
                                    val status = it.getString(2) ?: "pending"
                                    val priority = it.getString(3) ?: "medium"
                                    val isDone = (status == "completed")

                                    var matchesParent = false
                                    var subNameFound: String? = null

                                    if (spacesJson.isNotBlank() && spacesJson != "{}") {
                                        try {
                                            val obj = JSONObject(spacesJson)
                                            val keys = obj.keys()
                                            while (keys.hasNext()) {
                                                val k = keys.next()
                                                if (k.trim().equals(cleanParent, ignoreCase = true)) {
                                                    matchesParent = true
                                                    val subs = obj.optJSONArray(k)
                                                    if (subs != null && subs.length() > 0) {
                                                        subNameFound = subs.getString(0).trim()
                                                    }
                                                    break
                                                }
                                            }
                                        } catch (e: Exception) {}
                                    }

                                    if (matchesParent) {
                                        if (isDone) completed++ else total++
                                        if (!isDone) {
                                            if (subNameFound != null && subNameFound.isNotEmpty()) {
                                                subSpaceCounts[subNameFound] = (subSpaceCounts[subNameFound] ?: 0) + 1
                                            } else {
                                                directTasks.add(Pair(taskTitle, priority))
                                            }
                                        }
                                    }
                                }
                            }

                            // Add sub-spaces
                            subSpaceCounts.entries.forEachIndexed { idx, e ->
                                slices.add(
                                    MandalaWidgetRenderer.MandalaSlice(
                                        id = "sub_$idx",
                                        label = e.key,
                                        count = e.value,
                                        completedCount = 0,
                                        color = 0
                                    )
                                )
                            }
                            // Add direct tasks (up to 16 total)
                            val remainingCapacity = max(0, 16 - slices.size)
                            directTasks.take(remainingCapacity).forEachIndexed { idx, pair ->
                                val pColor = when (pair.second.lowercase()) {
                                    "critical" -> Color.parseColor("#EF4444")
                                    "high" -> Color.parseColor("#F59E0B")
                                    "low" -> Color.parseColor("#10B981")
                                    else -> Color.parseColor("#3B82F6")
                                }
                                slices.add(
                                    MandalaWidgetRenderer.MandalaSlice(
                                        id = "task_${slices.size}",
                                        label = pair.first,
                                        count = 1,
                                        completedCount = 0,
                                        color = pColor
                                    )
                                )
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading drilled data for $parentName", e)
        }

        // Harada 9x9 fallback
        if (slices.isEmpty() && (mode == "harada_9x9" || mode == "custom")) {
            try {
                val prefs = context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
                val jsonStr = prefs.getString("flutter.gtasks_custom_mandalas", null)
                if (!jsonStr.isNullOrEmpty()) {
                    val arr = JSONArray(jsonStr)
                    for (i in 0 until arr.length()) {
                        val m = arr.getJSONObject(i)
                        val nodes = m.optJSONArray("nodes")
                        if (nodes != null) {
                            var parentId: String? = null
                            for (n in 0 until nodes.length()) {
                                val node = nodes.getJSONObject(n)
                                if (node.optString("label", "").equals(cleanParent, ignoreCase = true)) {
                                    parentId = node.optString("id", "")
                                    break
                                }
                            }
                            if (parentId != null) {
                                for (n in 0 until nodes.length()) {
                                    val node = nodes.getJSONObject(n)
                                    if (node.optString("parent", "") == parentId) {
                                        slices.add(
                                            MandalaWidgetRenderer.MandalaSlice(
                                                id = node.optString("id", "h_$n"),
                                                label = node.optString("label", "Action"),
                                                count = 1,
                                                completedCount = 0,
                                                color = 0
                                            )
                                        )
                                    }
                                }
                                if (slices.isNotEmpty()) {
                                    total = slices.size
                                    break
                                }
                            }
                        }
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error loading drilled Harada data", e)
            }

            // Default classic 8 Harada action milestones if user has not yet customized this pillar
            if (slices.isEmpty()) {
                val defaultMilestones = when {
                    cleanParent.contains("Mental", ignoreCase = true) || cleanParent.contains("Mind", ignoreCase = true) ->
                        listOf("Positive Self-Talk", "Meditation 10m", "Vision Journal", "Focus Ritual", "Stress Control", "Evening Reflection", "Gratitude 3x", "Unshakable Will")
                    cleanParent.contains("Health", ignoreCase = true) || cleanParent.contains("Physical", ignoreCase = true) ->
                        listOf("8h Sleep", "Hydration 2.5L", "Nutrition Balance", "Cardio 20m", "Strength Training", "Stretching Routine", "Posture Check", "Vitality Rest")
                    cleanParent.contains("Competence", ignoreCase = true) || cleanParent.contains("Skill", ignoreCase = true) ->
                        listOf("Deep Work 90m", "Skill Practice", "Tool Mastery", "Code Review", "Architecture Study", "Fast Execution", "Quality Standard", "Knowledge Map")
                    cleanParent.contains("Speed", ignoreCase = true) || cleanParent.contains("Execution", ignoreCase = true) ->
                        listOf("Daily Top 3", "Timeboxing", "Zero Distractions", "Immediate Action", "Task Batching", "Progress Tracking", "Quick Decisions", "Sprint Review")
                    cleanParent.contains("Finance", ignoreCase = true) || cleanParent.contains("Wealth", ignoreCase = true) ->
                        listOf("Expense Tracking", "Budget Discipline", "Income Stream", "Investment Review", "Savings Target", "Asset Building", "Emergency Fund", "Financial Study")
                    cleanParent.contains("Relations", ignoreCase = true) || cleanParent.contains("Network", ignoreCase = true) ->
                        listOf("Active Listening", "Family Quality Time", "Express Gratitude", "Mentor Check-in", "Peer Collab", "Empathetic Help", "Network Nurturing", "Authentic Bond")
                    cleanParent.contains("Learning", ignoreCase = true) || cleanParent.contains("Study", ignoreCase = true) ->
                        listOf("Read 20 Pages", "Take Smart Notes", "Synthesize Ideas", "Teach Someone", "Listen to Podcast", "Course Progress", "Vocabulary Growth", "Apply Learning")
                    cleanParent.contains("Discipline", ignoreCase = true) || cleanParent.contains("Habit", ignoreCase = true) ->
                        listOf("Early Awakening", "Clean Workspace", "Checklist Zero", "No Procrastination", "Consistent Habit", "Evening Review", "Prep for Tomorrow", "Self Reflection")
                    else -> emptyList()
                }
                if (defaultMilestones.isNotEmpty()) {
                    defaultMilestones.forEachIndexed { idx, actionName ->
                        slices.add(
                            MandalaWidgetRenderer.MandalaSlice(
                                id = "harada_act_$idx",
                                label = actionName,
                                count = 1,
                                completedCount = 0,
                                color = 0
                            )
                        )
                    }
                    total = slices.size
                }
            }
        }

        // NOTE: If slices is empty, leave it empty! The renderer gracefully displays the Cosmic Empty State without repeated dummy nodes.

        return MandalaWidgetRenderer.MandalaRenderData(
            title = "$cleanParent Sub-Mandala",
            centerGoal = cleanParent,
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadMandalaData(context: Context, mode: String): MandalaWidgetRenderer.MandalaRenderData {
        return when (mode) {
            "harada_9x9" -> loadHaradaData(context)
            "priorities" -> loadPrioritiesData(context)
            "lists" -> loadListsData(context)
            "tags" -> loadTagsData(context)
            "custom" -> loadCustomMandalaData(context)
            else -> loadSpacesData(context)
        }
    }

    private fun loadSpacesData(context: Context): MandalaWidgetRenderer.MandalaRenderData {
        val spaceMap = mutableMapOf<String, MutableList<String>>() // Space -> Subspaces
        val spaceCounts = mutableMapOf<String, Int>()
        var total = 0
        var completed = 0

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val cursor = db.rawQuery(
                        "SELECT spaces, status FROM tasks WHERE sync_status != 'pending_delete'",
                        null
                    )
                    cursor.use {
                        while (it.moveToNext()) {
                            val spacesJson = it.getString(0) ?: ""
                            val status = it.getString(1) ?: "pending"
                            val isDone = (status == "completed")
                            if (isDone) completed++ else total++

                            if (spacesJson.isNotBlank() && spacesJson != "{}" && !isDone) {
                                try {
                                    val obj = JSONObject(spacesJson)
                                    val keys = obj.keys()
                                    while (keys.hasNext()) {
                                        val space = keys.next().trim()
                                        if (space.isNotEmpty()) {
                                            spaceCounts[space] = (spaceCounts[space] ?: 0) + 1
                                            val subList = spaceMap.getOrPut(space) { mutableListOf() }
                                            val subs = obj.optJSONArray(space)
                                            if (subs != null) {
                                                for (s in 0 until subs.length()) {
                                                    val subName = subs.getString(s).trim()
                                                    if (subName.isNotEmpty() && !subList.contains(subName)) {
                                                        subList.add(subName)
                                                    }
                                                }
                                            }
                                        }
                                    }
                                } catch (e: Exception) {}
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading spaces data", e)
        }

        // If no spaces found yet, provide starter spaces
        val slices = mutableListOf<MandalaWidgetRenderer.MandalaSlice>()
        if (spaceCounts.isEmpty()) {
            val defaultSpaces = listOf("Work", "Personal", "Health", "Projects", "Finance")
            defaultSpaces.forEachIndexed { idx, name ->
                slices.add(
                    MandalaWidgetRenderer.MandalaSlice(
                        id = "space_$idx",
                        label = name,
                        count = 0,
                        completedCount = 0,
                        color = 0,
                        subLabels = emptyList()
                    )
                )
            }
        } else {
            spaceCounts.entries.forEachIndexed { idx, entry ->
                slices.add(
                    MandalaWidgetRenderer.MandalaSlice(
                        id = "space_$idx",
                        label = entry.key,
                        count = entry.value,
                        completedCount = 0,
                        color = 0,
                        subLabels = spaceMap[entry.key] ?: emptyList()
                    )
                )
            }
        }

        return MandalaWidgetRenderer.MandalaRenderData(
            title = "Spaces & Subspaces",
            centerGoal = "Focus",
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadHaradaData(context: Context): MandalaWidgetRenderer.MandalaRenderData {
        // Standard 8 Harada 9x9 Mandalachart Pillars surrounding Core Goal
        val defaultPillars = listOf(
            "Mental & Mindset",
            "Physical Health",
            "Core Competence",
            "Execution Speed",
            "Finance & Wealth",
            "Relations & Network",
            "Learning & Study",
            "Daily Discipline"
        )

        // Try reading user's custom Harada 9x9 from SharedPreferences
        var centerGoal = "Core Mastery"
        val customPillars = mutableListOf<String>()

        try {
            val prefs = context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            val jsonStr = prefs.getString("flutter.gtasks_custom_mandalas", null)
            if (!jsonStr.isNullOrEmpty()) {
                val arr = JSONArray(jsonStr)
                for (i in 0 until arr.length()) {
                    val m = arr.getJSONObject(i)
                    val tpl = m.optString("template", "")
                    if (tpl == "harada_9x9" || m.optString("id", "").contains("harada")) {
                        centerGoal = m.optString("centerGoal", centerGoal)
                        val nodes = m.optJSONArray("nodes")
                        if (nodes != null) {
                            for (n in 0 until nodes.length()) {
                                val node = nodes.getJSONObject(n)
                                val parent = node.optString("parent", "")
                                if (parent == "center_goal" || parent.contains("root") || parent.contains("center")) {
                                    val label = node.optString("label", "")
                                    if (label.isNotBlank()) customPillars.add(label)
                                }
                            }
                        }
                        break
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error reading custom Harada mandala", e)
        }

        val pillars = if (customPillars.size >= 4) customPillars else defaultPillars
        val slices = pillars.mapIndexed { idx, pillar ->
            MandalaWidgetRenderer.MandalaSlice(
                id = "harada_$idx",
                label = pillar,
                count = idx + 1, // Progress / priority indicator
                completedCount = 0,
                color = 0,
                subLabels = emptyList()
            )
        }

        return MandalaWidgetRenderer.MandalaRenderData(
            title = "Harada 9×9 Matrix",
            centerGoal = centerGoal,
            totalCount = slices.size,
            completedCount = 0,
            slices = slices
        )
    }

    private fun loadPrioritiesData(context: Context): MandalaWidgetRenderer.MandalaRenderData {
        var pCritical = 0
        var pHigh = 0
        var pMed = 0
        var pLow = 0
        var total = 0
        var completed = 0

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val cursor = db.rawQuery(
                        "SELECT priority, status FROM tasks WHERE sync_status != 'pending_delete'",
                        null
                    )
                    cursor.use {
                        while (it.moveToNext()) {
                            val prio = it.getString(0)?.lowercase() ?: "medium"
                            val status = it.getString(1) ?: "pending"
                            if (status == "completed") {
                                completed++
                            } else {
                                total++
                                when (prio) {
                                    "critical" -> pCritical++
                                    "high" -> pHigh++
                                    "medium" -> pMed++
                                    "low" -> pLow++
                                    else -> pMed++
                                }
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading priorities data", e)
        }

        val slices = listOf(
            MandalaWidgetRenderer.MandalaSlice("p_crit", "🔥 Critical", pCritical, 0, Color.parseColor("#EF4444")),
            MandalaWidgetRenderer.MandalaSlice("p_high", "⚡ High", pHigh, 0, Color.parseColor("#F59E0B")),
            MandalaWidgetRenderer.MandalaSlice("p_med", "📌 Medium", pMed, 0, Color.parseColor("#3B82F6")),
            MandalaWidgetRenderer.MandalaSlice("p_low", "☕ Low", pLow, 0, Color.parseColor("#10B981"))
        )

        return MandalaWidgetRenderer.MandalaRenderData(
            title = "Priority Urgency Rings",
            centerGoal = "Focus",
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadListsData(context: Context): MandalaWidgetRenderer.MandalaRenderData {
        val listCounts = mutableMapOf<String, Int>()
        var total = 0
        var completed = 0

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val cursor = db.rawQuery(
                        "SELECT list_title, status, count(*) FROM tasks WHERE sync_status != 'pending_delete' GROUP BY list_title, status",
                        null
                    )
                    cursor.use {
                        while (it.moveToNext()) {
                            val title = it.getString(0) ?: "Tasks"
                            val status = it.getString(1) ?: "pending"
                            val count = it.getInt(2)
                            if (status == "completed") {
                                completed += count
                            } else {
                                total += count
                                listCounts[title] = (listCounts[title] ?: 0) + count
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading lists data", e)
        }

        val slices = mutableListOf<MandalaWidgetRenderer.MandalaSlice>()
        if (listCounts.isEmpty()) {
            slices.add(MandalaWidgetRenderer.MandalaSlice("l_0", "My Tasks", 0, 0, 0))
            slices.add(MandalaWidgetRenderer.MandalaSlice("l_1", "Work", 0, 0, 0))
            slices.add(MandalaWidgetRenderer.MandalaSlice("l_2", "Personal", 0, 0, 0))
            slices.add(MandalaWidgetRenderer.MandalaSlice("l_3", "Projects", 0, 0, 0))
        } else {
            listCounts.entries.forEachIndexed { idx, entry ->
                slices.add(
                    MandalaWidgetRenderer.MandalaSlice(
                        id = "l_$idx",
                        label = entry.key,
                        count = entry.value,
                        completedCount = 0,
                        color = 0
                    )
                )
            }
        }

        return MandalaWidgetRenderer.MandalaRenderData(
            title = "Task Lists",
            centerGoal = "Lists",
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadTagsData(context: Context): MandalaWidgetRenderer.MandalaRenderData {
        val tagCounts = mutableMapOf<String, Int>()
        var total = 0
        var completed = 0

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val cursor = db.rawQuery(
                        "SELECT tags, status FROM tasks WHERE sync_status != 'pending_delete'",
                        null
                    )
                    cursor.use {
                        while (it.moveToNext()) {
                            val tagsJson = it.getString(0) ?: ""
                            val status = it.getString(1) ?: "pending"
                            if (status == "completed") {
                                completed++
                            } else {
                                total++
                                if (tagsJson.isNotBlank() && tagsJson != "[]") {
                                    try {
                                        val arr = JSONArray(tagsJson)
                                        for (i in 0 until arr.length()) {
                                            val t = arr.getString(i).trim()
                                            if (t.isNotEmpty()) {
                                                tagCounts[t] = (tagCounts[t] ?: 0) + 1
                                            }
                                        }
                                    } catch (e: Exception) {}
                                }
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading tags data", e)
        }

        val slices = mutableListOf<MandalaWidgetRenderer.MandalaSlice>()
        if (tagCounts.isEmpty()) {
            listOf("Urgent", "Followup", "Ideas", "Review").forEachIndexed { idx, tag ->
                slices.add(MandalaWidgetRenderer.MandalaSlice("t_$idx", "#$tag", 0, 0, 0))
            }
        } else {
            tagCounts.entries.sortedByDescending { it.value }.take(8).forEachIndexed { idx, entry ->
                slices.add(
                    MandalaWidgetRenderer.MandalaSlice(
                        id = "t_$idx",
                        label = "#${entry.key}",
                        count = entry.value,
                        completedCount = 0,
                        color = 0
                    )
                )
            }
        }

        return MandalaWidgetRenderer.MandalaRenderData(
            title = "Top Tags",
            centerGoal = "Tags",
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadCustomMandalaData(context: Context): MandalaWidgetRenderer.MandalaRenderData {
        var title = "Custom Mandala"
        var centerGoal = "Core Goal"
        val slices = mutableListOf<MandalaWidgetRenderer.MandalaSlice>()

        try {
            val prefs = context.getSharedPreferences("FlutterSharedPreferences", Context.MODE_PRIVATE)
            val jsonStr = prefs.getString("flutter.gtasks_custom_mandalas", null)
            if (!jsonStr.isNullOrEmpty()) {
                val arr = JSONArray(jsonStr)
                if (arr.length() > 0) {
                    val m = arr.getJSONObject(0) // Active or first custom mandala
                    title = m.optString("title", title)
                    centerGoal = m.optString("centerGoal", centerGoal)
                    val nodes = m.optJSONArray("nodes")
                    if (nodes != null) {
                        for (i in 0 until nodes.length()) {
                            val node = nodes.getJSONObject(i)
                            val parent = node.optString("parent", "")
                            // First-level child nodes around center
                            if (parent.isNotEmpty()) {
                                slices.add(
                                    MandalaWidgetRenderer.MandalaSlice(
                                        id = node.optString("id", "c_$i"),
                                        label = node.optString("label", "Pillar"),
                                        count = 1,
                                        completedCount = 0,
                                        color = 0
                                    )
                                )
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading custom mandala data", e)
        }

        if (slices.isEmpty()) {
            return loadHaradaData(context)
        }

        return MandalaWidgetRenderer.MandalaRenderData(
            title = title,
            centerGoal = centerGoal,
            totalCount = slices.size,
            completedCount = 0,
            slices = slices
        )
    }
}
