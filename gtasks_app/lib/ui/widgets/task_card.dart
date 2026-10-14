import 'package:flutter/material.dart';
import '../../models/task_item.dart';
import 'task_detail_modal.dart';

class TaskCard extends StatefulWidget {
  final TaskItem task;
  final VoidCallback onToggleComplete;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  const TaskCard({
    super.key,
    required this.task,
    required this.onToggleComplete,
    this.onEdit,
    this.onDelete,
  });

  @override
  State<TaskCard> createState() => _TaskCardState();
}

class _TaskCardState extends State<TaskCard> {
  bool _isNotesExpanded = false;

  Color _getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'high':
        return Colors.redAccent;
      case 'medium':
        return Colors.orangeAccent;
      case 'low':
        return Colors.blueAccent;
      default:
        return Colors.grey;
    }
  }

  void _openQuickView() {
    showDialog(
      context: context,
      builder: (_) => TaskDetailModal(
        task: widget.task,
        onEdit: widget.onEdit ?? () {},
        onDelete: widget.onDelete ?? () {},
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final task = widget.task;
    final isDone = task.isCompleted;
    final cleanNotes = task.cleanNotes;
    final tags = task.allTags;

    return Card(
      elevation: 0.5,
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5),
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: _openQuickView,
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              IconButton(
                icon: Icon(
                  isDone ? Icons.check_circle : Icons.radio_button_unchecked,
                  color: isDone ? Colors.green : theme.colorScheme.primary,
                  size: 26,
                ),
                onPressed: widget.onToggleComplete,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      style: theme.textTheme.titleMedium?.copyWith(
                        decoration: isDone ? TextDecoration.lineThrough : null,
                        color: isDone ? theme.textTheme.bodySmall?.color : null,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    if (cleanNotes.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('📓 ', style: TextStyle(fontSize: 12)),
                          Expanded(
                            child: Text(
                              cleanNotes,
                              maxLines: _isNotesExpanded ? null : 2,
                              overflow: _isNotesExpanded ? TextOverflow.visible : TextOverflow.ellipsis,
                              style: theme.textTheme.bodySmall,
                            ),
                          ),
                        ],
                      ),
                      if (cleanNotes.length > 80 || cleanNotes.contains('\n'))
                        GestureDetector(
                          onTap: () => setState(() => _isNotesExpanded = !_isNotesExpanded),
                          child: Padding(
                            padding: const EdgeInsets.only(top: 2, left: 18),
                            child: Text(
                              _isNotesExpanded ? 'Show less' : 'Show more 📓',
                              style: TextStyle(
                                fontSize: 11,
                                color: theme.colorScheme.primary,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                          ),
                        ),
                    ],
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 6,
                      runSpacing: 4,
                      children: [
                        if (task.listTitle != null)
                          Chip(
                            visualDensity: VisualDensity.compact,
                            padding: EdgeInsets.zero,
                            label: Text(task.listTitle!, style: const TextStyle(fontSize: 11)),
                            backgroundColor: theme.colorScheme.surfaceContainerHighest,
                          ),
                        if (task.calculatedPriority.isNotEmpty && task.calculatedPriority != 'normal')
                          Chip(
                            visualDensity: VisualDensity.compact,
                            padding: EdgeInsets.zero,
                            label: Text(
                              task.calculatedPriority.toUpperCase(),
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: _getPriorityColor(task.calculatedPriority),
                              ),
                            ),
                            backgroundColor: _getPriorityColor(task.calculatedPriority).withValues(alpha: 0.15),
                          ),
                        ...task.spaces.entries.map(
                          (entry) => Chip(
                            avatar: const Icon(Icons.rocket_launch, size: 12, color: Colors.deepPurpleAccent),
                            visualDensity: VisualDensity.compact,
                            padding: EdgeInsets.zero,
                            label: Text(
                              entry.value.isEmpty ? entry.key : '${entry.key} › ${entry.value.join(', ')}',
                              style: const TextStyle(fontSize: 11, color: Colors.deepPurple, fontWeight: FontWeight.w500),
                            ),
                            backgroundColor: Colors.deepPurple.withValues(alpha: 0.1),
                          ),
                        ),
                        ...tags.map(
                          (tag) => Chip(
                            visualDensity: VisualDensity.compact,
                            padding: EdgeInsets.zero,
                            label: Text('#$tag', style: const TextStyle(fontSize: 11, color: Colors.blueAccent)),
                            backgroundColor: Colors.blue.withValues(alpha: 0.1),
                          ),
                        ),
                        if (task.due != null)
                          Chip(
                            avatar: const Icon(Icons.event, size: 14),
                            visualDensity: VisualDensity.compact,
                            padding: EdgeInsets.zero,
                            label: Text(
                              task.due!.substring(0, task.due!.length > 10 ? 10 : task.due!.length),
                              style: const TextStyle(fontSize: 11),
                            ),
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              PopupMenuButton<String>(
                icon: const Icon(Icons.more_vert, size: 20),
                onSelected: (val) {
                  if (val == 'view') _openQuickView();
                  if (val == 'edit' && widget.onEdit != null) widget.onEdit!();
                  if (val == 'delete' && widget.onDelete != null) widget.onDelete!();
                },
                itemBuilder: (ctx) => [
                  const PopupMenuItem(
                    value: 'view',
                    child: Row(
                      children: [
                        Icon(Icons.visibility_outlined, size: 18, color: Colors.blueGrey),
                        SizedBox(width: 8),
                        Text('Quick View / Notes'),
                      ],
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'edit',
                    child: Row(
                      children: [
                        Icon(Icons.edit, size: 18, color: Colors.blueAccent),
                        SizedBox(width: 8),
                        Text('Edit Task'),
                      ],
                    ),
                  ),
                  const PopupMenuItem(
                    value: 'delete',
                    child: Row(
                      children: [
                        Icon(Icons.delete_outline, size: 18, color: Colors.redAccent),
                        SizedBox(width: 8),
                        Text('Delete Task', style: TextStyle(color: Colors.redAccent)),
                      ],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
