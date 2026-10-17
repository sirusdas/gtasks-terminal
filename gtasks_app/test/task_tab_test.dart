import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/models/task_item.dart';
import 'package:gtasks_app/models/task_tab.dart';

void main() {
  group('TaskTab Model Tests', () {
    test('TaskTab serialize and deserialize correctly', () {
      final tab = TaskTab(
        id: 'tab_test_1',
        title: 'Work Project',
        iconCodePoint: Icons.work.codePoint,
        colorValue: Colors.blue.value,
        selectedSpace: 'Work',
        selectedSubspace: 'Backend',
        selectedPriority: 'high',
        selectedLists: {'Engineering'},
        selectedTags: {'urgent', 'api'},
        searchQuery: 'deploy',
        statusFilter: 'pending',
      );

      final json = tab.toJson();
      final restored = TaskTab.fromJson(json);

      expect(restored.id, 'tab_test_1');
      expect(restored.title, 'Work Project');
      expect(restored.selectedSpace, 'Work');
      expect(restored.selectedSubspace, 'Backend');
      expect(restored.selectedPriority, 'high');
      expect(restored.selectedLists, contains('Engineering'));
      expect(restored.selectedTags, contains('urgent'));
      expect(restored.selectedTags, contains('api'));
      expect(restored.searchQuery, 'deploy');
      expect(restored.statusFilter, 'pending');
    });

    test('TaskTab toWidgetJson maps filter metadata properly', () {
      final spaceTab = TaskTab(
        id: 'tab_space',
        title: 'Engineering',
        selectedSpace: 'Tech',
        selectedSubspace: 'DevOps',
      );
      final widgetJson = spaceTab.toWidgetJson();
      expect(widgetJson['id'], 'tab_space');
      expect(widgetJson['title'], 'Engineering');
      expect(widgetJson['filterType'], 'space');
      expect(widgetJson['filterVal'], 'Tech › DevOps');

      final priorityTab = TaskTab(
        id: 'tab_prio',
        title: 'Urgent',
        selectedPriority: 'critical',
      );
      final prioWidgetJson = priorityTab.toWidgetJson();
      expect(prioWidgetJson['filterType'], 'priority');
      expect(prioWidgetJson['filterVal'], 'critical');
    });

    test('TaskTab copyWith supports clear flags', () {
      final tab = TaskTab(
        id: 'tab_1',
        title: 'Base',
        selectedSpace: 'Home',
        selectedSubspace: 'Kitchen',
        selectedPriority: 'low',
        dateRange: DateTimeRange(start: DateTime(2025, 1, 1), end: DateTime(2025, 1, 2)),
      );

      final cleared = tab.copyWith(
        clearSpace: true,
        clearPriority: true,
        clearDateRange: true,
      );

      expect(cleared.selectedSpace, isNull);
      expect(cleared.selectedSubspace, isNull);
      expect(cleared.selectedPriority, isNull);
      expect(cleared.dateRange, isNull);
    });

    test('TaskTab computeTaskCount filters tasks accurately', () {
      final tasks = [
        TaskItem(
          id: '1',
          title: 'Buy groceries',
          description: '',
          status: 'pending',
          spaces: {'Personal': ['Shopping']},
          calculatedPriority: 'medium',
        ),
        TaskItem(
          id: '2',
          title: 'Fix production bug',
          description: '',
          status: 'pending',
          spaces: {'Work': ['Backend']},
          calculatedPriority: 'critical',
        ),
        TaskItem(
          id: '3',
          title: 'Design mockup',
          description: '',
          status: 'pending',
          spaces: {'Work': ['UI']},
          calculatedPriority: 'high',
        ),
        TaskItem(
          id: '4',
          title: 'Finished report',
          description: '',
          status: 'completed',
          spaces: {'Work': ['Backend']},
          calculatedPriority: 'high',
        ),
      ];

      final workTab = TaskTab(
        id: 'work_tab',
        title: 'Work Tasks',
        selectedSpace: 'Work',
        statusFilter: 'pending',
      );
      expect(workTab.computeTaskCount(tasks), 2);

      final highPrioTab = TaskTab(
        id: 'prio_tab',
        title: 'High Prio',
        selectedPriority: 'high',
        statusFilter: 'pending',
      );
      expect(highPrioTab.computeTaskCount(tasks), 2); // Task 2 (critical) and Task 3 (high)

      final backendTab = TaskTab(
        id: 'backend_tab',
        title: 'Work Backend',
        selectedSpace: 'Work',
        selectedSubspace: 'Backend',
        statusFilter: 'pending',
      );
      expect(backendTab.computeTaskCount(tasks), 1); // Only Task 2
    });
  });
}
