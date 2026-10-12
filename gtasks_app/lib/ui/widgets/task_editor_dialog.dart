import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';
import '../../utils/notes_parser.dart';
import 'searchable_picker_modal.dart';

class TaskEditorDialog extends StatefulWidget {
  final TaskItem? task; // null when adding a new task

  const TaskEditorDialog({super.key, this.task});

  @override
  State<TaskEditorDialog> createState() => _TaskEditorDialogState();
}

class _TaskEditorDialogState extends State<TaskEditorDialog> {
  late TextEditingController _titleController;
  late TextEditingController _notesController;
  late TextEditingController _tagsController;
  late TextEditingController _listController;
  String? _selectedAccount;
  String _selectedPriority = 'medium';
  DateTime? _selectedDueDate;
  bool _isFullscreenNotes = false;
  bool _isPreviewMode = false;

  @override
  void initState() {
    super.initState();
    final task = widget.task;
    if (task != null) {
      _titleController = TextEditingController(text: task.title);
      _notesController = TextEditingController(text: task.cleanNotes);
      _tagsController = TextEditingController(text: task.allTags.join(', '));
      _listController = TextEditingController(text: task.listTitle ?? 'My Tasks');
      _selectedAccount = task.account;
      _selectedPriority = task.calculatedPriority.toLowerCase();
      if (task.due != null && task.due!.isNotEmpty) {
        try {
          _selectedDueDate = DateTime.parse(task.due!);
        } catch (_) {}
      }
    } else {
      _titleController = TextEditingController();
      _notesController = TextEditingController();
      _tagsController = TextEditingController();
      _listController = TextEditingController(text: 'My Tasks');
    }
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_selectedAccount == null) {
      final provider = context.read<TaskProvider>();
      if (provider.selectedAccount != 'all' && provider.selectedAccount.isNotEmpty) {
        _selectedAccount = provider.selectedAccount;
      } else if (provider.accounts.isNotEmpty) {
        _selectedAccount = provider.accounts.first.id;
      } else {
        _selectedAccount = 'default';
      }
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _notesController.dispose();
    _tagsController.dispose();
    _listController.dispose();
    super.dispose();
  }

  void _saveTask() {
    final title = _titleController.text.trim();
    if (title.isEmpty) return;

    final tags = _tagsController.text
        .split(',')
        .map((t) => t.trim())
        .where((t) => t.isNotEmpty)
        .toList();

    final combinedNotes = NotesParser.combineNotesAndTags(
      _notesController.text.trim(),
      tags,
    );

    final provider = context.read<TaskProvider>();
    final listTitle = _listController.text.trim().isEmpty ? 'My Tasks' : _listController.text.trim();
    final dueStr = _selectedDueDate?.toIso8601String();

    if (widget.task != null) {
      provider.updateTask(
        taskId: widget.task!.id,
        title: title,
        description: combinedNotes,
        account: _selectedAccount,
        listTitle: listTitle,
        priority: _selectedPriority,
        due: dueStr,
        tags: tags,
      );
    } else {
      provider.addTask(
        title: title,
        description: combinedNotes,
        account: _selectedAccount,
        listTitle: listTitle,
        priority: _selectedPriority,
        due: dueStr,
        tags: tags,
      );
    }
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.task != null;
    final theme = Theme.of(context);
    final provider = context.watch<TaskProvider>();

    final availableAccounts = provider.accounts;
    final availableLists = provider.listsWithCounts.keys.toList();
    if (!availableLists.contains('My Tasks')) {
      availableLists.insert(0, 'My Tasks');
    }
    final availableTags = provider.tagsWithCounts.keys.toList();

    // If notes is expanded to full screen mode:
    if (_isFullscreenNotes) {
      return Scaffold(
        appBar: AppBar(
          title: Text(
            isEditing ? 'Notes Editor: ${widget.task!.title}' : 'Notes Editor',
            style: const TextStyle(fontSize: 16),
          ),
          actions: [
            IconButton(
              icon: Icon(_isPreviewMode ? Icons.edit_note : Icons.visibility_outlined),
              tooltip: _isPreviewMode ? 'Switch to Edit' : 'Markdown Preview',
              onPressed: () => setState(() => _isPreviewMode = !_isPreviewMode),
            ),
            IconButton(
              icon: const Icon(Icons.fullscreen_exit),
              tooltip: 'Exit Full Screen',
              onPressed: () => setState(() => _isFullscreenNotes = false),
            ),
            IconButton(
              icon: const Icon(Icons.check, color: Colors.greenAccent),
              tooltip: 'Done',
              onPressed: () => setState(() => _isFullscreenNotes = false),
            ),
          ],
        ),
        body: Padding(
          padding: const EdgeInsets.all(16),
          child: _isPreviewMode
              ? Container(
                  width: double.infinity,
                  height: double.infinity,
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: theme.colorScheme.outlineVariant),
                  ),
                  child: SingleChildScrollView(
                    child: SelectableText(
                      _notesController.text.isEmpty ? '*No content written yet.*' : _notesController.text,
                      style: const TextStyle(fontSize: 15, height: 1.5),
                    ),
                  ),
                )
              : TextField(
                  controller: _notesController,
                  autofocus: true,
                  maxLines: null,
                  expands: true,
                  textAlignVertical: TextAlignVertical.top,
                  decoration: const InputDecoration(
                    hintText: 'Type full markdown notes, snippets, or JSON payload here...',
                    border: OutlineInputBorder(),
                  ),
                  style: const TextStyle(fontSize: 15, height: 1.5),
                ),
        ),
      );
    }

    // Default Modal Sheet / Dialog mode
    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Container(
        constraints: BoxConstraints(
          maxHeight: MediaQuery.of(context).size.height * 0.90,
          maxWidth: 600,
        ),
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Header
            Row(
              children: [
                Icon(isEditing ? Icons.edit_note : Icons.add_task, color: theme.colorScheme.primary),
                const SizedBox(width: 8),
                Text(
                  isEditing ? 'Edit Task' : 'New Task',
                  style: theme.textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
                ),
                const Spacer(),
                if (isEditing)
                  IconButton(
                    icon: const Icon(Icons.delete_outline, color: Colors.redAccent),
                    tooltip: 'Delete Task',
                    onPressed: () {
                      context.read<TaskProvider>().deleteTask(widget.task!.id);
                      Navigator.pop(context);
                    },
                  ),
                IconButton(
                  icon: const Icon(Icons.close),
                  onPressed: () => Navigator.pop(context),
                ),
              ],
            ),
            const Divider(),
            Expanded(
              child: SingleChildScrollView(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const SizedBox(height: 6),
                    TextField(
                      controller: _titleController,
                      autofocus: !isEditing,
                      decoration: const InputDecoration(
                        labelText: 'Task Title *',
                        hintText: 'What needs to be done?',
                        border: OutlineInputBorder(),
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Account & List Row with Search / Autocomplete
                    Row(
                      children: [
                        // Account Selector
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: availableAccounts.any((a) => a.id == _selectedAccount)
                                ? _selectedAccount
                                : (availableAccounts.isNotEmpty ? availableAccounts.first.id : 'default'),
                            decoration: const InputDecoration(
                              labelText: 'Account',
                              prefixIcon: Icon(Icons.person_outline, size: 18),
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                            ),
                            items: [
                              if (availableAccounts.isEmpty)
                                const DropdownMenuItem(value: 'default', child: Text('Personal')),
                              ...availableAccounts.map(
                                (acc) => DropdownMenuItem(
                                  value: acc.id,
                                  child: Text(acc.name, overflow: TextOverflow.ellipsis),
                                ),
                              ),
                            ],
                            onChanged: (val) {
                              if (val != null) setState(() => _selectedAccount = val);
                            },
                          ),
                        ),
                        const SizedBox(width: 10),
                        // List Single-Select Picker with Search & Suggest & Add
                        Expanded(
                          child: InkWell(
                            borderRadius: BorderRadius.circular(8),
                            onTap: () async {
                              final listsWithCounts = provider.listsWithCounts;
                              final initial = _listController.text.trim().isNotEmpty
                                  ? {_listController.text.trim()}
                                  : {'My Tasks'};
                              final result = await SearchablePickerModal.show(
                                context: context,
                                title: 'Select Task List',
                                subtitle: 'Search existing lists or type to create a new one',
                                icon: Icons.list_alt,
                                optionsWithCounts: listsWithCounts,
                                initialSelected: initial,
                                isMultiSelect: false,
                                isTag: false,
                              );
                              if (result != null && result.isNotEmpty) {
                                setState(() {
                                  _listController.text = result.first;
                                });
                              }
                            },
                            child: InputDecorator(
                              decoration: const InputDecoration(
                                labelText: 'List / Project',
                                prefixIcon: Icon(Icons.list_alt, size: 18),
                                suffixIcon: Icon(Icons.arrow_drop_down, size: 20),
                                border: OutlineInputBorder(),
                                contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                              ),
                              child: Text(
                                _listController.text.isEmpty ? 'My Tasks' : _listController.text,
                                style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // Priority & Due Date Row
                    Row(
                      children: [
                        // Priority Selector
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: _selectedPriority,
                            decoration: const InputDecoration(
                              labelText: 'Priority',
                              prefixIcon: Icon(Icons.flag_outlined, size: 18),
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                            ),
                            items: const [
                              DropdownMenuItem(
                                value: 'critical',
                                child: Text('🔴 Critical', style: TextStyle(fontWeight: FontWeight.bold)),
                              ),
                              DropdownMenuItem(
                                value: 'high',
                                child: Text('🟠 High', style: TextStyle(fontWeight: FontWeight.bold)),
                              ),
                              DropdownMenuItem(
                                value: 'medium',
                                child: Text('🟡 Medium'),
                              ),
                              DropdownMenuItem(
                                value: 'low',
                                child: Text('🟢 Low'),
                              ),
                            ],
                            onChanged: (val) {
                              if (val != null) setState(() => _selectedPriority = val);
                            },
                          ),
                        ),
                        const SizedBox(width: 10),
                        // Due Date Selector
                        Expanded(
                          child: InkWell(
                            onTap: () async {
                              final picked = await showDatePicker(
                                context: context,
                                initialDate: _selectedDueDate ?? DateTime.now(),
                                firstDate: DateTime(2020),
                                lastDate: DateTime(2035),
                              );
                              if (picked != null) {
                                setState(() => _selectedDueDate = picked);
                              }
                            },
                            child: InputDecorator(
                              decoration: InputDecoration(
                                labelText: 'Due Date',
                                prefixIcon: const Icon(Icons.calendar_today_outlined, size: 18),
                                suffixIcon: _selectedDueDate != null
                                    ? IconButton(
                                        icon: const Icon(Icons.clear, size: 16),
                                        onPressed: () => setState(() => _selectedDueDate = null),
                                      )
                                    : null,
                                border: const OutlineInputBorder(),
                                contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 12),
                              ),
                              child: Text(
                                _selectedDueDate != null
                                    ? '${_selectedDueDate!.year}-${_selectedDueDate!.month.toString().padLeft(2, '0')}-${_selectedDueDate!.day.toString().padLeft(2, '0')}'
                                    : 'No due date',
                                style: TextStyle(
                                  color: _selectedDueDate != null ? theme.textTheme.bodyMedium?.color : theme.hintColor,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // Notes Section Header with Full Screen Toggle & Preview
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Notes / Description',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        TextButton.icon(
                          icon: const Icon(Icons.fullscreen, size: 18),
                          label: const Text('Full Screen', style: TextStyle(fontSize: 12)),
                          onPressed: () => setState(() => _isFullscreenNotes = true),
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    TextField(
                      controller: _notesController,
                      decoration: InputDecoration(
                        hintText: 'Notes, links, details... (Supports Markdown & JSON)',
                        border: const OutlineInputBorder(),
                        suffixIcon: IconButton(
                          icon: const Icon(Icons.open_in_full, size: 18),
                          tooltip: 'Expand to Full Screen Editor',
                          onPressed: () => setState(() => _isFullscreenNotes = true),
                        ),
                      ),
                      maxLines: 4,
                    ),

                    const SizedBox(height: 14),
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Tags',
                          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                        ),
                        TextButton.icon(
                          style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                          icon: const Icon(Icons.search, size: 16),
                          label: const Text('Search & Select Tags', style: TextStyle(fontSize: 12)),
                          onPressed: () async {
                            final currentTags = _tagsController.text
                                .split(',')
                                .map((t) => t.trim())
                                .where((t) => t.isNotEmpty)
                                .toSet();

                            final result = await SearchablePickerModal.show(
                              context: context,
                              title: 'Select Tags',
                              subtitle: 'Search existing tags or type to create a new one',
                              icon: Icons.tag,
                              optionsWithCounts: provider.tagsWithCounts,
                              initialSelected: currentTags,
                              isMultiSelect: true,
                              isTag: true,
                            );

                            if (result != null) {
                              setState(() {
                                _tagsController.text = result.join(', ');
                              });
                            }
                          },
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),
                    TextField(
                      controller: _tagsController,
                      onChanged: (_) => setState(() {}),
                      decoration: InputDecoration(
                        hintText: 'e.g. urgent, study, dev (or tap Search & Select)',
                        border: const OutlineInputBorder(),
                        prefixIcon: const Icon(Icons.tag, size: 18),
                        suffixIcon: IconButton(
                          icon: const Icon(Icons.tune, size: 18),
                          tooltip: 'Open Tags Search Modal',
                          onPressed: () async {
                            final currentTags = _tagsController.text
                                .split(',')
                                .map((t) => t.trim())
                                .where((t) => t.isNotEmpty)
                                .toSet();

                            final result = await SearchablePickerModal.show(
                              context: context,
                              title: 'Select Tags',
                              subtitle: 'Search existing tags or type to create a new one',
                              icon: Icons.tag,
                              optionsWithCounts: provider.tagsWithCounts,
                              initialSelected: currentTags,
                              isMultiSelect: true,
                              isTag: true,
                            );

                            if (result != null) {
                              setState(() {
                                _tagsController.text = result.join(', ');
                              });
                            }
                          },
                        ),
                      ),
                    ),
                    if (availableTags.isNotEmpty) ...[
                      const SizedBox(height: 6),
                      Wrap(
                        spacing: 6,
                        runSpacing: 4,
                        children: availableTags.take(10).map((tag) {
                          final currentTags = _tagsController.text
                              .split(',')
                              .map((t) => t.trim().toLowerCase())
                              .where((t) => t.isNotEmpty)
                              .toSet();
                          final isSelected = currentTags.contains(tag.toLowerCase());
                          return FilterChip(
                            label: Text(tag, style: const TextStyle(fontSize: 11)),
                            selected: isSelected,
                            visualDensity: VisualDensity.compact,
                            padding: const EdgeInsets.symmetric(horizontal: 4),
                            onSelected: (selected) {
                              setState(() {
                                final existing = _tagsController.text
                                    .split(',')
                                    .map((t) => t.trim())
                                    .where((t) => t.isNotEmpty)
                                    .toList();
                                if (selected) {
                                  if (!existing.any((t) => t.toLowerCase() == tag.toLowerCase())) {
                                    existing.add(tag);
                                  }
                                } else {
                                  existing.removeWhere((t) => t.toLowerCase() == tag.toLowerCase());
                                }
                                _tagsController.text = existing.join(', ');
                              });
                            },
                          );
                        }).toList(),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Cancel'),
                ),
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  icon: Icon(isEditing ? Icons.check : Icons.add),
                  label: Text(isEditing ? 'Save Changes' : 'Create Task'),
                  onPressed: _saveTask,
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
