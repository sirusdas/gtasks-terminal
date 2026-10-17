import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../../providers/ai_chat_provider.dart';
import '../../../providers/settings_provider.dart';
import 'ai_settings_modal.dart';

class AiChatBottomSheet extends StatefulWidget {
  const AiChatBottomSheet({super.key});

  static Future<void> show(BuildContext context) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => const AiChatBottomSheet(),
    );
  }

  @override
  State<AiChatBottomSheet> createState() => _AiChatBottomSheetState();
}

class _AiChatBottomSheetState extends State<AiChatBottomSheet> {
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final FocusNode _focusNode = FocusNode();

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _scrollToBottom();
    });
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    _focusNode.dispose();
    super.dispose();
  }

  void _scrollToBottom() {
    if (_scrollController.hasClients) {
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeOut,
      );
    }
  }

  void _handleSend([String? presetText]) {
    final text = (presetText ?? _inputController.text).trim();
    if (text.isEmpty) return;

    final ai = context.read<AiChatProvider>();
    _inputController.clear();
    ai.sendMessage(text);

    Future.delayed(const Duration(milliseconds: 150), _scrollToBottom);
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final ai = context.watch<AiChatProvider>();
    final settings = context.watch<SettingsProvider>();

    final double sheetHeight = MediaQuery.of(context).size.height * 0.88;

    return Container(
      height: sheetHeight,
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF161A22) : Colors.white,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.25),
            blurRadius: 16,
            offset: const Offset(0, -4),
          ),
        ],
      ),
      child: Column(
        children: [
          // Drag handle
          Center(
            child: Container(
              margin: const EdgeInsets.only(top: 10, bottom: 6),
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: Colors.grey.withOpacity(0.4),
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),

          // Header
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    gradient: const LinearGradient(
                      colors: [Color(0xFF8B5CF6), Color(0xFF3B82F6)],
                      begin: Alignment.topLeft,
                      end: Alignment.bottomRight,
                    ),
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(Icons.auto_awesome, color: Colors.white, size: 18),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Text(
                            'GTasks AI',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          const SizedBox(width: 8),
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                            decoration: BoxDecoration(
                              color: Colors.purple.withOpacity(0.15),
                              borderRadius: BorderRadius.circular(6),
                            ),
                            child: Text(
                              settings.aiProviderType == 'gemini'
                                  ? (settings.aiModelName.contains('pro') ? 'Gemini Pro' : 'Gemini Flash')
                                  : 'Dashboard Proxy',
                              style: const TextStyle(fontSize: 10, color: Colors.purple, fontWeight: FontWeight.bold),
                            ),
                          ),
                        ],
                      ),
                      Text(
                        'Autonomous task assistant with live MCP tools',
                        style: TextStyle(fontSize: 11, color: Colors.grey.shade600),
                      ),
                    ],
                  ),
                ),
                IconButton(
                  tooltip: 'New Chat Session',
                  icon: const Icon(Icons.add_comment_outlined, size: 20),
                  onPressed: () => ai.startNewSession(),
                ),
                IconButton(
                  tooltip: 'AI Settings',
                  icon: const Icon(Icons.settings_outlined, size: 20),
                  onPressed: () {
                    showDialog(
                      context: context,
                      builder: (_) => const AiSettingsModal(),
                    );
                  },
                ),
                IconButton(
                  tooltip: 'Close',
                  icon: const Icon(Icons.close, size: 20),
                  onPressed: () => Navigator.of(context).pop(),
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // Workflow Quick Chips Bar
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            child: Row(
              children: [
                _buildWorkflowChip(
                  icon: Icons.wb_sunny_outlined,
                  label: 'Morning Briefing',
                  color: Colors.amber,
                  onTap: () => _handleSend('/morning'),
                ),
                const SizedBox(width: 6),
                _buildWorkflowChip(
                  icon: Icons.nightlight_outlined,
                  label: 'Evening Review',
                  color: Colors.indigo,
                  onTap: () => _handleSend('/evening'),
                ),
                const SizedBox(width: 6),
                _buildWorkflowChip(
                  icon: Icons.inbox_outlined,
                  label: 'Inbox Triage',
                  color: Colors.teal,
                  onTap: () => _handleSend('/triage'),
                ),
                const SizedBox(width: 6),
                _buildWorkflowChip(
                  icon: Icons.account_tree_outlined,
                  label: 'Breakdown',
                  color: Colors.deepOrange,
                  onTap: () => _handleSend('/breakdown'),
                ),
              ],
            ),
          ),

          const Divider(height: 1),

          // Messages View or Empty State
          Expanded(
            child: ai.messages.isEmpty
                ? _buildEmptyState(context, settings)
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                    itemCount: ai.messages.length,
                    itemBuilder: (ctx, index) {
                      final msg = ai.messages[index];
                      return _buildMessageItem(context, msg);
                    },
                  ),
          ),

          // Status & Error Indicator
          if (ai.isLoading)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
              color: Colors.purple.withOpacity(0.08),
              child: Row(
                children: [
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2, color: Colors.purple),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      ai.statusText ?? 'Processing...',
                      style: const TextStyle(fontSize: 12, color: Colors.purple, fontWeight: FontWeight.w500),
                    ),
                  ),
                ],
              ),
            ),

          if (ai.errorMessage != null)
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              color: Colors.red.withOpacity(0.12),
              child: Row(
                children: [
                  const Icon(Icons.error_outline, color: Colors.red, size: 16),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      ai.errorMessage!,
                      style: const TextStyle(fontSize: 12, color: Colors.red),
                    ),
                  ),
                  if (ai.errorMessage!.contains('API Key'))
                    TextButton(
                      style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                      onPressed: () {
                        showDialog(context: context, builder: (_) => const AiSettingsModal());
                      },
                      child: const Text('Configure', style: TextStyle(fontSize: 12)),
                    ),
                ],
              ),
            ),

          // Bottom Input Bar
          Container(
            padding: EdgeInsets.only(
              left: 12,
              right: 12,
              top: 8,
              bottom: MediaQuery.of(context).viewInsets.bottom + 8,
            ),
            decoration: BoxDecoration(
              color: isDark ? const Color(0xFF1E222B) : Colors.grey.shade50,
              border: Border(top: BorderSide(color: isDark ? Colors.white10 : Colors.black12)),
            ),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _inputController,
                    focusNode: _focusNode,
                    minLines: 1,
                    maxLines: 4,
                    decoration: InputDecoration(
                      hintText: 'Ask anything or try /morning...',
                      hintStyle: TextStyle(fontSize: 14, color: Colors.grey.shade500),
                      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      filled: true,
                      fillColor: isDark ? const Color(0xFF161A22) : Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(20),
                        borderSide: BorderSide.none,
                      ),
                    ),
                    onSubmitted: (val) => _handleSend(),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton.filled(
                  style: IconButton.styleFrom(
                    backgroundColor: Colors.purple,
                    foregroundColor: Colors.white,
                  ),
                  icon: const Icon(Icons.arrow_upward, size: 20),
                  onPressed: ai.isLoading ? null : () => _handleSend(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWorkflowChip({
    required IconData icon,
    required String label,
    required Color color,
    required VoidCallback onTap,
  }) {
    return ActionChip(
      avatar: Icon(icon, size: 14, color: color),
      label: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
      backgroundColor: color.withOpacity(0.1),
      side: BorderSide(color: color.withOpacity(0.2)),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      onPressed: onTap,
    );
  }

  Widget _buildEmptyState(BuildContext context, SettingsProvider settings) {
    return Center(
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.purple.withOpacity(0.12),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.purple, size: 36),
            ),
            const SizedBox(height: 14),
            const Text(
              'How can I help you today?',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18),
            ),
            const SizedBox(height: 6),
            Text(
              'I can manage your tasks, spaces, batch reschedule, run morning briefings, and analyze your productivity.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: Colors.grey.shade600),
            ),
            const SizedBox(height: 20),

            // Quick suggestion buttons
            Wrap(
              spacing: 8,
              runSpacing: 8,
              alignment: WrapAlignment.center,
              children: [
                _buildPromptSuggestion('What tasks are due today?'),
                _buildPromptSuggestion('Show my overdue tasks'),
                _buildPromptSuggestion('Reschedule overdue tasks to tomorrow'),
                _buildPromptSuggestion('List all my spaces and sub-spaces'),
                _buildPromptSuggestion('Give me a productivity report for this week'),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPromptSuggestion(String prompt) {
    return InkWell(
      borderRadius: BorderRadius.circular(14),
      onTap: () => _handleSend(prompt),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          border: Border.all(color: Colors.purple.withOpacity(0.25)),
          borderRadius: BorderRadius.circular(14),
        ),
        child: Text(
          prompt,
          style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w500),
        ),
      ),
    );
  }

  Widget _buildMessageItem(BuildContext context, AiChatMessage msg) {
    final isUser = msg.role == 'user';
    final isDark = Theme.of(context).brightness == Brightness.dark;

    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Row(
        mainAxisAlignment: isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (!isUser) ...[
            Container(
              margin: const EdgeInsets.only(top: 2, right: 8),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.purple.withOpacity(0.15),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(Icons.auto_awesome, color: Colors.purple, size: 16),
            ),
          ],
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
              decoration: BoxDecoration(
                color: isUser
                    ? Colors.purple
                    : (isDark ? const Color(0xFF222734) : const Color(0xFFF1F5F9)),
                borderRadius: BorderRadius.circular(16).copyWith(
                  bottomRight: isUser ? const Radius.circular(2) : null,
                  bottomLeft: !isUser ? const Radius.circular(2) : null,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  if (!isUser && msg.toolCalls != null && msg.toolCalls!.isNotEmpty)
                    Container(
                      margin: const EdgeInsets.only(bottom: 8),
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.blue.withOpacity(0.1),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(Icons.bolt, size: 14, color: Colors.blue),
                          const SizedBox(width: 4),
                          Text(
                            'Tools: ${msg.toolCalls!.map((t) => t is Map ? t['name'] : t.toString()).join(', ')}',
                            style: const TextStyle(fontSize: 11, color: Colors.blue, fontWeight: FontWeight.bold),
                          ),
                        ],
                      ),
                    ),
                  if (isUser)
                    Text(
                      msg.content,
                      style: const TextStyle(color: Colors.white, fontSize: 14),
                    )
                  else
                    SelectableText(
                      msg.content,
                      style: TextStyle(
                        fontSize: 14,
                        color: isDark ? Colors.white70 : Colors.black87,
                      ),
                    ),
                ],
              ),
            ),
          ),
          if (isUser) ...[
            const SizedBox(width: 8),
            Container(
              margin: const EdgeInsets.only(top: 2),
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: Colors.grey.withOpacity(0.2),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.person, size: 16),
            ),
          ],
        ],
      ),
    );
  }
}
