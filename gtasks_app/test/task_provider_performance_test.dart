import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/models/task_item.dart';
import 'package:gtasks_app/providers/task_provider.dart';
import 'package:gtasks_app/api/api_client.dart';

void main() {
  group('TaskItem Precomputed Fields Tests', () {
    test('TaskItem extracts cleanNotes and allTags once upon construction', () {
      final task = TaskItem(
        id: 't1',
        title: 'Complete optimization',
        description: 'Review performance\n\n---\n[backend][mobile]',
        status: 'pending',
        tags: ['important'],
      );

      expect(task.cleanNotes, 'Review performance');
      expect(task.allTags, contains('important'));
      expect(task.allTags, contains('backend'));
      expect(task.allTags, contains('mobile'));
    });
  });

  group('TaskProvider Batch Filter & Cache Tests', () {
    test('applyFiltersBatch updates all filter properties atomically', () {
      final provider = TaskProvider(
        apiClient: ApiClient(baseUrl: 'http://localhost:48275'),
      );

      int notifyCount = 0;
      provider.addListener(() {
        notifyCount++;
      });

      provider.applyFiltersBatch(
        statusFilter: 'completed',
        selectedLists: {'Work', 'Personal'},
        selectedTags: {'feature'},
        selectedPriority: 'high',
        hideRecurring: true,
        sortField: 'due',
        sortAscending: true,
      );

      expect(notifyCount, 1);
      expect(provider.statusFilter, 'completed');
      expect(provider.selectedLists, contains('Work'));
      expect(provider.selectedLists, contains('Personal'));
      expect(provider.selectedTags, contains('feature'));
      expect(provider.selectedPriority, 'high');
      expect(provider.hideRecurring, true);
      expect(provider.sortField, 'due');
      expect(provider.sortAscending, true);
    });
  });
}
