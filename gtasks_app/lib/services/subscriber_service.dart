import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

class SubscriberSyncResult {
  final bool success;
  final String message;
  final int? statusCode;

  SubscriberSyncResult({
    required this.success,
    required this.message,
    this.statusCode,
  });
}

class SubscriberService {
  static final SubscriberService _instance = SubscriberService._internal();
  factory SubscriberService() => _instance;
  SubscriberService._internal();

  static const String _prefApiUrl = 'subscriber_webhook_api_url';
  static const String _prefSyncedEmails = 'subscriber_synced_emails';
  static const String _prefPendingQueue = 'subscriber_pending_queue';

  /// Get current configured external subscriber webhook / API URL
  Future<String?> getApiUrl() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_prefApiUrl);
  }

  /// Update the external subscriber webhook / API URL and flush any pending subscribers
  Future<void> setApiUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    final trimmed = url.trim();
    if (trimmed.isEmpty) {
      await prefs.remove(_prefApiUrl);
    } else {
      await prefs.setString(_prefApiUrl, trimmed);
      // Attempt flushing pending subscribers
      await flushPending();
    }
  }

  /// Check if a specific email has been recorded and synced to the subscriber endpoint
  Future<bool> isEmailSynced(String email) async {
    final prefs = await SharedPreferences.getInstance();
    final synced = prefs.getStringList(_prefSyncedEmails) ?? [];
    return synced.contains(email.trim().toLowerCase());
  }

  /// Register or sync an onboarded user's email to the external API
  Future<SubscriberSyncResult> syncSubscriber({
    required String email,
    String? name,
    String? accountId,
    bool force = false,
  }) async {
    final cleanEmail = email.trim().toLowerCase();
    if (cleanEmail.isEmpty || !cleanEmail.contains('@')) {
      return SubscriberSyncResult(
        success: false,
        message: 'Invalid email address',
      );
    }

    final prefs = await SharedPreferences.getInstance();
    final synced = prefs.getStringList(_prefSyncedEmails) ?? [];

    if (!force && synced.contains(cleanEmail)) {
      return SubscriberSyncResult(
        success: true,
        message: 'Email already synced as subscriber',
      );
    }

    final apiUrl = prefs.getString(_prefApiUrl);
    final payload = {
      'email': cleanEmail,
      'name': name ?? '',
      'account_id': accountId ?? 'default',
      'source': 'gtasks_app',
      'platform': Platform.operatingSystem,
      'timestamp': DateTime.now().toUtc().toIso8601String(),
    };

    if (apiUrl == null || apiUrl.trim().isEmpty) {
      // Queue for later sync when API URL is configured
      await _queuePending(payload);
      return SubscriberSyncResult(
        success: true,
        message: 'External API URL not set yet; queued subscriber locally',
      );
    }

    try {
      final response = await http.post(
        Uri.parse(apiUrl.trim()),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(payload),
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode >= 200 && response.statusCode < 300) {
        if (!synced.contains(cleanEmail)) {
          synced.add(cleanEmail);
          await prefs.setStringList(_prefSyncedEmails, synced);
        }
        await _removeFromPending(cleanEmail);
        return SubscriberSyncResult(
          success: true,
          message: 'Successfully registered onboarded user with external API (${response.statusCode})',
          statusCode: response.statusCode,
        );
      } else {
        await _queuePending(payload);
        return SubscriberSyncResult(
          success: false,
          message: 'External API returned HTTP ${response.statusCode}: ${response.body}',
          statusCode: response.statusCode,
        );
      }
    } catch (e) {
      await _queuePending(payload);
      return SubscriberSyncResult(
        success: false,
        message: 'Failed to connect to external subscriber API: $e',
      );
    }
  }

  /// Test connectivity to a given subscriber API URL
  Future<SubscriberSyncResult> testEndpoint(String testUrl) async {
    try {
      final testPayload = {
        'test': true,
        'email': 'ping@gtasks.app',
        'name': 'GTasks Diagnostic Ping',
        'source': 'gtasks_app_test',
        'timestamp': DateTime.now().toUtc().toIso8601String(),
      };

      final response = await http.post(
        Uri.parse(testUrl.trim()),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(testPayload),
      ).timeout(const Duration(seconds: 8));

      return SubscriberSyncResult(
        success: response.statusCode >= 200 && response.statusCode < 300,
        message: response.statusCode >= 200 && response.statusCode < 300
            ? 'Endpoint reachable and accepted test payload (HTTP ${response.statusCode})'
            : 'Endpoint responded with HTTP ${response.statusCode}',
        statusCode: response.statusCode,
      );
    } catch (e) {
      return SubscriberSyncResult(
        success: false,
        message: 'Could not connect to endpoint: $e',
      );
    }
  }

  /// Flush any pending subscribers queued when offline or before endpoint URL was configured
  Future<void> flushPending() async {
    final prefs = await SharedPreferences.getInstance();
    final apiUrl = prefs.getString(_prefApiUrl);
    if (apiUrl == null || apiUrl.trim().isEmpty) return;

    final rawQueue = prefs.getString(_prefPendingQueue);
    if (rawQueue == null || rawQueue.isEmpty) return;

    List<dynamic> queue = [];
    try {
      queue = jsonDecode(rawQueue) as List<dynamic>;
    } catch (_) {
      return;
    }

    final remaining = <Map<String, dynamic>>[];
    final synced = prefs.getStringList(_prefSyncedEmails) ?? [];

    for (final item in queue) {
      if (item is Map<String, dynamic>) {
        final email = item['email']?.toString() ?? '';
        try {
          final res = await http.post(
            Uri.parse(apiUrl.trim()),
            headers: {'Content-Type': 'application/json'},
            body: jsonEncode(item),
          ).timeout(const Duration(seconds: 8));

          if (res.statusCode >= 200 && res.statusCode < 300) {
            if (email.isNotEmpty && !synced.contains(email)) {
              synced.add(email);
            }
          } else {
            remaining.add(item);
          }
        } catch (_) {
          remaining.add(item);
        }
      }
    }

    await prefs.setStringList(_prefSyncedEmails, synced);
    await prefs.setString(_prefPendingQueue, jsonEncode(remaining));
  }

  Future<void> _queuePending(Map<String, dynamic> item) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_prefPendingQueue);
    List<dynamic> queue = [];
    if (raw != null && raw.isNotEmpty) {
      try {
        queue = jsonDecode(raw);
      } catch (_) {}
    }
    final email = item['email']?.toString() ?? '';
    // Avoid duplicate queue entries
    queue.removeWhere((e) => e is Map && e['email'] == email);
    queue.add(item);
    await prefs.setString(_prefPendingQueue, jsonEncode(queue));
  }

  Future<void> _removeFromPending(String email) async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_prefPendingQueue);
    if (raw == null) return;
    try {
      List<dynamic> queue = jsonDecode(raw);
      queue.removeWhere((e) => e is Map && e['email'] == email);
      await prefs.setString(_prefPendingQueue, jsonEncode(queue));
    } catch (_) {}
  }
}
