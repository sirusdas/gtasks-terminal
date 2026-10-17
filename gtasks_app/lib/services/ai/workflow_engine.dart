import 'ai_tools_registry.dart';

class WorkflowEngine {
  final AiToolsRegistry tools;

  WorkflowEngine(this.tools);

  Future<String> execute(String workflowName, {Map<String, dynamic>? parameters}) async {
    final name = workflowName.toLowerCase().replaceAll('/', '').trim();
    final todayStr = DateTime.now().toIso8601String().substring(0, 10);

    if (name == 'morning' || name == 'morning_briefing') {
      final report = await tools.executeTool('get_productivity_report', {'timeframe': 'today'});
      final dueToday = await tools.executeTool('query_tasks', {
        'status': 'pending',
        'due_before': todayStr,
        'due_after': todayStr,
        'limit': 15,
      });
      final overdue = await tools.executeTool('query_tasks', {
        'status': 'pending',
        'overdue_only': true,
        'limit': 15,
      });

      return '☀️ **Morning Briefing for $todayStr**\n\n'
          '$report\n\n'
          '**Tasks Due Today:**\n$dueToday\n\n'
          '**Overdue Attention Needed:**\n$overdue';
    } else if (name == 'evening' || name == 'evening_review') {
      final completed = await tools.executeTool('query_tasks', {
        'status': 'completed',
        'limit': 15,
      });
      final overdue = await tools.executeTool('query_tasks', {
        'status': 'pending',
        'overdue_only': true,
        'limit': 15,
      });

      return '🌙 **Evening Review for $todayStr**\n\n'
          '**Completed Today:**\n$completed\n\n'
          '**Pending / Rollover Candidates:**\n$overdue\n\n'
          '💡 Tip: Type or ask me "Reschedule overdue tasks to tomorrow" to roll them over!';
    } else if (name == 'triage' || name == 'inbox_triage') {
      final unspaced = await tools.executeTool('query_tasks', {
        'status': 'pending',
        'limit': 20,
      });
      final spaces = await tools.executeTool('list_spaces', {});

      return '⚡ **Inbox Triage**\n\n'
          '**Unsorted Tasks:**\n$unspaced\n\n'
          '**Available Spaces to assign:**\n$spaces';
    } else if (name == 'breakdown' || name == 'project_breakdown') {
      final goal = parameters?['goal'] ?? 'New Project';
      return '🔨 Project breakdown prepared for: "$goal". Tell me your desired deadlines and I will generate subtasks with spaces!';
    }

    return 'Unknown workflow: $workflowName. Available: /morning, /evening, /triage, /breakdown';
  }
}
