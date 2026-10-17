import 'dart:convert';
import 'package:http/http.dart' as http;
import 'ai_provider.dart';

class DashboardProxyProvider implements AiProvider {
  final String baseUrl;
  final String sessionId;
  final String? modelName;

  DashboardProxyProvider({
    required this.baseUrl,
    this.sessionId = 'default',
    this.modelName,
  });

  @override
  String get name => 'GTasks Server Proxy';

  @override
  Future<AiChatResponse> chat({
    required String prompt,
    required List<Map<String, dynamic>> history,
    Map<String, dynamic>? context,
  }) async {
    final cleanUrl = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl;
    final uri = Uri.parse('$cleanUrl/api/ai/chat');

    final response = await http.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'message': prompt,
        'session_id': sessionId,
        'context': context ?? {},
      }),
    );

    if (response.statusCode >= 200 && response.statusCode < 300) {
      final data = jsonDecode(response.body);
      return AiChatResponse(
        reply: data['reply']?.toString() ?? '',
        toolCalls: (data['tool_calls'] as List?)?.map((e) => Map<String, dynamic>.from(e)).toList() ?? [],
        toolResults: (data['tool_results'] as List?)?.map((e) => Map<String, dynamic>.from(e)).toList() ?? [],
        workflowExecuted: data['workflow_executed']?.toString(),
      );
    } else {
      throw Exception('Server returned ${response.statusCode}: ${response.body}');
    }
  }
}
