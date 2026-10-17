import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/providers/ai_chat_provider.dart';
import 'package:gtasks_app/services/ai/ai_provider.dart';
import 'package:gtasks_app/services/ai/ai_tools_registry.dart';
import 'package:gtasks_app/services/ai/workflow_engine.dart';

void main() {
  group('AI Architecture Unit Tests', () {
    test('AiChatMessage parses JSON map correctly', () {
      final msg = AiChatMessage.fromMap({
        'id': 'msg_123',
        'session_id': 'sess_1',
        'role': 'assistant',
        'content': 'I have created the task for you.',
        'tool_calls': '[{"name": "create_task", "arguments": {"title": "Test Task"}}]',
        'tool_results': '[{"name": "create_task", "result": {"success": true}}]',
        'created_at': '2026-10-16T08:00:00.000Z',
      });

      expect(msg.id, 'msg_123');
      expect(msg.sessionId, 'sess_1');
      expect(msg.role, 'assistant');
      expect(msg.content, 'I have created the task for you.');
      expect(msg.toolCalls?.length, 1);
      expect((msg.toolCalls![0] as Map)['name'], 'create_task');
      expect(msg.toolResults?.length, 1);
    });

    test('AiToolsRegistry declares expected core tool functions', () {
      final registry = AiToolsRegistry();
      final toolNames = registry.toolNames.toSet();

      expect(toolNames.contains('query_tasks'), isTrue);
      expect(toolNames.contains('create_task'), isTrue);
      expect(toolNames.contains('update_task'), isTrue);
      expect(toolNames.contains('complete_task'), isTrue);
      expect(toolNames.contains('batch_reschedule'), isTrue);
      expect(toolNames.contains('batch_complete'), isTrue);
      expect(toolNames.contains('list_spaces'), isTrue);
      expect(toolNames.contains('get_productivity_report'), isTrue);
    });

    test('WorkflowEngine handles breakdown workflow template', () async {
      final registry = AiToolsRegistry();
      final engine = WorkflowEngine(registry);

      final breakdownResult = await engine.execute('/breakdown', parameters: {'goal': 'Build Website'});
      expect(breakdownResult.contains('Build Website'), isTrue);
      expect(breakdownResult.contains('Project breakdown prepared'), isTrue);
    });

    test('AiChatResponse encapsulates reply and tools', () {
      final response = AiChatResponse(
        reply: 'Tasks updated successfully',
        toolCalls: [
          {'name': 'batch_reschedule', 'arguments': {'days_offset': 1}}
        ],
        toolResults: [
          {'name': 'batch_reschedule', 'result': 'Rescheduled 3 tasks'}
        ],
        workflowExecuted: '/morning',
      );

      expect(response.reply, 'Tasks updated successfully');
      expect(response.toolCalls.length, 1);
      expect(response.workflowExecuted, '/morning');
    });
  });
}
