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
import android.widget.EditText
import android.widget.ImageView
import android.widget.ListView
import android.widget.TextView
import org.json.JSONArray
import org.json.JSONObject

class WidgetFilterActivity : Activity() {

    data class FilterOption(val name: String, val count: Int)

    private var appWidgetId: Int = AppWidgetManager.INVALID_APPWIDGET_ID
    private var filterType: String = "space"
    private val allOptions = mutableListOf<FilterOption>()
    private val filteredOptions = mutableListOf<FilterOption>()
    private lateinit var adapter: FilterAdapter

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_widget_filter)

        appWidgetId = intent.getIntExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, AppWidgetManager.INVALID_APPWIDGET_ID)
        filterType = intent.getStringExtra("filter_type") ?: "space"

        val tvTitle = findViewById<TextView>(R.id.tv_filter_title)
        val ivIcon = findViewById<ImageView>(R.id.iv_filter_icon)
        val btnClose = findViewById<ImageView>(R.id.btn_filter_close)
        val etSearch = findViewById<EditText>(R.id.et_filter_search)
        val tvAll = findViewById<TextView>(R.id.tv_filter_all)
        val lvOptions = findViewById<ListView>(R.id.lv_filter_options)

        // Set title and icon based on filter type
        when (filterType) {
            "list" -> {
                tvTitle.text = "Filter by List"
                ivIcon.setImageResource(R.drawable.ic_widget_list)
            }
            "tag" -> {
                tvTitle.text = "Filter by Tag"
                ivIcon.setImageResource(R.drawable.ic_widget_tag)
            }
            "space" -> {
                tvTitle.text = "Filter by Workspace"
                ivIcon.setImageResource(R.drawable.ic_widget_space)
            }
            "subspace" -> {
                tvTitle.text = "Filter by Sub-workspace"
                ivIcon.setImageResource(R.drawable.ic_widget_subspace)
            }
            "account" -> {
                tvTitle.text = "Filter by Account"
                ivIcon.setImageResource(R.drawable.ic_widget_account)
            }
            "date" -> {
                tvTitle.text = "Filter by Date Window"
                ivIcon.setImageResource(R.drawable.ic_widget_calendar)
            }
            "sort" -> {
                tvTitle.text = "Sort Tasks By"
                ivIcon.setImageResource(R.drawable.ic_widget_sort)
            }
            else -> {
                tvTitle.text = "Filter Tasks"
            }
        }

        loadFilterOptionsFromDb()

        filteredOptions.addAll(allOptions)
        adapter = FilterAdapter(this, filteredOptions)
        lvOptions.adapter = adapter

        etSearch.addTextChangedListener(object : TextWatcher {
            override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) {}
            override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) {
                val q = s.toString().trim().lowercase()
                filteredOptions.clear()
                if (q.isEmpty()) {
                    filteredOptions.addAll(allOptions)
                } else {
                    filteredOptions.addAll(allOptions.filter { it.name.lowercase().contains(q) })
                }
                adapter.notifyDataSetChanged()
            }
            override fun afterTextChanged(s: Editable?) {}
        })

        // Clear filter / reset sort
        tvAll.setOnClickListener {
            val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)
            prefs.edit()
                .remove("filter_type_$appWidgetId")
                .remove("filter_val_$appWidgetId")
                .remove("sort_by_$appWidgetId")
                .apply()
            GTasksWidgetProvider.updateAllWidgets(applicationContext)
            finish()
        }

        // Select specific filter or sort
        lvOptions.setOnItemClickListener { _, _, position, _ ->
            val selected = filteredOptions[position]
            val prefs = getSharedPreferences("gtasks_widget_prefs", Context.MODE_PRIVATE)

            if (filterType == "sort") {
                val sortKey = when (selected.name) {
                    "Due Date (Earliest first)" -> "due_asc"
                    "Due Date (Latest first)" -> "due_desc"
                    "Modified Date (Recent first)" -> "modified"
                    "Created Date (Recent first)" -> "created"
                    "Title (A to Z)" -> "title"
                    else -> "priority"
                }
                prefs.edit()
                    .putString("sort_by_$appWidgetId", sortKey)
                    .apply()
            } else {
                prefs.edit()
                    .putString("filter_type_$appWidgetId", filterType)
                    .putString("filter_val_$appWidgetId", selected.name)
                    .apply()
            }

            GTasksWidgetProvider.updateAllWidgets(applicationContext)
            finish()
        }

        btnClose.setOnClickListener { finish() }
    }

    private fun loadFilterOptionsFromDb() {
        allOptions.clear()
        try {
            val dbFile = getDatabasePath("gtasks_local.db")
            if (!dbFile.exists()) return

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
                }
            }
        } catch (e: Exception) {
            e.printStackTrace()
        }
    }

    private class FilterAdapter(private val context: Context, private val items: List<FilterOption>) : BaseAdapter() {
        override fun getCount(): Int = items.size
        override fun getItem(position: Int): Any = items[position]
        override fun getItemId(position: Int): Long = position.toLong()

        override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
            val view = convertView ?: LayoutInflater.from(context).inflate(R.layout.item_filter_row, parent, false)
            val item = items[position]

            val tvName = view.findViewById<TextView>(R.id.tv_filter_item_name)
            val tvCount = view.findViewById<TextView>(R.id.tv_filter_item_count)

            tvName.text = item.name
            tvCount.text = "${item.count} tasks"

            return view
        }
    }
}
