import 'dart:convert';
import 'dart:io';
import 'package:path/path.dart' as p;
import 'package:path_provider/path_provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../storage/local_database.dart';
import '../models/task_item.dart';

class BackupMetadata {
  final String filename;
  final String filePath;
  final DateTime createdAt;
  final int taskCount;
  final int byteSize;
  final String note;

  BackupMetadata({
    required this.filename,
    required this.filePath,
    required this.createdAt,
    required this.taskCount,
    required this.byteSize,
    required this.note,
  });

  String get formattedSize {
    if (byteSize < 1024) return '$byteSize B';
    if (byteSize < 1024 * 1024) return '${(byteSize / 1024).toStringAsFixed(1)} KB';
    return '${(byteSize / (1024 * 1024)).toStringAsFixed(1)} MB';
  }
}

class BackupService {
  static final BackupService _instance = BackupService._internal();
  factory BackupService() => _instance;
  BackupService._internal();

  Future<Directory> _getBackupDirectory() async {
    final docsDir = await getApplicationDocumentsDirectory();
    final backupDir = Directory(p.join(docsDir.path, 'backups'));
    if (!await backupDir.exists()) {
      await backupDir.create(recursive: true);
    }
    return backupDir;
  }

  /// Create a full JSON snapshot of all local tasks, tabs, spaces, and preferences.
  Future<BackupMetadata> createBackup({String note = 'Manual Backup'}) async {
    final backupDir = await _getBackupDirectory();
    final now = DateTime.now();
    final timestamp = now.toIso8601String().replaceAll(':', '-').replaceAll('.', '-');
    final filename = 'gtasks_backup_$timestamp.json';
    final filePath = p.join(backupDir.path, filename);

    // Fetch all tasks from SQLite
    final tasks = await LocalDatabase.instance.getAllTasks();

    // Fetch tabs configuration from SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    final tabsJson = prefs.getString('task_tabs_config');
    List<dynamic>? tabsList;
    if (tabsJson != null && tabsJson.isNotEmpty) {
      try {
        tabsList = jsonDecode(tabsJson);
      } catch (_) {}
    }

    final backupData = {
      'app': 'gtasks',
      'version': 1,
      'created_at': now.toUtc().toIso8601String(),
      'note': note,
      'task_count': tasks.length,
      'tabs': tabsList ?? [],
      'tasks': tasks.map((t) => t.toJson()).toList(),
    };

    final content = const JsonEncoder.withIndent('  ').convert(backupData);
    final file = File(filePath);
    await file.writeAsString(content);

    return BackupMetadata(
      filename: filename,
      filePath: filePath,
      createdAt: now,
      taskCount: tasks.length,
      byteSize: await file.length(),
      note: note,
    );
  }

  /// List all local backups sorted newest first.
  Future<List<BackupMetadata>> listBackups() async {
    final backupDir = await _getBackupDirectory();
    final files = backupDir.listSync().whereType<File>().where((f) => f.path.endsWith('.json')).toList();

    final List<BackupMetadata> backups = [];

    for (final file in files) {
      try {
        final stat = file.statSync();
        final content = await file.readAsString();
        final Map<String, dynamic> data = jsonDecode(content);

        final taskCount = data['task_count'] as int? ?? (data['tasks'] as List?)?.length ?? 0;
        final note = data['note']?.toString() ?? 'Backup';
        final createdAtStr = data['created_at']?.toString();
        final createdAt = createdAtStr != null ? DateTime.tryParse(createdAtStr) ?? stat.modified : stat.modified;

        backups.add(BackupMetadata(
          filename: p.basename(file.path),
          filePath: file.path,
          createdAt: createdAt,
          taskCount: taskCount,
          byteSize: stat.size,
          note: note,
        ));
      } catch (_) {
        // Skip corrupt or unreadable files
      }
    }

    backups.sort((a, b) => b.createdAt.compareTo(a.createdAt));
    return backups;
  }

  /// Restore tasks and tabs from a backup file.
  /// Automatically creates a pre-restore safety backup first.
  Future<int> restoreBackup(String filePath) async {
    final file = File(filePath);
    if (!await file.exists()) {
      throw Exception('Backup file does not exist: $filePath');
    }

    final content = await file.readAsString();
    final Map<String, dynamic> data = jsonDecode(content);

    final rawTasks = data['tasks'] as List<dynamic>?;
    if (rawTasks == null) {
      throw Exception('Invalid backup format: missing "tasks" list');
    }

    // Safety backup of current state
    try {
      await createBackup(note: 'Pre-restore safety backup');
    } catch (_) {}

    int restoredCount = 0;
    for (final raw in rawTasks) {
      try {
        final task = TaskItem.fromJson(raw as Map<String, dynamic>);
        await LocalDatabase.instance.upsertTask(task, syncStatus: 'synced');
        restoredCount++;
      } catch (_) {}
    }

    // Restore tabs configuration if available
    final rawTabs = data['tabs'];
    if (rawTabs != null && rawTabs is List) {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setString('task_tabs_config', jsonEncode(rawTabs));
    }

    return restoredCount;
  }

  /// Delete a backup file.
  Future<bool> deleteBackup(String filePath) async {
    final file = File(filePath);
    if (await file.exists()) {
      await file.delete();
      return true;
    }
    return false;
  }
}
