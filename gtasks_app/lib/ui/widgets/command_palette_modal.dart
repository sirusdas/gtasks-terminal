import 'package:flutter/material.dart';

class SlashCommandInfo {
  final String name;
  final String alias;
  final String description;
  final String example;
  final String category;
  final IconData icon;
  final Color color;

  const SlashCommandInfo({
    required this.name,
    required this.alias,
    required this.description,
    required this.example,
    required this.category,
    required this.icon,
    required this.color,
  });
}

class CommandPaletteModal extends StatefulWidget {
  final Function(String command, bool runImmediately) onSelectCommand;

  const CommandPaletteModal({
    super.key,
    required this.onSelectCommand,
  });

  static Future<void> show(
    BuildContext context, {
    required Function(String command, bool runImmediately) onSelectCommand,
  }) {
    return showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => CommandPaletteModal(onSelectCommand: onSelectCommand),
    );
  }

  @override
  State<CommandPaletteModal> createState() => _CommandPaletteModalState();
}

class _CommandPaletteModalState extends State<CommandPaletteModal> {
  final TextEditingController _searchController = TextEditingController();
  String _selectedCategory = 'All';

  final List<SlashCommandInfo> _commands = const [
    SlashCommandInfo(
      name: '/help',
      alias: '/h',
      description: 'Open interactive command guide & search',
      example: '/help',
      category: 'System',
      icon: Icons.help_outline,
      color: Colors.blueAccent,
    ),
    SlashCommandInfo(
      name: '/add',
      alias: '/a',
      description: 'Start interactive Claude CLI-style Q&A task wizard',
      example: '/add (or /add buy milk today high)',
      category: 'Tasks',
      icon: Icons.add_task,
      color: Colors.green,
    ),
    SlashCommandInfo(
      name: '/today',
      alias: '/t',
      description: 'Show tasks scheduled for today',
      example: '/today',
      category: 'Filters',
      icon: Icons.calendar_today,
      color: Colors.amber,
    ),
    SlashCommandInfo(
      name: '/pending',
      alias: '/p',
      description: 'List all active pending to-do tasks',
      example: '/pending',
      category: 'Filters',
      icon: Icons.hourglass_top,
      color: Colors.teal,
    ),
    SlashCommandInfo(
      name: '/overdue',
      alias: '/o',
      description: 'Show overdue tasks requiring urgent action',
      example: '/overdue',
      category: 'Filters',
      icon: Icons.warning_amber_rounded,
      color: Colors.redAccent,
    ),
    SlashCommandInfo(
      name: '/high',
      alias: '/urgent',
      description: 'Show high and critical priority tasks',
      example: '/high',
      category: 'Filters',
      icon: Icons.bolt,
      color: Colors.orange,
    ),
    SlashCommandInfo(
      name: '/chain',
      alias: '| / &&',
      description: 'Combine multiple commands/filters with | or &&',
      example: '/today | /high (or /pending && /overdue)',
      category: 'Chained',
      icon: Icons.link,
      color: Colors.purpleAccent,
    ),
    SlashCommandInfo(
      name: '/search',
      alias: '/s',
      description: 'Search tasks by keyword, tag, notes, or space',
      example: '/search taxes',
      category: 'Tasks',
      icon: Icons.search,
      color: Colors.indigoAccent,
    ),
    SlashCommandInfo(
      name: '/spaces',
      alias: '/sp',
      description: 'View available spaces, subspaces and task counts',
      example: '/spaces',
      category: 'Productivity',
      icon: Icons.rocket_launch,
      color: Colors.deepPurple,
    ),
    SlashCommandInfo(
      name: '/summary',
      alias: '/stats',
      description: 'Productivity stats, counts, and completion rate',
      example: '/summary',
      category: 'Productivity',
      icon: Icons.pie_chart_outline,
      color: Colors.cyan,
    ),
    SlashCommandInfo(
      name: '/scope',
      alias: '/view',
      description: 'Toggle scope between Current View and All Tasks',
      example: '/scope (or /view)',
      category: 'Productivity',
      icon: Icons.filter_alt_outlined,
      color: Colors.teal,
    ),
    SlashCommandInfo(
      name: '/these',
      alias: '/focus',
      description: 'Summarize and focus on tasks visible in current view',
      example: '/these',
      category: 'Filters',
      icon: Icons.visibility_outlined,
      color: Colors.amber,
    ),
    SlashCommandInfo(
      name: '/doneall',
      alias: '/completeall',
      description: 'Mark all visible tasks in current view completed',
      example: '/doneall',
      category: 'Tasks',
      icon: Icons.done_all,
      color: Colors.green,
    ),
    SlashCommandInfo(
      name: '/done',
      alias: '/complete',
      description: 'Mark task completed by name or index',
      example: '/done 1',
      category: 'Tasks',
      icon: Icons.check_circle_outline,
      color: Colors.lightGreen,
    ),
    SlashCommandInfo(
      name: '/delete',
      alias: '/rm',
      description: 'Safely delete task by name or index',
      example: '/delete 2',
      category: 'Tasks',
      icon: Icons.delete_outline,
      color: Colors.red,
    ),
    SlashCommandInfo(
      name: '/open',
      alias: '/form',
      description: 'Open full-screen Flutter task creation form',
      example: '/open',
      category: 'Tasks',
      icon: Icons.edit_note,
      color: Colors.blue,
    ),
    SlashCommandInfo(
      name: '/clear',
      alias: '/cls',
      description: 'Clear current AI chat history',
      example: '/clear',
      category: 'System',
      icon: Icons.delete_sweep_outlined,
      color: Colors.blueGrey,
    ),
  ];

  final List<String> _categories = const [
    'All',
    'Tasks',
    'Filters',
    'Chained',
    'Productivity',
    'System',
  ];

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _searchController.text.trim().toLowerCase();

    final filtered = _commands.where((cmd) {
      if (_selectedCategory != 'All' && cmd.category != _selectedCategory) {
        return false;
      }
      if (query.isEmpty) return true;
      return cmd.name.toLowerCase().contains(query) ||
          cmd.alias.toLowerCase().contains(query) ||
          cmd.description.toLowerCase().contains(query) ||
          cmd.example.toLowerCase().contains(query);
    }).toList();

    return DraggableScrollableSheet(
      initialChildSize: 0.75,
      minChildSize: 0.4,
      maxChildSize: 0.95,
      builder: (context, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 16,
                offset: const Offset(0, -4),
              ),
            ],
          ),
          child: Column(
            children: [
              // Handle bar
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(top: 10, bottom: 8),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.outlineVariant,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // Title and Search Bar
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 8),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: Colors.amber.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.terminal, color: Colors.amber, size: 20),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Command Palette',
                            style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                          ),
                          Text(
                            'Tap a command to run or insert into chat',
                            style: theme.textTheme.bodySmall?.copyWith(color: Colors.grey, fontSize: 11),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close, size: 20),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),

              // Realtime Search Input
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: TextField(
                  controller: _searchController,
                  autofocus: false,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Search commands, syntax, or keywords...',
                    hintStyle: const TextStyle(fontSize: 13, color: Colors.grey),
                    prefixIcon: const Icon(Icons.search, size: 18),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 16),
                            onPressed: () {
                              _searchController.clear();
                              setState(() {});
                            },
                          )
                        : null,
                    isDense: true,
                    filled: true,
                    fillColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.4),
                    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    border: OutlineInputBorder(
                      borderRadius: BorderRadius.circular(12),
                      borderSide: BorderSide(color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5)),
                    ),
                  ),
                ),
              ),

              // Category Filter Pills
              Container(
                height: 42,
                padding: const EdgeInsets.symmetric(vertical: 4),
                child: ListView.separated(
                  scrollDirection: Axis.horizontal,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemCount: _categories.length,
                  separatorBuilder: (ctx, idx) => const SizedBox(width: 6),
                  itemBuilder: (context, index) {
                    final cat = _categories[index];
                    final isSelected = _selectedCategory == cat;
                    return ChoiceChip(
                      label: Text(
                        cat,
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                          color: isSelected ? theme.colorScheme.onPrimary : theme.colorScheme.onSurface,
                        ),
                      ),
                      selected: isSelected,
                      selectedColor: theme.colorScheme.primary,
                      showCheckmark: false,
                      visualDensity: VisualDensity.compact,
                      padding: const EdgeInsets.symmetric(horizontal: 6),
                      onSelected: (_) => setState(() => _selectedCategory = cat),
                    );
                  },
                ),
              ),

              const Divider(height: 1),

              // Commands List
              Expanded(
                child: filtered.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(24),
                          child: Column(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.search_off, size: 40, color: Colors.grey),
                              const SizedBox(height: 10),
                              Text(
                                'No commands match "${_searchController.text}"',
                                style: const TextStyle(color: Colors.grey),
                              ),
                            ],
                          ),
                        ),
                      )
                    : ListView.builder(
                        controller: scrollController,
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                        itemCount: filtered.length,
                        itemBuilder: (context, index) {
                          final cmd = filtered[index];
                          return Card(
                            elevation: 0,
                            margin: const EdgeInsets.symmetric(vertical: 4),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                              side: BorderSide(
                                color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                              ),
                            ),
                            child: ListTile(
                              dense: true,
                              leading: Container(
                                padding: const EdgeInsets.all(8),
                                decoration: BoxDecoration(
                                  color: cmd.color.withValues(alpha: 0.12),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Icon(cmd.icon, color: cmd.color, size: 18),
                              ),
                              title: Row(
                                children: [
                                  Text(
                                    cmd.name,
                                    style: const TextStyle(
                                      fontWeight: FontWeight.bold,
                                      fontSize: 14,
                                      fontFamily: 'monospace',
                                    ),
                                  ),
                                  const SizedBox(width: 6),
                                  Text(
                                    '(${cmd.alias})',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: Colors.grey.shade600,
                                      fontFamily: 'monospace',
                                    ),
                                  ),
                                ],
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const SizedBox(height: 2),
                                  Text(cmd.description, style: const TextStyle(fontSize: 12)),
                                  const SizedBox(height: 4),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                                      borderRadius: BorderRadius.circular(4),
                                    ),
                                    child: Text(
                                      'Ex: ${cmd.example}',
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontFamily: 'monospace',
                                        color: theme.colorScheme.primary,
                                      ),
                                    ),
                                  ),
                                ],
                              ),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: const Icon(Icons.input_rounded, size: 18),
                                    tooltip: 'Insert into chat',
                                    onPressed: () {
                                      Navigator.pop(context);
                                      widget.onSelectCommand(cmd.name, false);
                                    },
                                  ),
                                  FilledButton(
                                    style: FilledButton.styleFrom(
                                      visualDensity: VisualDensity.compact,
                                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                                    ),
                                    onPressed: () {
                                      Navigator.pop(context);
                                      widget.onSelectCommand(cmd.name, true);
                                    },
                                    child: const Text('Run', style: TextStyle(fontSize: 12)),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        );
      },
    );
  }
}
