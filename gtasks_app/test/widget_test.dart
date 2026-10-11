import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/models/task_item.dart';

void main() {
  test('TaskItem parses JSON successfully', () {
    final json = {
      'id': 'test-123',
      'title': 'Deploy GTasks',
      'description': 'Run production deployment',
      'status': 'needsAction',
      'tags': ['devops', 'urgent'],
      'calculated_priority': 'high',
      'account': 'Personal',
      'due': '2026-10-15T00:00:00Z',
    };

    final task = TaskItem.fromJson(json);

    expect(task.id, 'test-123');
    expect(task.title, 'Deploy GTasks');
    expect(task.isCompleted, false);
    expect(task.tags, contains('urgent'));
    expect(task.calculatedPriority, 'high');
  });
}
