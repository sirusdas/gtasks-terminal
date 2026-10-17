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

  test('TaskItem parses and serializes subtasks with parentId and position', () {
    final subtaskJson = {
      'id': 'sub-456',
      'title': 'Subtask of Deploy GTasks',
      'status': 'pending',
      'parent_id': 'test-123',
      'position': 1,
      'account': 'Personal',
      'due': '2026-10-18T00:00:00Z',
    };

    final subtask = TaskItem.fromJson(subtaskJson);
    expect(subtask.id, 'sub-456');
    expect(subtask.parentId, 'test-123');
    expect(subtask.isSubtask, true);
    expect(subtask.position, 1);

    final serialized = subtask.toJson();
    expect(serialized['parent_id'], 'test-123');
    expect(serialized['position'], 1);

    final copied = subtask.copyWith(title: 'Updated Subtask Title');
    expect(copied.parentId, 'test-123');
    expect(copied.isSubtask, true);
    expect(copied.title, 'Updated Subtask Title');
  });
}
