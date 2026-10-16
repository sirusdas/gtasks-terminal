import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/task_item.dart';
import '../../models/task_view_context.dart';
import '../../providers/task_provider.dart';
import '../screens/ai_chat_screen.dart';

/// Shows a fast, non-intrusive Quick AI Bottom Sheet right over the tasks list.
Future<void> showQuickAiBottomSheet(BuildContext context, TaskViewContext viewCtx) {
  return showModalBottomSheet(
    context: context,
    isScrollControlled: true,
    backgroundColor: Colors.transparent,
    builder: (_) => QuickAiBottomSheet(initialContext: viewCtx),
  );
}

enum _QuickWizardStep { none, title, due, priority, space, confirm }

class QuickAiBottomSheet extends StatefulWidget {
  final TaskViewContext initialContext;

  const QuickAiBottomSheet({super.key, required this.initialContext});

  @override
  State<QuickAiBottomSheet> createState() => _QuickAiBottomSheetState();
}

class _QuickAiBottomSheetState extends State<QuickAiBottomSheet> {
  late bool _isScopedToView;
  late TaskViewContext _currentContext;

  _QuickWizardStep _wizardStep = _QuickWizardStep.none;
  String? _draftTitle;
  String? _draftDue;
  String? _draftPriority;
  String? _draftSpace;

  TaskItem? _highlightedTask;
  String _assistantMessage = '';
  bool _confirmingBulkComplete = false;
  bool _isProcessing = false;

  final TextEditingController _promptController = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    _currentContext = widget.initialContext;
    _isScopedToView = _currentContext.hasAnyFilter && _currentContext.visibleCount > 0;
    _initWelcome();
  }

  @override
  void dispose() {
    _promptController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _initWelcome() {
    final pendingCount = _getTargetTasks().where((t) => !t.isCompleted).length;
    final scopeDesc = _isScopedToView ? _currentContext.filterDescription : 'All Tasks';

    setState(() {
      _assistantMessage = '🎯 **Active Scope: $scopeDesc** ($pendingCount pending tasks)\n'
          'Pick a quick action below or ask any question:';
    });
  }

  List<TaskItem> _getTargetTasks() {
    if (_isScopedToView) {
      return _currentContext.visibleTasks;
    }
    final provider = context.read<TaskProvider>();
    return provider.allTasksUnfiltered;
  }

  void _toggleScope() {
    setState(() {
      _isScopedToView = !_isScopedToView;
      _highlightedTask = null;
      _confirmingBulkComplete = false;
      _wizardStep = _QuickWizardStep.none;
      _initWelcome();
    });
  }

  void _expandToFullScreen() {
    Navigator.pop(context);
    Navigator.push(
      context,
      MaterialPageRoute(
        builder: (_) => AiChatScreen(initialContext: widget.initialContext),
      ),
    );
  }

  void _handleUrgent() {
    setState(() {
      _wizardStep = _QuickWizardStep.none;
      _confirmingBulkComplete = false;
      final pending = _getTargetTasks().where((t) => !t.isCompleted).toList();
      if (pending.isEmpty) {
        _assistantMessage = '✨ No pending tasks found in this view!';
        _highlightedTask = null;
        return;
      }

      const prioWeight = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1};
      pending.sort((a, b) {
        final pa = prioWeight[a.calculatedPriority.toLowerCase()] ?? 2;
        final pb = prioWeight[b.calculatedPriority.toLowerCase()] ?? 2;
        if (pb != pa) return pb.compareTo(pa);
        if (a.due != null && b.due != null) return a.due!.compareTo(b.due!);
        if (a.due != null) return -1;
        if (b.due != null) return 1;
        return 0;
      });

      _highlightedTask = pending.first;
      _assistantMessage = '⚡ **Most Urgent Task in View:**';
    });
  }

  void _handleEarliest() {
    setState(() {
      _wizardStep = _QuickWizardStep.none;
      _confirmingBulkComplete = false;
      final withDue = _getTargetTasks().where((t) => !t.isCompleted && t.due != null).toList();
      if (withDue.isEmpty) {
        _assistantMessage = 'ℹ️ No pending tasks with due dates in this view.';
        _highlightedTask = null;
        return;
      }

      withDue.sort((a, b) => a.due!.compareTo(b.due!));
      _highlightedTask = withDue.first;
      _assistantMessage = '⏰ **Earliest Due Task:** Due ${_highlightedTask!.formattedDueDate}';
    });
  }

  void _handleSummary() {
    setState(() {
      _wizardStep = _QuickWizardStep.none;
      _confirmingBulkComplete = false;
      _highlightedTask = null;

      final tasks = _getTargetTasks();
      final pending = tasks.where((t) => !t.isCompleted).length;
      final completed = tasks.where((t) => t.isCompleted).length;

      final todayStr = DateTime.now().toIso8601String().substring(0, 10);
      final overdue = tasks.where((t) => !t.isCompleted && t.due != null && t.due!.length >= 10 && t.due!.substring(0, 10).compareTo(todayStr) < 0).length;
      final dueToday = tasks.where((t) => !t.isCompleted && t.due != null && t.due!.length >= 10 && t.due!.substring(0, 10) == todayStr).length;
      final highPrio = tasks.where((t) => !t.isCompleted && (t.calculatedPriority == 'high' || t.calculatedPriority == 'critical')).length;

      final scopeDesc = _isScopedToView ? _currentContext.filterDescription : 'All Tasks';

      _assistantMessage = '📊 **Summary for $scopeDesc**\n\n'
          '• **Total:** ${tasks.length} tasks\n'
          '• **Pending:** $pending | **Completed:** $completed\n'
          '• **Due Today:** $dueToday | **Overdue:** $overdue\n'
          '• **High / Critical Priority:** $highPrio';
    });
  }

  void _handleDoneAll() {
    setState(() {
      _wizardStep = _QuickWizardStep.none;
      _highlightedTask = null;
      final pending = _getTargetTasks().where((t) => !t.isCompleted).length;
      if (pending == 0) {
        _assistantMessage = '✨ No pending tasks to complete in this view!';
        _confirmingBulkComplete = false;
      } else {
        _confirmingBulkComplete = true;
        _assistantMessage = '⚠️ **Confirm Bulk Complete**\n\nAre you sure you want to mark all **$pending** visible pending tasks as completed?';
      }
    });
  }

  Future<void> _executeBulkComplete() async {
    final provider = context.read<TaskProvider>();
    final pending = _getTargetTasks().where((t) => !t.isCompleted).toList();
    int count = 0;
    for (final t in pending) {
      final ok = await provider.completeTask(t.id);
      if (ok) count++;
    }
    await provider.refreshTasks();

    setState(() {
      _confirmingBulkComplete = false;
      _assistantMessage = '🎉 **Completed $count task${count == 1 ? "" : "s"}!**';
    });
  }

  void _startWizard() {
    setState(() {
      _confirmingBulkComplete = false;
      _highlightedTask = null;
      _wizardStep = _QuickWizardStep.title;
      _draftTitle = null;
      _draftDue = null;
      _draftPriority = 'medium';
      _draftSpace = _currentContext.selectedSpace;
      _assistantMessage = '🪄 **Task Creation Wizard (Step 1/4)**\nWhat is the **title** of the task?';
    });
    _focusNode.requestFocus();
  }

  void _handleWizardInput(String input) {
    final trimmed = input.trim();
    if (trimmed.toLowerCase() == 'cancel') {
      setState(() {
        _wizardStep = _QuickWizardStep.none;
        _assistantMessage = '🚫 Task creation cancelled.';
      });
      return;
    }

    if (_wizardStep == _QuickWizardStep.title) {
      if (trimmed.isEmpty) return;
      setState(() {
        _draftTitle = trimmed;
        _wizardStep = _QuickWizardStep.due;
        _assistantMessage = '📅 **Step 2/4:** Title: **$_draftTitle**\nWhen is this task **due**? Tap an option or type YYYY-MM-DD:';
      });
      _promptController.clear();
    } else if (_wizardStep == _QuickWizardStep.due) {
      final now = DateTime.now();
      String? dueStr;
      final lower = trimmed.toLowerCase();
      if (lower == 'today') {
        dueStr = now.toIso8601String().substring(0, 10);
      } else if (lower == 'tomorrow') {
        dueStr = now.add(const Duration(days: 1)).toIso8601String().substring(0, 10);
      } else if (lower == 'next week') {
        dueStr = now.add(const Duration(days: 7)).toIso8601String().substring(0, 10);
      } else if (lower == 'skip' || lower == 'none') {
        dueStr = null;
      } else {
        dueStr = trimmed.isNotEmpty ? trimmed : null;
      }

      setState(() {
        _draftDue = dueStr;
        _wizardStep = _QuickWizardStep.priority;
        _assistantMessage = '⚡ **Step 3/4:** What is the **priority**?';
      });
      _promptController.clear();
    } else if (_wizardStep == _QuickWizardStep.priority) {
      String p = 'medium';
      final lower = trimmed.toLowerCase();
      if (lower.contains('high') || lower.contains('critical')) {
        p = 'high';
      } else if (lower.contains('low')) {
        p = 'low';
      }

      setState(() {
        _draftPriority = p;
        _wizardStep = _QuickWizardStep.space;
        final defSpace = _draftSpace != null ? ' (Default: **$_draftSpace**)' : '';
        _assistantMessage = '📁 **Step 4/4:** Priority: **${p.toUpperCase()}**\nWhich **Space** does this belong to?$defSpace';
      });
      _promptController.clear();
    } else if (_wizardStep == _QuickWizardStep.space) {
      final lower = trimmed.toLowerCase();
      if (lower != 'skip' && lower != 'none' && trimmed.isNotEmpty) {
        _draftSpace = trimmed;
      }

      setState(() {
        _wizardStep = _QuickWizardStep.confirm;
        _assistantMessage = '✨ **Review Task Draft:**\n'
            '• **Title:** $_draftTitle\n'
            '• **Due:** ${_draftDue ?? "None"}\n'
            '• **Priority:** ${_draftPriority?.toUpperCase()}\n'
            '• **Space:** ${_draftSpace ?? "None"}';
      });
      _promptController.clear();
    }
  }

  Future<void> _submitWizardTask() async {
    final provider = context.read<TaskProvider>();
    final title = _draftTitle?.trim() ?? 'Untitled Task';

    final Map<String, List<String>> spacesMap = {};
    if (_draftSpace != null && _draftSpace!.isNotEmpty) {
      spacesMap[_draftSpace!] = [];
    }

    final success = await provider.addTask(
      title: title,
      due: _draftDue,
      priority: _draftPriority ?? 'medium',
      spaces: spacesMap,
    );

    if (success) {
      await provider.refreshTasks();
      setState(() {
        _wizardStep = _QuickWizardStep.none;
        _assistantMessage = '🎉 **Task Created Successfully!**\n"$title" was added to ${_draftSpace ?? "your workspace"}.';
      });
    } else {
      setState(() {
        _assistantMessage = '⚠️ Failed to create task. Please try again.';
      });
    }
  }

  Future<void> _handleUserPrompt(String query) async {
    final trimmed = query.trim();
    if (trimmed.isEmpty) return;

    if (_wizardStep != _QuickWizardStep.none) {
      _handleWizardInput(trimmed);
      return;
    }

    final qLower = trimmed.toLowerCase();
    if (qLower == 'urgent' || qLower == '/urgent') {
      _handleUrgent();
      return;
    }
    if (qLower == 'earliest' || qLower == '/earliest') {
      _handleEarliest();
      return;
    }
    if (qLower == 'summary' || qLower == '/summary') {
      _handleSummary();
      return;
    }
    if (qLower == 'wizard' || qLower == '/wizard' || qLower == 'add task') {
      _startWizard();
      return;
    }

    // Process natural language
    setState(() {
      _isProcessing = true;
      _highlightedTask = null;
      _confirmingBulkComplete = false;
    });

    final provider = context.read<TaskProvider>();
    String reply = '';

    try {
      final scopeDesc = _isScopedToView ? _currentContext.filterDescription : 'All Tasks';
      final sampleTasks = _getTargetTasks().take(8).map((t) => '- "${t.title}" (${t.calculatedPriority.toUpperCase()}, due: ${t.formattedDueDate ?? "none"})').join('\n');
      final prompt = 'Context: User viewing $scopeDesc.\nTasks:\n$sampleTasks\n\nQuery: $trimmed';

      final serverReply = await provider.apiClient.chatAi(prompt).timeout(const Duration(milliseconds: 3000));
      if (serverReply.isNotEmpty) {
        reply = serverReply;
      }
    } catch (_) {}

    if (reply.isEmpty) {
      // Local fallback
      final matches = _getTargetTasks().where((t) => t.title.toLowerCase().contains(qLower)).toList();
      if (matches.isNotEmpty) {
        reply = '🔍 Found **${matches.length}** task${matches.length == 1 ? "" : "s"} matching "$trimmed":';
        setState(() {
          _highlightedTask = matches.first;
        });
      } else {
        reply = '🤖 I processed: "$trimmed".\nTry "urgent", "earliest", "summary", or tap a quick pill above.';
      }
    }

    setState(() {
      _isProcessing = false;
      _assistantMessage = reply;
    });
    _promptController.clear();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    final scopeDesc = _isScopedToView ? _currentContext.filterDescription : 'All Tasks';
    final taskCount = _getTargetTasks().length;

    return Container(
      padding: EdgeInsets.only(bottom: bottomInset),
      decoration: const BoxDecoration(
        color: Color(0xFF1E232E),
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
        boxShadow: [
          BoxShadow(
            color: Colors.black54,
            blurRadius: 20,
            offset: Offset(0, -4),
          ),
        ],
      ),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Top drag handle
                Center(
                  child: Container(
                    width: 38,
                    height: 4,
                    decoration: BoxDecoration(
                      color: Colors.white24,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 10),

                // Header Row
                Row(
                  children: [
                    const Icon(Icons.auto_awesome, color: Colors.amber, size: 20),
                    const SizedBox(width: 8),
                    const Text(
                      'Quick AI Assistant',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const Spacer(),
                    // Expand to full chat
                    IconButton(
                      icon: const Icon(Icons.open_in_full, size: 18, color: Colors.white70),
                      tooltip: 'Expand to Full Chat',
                      onPressed: _expandToFullScreen,
                      visualDensity: VisualDensity.compact,
                    ),
                    // Close button
                    IconButton(
                      icon: const Icon(Icons.close, size: 18, color: Colors.white70),
                      tooltip: 'Close',
                      onPressed: () => Navigator.pop(context),
                      visualDensity: VisualDensity.compact,
                    ),
                  ],
                ),

                // Scope Banner Pill
                Container(
                  margin: const EdgeInsets.symmetric(vertical: 6),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: _isScopedToView ? const Color(0xFF1E3A8A).withOpacity(0.4) : Colors.white10,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: _isScopedToView ? Colors.blue.withOpacity(0.4) : Colors.white24,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        _isScopedToView ? Icons.filter_center_focus : Icons.public,
                        size: 14,
                        color: _isScopedToView ? Colors.lightBlueAccent : Colors.white60,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          _isScopedToView ? 'VIEW SCOPE: $scopeDesc ($taskCount tasks)' : 'GLOBAL SCOPE: All Tasks ($taskCount)',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w600,
                            color: _isScopedToView ? Colors.lightBlueAccent : Colors.white70,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                      InkWell(
                        onTap: _toggleScope,
                        borderRadius: BorderRadius.circular(6),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                          child: Text(
                            _isScopedToView ? 'Switch to All' : 'Switch to View',
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: Colors.amberAccent,
                            ),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),

                // Quick Action Chips Row
                SingleChildScrollView(
                  scrollDirection: Axis.horizontal,
                  child: Row(
                    children: [
                      _buildActionChip(
                        label: '🪄 Wizard',
                        color: Colors.purpleAccent,
                        onTap: _startWizard,
                      ),
                      _buildActionChip(
                        label: '⚡ Urgent',
                        color: Colors.amberAccent,
                        onTap: _handleUrgent,
                      ),
                      _buildActionChip(
                        label: '⏰ Earliest',
                        color: Colors.lightBlueAccent,
                        onTap: _handleEarliest,
                      ),
                      _buildActionChip(
                        label: '📊 Summary',
                        color: Colors.greenAccent,
                        onTap: _handleSummary,
                      ),
                      _buildActionChip(
                        label: '✅ Done All',
                        color: Colors.pinkAccent,
                        onTap: _handleDoneAll,
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 8),

                // Response / Result Box
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFF151A23),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: Colors.white12),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      if (_isProcessing)
                        const Row(
                          children: [
                            SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)),
                            SizedBox(width: 10),
                            Text('Thinking...', style: TextStyle(color: Colors.white70, fontSize: 12)),
                          ],
                        )
                      else
                        Text(
                          _assistantMessage,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12.5,
                            height: 1.4,
                          ),
                        ),

                      // Highlighted Task Card (if urgent or earliest selected)
                      if (_highlightedTask != null) ...[
                        const SizedBox(height: 8),
                        _buildTaskPreviewCard(_highlightedTask!),
                      ],

                      // Bulk Complete Confirmation Buttons
                      if (_confirmingBulkComplete) ...[
                        const SizedBox(height: 10),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            TextButton(
                              onPressed: () {
                                setState(() {
                                  _confirmingBulkComplete = false;
                                  _assistantMessage = '🚫 Bulk completion cancelled.';
                                });
                              },
                              child: const Text('Cancel', style: TextStyle(color: Colors.white60)),
                            ),
                            const SizedBox(width: 8),
                            ElevatedButton(
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.green.shade600),
                              onPressed: _executeBulkComplete,
                              child: const Text('Yes, Complete All', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                            ),
                          ],
                        ),
                      ],

                      // Wizard Quick Options (if in wizard)
                      if (_wizardStep == _QuickWizardStep.due) ...[
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 6,
                          children: [
                            _buildChoicePill('Today', () => _handleWizardInput('Today')),
                            _buildChoicePill('Tomorrow', () => _handleWizardInput('Tomorrow')),
                            _buildChoicePill('Next Week', () => _handleWizardInput('Next Week')),
                            _buildChoicePill('Skip', () => _handleWizardInput('Skip')),
                            _buildChoicePill('Cancel', () => _handleWizardInput('Cancel'), isCancel: true),
                          ],
                        ),
                      ] else if (_wizardStep == _QuickWizardStep.priority) ...[
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 6,
                          children: [
                            _buildChoicePill('High', () => _handleWizardInput('High')),
                            _buildChoicePill('Medium', () => _handleWizardInput('Medium')),
                            _buildChoicePill('Low', () => _handleWizardInput('Low')),
                            _buildChoicePill('Cancel', () => _handleWizardInput('Cancel'), isCancel: true),
                          ],
                        ),
                      ] else if (_wizardStep == _QuickWizardStep.space) ...[
                        const SizedBox(height: 8),
                        Wrap(
                          spacing: 6,
                          children: [
                            if (_draftSpace != null)
                              _buildChoicePill(_draftSpace!, () => _handleWizardInput(_draftSpace!)),
                            _buildChoicePill('Skip', () => _handleWizardInput('Skip')),
                            _buildChoicePill('Cancel', () => _handleWizardInput('Cancel'), isCancel: true),
                          ],
                        ),
                      ] else if (_wizardStep == _QuickWizardStep.confirm) ...[
                        const SizedBox(height: 10),
                        Row(
                          mainAxisAlignment: MainAxisAlignment.end,
                          children: [
                            TextButton(
                              onPressed: () {
                                setState(() {
                                  _wizardStep = _QuickWizardStep.none;
                                  _assistantMessage = '🚫 Task creation cancelled.';
                                });
                              },
                              child: const Text('Cancel', style: TextStyle(color: Colors.white60)),
                            ),
                            const SizedBox(width: 8),
                            ElevatedButton.icon(
                              style: ElevatedButton.styleFrom(backgroundColor: Colors.blue.shade600),
                              icon: const Icon(Icons.check, size: 16),
                              label: const Text('Create Task', style: TextStyle(color: Colors.white, fontWeight: FontWeight.bold)),
                              onPressed: _submitWizardTask,
                            ),
                          ],
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 8),

                // Bottom Input Row
                Row(
                  children: [
                    Expanded(
                      child: TextField(
                        controller: _promptController,
                        focusNode: _focusNode,
                        style: const TextStyle(color: Colors.white, fontSize: 13),
                        decoration: InputDecoration(
                          hintText: _wizardStep != _QuickWizardStep.none
                              ? 'Enter input for wizard...'
                              : 'Ask AI or type command...',
                          hintStyle: const TextStyle(color: Colors.white38, fontSize: 13),
                          filled: true,
                          fillColor: const Color(0xFF252D3D),
                          contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                          border: OutlineInputBorder(
                            borderRadius: BorderRadius.circular(10),
                            borderSide: BorderSide.none,
                          ),
                        ),
                        onSubmitted: (val) {
                          _handleUserPrompt(val);
                        },
                      ),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue.shade600,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                        visualDensity: VisualDensity.compact,
                      ),
                      onPressed: () {
                        _handleUserPrompt(_promptController.text);
                      },
                      child: const Icon(Icons.arrow_upward, size: 18, color: Colors.white),
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildActionChip({required String label, required Color color, required VoidCallback onTap}) {
    return Padding(
      padding: const EdgeInsets.only(right: 6),
      child: ActionChip(
        label: Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: color)),
        backgroundColor: const Color(0xFF252D3D),
        side: BorderSide(color: color.withOpacity(0.4)),
        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
        visualDensity: VisualDensity.compact,
        onPressed: onTap,
      ),
    );
  }

  Widget _buildChoicePill(String label, VoidCallback onTap, {bool isCancel = false}) {
    return ActionChip(
      label: Text(
        label,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: isCancel ? Colors.redAccent : Colors.white,
        ),
      ),
      backgroundColor: isCancel ? Colors.red.withOpacity(0.15) : const Color(0xFF2D3748),
      side: BorderSide(color: isCancel ? Colors.redAccent.withOpacity(0.4) : Colors.white24),
      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 0),
      visualDensity: VisualDensity.compact,
      onPressed: onTap,
    );
  }

  Widget _buildTaskPreviewCard(TaskItem task) {
    final provider = context.read<TaskProvider>();
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: const Color(0xFF252D3D),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: Colors.white12),
      ),
      child: Row(
        children: [
          IconButton(
            icon: Icon(
              task.isCompleted ? Icons.check_circle : Icons.radio_button_unchecked,
              color: task.isCompleted ? Colors.green : Colors.white54,
              size: 20,
            ),
            visualDensity: VisualDensity.compact,
            onPressed: () async {
              await provider.completeTask(task.id);
              await provider.refreshTasks();
              setState(() {
                _assistantMessage = '🎉 Marked "${task.title}" as completed!';
                _highlightedTask = null;
              });
            },
          ),
          const SizedBox(width: 6),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  task.title,
                  style: const TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 12.5,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 1),
                      decoration: BoxDecoration(
                        color: Colors.orange.withOpacity(0.2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        task.calculatedPriority.toUpperCase(),
                        style: const TextStyle(color: Colors.orange, fontSize: 9, fontWeight: FontWeight.bold),
                      ),
                    ),
                    if (task.formattedDueDate != null) ...[
                      const SizedBox(width: 6),
                      Text(
                        task.formattedDueDate!,
                        style: const TextStyle(color: Colors.white60, fontSize: 10),
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
          TextButton(
            style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
            onPressed: () async {
              await provider.completeTask(task.id);
              await provider.refreshTasks();
              setState(() {
                _assistantMessage = '🎉 Marked "${task.title}" as completed!';
                _highlightedTask = null;
              });
            },
            child: const Text('Complete', style: TextStyle(color: Colors.greenAccent, fontSize: 11)),
          ),
        ],
      ),
    );
  }
}
