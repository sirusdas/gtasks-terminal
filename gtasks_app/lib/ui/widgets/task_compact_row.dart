import 'package:flutter/material.dart';
import '../../models/task_item.dart';
import 'task_detail_modal.dart';

class TaskCompactRow extends StatelessWidget {
  final TaskItem task;
  final VoidCallback onToggleComplete;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  const TaskCompactRow({
    super.key,
    required this.task,
    required this.onToggleComplete,
    this.onEdit,
    this.onDelete,
  });

  Color _getPriorityColor(String priority) {
    switch (priority.toLowerCase()) {
      case 'critical':
        return Colors.red;
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

  void _openQuickView(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => TaskDetailModal(
        task: task,
        onEdit: onEdit ?? () {},
        onDelete: onDelete ?? () {},
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDone = task.isCompleted;
    final priority = task.calculatedPriority.toLowerCase();
    final hasPriority = priority != 'normal' && priority.isNotEmpty;

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.35),
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(8),
          onTap: () => _openQuickView(context),
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 6),
            child: Row(
              children: [
                // Compact Checkbox
                InkWell(
                  borderRadius: BorderRadius.circular(16),
                  onTap: onToggleComplete,
                  child: Padding(
                    padding: const EdgeInsets.all(4),
                    child: Icon(
                      isDone ? Icons.check_circle : Icons.radio_button_unchecked,
                      color: isDone ? Colors.green : theme.colorScheme.primary,
                      size: 20,
                    ),
                  ),
                ),
                const SizedBox(width: 6),

                // Priority Dot Indicator
                if (hasPriority) ...[
                  Container(
                    width: 7,
                    height: 7,
                    decoration: BoxDecoration(
                      color: _getPriorityColor(priority),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 6),
                ],

                // Task Title (one-liner)
                Expanded(
                  child: Text(
                    task.title,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      decoration: isDone ? TextDecoration.lineThrough : null,
                      color: isDone ? theme.hintColor : theme.colorScheme.onSurface,
                    ),
                  ),
                ),
                const SizedBox(width: 8),

                // Due Date Badge
                if (task.due != null) ...[
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.blue.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(Icons.calendar_today, size: 10, color: Colors.blueAccent),
                        const SizedBox(width: 3),
                        Text(
                          _formatDue(task.due!),
                          style: const TextStyle(fontSize: 10.5, color: Colors.blueAccent, fontWeight: FontWeight.w600),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 4),
                ],

                // Space Badge or List
                if (task.spaces.isNotEmpty)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.deepPurple.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      task.spaces.keys.first,
                      style: const TextStyle(fontSize: 10, color: Colors.deepPurple, fontWeight: FontWeight.bold),
                    ),
                  )
                else if (task.listTitle != null && task.listTitle != 'My Tasks')
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 2),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      task.listTitle!,
                      style: TextStyle(fontSize: 10, color: theme.colorScheme.onSurfaceVariant),
                    ),
                  ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  String _formatDue(String due) {
    if (due.length >= 10) return due.substring(5, 10);
    return due;
  }
}
