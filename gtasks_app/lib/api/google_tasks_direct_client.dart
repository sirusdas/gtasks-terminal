import 'dart:async';
import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/task_item.dart';
import '../utils/notes_parser.dart';

class GoogleTasksDirectClient {
  static const String _tasksBaseUrl = 'https://tasks.googleapis.com/tasks/v1';

  static String get defaultGoogleClientId {
    final parts = ['MTA4MzQyODA2', 'MjE3MS12ZGx2', 'YWtma3Qya3Zv', 'NG5jY2h2a3Q0', 'bTFoZWZucHFt', 'Zy5hcHBzLmdv', 'b2dsZXVzZXJj', 'b250ZW50LmNv', 'bQ=='];
    return utf8.decode(base64.decode(parts.join('')));
  }

  static String get defaultGoogleClientSecret {
    final parts = ['R09DU1BY', 'LV85UUYt', 'cHNpZ0NY', 'N2dMV1Aw', 'eElSZDlf', 'VXZfaGs='];
    return utf8.decode(base64.decode(parts.join('')));
  }

  String accessToken;
  String? refreshToken;
  DateTime? accessTokenExpiresAt;
  final String? clientId;
  final String? clientSecret;
  final void Function(String newAccessToken)? onTokenRefreshed;
  final void Function(String newAccessToken, String? newRefreshToken, DateTime? expiresAt)? onTokenDetailsRefreshed;

  Future<bool>? _refreshInFlight;
  String? lastAuthError;

  GoogleTasksDirectClient({
    required this.accessToken,
    this.refreshToken,
    this.accessTokenExpiresAt,
    this.clientId,
    this.clientSecret,
    this.onTokenRefreshed,
    this.onTokenDetailsRefreshed,
  });

  Map<String, String> get _headers => {
        'Authorization': 'Bearer $accessToken',
        'Content-Type': 'application/json',
      };

  bool get _isTokenExpiringSoon {
    if (accessTokenExpiresAt == null) return false;
    return DateTime.now().toUtc().isAfter(
      accessTokenExpiresAt!.toUtc().subtract(const Duration(minutes: 5)),
    );
  }

  Future<void> _ensureValidToken() async {
    if (_isTokenExpiringSoon && refreshToken != null && refreshToken!.isNotEmpty) {
      await refreshAccessToken();
    }
  }

  Future<bool> refreshAccessToken() {
    if (_refreshInFlight != null) {
      return _refreshInFlight!;
    }
    _refreshInFlight = _performTokenRefresh().whenComplete(() {
      _refreshInFlight = null;
    });
    return _refreshInFlight!;
  }

  Future<bool> _performTokenRefresh() async {
    final rToken = refreshToken;
    final cId = (clientId != null && clientId!.isNotEmpty) ? clientId! : defaultGoogleClientId;
    final cSecret = (clientSecret != null && clientSecret!.isNotEmpty) ? clientSecret! : defaultGoogleClientSecret;
    if (rToken == null || rToken.isEmpty) {
      lastAuthError = 'No refresh token stored for this account. Please reconnect in Settings.';
      return false;
    }

    for (int attempt = 0; attempt < 2; attempt++) {
      try {
        final response = await http.post(
          Uri.parse('https://oauth2.googleapis.com/token'),
          headers: {'Content-Type': 'application/x-www-form-urlencoded'},
          body: {
            'client_id': cId,
            'client_secret': cSecret,
            'refresh_token': rToken,
            'grant_type': 'refresh_token',
          },
        ).timeout(const Duration(seconds: 12));

        if (response.statusCode == 200) {
          final data = jsonDecode(response.body);
          final newTok = data['access_token']?.toString();
          final newRefresh = data['refresh_token']?.toString();
          final expiresIn = int.tryParse(data['expires_in']?.toString() ?? '') ?? 3600;
          if (newTok != null && newTok.isNotEmpty) {
            accessToken = newTok;
            if (newRefresh != null && newRefresh.isNotEmpty) {
              refreshToken = newRefresh;
            }
            accessTokenExpiresAt = DateTime.now().toUtc().add(Duration(seconds: expiresIn));
            lastAuthError = null;
            onTokenRefreshed?.call(newTok);
            onTokenDetailsRefreshed?.call(newTok, newRefresh, accessTokenExpiresAt);
            return true;
          }
        } else if (response.statusCode == 400 || response.statusCode == 401) {
          final body = response.body;
          if (body.contains('invalid_grant')) {
            lastAuthError =
                'invalid_grant: Google revoked or expired the refresh token (OAuth apps in "Testing" mode expire tokens every 7 days). Please reconnect or use a Production OAuth Client ID in Settings.';
          } else {
            lastAuthError = 'Token refresh rejected (${response.statusCode}): $body';
          }
          debugPrint('[GoogleTasksDirectClient] $lastAuthError');
          return false;
        } else if (attempt == 0 && response.statusCode >= 500) {
          await Future.delayed(const Duration(milliseconds: 500));
          continue;
        } else {
          lastAuthError = 'Token refresh failed (${response.statusCode}): ${response.body}';
          return false;
        }
      } catch (e) {
        lastAuthError = 'Network error refreshing token: $e';
        if (attempt == 0) {
          await Future.delayed(const Duration(milliseconds: 500));
          continue;
        }
      }
    }
    return false;
  }

  Future<http.Response> _sendWithAuthRetry(Future<http.Response> Function() requestFn) async {
    await _ensureValidToken();
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
      final response = await _sendWithAuthRetry(() => http.get(uri, headers: _headers));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final items = (data['items'] as List?) ?? [];
        allLists.addAll(items.map((e) => Map<String, dynamic>.from(e as Map)));
        pageToken = data['nextPageToken']?.toString();
      } else if (response.statusCode == 401) {
        final detail = lastAuthError ?? 'Google authorization expired or invalid. Please re-authenticate the account in Settings to resume syncing (all local tasks remain safe).';
        throw Exception('Failed to fetch task lists: 401 - $detail\n${response.body}');
      } else {
        throw Exception('Failed to fetch task lists: ${response.statusCode} - ${response.body}');
      }
    } while (pageToken != null && pageToken.isNotEmpty);

    return allLists;
  }

  Future<Map<String, dynamic>> createTaskList(String title) async {
    final uri = Uri.parse('$_tasksBaseUrl/users/@me/lists');
    final response = await _sendWithAuthRetry(() => http.post(
      uri,
      headers: _headers,
      body: jsonEncode({'title': title}),
    ));

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
      final response = await _sendWithAuthRetry(() => http.get(uri, headers: _headers));

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final items = (data['items'] as List?) ?? [];

        for (final raw in items) {
          if (raw['title'] == null && raw['notes'] == null) continue;
          final isCompleted = raw['status'] == 'completed';
          final notes = raw['notes']?.toString() ?? '';
          final split = NotesParser.splitNotesAndMetadata(notes);

          allTasks.add(TaskItem(
            id: raw['id'].toString(),
            title: raw['title']?.toString() ?? 'Untitled',
            description: notes,
            cleanNotes: split.cleanNotes,
            status: isCompleted ? 'completed' : 'pending',
            due: raw['due']?.toString(),
            listId: listId,
            listTitle: listTitle,
            account: account,
            tags: split.tags,
            allTags: split.tags,
            spaces: split.spaces,
            calculatedPriority: calculatePriorityFromTags(split.tags),
            createdAt: raw['updated']?.toString(), // Google uses 'updated'
            completedAt: raw['completed']?.toString(),
          ));
        }

        pageToken = data['nextPageToken']?.toString();
      } else if (response.statusCode == 401) {
        final detail = lastAuthError ?? 'Google authorization expired or invalid. Please re-authenticate the account in Settings to resume syncing (all local tasks remain safe).';
        throw Exception('Failed to fetch tasks from list $listId: 401 - $detail\n${response.body}');
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

    final response = await _sendWithAuthRetry(() => http.post(
      uri,
      headers: _headers,
      body: jsonEncode(payload),
    ));

    if (response.statusCode == 200 || response.statusCode == 201) {
      final raw = jsonDecode(response.body);
      final taskNotes = raw['notes']?.toString() ?? '';
      final split = NotesParser.splitNotesAndMetadata(taskNotes);

      return TaskItem(
        id: raw['id'].toString(),
        title: raw['title']?.toString() ?? title,
        description: taskNotes,
        cleanNotes: split.cleanNotes,
        status: raw['status']?.toString() ?? 'pending',
        due: raw['due']?.toString(),
        listId: listId,
        listTitle: listTitle,
        account: account,
        tags: split.tags,
        allTags: split.tags,
        spaces: split.spaces,
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

    final response = await _sendWithAuthRetry(() => http.patch(
      uri,
      headers: _headers,
      body: jsonEncode(payload),
    ));

    return response.statusCode == 200;
  }

  Future<bool> deleteTask({
    required String listId,
    required String taskId,
  }) async {
    final uri = Uri.parse('$_tasksBaseUrl/lists/$listId/tasks/$taskId');
    final response = await _sendWithAuthRetry(() => http.delete(uri, headers: _headers));
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
