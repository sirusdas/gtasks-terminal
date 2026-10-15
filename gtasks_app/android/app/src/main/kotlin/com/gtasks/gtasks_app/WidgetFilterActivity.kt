package com.gtasks.gtasks_app

import android.app.Activity
import android.appwidget.AppWidgetManager
import android.content.Context
import android.database.sqlite.SQLiteDatabase
import android.os.Bundle
import android.text.Editable
import android.text.TextWatcher
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import android.widget.Button
import android.widget.EditText
import android.widget.ImageView
import android.widget.ListView
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject

class WidgetFilterActivity : Activity() {

    data class FilterOption(
        val name: String,
        val count: Int,
        var isChecked: Boolean = false,
        var extra: String? = null
    )

    private var appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID
    private var filterType: String = "space"
    private val allOptions = mutableListOf<FilterOption>()
    private val filteredOptions = mutableListOf<FilterOption>()
    private lateinit var adapter: FilterAdapter

    private lateinit var tvTitle: TextView
    private lateinit var tvSubtitle: TextView
    private lateinit var ivIcon: ImageView
    private lateinit var btnClose: ImageView
    private lateinit var etSearch: EditText
    private lateinit var tvAll: TextView
    private lateinit var lvOptions: ListView
    private lateinit var btnDone: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_widget_filter)

        appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
        filterType = intent.getStringExtra("filter_type") ?: "space"

        tvTitle = findViewById(R.id.tv_filter_title)
        tvSubtitle = findViewById(R.id.tv_filter_subtitle)
        ivIcon = findViewById(R.id.iv_filter_icon)
        btnClose = findViewById(R.id.btn_filter_close)
        etSearch = findViewById(R.id.et_filter_search)
        tvAll = findViewById(R.id.tv_filter_all)
        lvOptions = findViewById(R.id.lv_filter_options)
        btnDone = findViewById(R.id.btn_filter_done)

        adapter = FilterAdapter(this, filteredOptions) { filterType }
        lvOptions.adapter = adapter

        etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                applySearchFilter(s.toString())
            }
            override fun afterTextChanged(s: Editable?) {}
        })

        // Clear filter / reset options
        tvAll.setOnClickListener {
            handleClearFilter()
        }

        // Done button (for multi-select or overview)
        btnDone.setOnClickListener {
            if (filterType == "hide_list" || filterType == "hide_tag") {
                filterType = "hide"
                setupForFilterType()
            } else {
                finish()
            }
        }

        // Close button
        btnClose.setOnClickListener {
            if (filterType == "hide_list" || filterType == "hide_tag") {
                filterType = "hide"
                setupForFilterType()
            } else {
                finish()
            }
        }

        // Option click listener
        lvOptions.setOnItemClickListener { _, _, position, _ ->
            handleItemClick(position)
        }

        setupForFilterType()
    }

    override fun onBackPressed() {
        if (filterType == "hide_list" || filterType == "hide_tag") {
            filterType = "hide"
            setupForFilterType()
            return
        }
        super.onBackPressed()
    }

    private fun setupForFilterType() {
        etSearch.setText("")
        val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)

        when (filterType) {
            "list" -> {
                tvTitle.text = "Filter by List"
                tvSubtitle.visibility = View.GONE
                ivIcon.setImageResource(R.drawable.ic_widget_list)
                tvAll.text = "★ All Lists (Clear Filter)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.VISIBLE
            }
            "tag" -> {
                tvTitle.text = "Filter by Tag"
                tvSubtitle.visibility = View.GONE
                ivIcon.setImageResource(R.drawable.ic_widget_tag)
                tvAll.text = "★ All Tags (Clear Filter)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.VISIBLE
            }
            "space" -> {
                tvTitle.text = "Filter by Workspace"
                tvSubtitle.visibility = View.GONE
                ivIcon.setImageResource(R.drawable.ic_widget_space)
                tvAll.text = "★ All Workspaces (Clear Filter)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.VISIBLE
            }
            "subspace" -> {
                tvTitle.text = "Filter by Sub-workspace"
                tvSubtitle.visibility = View.GONE
                ivIcon.setImageResource(R.drawable.ic_widget_subspace)
                tvAll.text = "★ All Sub-workspaces (Clear Filter)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.VISIBLE
            }
            "account" -> {
                tvTitle.text = "Filter by Account"
                tvSubtitle.visibility = View.GONE
                ivIcon.setImageResource(R.drawable.ic_widget_account)
                tvAll.text = "★ All Accounts (Clear Filter)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.VISIBLE
            }
            "date" -> {
                tvTitle.text = "Filter by Date Window"
                tvSubtitle.visibility = View.GONE
                ivIcon.setImageResource(R.drawable.ic_widget_calendar)
                tvAll.text = "★ All Dates (Clear Filter)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.GONE
            }
            "sort" -> {
                tvTitle.text = "Sort Tasks By"
                tvSubtitle.visibility = View.GONE
                ivIcon.setImageResource(R.drawable.ic_widget_sort)
                tvAll.text = "★ Default Priority (Reset Sort)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.GONE
            }
            "recurring" -> {
                tvTitle.text = "Recurring Tasks"
                tvSubtitle.text = "Include or exclude repeating routines"
                tvSubtitle.visibility = View.VISIBLE
                ivIcon.setImageResource(R.drawable.ic_widget_recurring)
                tvAll.text = "★ Show All (Include Recurring)"
                tvAll.visibility = View.VISIBLE
                btnDone.visibility = View.GONE
                etSearch.visibility = View.GONE
            }
            "hide" -> {
                tvTitle.text = "Exclusions & Hidden Filters"
                tvSubtitle.text = "Exclude routines, specific lists or tags from widget"
                tvSubtitle.visibility = View.VISIBLE
                ivIcon.setImageResource(R.drawable.ic_widget_visibility_off)
                tvAll.text = "★ Reset All Exclusions"
                tvAll.visibility = View.VISIBLE
                btnDone.text = "Done"
                btnDone.visibility = View.VISIBLE
                etSearch.visibility = View.GONE
            }
            "hide_list" -> {
                tvTitle.text = "Hide Specific Lists"
                tvSubtitle.text = "Select lists to exclude from widget view"
                tvSubtitle.visibility = View.VISIBLE
                ivIcon.setImageResource(R.drawable.ic_widget_visibility_off)
                tvAll.text = "★ Show All Lists (Clear Hidden Lists)"
                tvAll.visibility = View.VISIBLE
                btnDone.text = "Apply & Return"
                btnDone.visibility = View.VISIBLE
                etSearch.visibility = View.VISIBLE
            }
            "hide_tag" -> {
                tvTitle.text = "Hide Specific Tags"
                tvSubtitle.text = "Select tags to exclude from widget view"
                tvSubtitle.visibility = View.VISIBLE
                ivIcon.setImageResource(R.drawable.ic_widget_visibility_off)
                tvAll.text = "★ Show All Tags (Clear Hidden Tags)"
                tvAll.visibility = View.VISIBLE
                btnDone.text = "Apply & Return"
                btnDone.visibility = View.VISIBLE
                etSearch.visibility = View.VISIBLE
            }
        }

        loadFilterOptionsFromDb()
        applySearchFilter(etSearch.text.toString())
    }

    private fun applySearchFilter(query: String) {
        val q = query.trim().lowercase()
        filteredOptions.clear()
        if (q.isEmpty()) {
            filteredOptions.addAll(allOptions)
        } else {
            filteredOptions.addAll(allOptions.filter { it.name.lowercase().contains(q) })
        }
        adapter.notifyDataSetChanged()
    }

    private fun handleClearFilter() {
        val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)

        when (filterType) {
            "recurring" -> {
                prefs.edit().remove("hide_recurring_$appWidgetId").apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                finish()
            }
            "hide" -> {
                prefs.edit()
                    .remove("hide_recurring_$appWidgetId")
                    .remove("hidden_lists_$appWidgetId")
                    .remove("hidden_tags_$appWidgetId")
                    .apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                setupForFilterType()
            }
            "hide_list" -> {
                prefs.edit().remove("hidden_lists_$appWidgetId").apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                setupForFilterType()
            }
            "hide_tag" -> {
                prefs.edit().remove("hidden_tags_$appWidgetId").apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                setupForFilterType()
            }
            "sort" -> {
                prefs.edit().remove("sort_by_$appWidgetId").apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                finish()
            }
            else -> {
                prefs.edit()
                    .remove("filter_type_$appWidgetId")
                    .remove("filter_val_$appWidgetId")
                    .apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                finish()
            }
        }
    }

    private fun handleItemClick(position: Int) {
        if (position < 0 || position >= filteredOptions.size) return
        val selected = filteredOptions[position]
        val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)

        when (filterType) {
            "recurring" -> {
                val hideRecurring = selected.name.startsWith("Hide")
                prefs.edit().putBoolean("hide_recurring_$appWidgetId", hideRecurring).apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                finish()
            }
            "hide" -> {
                when (position) {
                    0 -> {
                        // Toggle recurring
                        val current = prefs.getBoolean("hide_recurring_$appWidgetId", false)
                        prefs.edit().putBoolean("hide_recurring_$appWidgetId", !current).apply()
                        GTasksWidgetProvider.updateAllWidgets(applicationContext)
                        setupForFilterType()
                    }
                    1 -> {
                        // Go to Hide Lists
                        filterType = "hide_list"
                        setupForFilterType()
                    }
                    2 -> {
                        // Go to Hide Tags
                        filterType = "hide_tag"
                        setupForFilterType()
                    }
                }
            }
            "hide_list" -> {
                val hiddenLists = getHiddenLists()
                if (hiddenLists.contains(selected.name)) {
                    hiddenLists.remove(selected.name)
                    selected.isChecked = false
                } else {
                    hiddenLists.add(selected.name)
                    selected.isChecked = true
                }
                saveHiddenLists(hiddenLists)
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                adapter.notifyDataSetChanged()
            }
            "hide_tag" -> {
                val hiddenTags = getHiddenTags()
                if (hiddenTags.contains(selected.name)) {
                    hiddenTags.remove(selected.name)
                    selected.isChecked = false
                } else {
                    hiddenTags.add(selected.name)
                    selected.isChecked = true
                }
                saveHiddenTags(hiddenTags)
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                adapter.notifyDataSetChanged()
            }
            "sort" -> {
                val sortKey = when (selected.name) {
                    "Due Date (Earliest first)" -> "due_asc"
                    "Due Date (Latest first)" -> "due_desc"
                    "Modified Date (Recent first)" -> "modified"
                    "Created Date (Recent first)" -> "created"
                    "Title (A to Z)" -> "title"
                    else -> "priority"
                }
                prefs.edit().putString("sort_by_$appWidgetId", sortKey).apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                finish()
            }
            else -> {
                prefs.edit()
                    .putString("filter_type_$appWidgetId", filterType)
                    .putString("filter_val_$appWidgetId", selected.name)
                    .apply()
                GTasksWidgetProvider.updateAllWidgets(applicationContext)
                finish()
            }
        }
    }

    private fun getHiddenLists(): MutableSet<String> {
        val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
        val json = prefs.getString("hidden_lists_$appWidgetId", null) ?: return mutableSetOf()
        val set = mutableSetOf<String>()
        try {
            val arr = JSONArray(json)
            for (i in 0 until arr.length()) {
                val s = arr.getString(i).trim()
                if (s.isNotEmpty()) set.add(s)
            }
        } catch (_: Exception) {}
        return set
    }

    private fun saveHiddenLists(set: Set<String>) {
        val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
        val arr = JSONArray()
        for (s in set) {
            arr.put(s)
        }
        prefs.edit().putString("hidden_lists_$appWidgetId", arr.toString()).apply()
    }

    private fun getHiddenTags(): MutableSet<String> {
        val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
        val json = prefs.getString("hidden_tags_$appWidgetId", null) ?: return mutableSetOf()
        val set = mutableSetOf<String>()
        try {
            val arr = JSONArray(json)
            for (i in 0 until arr.length()) {
                val s = arr.getString(i).trim()
                if (s.isNotEmpty()) set.add(s)
            }
        } catch (_: Exception) {}
        return set
    }

    private fun saveHiddenTags(set: Set<String>) {
        val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
        val arr = JSONArray()
        for (s in set) {
            arr.put(s)
        }
        prefs.edit().putString("hidden_tags_$appWidgetId", arr.toString()).apply()
    }

    private fun loadFilterOptionsFromDb() {
        allOptions.clear()
        try {
            val dbFile = getDatabasePath("gtasks_local.db")
            if (!dbFile.exists()) return

            val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
            val hideRecurring = prefs.getBoolean("hide_recurring_$appWidgetId", false)

            SQLiteDatabase.openDatabase(dbFile.absolutePath, null, SQLiteDatabase.OPEN_READONLY).use { db ->
                val check = db.rawQuery("SELECT name FROM sqlite_master WHERE type='table' AND name='tasks'", null)
                val exists = check.use { it.moveToFirst() }
                if (!exists) return

                when (filterType) {
                    "list" -> {
                        val cursor = db.rawQuery(
                            """
                            SELECT list_title, COUNT(*) FROM tasks 
                            WHERE status != 'completed' AND sync_status != 'pending_delete' 
                              AND list_title IS NOT NULL AND list_title != '' 
                            GROUP BY list_title ORDER BY COUNT(*) DESC
                            """.trimIndent(),
                            null
                        )
                        cursor.use {
                            while (it.moveToNext()) {
                                allOptions.add(FilterOption(it.getString(0), it.getInt(1)))
                            }
                        }
                    }
                    "account" -> {
                        val cursor = db.rawQuery(
                            """
                            SELECT account, COUNT(*) FROM tasks 
                            WHERE status != 'completed' AND sync_status != 'pending_delete' 
                              AND account IS NOT NULL AND account != '' 
                            GROUP BY account ORDER BY COUNT(*) DESC
                            """.trimIndent(),
                            null
                        )
                        cursor.use {
                            while (it.moveToNext()) {
                                allOptions.add(FilterOption(it.getString(0), it.getInt(1)))
                            }
                        }
                    }
                    "tag" -> {
                        val cursor = db.rawQuery(
                            "SELECT tags FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete' AND tags IS NOT NULL AND tags != '' AND tags != '[]'",
                            null
                        )
                        val counts = mutableMapOf<String, Int>()
                        cursor.use {
                            while (it.moveToNext()) {
                                try {
                                    val arr = JSONArray(it.getString(0))
                                    for (i in 0 until arr.length()) {
                                        val tag = arr.getString(i).trim()
                                        if (tag.isNotEmpty()) {
                                            counts[tag] = (counts[tag] ?: 0) + 1
                                        }
                                    }
                                } catch (_: Exception) {}
                            }
                        }
                        counts.entries.sortedByDescending { it.value }.forEach {
                            allOptions.add(FilterOption(it.key, it.value))
                        }
                    }
                    "space" -> {
                        val cursor = db.rawQuery(
                            "SELECT spaces FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete' AND spaces IS NOT NULL AND spaces != '' AND spaces != '{}'",
                            null
                        )
                        val counts = mutableMapOf<String, Int>()
                        cursor.use {
                            while (it.moveToNext()) {
                                try {
                                    val obj = JSONObject(it.getString(0))
                                    val keys = obj.keys()
                                    while (keys.hasNext()) {
                                        val space = keys.next().trim()
                                        if (space.isNotEmpty()) {
                                            counts[space] = (counts[space] ?: 0) + 1
                                        }
                                    }
                                } catch (_: Exception) {}
                            }
                        }
                        counts.entries.sortedByDescending { it.value }.forEach {
                            allOptions.add(FilterOption(it.key, it.value))
                        }
                    }
                    "subspace" -> {
                        val cursor = db.rawQuery(
                            "SELECT spaces FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete' AND spaces IS NOT NULL AND spaces != '' AND spaces != '{}'",
                            null
                        )
                        val counts = mutableMapOf<String, Int>()
                        cursor.use {
                            while (it.moveToNext()) {
                                try {
                                    val obj = JSONObject(it.getString(0))
                                    val keys = obj.keys()
                                    while (keys.hasNext()) {
                                        val space = keys.next().trim()
                                        val arr = obj.optJSONArray(space)
                                        if (arr != null) {
                                            for (i in 0 until arr.length()) {
                                                val sub = arr.getString(i).trim()
                                                if (sub.isNotEmpty()) {
                                                    val label = "$space › $sub"
                                                    counts[label] = (counts[label] ?: 0) + 1
                                                }
                                            }
                                        }
                                    }
                                } catch (_: Exception) {}
                            }
                        }
                        counts.entries.sortedByDescending { it.value }.forEach {
                            allOptions.add(FilterOption(it.key, it.value))
                        }
                    }
                    "date" -> {
                        fun countFor(whereClause: String): Int {
                            val c = db.rawQuery(
                                "SELECT COUNT(*) FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete' AND $whereClause",
                                null
                            )
                            return c.use { if (it.moveToFirst()) it.getInt(0) else 0 }
                        }

                        allOptions.add(FilterOption("Today", countFor("substr(due, 1, 10) = date('now', 'localtime')")))
                        allOptions.add(FilterOption("Tomorrow", countFor("substr(due, 1, 10) = date('now', 'localtime', '+1 day')")))
                        allOptions.add(FilterOption("Overdue", countFor("due IS NOT NULL AND due != '' AND substr(due, 1, 10) < date('now', 'localtime')")))
                        allOptions.add(FilterOption("Next 7 Days", countFor("due IS NOT NULL AND due != '' AND substr(due, 1, 10) >= date('now', 'localtime') AND substr(due, 1, 10) <= date('now', 'localtime', '+7 days')")))
                        allOptions.add(FilterOption("Upcoming", countFor("due IS NOT NULL AND due != '' AND substr(due, 1, 10) >= date('now', 'localtime')")))
                        allOptions.add(FilterOption("No Due Date", countFor("due IS NULL OR due = ''")))
                    }
                    "sort" -> {
                        val totalCursor = db.rawQuery(
                            "SELECT COUNT(*) FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete'",
                            null
                        )
                        val total = totalCursor.use { if (it.moveToFirst()) it.getInt(0) else 0 }

                        allOptions.add(FilterOption("Priority (Critical to Low)", total))
                        allOptions.add(FilterOption("Due Date (Earliest first)", total))
                        allOptions.add(FilterOption("Due Date (Latest first)", total))
                        allOptions.add(FilterOption("Modified Date (Recent first)", total))
                        allOptions.add(FilterOption("Created Date (Recent first)", total))
                        allOptions.add(FilterOption("Title (A to Z)", total))
                    }
                    "recurring" -> {
                        val totalCursor = db.rawQuery(
                            "SELECT COUNT(*) FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete'",
                            null
                        )
                        val total = totalCursor.use { if (it.moveToFirst()) it.getInt(0) else 0 }

                        val nonRecurringCursor = db.rawQuery(
                            """
                            SELECT COUNT(*) FROM tasks 
                            WHERE status != 'completed' AND sync_status != 'pending_delete'
                              AND (is_recurring = 0 OR is_recurring IS NULL) 
                              AND (recurrence_type IS NULL OR recurrence_type = '')
                            """.trimIndent(),
                            null
                        )
                        val nonRecurring = nonRecurringCursor.use { if (it.moveToFirst()) it.getInt(0) else 0 }
                        val recurring = total - nonRecurring

                        allOptions.add(FilterOption("Show All Tasks (Include Recurring)", total, isChecked = !hideRecurring))
                        allOptions.add(FilterOption("Hide Recurring Tasks (Exclude Routines)", nonRecurring, isChecked = hideRecurring, extra = "Excludes $recurring tasks"))
                    }
                    "hide" -> {
                        val recurringCursor = db.rawQuery(
                            """
                            SELECT COUNT(*) FROM tasks 
                            WHERE status != 'completed' AND sync_status != 'pending_delete'
                              AND (is_recurring = 1 OR (recurrence_type IS NOT NULL AND recurrence_type != ''))
                            """.trimIndent(),
                            null
                        )
                        val recurring = recurringCursor.use { if (it.moveToFirst()) it.getInt(0) else 0 }
                        val hiddenLists = getHiddenLists()
                        val hiddenTags = getHiddenTags()

                        allOptions.add(
                            FilterOption(
                                "Hide Recurring Tasks",
                                recurring,
                                isChecked = hideRecurring,
                                extra = if (hideRecurring) "ON (Hidden)" else "OFF (Visible)"
                            )
                        )
                        allOptions.add(
                            FilterOption(
                                "Hide Specific Lists (Exclude)...",
                                hiddenLists.size,
                                extra = if (hiddenLists.isEmpty()) "None hidden" else "${hiddenLists.size} lists hidden"
                            )
                        )
                        allOptions.add(
                            FilterOption(
                                "Hide Specific Tags (Exclude)...",
                                hiddenTags.size,
                                extra = if (hiddenTags.isEmpty()) "None hidden" else "${hiddenTags.size} tags hidden"
                            )
                        )
                    }
                    "hide_list" -> {
                        val hiddenLists = getHiddenLists()
                        val cursor = db.rawQuery(
                            """
                            SELECT list_title, COUNT(*) FROM tasks 
                            WHERE status != 'completed' AND sync_status != 'pending_delete' 
                              AND list_title IS NOT NULL AND list_title != '' 
                            GROUP BY list_title ORDER BY COUNT(*) DESC
                            """.trimIndent(),
                            null
                        )
                        cursor.use {
                            while (it.moveToNext()) {
                                val listName = it.getString(0)
                                val count = it.getInt(1)
                                allOptions.add(
                                    FilterOption(
                                        name = listName,
                                        count = count,
                                        isChecked = hiddenLists.contains(listName),
                                        extra = if (hiddenLists.contains(listName)) "Hidden" else null
                                    )
                                )
                            }
                        }
                    }
                    "hide_tag" -> {
                        val hiddenTags = getHiddenTags()
                        val cursor = db.rawQuery(
                            "SELECT tags FROM tasks WHERE status != 'completed' AND sync_status != 'pending_delete' AND tags IS NOT NULL AND tags != '' AND tags != '[]'",
                            null
                        )
                        val counts = mutableMapOf<String, Int>()
                        cursor.use {
                            while (it.moveToNext()) {
                                try {
                                    val arr = JSONArray(it.getString(0))
                                    for (i in 0 until arr.length()) {
                                        val tag = arr.getString(i).trim()
                                        if (tag.isNotEmpty()) {
                                            counts[tag] = (counts[tag] ?: 0) + 1
                                        }
                                    }
                                } catch (_: Exception) {}
                            }
                        }
                        counts.entries.sortedByDescending { it.value }.forEach {
                            allOptions.add(
                                FilterOption(
                                    name = it.key,
                                    count = it.value,
                                    isChecked = hiddenTags.contains(it.key),
                                    extra = if (hiddenTags.contains(it.key)) "Hidden" else null
                                )
                            )
                        }
                    }
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private class FilterAdapter(
        private val context: Context,
        private val items: List<FilterOption>,
        private val filterTypeProvider: () -> String
    ) : BaseAdapter() {
        override fun getCount(): Int = items.size
        override fun getItem(position: Int): Any = items[position]
        override fun getItemId(position: Int): Long = position.toLong()

        override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
            val view = convertView ?: LayoutInflater.from(context).inflate(R.layout.item_filter_row, parent, false)
            val item = items[position]
            val filterType = filterTypeProvider()

            val ivCheck = view.findViewById<ImageView>(R.id.iv_filter_item_check)
            val tvName = view.findViewById<TextView>(R.id.tv_filter_item_name)
            val tvCount = view.findViewById<TextView>(R.id.tv_filter_item_count)

            tvName.text = item.name
            tvCount.text = item.extra ?: "${item.count} tasks"

            when (filterType) {
                "hide_list", "hide_tag" -> {
                    ivCheck.visibility = View.VISIBLE
                    ivCheck.setImageResource(if (item.isChecked) R.drawable.ic_widget_checked else R.drawable.ic_widget_unchecked)
                }
                "hide" -> {
                    if (position == 0) {
                        ivCheck.visibility = View.VISIBLE
                        ivCheck.setImageResource(if (item.isChecked) R.drawable.ic_widget_checked else R.drawable.ic_widget_unchecked)
                    } else {
                        ivCheck.visibility = View.GONE
                    }
                }
                "recurring" -> {
                    ivCheck.visibility = View.VISIBLE
                    ivCheck.setImageResource(if (item.isChecked) R.drawable.ic_widget_checked else R.drawable.ic_widget_unchecked)
                }
                else -> {
                    ivCheck.visibility = View.GONE
                }
            }

            return view
        }
    }
}
