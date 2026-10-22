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
import kotlin.math.max
import kotlin.math.min
import org.json.JSONArray
import org.json.JSONObject
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale

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
        const val ACTION_PREV_TAB = "com.gtasks.gtasks_app.mandala.ACTION_PREV_TAB"
        const val ACTION_NEXT_TAB = "com.gtasks.gtasks_app.mandala.ACTION_NEXT_TAB"
        const val ACTION_TOGGLE_STATUS = "com.gtasks.gtasks_app.mandala.ACTION_TOGGLE_STATUS"
        const val ACTION_CLEAR_FILTER = "com.gtasks.gtasks_app.mandala.ACTION_CLEAR_FILTER"

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

        fun cleanSegment(str: String): String {
            return str
                .replace(Regex("""^[⬅️⤵️⚡🔥📌☕📋🏷️#🚨📅🌅📆📥✓🎯📦✨☸🌱\s]+"""), "")
                .replace(Regex("""\s*\(\d+\)$"""), "")
                .trim()
        }

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
                        .remove("drill_path_$appWidgetId")
                        .remove("drill_parent_$appWidgetId") // reset drill state when switching modes
                        .putInt("focus_$appWidgetId", -1) // reset focused slice
                        .apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_DRILL_DOWN -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val modeStr = prefs.getString("mode_$appWidgetId", "spaces") ?: "spaces"
                    val drillPath = prefs.getString("drill_path_$appWidgetId", null) ?: prefs.getString("drill_parent_$appWidgetId", null)
                    val focusIndex = prefs.getInt("focus_$appWidgetId", -1)
                    val data = if (!drillPath.isNullOrEmpty()) {
                        loadDrilledData(context, modeStr, drillPath, appWidgetId)
                    } else {
                        loadMandalaData(context, modeStr, appWidgetId)
                    }
                    if (focusIndex in data.slices.indices) {
                        val target = data.slices[focusIndex]
                        val nextPath = if (drillPath.isNullOrEmpty()) target.label else "$drillPath||${target.label}"
                        prefs.edit()
                            .putString("drill_path_$appWidgetId", nextPath)
                            .remove("drill_parent_$appWidgetId")
                            .putInt("focus_$appWidgetId", -1)
                            .apply()
                        updateWidgetById(context, appWidgetId)
                    }
                }
            }
            ACTION_DRILL_UP -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val drillPath = prefs.getString("drill_path_$appWidgetId", null) ?: prefs.getString("drill_parent_$appWidgetId", null)
                    if (!drillPath.isNullOrEmpty()) {
                        val segments = drillPath.split("||").filter { it.isNotBlank() }.toMutableList()
                        if (segments.size > 1) {
                            segments.removeAt(segments.size - 1)
                            prefs.edit()
                                .putString("drill_path_$appWidgetId", segments.joinToString("||"))
                                .remove("drill_parent_$appWidgetId")
                                .putInt("focus_$appWidgetId", -1)
                                .apply()
                        } else {
                            prefs.edit()
                                .remove("drill_path_$appWidgetId")
                                .remove("drill_parent_$appWidgetId")
                                .putInt("focus_$appWidgetId", -1)
                                .apply()
                        }
                        updateWidgetById(context, appWidgetId)
                    }
                }
            }
            ACTION_CANVAS_CLICK -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val drillPath = prefs.getString("drill_path_$appWidgetId", null) ?: prefs.getString("drill_parent_$appWidgetId", null)
                    val modeStr = prefs.getString("mode_$appWidgetId", "spaces") ?: "spaces"
                    val focusIndex = prefs.getInt("focus_$appWidgetId", -1)
                    val data = if (!drillPath.isNullOrEmpty()) {
                        loadDrilledData(context, modeStr, drillPath, appWidgetId)
                    } else {
                        loadMandalaData(context, modeStr, appWidgetId)
                    }

                    if (focusIndex in data.slices.indices) {
                        val target = data.slices[focusIndex]
                        val isPortal = target.count > 1 ||
                                target.label.contains("Batch", ignoreCase = true) ||
                                target.label.contains("Completed", ignoreCase = true) ||
                                target.subLabels.isNotEmpty()
                        if (isPortal) {
                            val nextPath = if (drillPath.isNullOrEmpty()) target.label else "$drillPath||${target.label}"
                            prefs.edit()
                                .putString("drill_path_$appWidgetId", nextPath)
                                .remove("drill_parent_$appWidgetId")
                                .putInt("focus_$appWidgetId", -1)
                                .apply()
                            updateWidgetById(context, appWidgetId)
                        } else {
                            val nextFocus = (focusIndex + 1) % data.slices.size
                            prefs.edit().putInt("focus_$appWidgetId", nextFocus).apply()
                            updateWidgetById(context, appWidgetId)
                        }
                    } else if (data.slices.isNotEmpty()) {
                        prefs.edit().putInt("focus_$appWidgetId", 0).apply()
                        updateWidgetById(context, appWidgetId)
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
            ACTION_PREV_TAB -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val wPrefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                    val tabs = WidgetTabFilter.getAvailableTabs(context)
                    if (tabs.isNotEmpty()) {
                        val currentIndex = wPrefs.getInt("tab_index_$appWidgetId", 0)
                        val newIndex = (currentIndex - 1 + tabs.size) % tabs.size
                        wPrefs.edit()
                            .putInt("tab_index_$appWidgetId", newIndex)
                            .remove("filter_type_$appWidgetId")
                            .remove("filter_val_$appWidgetId")
                            .apply()
                        prefs.edit()
                            .remove("drill_path_$appWidgetId")
                            .remove("drill_parent_$appWidgetId")
                            .putInt("focus_$appWidgetId", -1)
                            .apply()
                        updateWidgetById(context, appWidgetId)
                    }
                }
            }
            ACTION_NEXT_TAB -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val wPrefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                    val tabs = WidgetTabFilter.getAvailableTabs(context)
                    if (tabs.isNotEmpty()) {
                        val currentIndex = wPrefs.getInt("tab_index_$appWidgetId", 0)
                        val newIndex = (currentIndex + 1) % tabs.size
                        wPrefs.edit()
                            .putInt("tab_index_$appWidgetId", newIndex)
                            .remove("filter_type_$appWidgetId")
                            .remove("filter_val_$appWidgetId")
                            .apply()
                        prefs.edit()
                            .remove("drill_path_$appWidgetId")
                            .remove("drill_parent_$appWidgetId")
                            .putInt("focus_$appWidgetId", -1)
                            .apply()
                        updateWidgetById(context, appWidgetId)
                    }
                }
            }
            ACTION_TOGGLE_STATUS -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val wPrefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                    val cur = wPrefs.getString("mandala_status_$appWidgetId", "pending") ?: "pending"
                    val next = when (cur) {
                        "pending" -> "completed"
                        "completed" -> "all"
                        else -> "pending"
                    }
                    wPrefs.edit().putString("mandala_status_$appWidgetId", next).apply()
                    prefs.edit()
                        .remove("drill_path_$appWidgetId")
                        .remove("drill_parent_$appWidgetId")
                        .putInt("focus_$appWidgetId", -1)
                        .apply()
                    updateWidgetById(context, appWidgetId)
                }
            }
            ACTION_CLEAR_FILTER -> {
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    val wPrefs = context.getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
                    wPrefs.edit()
                        .remove("filter_type_$appWidgetId")
                        .remove("filter_val_$appWidgetId")
                        .remove("sort_by_$appWidgetId")
                        .remove("hide_recurring_$appWidgetId")
                        .remove("hidden_lists_$appWidgetId")
                        .remove("hidden_tags_$appWidgetId")
                        .remove("mandala_status_$appWidgetId")
                        .apply()
                    prefs.edit()
                        .remove("drill_path_$appWidgetId")
                        .remove("drill_parent_$appWidgetId")
                        .putInt("focus_$appWidgetId", -1)
                        .apply()
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

        // Fetch tab filter for this widget
        val filter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId, isMandala = true)

        // Bind Tab Bar views
        views.setTextViewText(R.id.mandala_tab_title, filter.title)
        views.setTextViewText(R.id.mandala_tab_badge, "(${filter.tabIndex + 1}/${filter.totalTabs})")

        // Status icon indicator
        when (filter.statusFilter) {
            "completed" -> views.setImageViewResource(R.id.mandala_btn_status, R.drawable.ic_widget_checked)
            "all" -> views.setImageViewResource(R.id.mandala_btn_status, R.drawable.ic_widget_check_circle)
            else -> views.setImageViewResource(R.id.mandala_btn_status, R.drawable.ic_widget_unchecked)
        }

        // Setup Tab navigation intents
        views.setOnClickPendingIntent(
            R.id.mandala_btn_tab_prev,
            createBroadcastPendingIntent(context, ACTION_PREV_TAB, appWidgetId, 21)
        )
        views.setOnClickPendingIntent(
            R.id.mandala_btn_tab_next,
            createBroadcastPendingIntent(context, ACTION_NEXT_TAB, appWidgetId, 22)
        )

        // Center Tab Pill -> Opens In-App scoped to this Tab
        val openTabIntent = Intent(context, MainActivity::class.java).apply {
            action = GTasksWidgetProvider.ACTION_OPEN_TAB
            putExtra("open_tab_id", filter.id)
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val openTabPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 100 + 23,
            openTabIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.mandala_btn_tab_center, openTabPendingIntent)

        // Status Toggle intent
        views.setOnClickPendingIntent(
            R.id.mandala_btn_status,
            createBroadcastPendingIntent(context, ACTION_TOGGLE_STATUS, appWidgetId, 24)
        )

        // Master Filter button intent -> Opens WidgetFilterActivity to set filter for this mandala widget
        val filterIntent = Intent(context, WidgetFilterActivity::class.java).apply {
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
            putExtra("filter_type", "menu")
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val filterPendingIntent = PendingIntent.getActivity(
            context,
            appWidgetId * 100 + 25,
            filterIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.mandala_btn_filter, filterPendingIntent)

        // Filter Buttons Strip -> Direct access to each filter category
        fun setupFilterButton(viewId: Int, filterTypeStr: String, reqCodeOffset: Int) {
            val fIntent = Intent(context, WidgetFilterActivity::class.java).apply {
                putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
                putExtra("filter_type", filterTypeStr)
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }
            val fPendingIntent = PendingIntent.getActivity(
                context,
                appWidgetId * 100 + reqCodeOffset,
                fIntent,
                PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
            )
            views.setOnClickPendingIntent(viewId, fPendingIntent)
        }

        setupFilterButton(R.id.mandala_filter_list, "list", 30)
        setupFilterButton(R.id.mandala_filter_tag, "tag", 31)
        setupFilterButton(R.id.mandala_filter_space, "space", 32)
        setupFilterButton(R.id.mandala_filter_subspace, "subspace", 33)
        setupFilterButton(R.id.mandala_filter_priority, "priority", 34)
        setupFilterButton(R.id.mandala_filter_account, "account", 35)
        setupFilterButton(R.id.mandala_filter_date, "date", 36)
        setupFilterButton(R.id.mandala_filter_recurring, "recurring", 37)
        setupFilterButton(R.id.mandala_filter_sort, "sort", 38)
        setupFilterButton(R.id.mandala_filter_hide, "hide", 39)

        // Active Filter Pill Container
        val pillText = WidgetTabFilter.formatFilterPill(filter)
        if (!pillText.isNullOrBlank()) {
            views.setViewVisibility(R.id.mandala_active_filter_container, android.view.View.VISIBLE)
            views.setTextViewText(R.id.mandala_active_filter_text, pillText)
            views.setOnClickPendingIntent(R.id.mandala_active_filter_container, filterPendingIntent)
            views.setOnClickPendingIntent(
                R.id.mandala_btn_clear_filter,
                createBroadcastPendingIntent(context, ACTION_CLEAR_FILTER, appWidgetId, 26)
            )
        } else {
            views.setViewVisibility(R.id.mandala_active_filter_container, android.view.View.GONE)
        }

        // Check if widget is drilled down into a sub-mandala
        val drillPath = prefs.getString("drill_path_$appWidgetId", null) ?: prefs.getString("drill_parent_$appWidgetId", null)
        val pathSegments = drillPath?.split("||")?.filter { it.isNotBlank() } ?: emptyList()

        // Fetch data
        val data = if (pathSegments.isNotEmpty()) {
            loadDrilledData(context, modeStr, drillPath!!, appWidgetId)
        } else {
            loadMandalaData(context, modeStr, appWidgetId)
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
        val modeDisplay = if (pathSegments.isNotEmpty()) {
            "⬅️ ${cleanSegment(pathSegments.last())}"
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

        if (pathSegments.isNotEmpty()) {
            if (focusedSlice != null) {
                val isPortal = focusedSlice.count > 1 ||
                        focusedSlice.label.contains("Batch", ignoreCase = true) ||
                        focusedSlice.label.contains("Completed", ignoreCase = true) ||
                        focusedSlice.subLabels.isNotEmpty()
                if (isPortal) {
                    val subCount = if (focusedSlice.subLabels.isNotEmpty()) " [${focusedSlice.subLabels.size} sub]" else ""
                    pillarText = "⤵ Enter: ${focusedSlice.label} (${focusedSlice.count})$subCount • Tap Canvas"
                    pillPendingIntent = createBroadcastPendingIntent(context, ACTION_DRILL_DOWN, appWidgetId, 11)
                } else {
                    pillarText = "📌 ${focusedSlice.label} • Open App ↗"
                    pillPendingIntent = createBroadcastPendingIntent(context, ACTION_CANVAS_CLICK, appWidgetId, 12)
                }
            } else {
                pillarText = "Total: ${data.totalCount} in ${cleanSegment(pathSegments.last())} • Tap ⬅️ to Return"
                pillPendingIntent = createBroadcastPendingIntent(context, ACTION_DRILL_UP, appWidgetId, 9)
            }
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
            putExtra("open_tab_id", filter.id)
            val targetFocus = if (pathSegments.isNotEmpty()) {
                cleanSegment(pathSegments.last())
            } else if (focusedSlice != null) {
                cleanSegment(focusedSlice.label)
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
    private data class WidgetTask(
        val id: String,
        val title: String,
        val priority: String,
        val status: String,
        val due: String?,
        val listTitle: String?,
        val spacesJson: String?,
        val tagsJson: String?
    )

    private fun loadDrilledData(context: Context, mode: String, drillPath: String, appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID): MandalaWidgetRenderer.MandalaRenderData {
        val slices = mutableListOf<MandalaWidgetRenderer.MandalaSlice>()
        var total = 0
        var completed = 0

        val pathSegments = drillPath.split("||").map { it.trim() }.filter { it.isNotEmpty() }
        if (pathSegments.isEmpty()) return loadMandalaData(context, mode, appWidgetId)

        val rootSegment = cleanSegment(pathSegments[0])

        val todayStr = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(Date())
        val cal = Calendar.getInstance()
        cal.add(Calendar.DAY_OF_YEAR, 7)
        val nextWeekStr = SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(cal.time)

        fun getPrioColor(prio: String): Int = when (prio.lowercase()) {
            "critical" -> Color.parseColor("#EF4444")
            "high" -> Color.parseColor("#F59E0B")
            "low" -> Color.parseColor("#10B981")
            else -> Color.parseColor("#3B82F6")
        }

        val allTasks = mutableListOf<WidgetTask>()
        val activeFilter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId, isMandala = true)

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    when (mode) {
                        "priorities" -> {
                            val prioTarget = when {
                                rootSegment.contains("critical", ignoreCase = true) -> "critical"
                                rootSegment.contains("high", ignoreCase = true) -> "high"
                                rootSegment.contains("med", ignoreCase = true) -> "medium"
                                rootSegment.contains("low", ignoreCase = true) -> "low"
                                else -> rootSegment.lowercase()
                            }
                            val qb = StringBuilder("SELECT id, title, priority, status, due, list_title, spaces, tags FROM tasks WHERE sync_status != 'pending_delete' AND lower(priority) = lower(?)")
                            val args = mutableListOf(prioTarget)
                            WidgetTabFilter.applyFilterToQuery(activeFilter, qb, args, skipPriority = true)
                            val cursor = db.rawQuery(qb.toString(), args.toTypedArray())
                            cursor.use {
                                while (it.moveToNext()) {
                                    allTasks.add(WidgetTask(
                                        id = it.getString(0) ?: "",
                                        title = it.getString(1) ?: "Task",
                                        priority = it.getString(2) ?: "medium",
                                        status = it.getString(3) ?: "pending",
                                        due = it.getString(4),
                                        listTitle = it.getString(5),
                                        spacesJson = it.getString(6),
                                        tagsJson = it.getString(7)
                                    ))
                                }
                            }
                        }
                        "lists" -> {
                            val qb = StringBuilder("SELECT id, title, priority, status, due, list_title, spaces, tags FROM tasks WHERE sync_status != 'pending_delete' AND lower(trim(list_title)) = lower(trim(?))")
                            val args = mutableListOf(rootSegment)
                            WidgetTabFilter.applyFilterToQuery(activeFilter, qb, args, skipList = true)
                            val cursor = db.rawQuery(qb.toString(), args.toTypedArray())
                            cursor.use {
                                while (it.moveToNext()) {
                                    allTasks.add(WidgetTask(
                                        id = it.getString(0) ?: "",
                                        title = it.getString(1) ?: "Task",
                                        priority = it.getString(2) ?: "medium",
                                        status = it.getString(3) ?: "pending",
                                        due = it.getString(4),
                                        listTitle = it.getString(5),
                                        spacesJson = it.getString(6),
                                        tagsJson = it.getString(7)
                                    ))
                                }
                            }
                        }
                        "tags" -> {
                            val cleanTag = rootSegment.replace("#", "").trim().lowercase()
                            val qb = StringBuilder("SELECT id, title, priority, status, due, list_title, spaces, tags FROM tasks WHERE sync_status != 'pending_delete'")
                            val args = mutableListOf<String>()
                            WidgetTabFilter.applyFilterToQuery(activeFilter, qb, args, skipTag = true)
                            val cursor = db.rawQuery(qb.toString(), if (args.isNotEmpty()) args.toTypedArray() else null)
                            cursor.use {
                                while (it.moveToNext()) {
                                    val tagsJson = it.getString(7) ?: ""
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
                                        allTasks.add(WidgetTask(
                                            id = it.getString(0) ?: "",
                                            title = it.getString(1) ?: "Task",
                                            priority = it.getString(2) ?: "medium",
                                            status = it.getString(3) ?: "pending",
                                            due = it.getString(4),
                                            listTitle = it.getString(5),
                                            spacesJson = it.getString(6),
                                            tagsJson = tagsJson
                                        ))
                                    }
                                }
                            }
                        }
                        else -> { // "spaces", "harada_9x9", "custom", etc.
                            val qb = StringBuilder("SELECT id, title, priority, status, due, list_title, spaces, tags FROM tasks WHERE sync_status != 'pending_delete'")
                            val args = mutableListOf<String>()
                            WidgetTabFilter.applyFilterToQuery(activeFilter, qb, args, skipSpace = true)
                            val cursor = db.rawQuery(qb.toString(), if (args.isNotEmpty()) args.toTypedArray() else null)
                            cursor.use {
                                while (it.moveToNext()) {
                                    val spacesJson = it.getString(6) ?: ""
                                    var matches = false
                                    if (rootSegment.equals("General", ignoreCase = true) || rootSegment.equals("Inbox", ignoreCase = true)) {
                                        if (spacesJson.isBlank() || spacesJson == "{}") matches = true
                                    } else if (spacesJson.isNotBlank() && spacesJson != "{}") {
                                        try {
                                            val obj = JSONObject(spacesJson)
                                            val keys = obj.keys()
                                            while (keys.hasNext()) {
                                                if (keys.next().trim().equals(rootSegment, ignoreCase = true)) {
                                                    matches = true
                                                    break
                                                }
                                            }
                                        } catch (e: Exception) {}
                                    }
                                    if (matches) {
                                        allTasks.add(WidgetTask(
                                            id = it.getString(0) ?: "",
                                            title = it.getString(1) ?: "Task",
                                            priority = it.getString(2) ?: "medium",
                                            status = it.getString(3) ?: "pending",
                                            due = it.getString(4),
                                            listTitle = it.getString(5),
                                            spacesJson = spacesJson,
                                            tagsJson = it.getString(7)
                                        ))
                                    }
                                }
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading drilled data for $drillPath", e)
        }

        val pendingTasks = if (activeFilter.statusFilter == "completed") allTasks else allTasks.filter { it.status != "completed" }
        val completedTasks = if (activeFilter.statusFilter == "pending") emptyList() else allTasks.filter { it.status == "completed" }
        total = pendingTasks.size
        completed = completedTasks.size

        if (pathSegments.size == 1) {
            // Level 1: In the root container (e.g. "My Tasks")
            if (pendingTasks.size <= 12) {
                pendingTasks.forEachIndexed { idx, t ->
                    slices.add(MandalaWidgetRenderer.MandalaSlice(
                        id = t.id.ifEmpty { "task_$idx" },
                        label = t.title,
                        count = 1,
                        completedCount = 0,
                        color = getPrioColor(t.priority)
                    ))
                }
            } else {
                // Decompose large list!
                val isPrioMode = mode == "priorities"
                val prioMap = pendingTasks.groupBy { it.priority.lowercase() }
                val maxPrioShare = if (pendingTasks.isNotEmpty()) (prioMap.values.maxOfOrNull { it.size } ?: 0).toDouble() / pendingTasks.size else 0.0
                val isPrioDiverse = !isPrioMode && prioMap.keys.size > 1 && maxPrioShare < 0.85

                if (isPrioDiverse) {
                    val crit = prioMap["critical"] ?: emptyList()
                    val high = prioMap["high"] ?: emptyList()
                    val med = prioMap["medium"] ?: emptyList()
                    val low = prioMap["low"] ?: emptyList()
                    if (crit.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("p_crit", "🚨 Critical (${crit.size})", crit.size, 0, Color.parseColor("#EF4444"), crit.take(2).map { it.title }))
                    if (high.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("p_high", "🔥 High (${high.size})", high.size, 0, Color.parseColor("#F59E0B"), high.take(2).map { it.title }))
                    if (med.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("p_med", "⚡ Medium (${med.size})", med.size, 0, Color.parseColor("#3B82F6"), med.take(2).map { it.title }))
                    if (low.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("p_low", "🌱 Low (${low.size})", low.size, 0, Color.parseColor("#10B981"), low.take(2).map { it.title }))
                } else {
                    val overdue = pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) < todayStr }
                    val dueToday = pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) == todayStr }
                    val week = pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) > todayStr && it.due.take(10) <= nextWeekStr }
                    val upcoming = pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) > nextWeekStr }
                    val nodue = pendingTasks.filter { it.due.isNullOrEmpty() }

                    if (overdue.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("t_overdue", "🚨 Overdue (${overdue.size})", overdue.size, 0, Color.parseColor("#EF4444"), overdue.take(2).map { it.title }))
                    if (dueToday.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("t_today", "📅 Due Today (${dueToday.size})", dueToday.size, 0, Color.parseColor("#F59E0B"), dueToday.take(2).map { it.title }))
                    if (week.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("t_week", "🌅 This Week (${week.size})", week.size, 0, Color.parseColor("#3B82F6"), week.take(2).map { it.title }))
                    if (upcoming.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("t_upcoming", "📆 Upcoming (${upcoming.size})", upcoming.size, 0, Color.parseColor("#8B5CF6"), upcoming.take(2).map { it.title }))
                    if (nodue.isNotEmpty()) slices.add(MandalaWidgetRenderer.MandalaSlice("t_nodue", "📥 Someday (${nodue.size})", nodue.size, 0, Color.parseColor("#10B981"), nodue.take(2).map { it.title }))
                }
            }

            if (completedTasks.isNotEmpty()) {
                slices.add(MandalaWidgetRenderer.MandalaSlice("t_done", "✓ Completed (${completedTasks.size})", completedTasks.size, completedTasks.size, Color.parseColor("#64748B"), completedTasks.take(2).map { it.title }))
            }
        } else {
            // Level 2+: Inside a Portal / Chamber
            val subRaw = pathSegments[1].lowercase()
            val chamberTasks: List<WidgetTask> = when {
                subRaw.contains("completed") || subRaw.contains("done") -> completedTasks
                subRaw.contains("critical") -> pendingTasks.filter { it.priority.lowercase() == "critical" }
                subRaw.contains("high") -> pendingTasks.filter { it.priority.lowercase() == "high" }
                subRaw.contains("med") -> pendingTasks.filter { it.priority.lowercase() == "medium" }
                subRaw.contains("low") -> pendingTasks.filter { it.priority.lowercase() == "low" }
                subRaw.contains("overdue") -> pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) < todayStr }
                subRaw.contains("today") -> pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) == todayStr }
                subRaw.contains("week") -> pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) > todayStr && it.due.take(10) <= nextWeekStr }
                subRaw.contains("upcoming") || subRaw.contains("later") -> pendingTasks.filter { !it.due.isNullOrEmpty() && it.due.take(10) > nextWeekStr }
                subRaw.contains("someday") || subRaw.contains("no due") || subRaw.contains("nodue") -> pendingTasks.filter { it.due.isNullOrEmpty() }
                else -> pendingTasks
            }

            if (pathSegments.size == 2) {
                if (chamberTasks.size <= 12) {
                    chamberTasks.forEachIndexed { idx, t ->
                        slices.add(MandalaWidgetRenderer.MandalaSlice(
                            id = t.id.ifEmpty { "ctask_$idx" },
                            label = t.title,
                            count = 1,
                            completedCount = if (t.status == "completed") 1 else 0,
                            color = getPrioColor(t.priority)
                        ))
                    }
                } else {
                    // Harada 8-Task Action Batches!
                    val batchSize = 8
                    val batchColors = listOf(
                        Color.parseColor("#EC4899"), // Rose
                        Color.parseColor("#8B5CF6"), // Violet
                        Color.parseColor("#3B82F6"), // Blue
                        Color.parseColor("#06B6D4"), // Cyan
                        Color.parseColor("#10B981"), // Emerald
                        Color.parseColor("#F59E0B"), // Amber
                        Color.parseColor("#F97316"), // Orange
                        Color.parseColor("#E11D48")  // Ruby
                    )
                    val numBatches = (chamberTasks.size + batchSize - 1) / batchSize
                    for (b in 0 until numBatches) {
                        val start = b * batchSize
                        val end = minOf(start + batchSize, chamberTasks.size)
                        val bSlice = chamberTasks.subList(start, end)
                        val bColor = batchColors[b % batchColors.size]
                        slices.add(MandalaWidgetRenderer.MandalaSlice(
                            id = "batch_$b",
                            label = "🎯 Focus Batch ${b + 1} (${bSlice.size})",
                            count = bSlice.size,
                            completedCount = bSlice.count { it.status == "completed" },
                            color = bColor,
                            subLabels = bSlice.take(2).map { it.title }
                        ))
                    }
                }
            } else {
                // Level 3+: Specific Action Batch selected
                val batchStr = pathSegments[2]
                val match = Regex("""Batch\s*(\d+)""", RegexOption.IGNORE_CASE).find(batchStr)
                val bIndex = if (match != null) (match.groupValues[1].toIntOrNull() ?: 1) - 1 else 0
                val start = bIndex * 8
                val end = minOf(start + 8, chamberTasks.size)
                val batchTasks = if (start in chamberTasks.indices) chamberTasks.subList(start, end) else emptyList()

                batchTasks.forEachIndexed { idx, t ->
                    slices.add(MandalaWidgetRenderer.MandalaSlice(
                        id = t.id.ifEmpty { "btask_$idx" },
                        label = t.title,
                        count = 1,
                        completedCount = if (t.status == "completed") 1 else 0,
                        color = getPrioColor(t.priority)
                    ))
                }
            }
        }

        // Harada 9x9 custom fallback if still empty
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
                                if (node.optString("label", "").equals(rootSegment, ignoreCase = true)) {
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
        }

        val displayCenter = cleanSegment(pathSegments.last())
        return MandalaWidgetRenderer.MandalaRenderData(
            title = "$displayCenter Sub-Mandala",
            centerGoal = displayCenter,
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadMandalaData(context: Context, mode: String, appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID): MandalaWidgetRenderer.MandalaRenderData {
        return when (mode) {
            "harada_9x9" -> loadHaradaData(context)
            "priorities" -> loadPrioritiesData(context, appWidgetId)
            "lists" -> loadListsData(context, appWidgetId)
            "tags" -> loadTagsData(context, appWidgetId)
            "custom" -> loadCustomMandalaData(context)
            else -> loadSpacesData(context, appWidgetId)
        }
    }

    private fun loadSpacesData(context: Context, appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID): MandalaWidgetRenderer.MandalaRenderData {
        val spaceMap = mutableMapOf<String, MutableList<String>>() // Space -> Subspaces
        val spaceCounts = mutableMapOf<String, Int>()
        var total = 0
        var completed = 0

        val filter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId, isMandala = true)

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val qb = StringBuilder("SELECT spaces, status FROM tasks WHERE sync_status != 'pending_delete'")
                    val args = mutableListOf<String>()
                    WidgetTabFilter.applyFilterToQuery(filter, qb, args, skipSpace = true)
                    val cursor = db.rawQuery(qb.toString(), if (args.isNotEmpty()) args.toTypedArray() else null)
                    cursor.use {
                        while (it.moveToNext()) {
                            val spacesJson = it.getString(0) ?: ""
                            val status = it.getString(1) ?: "pending"
                            val isDone = (status == "completed")
                            if (isDone) completed++ else total++

                            val shouldInclude = when (filter.statusFilter) {
                                "completed" -> isDone
                                "all" -> true
                                else -> !isDone
                            }

                            if (shouldInclude) {
                                var hasAssignedSpace = false
                                if (spacesJson.isNotBlank() && spacesJson != "{}") {
                                    try {
                                        val obj = JSONObject(spacesJson)
                                        val keys = obj.keys()
                                        while (keys.hasNext()) {
                                            val space = keys.next().trim()
                                            if (space.isNotEmpty()) {
                                                hasAssignedSpace = true
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
                                if (!hasAssignedSpace) {
                                    spaceCounts["General"] = (spaceCounts["General"] ?: 0) + 1
                                }
                            }
                        }
                    }
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Error loading spaces data", e)
        }

        val slices = mutableListOf<MandalaWidgetRenderer.MandalaSlice>()
        if (spaceCounts.isEmpty()) {
            if (total == 0) {
                slices.add(MandalaWidgetRenderer.MandalaSlice("space_empty", "No Tasks 🎉", 0, 0, Color.parseColor("#64748B")))
            } else {
                slices.add(MandalaWidgetRenderer.MandalaSlice("space_general", "General", total, 0, 0))
            }
        } else if (spaceCounts.size == 1 && (spaceMap[spaceCounts.keys.first()]?.isNotEmpty() == true)) {
            val singleSpace = spaceCounts.keys.first()
            val subs = spaceMap[singleSpace] ?: emptyList()
            subs.forEachIndexed { idx, subName ->
                slices.add(
                    MandalaWidgetRenderer.MandalaSlice(
                        id = "sub_$idx",
                        label = subName,
                        count = 1,
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
            centerGoal = if (filter.title.isNotBlank()) filter.title else "Focus",
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

    private fun loadPrioritiesData(context: Context, appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID): MandalaWidgetRenderer.MandalaRenderData {
        var pCritical = 0
        var pHigh = 0
        var pMed = 0
        var pLow = 0
        var total = 0
        var completed = 0

        val filter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId, isMandala = true)

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val qb = StringBuilder("SELECT priority, status FROM tasks WHERE sync_status != 'pending_delete'")
                    val args = mutableListOf<String>()
                    WidgetTabFilter.applyFilterToQuery(filter, qb, args, skipPriority = true)
                    val cursor = db.rawQuery(qb.toString(), if (args.isNotEmpty()) args.toTypedArray() else null)
                    cursor.use {
                        while (it.moveToNext()) {
                            val prio = it.getString(0)?.lowercase() ?: "medium"
                            val status = it.getString(1) ?: "pending"
                            val isDone = (status == "completed")
                            if (isDone) completed++ else total++

                            val shouldInclude = when (filter.statusFilter) {
                                "completed" -> isDone
                                "all" -> true
                                else -> !isDone
                            }

                            if (shouldInclude) {
                                when (prio) {
                                    "critical" -> pCritical++
                                    "high" -> pHigh++
                                    "medium", "normal" -> pMed++
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
            centerGoal = if (filter.title.isNotBlank()) filter.title else "Focus",
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadListsData(context: Context, appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID): MandalaWidgetRenderer.MandalaRenderData {
        val listCounts = mutableMapOf<String, Int>()
        var total = 0
        var completed = 0

        val filter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId, isMandala = true)

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val qb = StringBuilder("SELECT list_title, status, count(*) FROM tasks WHERE sync_status != 'pending_delete'")
                    val args = mutableListOf<String>()
                    WidgetTabFilter.applyFilterToQuery(filter, qb, args, skipList = true)
                    qb.append(" GROUP BY list_title, status")
                    val cursor = db.rawQuery(qb.toString(), if (args.isNotEmpty()) args.toTypedArray() else null)
                    cursor.use {
                        while (it.moveToNext()) {
                            val rawTitle = it.getString(0)
                            val title = if (rawTitle.isNullOrBlank()) "Tasks" else rawTitle.trim()
                            val status = it.getString(1) ?: "pending"
                            val count = it.getInt(2)
                            val isDone = (status == "completed")
                            if (isDone) completed += count else total += count

                            val shouldInclude = when (filter.statusFilter) {
                                "completed" -> isDone
                                "all" -> true
                                else -> !isDone
                            }

                            if (shouldInclude) {
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
            if (total == 0) {
                slices.add(MandalaWidgetRenderer.MandalaSlice("l_empty", "No Tasks 🎉", 0, 0, Color.parseColor("#64748B")))
            } else {
                slices.add(MandalaWidgetRenderer.MandalaSlice("l_0", "My Tasks", total, 0, 0))
            }
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
            centerGoal = if (filter.title.isNotBlank()) filter.title else "Lists",
            totalCount = total,
            completedCount = completed,
            slices = slices
        )
    }

    private fun loadTagsData(context: Context, appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID): MandalaWidgetRenderer.MandalaRenderData {
        val tagCounts = mutableMapOf<String, Int>()
        var total = 0
        var completed = 0

        val filter = WidgetTabFilter.getActiveTabFilter(context, appWidgetId, isMandala = true)

        try {
            val dbFile = context.getDatabasePath("gtasks_local.db")
            if (dbFile.exists()) {
                SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                    val qb = StringBuilder("SELECT tags, status FROM tasks WHERE sync_status != 'pending_delete'")
                    val args = mutableListOf<String>()
                    WidgetTabFilter.applyFilterToQuery(filter, qb, args, skipTag = true)
                    val cursor = db.rawQuery(qb.toString(), if (args.isNotEmpty()) args.toTypedArray() else null)
                    cursor.use {
                        while (it.moveToNext()) {
                            val tagsJson = it.getString(0) ?: ""
                            val status = it.getString(1) ?: "pending"
                            val isDone = (status == "completed")
                            if (isDone) completed++ else total++

                            val shouldInclude = when (filter.statusFilter) {
                                "completed" -> isDone
                                "all" -> true
                                else -> !isDone
                            }

                            var hasTag = false
                            if (shouldInclude && tagsJson.isNotBlank() && tagsJson != "[]") {
                                try {
                                    val arr = JSONArray(tagsJson)
                                    for (i in 0 until arr.length()) {
                                        val t = arr.getString(i).trim()
                                        if (t.isNotEmpty()) {
                                            hasTag = true
                                            tagCounts[t] = (tagCounts[t] ?: 0) + 1
                                        }
                                    }
                                } catch (e: Exception) {}
                            }
                            if (shouldInclude && !hasTag) {
                                tagCounts["Untagged"] = (tagCounts["Untagged"] ?: 0) + 1
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
            if (total == 0) {
                slices.add(MandalaWidgetRenderer.MandalaSlice("t_empty", "No Tasks 🎉", 0, 0, Color.parseColor("#64748B")))
            } else {
                slices.add(MandalaWidgetRenderer.MandalaSlice("t_0", "#Untagged", total, 0, 0))
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
            centerGoal = if (filter.title.isNotBlank()) filter.title else "Tags",
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
