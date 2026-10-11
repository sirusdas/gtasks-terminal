import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import '../../utils/notes_parser.dart';
import '../widgets/task_card.dart';
import '../widgets/developer_settings_modal.dart';
import '../widgets/add_account_modal.dart';
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
    final titleController = TextEditingController();
    final notesController = TextEditingController();
    final tagsController = TextEditingController();

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          left: 20,
          right: 20,
          top: 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Text('Create Task', style: Theme.of(ctx).textTheme.titleLarge),
            const SizedBox(height: 12),
            TextField(
              controller: titleController,
              autofocus: true,
              decoration: const InputDecoration(
                labelText: 'Task title',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: notesController,
              decoration: const InputDecoration(
                labelText: 'Notes / description',
                border: OutlineInputBorder(),
              ),
              maxLines: 2,
            ),
            const SizedBox(height: 10),
            TextField(
              controller: tagsController,
              decoration: const InputDecoration(
                labelText: 'Tags (comma separated, e.g. urgent, work)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.add_task),
              label: const Text('Save Task'),
              onPressed: () {
                final title = titleController.text.trim();
                if (title.isNotEmpty) {
                  final tags = tagsController.text
                      .split(',')
                      .map((t) => t.trim())
                      .where((t) => t.isNotEmpty)
                      .toList();
                  final combinedNotes = NotesParser.combineNotesAndTags(
                    notesController.text.trim(),
                    tags,
                  );
                  context.read<TaskProvider>().addTask(
                    title: title,
                    description: combinedNotes,
                    tags: tags,
                  );
                  Navigator.pop(ctx);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showEditTaskSheet(BuildContext context, task) {
    // Show only the clean user notes in the notes input box
    final titleController = TextEditingController(text: task.title);
    final notesController = TextEditingController(text: task.cleanNotes);
    final tagsController = TextEditingController(text: task.allTags.join(', '));

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => Padding(
        padding: EdgeInsets.only(
          bottom: MediaQuery.of(ctx).viewInsets.bottom + 20,
          left: 20,
          right: 20,
          top: 20,
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text('Edit Task', style: Theme.of(ctx).textTheme.titleLarge),
                IconButton(
                  icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                  tooltip: 'Delete Task',
                  onPressed: () {
                    context.read<TaskProvider>().deleteTask(task.id);
                    Navigator.pop(ctx);
                  },
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextField(
              controller: titleController,
              decoration: const InputDecoration(
                labelText: 'Task title',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 10),
            TextField(
              controller: notesController,
              decoration: const InputDecoration(
                labelText: 'Notes / description (tags separated automatically)',
                border: OutlineInputBorder(),
              ),
              maxLines: 4,
            ),
            const SizedBox(height: 10),
            TextField(
              controller: tagsController,
              decoration: const InputDecoration(
                labelText: 'Tags (comma separated, e.g. work, p1)',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.check),
              label: const Text('Update Task'),
              onPressed: () {
                final title = titleController.text.trim();
                if (title.isNotEmpty) {
                  final tags = tagsController.text
                      .split(',')
                      .map((t) => t.trim())
                      .where((t) => t.isNotEmpty)
                      .toList();
                  final combinedNotes = NotesParser.combineNotesAndTags(
                    notesController.text.trim(),
                    tags,
                  );
                  context.read<TaskProvider>().updateTask(
                    taskId: task.id,
                    title: title,
                    description: combinedNotes,
                    tags: tags,
                  );
                  Navigator.pop(ctx);
                }
              },
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TaskProvider>();
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.check_box_outlined, color: Colors.blueAccent),
            SizedBox(width: 8),
            Text('GTasks App', style: TextStyle(fontWeight: FontWeight.bold)),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.tune, color: Colors.amber),
            tooltip: 'Developer Settings (Backend Endpoint)',
            onPressed: () {
              showDialog(
                context: context,
                builder: (_) => const DeveloperSettingsModal(),
              );
            },
          ),
          IconButton(
            icon: const Icon(Icons.analytics_outlined),
            tooltip: 'Reports & Velocity',
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
                    content: Text(success ? 'Sync initiated successfully' : 'Sync error'),
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
          preferredSize: const Size.fromHeight(105),
          child: Column(
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
                      selected: provider.statusFilter == 'needsAction',
                      onSelected: (_) => provider.setStatusFilter('needsAction'),
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
      body: provider.isLoading && provider.tasks.isEmpty
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
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.inbox_outlined, size: 54, color: theme.disabledColor),
                          const SizedBox(height: 8),
                          Text('No tasks match your criteria', style: theme.textTheme.titleMedium),
                        ],
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
      floatingActionButton: FloatingActionButton.extended(
        icon: const Icon(Icons.add),
        label: const Text('New Task'),
        onPressed: () => _showAddTaskSheet(context),
      ),
    );
  }
}
