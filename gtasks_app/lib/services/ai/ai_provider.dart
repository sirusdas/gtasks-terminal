abstract class AiProvider {
  String get name;
  Future<AiChatResponse> chat({
    required String prompt,
    required List<Map<String, dynamic>> history,
    Map<String, dynamic>? context,
  });
}

class AiChatResponse {
  final String reply;
  final List<Map<String, dynamic>> toolCalls;
  final List<Map<String, dynamic>> toolResults;
  final String? workflowExecuted;

  AiChatResponse({
    required this.reply,
    this.toolCalls = const [],
    this.toolResults = const [],
    this.workflowExecuted,
  });
}
