import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';
import '../widgets/task_detail_modal.dart';
import '../widgets/task_editor_dialog.dart';
import '../widgets/command_palette_modal.dart';

enum ChatSender { user, assistant }

enum WizardStep {
  none,
  addingTitle,
  addingDue,
  addingPriority,
  addingSpace,
  confirmingReview,
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
  final ScrollController _scrollController = ScrollController();
  final GlobalKey<_ChatInputBarState> _inputBarKey = GlobalKey<_ChatInputBarState>();
  bool _isProcessing = false;

  // Conversational Wizard State (Claude CLI Q&A style)
  WizardStep _wizardStep = WizardStep.none;
  String? _draftTitle;
  String? _draftDue;
  String? _draftPriority;
  Map<String, List<String>>? _draftSpaces;
  TaskItem? _targetTaskForUpdate;
  String? _targetFieldForUpdate;

  // Selected quick filter combiners for command chaining
  final Set<String> _chainedFilters = {};

  final List<String> _quickActionPills = [
    '/help',
    '➕ Add Task',
    '📅 Due Today',
    '⚡ High Priority',
    '⏳ Pending',
    '🚨 Overdue',
    '🌌 Spaces',
    '📊 Summary',
  ];

  @override
  void initState() {
    super.initState();
    _messages.add(
      ChatMessage(
        id: 'welcome',
        sender: ChatSender.assistant,
        text: '👋 Welcome to **GTasks AI Assistant**!\n\n'
            'I can help you manage tasks conversationally, chain commands, or guide you through a step-by-step Q&A wizard.\n\n'
            '• Type `/help` or tap **`[/]`** to open the interactive Command Palette.\n'
            '• Chain commands with `|` or `&&` (e.g. `/today | /high`).\n'
            '• Tap **➕ Add Task** for Claude CLI-style Q&A with skip options!',
        suggestionChips: [
          '/help',
          '➕ Add Task',
          '📅 Due Today',
          '⚡ High Priority',
          '⏳ Pending Tasks',
          '📊 Summary',
        ],
      ),
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOutCubic,
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

  void _openCommandPalette() {
    CommandPaletteModal.show(
      context,
      onSelectCommand: (cmd, runImmediately) {
        if (runImmediately) {
          _handleSubmitted(cmd);
        } else {
          _inputBarKey.currentState?.setText(cmd);
        }
      },
    );
  }

  Future<void> _handleSubmitted(String text) async {
    final query = text.trim();
    if (query.isEmpty || _isProcessing) return;

    _inputBarKey.currentState?.clear();
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
      final qLower = query.toLowerCase();

      // Check for Cancel / Stop
      if (qLower == 'cancel' || qLower == 'exit' || qLower == 'stop' || qLower == 'reset' || qLower == '❌ cancel' || qLower == '🚫 cancel') {
        _resetWizard();
        replyText = '🚫 Wizard canceled. What would you like to do next?';
        suggestionChips = ['/help', '➕ Add Task', '⏳ Pending Tasks', '📅 Due Today', '📊 Summary'];
      }
      // Check for /clear or /cls
      else if (qLower == '/clear' || qLower == '/cls' || qLower == 'clear' || qLower == 'cls') {
        _resetWizard();
        _messages.clear();
        _messages.add(
          ChatMessage(
            id: 'cleared',
            sender: ChatSender.assistant,
            text: '🧹 Chat cleared! How can I assist you?',
            suggestionChips: ['/help', '➕ Add Task', '📅 Due Today', '📊 Summary'],
          ),
        );
        return;
      }
      // Check for /help
      else if (qLower == '/help' || qLower == '/h') {
        _openCommandPalette();
        replyText = '📖 Opened Command Palette with real-time search. You can also pick actions below:';
        suggestionChips = ['➕ Add Task', '📅 Due Today', '⚡ High Priority', '⏳ Pending', '📊 Summary'];
      }
      // Active Wizard Step
      else if (_wizardStep != WizardStep.none) {
        final stepResult = await _handleWizardStep(query, provider);
        replyText = stepResult.text;
        actionTasks = stepResult.tasks;
        suggestionChips = stepResult.chips;
      }
      // Command Chaining / Multi-Command Pipeline (| or && or +)
      else if (_isChainedCommand(query)) {
        final chainedResult = await _handleChainedCommand(query, provider);
        replyText = chainedResult.text;
        actionTasks = chainedResult.tasks;
        suggestionChips = chainedResult.chips;
      }
      // Direct Slash Commands & Easy Picks
      else if (_isSlashOrQuickCommand(query)) {
        final pickResult = await _handleSlashOrQuickCommand(query, provider);
        replyText = pickResult.text;
        actionTasks = pickResult.tasks;
        suggestionChips = pickResult.chips;
      }
      // Try backend server if available
      else {
        bool backendHandled = false;
        try {
          final serverReply = await provider.apiClient.chatAi(query).timeout(const Duration(milliseconds: 3000));
          if (serverReply.isNotEmpty) {
            replyText = serverReply;
            backendHandled = true;
            await provider.refreshTasks();
            suggestionChips = ['📅 Due Today', '⚡ High Priority', '➕ Add Task', '📊 Summary'];
          }
        } catch (_) {
          backendHandled = false;
        }

        // Local fallback NLP
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
      suggestionChips = ['/help', '⏳ Pending Tasks'];
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

  bool _isChainedCommand(String query) {
    return query.contains('|') || query.contains('&&') || (query.contains('+') && !query.contains('➕'));
  }

  Future<_LocalQueryResult> _handleChainedCommand(String query, TaskProvider provider) async {
    // Split on | or && or +
    final parts = query.split(RegExp(r'\s*(?:\||&&|\+)\s*')).map((s) => s.trim().toLowerCase()).toList();

    bool filterDueToday = false;
    bool filterOverdue = false;
    bool filterPending = false;
    bool filterHigh = false;
    String? spaceFilter;

    for (final p in parts) {
      final clean = p.replaceAll(RegExp(r'^/'), '');
      if (clean == 'today' || clean == 'due today' || clean == 't') filterDueToday = true;
      if (clean == 'overdue' || clean == 'o') filterOverdue = true;
      if (clean == 'pending' || clean == 'p') filterPending = true;
      if (clean == 'high' || clean == 'urgent' || clean == 'critical') filterHigh = true;
      if (clean.startsWith('space:') || clean.startsWith('space ')) {
        spaceFilter = clean.replaceFirst(RegExp(r'^space:?\s*'), '');
      }
    }

    var list = provider.tasks.where((t) => !t.isCompleted).toList();

    if (filterPending) {
      list = list.where((t) => !t.isCompleted).toList();
    }
    if (filterDueToday) {
      list = list.where(_isTaskDueToday).toList();
    }
    if (filterOverdue) {
      list = list.where(_isTaskOverdue).toList();
    }
    if (filterHigh) {
      list = list.where((t) => t.calculatedPriority == 'high' || t.calculatedPriority == 'critical').toList();
    }
    if (spaceFilter != null && spaceFilter.isNotEmpty) {
      list = list.where((t) => t.spaces.keys.any((s) => s.toLowerCase() == spaceFilter!.toLowerCase())).toList();
    }

    final chainLabel = parts.join(' ⧉ ');
    if (list.isEmpty) {
      return _LocalQueryResult(
        text: '🔍 **Chained Query:** `$chainLabel`\n\nNo tasks match this combined filter.',
        chips: ['📅 Due Today', '⏳ Pending Tasks', '➕ Add Task', '📊 Summary'],
      );
    }

    return _LocalQueryResult(
      text: '🔗 **Chained Query Result (${list.length} tasks):** `$chainLabel`',
      tasks: list,
      chips: ['📅 Due Today', '⚡ High Priority', '➕ Add Task', '📊 Summary'],
    );
  }

  bool _isSlashOrQuickCommand(String query) {
    final trimmed = query.trim().toLowerCase();
    if (trimmed.startsWith('/')) return true;
    final numVal = int.tryParse(trimmed);
    if (numVal != null && numVal >= 1 && numVal <= 12) return true;
    return trimmed == 'help' ||
        trimmed == 'menu' ||
        trimmed == 'picks' ||
        trimmed == 'options' ||
        trimmed == 'today' ||
        trimmed == 'pending' ||
        trimmed == 'overdue' ||
        trimmed == 'summary' ||
        trimmed == 'spaces' ||
        trimmed == '?';
  }

  Future<_LocalQueryResult> _handleSlashOrQuickCommand(String query, TaskProvider provider) async {
    var cmd = query.trim().toLowerCase();
    if (cmd.startsWith('/')) cmd = cmd.substring(1).trim();

    final numVal = int.tryParse(cmd);

    // 1 / Pending
    if (numVal == 1 || cmd == 'pending' || cmd == 'p') {
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

    // 2 / Overdue
    if (numVal == 2 || cmd == 'overdue' || cmd == 'o') {
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

    // 3 / Due Today
    if (numVal == 3 || cmd == 'today' || cmd == 'due today' || cmd == 't') {
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

    // 4 / High Priority
    if (numVal == 4 || cmd == 'high' || cmd == 'urgent' || cmd == 'critical') {
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

    // 5 / Add Task (Interactive Claude CLI-Style Wizard)
    if (numVal == 5 || cmd.startsWith('add') || cmd.startsWith('new') || cmd == 'a') {
      final arg = cmd.replaceFirst(RegExp(r'^(?:add|new|a)\s*'), '').trim();
      if (arg.isNotEmpty) {
        _draftTitle = arg;
        _wizardStep = WizardStep.addingDue;
        return _LocalQueryResult(
          text: '📝 **Task Title:** "$_draftTitle"\n\n'
              '📅 **Step 2 of 4: When is this due?**\n'
              'Select an option or tap Skip:',
          chips: ['📅 Today', '🌅 Tomorrow', '🗓 End of Week', '⏩ Next Week', '⏭️ Skip Due Date', '❌ Cancel'],
        );
      }
      _wizardStep = WizardStep.addingTitle;
      return _LocalQueryResult(
        text: '📝 **Interactive Task Wizard: Step 1 of 4**\n\n'
            'What would you like the task title to be?',
        chips: ['📝 Open Full Form', '❌ Cancel'],
      );
    }

    // 6 / Update
    if (numVal == 6 || cmd.startsWith('update') || cmd.startsWith('edit')) {
      final pending = provider.tasks.where((t) => !t.isCompleted).take(6).toList();
      if (pending.isEmpty) {
        return _LocalQueryResult(text: 'No pending tasks to update.', chips: ['➕ Add Task']);
      }
      _wizardStep = WizardStep.updatingSelectTask;
      return _LocalQueryResult(
        text: '✏️ **Which task would you like to update?**\nTap an option or enter title/number:',
        tasks: pending,
        chips: [...pending.map((t) => 'Edit "${t.title}"'), '❌ Cancel'],
      );
    }

    // 7 / Mark Done
    if (numVal == 7 || cmd.startsWith('done') || cmd.startsWith('complete')) {
      final target = cmd.replaceFirst(RegExp(r'^(?:done|complete)\s*'), '').trim();
      if (target.isNotEmpty) {
        final task = _findTask(target, provider);
        if (task != null) {
          await provider.completeTask(task.id);
          return _LocalQueryResult(
            text: '✅ Marked **${task.title}** as completed!',
            tasks: [task],
            chips: ['⏳ Pending Tasks', '📅 Due Today', '📊 Summary'],
          );
        }
      }
      final pending = provider.tasks.where((t) => !t.isCompleted).take(8).toList();
      _wizardStep = WizardStep.completingSelectTask;
      return _LocalQueryResult(
        text: '✅ **Which task would you like to complete?**\nTap the checkbox on any card or type title:',
        tasks: pending,
        chips: ['❌ Cancel'],
      );
    }

    // 8 / Delete
    if (numVal == 8 || cmd.startsWith('delete') || cmd.startsWith('rm')) {
      final target = cmd.replaceFirst(RegExp(r'^(?:delete|rm)\s*'), '').trim();
      if (target.isNotEmpty) {
        final task = _findTask(target, provider);
        if (task != null) {
          await provider.deleteTask(task.id);
          return _LocalQueryResult(
            text: '🗑️ Deleted task **${task.title}**.',
            chips: ['⏳ Pending Tasks', '➕ Add Task', '📊 Summary'],
          );
        }
      }
      final pending = provider.tasks.where((t) => !t.isCompleted).take(8).toList();
      _wizardStep = WizardStep.deletingSelectTask;
      return _LocalQueryResult(
        text: '🗑️ **Which task would you like to delete?**\nTap delete on any card or type title:',
        tasks: pending,
        chips: ['❌ Cancel'],
      );
    }

    // 9 / Search
    if (numVal == 9 || cmd.startsWith('search') || cmd.startsWith('s ')) {
      final term = cmd.replaceFirst(RegExp(r'^(?:search|s)\s*'), '').trim();
      if (term.isNotEmpty) {
        return _searchTasksLocally(term, provider);
      }
      _wizardStep = WizardStep.searchingKeyword;
      return _LocalQueryResult(text: '🔍 What keyword or tag would you like to search for?', chips: ['❌ Cancel']);
    }

    // 10 / Spaces
    if (numVal == 10 || cmd == 'spaces' || cmd == 'sp') {
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

    // 11 / Summary
    if (numVal == 11 || cmd == 'summary' || cmd == 'stats') {
      return _buildSummaryResult(provider);
    }

    // Open Full Form
    if (cmd == 'open' || cmd == 'form') {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        if (mounted) {
          Navigator.push(
            context,
            MaterialPageRoute(builder: (_) => const TaskEditorDialog(isFullScreen: true)),
          );
        }
      });
      return _LocalQueryResult(text: '📝 Opening Full Task Editor form...');
    }

    // Default: Help menu
    _openCommandPalette();
    return _LocalQueryResult(
      text: '🤖 **GTasks Command Palette opened.** Choose a command or tap an option below:',
      chips: ['/today', '/pending', '/high', '/overdue', '/add', '/summary'],
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

    // Check Open Full Form
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
      return _LocalQueryResult(text: '📝 Opening Full Task Editor for you...');
    }

    switch (_wizardStep) {
      case WizardStep.addingTitle:
        _draftTitle = qTrim;
        _wizardStep = WizardStep.addingDue;
        return _LocalQueryResult(
          text: '📝 **Task Title:** "$_draftTitle"\n\n'
              '📅 **Step 2 of 4: When is this due?**\n'
              'Select a preset or tap Skip to set no due date:',
          chips: [
            '📅 Today',
            '🌅 Tomorrow',
            '🗓 End of Week',
            '⏩ Next Week',
            '⏭️ Skip Due Date',
            '❌ Cancel',
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
        } else if (qLower.contains('skip') || qLower.contains('none') || qLower.contains('no due')) {
          _draftDue = null;
        } else {
          try {
            final parsed = DateTime.parse(qTrim);
            _draftDue = DateFormat('yyyy-MM-dd').format(parsed);
          } catch (_) {
            _draftDue = qTrim;
          }
        }

        _wizardStep = WizardStep.addingPriority;
        return _LocalQueryResult(
          text: '⚡ **Step 3 of 4: What priority level?**\n'
              'Select priority or tap Skip for Normal:',
          chips: [
            '🔴 Critical',
            '🟠 High',
            '🔵 Normal',
            '🟢 Low',
            '⏭️ Skip (Normal)',
            '❌ Cancel',
          ],
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
          text: '🌌 **Step 4 of 4: Assign to Space?** (Optional)\n'
              'Tap an existing space or tap Skip:',
          chips: [
            ...spaces.map((s) => 'Space: $s'),
            '⏭️ Skip Space',
            '❌ Cancel',
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

        _wizardStep = WizardStep.confirmingReview;
        return _LocalQueryResult(
          text: '📋 **Review & Confirm Task**\n\n'
              '• **Title:** ${_draftTitle ?? "New Task"}\n'
              '• **Due Date:** ${_draftDue ?? "No due date"}\n'
              '• **Priority:** ${(_draftPriority ?? "normal").toUpperCase()}\n'
              '• **Space:** ${_draftSpaces != null ? _draftSpaces!.keys.join(", ") : "None"}\n\n'
              'Tap **Confirm** to create or tap an option to edit:',
          chips: [
            '✅ Confirm & Create',
            '✏️ Change Title',
            '📅 Change Date',
            '⚡ Change Priority',
            '❌ Cancel',
          ],
        );

      case WizardStep.confirmingReview:
        if (qLower.contains('confirm') || qLower.contains('create') || qLower.contains('yes') || qLower.contains('ok')) {
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
              text: '⚠️ Failed to create task.',
              chips: ['➕ Try Again', '📊 Summary'],
            );
          }
        } else if (qLower.contains('title')) {
          _wizardStep = WizardStep.addingTitle;
          return _LocalQueryResult(text: 'Enter the new title for this task:', chips: ['❌ Cancel']);
        } else if (qLower.contains('date')) {
          _wizardStep = WizardStep.addingDue;
          return _LocalQueryResult(
            text: 'When is this due?',
            chips: ['📅 Today', '🌅 Tomorrow', '🗓 End of Week', '⏭️ Skip Due Date', '❌ Cancel'],
          );
        } else if (qLower.contains('priority')) {
          _wizardStep = WizardStep.addingPriority;
          return _LocalQueryResult(
            text: 'Select priority level:',
            chips: ['🔴 Critical', '🟠 High', '🔵 Normal', '🟢 Low', '❌ Cancel'],
          );
        }
        return _LocalQueryResult(
          text: 'Tap Confirm to save or choose what to adjust:',
          chips: ['✅ Confirm & Create', '✏️ Change Title', '📅 Change Date', '⚡ Change Priority', '❌ Cancel'],
        );

      case WizardStep.updatingSelectTask:
        final task = _findTask(qTrim.replaceAll(RegExp(r'^edit\s*"?|"?$', caseSensitive: false), ''), provider);
        if (task == null) {
          return _LocalQueryResult(
            text: '❓ Could not find task matching "$qTrim". Please type exact title or number:',
            chips: ['❌ Cancel'],
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
            '❌ Cancel',
          ],
        );

      case WizardStep.updatingSelectField:
        final target = _targetTaskForUpdate;
        if (target == null) {
          _resetWizard();
          return _LocalQueryResult(text: 'Update session expired.', chips: ['✏️ Update Task']);
        }

        if (qLower.contains('title')) {
          _targetFieldForUpdate = 'title';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(text: 'Enter the new title for **${target.title}**:', chips: ['❌ Cancel']);
        } else if (qLower.contains('due') || qLower.contains('date')) {
          _targetFieldForUpdate = 'due';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(
            text: 'Enter new due date (or tap preset):',
            chips: ['📅 Today', '🌅 Tomorrow', '🗓 Next Week', '⏭️ Clear Date', '❌ Cancel'],
          );
        } else if (qLower.contains('priority')) {
          _targetFieldForUpdate = 'priority';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(
            text: 'Select new priority:',
            chips: ['🔴 Critical', '🟠 High', '🔵 Normal', '🟢 Low', '❌ Cancel'],
          );
        } else if (qLower.contains('space')) {
          _targetFieldForUpdate = 'space';
          _wizardStep = WizardStep.updatingFieldValue;
          return _LocalQueryResult(
            text: 'Enter space name or tap an existing space:',
            chips: [...provider.spacesWithCounts.keys.take(4).map((s) => 'Space: $s'), '🚫 Clear Space', '❌ Cancel'],
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
          text: 'Please choose what to update:',
          chips: ['✏️ Change Title', '📅 Change Due Date', '⚡ Change Priority', '🌌 Change Space', '❌ Cancel'],
        );

      case WizardStep.updatingFieldValue:
        final target = _targetTaskForUpdate;
        final field = _targetFieldForUpdate;
        if (target == null || field == null) {
          _resetWizard();
          return _LocalQueryResult(text: 'Update session expired.', chips: ['✏️ Update Task']);
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
          } else if (qLower.contains('clear') || qLower.contains('none') || qLower.contains('skip')) {
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

    // Summary / Stats / Overview
    if (qLower.contains('summary') || qLower.contains('stats') || qLower.contains('how many task') || qLower.contains('overview')) {
      return _buildSummaryResult(provider);
    }

    // Due Today
    if (qLower.contains('due today') || qLower == 'today') {
      return _handleSlashOrQuickCommand('/today', provider);
    }

    // Overdue
    if (qLower.contains('overdue') || qLower.contains('past due')) {
      return _handleSlashOrQuickCommand('/overdue', provider);
    }

    // High Priority
    if (qLower.contains('high priority') || qLower.contains('urgent') || qLower.contains('critical')) {
      return _handleSlashOrQuickCommand('/high', provider);
    }

    // One-shot Add Task with inline tags/spaces
    if (qLower.startsWith('add ') || qLower.startsWith('create ') || qLower.startsWith('new task ')) {
      var raw = q.replaceFirst(RegExp(r'^(?:add|create|new task)\s*', caseSensitive: false), '').trim();
      if (raw.isEmpty || raw.toLowerCase() == 'task') {
        _wizardStep = WizardStep.addingTitle;
        return _LocalQueryResult(
          text: '📝 **Interactive Task Wizard: Step 1 of 4**\n\nWhat would you like the task title to be?',
          chips: ['📝 Open Full Form', '❌ Cancel'],
        );
      }

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

    // Search
    if (qLower.startsWith('search ') || qLower.startsWith('find ')) {
      final term = q.replaceFirst(RegExp(r'^(?:search|find)\s+', caseSensitive: false), '').trim();
      return _searchTasksLocally(term, provider);
    }

    // Pending Tasks
    if (qLower.contains('pending') || qLower == 'list' || qLower.contains('show tasks') || qLower.contains('my tasks')) {
      return _handleSlashOrQuickCommand('/pending', provider);
    }

    // Default Fallback
    return _LocalQueryResult(
      text: 'I understood: "$q".\n\n'
          'Try slash commands or chained queries:\n'
          '• `/help` - Open Command Palette with search\n'
          '• `/today | /high` - Tasks due today AND high priority\n'
          '• `/add` - Interactive Claude CLI-style Q&A\n'
          '• `/summary` - Overall productivity stats',
      chips: [
        '/help',
        '/today | /high',
        '➕ Add Task',
        '📅 Due Today',
        '⏳ Pending Tasks',
        '📊 Summary',
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

    // Exact title match
    for (final t in provider.tasks) {
      if (t.title.toLowerCase() == lower) return t;
    }

    // Substring title match
    for (final t in provider.tasks) {
      if (t.title.toLowerCase().contains(lower)) return t;
    }

    // Number match
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
      resizeToAvoidBottomInset: true,
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
                  _wizardStep != WizardStep.none ? 'Claude Q&A Active' : 'Slash Commands & Smart Chains',
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
            icon: const Icon(Icons.terminal),
            tooltip: 'Command Palette (/help)',
            onPressed: _openCommandPalette,
          ),
          IconButton(
            icon: const Icon(Icons.delete_sweep_outlined),
            tooltip: 'Clear Chat (/clear)',
            onPressed: () => _handleSubmitted('/clear'),
          ),
        ],
      ),
      body: Column(
        children: [
          // Top Quick Action Pills
          Container(
            height: 46,
            padding: const EdgeInsets.symmetric(vertical: 5),
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
                  onPressed: () {
                    if (prompt == '/help') {
                      _openCommandPalette();
                    } else {
                      _handleSubmitted(prompt.replaceAll(RegExp(r'^[^\w/]+'), '').trim());
                    }
                  },
                );
              },
            ),
          ),

          // Messages List with RepaintBoundary for smooth 120Hz scrolling
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              physics: const BouncingScrollPhysics(parent: AlwaysScrollableScrollPhysics()),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return RepaintBoundary(
                  child: _buildMessageBubble(context, message),
                );
              },
            ),
          ),

          // Processing Indicator
          if (_isProcessing)
            Padding(
              padding: const EdgeInsets.only(left: 20, bottom: 6),
              child: Row(
                children: [
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.amber),
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Thinking & chaining...',
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
                      'Claude Q&A Wizard active: choose option or tap Skip',
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

          // Quick Filter Combiner / Command Chainer Bar
          _buildQuickChainerBar(theme),

          // Decoupled, High-Performance Chat Input Bar
          _ChatInputBar(
            key: _inputBarKey,
            wizardStep: _wizardStep,
            onSubmitted: _handleSubmitted,
            onOpenPalette: _openCommandPalette,
          ),
        ],
      ),
    );
  }

  Widget _buildQuickChainerBar(ThemeData theme) {
    final chainOptions = ['today', 'high', 'pending', 'overdue'];

    return Container(
      height: 38,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 2),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.2),
        border: Border(top: BorderSide(color: theme.dividerColor.withValues(alpha: 0.15))),
      ),
      child: Row(
        children: [
          Icon(Icons.link, size: 14, color: theme.colorScheme.primary),
          const SizedBox(width: 6),
          Text('Chain:', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: theme.colorScheme.primary)),
          const SizedBox(width: 6),
          Expanded(
            child: ListView(
              scrollDirection: Axis.horizontal,
              children: [
                ...chainOptions.map((opt) {
                  final isSelected = _chainedFilters.contains(opt);
                  return Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 3),
                    child: FilterChip(
                      label: Text(opt == 'high' ? '⚡ high' : (opt == 'today' ? '📅 today' : opt), style: const TextStyle(fontSize: 10)),
                      selected: isSelected,
                      visualDensity: VisualDensity.compact,
                      padding: EdgeInsets.zero,
                      showCheckmark: false,
                      onSelected: (val) {
                        setState(() {
                          if (val) {
                            _chainedFilters.add(opt);
                          } else {
                            _chainedFilters.remove(opt);
                          }
                        });
                      },
                    ),
                  );
                }),
                if (_chainedFilters.length >= 2) ...[
                  const SizedBox(width: 4),
                  ActionChip(
                    avatar: const Icon(Icons.play_arrow, size: 12, color: Colors.white),
                    label: Text('Run: ${_chainedFilters.join(" | ")}', style: const TextStyle(fontSize: 10, color: Colors.white, fontWeight: FontWeight.bold)),
                    backgroundColor: Colors.deepPurple,
                    visualDensity: VisualDensity.compact,
                    padding: const EdgeInsets.symmetric(horizontal: 4),
                    onPressed: () {
                      final combined = _chainedFilters.map((s) => '/$s').join(' | ');
                      _chainedFilters.clear();
                      _handleSubmitted(combined);
                    },
                  ),
                ],
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

                // Interactive Task Cards (Zero Task IDs displayed)
                if (message.taskItems != null && message.taskItems!.isNotEmpty) ...[
                  const SizedBox(height: 6),
                  ...message.taskItems!.map((task) => _buildChatTaskCard(context, task)),
                ],

                // Action / Suggestion Chips
                if (!isUser && message.suggestionChips != null && message.suggestionChips!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6,
                    runSpacing: 6,
                    children: message.suggestionChips!.map((chipText) {
                      final isSkip = chipText.toLowerCase().contains('skip');
                      final isCancel = chipText.toLowerCase().contains('cancel');
                      return ActionChip(
                        label: Text(
                          chipText,
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: isSkip || isCancel ? FontWeight.w600 : FontWeight.w500,
                            color: isCancel
                                ? Colors.redAccent
                                : (isSkip ? Colors.amber.shade800 : theme.colorScheme.primary),
                          ),
                        ),
                        backgroundColor: isCancel
                            ? Colors.red.withValues(alpha: 0.08)
                            : (isSkip ? Colors.amber.withValues(alpha: 0.08) : theme.colorScheme.surface),
                        side: BorderSide(
                          color: isCancel
                              ? Colors.red.withValues(alpha: 0.3)
                              : (isSkip ? Colors.amber.withValues(alpha: 0.3) : theme.colorScheme.primary.withValues(alpha: 0.3)),
                        ),
                        padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 2),
                        visualDensity: VisualDensity.compact,
                        onPressed: () {
                          if (chipText == '/help') {
                            _openCommandPalette();
                          } else {
                            _handleSubmitted(chipText);
                          }
                        },
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
              // Due Date Chip (Zero Task IDs)
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

// Decoupled, high-performance Input Bar with dedicated [/] Palette trigger
class _ChatInputBar extends StatefulWidget {
  final WizardStep wizardStep;
  final Function(String) onSubmitted;
  final VoidCallback onOpenPalette;

  const _ChatInputBar({
    super.key,
    required this.wizardStep,
    required this.onSubmitted,
    required this.onOpenPalette,
  });

  @override
  State<_ChatInputBar> createState() => _ChatInputBarState();
}

class _ChatInputBarState extends State<_ChatInputBar> {
  final TextEditingController _controller = TextEditingController();
  final FocusNode _focusNode = FocusNode();

  void clear() {
    _controller.clear();
  }

  void setText(String text) {
    _controller.text = text;
    _controller.selection = TextSelection.fromPosition(TextPosition(offset: text.length));
    _focusNode.requestFocus();
  }

  @override
  void dispose() {
    _controller.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return SafeArea(
      top: false,
      bottom: true,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
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
            // Dedicated Quick Slash Command Palette Trigger Button
            IconButton(
              icon: Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: Colors.amber.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: const Text(
                  '/',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: Colors.amber,
                    fontFamily: 'monospace',
                  ),
                ),
              ),
              tooltip: 'Command Palette (/help)',
              onPressed: widget.onOpenPalette,
            ),
            const SizedBox(width: 4),

            // Input Field
            Expanded(
              child: TextField(
                controller: _controller,
                focusNode: _focusNode,
                minLines: 1,
                maxLines: 4,
                textInputAction: TextInputAction.send,
                onSubmitted: widget.onSubmitted,
                decoration: InputDecoration(
                  hintText: widget.wizardStep != WizardStep.none
                      ? "Answer or tap Skip / Choice..."
                      : "Type message, /command, or chain (|)...",
                  hintStyle: const TextStyle(fontSize: 13, color: Colors.grey),
                  filled: true,
                  fillColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(24),
                    borderSide: BorderSide.none,
                  ),
                ),
              ),
            ),
            const SizedBox(width: 6),

            // Send Button
            IconButton.filled(
              icon: const Icon(Icons.send_rounded, size: 18),
              onPressed: () => widget.onSubmitted(_controller.text),
            ),
          ],
        ),
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
