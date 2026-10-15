import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';
import '../../utils/notes_parser.dart';
import 'searchable_picker_modal.dart';
import 'searchable_space_picker_modal.dart';

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
  late TextEditingController _spacesController;
  late TextEditingController _listController;
  Set<String> _selectedTags = {};
  Map<String, List<String>> _selectedSpaces = {};
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
      final parsedNotes = NotesParser.splitNotesAndMetadata(task.description);
      _notesController = TextEditingController(
        text: task.cleanNotes.isNotEmpty ? task.cleanNotes : parsedNotes.cleanNotes,
      );
      _selectedTags = <String>{
        ...task.allTags,
        ...task.tags,
        ...parsedNotes.tags,
      };
      _tagsController = TextEditingController(text: _selectedTags.join(', '));
      final taskSpaces = task.spaces.isNotEmpty ? task.spaces : parsedNotes.spaces;
      _selectedSpaces = Map.from(taskSpaces.map((k, v) => MapEntry(k, List<String>.from(v))));
      _spacesController = TextEditingController(text: NotesParser.formatSpacesInput(_selectedSpaces));
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
      _selectedTags = {};
      _tagsController = TextEditingController();
      _selectedSpaces = {};
      _spacesController = TextEditingController();
      _listController = TextEditingController(text: 'My Tasks');
    }
  }

  void _syncTagsText() {
    _tagsController.text = _selectedTags.join(', ');
  }

  Future<void> _openTagPicker() async {
    final provider = context.read<TaskProvider>();
    final result = await SearchablePickerModal.show(
      context: context,
      title: 'Select Tags',
      subtitle: 'Search existing tags or type to create a new one',
      icon: Icons.tag,
      optionsWithCounts: provider.tagsWithCounts,
      initialSelected: _selectedTags,
      isMultiSelect: true,
      isTag: true,
    );
    if (result != null) {
      setState(() {
        _selectedTags = result;
        _syncTagsText();
      });
    }
  }

  void _syncSpacesText() {
    _spacesController.text = NotesParser.formatSpacesInput(_selectedSpaces);
  }

  Future<void> _openSpacePicker() async {
    final provider = context.read<TaskProvider>();
    final result = await SearchableSpacePickerModal.show(
      context: context,
      spacesWithCounts: provider.spacesWithCounts,
      subspacesWithCounts: provider.subspacesWithCounts,
      initialSelected: _selectedSpaces,
      isSingleSelect: false,
    );
    if (result != null) {
      setState(() {
        _selectedSpaces = result;
        _syncSpacesText();
      });
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
    _spacesController.dispose();
    _listController.dispose();
    super.dispose();
  }

  void _saveTask() {
    final title = _titleController.text.trim();
    if (title.isEmpty) return;

    final tags = _selectedTags.isNotEmpty
        ? _selectedTags.toList()
        : _tagsController.text
            .split(',')
            .map((t) => t.trim())
            .where((t) => t.isNotEmpty)
            .toList();

    final spaces = _selectedSpaces.isNotEmpty
        ? _selectedSpaces
        : NotesParser.parseSpacesInput(_spacesController.text.trim());

    final combinedNotes = NotesParser.combineNotesAndMetadata(
      _notesController.text.trim(),
      tags,
      spaces: spaces,
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
        spaces: spaces,
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
        spaces: spaces,
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

                    // Tags Header
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            const Text(
                              'Tags',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                            if (_selectedTags.isNotEmpty) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.teal.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  '${_selectedTags.length}',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.teal,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                        TextButton.icon(
                          style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                          icon: const Icon(Icons.tune, size: 16),
                          label: const Text('Browse & Manage', style: TextStyle(fontSize: 12)),
                          onPressed: _openTagPicker,
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),

                    // Interactive Tags Box
                    if (_selectedTags.isEmpty)
                      InkWell(
                        borderRadius: BorderRadius.circular(8),
                        onTap: _openTagPicker,
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                          decoration: BoxDecoration(
                            border: Border.all(color: theme.colorScheme.outlineVariant),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.tag, size: 18, color: theme.hintColor),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Tap to assign tags (e.g. urgent, study, dev)',
                                  style: TextStyle(color: theme.hintColor, fontSize: 13),
                                ),
                              ),
                              Icon(Icons.arrow_drop_down, color: theme.hintColor),
                            ],
                          ),
                        ),
                      )
                    else
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.teal.withValues(alpha: 0.03),
                          border: Border.all(color: Colors.teal.withValues(alpha: 0.3)),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Wrap(
                              spacing: 6,
                              runSpacing: 6,
                              children: _selectedTags.map((tag) {
                                return Chip(
                                  avatar: const Text('#', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 12, color: Colors.teal)),
                                  visualDensity: VisualDensity.compact,
                                  padding: EdgeInsets.zero,
                                  labelPadding: const EdgeInsets.only(left: 2, right: 4),
                                  backgroundColor: Colors.teal.withValues(alpha: 0.08),
                                  label: Text(tag, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: Colors.teal)),
                                  deleteIcon: const Icon(Icons.close, size: 14),
                                  onDeleted: () {
                                    setState(() {
                                      _selectedTags.remove(tag);
                                      _syncTagsText();
                                    });
                                  },
                                );
                              }).toList(),
                            ),
                            const SizedBox(height: 4),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                TextButton.icon(
                                  style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                                  icon: const Icon(Icons.add, size: 14),
                                  label: const Text('Add / Edit More Tags', style: TextStyle(fontSize: 11)),
                                  onPressed: _openTagPicker,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
                    const SizedBox(height: 14),

                    // Spaces & Sub-spaces Header
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Row(
                          children: [
                            const Text(
                              'Spaces & Sub-spaces',
                              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                            ),
                            if (_selectedSpaces.isNotEmpty) ...[
                              const SizedBox(width: 6),
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                decoration: BoxDecoration(
                                  color: Colors.deepPurpleAccent.withValues(alpha: 0.15),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  '${_selectedSpaces.length}',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                    color: Colors.deepPurple,
                                  ),
                                ),
                              ),
                            ],
                          ],
                        ),
                        TextButton.icon(
                          style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                          icon: const Icon(Icons.tune, size: 16),
                          label: const Text('Browse & Manage', style: TextStyle(fontSize: 12)),
                          onPressed: _openSpacePicker,
                        ),
                      ],
                    ),
                    const SizedBox(height: 4),

                    // Interactive Spaces Box
                    if (_selectedSpaces.isEmpty)
                      InkWell(
                        borderRadius: BorderRadius.circular(8),
                        onTap: _openSpacePicker,
                        child: Container(
                          width: double.infinity,
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 12),
                          decoration: BoxDecoration(
                            border: Border.all(color: theme.colorScheme.outlineVariant),
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: Row(
                            children: [
                              Icon(Icons.rocket_launch_outlined, size: 18, color: theme.hintColor),
                              const SizedBox(width: 8),
                              Expanded(
                                child: Text(
                                  'Tap to assign spaces & sub-spaces (e.g. work › dev)',
                                  style: TextStyle(color: theme.hintColor, fontSize: 13),
                                ),
                              ),
                              Icon(Icons.arrow_drop_down, color: theme.hintColor),
                            ],
                          ),
                        ),
                      )
                    else
                      Container(
                        width: double.infinity,
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.deepPurple.withValues(alpha: 0.03),
                          border: Border.all(color: Colors.deepPurpleAccent.withValues(alpha: 0.3)),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            ..._selectedSpaces.entries.map((entry) {
                              final space = entry.key;
                              final subs = entry.value;
                              return Padding(
                                padding: const EdgeInsets.only(bottom: 6),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                                  decoration: BoxDecoration(
                                    color: theme.colorScheme.surface,
                                    borderRadius: BorderRadius.circular(6),
                                    border: Border.all(color: theme.colorScheme.outlineVariant.withValues(alpha: 0.6)),
                                  ),
                                  child: Column(
                                    crossAxisAlignment: CrossAxisAlignment.start,
                                    children: [
                                      Row(
                                        children: [
                                          const Icon(Icons.rocket_launch, size: 14, color: Colors.deepPurpleAccent),
                                          const SizedBox(width: 6),
                                          Text(
                                            space,
                                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: Colors.deepPurple),
                                          ),
                                          const Spacer(),
                                          InkWell(
                                            onTap: () {
                                              setState(() {
                                                _selectedSpaces.remove(space);
                                                _syncSpacesText();
                                              });
                                            },
                                            child: Icon(Icons.close, size: 16, color: theme.hintColor),
                                          ),
                                        ],
                                      ),
                                      if (subs.isNotEmpty) ...[
                                        const SizedBox(height: 6),
                                        Wrap(
                                          spacing: 6,
                                          runSpacing: 4,
                                          children: subs.map((sub) {
                                            return Chip(
                                              avatar: const Icon(Icons.subdirectory_arrow_right, size: 12, color: Colors.deepPurpleAccent),
                                              visualDensity: VisualDensity.compact,
                                              padding: EdgeInsets.zero,
                                              labelPadding: const EdgeInsets.only(left: 2, right: 4),
                                              backgroundColor: Colors.deepPurple.withValues(alpha: 0.08),
                                              label: Text(sub, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500)),
                                              deleteIcon: const Icon(Icons.close, size: 12),
                                              onDeleted: () {
                                                setState(() {
                                                  _selectedSpaces[space]!.remove(sub);
                                                  _syncSpacesText();
                                                });
                                              },
                                            );
                                          }).toList(),
                                        ),
                                      ],
                                    ],
                                  ),
                                ),
                              );
                            }),
                            Row(
                              mainAxisAlignment: MainAxisAlignment.end,
                              children: [
                                TextButton.icon(
                                  style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                                  icon: const Icon(Icons.add, size: 14),
                                  label: const Text('Add / Edit More Spaces', style: TextStyle(fontSize: 11)),
                                  onPressed: _openSpacePicker,
                                ),
                              ],
                            ),
                          ],
                        ),
                      ),
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
