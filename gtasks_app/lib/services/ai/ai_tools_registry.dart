import 'package:flutter/foundation.dart';
import '../../models/task_item.dart';
import '../../storage/local_database.dart';
import '../../providers/task_provider.dart';
import '../../utils/notes_parser.dart';

class AiToolsRegistry {
  final TaskProvider? taskProvider;
  final LocalDatabase db = LocalDatabase.instance;

  static const List<String> supportedTools = [
    'query_tasks',
    'create_task',
    'update_task',
    'complete_task',
    'batch_reschedule',
    'batch_complete',
    'list_spaces',
    'get_productivity_report',
  ];

  List<String> get toolNames => supportedTools;

  AiToolsRegistry({this.taskProvider});

  Future<String> executeTool(String name, Map<String, dynamic> args) async {
    try {
      switch (name) {
        case 'query_tasks':
          return await _queryTasks(args);
        case 'create_task':
          return await _createTask(args);
        case 'update_task':
          return await _updateTask(args);
        case 'complete_task':
          return await _completeTask(args);
        case 'batch_reschedule':
          return await _batchReschedule(args);
        case 'batch_complete':
          return await _batchComplete(args);
        case 'list_spaces':
          return await _listSpaces();
        case 'get_productivity_report':
          return await _getProductivityReport(args);
        default:
          return 'Unknown tool: $name';
      }
    } catch (e, stack) {
      debugPrint('[AiToolsRegistry] Error executing $name: $e\n$stack');
      return 'Error executing $name: $e';
    }
  }

  Future<String> _queryTasks(Map<String, dynamic> args) async {
    final allTasks = taskProvider?.tasks ?? await db.getAllTasks();

    final query = args['query']?.toString().toLowerCase();
    final status = args['status']?.toString().toLowerCase();
    final priority = args['priority']?.toString().toLowerCase();
    final space = args['space']?.toString().toLowerCase();
    final subspace = args['subspace']?.toString().toLowerCase();
    final overdueOnly = args['overdue_only'] == true;
    final dueBefore = args['due_before']?.toString();
    final dueAfter = args['due_after']?.toString();
    final limit = (args['limit'] as num?)?.toInt() ?? 25;

    final todayStr = DateTime.now().toIso8601String().substring(0, 10);

    final filtered = allTasks.where((t) {
      if (status != null && status != 'all') {
        if (status == 'pending' && t.isCompleted) return false;
        if (status == 'completed' && !t.isCompleted) return false;
      }

      if (priority != null && priority != 'all') {
        final p = t.calculatedPriority.toLowerCase();
        if (priority == 'high+' && p != 'critical' && p != 'high') return false;
        if (priority != 'high+' && p != priority) return false;
      }

      if (space != null && space != 'all') {
        final matches = t.spaces.keys.any((s) => s.toLowerCase() == space);
        if (!matches) return false;
      }

      if (subspace != null) {
        final matches = t.spaces.values.any(
          (subs) => subs.any((s) => s.toLowerCase() == subspace),
        );
        if (!matches) return false;
      }

      if (query != null && query.isNotEmpty) {
        final inTitle = t.title.toLowerCase().contains(query);
        final inDesc = t.description.toLowerCase().contains(query);
        if (!inTitle && !inDesc) return false;
      }

      final taskDue = t.formattedDueDate;
      if (overdueOnly) {
        if (taskDue == null || taskDue.compareTo(todayStr) >= 0 || t.isCompleted) return false;
      }
      if (dueBefore != null && taskDue != null && taskDue.compareTo(dueBefore.substring(0, 10)) > 0) {
        return false;
      }
      if (dueAfter != null && taskDue != null && taskDue.compareTo(dueAfter.substring(0, 10)) < 0) {
        return false;
      }

      return true;
    }).toList();

    if (filtered.isEmpty) {
      return 'No tasks found matching criteria.';
    }

    final buffer = StringBuffer('Found ${filtered.length} tasks (showing top ${filtered.length > limit ? limit : filtered.length}):\n');
    for (final t in filtered.take(limit)) {
      final statusStr = t.isCompleted ? '✓' : ' ';
      final dueStr = t.formattedDueDate != null ? ' | 📅 ${t.formattedDueDate}' : '';
      final prioStr = t.calculatedPriority != 'medium' ? ' | 🔥 ${t.calculatedPriority}' : '';
      final spaceStr = t.spaces.isNotEmpty ? ' | 🚀 ${_formatSpace(t.spaces)}' : '';
      final tagsStr = t.allTags.isNotEmpty ? ' | #${t.allTags.join(' #')}' : '';

      buffer.writeln('- [ID: ${t.id}] [$statusStr] ${t.title}$spaceStr$dueStr$prioStr$tagsStr');
    }

    return buffer.toString().trim();
  }

  Future<String> _createTask(Map<String, dynamic> args) async {
    final title = args['title']?.toString() ?? 'New Task';
    final due = args['due']?.toString();
    final priority = args['priority']?.toString() ?? 'medium';
    final space = args['space']?.toString();
    final subspace = args['subspace']?.toString();
    final notes = args['description']?.toString() ?? '';

    List<String> tags = [];
    if (args['tags'] is List) {
      tags = (args['tags'] as List).map((e) => e.toString()).toList();
    }

    Map<String, List<String>> spaces = {};
    if (space != null && space.isNotEmpty) {
      spaces[space] = subspace != null && subspace.isNotEmpty ? [subspace] : [];
    }

    final formattedNotes = NotesParser.combineNotesAndMetadata(
      notes,
      tags,
      spaces: spaces,
    );

    if (taskProvider != null) {
      await taskProvider!.addTask(
        title: title,
        description: formattedNotes,
        due: due,
        tags: tags,
        spaces: spaces,
      );
      return 'Task created successfully: "$title"';
    } else {
      final task = TaskItem(
        id: 't_${DateTime.now().millisecondsSinceEpoch}',
        title: title,
        description: formattedNotes,
        status: 'pending',
        due: due,
        tags: tags,
        spaces: spaces,
        calculatedPriority: priority,
      );
      await db.upsertTask(task, syncStatus: 'pending_insert');
      return 'Task created locally: "$title" (ID: ${task.id})';
    }
  }

  Future<String> _updateTask(Map<String, dynamic> args) async {
    final taskId = args['task_id']?.toString();
    if (taskId == null) return 'Task ID is required.';

    final existing = await db.getTaskById(taskId);
    if (existing == null) return 'Task with ID $taskId not found.';

    final title = args['title']?.toString() ?? existing.title;
    final due = args['due']?.toString() ?? existing.due;
    final status = args['status']?.toString() ?? existing.status;
    final priority = args['priority']?.toString() ?? existing.calculatedPriority;

    final updated = TaskItem(
      id: existing.id,
      title: title,
      description: existing.description,
      status: status,
      due: due,
      listId: existing.listId,
      listTitle: existing.listTitle,
      account: existing.account,
      tags: existing.tags,
      spaces: existing.spaces,
      calculatedPriority: priority,
    );

    await db.upsertTask(updated, syncStatus: 'pending_update');
    taskProvider?.notifyListeners();
    return 'Task updated successfully: "${updated.title}"';
  }

  Future<String> _completeTask(Map<String, dynamic> args) async {
    final taskId = args['task_id']?.toString();
    if (taskId == null) return 'Task ID is required.';

    if (taskProvider != null) {
      final task = taskProvider!.tasks.where((t) => t.id == taskId).firstOrNull;
      if (task != null) {
        await taskProvider!.completeTask(taskId);
        return 'Task marked as completed: "${task.title}"';
      }
    }

    await db.markTaskCompleted(taskId);
    return 'Task marked as completed (ID: $taskId)';
  }

  Future<String> _batchReschedule(Map<String, dynamic> args) async {
    final taskIds = (args['task_ids'] as List?)?.map((e) => e.toString()).toList() ?? [];
    final newDue = args['new_due_date']?.toString();
    if (taskIds.isEmpty || newDue == null) return 'task_ids and new_due_date are required.';

    int count = 0;
    for (final id in taskIds) {
      final t = await db.getTaskById(id);
      if (t != null) {
        final updated = TaskItem(
          id: t.id,
          title: t.title,
          description: t.description,
          status: t.status,
          due: newDue,
          listId: t.listId,
          listTitle: t.listTitle,
          account: t.account,
          tags: t.tags,
          spaces: t.spaces,
          calculatedPriority: t.calculatedPriority,
        );
        await db.upsertTask(updated, syncStatus: 'pending_update');
        count++;
      }
    }
    taskProvider?.notifyListeners();
    return 'Batch Reschedule complete: $count tasks moved to $newDue';
  }

  Future<String> _batchComplete(Map<String, dynamic> args) async {
    final taskIds = (args['task_ids'] as List?)?.map((e) => e.toString()).toList() ?? [];
    if (taskIds.isEmpty) return 'task_ids is required.';

    int count = 0;
    for (final id in taskIds) {
      await db.markTaskCompleted(id);
      count++;
    }
    taskProvider?.notifyListeners();
    return 'Batch Complete: $count tasks marked completed.';
  }

  Future<String> _listSpaces() async {
    final allTasks = taskProvider?.tasks ?? await db.getAllTasks();
    final spaceMap = <String, Set<String>>{};

    for (final t in allTasks) {
      for (final entry in t.spaces.entries) {
        if (!spaceMap.containsKey(entry.key)) {
          spaceMap[entry.key] = <String>{};
        }
        spaceMap[entry.key]!.addAll(entry.value);
      }
    }

    if (spaceMap.isEmpty) {
      return 'No spaces configured yet.';
    }

    final buffer = StringBuffer('Active Spaces & Sub-spaces:\n');
    for (final e in spaceMap.entries) {
      if (e.value.isNotEmpty) {
        buffer.writeln('- 🚀 **${e.key}**: ${e.value.join(', ')}');
      } else {
        buffer.writeln('- 🚀 **${e.key}** (no sub-spaces)');
      }
    }
    return buffer.toString().trim();
  }

  Future<String> _getProductivityReport(Map<String, dynamic> args) async {
    final timeframe = args['timeframe']?.toString() ?? 'today';
    final allTasks = taskProvider?.tasks ?? await db.getAllTasks();
    final todayStr = DateTime.now().toIso8601String().substring(0, 10);

    final total = allTasks.length;
    final completed = allTasks.where((t) => t.isCompleted).length;
    final pending = allTasks.where((t) => !t.isCompleted).length;
    final overdue = allTasks.where((t) => !t.isCompleted && t.formattedDueDate != null && t.formattedDueDate!.compareTo(todayStr) < 0).length;

    final rate = total > 0 ? (completed / total * 100).toStringAsFixed(1) : '0';

    final spaceCounts = <String, int>{};
    for (final t in allTasks) {
      if (!t.isCompleted) {
        for (final s in t.spaces.keys) {
          spaceCounts[s] = (spaceCounts[s] ?? 0) + 1;
        }
      }
    }

    final buffer = StringBuffer('📊 **Productivity Report (${timeframe.toUpperCase()})**\n');
    buffer.writeln('- Total Tasks: $total');
    buffer.writeln('- ✅ Completed: $completed ($rate%)');
    buffer.writeln('- ⏳ Pending: $pending');
    buffer.writeln('- ⚠️ Overdue: $overdue');

    if (spaceCounts.isNotEmpty) {
      buffer.writeln('\n**Pending by Space:**');
      for (final e in spaceCounts.entries) {
        buffer.writeln('- 🚀 ${e.key}: ${e.value} tasks');
      }
    }

    return buffer.toString().trim();
  }

  String _formatSpace(Map<String, List<String>> spaces) {
    if (spaces.isEmpty) return '';
    final entry = spaces.entries.first;
    if (entry.value.isNotEmpty) {
      return '${entry.key} › ${entry.value.join(',')}';
    }
    return entry.key;
  }
}
