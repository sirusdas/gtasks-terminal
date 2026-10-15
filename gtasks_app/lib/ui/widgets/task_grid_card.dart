import 'package:flutter/material.dart';
import '../../models/task_item.dart';
import 'task_detail_modal.dart';

class TaskGridCard extends StatelessWidget {
  final TaskItem task;
  final VoidCallback onToggleComplete;
  final VoidCallback? onEdit;
  final VoidCallback? onDelete;

  const TaskGridCard({
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
        borderRadius: BorderRadius.circular(10),
        side: BorderSide(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5),
        ),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(10),
        onTap: () => _openQuickView(context),
        child: Padding(
          padding: const EdgeInsets.all(10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top Row: Checkbox + Priority
              Row(
                children: [
                  InkWell(
                    borderRadius: BorderRadius.circular(14),
                    onTap: onToggleComplete,
                    child: Icon(
                      isDone ? Icons.check_circle : Icons.radio_button_unchecked,
                      color: isDone ? Colors.green : theme.colorScheme.primary,
                      size: 20,
                    ),
                  ),
                  const Spacer(),
                  if (hasPriority)
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1.5),
                      decoration: BoxDecoration(
                        color: _getPriorityColor(priority).withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        priority.toUpperCase(),
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.bold,
                          color: _getPriorityColor(priority),
                        ),
                      ),
                    ),
                ],
              ),
              const SizedBox(height: 6),

              // Title (2 lines max)
              Expanded(
                child: Text(
                  task.title,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                    decoration: isDone ? TextDecoration.lineThrough : null,
                    color: isDone ? theme.hintColor : theme.colorScheme.onSurface,
                  ),
                ),
              ),

              const SizedBox(height: 4),

              // Footer: Space / Due
              Row(
                children: [
                  if (task.spaces.isNotEmpty)
                    Expanded(
                      child: Text(
                        task.spaces.keys.first,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(fontSize: 10, color: Colors.deepPurple, fontWeight: FontWeight.bold),
                      ),
                    )
                  else if (task.listTitle != null && task.listTitle != 'My Tasks')
                    Expanded(
                      child: Text(
                        task.listTitle!,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: TextStyle(fontSize: 10, color: theme.hintColor),
                      ),
                    )
                  else
                    const Spacer(),
                  if (task.due != null) ...[
                    const Icon(Icons.schedule, size: 10, color: Colors.blueAccent),
                    const SizedBox(width: 2),
                    Text(
                      _formatDue(task.due!),
                      style: const TextStyle(fontSize: 10, color: Colors.blueAccent, fontWeight: FontWeight.bold),
                    ),
                  ],
                ],
              ),
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
