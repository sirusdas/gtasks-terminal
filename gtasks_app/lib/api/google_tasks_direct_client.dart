import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/task_item.dart';
import '../utils/notes_parser.dart';

class GoogleTasksDirectClient {
  static const String _tasksBaseUrl = 'https://tasks.googleapis.com/tasks/v1';

  final String accessToken;
  final String? refreshToken;
  final String? clientId;
  final String? clientSecret;

  GoogleTasksDirectClient({
    required this.accessToken,
    this.refreshToken,
    this.clientId,
    this.clientSecret,
  });

  Map<String, String> get _headers => {
        'Authorization': 'Bearer $accessToken',
        'Content-Type': 'application/json',
      };

  // ---------------------------------------------------------------------------
  // Task Lists API
  // ---------------------------------------------------------------------------

  Future<List<Map<String, dynamic>>> fetchTaskLists() async {
    final List<Map<String, dynamic>> allLists = [];
    String? pageToken;

    do {
      final Map<String, String> queryParams = {
        'maxResults': '100',
        if (pageToken != null && pageToken.isNotEmpty) 'pageToken': pageToken,
      };
      final uri = Uri.parse('$_tasksBaseUrl/users/@me/lists').replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: _headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final items = (data['items'] as List?) ?? [];
        allLists.addAll(items.map((e) => Map<String, dynamic>.from(e as Map)));
        pageToken = data['nextPageToken']?.toString();
      } else {
        throw Exception('Failed to fetch task lists: ${response.statusCode} - ${response.body}');
      }
    } while (pageToken != null && pageToken.isNotEmpty);

    return allLists;
  }

  Future<Map<String, dynamic>> createTaskList(String title) async {
    final uri = Uri.parse('$_tasksBaseUrl/users/@me/lists');
    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode({'title': title}),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      return Map<String, dynamic>.from(jsonDecode(response.body) as Map);
    } else {
      throw Exception('Failed to create task list: ${response.statusCode} - ${response.body}');
    }
  }

  // ---------------------------------------------------------------------------
  // Tasks API
  // ---------------------------------------------------------------------------

  Future<List<TaskItem>> fetchTasks({
    required String listId,
    String? listTitle,
    String account = 'default',
    bool showCompleted = true,
    DateTime? updatedMin,
  }) async {
    final List<TaskItem> allTasks = [];
    String? pageToken;

    do {
      final Map<String, String> queryParams = {
        'showCompleted': showCompleted.toString(),
        'showHidden': 'true',
        'maxResults': '100',
        if (updatedMin != null) 'updatedMin': updatedMin.toUtc().toIso8601String(),
        if (pageToken != null && pageToken.isNotEmpty) 'pageToken': pageToken,
      };
      final uri = Uri.parse('$_tasksBaseUrl/lists/$listId/tasks').replace(queryParameters: queryParams);
      final response = await http.get(uri, headers: _headers);

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final items = (data['items'] as List?) ?? [];

        for (final raw in items) {
          if (raw['title'] == null && raw['notes'] == null) continue;
          final isCompleted = raw['status'] == 'completed';
          final notes = raw['notes']?.toString() ?? '';
          final split = NotesParser.splitNotesAndTags(notes);

          allTasks.add(TaskItem(
            id: raw['id'].toString(),
            title: raw['title']?.toString() ?? 'Untitled',
            description: split.cleanNotes,
            status: isCompleted ? 'completed' : 'pending',
            due: raw['due']?.toString(),
            listId: listId,
            listTitle: listTitle,
            account: account,
            tags: split.tags,
            calculatedPriority: calculatePriorityFromTags(split.tags),
            createdAt: raw['updated']?.toString(), // Google uses 'updated'
            completedAt: raw['completed']?.toString(),
          ));
        }

        pageToken = data['nextPageToken']?.toString();
      } else {
        throw Exception('Failed to fetch tasks from list $listId: ${response.statusCode} - ${response.body}');
      }
    } while (pageToken != null && pageToken.isNotEmpty);

    return allTasks;
  }

  Future<TaskItem> createTask({
    required String listId,
    required String title,
    String? notes,
    String? due,
    String? listTitle,
    String account = 'default',
  }) async {
    final uri = Uri.parse('$_tasksBaseUrl/lists/$listId/tasks');
    final payload = {
      'title': title,
      if (notes != null) 'notes': notes,
      if (due != null) 'due': due,
    };

    final response = await http.post(
      uri,
      headers: _headers,
      body: jsonEncode(payload),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final raw = jsonDecode(response.body);
      final taskNotes = raw['notes']?.toString() ?? '';
      final split = NotesParser.splitNotesAndTags(taskNotes);

      return TaskItem(
        id: raw['id'].toString(),
        title: raw['title']?.toString() ?? title,
        description: split.cleanNotes,
        status: raw['status']?.toString() ?? 'pending',
        due: raw['due']?.toString(),
        listId: listId,
        listTitle: listTitle,
        account: account,
        tags: split.tags,
        calculatedPriority: calculatePriorityFromTags(split.tags),
        createdAt: raw['updated']?.toString(),
      );
    } else {
      throw Exception('Failed to create task: ${response.statusCode} - ${response.body}');
    }
  }

  Future<bool> updateTask({
    required String listId,
    required String taskId,
    String? title,
    String? notes,
    String? status,
    String? due,
  }) async {
    final uri = Uri.parse('$_tasksBaseUrl/lists/$listId/tasks/$taskId');
    final payload = <String, dynamic>{};
    if (title != null) payload['title'] = title;
    if (notes != null) payload['notes'] = notes;
    if (due != null) payload['due'] = due;
    if (status != null) {
      payload['status'] = status == 'completed' ? 'completed' : 'needsAction';
    }

    final response = await http.patch(
      uri,
      headers: _headers,
      body: jsonEncode(payload),
    );

    return response.statusCode == 200;
  }

  Future<bool> deleteTask({
    required String listId,
    required String taskId,
  }) async {
    final uri = Uri.parse('$_tasksBaseUrl/lists/$listId/tasks/$taskId');
    final response = await http.delete(uri, headers: _headers);
    return response.statusCode == 204 || response.statusCode == 200;
  }

  // ---------------------------------------------------------------------------
  // Priority Helper
  // ---------------------------------------------------------------------------

  static String calculatePriorityFromTags(List<String> tags) {
    for (final tag in tags) {
      final t = tag.toLowerCase().trim();
      final asteriskMatch = RegExp(r'^\[?(\*+)\]?$').firstMatch(t);
      if (asteriskMatch != null) {
        final count = asteriskMatch.group(1)!.length;
        if (count >= 6) return 'critical';
        if (count >= 4) return 'high';
        if (count == 3) return 'medium';
        return 'low';
      }
      if (t == 'critical' || t == 'urgent' || t == 'p0') return 'critical';
      if (t == 'high' || t == 'p1') return 'high';
      if (t == 'medium' || t == 'med' || t == 'p2') return 'medium';
      if (t == 'low' || t == 'p3' || t == 'someday') return 'low';
    }
    return 'medium';
  }
}
