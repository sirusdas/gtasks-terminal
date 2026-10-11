import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';
import '../../utils/notes_parser.dart';

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
  bool _isFullscreenNotes = false;
  bool _isPreviewMode = false;

  @override
  void initState() {
    super.initState();
    if (widget.task != null) {
      _titleController = TextEditingController(text: widget.task!.title);
      _notesController = TextEditingController(text: widget.task!.cleanNotes);
      _tagsController = TextEditingController(text: widget.task!.allTags.join(', '));
    } else {
      _titleController = TextEditingController();
      _notesController = TextEditingController();
      _tagsController = TextEditingController();
    }
  }

  @override
  void dispose() {
    _titleController.dispose();
    _notesController.dispose();
    _tagsController.dispose();
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
    if (widget.task != null) {
      provider.updateTask(
        taskId: widget.task!.id,
        title: title,
        description: combinedNotes,
        tags: tags,
      );
    } else {
      provider.addTask(
        title: title,
        description: combinedNotes,
        tags: tags,
      );
    }
    Navigator.pop(context);
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.task != null;
    final theme = Theme.of(context);

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
          maxHeight: MediaQuery.of(context).size.height * 0.85,
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
                        labelText: 'Task Title',
                        hintText: 'What needs to be done?',
                        border: OutlineInputBorder(),
                      ),
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
                        Row(
                          children: [
                            TextButton.icon(
                              icon: const Icon(Icons.fullscreen, size: 18),
                              label: const Text('Full Screen', style: TextStyle(fontSize: 12)),
                              onPressed: () => setState(() => _isFullscreenNotes = true),
                            ),
                          ],
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
                      maxLines: 5,
                    ),

                    const SizedBox(height: 14),
                    const Text('Tags', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 4),
                    TextField(
                      controller: _tagsController,
                      decoration: const InputDecoration(
                        hintText: 'e.g. urgent, study, dev (comma separated)',
                        border: OutlineInputBorder(),
                        prefixIcon: Icon(Icons.tag, size: 18),
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
