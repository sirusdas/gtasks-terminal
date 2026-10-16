import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import '../widgets/task_card.dart';
import '../widgets/task_compact_row.dart';
import '../widgets/task_grid_card.dart';
import '../widgets/task_grid_compact_card.dart';
import '../widgets/settings_modal.dart';
import '../widgets/add_account_modal.dart';
import '../widgets/tasks_sidebar_drawer.dart';
import '../widgets/task_filter_modal.dart';
import '../widgets/task_editor_dialog.dart';
import '../widgets/sync_progress_dialog.dart';
import '../../services/widget_service.dart';
import '../../providers/settings_provider.dart';
import '../../models/task_view_context.dart';
import '../../models/task_item.dart';
import 'reports_screen.dart';
import 'ai_chat_screen.dart';
import '../widgets/task_detail_modal.dart';

class AppTab {
  final String id;
  final String title;
  final IconData icon;
  final Color? accentColor;
  final String? space;
  final String? filterType;
  final String? filterVal;

  const AppTab({
    required this.id,
    required this.title,
    required this.icon,
    this.accentColor,
    this.space,
    this.filterType,
    this.filterVal,
  });
}

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _tabScrollController = ScrollController();
  Timer? _searchDebounce;
  String _activeTabId = 'all';
  String? _pendingPreviewTaskId;

  @override
  void initState() {
    super.initState();
    WidgetService.init();
    WidgetService.setActionListener((action) {
      if (mounted) _handleWidgetAction(action);
    });

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final provider = context.read<TaskProvider>();
      // Check if launched from widget with initial action immediately
      final initialAction = await WidgetService.getInitialAction();
      if (initialAction != null && mounted) {
        _handleWidgetAction(initialAction);
      }

      await provider.loadInitialData();
      if (!mounted) return;
      _checkAccountStatusAtStartup(provider);
      if (_pendingPreviewTaskId != null) {
        final pendingId = _pendingPreviewTaskId!;
        _pendingPreviewTaskId = null;
        _openTaskPreviewById(pendingId);
      }
    });
  }

  void _handleWidgetAction(String action) {
    if (!mounted) return;
    if (action == 'open_task_editor') {
      _showAddTaskSheet(context, isFromWidget: true);
    } else if (action.startsWith('open_ai_chat')) {
      final provider = context.read<TaskProvider>();
      TaskViewContext viewCtx;
      if (action.contains(':')) {
        final parts = action.split(':');
        final filterType = parts.length > 1 ? parts[1] : '';
        final filterVal = parts.length > 2 ? parts[2] : '';

        List<TaskItem> filteredList = provider.tasks;
        String? selectedSpace;
        String? selectedSubspace;
        Set<String> selectedLists = {};
        Set<String> selectedTags = {};

        if (filterType == 'space') {
          selectedSpace = filterVal;
          filteredList = provider.allTasksUnfiltered.where((t) => t.spaces.containsKey(filterVal)).toList();
        } else if (filterType == 'subspace') {
          final subParts = filterVal.split(' › ');
          selectedSpace = subParts[0];
          selectedSubspace = subParts.length > 1 ? subParts[1] : null;
          filteredList = provider.allTasksUnfiltered.where((t) =>
              t.spaces.containsKey(selectedSpace) &&
              (selectedSubspace == null || (t.spaces[selectedSpace]?.contains(selectedSubspace) ?? false))
          ).toList();
        } else if (filterType == 'list') {
          selectedLists = {filterVal};
          filteredList = provider.allTasksUnfiltered.where((t) => t.listTitle == filterVal).toList();
        } else if (filterType == 'tag') {
          selectedTags = {filterVal};
          filteredList = provider.allTasksUnfiltered.where((t) => t.allTags.contains(filterVal)).toList();
        }

        viewCtx = TaskViewContext(
          visibleTasks: List.unmodifiable(filteredList),
          totalTasksCount: provider.allTasksUnfiltered.length,
          selectedSpace: selectedSpace,
          selectedSubspace: selectedSubspace,
          selectedLists: selectedLists,
          selectedTags: selectedTags,
          statusFilter: provider.statusFilter,
        );
      } else {
        viewCtx = _buildCurrentViewContext(provider);
      }

      Navigator.push(
        context,
        MaterialPageRoute(
          builder: (_) => AiChatScreen(initialContext: viewCtx),
          fullscreenDialog: true,
        ),
      );
    } else if (action.startsWith('open_task_preview:')) {
      final taskId = action.substring('open_task_preview:'.length);
      _openTaskPreviewById(taskId);
    } else if (action.startsWith('open_tab:')) {
      final parts = action.split(':');
      final tabId = parts.length > 1 ? parts[1] : '';
      final filterType = parts.length > 2 ? parts[2] : '';
      final filterVal = parts.length > 3 ? parts[3] : '';
      _openTabByAction(tabId, filterType, filterVal);
    }
  }

  void _openTaskPreviewById(String taskId) {
    if (taskId.isEmpty) return;
    final provider = context.read<TaskProvider>();
    if (provider.isLoading && provider.allTasksUnfiltered.isEmpty) {
      _pendingPreviewTaskId = taskId;
      return;
    }
    TaskItem? targetTask;
    try {
      targetTask = provider.allTasksUnfiltered.firstWhere((t) => t.id == taskId);
    } catch (_) {
      try {
        targetTask = provider.tasks.firstWhere((t) => t.id == taskId);
      } catch (_) {
        targetTask = null;
      }
    }
    if (targetTask != null && mounted) {
      showDialog(
        context: context,
        builder: (_) => TaskDetailModal(
          task: targetTask!,
          onEdit: () => _showEditTaskSheet(context, targetTask!),
          onDelete: () => provider.deleteTask(targetTask!.id),
        ),
      );
    }
  }

  void _openTabByAction(String tabId, String filterType, String filterVal) {
    final provider = context.read<TaskProvider>();
    final allTabs = _buildAvailableTabs(provider);
    final match = allTabs.firstWhere(
      (t) => t.id == tabId || (filterType.isNotEmpty && t.filterType == filterType && t.filterVal == filterVal),
      orElse: () => allTabs.first,
    );
    _selectTab(match, allTabs);
  }

  List<AppTab> _buildAvailableTabs(TaskProvider provider) {
    final tabs = <AppTab>[
      const AppTab(
        id: 'all',
        title: 'All Tasks',
        icon: Icons.all_inbox_rounded,
        accentColor: Colors.blueAccent,
      ),
      const AppTab(
        id: 'today',
        title: 'Today & Due',
        icon: Icons.today_rounded,
        accentColor: Colors.amber,
        filterType: 'date',
        filterVal: 'today',
      ),
      const AppTab(
        id: 'priority',
        title: 'High Priority',
        icon: Icons.local_fire_department_rounded,
        accentColor: Colors.deepOrangeAccent,
        filterType: 'priority',
        filterVal: 'high',
      ),
    ];

    for (final spaceName in provider.spacesWithCounts.keys) {
      tabs.add(AppTab(
        id: 'space:$spaceName',
        title: spaceName,
        icon: Icons.rocket_launch_rounded,
        accentColor: Colors.purpleAccent,
        space: spaceName,
        filterType: 'space',
        filterVal: spaceName,
      ));
    }

    return tabs;
  }

  int _getTabCount(AppTab tab, TaskProvider provider) {
    if (tab.id == 'all') {
      return provider.allTasksUnfiltered.where((t) => !t.isCompleted).length;
    } else if (tab.id == 'today') {
      final now = DateTime.now();
      final todayStr = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
      return provider.allTasksUnfiltered.where((t) {
        if (t.isCompleted || t.due == null || t.due!.isEmpty) return false;
        final duePart = t.due!.length >= 10 ? t.due!.substring(0, 10) : t.due!;
        return duePart.compareTo(todayStr) <= 0;
      }).length;
    } else if (tab.id == 'priority') {
      return provider.allTasksUnfiltered.where((t) {
        if (t.isCompleted) return false;
        final p = t.calculatedPriority.toLowerCase();
        return p == 'critical' || p == 'high';
      }).length;
    } else if (tab.space != null) {
      return provider.spacesWithCounts[tab.space!] ?? 0;
    }
    return 0;
  }

  void _selectTab(AppTab tab, List<AppTab> allTabs) {
    setState(() {
      _activeTabId = tab.id;
    });

    final provider = context.read<TaskProvider>();
    if (tab.id == 'all') {
      provider.clearSpaceFilter();
      provider.setPriorityFilter(null);
      provider.setDateFilter(provider.dateField, null);
    } else if (tab.id == 'today') {
      provider.clearSpaceFilter();
      provider.setPriorityFilter(null);
      final now = DateTime.now();
      final endOfToday = DateTime(now.year, now.month, now.day, 23, 59, 59);
      provider.setDateFilter('due', DateTimeRange(
        start: DateTime(2000, 1, 1),
        end: endOfToday,
      ));
    } else if (tab.id == 'priority') {
      provider.clearSpaceFilter();
      provider.setDateFilter(provider.dateField, null);
      provider.setPriorityFilter('high');
    } else if (tab.space != null) {
      provider.setDateFilter(provider.dateField, null);
      provider.setPriorityFilter(null);
      provider.setSpaceFilter(tab.space!);
    }

    final tabIndex = allTabs.indexWhere((t) => t.id == tab.id);
    if (tabIndex != -1 && _tabScrollController.hasClients) {
      final targetOffset = (tabIndex * 110.0).clamp(0.0, _tabScrollController.position.maxScrollExtent);
      _tabScrollController.animateTo(
        targetOffset,
        duration: const Duration(milliseconds: 250),
        curve: Curves.easeOutCubic,
      );
    }
  }

  void _stepTab(int delta, List<AppTab> allTabs) {
    if (allTabs.isEmpty) return;
    final currentIndex = allTabs.indexWhere((t) => t.id == _activeTabId);
    final validIndex = currentIndex == -1 ? 0 : currentIndex;
    final nextIndex = (validIndex + delta + allTabs.length) % allTabs.length;
    _selectTab(allTabs[nextIndex], allTabs);
  }

  void _checkAccountStatusAtStartup(TaskProvider provider) {
    if (provider.errorMessage != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: Colors.red.shade800,
          duration: const Duration(seconds: 5),
          content: Row(
            children: [
              const Icon(Icons.error_outline, color: Colors.white, size: 20),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  'Connection error: ${provider.errorMessage}',
                  style: const TextStyle(fontSize: 12),
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          action: SnackBarAction(
            label: 'Settings',
            textColor: Colors.amberAccent,
            onPressed: () {
              showDialog(
                context: context,
                builder: (_) => const SettingsModal(),
              );
            },
          ),
        ),
      );
    } else if (provider.accounts.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          backgroundColor: Colors.amber.shade900,
          duration: const Duration(seconds: 5),
          content: const Row(
            children: [
              Icon(Icons.account_circle_outlined, color: Colors.white, size: 20),
              SizedBox(width: 8),
              Expanded(
                child: Text(
                  'No accounts configured. Tap to connect Google account.',
                  style: TextStyle(fontSize: 13),
                ),
              ),
            ],
          ),
          action: SnackBarAction(
            label: 'Add Account',
            textColor: Colors.white,
            onPressed: () {
              showDialog(
                context: context,
                builder: (_) => const AddGoogleAccountModal(),
              );
            },
          ),
        ),
      );
    }
  }

  @override
  void dispose() {
    WidgetService.setActionListener(null);
    _searchDebounce?.cancel();
    _searchController.dispose();
    _tabScrollController.dispose();
    super.dispose();
  }

  void _showAddTaskSheet(BuildContext context, {bool isFromWidget = false}) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => TaskEditorDialog(
          isFullScreen: true,
          isFromWidget: isFromWidget,
        ),
      ),
    );
  }

  void _showEditTaskSheet(BuildContext context, dynamic task) {
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => TaskEditorDialog(
          task: task,
          isFullScreen: true,
          isFromWidget: false,
        ),
      ),
    );
  }

  TaskViewContext _buildCurrentViewContext(TaskProvider provider) {
    return TaskViewContext(
      visibleTasks: List.unmodifiable(provider.tasks),
      totalTasksCount: provider.allTasksUnfiltered.length,
      searchQuery: provider.searchQuery.isNotEmpty ? provider.searchQuery : null,
      selectedSpace: provider.selectedSpace,
      selectedSubspace: provider.selectedSubspace,
      selectedPriority: provider.selectedPriority,
      selectedLists: Set.unmodifiable(provider.selectedLists),
      selectedTags: Set.unmodifiable(provider.selectedTags),
      statusFilter: provider.statusFilter,
      dateRange: provider.dateRange,
      dateField: provider.dateField,
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TaskProvider>();
    final theme = Theme.of(context);
    final hasViewFilters = provider.hasActiveFilters || provider.searchQuery.isNotEmpty;

    // Automatically synchronize active tab state with provider active filters
    if (provider.selectedSpace != null) {
      final spaceTabId = 'space:${provider.selectedSpace}';
      if (_activeTabId != spaceTabId) {
        _activeTabId = spaceTabId;
      }
    } else if (provider.selectedPriority != null && (provider.selectedPriority == 'high' || provider.selectedPriority == 'critical')) {
      if (_activeTabId != 'priority') {
        _activeTabId = 'priority';
      }
    } else if (provider.dateRange != null && provider.dateField == 'due') {
      if (_activeTabId != 'today') {
        _activeTabId = 'today';
      }
    } else if (!provider.hasActiveFilters && _activeTabId != 'all') {
      _activeTabId = 'all';
    }

    return Scaffold(
      drawer: const TasksSidebarDrawer(),
      appBar: AppBar(
        title: const Text('GTasks', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
          // AI Assistant & Chat Bot button with view-context badge
          Badge(
            isLabelVisible: hasViewFilters,
            backgroundColor: Colors.amber,
            textColor: Colors.black,
            label: Text(
              '${provider.tasks.length}',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 10),
            ),
            child: IconButton(
              icon: const Icon(Icons.auto_awesome, color: Colors.amber),
              tooltip: hasViewFilters
                  ? 'AI Assistant (Scoped to this view: ${provider.tasks.length} tasks)'
                  : 'AI Assistant & Chat Bot',
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => AiChatScreen(
                      initialContext: _buildCurrentViewContext(provider),
                    ),
                    fullscreenDialog: true,
                  ),
                );
              },
            ),
          ),
          // Filter drawer toggle button with active badge
          Badge(
            isLabelVisible: provider.activeFilterCount > 0,
            label: Text('${provider.activeFilterCount}'),
            child: IconButton(
              icon: const Icon(Icons.filter_list),
              tooltip: 'Filters & Sort',
              onPressed: () {
                showModalBottomSheet(
                  context: context,
                  isScrollControlled: true,
                  backgroundColor: Colors.transparent,
                  builder: (_) => const TaskFilterModal(),
                );
              },
            ),
          ),
          IconButton(
            icon: const Icon(Icons.analytics_outlined),
            tooltip: 'Reports & Analytics',
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => ReportsScreen(apiClient: provider.apiClient),
                ),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.settings_outlined),
            tooltip: 'Settings & Accounts',
            onPressed: () {
              showDialog(
                context: context,
                builder: (_) => const SettingsModal(),
              );
            },
          ),
          PopupMenuButton<String>(
            icon: provider.isLoading
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.sync),
            tooltip: 'Google Sync Options',
            onSelected: (action) {
              final isAll = action == 'sync_all';
              SyncProgressDialog.show(context, isFullSync: isAll);
            },
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: 'sync_all',
                child: ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.cloud_sync, color: Colors.blueAccent),
                  title: Text('Sync All (Full --all)', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: Text('Pull all tasks & lists from Google Tasks'),
                ),
              ),
              const PopupMenuItem(
                value: 'quick_sync',
                child: ListTile(
                  dense: true,
                  contentPadding: EdgeInsets.zero,
                  leading: Icon(Icons.sync, color: Colors.teal),
                  title: Text('Quick Sync'),
                  subtitle: Text('Sync recent changes'),
                ),
              ),
            ],
          ),
          Consumer<SettingsProvider>(
            builder: (context, settings, _) {
              final mode = settings.taskViewMode;
              final icon = mode == 'two_column_compact'
                  ? Icons.view_compact
                  : mode == 'two_column'
                      ? Icons.grid_view
                      : mode == 'compact'
                          ? Icons.view_headline
                          : Icons.view_agenda;
              return PopupMenuButton<String>(
                icon: Icon(icon),
                tooltip: 'Switch View (Detailed, Compact, 2-Column, 2-Col Compact)',
                onSelected: (newMode) => settings.setTaskViewMode(newMode),
                itemBuilder: (context) => [
                  const PopupMenuItem(
                    value: 'detailed',
                    child: ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(Icons.view_agenda, color: Colors.blueAccent),
                      title: Text('Detailed Card View', style: TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('Full cards with notes & tag chips'),
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'compact',
                    child: ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(Icons.view_headline, color: Colors.teal),
                      title: Text('Compact View (One-liner)', style: TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('Single-line tasks to fit more on screen'),
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'two_column',
                    child: ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(Icons.grid_view, color: Colors.deepPurpleAccent),
                      title: Text('2-Column Grid Cards', style: TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('Side-by-side cards with 2-line preview'),
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'two_column_compact',
                    child: ListTile(
                      dense: true,
                      contentPadding: EdgeInsets.zero,
                      leading: Icon(Icons.view_compact, color: Colors.indigoAccent),
                      title: Text('2-Column Compact Grid', style: TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('Minimal one-liners side-by-side'),
                    ),
                  ),
                ],
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh',
            onPressed: () => provider.refreshTasks(),
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(102),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 14),
                child: TextField(
                  controller: _searchController,
                  decoration: InputDecoration(
                    hintText: 'Search tasks by title, note, or tag...',
                    prefixIcon: const Icon(Icons.search),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear),
                            onPressed: () {
                              _searchDebounce?.cancel();
                              _searchController.clear();
                              provider.setSearchQuery('');
                              setState(() {});
                            },
                          )
                        : null,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onChanged: (val) {
                    _searchDebounce?.cancel();
                    _searchDebounce = Timer(const Duration(milliseconds: 200), () {
                      if (mounted) provider.setSearchQuery(val);
                    });
                    setState(() {});
                  },
                ),
              ),
              const SizedBox(height: 6),
              SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Row(
                  children: [
                    FilterChip(
                      label: const Text('Pending'),
                      selected: provider.statusFilter == 'pending',
                      onSelected: (_) => provider.setStatusFilter('pending'),
                    ),
                    const SizedBox(width: 8),
                    FilterChip(
                      label: const Text('Completed'),
                      selected: provider.statusFilter == 'completed',
                      onSelected: (_) => provider.setStatusFilter('completed'),
                    ),
                    const SizedBox(width: 8),
                    FilterChip(
                      label: const Text('All Tasks'),
                      selected: provider.statusFilter == 'all',
                      onSelected: (_) => provider.setStatusFilter('all'),
                    ),
                    if (provider.accounts.isNotEmpty) ...[
                      const SizedBox(width: 12),
                      Container(
                        height: 24,
                        width: 1,
                        color: theme.colorScheme.outlineVariant,
                      ),
                      const SizedBox(width: 12),
                      DropdownButton<String>(
                        value: provider.accounts.any((a) => a.id == provider.selectedAccount) || provider.selectedAccount == 'all'
                            ? provider.selectedAccount
                            : 'all',
                        underline: const SizedBox(),
                        items: [
                          const DropdownMenuItem(value: 'all', child: Text('All Accounts')),
                          ...provider.accounts.map(
                            (acc) => DropdownMenuItem(
                              value: acc.id,
                              child: Text(acc.name),
                            ),
                          ),
                          const DropdownMenuItem(
                            value: '__add_new__',
                            child: Row(
                              children: [
                                Icon(Icons.add, size: 16, color: Colors.blueAccent),
                                SizedBox(width: 4),
                                Text('+ Add Account', style: TextStyle(color: Colors.blueAccent, fontWeight: FontWeight.bold)),
                              ],
                            ),
                          ),
                        ],
                        onChanged: (val) {
                          if (val == '__add_new__') {
                            showDialog(
                              context: context,
                              builder: (_) => const AddGoogleAccountModal(),
                            );
                          } else if (val != null) {
                            provider.setAccount(val);
                          }
                        },
                      ),
                    ] else ...[
                      const SizedBox(width: 12),
                      ActionChip(
                        avatar: const Icon(Icons.add, size: 16, color: Colors.amber),
                        label: const Text('Add Account', style: TextStyle(fontSize: 12)),
                        onPressed: () {
                          showDialog(
                            context: context,
                            builder: (_) => const AddGoogleAccountModal(),
                          );
                        },
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(height: 6),
            ],
          ),
        ),
      ),
      body: Column(
        children: [
          _buildTabBar(context, provider, theme),
          // Active Filters Strip (Lists / Tags / Priority / Recurring / Hidden Lists & Tags / Date Range)
          if (provider.hasActiveFilters)
            Container(
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.35),
                border: Border(
                  bottom: BorderSide(
                    color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                  ),
                ),
              ),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                child: Row(
                  children: [
                    ...provider.selectedLists.map((l) => Padding(
                          padding: const EdgeInsets.only(right: 6),
                          child: Chip(
                            avatar: const Icon(Icons.folder, size: 14),
                            label: Text('List: $l', style: const TextStyle(fontSize: 12)),
                            deleteIcon: const Icon(Icons.close, size: 14),
                            onDeleted: () => provider.toggleSelectedList(l),
                            visualDensity: VisualDensity.compact,
                          ),
                        )),
                    ...provider.selectedTags.map((t) => Padding(
                          padding: const EdgeInsets.only(right: 6),
                          child: Chip(
                            avatar: const Icon(Icons.tag, size: 14, color: Colors.teal),
                            label: Text('Tag: #$t', style: const TextStyle(fontSize: 12)),
                            deleteIcon: const Icon(Icons.close, size: 14),
                            onDeleted: () => provider.toggleSelectedTag(t),
                            visualDensity: VisualDensity.compact,
                          ),
                        )),
                    if (provider.selectedSpace != null)
                      Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: Chip(
                          avatar: const Icon(Icons.rocket_launch, size: 14, color: Colors.deepPurpleAccent),
                          label: Text(
                            provider.selectedSubspace != null
                                ? 'Space: ${provider.selectedSpace} › ${provider.selectedSubspace}'
                                : 'Space: ${provider.selectedSpace}',
                            style: const TextStyle(fontSize: 12, color: Colors.deepPurple, fontWeight: FontWeight.bold),
                          ),
                          deleteIcon: const Icon(Icons.close, size: 14),
                          onDeleted: () => provider.clearSpaceFilter(),
                          backgroundColor: Colors.deepPurple.withValues(alpha: 0.1),
                          visualDensity: VisualDensity.compact,
                        ),
                      ),
                    if (provider.selectedPriority != null)
                      Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: Chip(
                          avatar: const Icon(Icons.flag, size: 14),
                          label: Text('Priority: ${provider.selectedPriority}', style: const TextStyle(fontSize: 12)),
                          deleteIcon: const Icon(Icons.close, size: 14),
                          onDeleted: () => provider.setPriorityFilter(null),
                          visualDensity: VisualDensity.compact,
                        ),
                      ),
                    if (provider.hideRecurring)
                      Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: Chip(
                          avatar: const Icon(Icons.redo_outlined, size: 14, color: Colors.orange),
                          label: const Text('Hide Recurring', style: TextStyle(fontSize: 12, color: Colors.orange)),
                          deleteIcon: const Icon(Icons.close, size: 14),
                          onDeleted: () => provider.setHideRecurring(false),
                          visualDensity: VisualDensity.compact,
                        ),
                      ),
                    ...provider.hiddenLists.map((hl) => Padding(
                          padding: const EdgeInsets.only(right: 6),
                          child: Chip(
                            avatar: const Icon(Icons.visibility_off, size: 14, color: Colors.red),
                            label: Text('Hide: $hl', style: const TextStyle(fontSize: 12, color: Colors.red)),
                            deleteIcon: const Icon(Icons.close, size: 14),
                            onDeleted: () => provider.toggleHiddenList(hl),
                            visualDensity: VisualDensity.compact,
                          ),
                        )),
                    ...provider.hiddenTags.map((ht) => Padding(
                          padding: const EdgeInsets.only(right: 6),
                          child: Chip(
                            avatar: const Icon(Icons.visibility_off, size: 14, color: Colors.red),
                            label: Text('Hide: #$ht', style: const TextStyle(fontSize: 12, color: Colors.red)),
                            deleteIcon: const Icon(Icons.close, size: 14),
                            onDeleted: () => provider.toggleHiddenTag(ht),
                            visualDensity: VisualDensity.compact,
                          ),
                        )),
                    if (provider.dateRange != null)
                      Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: Chip(
                          avatar: const Icon(Icons.date_range, size: 14),
                          label: Text(
                            '${provider.dateField}: ${provider.dateRange!.start.month}/${provider.dateRange!.start.day} - ${provider.dateRange!.end.month}/${provider.dateRange!.end.day}',
                            style: const TextStyle(fontSize: 12),
                          ),
                          deleteIcon: const Icon(Icons.close, size: 14),
                          onDeleted: () => provider.setDateFilter(provider.dateField, null),
                          visualDensity: VisualDensity.compact,
                        ),
                      ),
                    TextButton(
                      onPressed: () => provider.clearAllFilters(),
                      child: const Text('Clear All', style: TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
              ),
            ),
          Expanded(
            child: provider.isLoading && provider.tasks.isEmpty
                ? const Center(child: CircularProgressIndicator())
                : provider.errorMessage != null && provider.tasks.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            const Icon(Icons.cloud_off, size: 48, color: Colors.orange),
                            const SizedBox(height: 12),
                            Text('Error: ${provider.errorMessage}'),
                            const SizedBox(height: 12),
                            ElevatedButton(
                              onPressed: () => provider.loadInitialData(),
                              child: const Text('Retry'),
                            ),
                          ],
                        ),
                      )
                    : provider.tasks.isEmpty
                        ? Center(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(horizontal: 24),
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  if (provider.accounts.isEmpty) ...[
                                    Icon(Icons.no_accounts_outlined, size: 58, color: Colors.amber.shade600),
                                    const SizedBox(height: 12),
                                    Text(
                                      'No Accounts Configured',
                                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                                    ),
                                    const SizedBox(height: 6),
                                    Text(
                                      'Connect a Google account to sync your tasks or create a new task locally.',
                                      textAlign: TextAlign.center,
                                      style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                                    ),
                                    const SizedBox(height: 16),
                                    ElevatedButton.icon(
                                      icon: const Icon(Icons.account_circle),
                                      label: const Text('Add Account'),
                                      onPressed: () {
                                        showDialog(
                                          context: context,
                                          builder: (_) => const AddGoogleAccountModal(),
                                        );
                                      },
                                    ),
                                  ] else ...[
                                    Icon(Icons.inbox_outlined, size: 54, color: theme.disabledColor),
                                    const SizedBox(height: 8),
                                    Text('No tasks match your criteria', style: theme.textTheme.titleMedium),
                                    const SizedBox(height: 4),
                                    Text('Tap + New Task to create one', style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor)),
                                    if (hasViewFilters) ...[
                                      const SizedBox(height: 12),
                                      OutlinedButton.icon(
                                        icon: const Icon(Icons.auto_awesome, size: 16, color: Colors.amber),
                                        label: const Text('Ask AI about this view', style: TextStyle(fontSize: 12)),
                                        onPressed: () {
                                          Navigator.push(
                                            context,
                                            MaterialPageRoute(
                                              builder: (_) => AiChatScreen(
                                                initialContext: _buildCurrentViewContext(provider),
                                              ),
                                              fullscreenDialog: true,
                                            ),
                                          );
                                        },
                                      ),
                                    ],
                                  ],
                                ],
                              ),
                            ),
                          )
                        : Consumer<SettingsProvider>(
                            builder: (context, settings, _) {
                              final mode = settings.taskViewMode;
                              if (mode == 'two_column_compact') {
                                return RefreshIndicator(
                                  onRefresh: () => provider.refreshTasks(),
                                  child: GridView.builder(
                                    physics: const AlwaysScrollableScrollPhysics(
                                      parent: BouncingScrollPhysics(),
                                    ),
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
                                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                      crossAxisCount: 2,
                                      crossAxisSpacing: 6,
                                      mainAxisSpacing: 6,
                                      childAspectRatio: 3.6,
                                    ),
                                    addRepaintBoundaries: true,
                                    itemCount: provider.tasks.length,
                                    itemBuilder: (ctx, index) {
                                      final task = provider.tasks[index];
                                      return TaskGridCompactCard(
                                        key: ValueKey(task.id),
                                        task: task,
                                        onToggleComplete: () => provider.completeTask(task.id),
                                        onEdit: () => _showEditTaskSheet(context, task),
                                        onDelete: () => provider.deleteTask(task.id),
                                      );
                                    },
                                  ),
                                );
                              } else if (mode == 'two_column') {
                                return RefreshIndicator(
                                  onRefresh: () => provider.refreshTasks(),
                                  child: GridView.builder(
                                    physics: const AlwaysScrollableScrollPhysics(
                                      parent: BouncingScrollPhysics(),
                                    ),
                                    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                    gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                                      crossAxisCount: 2,
                                      crossAxisSpacing: 8,
                                      mainAxisSpacing: 8,
                                      childAspectRatio: 1.55,
                                    ),
                                    addRepaintBoundaries: true,
                                    itemCount: provider.tasks.length,
                                    itemBuilder: (ctx, index) {
                                      final task = provider.tasks[index];
                                      return TaskGridCard(
                                        key: ValueKey(task.id),
                                        task: task,
                                        onToggleComplete: () => provider.completeTask(task.id),
                                        onEdit: () => _showEditTaskSheet(context, task),
                                        onDelete: () => provider.deleteTask(task.id),
                                      );
                                    },
                                  ),
                                );
                              } else if (mode == 'compact') {
                                return RefreshIndicator(
                                  onRefresh: () => provider.refreshTasks(),
                                  child: ListView.builder(
                                    physics: const AlwaysScrollableScrollPhysics(
                                      parent: BouncingScrollPhysics(),
                                    ),
                                    padding: const EdgeInsets.symmetric(vertical: 4),
                                    addRepaintBoundaries: true,
                                    itemCount: provider.tasks.length,
                                    itemBuilder: (ctx, index) {
                                      final task = provider.tasks[index];
                                      return TaskCompactRow(
                                        key: ValueKey(task.id),
                                        task: task,
                                        onToggleComplete: () => provider.completeTask(task.id),
                                        onEdit: () => _showEditTaskSheet(context, task),
                                        onDelete: () => provider.deleteTask(task.id),
                                      );
                                    },
                                  ),
                                );
                              } else {
                                return RefreshIndicator(
                                  onRefresh: () => provider.refreshTasks(),
                                  child: ListView.builder(
                                    physics: const AlwaysScrollableScrollPhysics(
                                      parent: BouncingScrollPhysics(),
                                    ),
                                    addRepaintBoundaries: true,
                                    itemCount: provider.tasks.length,
                                    itemBuilder: (ctx, index) {
                                      final task = provider.tasks[index];
                                      return TaskCard(
                                        key: ValueKey(task.id),
                                        task: task,
                                        onToggleComplete: () => provider.completeTask(task.id),
                                        onEdit: () => _showEditTaskSheet(context, task),
                                        onDelete: () => provider.deleteTask(task.id),
                                      );
                                    },
                                  ),
                                );
                              }
                            },
                          ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: const Text('New Task'),
        onPressed: () => _showAddTaskSheet(context),
      ),
    );
  }

  Widget _buildTabBar(BuildContext context, TaskProvider provider, ThemeData theme) {
    final tabs = _buildAvailableTabs(provider);
    if (tabs.isEmpty) return const SizedBox.shrink();

    final isDark = theme.brightness == Brightness.dark;

    return Container(
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1B2232) : theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outlineVariant.withValues(alpha: 0.35),
            width: 1,
          ),
        ),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 6),
      child: Row(
        children: [
          // Previous Tab Button ◀
          IconButton(
            icon: const Icon(Icons.chevron_left_rounded, size: 22),
            tooltip: 'Previous Tab',
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            onPressed: () => _stepTab(-1, tabs),
          ),

          // Scrollable Tabs
          Expanded(
            child: SingleChildScrollView(
              controller: _tabScrollController,
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              child: Row(
                children: tabs.map((tab) {
                  final isSelected = _activeTabId == tab.id;
                  final count = _getTabCount(tab, provider);
                  final accent = tab.accentColor ?? theme.colorScheme.primary;

                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(20),
                        onTap: () => _selectTab(tab, tabs),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          curve: Curves.easeOutCubic,
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            color: isSelected
                                ? accent.withValues(alpha: isDark ? 0.22 : 0.15)
                                : (isDark ? Colors.white.withValues(alpha: 0.04) : Colors.black.withValues(alpha: 0.03)),
                            borderRadius: BorderRadius.circular(20),
                            border: Border.all(
                              color: isSelected ? accent : theme.colorScheme.outlineVariant.withValues(alpha: 0.3),
                              width: isSelected ? 1.5 : 1.0,
                            ),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(
                                tab.icon,
                                size: 14,
                                color: isSelected ? accent : (isDark ? Colors.white70 : Colors.black54),
                              ),
                              const SizedBox(width: 5),
                              Text(
                                tab.title,
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                  color: isSelected
                                      ? (isDark ? Colors.white : accent)
                                      : (isDark ? Colors.white70 : Colors.black87),
                                ),
                              ),
                              const SizedBox(width: 5),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                decoration: BoxDecoration(
                                  color: isSelected
                                      ? accent.withValues(alpha: 0.25)
                                      : (isDark ? Colors.white12 : Colors.black.withValues(alpha: 0.08)),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  '$count',
                                  style: TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: isSelected ? accent : (isDark ? Colors.white60 : Colors.black54),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          // Next Tab Button ▶
          IconButton(
            icon: const Icon(Icons.chevron_right_rounded, size: 22),
            tooltip: 'Next Tab',
            visualDensity: VisualDensity.compact,
            padding: EdgeInsets.zero,
            constraints: const BoxConstraints(minWidth: 32, minHeight: 32),
            onPressed: () => _stepTab(1, tabs),
          ),
        ],
      ),
    );
  }
}
