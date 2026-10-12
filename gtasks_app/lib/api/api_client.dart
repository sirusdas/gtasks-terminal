import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/task_item.dart';
import '../models/account.dart';

class ApiClient {
  String baseUrl;

  ApiClient({this.baseUrl = 'http://127.0.0.1:48275'});

  Future<List<TaskItem>> fetchTasks({String? account, String? status}) async {
    final queryParams = <String, String>{};
    if (account != null && account.isNotEmpty && account != 'all') {
      queryParams['account'] = account;
    }
    if (status != null && status.isNotEmpty && status != 'all') {
      queryParams['status'] = status;
    }

    final uri = Uri.parse('$baseUrl/api/tasks').replace(queryParameters: queryParams.isEmpty ? null : queryParams);
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final rawList = data is Map ? (data['tasks'] ?? []) : data;
      return (rawList as List).map((item) => TaskItem.fromJson(item)).toList();
    } else {
      throw Exception('Failed to load tasks: HTTP ${response.statusCode}');
    }
  }

  Future<List<GTasksAccount>> fetchAccounts() async {
    final uri = Uri.parse('$baseUrl/api/accounts');
    final response = await http.get(uri);

    if (response.statusCode == 200) {
      final data = json.decode(response.body);
      final rawList = data is Map ? (data['accounts'] ?? []) : data;
      return (rawList as List).map((item) => GTasksAccount.fromJson(item)).toList();
    } else {
      return [GTasksAccount(id: 'default', name: 'Default Account', isDefault: true)];
    }
  }

  Future<bool> switchAccount(String accountId) async {
    final uri = Uri.parse('$baseUrl/api/accounts/$accountId/switch');
    final response = await http.post(uri);
    return response.statusCode == 200;
  }

  Future<bool> deleteAccount(String accountId, {bool hard = false}) async {
    try {
      final uri = Uri.parse('$baseUrl/api/accounts/$accountId?hard=$hard');
      final response = await http.delete(uri);
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  Future<bool> restoreAccount(String accountId) async {
    try {
      final uri = Uri.parse('$baseUrl/api/accounts/$accountId/restore');
      final response = await http.post(uri);
      return response.statusCode == 200;
    } catch (_) {
      return false;
    }
  }


  Future<Map<String, dynamic>> startGoogleAuth(String accountName, {String redirectUri = 'http://localhost:48275/api/auth/google/callback'}) async {
    final uri = Uri.parse('$baseUrl/api/auth/google/start');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'account_name': accountName,
        'redirect_uri': redirectUri,
      }),
    );
    if (response.statusCode == 200) {
      return json.decode(response.body);
    }
    throw Exception('Failed to initiate Google OAuth: ${response.body}');
  }

  Future<bool> submitAuthCode(String accountName, String code, {String redirectUri = 'http://localhost:48275/api/auth/google/callback'}) async {
    final uri = Uri.parse('$baseUrl/api/auth/google/submit-code');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'account_name': accountName,
        'code': code,
        'redirect_uri': redirectUri,
      }),
    );
    return response.statusCode == 200;
  }

  Future<bool> completeTask(String taskId, {String? account}) async {
    final uri = Uri.parse('$baseUrl/api/tasks/$taskId/complete');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'account': account ?? 'default'}),
    );
    return response.statusCode == 200;
  }

  Future<bool> createTask({
    required String title,
    String? description,
    String? due,
    String? account,
    String? listTitle,
    String? priority,
    List<String>? tags,
  }) async {
    final uri = Uri.parse('$baseUrl/api/tasks');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'title': title,
        'description': description ?? '',
        'notes': description ?? '',
        'due': due,
        'account_id': account ?? 'default',
        'list_title': listTitle ?? 'My Tasks',
        'priority': priority ?? 'medium',
        'tags': tags ?? [],
      }),
    );
    return response.statusCode == 200 || response.statusCode == 201;
  }

  Future<bool> updateTask({
    required String taskId,
    required String title,
    String? description,
    String? due,
    String? account,
    String? listTitle,
    String? priority,
    List<String>? tags,
  }) async {
    final uri = Uri.parse('$baseUrl/api/tasks/$taskId');
    final response = await http.put(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'title': title,
        'description': description ?? '',
        'notes': description ?? '',
        'due': due,
        'account_id': account ?? 'default',
        if (listTitle != null) 'list_title': listTitle,
        if (priority != null) 'priority': priority,
        'tags': tags ?? [],
      }),
    );
    return response.statusCode == 200;
  }

  Future<bool> deleteTask(String taskId, {String? account}) async {
    final uri = Uri.parse('$baseUrl/api/tasks/$taskId/delete');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({'account': account ?? 'default'}),
    );
    return response.statusCode == 200;
  }

  Future<bool> triggerGoogleSync({String? account}) async {
    final uri = Uri.parse('$baseUrl/api/sync/advanced');
    final Map<String, dynamic> body = {'sync_type': 'both'};
    if (account != null && account != 'all') {
      body['account'] = account;
    }
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode(body),
    );
    return response.statusCode == 200;
  }

  Future<Map<String, dynamic>> fetchReportTypes() async {
    final uri = Uri.parse('$baseUrl/api/reports/types');
    final response = await http.get(uri);
    if (response.statusCode == 200) {
      final jsonBody = json.decode(response.body);
      return jsonBody['data'] ?? {};
    }
    return {};
  }

  Future<Map<String, dynamic>> generateReport(String reportType, {String? account}) async {
    final uri = Uri.parse('$baseUrl/api/reports/generate');
    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode({
        'report_type': reportType,
        'account_id': account ?? 'all',
      }),
    );
    if (response.statusCode == 200) {
      final jsonBody = json.decode(response.body);
      return jsonBody['data'] ?? {};
    }
    throw Exception('Failed to generate report: HTTP ${response.statusCode}');
  }
}
