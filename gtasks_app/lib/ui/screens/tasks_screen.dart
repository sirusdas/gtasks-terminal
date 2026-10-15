import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import '../widgets/task_card.dart';
import '../widgets/task_compact_row.dart';
import '../widgets/task_grid_card.dart';
import '../widgets/settings_modal.dart';
import '../widgets/add_account_modal.dart';
import '../widgets/tasks_sidebar_drawer.dart';
import '../widgets/task_filter_modal.dart';
import '../widgets/task_editor_dialog.dart';
import '../widgets/sync_progress_dialog.dart';
import '../../services/widget_service.dart';
import '../../providers/settings_provider.dart';
import 'reports_screen.dart';

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _searchDebounce;

  @override
  void initState() {
    super.initState();
    WidgetService.init();
    WidgetService.setActionListener((action) {
      if (action == 'open_task_editor' && mounted) {
        _showAddTaskSheet(context, isFromWidget: true);
      }
    });

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      final provider = context.read<TaskProvider>();
      await provider.loadInitialData();
      if (!mounted) return;
      _checkAccountStatusAtStartup(provider);

      // Check if launched from widget with initial action
      final initialAction = await WidgetService.getInitialAction();
      if (initialAction == 'open_task_editor' && mounted) {
        _showAddTaskSheet(context, isFromWidget: true);
      }
    });
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

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TaskProvider>();
    final theme = Theme.of(context);

    return Scaffold(
      drawer: const TasksSidebarDrawer(),
      appBar: AppBar(
        title: const Text('GTasks', style: TextStyle(fontWeight: FontWeight.bold)),
        actions: [
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
              final icon = mode == 'two_column'
                  ? Icons.grid_view
                  : mode == 'compact'
                      ? Icons.view_headline
                      : Icons.view_agenda;
              return PopupMenuButton<String>(
                icon: Icon(icon),
                tooltip: 'Switch View (Detailed, Compact, 2-Column)',
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
                      title: Text('2-Column Grid View', style: TextStyle(fontWeight: FontWeight.bold)),
                      subtitle: Text('Side-by-side cards in two columns'),
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
                                  ],
                                ],
                              ),
                            ),
                          )
                        : Consumer<SettingsProvider>(
                            builder: (context, settings, _) {
                              final mode = settings.taskViewMode;
                              if (mode == 'two_column') {
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
}
