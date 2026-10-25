import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/models/task_item.dart';
import 'package:gtasks_app/models/task_tab.dart';
import 'package:gtasks_app/providers/task_provider.dart';
import 'package:gtasks_app/api/api_client.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

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
        selectedSpace: 'engineering',
        selectedSubspace: 'mobile',
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
      expect(provider.selectedSpace, 'engineering');
      expect(provider.selectedSubspace, 'mobile');
      expect(provider.selectedPriority, 'high');
      expect(provider.hideRecurring, true);
      expect(provider.sortField, 'due');
      expect(provider.sortAscending, true);
    });

    test('applyFiltersBatch clears space filter when clearSpace is true', () {
      final provider = TaskProvider(
        apiClient: ApiClient(baseUrl: 'http://localhost:48275'),
      );

      provider.setSelectedSpace('work', subspace: 'frontend');
      expect(provider.selectedSpace, 'work');
      expect(provider.selectedSubspace, 'frontend');

      provider.applyFiltersBatch(clearSpace: true);
      expect(provider.selectedSpace, isNull);
      expect(provider.selectedSubspace, isNull);
    });

    test('switching between all-account tab and single-account tab immediately updates sidebar aggregates and filters', () {
      final provider = TaskProvider(
        apiClient: ApiClient(baseUrl: 'http://localhost:48275'),
      );

      // Add a single-account tab
      provider.addNewTab(
        title: 'Work Only',
        account: 'work_acc',
        space: 'Backend',
        tag: 'urgent',
      );

      expect(provider.activeTab?.title, 'Work Only');
      expect(provider.selectedAccount, 'work_acc');
      expect(provider.selectedSpace, 'Backend');
      expect(provider.selectedTags, contains('urgent'));

      // Switch to default all-tasks tab
      provider.switchToTab(0);
      expect(provider.activeTabIndex, 0);
      expect(provider.selectedAccount, 'all');
      expect(provider.selectedAccounts, isEmpty);
      expect(provider.selectedSpace, isNull);
      expect(provider.selectedTags, isEmpty);

      // Switch back to Work Only tab
      provider.switchToTab(provider.tabs.length - 1);
      expect(provider.selectedAccount, 'work_acc');
      expect(provider.selectedSpace, 'Backend');
      expect(provider.selectedTags, contains('urgent'));
    });

    test('TaskProvider Saved Views CRUD operations work properly', () async {
      final provider = TaskProvider(
        apiClient: ApiClient(baseUrl: 'http://localhost:48275'),
        isStandalone: true,
      );

      final mandalaTab = TaskTab(
        id: 'tab_mandala_view',
        title: 'Project Mandala',
        viewMode: 'mandala',
        selectedSpace: 'Engineering',
        mandalaGrouping: 'spaces',
        mandalaGeometry: 'padma',
        mandalaTheme: 'cyberpunk',
      );

      // Save view
      await provider.saveView(mandalaTab);
      expect(provider.savedViews.length, 1);
      expect(provider.savedViews.first.title, 'Project Mandala');
      expect(provider.savedViews.first.viewMode, 'mandala');
      expect(provider.savedViews.first.mandalaGeometry, 'padma');
      expect(provider.isTabSaved(mandalaTab), isTrue);

      final savedViewId = provider.savedViews.first.id;

      // Rename saved view
      await provider.renameSavedView(savedViewId, 'Engineering Mandala Atlas');
      expect(provider.savedViews.first.title, 'Engineering Mandala Atlas');

      // Open saved view
      final initialTabCount = provider.tabs.length;
      provider.openSavedView(provider.savedViews.first, forceNewTab: true);
      expect(provider.tabs.length, initialTabCount + 1);
      expect(provider.activeTab?.title, 'Engineering Mandala Atlas');
      expect(provider.activeTab?.viewMode, 'mandala');
      expect(provider.activeTab?.mandalaGeometry, 'padma');

      // Delete saved view
      await provider.deleteSavedView(savedViewId);
      expect(provider.savedViews, isEmpty);
    });
  });
}
