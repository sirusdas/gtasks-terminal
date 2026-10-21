import 'package:google_generative_ai/google_generative_ai.dart';
import 'ai_provider.dart';
import 'ai_tools_registry.dart';

class GeminiProvider implements AiProvider {
  final String apiKey;
  final String modelName;
  final AiToolsRegistry tools;

  GeminiProvider({
    required this.apiKey,
    this.modelName = 'gemini-1.5-flash',
    AiToolsRegistry? tools,
  }) : tools = tools ?? AiToolsRegistry();

  @override
  String get name => 'Google Gemini ($modelName)';

  @override
  Future<AiChatResponse> chat({
    required String prompt,
    required List<Map<String, dynamic>> history,
    Map<String, dynamic>? context,
  }) async {
    if (apiKey.trim().isEmpty) {
      return AiChatResponse(
        reply: '⚠️ **Gemini API Key missing.**\n\n'
            'Please tap the Settings icon (⚙️) above and enter your free Gemini API Key from Google AI Studio.',
      );
    }

    final todayStr = DateTime.now().toIso8601String().substring(0, 10);
    final activeAccount = context?['active_account'] ?? 'All';
    final activeSpace = context?['active_space'] ?? 'All';

    final systemInstruction = Content.system(
      'You are GTasks AI Assistant, an ultra-fast productivity coordinator. '
      'Today is $todayStr. Current viewing account: "$activeAccount", space: "$activeSpace".\n'
      'Rules:\n'
      '1. You have direct tools to query, create, update, reschedule, complete tasks, and create/decompose custom focus mandalas.\n'
      '2. Always call `query_tasks` to check actual tasks rather than guessing.\n'
      '3. Tasks support Spaces and Sub-spaces (e.g. work › dev, personal › health).\n'
      '4. Return crisp, friendly markdown with emojis.',
    );

    final geminiTools = [
      Tool(functionDeclarations: [
        FunctionDeclaration(
          'query_tasks',
          'Search and filter user tasks by space, sub-space, status, priority, or date.',
          Schema(SchemaType.object, properties: {
            'query': Schema(SchemaType.string, description: 'Search keyword'),
            'status': Schema(SchemaType.string, description: 'pending, completed, or all'),
            'priority': Schema(SchemaType.string, description: 'critical, high, medium, low'),
            'space': Schema(SchemaType.string, description: 'Space filter e.g. work, personal'),
            'subspace': Schema(SchemaType.string, description: 'Sub-space filter e.g. dev, mobile'),
            'overdue_only': Schema(SchemaType.boolean, description: 'Only tasks with due date in the past'),
            'due_before': Schema(SchemaType.string, description: 'YYYY-MM-DD'),
            'due_after': Schema(SchemaType.string, description: 'YYYY-MM-DD'),
          }),
        ),
        FunctionDeclaration(
          'create_task',
          'Create a new task with title, priority, due date, spaces, and tags.',
          Schema(SchemaType.object, properties: {
            'title': Schema(SchemaType.string, description: 'Task title'),
            'description': Schema(SchemaType.string, description: 'Notes or description'),
            'due': Schema(SchemaType.string, description: 'Due date in YYYY-MM-DD'),
            'priority': Schema(SchemaType.string, description: 'critical, high, medium, low'),
            'space': Schema(SchemaType.string, description: 'Primary space name'),
            'subspace': Schema(SchemaType.string, description: 'Sub-space name'),
            'tags': Schema(SchemaType.array, items: Schema(SchemaType.string), description: 'List of tags'),
          }, requiredProperties: ['title']),
        ),
        FunctionDeclaration(
          'update_task',
          'Update task details like title, due date, status, or priority.',
          Schema(SchemaType.object, properties: {
            'task_id': Schema(SchemaType.string, description: 'ID of the task'),
            'title': Schema(SchemaType.string),
            'due': Schema(SchemaType.string, description: 'YYYY-MM-DD'),
            'status': Schema(SchemaType.string, description: 'pending or completed'),
            'priority': Schema(SchemaType.string),
          }, requiredProperties: ['task_id']),
        ),
        FunctionDeclaration(
          'complete_task',
          'Mark a task as completed.',
          Schema(SchemaType.object, properties: {
            'task_id': Schema(SchemaType.string, description: 'ID of the task'),
          }, requiredProperties: ['task_id']),
        ),
        FunctionDeclaration(
          'batch_reschedule',
          'Reschedule multiple task IDs to a new date.',
          Schema(SchemaType.object, properties: {
            'task_ids': Schema(SchemaType.array, items: Schema(SchemaType.string)),
            'new_due_date': Schema(SchemaType.string, description: 'YYYY-MM-DD'),
          }, requiredProperties: ['task_ids', 'new_due_date']),
        ),
        FunctionDeclaration(
          'list_spaces',
          'List all registered spaces and sub-spaces.',
          Schema(SchemaType.object, properties: {}),
        ),
        FunctionDeclaration(
          'get_productivity_report',
          'Generate productivity metrics, completion percentage, and space breakdown.',
          Schema(SchemaType.object, properties: {
            'timeframe': Schema(SchemaType.string, description: 'today, week, month'),
          }),
        ),
        FunctionDeclaration(
          'create_mandala',
          'Create or decompose into a focused custom mandala with a center goal and peripheral petals/actions.',
          Schema(SchemaType.object, properties: {
            'title': Schema(SchemaType.string, description: 'Title of the mandala'),
            'center_goal': Schema(SchemaType.string, description: 'Central goal/theme for the bindu'),
            'geometry': Schema(SchemaType.string, description: 'padma (lotus), chakra (8-spoke wheel), bhupura (square gate), or sriyantra (triangles)'),
            'items': Schema(SchemaType.array, items: Schema(SchemaType.string), description: 'List of focus tasks, petals, or sub-actions'),
          }, requiredProperties: ['title', 'center_goal', 'items']),
        ),
      ]),
    ];

    final model = GenerativeModel(
      model: modelName,
      apiKey: apiKey,
      systemInstruction: systemInstruction,
      tools: geminiTools,
    );

    // Build history contents
    final contents = <Content>[];
    for (final m in history) {
      final role = m['role'] == 'user' ? 'user' : 'model';
      contents.add(Content(role, [TextPart(m['content'].toString())]));
    }
    contents.add(Content.text(prompt));

    final executedToolCalls = <Map<String, dynamic>>[];
    final executedToolResults = <Map<String, dynamic>>[];

    // Function calling loop (up to 3 turns)
    for (int turn = 0; turn < 3; turn++) {
      final response = await model.generateContent(contents);
      final functionCalls = response.functionCalls.toList();

      if (functionCalls.isEmpty) {
        final replyText = response.text ?? '';
        return AiChatResponse(
          reply: replyText.isNotEmpty ? replyText : 'Operation completed.',
          toolCalls: executedToolCalls,
          toolResults: executedToolResults,
        );
      }

      // Execute tool
      final call = functionCalls.first;
      final callName = call.name;
      final callArgs = Map<String, dynamic>.from(call.args);

      executedToolCalls.add({'name': callName, 'args': callArgs});

      final resultStr = await tools.executeTool(callName, callArgs);
      executedToolResults.add({'name': callName, 'result': resultStr});

      // Append assistant's function call response and tool result
      contents.add(Content('model', [FunctionCall(callName, callArgs)]));
      contents.add(Content('function', [
        FunctionResponse(callName, {'output': resultStr}),
      ]));
    }

    return AiChatResponse(
      reply: 'Executed tools successfully.',
      toolCalls: executedToolCalls,
      toolResults: executedToolResults,
    );
  }
}
