import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';
import '../widgets/task_detail_modal.dart';
import '../widgets/task_editor_dialog.dart';

enum ChatSender { user, assistant }

enum WizardStep {
  none,
  addingTitle,
  addingDue,
  addingPriority,
  addingSpace,
  updatingSelectTask,
  updatingSelectField,
  updatingFieldValue,
  completingSelectTask,
  deletingSelectTask,
  searchingKeyword,
}

class ChatMessage {
  final String id;
  final ChatSender sender;
  final String text;
  final DateTime timestamp;
  final List<TaskItem>? taskItems;
  final List<String>? suggestionChips;
  final bool isError;

  ChatMessage({
    required this.id,
    required this.sender,
    required this.text,
    DateTime? timestamp,
    this.taskItems,
    this.suggestionChips,
    this.isError = false,
  }) : timestamp = timestamp ?? DateTime.now();
}

class AiChatScreen extends StatefulWidget {
  const AiChatScreen({super.key});

  @override
  State<AiChatScreen> createState() => _AiChatScreenState();
}

class _AiChatScreenState extends State<AiChatScreen> {
  final List<ChatMessage> _messages = [];
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  bool _isProcessing = false;

  // Conversational Wizard State
  WizardStep _wizardStep = WizardStep.none;
  String? _draftTitle;
  String? _draftDue;
  String? _draftPriority;
  Map<String, List<String>>? _draftSpaces;
  TaskItem? _targetTaskForUpdate;
  String? _targetFieldForUpdate;

  final List<String> _quickActionPills = [
    '📊 Summary',
    '⏳ Pending Tasks',
    '📅 Due Today',
    '⚡ High Priority',
    '➕ Add Task',
    '🌌 Spaces',
    '🚨 Overdue',
    '❓ Help & Menu',
  ];

  @override
  void initState() {
    super.initState();
    _messages.add(
      ChatMessage(
        id: 'welcome',
        sender: ChatSender.assistant,
        text: '👋 Hi! I am your **GTasks AI Assistant**.\n\n'
            'I can help you add tasks step-by-step, review deadlines, prioritize your work, or organize spaces.\n\n'
            'Tap any quick action pill below, choose a command, or ask naturally!',
        suggestionChips: [
          '📊 Summary',
          '⏳ Pending Tasks',
          '📅 Due Today',
          '⚡ High Priority',
          '➕ Add Task',
          '🌌 Spaces',
          '❓ Help & Menu',
        ],
      ),
    );
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  bool _isTaskOverdue(TaskItem t) {
    if (t.isCompleted || t.formattedDueDate == null) return false;
    try {
      final dueDate = DateTime.parse(t.formattedDueDate!);
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      return dueDate.isBefore(today);
    } catch (_) {
      return false;
    }
  }

  bool _isTaskDueToday(TaskItem t) {
    if (t.isCompleted || t.formattedDueDate == null) return false;
    final todayStr = DateFormat('yyyy-MM-dd').format(DateTime.now());
    return t.formattedDueDate == todayStr;
  }

  Future<void> _handleSubmitted(String text) async {
    final query = text.trim();
    if (query.isEmpty || _isProcessing) return;

    _inputController.clear();
    setState(() {
      _messages.add(
        ChatMessage(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          sender: ChatSender.user,
          text: query,
        ),
      );
      _isProcessing = true;
    });
    _scrollToBottom();

    final provider = context.read<TaskProvider>();
    String replyText = '';
    List<TaskItem>? actionTasks;
    List<String>? suggestionChips;
    bool isError = false;

    try {
      // 1. Check for cancel / exit during wizard
      final qLower = query.toLowerCase();
      if (qLower == 'cancel' || qLower == 'exit' || qLower == 'stop' || qLower == 'reset') {
        _resetWizard();
        replyText = '🚫 Action canceled. How else can I assist you?';
        suggestionChips = ['⏳ Pending Tasks', '📅 Due Today', '➕ Add Task', '📊 Summary'];
      }
      // 2. Active Conversational Wizard takes precedence
      else if (_wizardStep != WizardStep.none) {
        final stepResult = await _handleWizardStep(query, provider);
        replyText = stepResult.text;
        actionTasks = stepResult.tasks;
        suggestionChips = stepResult.chips;
      }
      // 3. Easy Picks by number (1 to 12) or quick menus
      else if (_isQuickPick(query)) {
        final pickResult = await _handleQuickPick(query, provider);
        replyText = pickResult.text;
        actionTasks = pickResult.tasks;
        suggestionChips = pickResult.chips;
      }
      // 4. Try backend server if available
      else {
        bool backendHandled = false;
        try {
          final serverReply = await provider.apiClient.chatAi(query).timeout(const Duration(milliseconds: 3500));
          if (serverReply.isNotEmpty) {
            replyText = serverReply;
            backendHandled = true;
            await provider.refreshTasks();
            suggestionChips = ['⏳ Pending Tasks', '📅 Due Today', '➕ Add Task', '📊 Summary'];
          }
        } catch (_) {
          backendHandled = false;
        }

        // 5. Local intelligent processor fallback
        if (!backendHandled) {
          final localResult = await _processQueryLocally(query, provider);
          replyText = localResult.text;
          actionTasks = localResult.tasks;
          suggestionChips = localResult.chips;
        }
      }
    } catch (e) {
      isError = true;
      replyText = '⚠️ An issue occurred: $e';
      suggestionChips = ['❓ Help & Menu', '⏳ Pending Tasks'];
    } finally {
      if (mounted) {
        setState(() {
          _isProcessing = false;
          _messages.add(
            ChatMessage(
              id: DateTime.now().millisecondsSinceEpoch.toString(),
              sender: ChatSender.assistant,
              text: replyText,
              taskItems: actionTasks,
              suggestionChips: suggestionChips,
              isError: isError,
            ),
          );
        });
        _scrollToBottom();
      }
    }
  }

  void _resetWizard() {
    _wizardStep = WizardStep.none;
    _draftTitle = null;
    _draftDue = null;
    _draftPriority = null;
    _draftSpaces = null;
    _targetTaskForUpdate = null;
    _targetFieldForUpdate = null;
  }

  bool _isQuickPick(String query) {
    final trimmed = query.trim();
    final numVal = int.tryParse(trimmed);
    if (numVal != null && numVal >= 1 && numVal <= 12) return true;
    final lower = trimmed.toLowerCase();
    return lower == 'help' ||
        lower == 'menu' ||
        lower == 'picks' ||
        lower == 'easy picks' ||
        lower == 'options' ||
        lower == '?';
  }

  Future<_LocalQueryResult> _handleQuickPick(String query, TaskProvider provider) async {
    final trimmed = query.trim();
    final numVal = int.tryParse(trimmed);
    final lower = trimmed.toLowerCase();

    // 1: Pending Tasks
    if (numVal == 1 || lower.contains('pending')) {
      final pending = provider.tasks.where((t) => !t.isCompleted).take(10).toList();
      if (pending.isEmpty) {
        return _LocalQueryResult(
          text: '🎉 Awesome! You have no pending tasks right now.',
          chips: ['➕ Add Task', '📊 Summary'],
        );
      }
      return _LocalQueryResult(
        text: '⏳ **Pending Tasks (${pending.length}):**',
        tasks: pending,
        chips: ['📅 Due Today', '⚡ High Priority', '➕ Add Task', '📊 Summary'],
      );
    }

    // 2: Overdue Tasks
    if (numVal == 2 || lower.contains('overdue')) {
      final overdue = provider.tasks.where(_isTaskOverdue).toList();
      if (overdue.isEmpty) {
        return _LocalQueryResult(
          text: '✨ Great job! You have zero overdue tasks.',
          chips: ['📅 Due Today', '⏳ Pending Tasks', '📊 Summary'],
        );
      }
      return _LocalQueryResult(
        text: '🚨 **Overdue Tasks (${overdue.length}):**',
        tasks: overdue,
        chips: ['📅 Due Today', '⚡ High Priority', '📊 Summary'],
      );
    }

    // 3: Due Today
    if (numVal == 3 || lower.contains('due today') || lower == 'today') {
      final dueToday = provider.tasks.where(_isTaskDueToday).toList();
      if (dueToday.isEmpty) {
        return _LocalQueryResult(
          text: '🎉 No tasks due today! Enjoy your day or plan ahead.',
          chips: ['⏳ Pending Tasks', '➕ Add Task', '📊 Summary'],
        );
      }
      return _LocalQueryResult(
        text: '📅 **Tasks Due Today (${dueToday.length}):**',
        tasks: dueToday,
        chips: ['⏳ Pending Tasks', '⚡ High Priority', '➕ Add Task', '📊 Summary'],
      );
    }

    // 4: High / Critical Priority
    if (numVal == 4 || lower.contains('high') || lower.contains('critical') || lower.contains('urgent')) {
      final highPrio = provider.tasks
          .where((t) => !t.isCompleted && (t.calculatedPriority == 'high' || t.calculatedPriority == 'critical'))
          .toList();
      if (highPrio.isEmpty) {
        return _LocalQueryResult(
          text: '✨ No high or critical priority tasks pending!',
          chips: ['⏳ Pending Tasks', '📅 Due Today', '➕ Add Task'],
        );
      }
      return _LocalQueryResult(
        text: '⚡ **High & Critical Priority Tasks (${highPrio.length}):**',
        tasks: highPrio,
        chips: ['📅 Due Today', '⏳ Pending Tasks', '📊 Summary'],
      );
    }

    // 5: Add Task (Launch Wizard)
    if (numVal == 5 || lower.contains('add task') || lower == 'add') {
      _wizardStep = WizardStep.addingTitle;
      return _LocalQueryResult(
        text: '📝 **New Task Wizard**\n\nWhat would you like the task title to be?',
        chips: ['📝 Open Full Form', '🚫 Cancel'],
      );
    }

    // 6: Update Task
    if (numVal == 6 || lower.contains('update') || lower.contains('edit')) {
      final pending = provider.tasks.where((t) => !t.isCompleted).take(6).toList();
      if (pending.isEmpty) {
        return _LocalQueryResult(
          text: 'No pending tasks available to update.',
          chips: ['➕ Add Task', '📊 Summary'],
        );
      }
      _wizardStep = WizardStep.updatingSelectTask;
      return _LocalQueryResult(
        text: '✏️ **Which task would you like to update?**\n'
            'Type the task title, number, or tap an option below:',
        tasks: pending,
        chips: [...pending.map((t) => 'Edit "${t.title}"'), '🚫 Cancel'],
      );
    }

    // 7: Mark Done
    if (numVal == 7 || lower.contains('mark done') || lower.contains('complete')) {
      final pending = provider.tasks.where((t) => !t.isCompleted).take(8).toList();
      if (pending.isEmpty) {
        return _LocalQueryResult(
          text: '🎉 All tasks are already completed!',
          chips: ['➕ Add Task', '📊 Summary'],
        );
      }
      _wizardStep = WizardStep.completingSelectTask;
      return _LocalQueryResult(
        text: '✅ **Which task would you like to mark as completed?**\n'
            'Tap the checkbox directly on any card below or type its title:',
        tasks: pending,
        chips: ['🚫 Cancel'],
      );
    }

    // 8: Delete Task
    if (numVal == 8 || lower.contains('delete') || lower.contains('remove')) {
      final pending = provider.tasks.where((t) => !t.isCompleted).take(8).toList();
      if (pending.isEmpty) {
        return _LocalQueryResult(
          text: 'No pending tasks to delete.',
          chips: ['➕ Add Task', '📊 Summary'],
        );
      }
      _wizardStep = WizardStep.deletingSelectTask;
      return _LocalQueryResult(
        text: '🗑️ **Which task would you like to delete?**\n'
            'Tap the delete icon on any card below or type its title:',
        tasks: pending,
        chips: ['🚫 Cancel'],
      );
    }

    // 9: Search Tasks
    if (numVal == 9 || lower == 'search') {
      _wizardStep = WizardStep.searchingKeyword;
      return _LocalQueryResult(
        text: '🔍 **What keyword or tag would you like to search for?**',
        chips: ['🚫 Cancel'],
      );
    }

    // 10: Spaces
    if (numVal == 10 || lower.contains('space')) {
      final spacesMap = provider.spacesWithCounts;
      if (spacesMap.isEmpty) {
        return _LocalQueryResult(
          text: '🌌 No spaces defined yet. Add spaces like `work:frontend` or `#space` to tasks.',
          chips: ['➕ Add Task', '📊 Summary'],
        );
      }
      final buffer = StringBuffer('🌌 **Spaces & Task Counts:**\n\n');
      spacesMap.forEach((sp, count) {
        buffer.writeln('• **$sp** ($count tasks)');
      });
      return _LocalQueryResult(
        text: buffer.toString(),
        chips: [...spacesMap.keys.take(4).map((s) => 'Space: $s'), '➕ Add Task'],
      );
    }

    // 11: Summary
    if (numVal == 11 || lower.contains('summary') || lower.contains('stats')) {
      return _buildSummaryResult(provider);
    }

    // 12 or Help / Menu:
    return _buildHelpMenu();
  }

  _LocalQueryResult _buildHelpMenu() {
    return _LocalQueryResult(
      text: '🤖 **GTasks AI Interactive Menu & Easy Picks**\n\n'
          'Enter a number `1` - `12` or tap any option below:\n\n'
          '1️⃣ **Pending Tasks** - View active to-dos\n'
          '2️⃣ **Overdue Tasks** - Deadlines requiring attention\n'
          '3️⃣ **Due Today** - Tasks scheduled for today\n'
          '4️⃣ **High Priority** - Urgent & critical tasks\n'
          '5️⃣ **Add Task** - Guided step-by-step wizard\n'
          '6️⃣ **Update Task** - Modify title, date, priority, or space\n'
          '7️⃣ **Mark Done** - Complete tasks interactively\n'
          '8️⃣ **Delete Task** - Safely remove tasks\n'
          '9️⃣ **Search** - Find by title, tag, or notes\n'
          '🔟 **Spaces** - Browse spaces & subspaces\n'
          '1️⃣1️⃣ **Summary** - Productivity statistics\n'
          '1️⃣2️⃣ **AI Tips** - Natural language query examples',
      chips: [
        '1. ⏳ Pending',
        '2. 🚨 Overdue',
        '3. 📅 Due Today',
        '4. ⚡ High Priority',
        '5. ➕ Add Task',
        '6. ✏️ Update Task',
        '7. ✅ Mark Done',
        '8. 🗑️ Delete Task',
        '9. 🔍 Search',
        '10. 🌌 Spaces',
        '11. 📊 Summary',
      ],
    );
  }

  _LocalQueryResult _buildSummaryResult(TaskProvider provider) {
    final total = provider.tasks.length;
    final pending = provider.pendingTasksCount;
    final completed = provider.tasks.where((t) => t.isCompleted).length;
    final overdue = provider.tasks.where(_isTaskOverdue).length;
    final highPrio = provider.tasks
        .where((t) => !t.isCompleted && (t.calculatedPriority == 'high' || t.calculatedPriority == 'critical'))
        .length;

    final summary = '📊 **Productivity Summary**\n\n'
        '• **Total Tasks:** $total\n'
        '• **Pending:** $pending\n'
        '• **Completed:** $completed\n'
        '• **Overdue:** $overdue\n'
        '• **High / Critical Priority:** $highPrio\n'
        '• **Completion Rate:** ${total > 0 ? ((completed / total) * 100).toStringAsFixed(1) : 0}%';

    return _LocalQueryResult(
      text: summary,
      chips: ['📅 Due Today', '🚨 Overdue', '⏳ Pending Tasks', '➕ Add Task'],
    );
  }

  Future<_LocalQueryResult> _handleWizardStep(String query, TaskProvider provider) async {
    final qTrim = query.trim();
    final qLower = qTrim.toLowerCase();

    // Check if user tapped Open Full Form
    if (qLower.contains('full form') || qLower.contains('open form')) {
      _resetWizard();
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const TaskEditorDialog(isFullScreen: true)),
          );
        }
      });
      return _LocalQueryResult(
        text: '📝 Opening the Full Task Editor for you...',
        chips: ['⏳ Pending Tasks', '📊 Summary'],
      );
    }

    switch (_wizardStep) {
      case WizardStep.addingTitle:
        _draftTitle = qTrim;
        _wizardStep = WizardStep.addingDue;
        return _LocalQueryResult(
          text: 'Got it: **"$_draftTitle"**.\n\n📅 **When is this task due?**\n'
              'Tap an option below or type a date (e.g. tomorrow, Friday, 2026-10-25):',
          chips: [
            '📅 Today',
            '🌅 Tomorrow',
            '🗓 End of Week',
            '⏩ Next Week',
            '🚫 No Due Date',
            '🚫 Cancel',
          ],
        );

      case WizardStep.addingDue:
        final now = DateTime.now();
        if (qLower.contains('today')) {
          _draftDue = DateFormat('yyyy-MM-dd').format(now);
        } else if (qLower.contains('tomorrow')) {
          _draftDue = DateFormat('yyyy-MM-dd').format(now.add(const Duration(days: 1)));
        } else if (qLower.contains('end of week')) {
          final daysUntilSunday = DateTime.sunday - now.weekday;
          _draftDue = DateFormat('yyyy-MM-dd').format(now.add(Duration(days: daysUntilSunday <= 0 ? 7 : daysUntilSunday)));
        } else if (qLower.contains('next week')) {
          _draftDue = DateFormat('yyyy-MM-dd').format(now.add(const Duration(days: 7)));
        } else if (qLower.contains('no due date') || qLower.contains('skip') || qLower.contains('none')) {
          _draftDue = null;
        } else {
          // Attempt custom date parse or keep string
          try {
            final parsed = DateTime.parse(qTrim);
            _draftDue = DateFormat('yyyy-MM-dd').format(parsed);
          } catch (_) {
            _draftDue = qTrim;
          }
        }

        _wizardStep = WizardStep.addingPriority;
        return _LocalQueryResult(
          text: '⚡ **What priority level should we set?**',
          chips: ['🟢 Low', '🔵 Normal', '🟠 High', '🔴 Critical', '🚫 Cancel'],
        );

      case WizardStep.addingPriority:
        if (qLower.contains('critical') || qLower.contains('red')) {
          _draftPriority = 'critical';
        } else if (qLower.contains('high') || qLower.contains('orange')) {
          _draftPriority = 'high';
        } else if (qLower.contains('low') || qLower.contains('green')) {
          _draftPriority = 'low';
        } else {
          _draftPriority = 'normal';
        }

        _wizardStep = WizardStep.addingSpace;
        final spaces = provider.spacesWithCounts.keys.take(4).toList();
        return _LocalQueryResult(
          text: '🌌 **Assign to a Space?** (Optional)\n'
              'Tap a space below, type a space name (e.g. `work:frontend`), or tap Skip:',
          chips: [
            ...spaces.map((s) => 'Space: $s'),
            '🚫 Skip Space',
            '🚫 Cancel',
          ],
        );

      case WizardStep.addingSpace:
        if (!qLower.contains('skip') && !qLower.contains('none') && !qLower.contains('no space')) {
          final spaceClean = qTrim.replaceFirst(RegExp(r'^(?:space:\s*|space\s+)', caseSensitive: false), '').trim();
          if (spaceClean.isNotEmpty) {
            final parts = spaceClean.split(':');
            final spName = parts[0];
            final subNames = parts.length > 1 ? parts.sublist(1) : <String>[];
            _draftSpaces = {spName: subNames};
          }
        }

        // Finalize task creation!
        final title = _draftTitle ?? 'New Task';
        final success = await provider.addTask(
          title: title,
          due: _draftDue,
          priority: _draftPriority ?? 'normal',
          spaces: _draftSpaces,
        );

        _resetWizard();

        if (success) {
          final added = provider.tasks.isNotEmpty ? provider.tasks.first : null;
          return _LocalQueryResult(
            text: '✨ **Task created successfully!**\n\n'
                '• **Title:** $title\n'
                '• **Due:** ${_draftDue ?? "No due date"}\n'
                '• **Priority:** ${(_draftPriority ?? "normal").toUpperCase()}\n'
                '• **Space:** ${_draftSpaces != null ? _draftSpaces!.keys.join(", ") : "None"}',
            tasks: added != null ? [added] : null,
            chips: ['➕ Add Another Task', '⏳ Pending Tasks', '📅 Due Today', '📊 Summary'],
          );
        } else {
          return _LocalQueryResult(
            text: '⚠️ Failed to create task. Please check storage connection.',
            chips: ['➕ Try Again', '📊 Summary'],
          );
        }

      case WizardStep.updatingSelectTask:
        final task = _findTask(qTrim.replaceAll(RegExp(r'^edit\s*"?|"?$', caseSensitive: false), ''), provider);
        if (task == null) {
          return _LocalQueryResult(
            text: '❓ Could not find task matching "$qTrim". Please type the exact name or number:',
            chips: ['🚫 Cancel'],
          );
        }
        _targetTaskForUpdate = task;
        _wizardStep = WizardStep.updatingSelectField;
        return _LocalQueryResult(
          text: '✏️ Selected **${task.title}**.\n\nWhat would you like to update?',
          tasks: [task],
          chips: [
            '✏️ Change Title',
            '📅 Change Due Date',
            '⚡ Change Priority',
            '🌌 Change Space',
            '✅ Mark Completed',
            '🚫 Cancel',
          ],
        );

      case WizardStep.updatingSelectField:
        final target = _targetTaskForUpdate;
        if (target == null) {
          _resetWizard();
          return _LocalQueryResult(text: 'Update session expired. Please start again.', chips: ['✏️ Update Task']);
        }

        if (qLower.contains('title')) {
          _targetFieldForUpdate = 'title';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(text: 'Enter the new title for **${target.title}**:', chips: ['🚫 Cancel']);
        } else if (qLower.contains('due') || qLower.contains('date')) {
          _targetFieldForUpdate = 'due';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(
            text: 'Enter new due date (or tap preset):',
            chips: ['📅 Today', '🌅 Tomorrow', '🗓 Next Week', '🚫 No Due Date', '🚫 Cancel'],
          );
        } else if (qLower.contains('priority')) {
          _targetFieldForUpdate = 'priority';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(
            text: 'Select new priority:',
            chips: ['🟢 Low', '🔵 Normal', '🟠 High', '🔴 Critical', '🚫 Cancel'],
          );
        } else if (qLower.contains('space')) {
          _targetFieldForUpdate = 'space';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(
            text: 'Enter space name or tap an existing space:',
            chips: [...provider.spacesWithCounts.keys.take(4).map((s) => 'Space: $s'), '🚫 Clear Space', '🚫 Cancel'],
          );
        } else if (qLower.contains('complete') || qLower.contains('mark done')) {
          await provider.completeTask(target.id);
          _resetWizard();
          return _LocalQueryResult(
            text: '✅ Marked **${target.title}** as completed!',
            chips: ['⏳ Pending Tasks', '📊 Summary'],
          );
        }
        return _LocalQueryResult(
          text: 'Please select what to update:',
          chips: ['✏️ Change Title', '📅 Change Due Date', '⚡ Change Priority', '🌌 Change Space', '🚫 Cancel'],
        );

      case WizardStep.updatingFieldValue:
        final target = _targetTaskForUpdate;
        final field = _targetFieldForUpdate;
        if (target == null || field == null) {
          _resetWizard();
          return _LocalQueryResult(text: 'Update session expired. Please start again.', chips: ['✏️ Update Task']);
        }

        bool success = false;
        if (field == 'title') {
          success = await provider.updateTask(taskId: target.id, title: qTrim);
        } else if (field == 'due') {
          String? newDue;
          if (qLower.contains('today')) {
            newDue = DateFormat('yyyy-MM-dd').format(DateTime.now());
          } else if (qLower.contains('tomorrow')) {
            newDue = DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 1)));
          } else if (qLower.contains('next week')) {
            newDue = DateFormat('yyyy-MM-dd').format(DateTime.now().add(const Duration(days: 7)));
          } else if (qLower.contains('no due date') || qLower.contains('clear')) {
            newDue = '';
          } else {
            newDue = qTrim;
          }
          success = await provider.updateTask(taskId: target.id, title: target.title, due: newDue);
        } else if (field == 'priority') {
          String prio = 'normal';
          if (qLower.contains('critical')) {
            prio = 'critical';
          } else if (qLower.contains('high')) {
            prio = 'high';
          } else if (qLower.contains('low')) {
            prio = 'low';
          }
          success = await provider.updateTask(taskId: target.id, title: target.title, priority: prio);
        } else if (field == 'space') {
          Map<String, List<String>> spaces = {};
          if (!qLower.contains('clear') && !qLower.contains('none')) {
            final spClean = qTrim.replaceFirst(RegExp(r'^(?:space:\s*|space\s+)', caseSensitive: false), '').trim();
            final parts = spClean.split(':');
            spaces[parts[0]] = parts.length > 1 ? parts.sublist(1) : [];
          }
          success = await provider.updateTask(taskId: target.id, title: target.title, spaces: spaces);
        }

        _resetWizard();
        if (success) {
          final updated = provider.tasks.firstWhere((t) => t.id == target.id, orElse: () => target);
          return _LocalQueryResult(
            text: '✨ Updated **${target.title}** successfully!',
            tasks: [updated],
            chips: ['⏳ Pending Tasks', '📅 Due Today', '📊 Summary'],
          );
        } else {
          return _LocalQueryResult(text: '⚠️ Could not update task.', chips: ['✏️ Try Again', '⏳ Pending Tasks']);
        }

      case WizardStep.completingSelectTask:
        final task = _findTask(qTrim, provider);
        _resetWizard();
        if (task != null) {
          final ok = await provider.completeTask(task.id);
          if (ok) {
            return _LocalQueryResult(
              text: '✅ Marked **${task.title}** as completed!',
              tasks: [task],
              chips: ['⏳ Pending Tasks', '📅 Due Today', '📊 Summary'],
            );
          }
        }
        return _LocalQueryResult(text: '❓ Could not complete task matching "$qTrim".', chips: ['⏳ Pending Tasks']);

      case WizardStep.deletingSelectTask:
        final task = _findTask(qTrim, provider);
        _resetWizard();
        if (task != null) {
          final ok = await provider.deleteTask(task.id);
          if (ok) {
            return _LocalQueryResult(
              text: '🗑️ Deleted task **${task.title}**.',
              chips: ['⏳ Pending Tasks', '➕ Add Task', '📊 Summary'],
            );
          }
        }
        return _LocalQueryResult(text: '❓ Could not delete task matching "$qTrim".', chips: ['⏳ Pending Tasks']);

      case WizardStep.searchingKeyword:
        _resetWizard();
        return _searchTasksLocally(qTrim, provider);

      case WizardStep.none:
        return _processQueryLocally(query, provider);
    }
  }

  Future<_LocalQueryResult> _processQueryLocally(String query, TaskProvider provider) async {
    final q = query.trim();
    final qLower = q.toLowerCase();

    // A. Summary / Stats / Overview
    if (qLower.contains('summary') || qLower.contains('stats') || qLower.contains('how many task') || qLower.contains('overview')) {
      return _buildSummaryResult(provider);
    }

    // B. Due Today
    if (qLower.contains('due today') || qLower == 'today' || qLower.contains('what is due today')) {
      return _handleQuickPick('3', provider);
    }

    // C. Overdue Tasks
    if (qLower.contains('overdue') || qLower.contains('past due')) {
      return _handleQuickPick('2', provider);
    }

    // D. High Priority
    if (qLower.contains('high priority') || qLower.contains('urgent') || qLower.contains('critical')) {
      return _handleQuickPick('4', provider);
    }

    // E. Mark Done / Complete
    if (qLower.startsWith('done ') || qLower.startsWith('complete ') || qLower.startsWith('finish ') || qLower.startsWith('mark done ')) {
      final target = q.replaceFirst(RegExp(r'^(?:complete|done|finish|mark done)\s+', caseSensitive: false), '').trim();
      final task = _findTask(target, provider);
      if (task != null) {
        final success = await provider.completeTask(task.id);
        if (success) {
          return _LocalQueryResult(
            text: '✅ Marked **${task.title}** as completed!',
            tasks: [task],
            chips: ['⏳ Pending Tasks', '📅 Due Today', '📊 Summary'],
          );
        } else {
          return _LocalQueryResult(text: '⚠️ Could not mark "${task.title}" as completed.');
        }
      } else {
        return _LocalQueryResult(text: '❓ Could not find task matching "$target".');
      }
    }

    // F. Delete Task
    if (qLower.startsWith('delete ') || qLower.startsWith('remove ') || qLower.startsWith('trash ')) {
      final target = q.replaceFirst(RegExp(r'^(?:delete|remove|trash)\s+', caseSensitive: false), '').trim();
      final task = _findTask(target, provider);
      if (task != null) {
        final success = await provider.deleteTask(task.id);
        if (success) {
          return _LocalQueryResult(
            text: '🗑️ Deleted task **${task.title}**.',
            chips: ['⏳ Pending Tasks', '➕ Add Task', '📊 Summary'],
          );
        } else {
          return _LocalQueryResult(text: '⚠️ Could not delete "${task.title}".');
        }
      } else {
        return _LocalQueryResult(text: '❓ Could not find task matching "$target".');
      }
    }

    // G. Spaces
    if (qLower == 'spaces' || qLower.contains('show spaces') || qLower.contains('list spaces')) {
      return _handleQuickPick('10', provider);
    }

    // H. Add / Create Task
    if (qLower.startsWith('add ') || qLower.startsWith('create ') || qLower.startsWith('new task ') || qLower == 'add task' || qLower == 'add') {
      var raw = q.replaceFirst(RegExp(r'^(?:add|create|new task)\s*', caseSensitive: false), '').trim();
      if (raw.isEmpty || raw.toLowerCase() == 'task') {
        // Start interactive guided wizard!
        _wizardStep = WizardStep.addingTitle;
        return _LocalQueryResult(
          text: '📝 **New Task Wizard**\n\nWhat would you like the task title to be?',
          chips: ['📝 Open Full Form', '🚫 Cancel'],
        );
      }

      // One-shot natural language parsing
      String? due;
      String priority = 'normal';
      Map<String, List<String>> spaces = {};
      List<String> tags = [];

      // Priority
      if (raw.toLowerCase().contains('priority:critical') || raw.toLowerCase().contains('critical priority')) {
        priority = 'critical';
        raw = raw.replaceAll(RegExp(r'(?:with\s+)?priority:critical|with\s+critical\s+priority', caseSensitive: false), '').trim();
      } else if (raw.toLowerCase().contains('priority:high') || raw.toLowerCase().contains('high priority')) {
        priority = 'high';
        raw = raw.replaceAll(RegExp(r'(?:with\s+)?priority:high|with\s+high\s+priority', caseSensitive: false), '').trim();
      } else if (raw.toLowerCase().contains('priority:low') || raw.toLowerCase().contains('low priority')) {
        priority = 'low';
        raw = raw.replaceAll(RegExp(r'(?:with\s+)?priority:low|with\s+low\s+priority', caseSensitive: false), '').trim();
      }

      // Due Date
      final now = DateTime.now();
      if (raw.toLowerCase().contains('due tomorrow') || raw.toLowerCase().contains('tomorrow')) {
        due = DateFormat('yyyy-MM-dd').format(now.add(const Duration(days: 1)));
        raw = raw.replaceAll(RegExp(r'\bdue\s+tomorrow\b|\btomorrow\b', caseSensitive: false), '').trim();
      } else if (raw.toLowerCase().contains('due today') || raw.toLowerCase().contains('today')) {
        due = DateFormat('yyyy-MM-dd').format(now);
        raw = raw.replaceAll(RegExp(r'\bdue\s+today\b|\btoday\b', caseSensitive: false), '').trim();
      }

      // Space
      final spaceMatch = RegExp(r'space:([a-zA-Z0-9_:\-,]+)', caseSensitive: false).firstMatch(raw);
      if (spaceMatch != null) {
        final spStr = spaceMatch.group(1)!;
        final parts = spStr.split(':');
        spaces[parts[0]] = parts.length > 1 ? parts.sublist(1) : <String>[];
        raw = raw.replaceFirst(spaceMatch.group(0)!, '').trim();
      }

      // Tags
      final tagMatches = RegExp(r'#([a-zA-Z0-9_\-]+)').allMatches(raw);
      for (final m in tagMatches) {
        tags.add(m.group(1)!);
      }
      raw = raw.replaceAll(RegExp(r'#[a-zA-Z0-9_\-]+'), '').trim();

      final title = raw.isNotEmpty ? raw : 'New Task';
      final success = await provider.addTask(
        title: title,
        due: due,
        priority: priority,
        spaces: spaces.isNotEmpty ? spaces : null,
        tags: tags.isNotEmpty ? tags : null,
      );

      if (success) {
        final added = provider.tasks.isNotEmpty ? provider.tasks.first : null;
        return _LocalQueryResult(
          text: '✨ Created task **"$title"** successfully!',
          tasks: added != null ? [added] : null,
          chips: ['➕ Add Another Task', '⏳ Pending Tasks', '📅 Due Today', '📊 Summary'],
        );
      } else {
        return _LocalQueryResult(text: '⚠️ Failed to create task.');
      }
    }

    // I. Search / Find Tasks
    if (qLower.startsWith('search ') || qLower.startsWith('find ')) {
      final term = q.replaceFirst(RegExp(r'^(?:search|find)\s+', caseSensitive: false), '').trim();
      return _searchTasksLocally(term, provider);
    }

    // J. Pending Tasks List
    if (qLower.contains('pending') || qLower == 'list' || qLower.contains('show tasks') || qLower.contains('my tasks')) {
      return _handleQuickPick('1', provider);
    }

    // K. Help / Greeting
    if (qLower == 'help' || qLower == 'hi' || qLower == 'hello' || qLower == '?' || qLower == 'menu') {
      return _buildHelpMenu();
    }

    // Default fallback
    return _LocalQueryResult(
      text: 'I understood: "$q".\n\n'
          'Try typing numbers `1` - `12` or commands like:\n'
          '• `Add <task title> tomorrow with high priority`\n'
          '• `Due today`\n'
          '• `Pending tasks`\n'
          '• `Complete <task name>`\n'
          '• `Summary`',
      chips: [
        '1. ⏳ Pending',
        '3. 📅 Due Today',
        '4. ⚡ High Priority',
        '5. ➕ Add Task',
        '11. 📊 Summary',
        '❓ Help & Menu',
      ],
    );
  }

  _LocalQueryResult _searchTasksLocally(String term, TaskProvider provider) {
    final termLower = term.toLowerCase();
    final matches = provider.tasks.where((t) =>
        t.title.toLowerCase().contains(termLower) ||
        t.cleanNotes.toLowerCase().contains(termLower) ||
        t.allTags.any((tag) => tag.toLowerCase().contains(termLower)) ||
        t.spaces.keys.any((sp) => sp.toLowerCase().contains(termLower))
    ).take(10).toList();

    if (matches.isEmpty) {
      return _LocalQueryResult(
        text: '🔍 No tasks found matching "$term".',
        chips: ['⏳ Pending Tasks', '➕ Add Task', '📊 Summary'],
      );
    }
    return _LocalQueryResult(
      text: '🔍 Found ${matches.length} task(s) matching "$term":',
      tasks: matches,
      chips: ['⏳ Pending Tasks', '📅 Due Today', '📊 Summary'],
    );
  }

  TaskItem? _findTask(String target, TaskProvider provider) {
    if (target.isEmpty) return null;
    final lower = target.toLowerCase().trim();

    // 1. Exact title match
    for (final t in provider.tasks) {
      if (t.title.toLowerCase() == lower) return t;
    }

    // 2. Substring title match
    for (final t in provider.tasks) {
      if (t.title.toLowerCase().contains(lower)) return t;
    }

    // 3. Number match (1-based index)
    final idx = int.tryParse(lower);
    if (idx != null && idx > 0 && idx <= provider.tasks.length) {
      return provider.tasks[idx - 1];
    }

    return null;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.amber.withValues(alpha: 0.2),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.amber, size: 20),
            ),
            const SizedBox(width: 10),
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('AI Assistant', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                Text(
                  _wizardStep != WizardStep.none ? 'Guided Step Active' : 'Natural Language & Smart Picks',
                  style: theme.textTheme.bodySmall?.copyWith(
                    color: _wizardStep != WizardStep.none ? Colors.amber : Colors.grey,
                    fontSize: 11,
                    fontWeight: _wizardStep != WizardStep.none ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline),
            tooltip: 'Interactive Menu',
            onPressed: () => _handleSubmitted('help'),
          ),
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined),
            tooltip: 'Clear Chat',
            onPressed: () {
              _resetWizard();
              setState(() {
                _messages.clear();
                _messages.add(
                  ChatMessage(
                    id: 'cleared',
                    sender: ChatSender.assistant,
                    text: '🧹 Chat cleared. How can I assist you today?',
                    suggestionChips: [
                      '📊 Summary',
                      '⏳ Pending Tasks',
                      '📅 Due Today',
                      '⚡ High Priority',
                      '➕ Add Task',
                      '❓ Help & Menu',
                    ],
                  ),
                );
              });
            },
          ),
        ],
      ),
      body: Column(
        children: [
          // Top Quick Action Pills
          Container(
            height: 48,
            padding: const EdgeInsets.symmetric(vertical: 6),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.3),
              border: Border(
                bottom: BorderSide(
                  color: theme.dividerColor.withValues(alpha: 0.2),
                ),
              ),
            ),
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12),
              itemCount: _quickActionPills.length,
              separatorBuilder: (ctx, idx) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final prompt = _quickActionPills[index];
                return ActionChip(
                  label: Text(
                    prompt,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                  backgroundColor: theme.colorScheme.surface,
                  side: BorderSide(color: theme.colorScheme.primary.withValues(alpha: 0.3)),
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  onPressed: () => _handleSubmitted(prompt.replaceAll(RegExp(r'^[^\w]+'), '').trim()),
                );
              },
            ),
          ),

          // Chat Messages List
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildMessageBubble(context, message);
              },
            ),
          ),

          // Processing Indicator
          if (_isProcessing)
            Padding(
              padding: const EdgeInsets.only(left: 20, bottom: 8),
              child: Row(
                children: [
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.amber),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Thinking & organizing...',
                    style: theme.textTheme.bodySmall?.copyWith(fontStyle: FontStyle.italic, color: Colors.grey),
                  ),
                ],
              ),
            ),

          // Active Wizard Banner
          if (_wizardStep != WizardStep.none)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              color: Colors.amber.withValues(alpha: 0.15),
              child: Row(
                children: [
                  const Icon(Icons.assistant, size: 16, color: Colors.amber),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Interactive Wizard active: answer prompt or tap chips',
                      style: TextStyle(fontSize: 11, color: Colors.amber.shade900, fontWeight: FontWeight.w600),
                    ),
                  ),
                  TextButton(
                    onPressed: () => _handleSubmitted('cancel'),
                    style: TextButton.styleFrom(visualDensity: VisualDensity.compact, padding: EdgeInsets.zero),
                    child: const Text('Cancel', style: TextStyle(fontSize: 12, color: Colors.red)),
                  ),
                ],
              ),
            ),

          // Input Bar
          Container(
            padding: EdgeInsets.fromLTRB(12, 8, 12, MediaQuery.of(context).padding.bottom + 8),
            decoration: BoxDecoration(
              color: theme.colorScheme.surface,
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withValues(alpha: 0.05),
                  offset: const Offset(0, -2),
                  blurRadius: 6,
                ),
              ],
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _inputController,
                    minLines: 1,
                    maxLines: 4,
                    textInputAction: TextInputAction.send,
                    onSubmitted: _handleSubmitted,
                    decoration: InputDecoration(
                      hintText: _wizardStep != WizardStep.none
                          ? "Type answer or tap choice..."
                          : "Ask anything (e.g. 'Add tax return Friday', '1-12')...",
                      hintStyle: const TextStyle(fontSize: 13, color: Colors.grey),
                      filled: true,
                      fillColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(24),
                        borderSide: BorderSide.none,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  icon: const Icon(Icons.send_rounded, size: 18),
                  onPressed: () => _handleSubmitted(_inputController.text),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(BuildContext context, ChatMessage message) {
    final theme = Theme.of(context);
    final isUser = message.sender == ChatSender.user;

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.amber.withValues(alpha: 0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.amber, size: 16),
            ),
            const SizedBox(width: 8),
          ],
          Flexible(
            child: Column(
              crossAxisAlignment: isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
              children: [
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: isUser
                        ? theme.colorScheme.primary
                        : theme.colorScheme.surfaceContainerHighest,
                    borderRadius: BorderRadius.only(
                      topLeft: const Radius.circular(16),
                      topRight: const Radius.circular(16),
                      bottomLeft: isUser ? const Radius.circular(16) : const Radius.circular(4),
                      bottomRight: isUser ? const Radius.circular(4) : const Radius.circular(16),
                    ),
                  ),
                  child: Text(
                    message.text,
                    style: TextStyle(
                      fontSize: 14,
                      color: isUser ? theme.colorScheme.onPrimary : theme.colorScheme.onSurface,
                      height: 1.35,
                    ),
                  ),
                ),

                // Interactive Task Cards attached to message (NO task IDs displayed)
                if (message.taskItems != null && message.taskItems!.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  ...message.taskItems!.map((task) => _buildChatTaskCard(context, task)),
                ],

                // Action / Suggestion Chips attached to message
                if (!isUser && message.suggestionChips != null && message.suggestionChips!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: message.suggestionChips!.map((chipText) {
                      return ActionChip(
                        label: Text(
                          chipText,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                        backgroundColor: theme.colorScheme.surface,
                        side: BorderSide(color: theme.colorScheme.primary.withValues(alpha: 0.3)),
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                        visualDensity: VisualDensity.compact,
                        onPressed: () => _handleSubmitted(chipText),
                      );
                    }).toList(),
                  ),
                ],
              ],
            ),
          ),
          if (isUser) const SizedBox(width: 8),
        ],
      ),
    );
  }

  Widget _buildChatTaskCard(BuildContext context, TaskItem task) {
    final theme = Theme.of(context);
    final provider = context.read<TaskProvider>();
    final isOverdue = _isTaskOverdue(task);
    final isToday = _isTaskDueToday(task);

    return Container(
      margin: const EdgeInsets.only(top: 6),
      decoration: BoxDecoration(
        color: theme.colorScheme.surface,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: isOverdue
              ? Colors.red.withValues(alpha: 0.4)
              : (isToday ? Colors.orange.withValues(alpha: 0.4) : theme.dividerColor.withValues(alpha: 0.3)),
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 4,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ListTile(
        dense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
        leading: Checkbox(
          value: task.isCompleted,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
          onChanged: (_) async {
            await provider.completeTask(task.id);
            if (mounted) setState(() {});
          },
        ),
        title: Text(
          task.title,
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.bold,
            decoration: task.isCompleted ? TextDecoration.lineThrough : null,
          ),
        ),
        subtitle: Padding(
          padding: const EdgeInsets.only(top: 4),
          child: Wrap(
            spacing: 6,
            runSpacing: 4,
            crossAxisAlignment: WrapCrossAlignment.center,
            children: [
              // Due Date Chip (No Task ID!)
              if (task.formattedDueDate != null)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                  decoration: BoxDecoration(
                    color: isOverdue
                        ? Colors.red.withValues(alpha: 0.15)
                        : (isToday ? Colors.orange.withValues(alpha: 0.15) : Colors.blue.withValues(alpha: 0.12)),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Icon(
                        Icons.calendar_today,
                        size: 11,
                        color: isOverdue ? Colors.red : (isToday ? Colors.orange.shade800 : Colors.blueAccent),
                      ),
                      const SizedBox(width: 3),
                      Text(
                        isOverdue ? 'Overdue: ${task.formattedDueDate}' : (isToday ? 'Today' : task.formattedDueDate!),
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: isOverdue ? Colors.red : (isToday ? Colors.orange.shade800 : Colors.blueAccent),
                        ),
                      ),
                    ],
                  ),
                ),

              // Priority Badge
              if (task.calculatedPriority != 'normal')
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                  decoration: BoxDecoration(
                    color: task.calculatedPriority == 'critical'
                        ? Colors.red.withValues(alpha: 0.2)
                        : Colors.orange.withValues(alpha: 0.2),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    task.calculatedPriority.toUpperCase(),
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: task.calculatedPriority == 'critical' ? Colors.red : Colors.orange.shade800,
                    ),
                  ),
                ),

              // Space Badge
              if (task.spaces.isNotEmpty)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                  decoration: BoxDecoration(
                    color: Colors.deepPurple.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(4),
                  ),
                  child: Text(
                    task.spaces.keys.join(', '),
                    style: const TextStyle(fontSize: 10, color: Colors.deepPurple, fontWeight: FontWeight.w600),
                  ),
                ),

              // Tag Badges
              if (task.allTags.isNotEmpty)
                ...task.allTags.take(2).map(
                  (tag) => Text('#$tag', style: const TextStyle(fontSize: 10, color: Colors.grey)),
                ),
            ],
          ),
        ),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.edit_outlined, size: 16),
              tooltip: 'Edit in Form',
              onPressed: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => TaskEditorDialog(task: task, isFullScreen: true),
                  ),
                );
              },
            ),
            IconButton(
              icon: const Icon(Icons.delete_outline, size: 16, color: Colors.redAccent),
              tooltip: 'Delete',
              onPressed: () async {
                await provider.deleteTask(task.id);
                if (mounted) setState(() {});
              },
            ),
          ],
        ),
        onTap: () {
          showDialog(
            context: context,
            builder: (_) => TaskDetailModal(
              task: task,
              onEdit: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => TaskEditorDialog(task: task, isFullScreen: true),
                  ),
                );
              },
              onDelete: () async {
                await provider.deleteTask(task.id);
                if (mounted) setState(() {});
              },
            ),
          );
        },
      ),
    );
  }
}

class _LocalQueryResult {
  final String text;
  final List<TaskItem>? tasks;
  final List<String>? chips;

  _LocalQueryResult({
    required this.text,
    this.tasks,
    this.chips,
  });
}
