import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';
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
    final subtasksCount = context.watch<TaskProvider>().getSubtasksCount(task.id);

    return Card(
      elevation: 0,
      margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
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
                          _TaskBadge(
                            backgroundColor: theme.colorScheme.surfaceContainerHighest,
                            label: Text(task.listTitle!, style: const TextStyle(fontSize: 11)),
                          ),
                        if (task.calculatedPriority.isNotEmpty && task.calculatedPriority != 'normal')
                          _TaskBadge(
                            backgroundColor: _getPriorityColor(task.calculatedPriority).withValues(alpha: 0.15),
                            label: Text(
                              task.calculatedPriority.toUpperCase(),
                              style: TextStyle(
                                fontSize: 10,
                                fontWeight: FontWeight.bold,
                                color: _getPriorityColor(task.calculatedPriority),
                              ),
                            ),
                          ),
                        ...task.spaces.entries.map(
                          (entry) => _TaskBadge(
                            avatar: const Icon(Icons.rocket_launch, size: 12, color: Colors.deepPurpleAccent),
                            backgroundColor: Colors.deepPurple.withValues(alpha: 0.1),
                            label: Text(
                              entry.value.isEmpty ? entry.key : '${entry.key} › ${entry.value.join(', ')}',
                              style: const TextStyle(fontSize: 11, color: Colors.deepPurple, fontWeight: FontWeight.w500),
                            ),
                          ),
                        ),
                        ...tags.map(
                          (tag) => _TaskBadge(
                            backgroundColor: Colors.blue.withValues(alpha: 0.1),
                            label: Text('#$tag', style: const TextStyle(fontSize: 11, color: Colors.blueAccent)),
                          ),
                        ),
                        if (task.formattedDueDate != null)
                          _TaskBadge(
                            avatar: const Icon(Icons.event, size: 13),
                            backgroundColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.6),
                            label: Text(
                              task.formattedDueDate!,
                              style: const TextStyle(fontSize: 11),
                            ),
                          ),
                        if (task.isSubtask)
                          _TaskBadge(
                            avatar: const Icon(Icons.subdirectory_arrow_right, size: 12, color: Colors.teal),
                            backgroundColor: Colors.teal.withValues(alpha: 0.12),
                            label: const Text(
                              '↳ Sub-task',
                              style: TextStyle(fontSize: 10.5, color: Colors.teal, fontWeight: FontWeight.bold),
                            ),
                          ),
                        if (subtasksCount > 0)
                          _TaskBadge(
                            avatar: const Icon(Icons.account_tree_outlined, size: 12, color: Colors.indigo),
                            backgroundColor: Colors.indigo.withValues(alpha: 0.12),
                            label: Text(
                              '↳ $subtasksCount subtask${subtasksCount > 1 ? 's' : ''}',
                              style: const TextStyle(fontSize: 10.5, color: Colors.indigo, fontWeight: FontWeight.bold),
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

class _TaskBadge extends StatelessWidget {
  final Widget label;
  final Widget? avatar;
  final Color? backgroundColor;

  const _TaskBadge({
    required this.label,
    this.avatar,
    this.backgroundColor,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 3),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (avatar != null) ...[
            avatar!,
            const SizedBox(width: 4),
          ],
          label,
        ],
      ),
    );
  }
}
