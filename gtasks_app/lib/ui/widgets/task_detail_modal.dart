import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../../models/task_item.dart';

class TaskDetailModal extends StatefulWidget {
  final TaskItem task;
  final VoidCallback onEdit;
  final VoidCallback onDelete;

  const TaskDetailModal({
    super.key,
    required this.task,
    required this.onEdit,
    required this.onDelete,
  });

  @override
  State<TaskDetailModal> createState() => _TaskDetailModalState();
}

class _TaskDetailModalState extends State<TaskDetailModal> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  double _fontSize = 15.0;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final task = widget.task;
    final cleanNotes = task.cleanNotes;
    final tags = task.allTags;

    final jsonPretty = const JsonEncoder.withIndent('  ').convert(task.toJson());

    return Dialog(
      insetPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: ConstrainedBox(
        constraints: const BoxConstraints(maxWidth: 600, maxHeight: 700),
        child: Column(
          children: [
            // Header bar
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 12, 8),
              child: Row(
                children: [
                  Expanded(
                    child: Text(
                      task.title,
                      style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.edit_outlined, size: 20),
                    tooltip: 'Edit Task',
                    onPressed: () {
                      Navigator.pop(context);
                      widget.onEdit();
                    },
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20),
                    onPressed: () => Navigator.pop(context),
                  ),
                ],
              ),
            ),

            // Tab bar: Notes vs Raw JSON
            TabBar(
              controller: _tabController,
              tabs: const [
                Tab(icon: Icon(Icons.menu_book, size: 18), text: 'Notes & Details'),
                Tab(icon: Icon(Icons.data_object, size: 18), text: 'Raw JSON'),
              ],
            ),

            // Body
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // Tab 1: Clean Notes Reader with Font Sizer
                  Column(
                    children: [
                      // Controls bar
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                        child: Row(
                          children: [
                            const Text('Text size: ', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            IconButton(
                              icon: const Icon(Icons.remove, size: 16),
                              onPressed: () => setState(() => _fontSize = (_fontSize - 1).clamp(11, 24)),
                            ),
                            Text('${_fontSize.toInt()}sp', style: const TextStyle(fontSize: 12)),
                            IconButton(
                              icon: const Icon(Icons.add, size: 16),
                              onPressed: () => setState(() => _fontSize = (_fontSize + 1).clamp(11, 24)),
                            ),
                            const Spacer(),
                            if (task.listTitle != null)
                              Chip(
                                label: Text(task.listTitle!, style: const TextStyle(fontSize: 11)),
                                visualDensity: VisualDensity.compact,
                              ),
                          ],
                        ),
                      ),
                      const Divider(height: 1),

                      // Notes text
                      Expanded(
                        child: SingleChildScrollView(
                          padding: const EdgeInsets.all(18),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              if (cleanNotes.isNotEmpty)
                                SelectableText(
                                  cleanNotes,
                                  style: TextStyle(fontSize: _fontSize, height: 1.5),
                                )
                              else
                                Center(
                                  child: Padding(
                                    padding: const EdgeInsets.symmetric(vertical: 40),
                                    child: Text(
                                      'No notes for this task.',
                                      style: TextStyle(color: theme.disabledColor, fontStyle: FontStyle.italic),
                                    ),
                                  ),
                                ),

                              if (tags.isNotEmpty) ...[
                                const SizedBox(height: 24),
                                const Text('Tags:', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                                const SizedBox(height: 8),
                                Wrap(
                                  spacing: 6,
                                  runSpacing: 6,
                                  children: tags.map(
                                    (tag) => Chip(
                                      avatar: const Icon(Icons.tag, size: 14, color: Colors.blueAccent),
                                      label: Text(tag, style: const TextStyle(fontSize: 12, color: Colors.blueAccent)),
                                      backgroundColor: Colors.blue.withValues(alpha: 0.1),
                                      visualDensity: VisualDensity.compact,
                                    ),
                                  ).toList(),
                                ),
                              ],
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),

                  // Tab 2: Raw JSON Inspector
                  Column(
                    children: [
                      Padding(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                        child: Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text('Task Object Payload', style: TextStyle(fontSize: 12, color: Colors.grey)),
                            TextButton.icon(
                              icon: const Icon(Icons.copy, size: 16),
                              label: const Text('Copy JSON'),
                              onPressed: () {
                                Clipboard.setData(ClipboardData(text: jsonPretty));
                                ScaffoldMessenger.of(context).showSnackBar(
                                  const SnackBar(content: Text('Copied JSON to clipboard!')),
                                );
                              },
                            ),
                          ],
                        ),
                      ),
                      const Divider(height: 1),
                      Expanded(
                        child: Container(
                          color: theme.brightness == Brightness.dark ? const Color(0xFF141824) : const Color(0xFFF1F5F9),
                          padding: const EdgeInsets.all(14),
                          width: double.infinity,
                          child: SingleChildScrollView(
                            child: SelectableText(
                              jsonPretty,
                              style: const TextStyle(
                                fontFamily: 'monospace',
                                fontSize: 12,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
