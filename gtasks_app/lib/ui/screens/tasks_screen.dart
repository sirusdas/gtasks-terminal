import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import '../widgets/task_card.dart';
import '../widgets/developer_settings_modal.dart';
import '../widgets/settings_modal.dart';
import '../widgets/add_account_modal.dart';
import '../widgets/tasks_sidebar_drawer.dart';
import '../widgets/task_filter_modal.dart';
import '../widgets/task_editor_dialog.dart';
import 'reports_screen.dart';

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<TaskProvider>().loadInitialData();
    });
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _showAddTaskSheet(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => const TaskEditorDialog(),
    );
  }

  void _showEditTaskSheet(BuildContext context, dynamic task) {
    showDialog(
      context: context,
      builder: (_) => TaskEditorDialog(task: task),
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
          IconButton(
            icon: const Icon(Icons.sync),
            tooltip: 'Google Sync',
            onPressed: () async {
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Starting Google Sync...')),
              );
              final success = await provider.apiClient.triggerGoogleSync();
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    backgroundColor: success ? Colors.green.shade700 : Colors.red.shade700,
                    content: Text(success ? '✅ Google Tasks Sync initiated successfully!' : '❌ Sync failed. Check credentials/network.'),
                  ),
                );
                provider.refreshTasks();
              }
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
                              _searchController.clear();
                              provider.setSearchQuery('');
                            },
                          )
                        : null,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 8),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                  onChanged: (val) => provider.setSearchQuery(val),
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
                        value: provider.selectedAccount,
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
                        : RefreshIndicator(
                            onRefresh: () => provider.refreshTasks(),
                            child: ListView.builder(
                              itemCount: provider.tasks.length,
                              itemBuilder: (ctx, index) {
                                final task = provider.tasks[index];
                                return TaskCard(
                                  task: task,
                                  onToggleComplete: () => provider.completeTask(task.id),
                                  onEdit: () => _showEditTaskSheet(context, task),
                                  onDelete: () => provider.deleteTask(task.id),
                                );
                              },
                            ),
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
