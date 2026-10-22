package com.gtasks.gtasks_app

import android.appwidget.AppWidgetManager
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.util.Log
import org.json.JSONArray
import org.json.JSONObject

data class WidgetTabFilter(
    val id: String = "all",
    val title: String = "✦ All Tasks",
    val tabIndex: Int = 0,
    val totalTabs: Int = 1,
    val accounts: Set<String> = emptySet(),
    val statusFilter: String = "pending",
    val hideRecurring: Boolean = false,
    val hiddenLists: Set<String> = emptySet(),
    val hiddenTags: Set<String> = emptySet(),
    val selectedLists: Set<String> = emptySet(),
    val selectedTags: Set<String> = emptySet(),
    val selectedSpace: String? = null,
    val selectedSubspace: String? = null,
    val selectedPriority: String? = null,
    val filterType: String? = null,
    val filterVal: String? = null,
    val sortBy: String = "priority",
    val sortAscending: Boolean = true
) {
    companion object {
        private const val TAG = "WidgetTabFilter"
        const val WIDGET_PREFS = "gtasks_widget_prefs"

        fun getActiveTabFilter(
            context: Context,
            appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID,
            isMandala: Boolean = false
        ): WidgetTabFilter {
            try {
                val prefs = context.getSharedPreferences(WIDGET_PREFS, Context.MODE_PRIVATE)
                val tabsJson = prefs.getString("tabs_json", null)
                val tabIndexKey = "tab_index_$appWidgetId"
                val statusOverrideKey = "mandala_status_$appWidgetId"
                val widgetStatus = if (isMandala && appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    prefs.getString(statusOverrideKey, null)
                } else null

                if (!tabsJson.isNullOrEmpty()) {
                    val arr = JSONArray(tabsJson)
                    if (arr.length() > 0) {
                        val defaultActive = prefs.getInt("active_tab_index", 0)
                        var tabIndex = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                            prefs.getInt(tabIndexKey, defaultActive)
                        } else {
                            defaultActive
                        }
                        if (tabIndex < 0 || tabIndex >= arr.length()) {
                            tabIndex = 0
                        }
                        val obj = arr.getJSONObject(tabIndex)

                        val id = obj.optString("id", "tab_$tabIndex")
                        val title = obj.optString("title", "✦ Tab ${tabIndex + 1}")

                        val accs = mutableSetOf<String>()
                        val accsArr = obj.optJSONArray("accounts")
                        if (accsArr != null) {
                            for (i in 0 until accsArr.length()) {
                                val a = accsArr.getString(i).trim()
                                if (a.isNotEmpty() && a != "all") accs.add(a)
                            }
                        } else {
                            val acc = obj.optString("account", "").trim()
                            if (acc.isNotEmpty() && acc != "all") accs.add(acc)
                        }

                        val status = widgetStatus ?: obj.optString("statusFilter", "pending")
                        val hideRec = obj.optBoolean("hideRecurring", false)

                        val hLists = mutableSetOf<String>()
                        val hlArr = obj.optJSONArray("hiddenLists")
                        if (hlArr != null) {
                            for (i in 0 until hlArr.length()) {
                                val l = hlArr.getString(i).trim()
                                if (l.isNotEmpty()) hLists.add(l)
                            }
                        }

                        val hTags = mutableSetOf<String>()
                        val htArr = obj.optJSONArray("hiddenTags")
                        if (htArr != null) {
                            for (i in 0 until htArr.length()) {
                                val t = htArr.getString(i).trim()
                                if (t.isNotEmpty()) hTags.add(t)
                            }
                        }

                        val sLists = mutableSetOf<String>()
                        val slArr = obj.optJSONArray("selectedLists")
                        if (slArr != null) {
                            for (i in 0 until slArr.length()) {
                                val l = slArr.getString(i).trim()
                                if (l.isNotEmpty()) sLists.add(l)
                            }
                        }

                        val sTags = mutableSetOf<String>()
                        val stArr = obj.optJSONArray("selectedTags")
                        if (stArr != null) {
                            for (i in 0 until stArr.length()) {
                                val t = stArr.getString(i).trim()
                                if (t.isNotEmpty()) sTags.add(t)
                            }
                        }

                        val sp = obj.optString("selectedSpace").ifEmpty { null }
                        val sub = obj.optString("selectedSubspace").ifEmpty { null }
                        val prio = obj.optString("selectedPriority").ifEmpty { null }
                        val fType = obj.optString("filterType").ifEmpty { null }
                        val fVal = obj.optString("filterVal").ifEmpty { null }
                        val sortF = obj.optString("sortField", "priority")
                        val sortAsc = obj.optBoolean("sortAscending", true)

                        return WidgetTabFilter(
                            id = id,
                            title = title,
                            tabIndex = tabIndex,
                            totalTabs = arr.length(),
                            accounts = accs,
                            statusFilter = status,
                            hideRecurring = hideRec,
                            hiddenLists = hLists,
                            hiddenTags = hTags,
                            selectedLists = sLists,
                            selectedTags = sTags,
                            selectedSpace = sp,
                            selectedSubspace = sub,
                            selectedPriority = prio,
                            filterType = fType,
                            filterVal = fVal,
                            sortBy = sortF,
                            sortAscending = sortAsc
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error parsing active tab filter", e)
            }

            val defaultStatus = if (isMandala && appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                context.getSharedPreferences(WIDGET_PREFS, Context.MODE_PRIVATE)
                    .getString("mandala_status_$appWidgetId", "pending") ?: "pending"
            } else {
                "pending"
            }
            return WidgetTabFilter(statusFilter = defaultStatus)
        }

        fun getAvailableTabs(context: Context): List<WidgetTabFilter> {
            val tabs = mutableListOf<WidgetTabFilter>()
            try {
                val prefs = context.getSharedPreferences(WIDGET_PREFS, Context.MODE_PRIVATE)
                val tabsJson = prefs.getString("tabs_json", null)
                if (!tabsJson.isNullOrEmpty()) {
                    val arr = JSONArray(tabsJson)
                    for (i in 0 until arr.length()) {
                        val obj = arr.getJSONObject(i)
                        val id = obj.optString("id", "tab_$i")
                        val title = obj.optString("title", "✦ Tab ${i + 1}")

                        val accs = mutableSetOf<String>()
                        val accsArr = obj.optJSONArray("accounts")
                        if (accsArr != null) {
                            for (j in 0 until accsArr.length()) {
                                val a = accsArr.getString(j).trim()
                                if (a.isNotEmpty() && a != "all") accs.add(a)
                            }
                        } else {
                            val acc = obj.optString("account", "").trim()
                            if (acc.isNotEmpty() && acc != "all") accs.add(acc)
                        }

                        val status = obj.optString("statusFilter", "pending")
                        val hideRec = obj.optBoolean("hideRecurring", false)

                        val hLists = mutableSetOf<String>()
                        val hlArr = obj.optJSONArray("hiddenLists")
                        if (hlArr != null) {
                            for (j in 0 until hlArr.length()) {
                                val l = hlArr.getString(j).trim()
                                if (l.isNotEmpty()) hLists.add(l)
                            }
                        }

                        val hTags = mutableSetOf<String>()
                        val htArr = obj.optJSONArray("hiddenTags")
                        if (htArr != null) {
                            for (j in 0 until htArr.length()) {
                                val t = htArr.getString(j).trim()
                                if (t.isNotEmpty()) hTags.add(t)
                            }
                        }

                        val sLists = mutableSetOf<String>()
                        val slArr = obj.optJSONArray("selectedLists")
                        if (slArr != null) {
                            for (j in 0 until slArr.length()) {
                                val l = slArr.getString(j).trim()
                                if (l.isNotEmpty()) sLists.add(l)
                            }
                        }

                        val sTags = mutableSetOf<String>()
                        val stArr = obj.optJSONArray("selectedTags")
                        if (stArr != null) {
                            for (j in 0 until stArr.length()) {
                                val t = stArr.getString(j).trim()
                                if (t.isNotEmpty()) sTags.add(t)
                            }
                        }

                        val sp = obj.optString("selectedSpace").ifEmpty { null }
                        val sub = obj.optString("selectedSubspace").ifEmpty { null }
                        val prio = obj.optString("selectedPriority").ifEmpty { null }
                        val fType = obj.optString("filterType").ifEmpty { null }
                        val fVal = obj.optString("filterVal").ifEmpty { null }
                        val sortF = obj.optString("sortField", "priority")
                        val sortAsc = obj.optBoolean("sortAscending", true)

                        tabs.add(
                            WidgetTabFilter(
                                id = id,
                                title = title,
                                tabIndex = i,
                                totalTabs = arr.length(),
                                accounts = accs,
                                statusFilter = status,
                                hideRecurring = hideRec,
                                hiddenLists = hLists,
                                hiddenTags = hTags,
                                selectedLists = sLists,
                                selectedTags = sTags,
                                selectedSpace = sp,
                                selectedSubspace = sub,
                                selectedPriority = prio,
                                filterType = fType,
                                filterVal = fVal,
                                sortBy = sortF,
                                sortAscending = sortAsc
                            )
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error getting available tabs", e)
            }

            if (tabs.isNotEmpty()) {
                return tabs
            }

            // Fallback default tabs if not yet synced from Flutter
            tabs.add(WidgetTabFilter("all", "✦ All Tasks", 0, 3, emptySet(), "pending"))
            tabs.add(WidgetTabFilter("today", "⏰ Today & Due", 1, 3, emptySet(), "pending", filterType = "date", filterVal = "today"))
            tabs.add(WidgetTabFilter("priority", "🔥 High Priority", 2, 3, emptySet(), "pending", selectedPriority = "high"))

            return tabs
        }

        fun applyFilterToQuery(
            filter: WidgetTabFilter,
            queryBuilder: StringBuilder,
            args: MutableList<String>,
            skipPriority: Boolean = false,
            skipList: Boolean = false,
            skipSpace: Boolean = false
        ) {
            // Account filter: safely match account or fallback to 'default' if local DB uses default
            if (filter.accounts.isNotEmpty() && !filter.accounts.contains("all")) {
                val placeholders = filter.accounts.map { "?" }.joinToString(",")
                queryBuilder.append(" AND (account IN ($placeholders) OR account = 'default' OR account IS NULL)")
                args.addAll(filter.accounts)
            }

            // Status filter: respect pending / completed / all
            when (filter.statusFilter) {
                "pending" -> queryBuilder.append(" AND (status IS NULL OR status != 'completed')")
                "completed" -> queryBuilder.append(" AND status = 'completed'")
                // "all" -> no status restriction
            }

            // Recurring exclusion
            if (filter.hideRecurring) {
                queryBuilder.append(" AND (is_recurring = 0 OR is_recurring IS NULL) AND (recurrence_type IS NULL OR recurrence_type = '')")
            }

            // Hidden lists exclusion
            if (filter.hiddenLists.isNotEmpty()) {
                val placeholders = filter.hiddenLists.map { "?" }.joinToString(",")
                queryBuilder.append(" AND (list_title IS NULL OR list_title NOT IN ($placeholders))")
                args.addAll(filter.hiddenLists)
            }

            // Hidden tags exclusion
            if (filter.hiddenTags.isNotEmpty()) {
                for (t in filter.hiddenTags) {
                    queryBuilder.append(" AND (tags IS NULL OR tags NOT LIKE ?)")
                    args.add("%\"$t\"%")
                }
            }

            // Selected lists filter
            if (!skipList && filter.selectedLists.isNotEmpty()) {
                val placeholders = filter.selectedLists.map { "?" }.joinToString(",")
                queryBuilder.append(" AND list_title IN ($placeholders)")
                args.addAll(filter.selectedLists)
            }

            // Selected priority filter
            if (!skipPriority && filter.selectedPriority != null) {
                if (filter.selectedPriority.equals("high", ignoreCase = true)) {
                    queryBuilder.append(" AND lower(priority) IN ('critical', 'high')")
                } else {
                    queryBuilder.append(" AND lower(priority) = ?")
                    args.add(filter.selectedPriority.lowercase())
                }
            }

            // Selected space & subspace filter
            if (!skipSpace && filter.selectedSpace != null) {
                queryBuilder.append(" AND spaces LIKE ?")
                args.add("%\"${filter.selectedSpace}\"%")
                if (filter.selectedSubspace != null && filter.selectedSubspace.isNotBlank()) {
                    queryBuilder.append(" AND spaces LIKE ?")
                    args.add("%\"${filter.selectedSubspace}\"%")
                }
            }

            // filterType & filterVal logic (e.g. date / list / tag / space / priority)
            if (!filter.filterType.isNullOrBlank() && !filter.filterVal.isNullOrBlank()) {
                when (filter.filterType) {
                    "date" -> {
                        when (filter.filterVal.lowercase()) {
                            "today" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) <= date('now', 'localtime')")
                            "tomorrow" -> queryBuilder.append(" AND substr(due, 1, 10) = date('now', 'localtime', '+1 day')")
                            "overdue" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) < date('now', 'localtime')")
                            "next 7 days" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) >= date('now', 'localtime') AND substr(due, 1, 10) <= date('now', 'localtime', '+7 days')")
                            "upcoming" -> queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) >= date('now', 'localtime')")
                            "no due date" -> queryBuilder.append(" AND (due IS NULL OR due = '')")
                        }
                    }
                    "list" -> {
                        if (!skipList && filter.selectedLists.isEmpty()) {
                            queryBuilder.append(" AND list_title = ?")
                            args.add(filter.filterVal)
                        }
                    }
                    "tag" -> {
                        if (filter.selectedTags.isEmpty()) {
                            queryBuilder.append(" AND tags LIKE ?")
                            args.add("%\"${filter.filterVal}\"%")
                        }
                    }
                    "space" -> {
                        if (!skipSpace && filter.selectedSpace == null) {
                            queryBuilder.append(" AND spaces LIKE ?")
                            args.add("%\"${filter.filterVal}\"%")
                        }
                    }
                    "subspace" -> {
                        if (!skipSpace && filter.selectedSpace == null) {
                            val parts = filter.filterVal.split(" › ")
                            if (parts.size >= 2) {
                                queryBuilder.append(" AND spaces LIKE ? AND spaces LIKE ?")
                                args.add("%\"${parts[0]}\"%")
                                args.add("%\"${parts[1]}\"%")
                            } else {
                                queryBuilder.append(" AND spaces LIKE ?")
                                args.add("%\"${filter.filterVal}\"%")
                            }
                        }
                    }
                    "priority" -> {
                        if (!skipPriority && filter.selectedPriority == null) {
                            if (filter.filterVal.lowercase() == "high") {
                                queryBuilder.append(" AND lower(priority) IN ('critical', 'high')")
                            } else {
                                queryBuilder.append(" AND lower(priority) = ?")
                                args.add(filter.filterVal.lowercase())
                            }
                        }
                    }
                }
            }
        }
    }
}
