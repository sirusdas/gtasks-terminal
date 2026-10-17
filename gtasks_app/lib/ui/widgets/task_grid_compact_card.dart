import 'package:flutter/material.dart';
import '../../models/task_item.dart';
import 'task_detail_modal.dart';

class TaskGridCompactCard extends StatelessWidget {
  final TaskItem task;
  final VoidCallback onToggleComplete;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  const TaskGridCompactCard({
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

    return Card(
      elevation: 0,
      margin: EdgeInsets.zero,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5),
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(8),
        onTap: () => _openQuickView(context),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 5),
          child: Row(
            children: [
              // Checkbox
              InkWell(
                borderRadius: BorderRadius.circular(12),
                onTap: onToggleComplete,
                child: Padding(
                  padding: const EdgeInsets.all(2),
                  child: Icon(
                    isDone ? Icons.check_circle : Icons.radio_button_unchecked,
                    color: isDone ? Colors.green : theme.colorScheme.primary,
                    size: 17,
                  ),
                ),
              ),
              const SizedBox(width: 4),

              // Priority dot
              if (hasPriority) ...[
                Container(
                  width: 6,
                  height: 6,
                  decoration: BoxDecoration(
                    color: _getPriorityColor(priority),
                    shape: BoxShape.circle,
                  ),
                ),
                const SizedBox(width: 4),
              ],

              if (task.isSubtask) ...[
                const Icon(Icons.subdirectory_arrow_right, size: 12, color: Colors.teal),
                const SizedBox(width: 2),
              ],

              // Title (1 line)
              Expanded(
                child: Text(
                  task.title,
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 11.5,
                    fontWeight: FontWeight.w500,
                    decoration: isDone ? TextDecoration.lineThrough : null,
                    color: isDone ? theme.hintColor : theme.colorScheme.onSurface,
                  ),
                ),
              ),

              // Due snippet (if present)
              if (task.due != null) ...[
                const SizedBox(width: 3),
                Text(
                  _formatDue(task.due!),
                  style: const TextStyle(
                    fontSize: 9,
                    color: Colors.blueAccent,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
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
