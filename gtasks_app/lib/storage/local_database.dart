import 'dart:convert';
import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart' as p;
import '../models/task_item.dart';

class LocalDatabase {
  static final LocalDatabase instance = LocalDatabase._init();
  static Database? _database;

  LocalDatabase._init();

  Future<Database> get database async {
    if (_database != null) return _database!;
    _database = await _initDB('gtasks_local.db');
    return _database!;
  }

  Future<Database> _initDB(String filePath) async {
    final dbPath = await getDatabasesPath();
    final path = p.join(dbPath, filePath);

    return await openDatabase(
      path,
      version: 1,
      onCreate: _createDB,
    );
  }

  Future<void> _createDB(Database db, int version) async {
    // Tasks table matching both Python CLI and Google Tasks data attributes
    await db.execute('''
      CREATE TABLE tasks (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        due TEXT,
        priority TEXT,
        status TEXT NOT NULL DEFAULT 'pending',
        tags TEXT, -- JSON array of tags
        list_id TEXT,
        list_title TEXT,
        account TEXT NOT NULL DEFAULT 'default',
        created_at TEXT,
        modified_at TEXT,
        completed_at TEXT,
        is_recurring INTEGER DEFAULT 0,
        recurrence_type TEXT,
        sync_status TEXT DEFAULT 'synced' -- 'synced', 'pending_insert', 'pending_update', 'pending_delete'
      )
    ''');

    // Task lists table
    await db.execute('''
      CREATE TABLE task_lists (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        account TEXT NOT NULL DEFAULT 'default',
        updated_at TEXT
      )
    ''');

    await db.execute('CREATE INDEX idx_tasks_status ON tasks(status);');
    await db.execute('CREATE INDEX idx_tasks_account ON tasks(account);');
    await db.execute('CREATE INDEX idx_tasks_list_id ON tasks(list_id);');
  }

  // ---------------------------------------------------------------------------
  // CRUD Operations
  // ---------------------------------------------------------------------------

  Future<List<TaskItem>> getAllTasks({String? account, String? status}) async {
    final db = await database;
    String whereClause = '';
    List<dynamic> whereArgs = [];

    if (account != null && account != 'all') {
      whereClause += 'account = ?';
      whereArgs.add(account);
    }

    if (status != null && status != 'all') {
      if (whereClause.isNotEmpty) whereClause += ' AND ';
      whereClause += 'status = ?';
      whereArgs.add(status);
    } else if (status != 'all') {
      if (whereClause.isNotEmpty) whereClause += ' AND ';
      whereClause += "status != 'deleted'";
    }

    final result = await db.query(
      'tasks',
      where: whereClause.isNotEmpty ? whereClause : null,
      whereArgs: whereArgs.isNotEmpty ? whereArgs : null,
      orderBy: 'modified_at DESC',
    );

    return result.map((row) => _fromDbRow(row)).toList();
  }

  TaskItem fromDbRow(Map<String, dynamic> row) => _fromDbRow(row);

  Future<TaskItem?> getTaskById(String id) async {
    final db = await database;
    final result = await db.query(
      'tasks',
      where: 'id = ?',
      whereArgs: [id],
      limit: 1,
    );
    if (result.isEmpty) return null;
    return _fromDbRow(result.first);
  }

  Future<int> upsertTask(TaskItem task, {String syncStatus = 'synced'}) async {
    final db = await database;
    final row = _toDbRow(task, syncStatus: syncStatus);
    return await db.insert(
      'tasks',
      row,
      conflictAlgorithm: ConflictAlgorithm.replace,
    );
  }

  Future<void> upsertTasks(List<TaskItem> tasks, {String syncStatus = 'synced'}) async {
    final db = await database;
    final batch = db.batch();
    for (final task in tasks) {
      batch.insert(
        'tasks',
        _toDbRow(task, syncStatus: syncStatus),
        conflictAlgorithm: ConflictAlgorithm.replace,
      );
    }
    await batch.commit(noResult: true);
  }

  Future<int> markTaskCompleted(String id) async {
    final db = await database;
    return await db.update(
      'tasks',
      {
        'status': 'completed',
        'completed_at': DateTime.now().toUtc().toIso8601String(),
        'modified_at': DateTime.now().toUtc().toIso8601String(),
        'sync_status': 'pending_update',
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> markTaskPendingDelete(String id) async {
    final db = await database;
    return await db.update(
      'tasks',
      {
        'status': 'deleted',
        'sync_status': 'pending_delete',
        'modified_at': DateTime.now().toUtc().toIso8601String(),
      },
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> markTaskSynced(String id) async {
    final db = await database;
    return await db.update(
      'tasks',
      {'sync_status': 'synced'},
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<List<Map<String, dynamic>>> getPendingSyncRows({String? account}) async {
    final db = await database;
    if (account != null && account != 'all') {
      return await db.query(
        'tasks',
        where: "sync_status != 'synced' AND account = ?",
        whereArgs: [account],
      );
    }
    return await db.query(
      'tasks',
      where: "sync_status != 'synced'",
    );
  }

  Future<int> deleteTask(String id) async {
    final db = await database;
    return await db.delete(
      'tasks',
      where: 'id = ?',
      whereArgs: [id],
    );
  }

  Future<int> clearAllTasks({String? account}) async {
    final db = await database;
    if (account != null && account != 'all') {
      return await db.delete('tasks', where: 'account = ?', whereArgs: [account]);
    }
    return await db.delete('tasks');
  }

  // ---------------------------------------------------------------------------
  // Lists & Tags Aggregations (Pending Only)
  // ---------------------------------------------------------------------------

  Future<Map<String, int>> getPendingListsWithCounts({String? account}) async {
    final tasks = await getAllTasks(account: account, status: 'pending');
    final Map<String, int> counts = {};
    for (final t in tasks) {
      final list = (t.listTitle != null && t.listTitle!.isNotEmpty)
          ? t.listTitle!
          : 'Default List';
      counts[list] = (counts[list] ?? 0) + 1;
    }
    return counts;
  }

  Future<Map<String, int>> getPendingTagsWithCounts({String? account}) async {
    final tasks = await getAllTasks(account: account, status: 'pending');
    final Map<String, int> counts = {};
    for (final t in tasks) {
      for (final tag in t.allTags) {
        if (tag.trim().isNotEmpty) {
          counts[tag] = (counts[tag] ?? 0) + 1;
        }
      }
    }
    return counts;
  }

  Future<int> getPendingCount({String? account}) async {
    final db = await database;
    String sql = "SELECT COUNT(*) FROM tasks WHERE status != 'completed'";
    List<dynamic> args = [];
    if (account != null && account != 'all') {
      sql += " AND account = ?";
      args.add(account);
    }
    final res = await db.rawQuery(sql, args);
    return Sqflite.firstIntValue(res) ?? 0;
  }

  // ---------------------------------------------------------------------------
  // Helper Serialization
  // ---------------------------------------------------------------------------

  TaskItem _fromDbRow(Map<String, dynamic> row) {
    List<String> parsedTags = [];
    if (row['tags'] != null && row['tags'].toString().isNotEmpty) {
      try {
        final decoded = jsonDecode(row['tags'].toString());
        if (decoded is List) {
          parsedTags = decoded.map((e) => e.toString()).toList();
        }
      } catch (_) {}
    }

    return TaskItem(
      id: row['id']?.toString() ?? '',
      title: row['title']?.toString() ?? 'Untitled',
      description: row['description']?.toString() ?? '',
      status: row['status']?.toString() ?? 'pending',
      due: row['due']?.toString(),
      listId: row['list_id']?.toString(),
      listTitle: row['list_title']?.toString(),
      account: row['account']?.toString() ?? 'default',
      tags: parsedTags,
      calculatedPriority: row['priority']?.toString() ?? 'medium',
      createdAt: row['created_at']?.toString(),
      completedAt: row['completed_at']?.toString(),
      isRecurring: row['is_recurring'] == 1,
      recurrenceType: row['recurrence_type']?.toString(),
    );
  }

  Map<String, dynamic> _toDbRow(TaskItem task, {String syncStatus = 'synced'}) {
    return {
      'id': task.id,
      'title': task.title,
      'description': task.description,
      'due': task.due,
      'priority': task.calculatedPriority,
      'status': task.status,
      'tags': jsonEncode(task.tags),
      'list_id': task.listId,
      'list_title': task.listTitle,
      'account': task.account,
      'created_at': task.createdAt ?? DateTime.now().toUtc().toIso8601String(),
      'modified_at': DateTime.now().toUtc().toIso8601String(),
      'completed_at': task.completedAt,
      'is_recurring': task.isRecurring ? 1 : 0,
      'recurrence_type': task.recurrenceType,
      'sync_status': syncStatus,
    };
  }
}
