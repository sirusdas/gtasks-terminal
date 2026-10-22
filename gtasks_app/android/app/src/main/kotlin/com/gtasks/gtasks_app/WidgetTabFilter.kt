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
    val sortAscending: Boolean = true,
    val dateField: String? = null,
    val dateRangeStart: String? = null,
    val dateRangeEnd: String? = null
) {
    companion object {
        private const val TAG = "WidgetTabFilter"
        const val WIDGET_PREFS = "gtasks_widget_prefs"

        private fun JSONObject.optNullableString(name: String): String? {
            if (this.isNull(name)) return null
            val v = this.optString(name, "").trim()
            return if (v.isEmpty() || v.equals("null", ignoreCase = true)) null else v
        }

        fun getActiveTabFilter(
            context: Context,
            appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID,
            isMandala: Boolean = false
        ): WidgetTabFilter {
            try {
                val prefs = context.getSharedPreferences(WIDGET_PREFS, Context.MODE_PRIVATE)
                val tabsJson = prefs.getString("tabs_json", null)
                val tabIndexKey = "tab_index_$appWidgetId"
                val statusOverrideKey = if (isMandala) "mandala_status_$appWidgetId" else "widget_status_$appWidgetId"
                val widgetStatus = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    prefs.getString(statusOverrideKey, null)
                } else null

                val widgetFilterType = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) prefs.getString("filter_type_$appWidgetId", null) else null
                val widgetFilterVal = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) prefs.getString("filter_val_$appWidgetId", null) else null
                val widgetHideRecurring = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID && prefs.contains("hide_recurring_$appWidgetId")) {
                    prefs.getBoolean("hide_recurring_$appWidgetId", false)
                } else null
                val widgetHiddenLists = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) prefs.getStringSet("hidden_lists_$appWidgetId", null) else null
                val widgetHiddenTags = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) prefs.getStringSet("hidden_tags_$appWidgetId", null) else null
                val widgetSortBy = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) prefs.getString("sort_by_$appWidgetId", null) else null

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

                        val id = obj.optNullableString("id") ?: "tab_$tabIndex"
                        val title = obj.optNullableString("title") ?: "✦ Tab ${tabIndex + 1}"

                        val accs = mutableSetOf<String>()
                        val accsArr = obj.optJSONArray("accounts")
                        if (accsArr != null) {
                            for (i in 0 until accsArr.length()) {
                                if (!accsArr.isNull(i)) {
                                    val a = accsArr.getString(i).trim()
                                    if (a.isNotEmpty() && a != "all" && !a.equals("null", ignoreCase = true)) {
                                        accs.add(a)
                                    }
                                }
                            }
                        } else {
                            val acc = obj.optNullableString("account")
                            if (acc != null && acc != "all") accs.add(acc)
                        }

                        val status = widgetStatus ?: obj.optNullableString("statusFilter") ?: "pending"
                        val hideRec = widgetHideRecurring ?: obj.optBoolean("hideRecurring", false)

                        val hLists = widgetHiddenLists?.toSet() ?: mutableSetOf<String>().apply {
                            val hlArr = obj.optJSONArray("hiddenLists")
                            if (hlArr != null) {
                                for (i in 0 until hlArr.length()) {
                                    if (!hlArr.isNull(i)) {
                                        val l = hlArr.getString(i).trim()
                                        if (l.isNotEmpty() && !l.equals("null", ignoreCase = true)) add(l)
                                    }
                                }
                            }
                        }

                        val hTags = widgetHiddenTags?.toSet() ?: mutableSetOf<String>().apply {
                            val htArr = obj.optJSONArray("hiddenTags")
                            if (htArr != null) {
                                for (i in 0 until htArr.length()) {
                                    if (!htArr.isNull(i)) {
                                        val t = htArr.getString(i).trim()
                                        if (t.isNotEmpty() && !t.equals("null", ignoreCase = true)) add(t)
                                    }
                                }
                            }
                        }

                        val sLists = mutableSetOf<String>()
                        val slArr = obj.optJSONArray("selectedLists")
                        if (slArr != null) {
                            for (i in 0 until slArr.length()) {
                                if (!slArr.isNull(i)) {
                                    val l = slArr.getString(i).trim()
                                    if (l.isNotEmpty() && !l.equals("null", ignoreCase = true)) sLists.add(l)
                                }
                            }
                        }

                        val sTags = mutableSetOf<String>()
                        val stArr = obj.optJSONArray("selectedTags")
                        if (stArr != null) {
                            for (i in 0 until stArr.length()) {
                                if (!stArr.isNull(i)) {
                                    val t = stArr.getString(i).trim()
                                    if (t.isNotEmpty() && !t.equals("null", ignoreCase = true)) sTags.add(t)
                                }
                            }
                        }

                        val sp = obj.optNullableString("selectedSpace")
                        val sub = obj.optNullableString("selectedSubspace")
                        val prio = obj.optNullableString("selectedPriority")
                        val fType = widgetFilterType ?: obj.optNullableString("filterType")
                        val fVal = widgetFilterVal ?: obj.optNullableString("filterVal")
                        val sortF = widgetSortBy ?: obj.optNullableString("sortField") ?: "priority"
                        val sortAsc = obj.optBoolean("sortAscending", true)

                        val dField = obj.optNullableString("dateField")
                        val dStart = obj.optNullableString("dateRangeStart")
                        val dEnd = obj.optNullableString("dateRangeEnd")

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
                            sortAscending = sortAsc,
                            dateField = dField,
                            dateRangeStart = dStart,
                            dateRangeEnd = dEnd
                        )
                    }
                }
            } catch (e: Exception) {
                Log.e(TAG, "Error parsing active tab filter", e)
            }

            val defaultStatus = if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                if (isMandala) {
                    context.getSharedPreferences(WIDGET_PREFS, Context.MODE_PRIVATE)
                        .getString("mandala_status_$appWidgetId", "pending") ?: "pending"
                } else {
                    context.getSharedPreferences(WIDGET_PREFS, Context.MODE_PRIVATE)
                        .getString("widget_status_$appWidgetId", "pending") ?: "pending"
                }
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
                        val id = obj.optNullableString("id") ?: "tab_$i"
                        val title = obj.optNullableString("title") ?: "✦ Tab ${i + 1}"

                        val accs = mutableSetOf<String>()
                        val accsArr = obj.optJSONArray("accounts")
                        if (accsArr != null) {
                            for (j in 0 until accsArr.length()) {
                                if (!accsArr.isNull(j)) {
                                    val a = accsArr.getString(j).trim()
                                    if (a.isNotEmpty() && a != "all" && !a.equals("null", ignoreCase = true)) {
                                        accs.add(a)
                                    }
                                }
                            }
                        } else {
                            val acc = obj.optNullableString("account")
                            if (acc != null && acc != "all") accs.add(acc)
                        }

                        val status = obj.optNullableString("statusFilter") ?: "pending"
                        val hideRec = obj.optBoolean("hideRecurring", false)

                        val hLists = mutableSetOf<String>()
                        val hlArr = obj.optJSONArray("hiddenLists")
                        if (hlArr != null) {
                            for (j in 0 until hlArr.length()) {
                                if (!hlArr.isNull(j)) {
                                    val l = hlArr.getString(j).trim()
                                    if (l.isNotEmpty() && !l.equals("null", ignoreCase = true)) hLists.add(l)
                                }
                            }
                        }

                        val hTags = mutableSetOf<String>()
                        val htArr = obj.optJSONArray("hiddenTags")
                        if (htArr != null) {
                            for (j in 0 until htArr.length()) {
                                if (!htArr.isNull(j)) {
                                    val t = htArr.getString(j).trim()
                                    if (t.isNotEmpty() && !t.equals("null", ignoreCase = true)) hTags.add(t)
                                }
                            }
                        }

                        val sLists = mutableSetOf<String>()
                        val slArr = obj.optJSONArray("selectedLists")
                        if (slArr != null) {
                            for (j in 0 until slArr.length()) {
                                if (!slArr.isNull(j)) {
                                    val l = slArr.getString(j).trim()
                                    if (l.isNotEmpty() && !l.equals("null", ignoreCase = true)) sLists.add(l)
                                }
                            }
                        }

                        val sTags = mutableSetOf<String>()
                        val stArr = obj.optJSONArray("selectedTags")
                        if (stArr != null) {
                            for (j in 0 until stArr.length()) {
                                if (!stArr.isNull(j)) {
                                    val t = stArr.getString(j).trim()
                                    if (t.isNotEmpty() && !t.equals("null", ignoreCase = true)) sTags.add(t)
                                }
                            }
                        }

                        val sp = obj.optNullableString("selectedSpace")
                        val sub = obj.optNullableString("selectedSubspace")
                        val prio = obj.optNullableString("selectedPriority")
                        val fType = obj.optNullableString("filterType")
                        val fVal = obj.optNullableString("filterVal")
                        val sortF = obj.optNullableString("sortField") ?: "priority"
                        val sortAsc = obj.optBoolean("sortAscending", true)

                        val dField = obj.optNullableString("dateField")
                        val dStart = obj.optNullableString("dateRangeStart")
                        val dEnd = obj.optNullableString("dateRangeEnd")

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
                                sortAscending = sortAsc,
                                dateField = dField,
                                dateRangeStart = dStart,
                                dateRangeEnd = dEnd
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
            skipSpace: Boolean = false,
            skipTag: Boolean = false
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

            // Selected tags filter
            if (!skipTag && filter.selectedTags.isNotEmpty()) {
                val tagClauses = filter.selectedTags.map { "tags LIKE ?" }.joinToString(" OR ")
                queryBuilder.append(" AND ($tagClauses)")
                for (t in filter.selectedTags) {
                    args.add("%\"$t\"%")
                }
            }

            // Selected priority filter
            if (!skipPriority && !filter.selectedPriority.isNullOrBlank() && !filter.selectedPriority.equals("null", ignoreCase = true)) {
                if (filter.selectedPriority.equals("high", ignoreCase = true)) {
                    queryBuilder.append(" AND lower(priority) IN ('critical', 'high')")
                } else {
                    queryBuilder.append(" AND lower(priority) = ?")
                    args.add(filter.selectedPriority.lowercase())
                }
            }

            // Selected space & subspace filter
            if (!skipSpace && !filter.selectedSpace.isNullOrBlank() && !filter.selectedSpace.equals("null", ignoreCase = true)) {
                queryBuilder.append(" AND spaces LIKE ?")
                args.add("%\"${filter.selectedSpace}\"%")
                if (!filter.selectedSubspace.isNullOrBlank() && !filter.selectedSubspace.equals("null", ignoreCase = true)) {
                    queryBuilder.append(" AND spaces LIKE ?")
                    args.add("%\"${filter.selectedSubspace}\"%")
                }
            }

            // Custom dateRangeStart / dateRangeEnd filter
            if (!filter.dateRangeStart.isNullOrBlank() && !filter.dateRangeEnd.isNullOrBlank()) {
                if (filter.dateRangeStart.startsWith("2000")) {
                    // Today & Due convention
                    queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) <= date('now', 'localtime')")
                } else {
                    val s = if (filter.dateRangeStart.length >= 10) filter.dateRangeStart.substring(0, 10) else filter.dateRangeStart
                    val e = if (filter.dateRangeEnd.length >= 10) filter.dateRangeEnd.substring(0, 10) else filter.dateRangeEnd
                    queryBuilder.append(" AND due IS NOT NULL AND due != '' AND substr(due, 1, 10) >= ? AND substr(due, 1, 10) <= ?")
                    args.add(s)
                    args.add(e)
                }
            }

            // filterType & filterVal logic (e.g. date / list / tag / space / priority)
            if (!filter.filterType.isNullOrBlank() && !filter.filterType.equals("null", ignoreCase = true) &&
                !filter.filterVal.isNullOrBlank() && !filter.filterVal.equals("null", ignoreCase = true)) {
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
                        if (!skipTag && filter.selectedTags.isEmpty()) {
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

        fun formatFilterPill(filter: WidgetTabFilter, viewMode: String? = null): String? {
            val filterLabel = when (filter.filterType?.lowercase()) {
                "space" -> if (!filter.filterVal.isNullOrBlank() && !filter.filterVal.equals("null", ignoreCase = true)) "Space: ${filter.filterVal}" else null
                "subspace" -> if (!filter.filterVal.isNullOrBlank() && !filter.filterVal.equals("null", ignoreCase = true)) filter.filterVal else null
                "tag" -> if (!filter.filterVal.isNullOrBlank() && !filter.filterVal.equals("null", ignoreCase = true)) "#${filter.filterVal}" else null
                "list" -> if (!filter.filterVal.isNullOrBlank() && !filter.filterVal.equals("null", ignoreCase = true)) "List: ${filter.filterVal}" else null
                "account" -> if (!filter.filterVal.isNullOrBlank() && !filter.filterVal.equals("null", ignoreCase = true)) "@${filter.filterVal}" else null
                "date" -> if (!filter.filterVal.isNullOrBlank() && !filter.filterVal.equals("null", ignoreCase = true)) "📅 ${filter.filterVal}" else null
                else -> if (!filter.selectedSpace.isNullOrBlank() && !filter.selectedSpace.equals("null", ignoreCase = true)) {
                    if (!filter.selectedSubspace.isNullOrBlank() && !filter.selectedSubspace.equals("null", ignoreCase = true)) {
                        "Space: ${filter.selectedSpace} › ${filter.selectedSubspace}"
                    } else {
                        "Space: ${filter.selectedSpace}"
                    }
                } else null
            }

            val sortLabel = when (filter.sortBy) {
                "due_asc" -> "Due ↑"
                "due_desc" -> "Due ↓"
                "modified" -> "Modified"
                "created" -> "Created"
                "title" -> "Title A-Z"
                else -> null
            }

            val pillParts = mutableListOf<String>()
            if (!filterLabel.isNullOrBlank()) pillParts.add(filterLabel)
            if (filter.selectedLists.isNotEmpty()) {
                val sLists = filter.selectedLists.toList()
                pillParts.add(if (sLists.size == 1) "List: ${sLists[0]}" else "${sLists.size} lists")
            }
            if (filter.selectedTags.isNotEmpty()) {
                val sTags = filter.selectedTags.toList()
                pillParts.add(if (sTags.size == 1) "#${sTags[0]}" else "${sTags.size} tags")
            }
            if (!filter.selectedPriority.isNullOrBlank() && !filter.selectedPriority.equals("null", ignoreCase = true)) {
                pillParts.add("Priority: ${filter.selectedPriority}")
            }
            if (filter.hideRecurring) pillParts.add("No Recurring")
            if (filter.hiddenLists.isNotEmpty()) {
                val hLists = filter.hiddenLists.toList()
                pillParts.add(if (hLists.size == 1) "Hide: ${hLists[0]}" else "Hide: ${hLists.size} lists")
            }
            if (filter.hiddenTags.isNotEmpty()) {
                val hTags = filter.hiddenTags.toList()
                pillParts.add(if (hTags.size == 1) "Hide: #${hTags[0]}" else "Hide: ${hTags.size} tags")
            }
            if (filter.statusFilter == "completed") {
                pillParts.add("Completed")
            } else if (filter.statusFilter == "all") {
                pillParts.add("All Statuses")
            }
            if (!sortLabel.isNullOrBlank()) pillParts.add("Sort: $sortLabel")
            if (viewMode == "compact") pillParts.add("1-Line")
            if (viewMode == "two_column") pillParts.add("2-Col")
            if (viewMode == "two_column_compact") pillParts.add("2-Col Compact")

            return if (pillParts.isNotEmpty()) pillParts.joinToString(" • ") else null
        }
    }
}
