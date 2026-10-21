import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/task_item.dart';
import '../utils/notes_parser.dart';

class MicrosoftTodoDirectClient {
  static const String _graphBaseUrl = 'https://graph.microsoft.com/v1.0';

  // Standard Microsoft public client application ID (Microsoft CLI / PowerShell public client)
  static const String defaultMicrosoftClientId = '04b07795-8ddb-461a-bbee-02f9e1bf7b46';

  String accessToken;
  String? refreshToken;
  final String? clientId;
  final String? clientSecret;
  final void Function(String newAccessToken, String? newRefreshToken)? onTokenRefreshed;

  MicrosoftTodoDirectClient({
    required this.accessToken,
    this.refreshToken,
    this.clientId,
    this.clientSecret,
    this.onTokenRefreshed,
  });

  Map<String, String> get _headers => {
        'Authorization': 'Bearer $accessToken',
        'Content-Type': 'application/json',
      };

  Future<bool> refreshAccessToken() async {
    final rToken = refreshToken;
    final cId = clientId ?? defaultMicrosoftClientId;
    if (rToken == null || rToken.isEmpty) return false;

    try {
      final Map<String, String> body = {
        'client_id': cId,
        'grant_type': 'refresh_token',
        'refresh_token': rToken,
        'scope': 'Tasks.ReadWrite offline_access User.Read',
      };
      if (clientSecret != null && clientSecret!.isNotEmpty) {
        body['client_secret'] = clientSecret!;
      }

      final response = await http.post(
        Uri.parse('https://login.microsoftonline.com/common/oauth2/v2.0/token'),
        headers: {'Content-Type': 'application/x-www-form-urlencoded'},
        body: body,
      ).timeout(const Duration(seconds: 12));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final newAccessTok = data['access_token']?.toString();
        final newRefreshTok = data['refresh_token']?.toString() ?? rToken;
        if (newAccessTok != null && newAccessTok.isNotEmpty) {
          accessToken = newAccessTok;
          refreshToken = newRefreshTok;
          onTokenRefreshed?.call(newAccessTok, newRefreshTok);
          return true;
        }
      }
    } catch (_) {}
    return false;
  }

  Future<http.Response> _sendWithAuthRetry(Future<http.Response> Function() requestFn) async {
    http.Response response = await requestFn().timeout(const Duration(seconds: 12));
    if (response.statusCode == 401 && refreshToken != null && refreshToken!.isNotEmpty) {
      final refreshed = await refreshAccessToken();
      if (refreshed) {
        response = await requestFn().timeout(const Duration(seconds: 12));
      }
    }
    return response;
  }

  // ---------------------------------------------------------------------------
  // User Profile
  // ---------------------------------------------------------------------------

  Future<Map<String, dynamic>?> fetchUserProfile() async {
    try {
      final uri = Uri.parse('$_graphBaseUrl/me');
      final response = await _sendWithAuthRetry(() => http.get(uri, headers: _headers));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final displayName = data['displayName']?.toString() ?? 'Microsoft Account';
        final email = data['mail']?.toString() ?? data['userPrincipalName']?.toString() ?? '';
        return {
          'id': data['id']?.toString() ?? '',
          'displayName': displayName,
          'email': email,
        };
      }
    } catch (_) {}
    return null;
  }

  // ---------------------------------------------------------------------------
  // Task Lists
  // ---------------------------------------------------------------------------

  Future<List<Map<String, dynamic>>> fetchTaskLists() async {
    final List<Map<String, dynamic>> allLists = [];
    String? nextUrl = '$_graphBaseUrl/me/todo/lists';

    while (nextUrl != null && nextUrl.isNotEmpty) {
      final uri = Uri.parse(nextUrl);
      final response = await _sendWithAuthRetry(() => http.get(uri, headers: _headers));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final items = (data['value'] as List?) ?? [];
        for (final item in items) {
          allLists.add({
            'id': item['id']?.toString() ?? '',
            'title': item['displayName']?.toString() ?? 'Tasks',
            'isOwner': item['isOwner'] == true,
            'wellknownListName': item['wellknownListName']?.toString(),
          });
        }
        nextUrl = data['@odata.nextLink']?.toString();
      } else {
        break;
      }
    }

    return allLists;
  }

  Future<Map<String, dynamic>> createTaskList(String displayName) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists');
    final response = await _sendWithAuthRetry(
      () => http.post(
        uri,
        headers: _headers,
        body: jsonEncode({'displayName': displayName}),
      ),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final item = jsonDecode(response.body);
      return {
        'id': item['id']?.toString() ?? '',
        'title': item['displayName']?.toString() ?? displayName,
        'isOwner': true,
      };
    }
    throw Exception('Failed to create Microsoft To Do list: ${response.statusCode} ${response.body}');
  }

  Future<bool> deleteTaskList(String listId) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId');
    final response = await _sendWithAuthRetry(() => http.delete(uri, headers: _headers));
    return response.statusCode == 204 || response.statusCode == 200;
  }

  // ---------------------------------------------------------------------------
  // Tasks
  // ---------------------------------------------------------------------------

  Future<List<TaskItem>> fetchTasks({
    required String listId,
    required String listTitle,
    required String account,
    DateTime? updatedMin,
  }) async {
    final List<TaskItem> allTasks = [];
    
    final queryParams = <String, String>{
      '\$top': '100',
    };
    if (updatedMin != null) {
      queryParams['\$filter'] = 'lastModifiedDateTime ge ${updatedMin.toUtc().toIso8601String()}';
    }

    String? nextUrl = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks')
        .replace(queryParameters: queryParams)
        .toString();

    while (nextUrl != null && nextUrl.isNotEmpty) {
      final uri = Uri.parse(nextUrl);
      final response = await _sendWithAuthRetry(() => http.get(uri, headers: _headers));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final items = (data['value'] as List?) ?? [];

        for (final item in items) {
          final id = item['id']?.toString() ?? '';
          final title = item['title']?.toString() ?? 'Untitled';
          final statusRaw = item['status']?.toString() ?? 'notStarted';
          final isCompleted = statusRaw == 'completed';
          final rawNotes = item['body']?['content']?.toString() ?? '';

          // Parse due date: Microsoft Graph returns dueDateTime: { dateTime: "...", timeZone: "UTC" }
          String? dueDate;
          if (item['dueDateTime'] != null && item['dueDateTime']['dateTime'] != null) {
            final dtStr = item['dueDateTime']['dateTime'].toString();
            dueDate = dtStr.length >= 10 ? dtStr.substring(0, 10) : dtStr;
          }

          // Parse priority from Microsoft importance: low, normal, high
          final importance = item['importance']?.toString().toLowerCase() ?? 'normal';
          String priority = 'medium';
          if (importance == 'high') {
            priority = 'high';
          } else if (importance == 'low') {
            priority = 'low';
          }

          // Extract tags, spaces, and clean notes using NotesParser
          final parsed = NotesParser.splitNotesAndMetadata(rawNotes);
          final calculatedPriority = calculatePriorityFromTags(parsed.tags, fallback: priority);

          allTasks.add(TaskItem(
            id: id,
            title: title,
            description: rawNotes,
            status: isCompleted ? 'completed' : 'pending',
            due: dueDate,
            listId: listId,
            listTitle: listTitle,
            account: account,
            tags: parsed.tags,
            spaces: parsed.spaces,
            calculatedPriority: calculatedPriority,
            createdAt: item['createdDateTime']?.toString(),
            completedAt: item['completedDateTime']?['dateTime']?.toString(),
            cleanNotes: parsed.cleanNotes,
            allTags: parsed.tags,
            formattedDueDate: dueDate,
          ));
        }

        nextUrl = data['@odata.nextLink']?.toString();
      } else {
        break;
      }
    }

    return allTasks;
  }

  Future<TaskItem> createTask({
    required String listId,
    required String title,
    String? notes,
    String? due,
    String? listTitle,
    String? account,
    String? priority,
  }) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks');

    final Map<String, dynamic> body = {
      'title': title,
    };

    if (notes != null && notes.isNotEmpty) {
      body['body'] = {
        'content': notes,
        'contentType': 'text',
      };
    }

    if (due != null && due.isNotEmpty) {
      final dateOnly = due.length >= 10 ? due.substring(0, 10) : due;
      body['dueDateTime'] = {
        'dateTime': '${dateOnly}T00:00:00.0000000',
        'timeZone': 'UTC',
      };
    }

    if (priority != null) {
      final p = priority.toLowerCase();
      if (p == 'critical' || p == 'high') {
        body['importance'] = 'high';
      } else if (p == 'low') {
        body['importance'] = 'low';
      } else {
        body['importance'] = 'normal';
      }
    }

    final response = await _sendWithAuthRetry(
      () => http.post(
        uri,
        headers: _headers,
        body: jsonEncode(body),
      ),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final item = jsonDecode(response.body);
      final rawNotes = item['body']?['content']?.toString() ?? notes ?? '';
      final parsed = NotesParser.splitNotesAndMetadata(rawNotes);
      String? dueDate;
      if (item['dueDateTime'] != null && item['dueDateTime']['dateTime'] != null) {
        final dtStr = item['dueDateTime']['dateTime'].toString();
        dueDate = dtStr.length >= 10 ? dtStr.substring(0, 10) : dtStr;
      }

      final importance = item['importance']?.toString().toLowerCase() ?? 'normal';
      final defaultPrio = importance == 'high' ? 'high' : (importance == 'low' ? 'low' : 'medium');
      final effectivePrio = calculatePriorityFromTags(parsed.tags, fallback: defaultPrio);

      return TaskItem(
        id: item['id'].toString(),
        title: item['title']?.toString() ?? title,
        description: rawNotes,
        status: item['status'] == 'completed' ? 'completed' : 'pending',
        due: dueDate ?? due,
        listId: listId,
        listTitle: listTitle,
        account: account ?? 'microsoft',
        tags: parsed.tags,
        spaces: parsed.spaces,
        calculatedPriority: effectivePrio,
        createdAt: item['createdDateTime']?.toString() ?? DateTime.now().toUtc().toIso8601String(),
        cleanNotes: parsed.cleanNotes,
        allTags: parsed.tags,
        formattedDueDate: dueDate ?? due,
      );
    }

    throw Exception('Failed to create Microsoft To Do task: ${response.statusCode} ${response.body}');
  }

  Future<bool> updateTask({
    required String listId,
    required String taskId,
    String? title,
    String? notes,
    String? due,
    String? status,
    String? priority,
  }) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks/$taskId');

    final Map<String, dynamic> body = {};

    if (title != null) {
      body['title'] = title;
    }

    if (notes != null) {
      body['body'] = {
        'content': notes,
        'contentType': 'text',
      };
    }

    if (status != null) {
      body['status'] = status == 'completed' ? 'completed' : 'notStarted';
    }

    if (due != null) {
      if (due.isNotEmpty) {
        final dateOnly = due.length >= 10 ? due.substring(0, 10) : due;
        body['dueDateTime'] = {
          'dateTime': '${dateOnly}T00:00:00.0000000',
          'timeZone': 'UTC',
        };
      } else {
        body['dueDateTime'] = null;
      }
    }

    if (priority != null) {
      final p = priority.toLowerCase();
      if (p == 'critical' || p == 'high') {
        body['importance'] = 'high';
      } else if (p == 'low') {
        body['importance'] = 'low';
      } else {
        body['importance'] = 'normal';
      }
    }

    final response = await _sendWithAuthRetry(
      () => http.patch(
        uri,
        headers: _headers,
        body: jsonEncode(body),
      ),
    );

    return response.statusCode == 200;
  }

  Future<bool> deleteTask({
    required String listId,
    required String taskId,
  }) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks/$taskId');
    final response = await _sendWithAuthRetry(() => http.delete(uri, headers: _headers));
    return response.statusCode == 204 || response.statusCode == 200;
  }

  // ---------------------------------------------------------------------------
  // Checklist Items (Subtasks)
  // ---------------------------------------------------------------------------

  Future<List<Map<String, dynamic>>> fetchChecklistItems({
    required String listId,
    required String taskId,
  }) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks/$taskId/checklistItems');
    final response = await _sendWithAuthRetry(() => http.get(uri, headers: _headers));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      final items = (data['value'] as List?) ?? [];
      return items.map((i) => {
        'id': i['id']?.toString() ?? '',
        'displayName': i['displayName']?.toString() ?? '',
        'isChecked': i['isChecked'] == true,
      }).toList();
    }
    return [];
  }

  Future<Map<String, dynamic>?> createChecklistItem({
    required String listId,
    required String taskId,
    required String title,
  }) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks/$taskId/checklistItems');
    final response = await _sendWithAuthRetry(
      () => http.post(
        uri,
        headers: _headers,
        body: jsonEncode({'displayName': title}),
      ),
    );

    if (response.statusCode == 200 || response.statusCode == 201) {
      final data = jsonDecode(response.body);
      return {
        'id': data['id']?.toString() ?? '',
        'displayName': data['displayName']?.toString() ?? title,
        'isChecked': data['isChecked'] == true,
      };
    }
    return null;
  }

  Future<bool> updateChecklistItem({
    required String listId,
    required String taskId,
    required String itemId,
    bool? isChecked,
    String? title,
  }) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks/$taskId/checklistItems/$itemId');
    final Map<String, dynamic> body = {};
    if (isChecked != null) body['isChecked'] = isChecked;
    if (title != null) body['displayName'] = title;

    final response = await _sendWithAuthRetry(
      () => http.patch(
        uri,
        headers: _headers,
        body: jsonEncode(body),
      ),
    );
    return response.statusCode == 200;
  }

  Future<bool> deleteChecklistItem({
    required String listId,
    required String taskId,
    required String itemId,
  }) async {
    final uri = Uri.parse('$_graphBaseUrl/me/todo/lists/$listId/tasks/$taskId/checklistItems/$itemId');
    final response = await _sendWithAuthRetry(() => http.delete(uri, headers: _headers));
    return response.statusCode == 204 || response.statusCode == 200;
  }

  // ---------------------------------------------------------------------------
  // Priority Helper
  // ---------------------------------------------------------------------------

  static String calculatePriorityFromTags(List<String> tags, {String fallback = 'medium'}) {
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
    return fallback;
  }
}

