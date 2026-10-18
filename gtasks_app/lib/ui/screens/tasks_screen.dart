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

class TasksScreen extends StatefulWidget {
  const TasksScreen({super.key});

  @override
  State<TasksScreen> createState() => _TasksScreenState();
}

class _TasksScreenState extends State<TasksScreen> {
  final TextEditingController _searchController = TextEditingController();
  final ScrollController _tabScrollController = ScrollController();
  Timer? _searchDebounce;
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
    final tabIndex = provider.tabs.indexWhere((t) => t.id == tabId);
    if (tabIndex != -1) {
      provider.switchToTab(tabIndex);
    } else if (filterType.isNotEmpty) {
      final matchIdx = provider.tabs.indexWhere((t) {
        if (filterType == 'space') return t.selectedSpace == filterVal;
        if (filterType == 'priority') return t.selectedPriority == filterVal;
        if (filterType == 'list') return t.selectedLists.contains(filterVal);
        if (filterType == 'tag') return t.selectedTags.contains(filterVal);
        return false;
      });
      if (matchIdx != -1) {
        provider.switchToTab(matchIdx);
      } else {
        provider.addNewTab(
          title: filterVal.isNotEmpty ? filterVal : 'Tab',
          space: filterType == 'space' ? filterVal : null,
          priority: filterType == 'priority' ? filterVal : null,
          list: filterType == 'list' ? filterVal : null,
          tag: filterType == 'tag' ? filterVal : null,
        );
      }
    }
  }

  void _showNewTabDialog(BuildContext context, TaskProvider provider) {
    Set<String> chosenAccounts = Set.from(
      provider.selectedAccounts.isNotEmpty
          ? provider.selectedAccounts
          : (provider.selectedAccount != 'all' ? {provider.selectedAccount} : <String>{}),
    );

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final theme = Theme.of(ctx);
        return StatefulBuilder(
          builder: (modalCtx, setModalState) {
            final isAllSelected = chosenAccounts.isEmpty || chosenAccounts.contains('all');

            String getAccountScopeLabel() {
              if (isAllSelected) return 'All Accounts';
              final names = chosenAccounts.map((id) {
                final match = provider.accounts.where((a) => a.id == id);
                return match.isNotEmpty ? match.first.name : id;
              }).toList();
              return names.join(', ');
            }

            String formatTitleWithAccounts(String baseTitle) {
              if (isAllSelected) return baseTitle;
              final scope = getAccountScopeLabel();
              return '$scope - $baseTitle';
            }

            return Container(
              decoration: BoxDecoration(
                color: theme.colorScheme.surface,
                borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              child: SafeArea(
                child: ConstrainedBox(
                  constraints: BoxConstraints(
                    maxHeight: MediaQuery.of(ctx).size.height * 0.85,
                  ),
                  child: SingleChildScrollView(
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Center(
                          child: Container(
                            width: 40,
                            height: 4,
                            decoration: BoxDecoration(
                              color: theme.colorScheme.outlineVariant,
                              borderRadius: BorderRadius.circular(2),
                            ),
                          ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            const Icon(Icons.tab, color: Colors.blueAccent),
                            const SizedBox(width: 8),
                            Text(
                              'Open New Tab',
                              style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                            ),
                          ],
                        ),
                        const SizedBox(height: 12),

                        // Multi-Account Selector Header
                        if (provider.accounts.isNotEmpty) ...[
                          Row(
                            children: [
                              Icon(Icons.people_alt_rounded, size: 16, color: theme.colorScheme.primary),
                              const SizedBox(width: 6),
                              Text(
                                'Select Accounts (Multi-select)',
                                style: theme.textTheme.labelMedium?.copyWith(
                                  fontWeight: FontWeight.w600,
                                  color: theme.colorScheme.primary,
                                ),
                              ),
                              const Spacer(),
                              Text(
                                isAllSelected ? 'All Accounts' : '${chosenAccounts.length} selected',
                                style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: [
                              FilterChip(
                                avatar: Icon(
                                  Icons.all_inclusive_rounded,
                                  size: 16,
                                  color: isAllSelected ? theme.colorScheme.onPrimary : Colors.blueAccent,
                                ),
                                label: const Text('All Accounts'),
                                selected: isAllSelected,
                                selectedColor: theme.colorScheme.primary,
                                checkmarkColor: theme.colorScheme.onPrimary,
                                labelStyle: TextStyle(
                                  color: isAllSelected ? theme.colorScheme.onPrimary : null,
                                  fontWeight: isAllSelected ? FontWeight.bold : FontWeight.normal,
                                ),
                                onSelected: (_) {
                                  setModalState(() {
                                    chosenAccounts.clear();
                                  });
                                },
                              ),
                              ...provider.accounts.map((acc) {
                                final isSelected = !isAllSelected && chosenAccounts.contains(acc.id);
                                return FilterChip(
                                  avatar: Icon(
                                    Icons.account_circle_rounded,
                                    size: 16,
                                    color: isSelected ? theme.colorScheme.onPrimary : Colors.teal,
                                  ),
                                  label: Text(acc.name),
                                  selected: isSelected,
                                  selectedColor: Colors.teal,
                                  checkmarkColor: Colors.white,
                                  labelStyle: TextStyle(
                                    color: isSelected ? Colors.white : null,
                                    fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                                  ),
                                  onSelected: (selected) {
                                    setModalState(() {
                                      if (selected) {
                                        chosenAccounts.remove('all');
                                        chosenAccounts.add(acc.id);
                                      } else {
                                        chosenAccounts.remove(acc.id);
                                      }
                                    });
                                  },
                                );
                              }),
                            ],
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Active Scope: ${getAccountScopeLabel()}',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.primary,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                          const Divider(height: 20),
                        ],

                        // Presets
                        Text(
                          'Views & Presets',
                          style: theme.textTheme.labelMedium?.copyWith(color: theme.hintColor),
                        ),
                        const SizedBox(height: 4),

                        if (!isAllSelected && chosenAccounts.isNotEmpty)
                          ListTile(
                            leading: const Icon(Icons.folder_shared_rounded, color: Colors.teal),
                            title: Text('Open Tab for ${getAccountScopeLabel()}'),
                            subtitle: Text('Tab filtered exclusively to ${getAccountScopeLabel()}'),
                            dense: true,
                            onTap: () {
                              Navigator.pop(ctx);
                              provider.addNewTab(
                                title: getAccountScopeLabel(),
                                accounts: chosenAccounts,
                                iconCodePoint: Icons.account_circle_rounded.codePoint,
                              );
                            },
                          ),

                        ListTile(
                          leading: const Icon(Icons.all_inbox_rounded, color: Colors.blueAccent),
                          title: Text(formatTitleWithAccounts('All Tasks')),
                          subtitle: Text('Clean tab with all pending tasks for ${getAccountScopeLabel()}'),
                          dense: true,
                          onTap: () {
                            Navigator.pop(ctx);
                            provider.addNewTab(
                              title: formatTitleWithAccounts('All Tasks'),
                              accounts: isAllSelected ? null : chosenAccounts,
                              iconCodePoint: Icons.all_inbox_rounded.codePoint,
                            );
                          },
                        ),
                        ListTile(
                          leading: const Icon(Icons.copy_rounded, color: Colors.teal),
                          title: const Text('Duplicate Current Tab'),
                          subtitle: const Text('Copy current filters to a new tab'),
                          dense: true,
                          onTap: () {
                            Navigator.pop(ctx);
                            provider.duplicateTab(provider.activeTabIndex);
                          },
                        ),
                        ListTile(
                          leading: const Icon(Icons.today_rounded, color: Colors.amber),
                          title: Text(formatTitleWithAccounts('Today & Due')),
                          subtitle: Text('Tasks due today or overdue for ${getAccountScopeLabel()}'),
                          dense: true,
                          onTap: () {
                            Navigator.pop(ctx);
                            final now = DateTime.now();
                            provider.addNewTab(
                              title: formatTitleWithAccounts('Today & Due'),
                              accounts: isAllSelected ? null : chosenAccounts,
                              iconCodePoint: Icons.today_rounded.codePoint,
                              dateField: 'due',
                              dateRange: DateTimeRange(
                                start: DateTime(2000, 1, 1),
                                end: DateTime(now.year, now.month, now.day, 23, 59, 59),
                              ),
                            );
                          },
                        ),
                        ListTile(
                          leading: const Icon(Icons.local_fire_department_rounded, color: Colors.deepOrangeAccent),
                          title: Text(formatTitleWithAccounts('High Priority')),
                          subtitle: Text('Critical and high priority tasks for ${getAccountScopeLabel()}'),
                          dense: true,
                          onTap: () {
                            Navigator.pop(ctx);
                            provider.addNewTab(
                              title: formatTitleWithAccounts('High Priority'),
                              accounts: isAllSelected ? null : chosenAccounts,
                              iconCodePoint: Icons.local_fire_department_rounded.codePoint,
                              priority: 'high',
                            );
                          },
                        ),
                        if (provider.spacesWithCounts.isNotEmpty) ...[
                          const Divider(height: 24),
                          Text('Spaces for ${getAccountScopeLabel()}', style: theme.textTheme.labelMedium?.copyWith(color: theme.hintColor)),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 8,
                            runSpacing: 8,
                            children: provider.spacesWithCounts.keys.map((space) {
                              return ActionChip(
                                avatar: const Icon(Icons.rocket_launch_rounded, size: 14, color: Colors.purpleAccent),
                                label: Text(space),
                                onPressed: () {
                                  Navigator.pop(ctx);
                                  provider.addNewTab(
                                    title: formatTitleWithAccounts(space),
                                    accounts: isAllSelected ? null : chosenAccounts,
                                    space: space,
                                    iconCodePoint: Icons.rocket_launch_rounded.codePoint,
                                  );
                                },
                              );
                            }).toList(),
                          ),
                        ],
                        const SizedBox(height: 16),
                      ],
                    ),
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  void _showRenameTabDialog(BuildContext context, TaskProvider provider, int tabIndex) {
    if (tabIndex < 0 || tabIndex >= provider.tabs.length) return;
    final tab = provider.tabs[tabIndex];
    final controller = TextEditingController(text: tab.title);

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Rename Tab'),
        content: TextField(
          controller: controller,
          autofocus: true,
          decoration: const InputDecoration(
            labelText: 'Tab Name',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () {
              final newName = controller.text.trim();
              if (newName.isNotEmpty) {
                provider.renameTab(tabIndex, newName);
              }
              Navigator.pop(ctx);
            },
            child: const Text('Save'),
          ),
        ],
      ),
    );
  }

  void _showTabContextMenu(BuildContext context, TaskProvider provider, int tabIndex) {
    if (tabIndex < 0 || tabIndex >= provider.tabs.length) return;
    final tab = provider.tabs[tabIndex];
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final theme = Theme.of(ctx);
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                ListTile(
                  leading: const Icon(Icons.edit_rounded),
                  title: const Text('Rename Tab'),
                  subtitle: Text(tab.title),
                  onTap: () {
                    Navigator.pop(ctx);
                    _showRenameTabDialog(context, provider, tabIndex);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.copy_rounded),
                  title: const Text('Duplicate Tab'),
                  subtitle: const Text('Clone this tab and its filters'),
                  onTap: () {
                    Navigator.pop(ctx);
                    provider.duplicateTab(tabIndex);
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.switch_account_rounded, color: Colors.blueAccent),
                  title: const Text('Filter by Account(s)'),
                  subtitle: Text(tab.effectiveAccounts.isEmpty || tab.effectiveAccounts.contains('all')
                      ? 'All Accounts'
                      : tab.effectiveAccounts.map((id) {
                          final match = provider.accounts.where((a) => a.id == id);
                          return match.isNotEmpty ? match.first.name : id;
                        }).join(', ')),
                  onTap: () {
                    Navigator.pop(ctx);
                    _showChangeAccountDialog(context, provider, tabIndex);
                  },
                ),
                if (provider.tabs.length > 1)
                  ListTile(
                    leading: const Icon(Icons.close_rounded, color: Colors.redAccent),
                    title: const Text('Close Tab', style: TextStyle(color: Colors.redAccent)),
                    onTap: () {
                      Navigator.pop(ctx);
                      provider.closeTab(tabIndex);
                    },
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showChangeAccountDialog(BuildContext context, TaskProvider provider, int tabIndex) {
    if (tabIndex < 0 || tabIndex >= provider.tabs.length) return;
    final tab = provider.tabs[tabIndex];
    Set<String> chosenAccounts = Set.from(tab.effectiveAccounts);

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(20))),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (modalCtx, setModalState) {
            final isAllSelected = chosenAccounts.isEmpty || chosenAccounts.contains('all');

            return SafeArea(
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Filter Tab by Account(s)',
                      style: Theme.of(ctx).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      'Select one or multiple accounts for this tab',
                      style: Theme.of(ctx).textTheme.bodySmall?.copyWith(color: Theme.of(ctx).hintColor),
                    ),
                    const SizedBox(height: 12),
                    ListTile(
                      leading: const Icon(Icons.people_alt_rounded, color: Colors.blueAccent),
                      title: const Text('All Accounts'),
                      trailing: isAllSelected
                          ? const Icon(Icons.check_circle_rounded, color: Colors.blueAccent)
                          : null,
                      onTap: () {
                        setModalState(() {
                          chosenAccounts.clear();
                        });
                      },
                    ),
                    ...provider.accounts.map((acc) {
                      final isSelected = !isAllSelected && chosenAccounts.contains(acc.id);
                      return ListTile(
                        leading: const Icon(Icons.account_circle_rounded, color: Colors.teal),
                        title: Text(acc.name),
                        subtitle: Text(acc.email ?? acc.id),
                        trailing: Checkbox(
                          value: isSelected,
                          onChanged: (val) {
                            setModalState(() {
                              if (val == true) {
                                chosenAccounts.remove('all');
                                chosenAccounts.add(acc.id);
                              } else {
                                chosenAccounts.remove(acc.id);
                              }
                            });
                          },
                        ),
                        onTap: () {
                          setModalState(() {
                            if (!isSelected) {
                              chosenAccounts.remove('all');
                              chosenAccounts.add(acc.id);
                            } else {
                              chosenAccounts.remove(acc.id);
                            }
                          });
                        },
                      );
                    }),
                    const SizedBox(height: 8),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: () => Navigator.pop(ctx),
                          child: const Text('Cancel'),
                        ),
                        const SizedBox(width: 8),
                        ElevatedButton(
                          onPressed: () {
                            Navigator.pop(ctx);
                            provider.updateTabAccounts(tabIndex, chosenAccounts);
                          },
                          child: const Text('Apply'),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                  ],
                ),
              ),
            );
          },
        );
      },
    );
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

  void _handleToggleComplete(BuildContext context, TaskProvider provider, TaskItem task) async {
    final title = task.title.trim().isEmpty ? 'Task' : task.title.trim();

    // Show in-progress toast message immediately
    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        duration: const Duration(milliseconds: 1400),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.only(bottom: 80, left: 16, right: 16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        content: Row(
          children: [
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                'Completing "$title"...',
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Colors.white),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
        ),
      ),
    );

    final success = await provider.completeTask(task.id);
    if (!context.mounted) return;

    ScaffoldMessenger.of(context).hideCurrentSnackBar();
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        duration: const Duration(milliseconds: 2200),
        behavior: SnackBarBehavior.floating,
        margin: const EdgeInsets.only(bottom: 80, left: 16, right: 16),
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        backgroundColor: success ? const Color(0xFF15803D) : Colors.red.shade800,
        content: Row(
          children: [
            Icon(
              success ? Icons.check_circle_rounded : Icons.error_outline_rounded,
              color: Colors.white,
              size: 20,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Text(
                success ? 'Completed "$title"' : 'Failed to complete "$title"',
                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500, color: Colors.white),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ),
          ],
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
            icon: (provider.isLoading || provider.isSyncing)
                ? const SizedBox(
                    width: 20,
                    height: 20,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                  )
                : const Icon(Icons.sync),
            tooltip: 'Google Sync Options',
            onSelected: (action) {
              if (provider.isSyncing) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text('Sync is already in progress...'),
                    duration: Duration(seconds: 2),
                  ),
                );
                return;
              }
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
          preferredSize: const Size.fromHeight(50),
          child: Padding(
            padding: const EdgeInsets.fromLTRB(14, 0, 14, 8),
            child: Row(
              children: [
                Expanded(
                  child: SizedBox(
                    height: 38,
                    child: TextField(
                      controller: _searchController,
                      decoration: InputDecoration(
                        hintText: 'Search tasks, tags, notes...',
                        hintStyle: TextStyle(fontSize: 13, color: theme.hintColor),
                        prefixIcon: const Icon(Icons.search, size: 18),
                        suffixIcon: _searchController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear, size: 16),
                                onPressed: () {
                                  _searchDebounce?.cancel();
                                  _searchController.clear();
                                  provider.setSearchQuery('');
                                  setState(() {});
                                },
                              )
                            : null,
                        isDense: true,
                        contentPadding: const EdgeInsets.symmetric(vertical: 0, horizontal: 10),
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
                ),
                const SizedBox(width: 8),
                // Compact Status Toggle Menu (Pending, Completed, All)
                PopupMenuButton<String>(
                  tooltip: 'Status Filter',
                  initialValue: provider.statusFilter,
                  onSelected: (val) => provider.setStatusFilter(val),
                  itemBuilder: (context) => [
                    const PopupMenuItem(
                      value: 'pending',
                      child: Row(
                        children: [
                          Icon(Icons.check_circle_outline, size: 18, color: Colors.blueAccent),
                          SizedBox(width: 8),
                          Text('Pending Tasks'),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'completed',
                      child: Row(
                        children: [
                          Icon(Icons.done_all, size: 18, color: Colors.green),
                          SizedBox(width: 8),
                          Text('Completed Tasks'),
                        ],
                      ),
                    ),
                    const PopupMenuItem(
                      value: 'all',
                      child: Row(
                        children: [
                          Icon(Icons.inbox, size: 18, color: Colors.purpleAccent),
                          SizedBox(width: 8),
                          Text('All Tasks'),
                        ],
                      ),
                    ),
                  ],
                  child: Container(
                    height: 38,
                    padding: const EdgeInsets.symmetric(horizontal: 10),
                    decoration: BoxDecoration(
                      color: provider.statusFilter != 'pending'
                          ? theme.colorScheme.primaryContainer
                          : theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                      ),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(
                          provider.statusFilter == 'completed'
                              ? Icons.done_all
                              : provider.statusFilter == 'all'
                                  ? Icons.inbox
                                  : Icons.pending_actions,
                          size: 16,
                          color: provider.statusFilter != 'pending'
                              ? theme.colorScheme.onPrimaryContainer
                              : theme.colorScheme.onSurfaceVariant,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          provider.statusFilter == 'completed'
                              ? 'Done'
                              : provider.statusFilter == 'all'
                                  ? 'All'
                                  : 'Pending',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: provider.statusFilter != 'pending'
                                ? theme.colorScheme.onPrimaryContainer
                                : theme.colorScheme.onSurfaceVariant,
                          ),
                        ),
                        const SizedBox(width: 2),
                        const Icon(Icons.arrow_drop_down, size: 16),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
      body: Column(
        children: [
          _buildTabBar(context, provider, theme),
          // Compact Micro Active Filters Strip (Saves over 30% vertical screen space)
          if (provider.hasActiveFilters)
            Container(
              height: 32,
              decoration: BoxDecoration(
                color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.25),
                border: Border(
                  bottom: BorderSide(
                    color: theme.colorScheme.outlineVariant.withValues(alpha: 0.3),
                  ),
                ),
              ),
              child: SingleChildScrollView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                child: Row(
                  children: [
                    ...provider.selectedLists.map((l) => _buildMicroFilterPill(
                          label: 'List: $l',
                          icon: Icons.folder,
                          onDeleted: () => provider.toggleSelectedList(l),
                          color: Colors.blueAccent,
                        )),
                    ...provider.selectedTags.map((t) => _buildMicroFilterPill(
                          label: '#$t',
                          icon: Icons.tag,
                          onDeleted: () => provider.toggleSelectedTag(t),
                          color: Colors.teal,
                        )),
                    if (provider.selectedSpace != null)
                      _buildMicroFilterPill(
                        label: provider.selectedSubspace != null
                            ? '${provider.selectedSpace} › ${provider.selectedSubspace}'
                            : provider.selectedSpace!,
                        icon: Icons.rocket_launch,
                        onDeleted: () => provider.clearSpaceFilter(),
                        color: Colors.deepPurpleAccent,
                      ),
                    if (provider.selectedPriority != null)
                      _buildMicroFilterPill(
                        label: 'Priority: ${provider.selectedPriority}',
                        icon: Icons.flag,
                        onDeleted: () => provider.setPriorityFilter(null),
                        color: Colors.deepOrangeAccent,
                      ),
                    if (provider.hideRecurring)
                      _buildMicroFilterPill(
                        label: 'Hide Recurring',
                        icon: Icons.redo_outlined,
                        onDeleted: () => provider.setHideRecurring(false),
                        color: Colors.orange,
                      ),
                    ...provider.hiddenLists.map((hl) => _buildMicroFilterPill(
                          label: 'Hide: $hl',
                          icon: Icons.visibility_off,
                          onDeleted: () => provider.toggleHiddenList(hl),
                          color: Colors.redAccent,
                        )),
                    ...provider.hiddenTags.map((ht) => _buildMicroFilterPill(
                          label: 'Hide: #$ht',
                          icon: Icons.visibility_off,
                          onDeleted: () => provider.toggleHiddenTag(ht),
                          color: Colors.redAccent,
                        )),
                    if (provider.dateRange != null)
                      _buildMicroFilterPill(
                        label: '${provider.dateField}: ${provider.dateRange!.start.month}/${provider.dateRange!.start.day} - ${provider.dateRange!.end.month}/${provider.dateRange!.end.day}',
                        icon: Icons.date_range,
                        onDeleted: () => provider.setDateFilter(provider.dateField, null),
                        color: Colors.indigoAccent,
                      ),
                    InkWell(
                      borderRadius: BorderRadius.circular(10),
                      onTap: () => provider.clearAllFilters(),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                        child: Text(
                          'Clear All',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: theme.colorScheme.error,
                          ),
                        ),
                      ),
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
                                        onToggleComplete: () => _handleToggleComplete(context, provider, task),
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
                                        onToggleComplete: () => _handleToggleComplete(context, provider, task),
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
                                        onToggleComplete: () => _handleToggleComplete(context, provider, task),
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
                                        onToggleComplete: () => _handleToggleComplete(context, provider, task),
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
    final tabs = provider.tabs;
    if (tabs.isEmpty) return const SizedBox.shrink();

    final isDark = theme.brightness == Brightness.dark;
    final activeIndex = provider.activeTabIndex;

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
            onPressed: () {
              if (tabs.length > 1) {
                final nextIdx = (activeIndex - 1 + tabs.length) % tabs.length;
                provider.switchToTab(nextIdx);
              }
            },
          ),

          // Scrollable Tabs
          Expanded(
            child: SingleChildScrollView(
              controller: _tabScrollController,
              scrollDirection: Axis.horizontal,
              physics: const BouncingScrollPhysics(),
              child: Row(
                children: [
                  ...tabs.asMap().entries.map((entry) {
                    final idx = entry.key;
                    final tab = entry.value;
                    final isSelected = activeIndex == idx;
                    final count = tab.computeTaskCount(provider.allTasksUnfiltered);
                    final accent = tab.accentColor ?? (isSelected ? theme.colorScheme.primary : Colors.grey);

                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 3),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          borderRadius: BorderRadius.circular(16),
                          onTap: () => provider.switchToTab(idx),
                          onLongPress: () => _showTabContextMenu(context, provider, idx),
                          child: AnimatedContainer(
                            duration: const Duration(milliseconds: 200),
                            curve: Curves.easeOutCubic,
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                            decoration: BoxDecoration(
                              color: isSelected
                                  ? (isDark ? theme.colorScheme.surfaceContainerHighest : Colors.white)
                                  : (isDark ? Colors.white.withValues(alpha: 0.04) : Colors.black.withValues(alpha: 0.03)),
                              borderRadius: BorderRadius.circular(16),
                              boxShadow: isSelected
                                  ? [
                                      BoxShadow(
                                        color: Colors.black.withValues(alpha: isDark ? 0.3 : 0.08),
                                        blurRadius: 4,
                                        offset: const Offset(0, 2),
                                      ),
                                    ]
                                  : null,
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
                                const SizedBox(width: 6),
                                ConstrainedBox(
                                  constraints: const BoxConstraints(maxWidth: 120),
                                  child: Text(
                                    tab.title,
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                      color: isSelected
                                          ? (isDark ? Colors.white : theme.colorScheme.onSurface)
                                          : (isDark ? Colors.white70 : Colors.black87),
                                    ),
                                  ),
                                ),
                                if (tab.selectedAccount != null && tab.selectedAccount != 'all') ...[
                                  const SizedBox(width: 4),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                                    decoration: BoxDecoration(
                                      color: Colors.teal.withValues(alpha: 0.15),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      tab.selectedAccount!,
                                      style: const TextStyle(fontSize: 9, color: Colors.teal, fontWeight: FontWeight.w600),
                                    ),
                                  ),
                                ],
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: isSelected
                                        ? accent.withValues(alpha: 0.2)
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
                                if (tabs.length > 1) ...[
                                  const SizedBox(width: 4),
                                  InkWell(
                                    borderRadius: BorderRadius.circular(10),
                                    onTap: () => provider.closeTab(idx),
                                    child: Padding(
                                      padding: const EdgeInsets.all(2.0),
                                      child: Icon(
                                        Icons.close_rounded,
                                        size: 13,
                                        color: isSelected
                                            ? (isDark ? Colors.white70 : Colors.black54)
                                            : (isDark ? Colors.white38 : Colors.black38),
                                      ),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          ),
                        ),
                      ),
                    );
                  }),
                  // Add New Tab [+] button
                  Padding(
                    padding: const EdgeInsets.only(left: 4, right: 8),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        borderRadius: BorderRadius.circular(16),
                        onTap: () => _showNewTabDialog(context, provider),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
                          decoration: BoxDecoration(
                            border: Border.all(
                              color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                              style: BorderStyle.solid,
                            ),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.add_rounded, size: 16, color: theme.colorScheme.primary),
                              const SizedBox(width: 4),
                              Text(
                                'New Tab',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: theme.colorScheme.primary,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
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
            onPressed: () {
              if (tabs.length > 1) {
                final nextIdx = (activeIndex + 1) % tabs.length;
                provider.switchToTab(nextIdx);
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildMicroFilterPill({
    required String label,
    required IconData icon,
    required VoidCallback onDeleted,
    Color? color,
  }) {
    final pillColor = color ?? Colors.blueAccent;
    return Container(
      margin: const EdgeInsets.only(right: 6),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: pillColor.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: pillColor.withValues(alpha: 0.35),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: pillColor),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: pillColor,
            ),
          ),
          const SizedBox(width: 4),
          GestureDetector(
            onTap: onDeleted,
            child: Icon(Icons.close_rounded, size: 13, color: pillColor),
          ),
        ],
      ),
    );
  }
}
