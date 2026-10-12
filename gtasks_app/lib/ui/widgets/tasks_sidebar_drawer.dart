import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import '../../providers/settings_provider.dart';
import 'settings_modal.dart';

class TasksSidebarDrawer extends StatefulWidget {
  const TasksSidebarDrawer({super.key});

  @override
  State<TasksSidebarDrawer> createState() => _TasksSidebarDrawerState();
}

class _TasksSidebarDrawerState extends State<TasksSidebarDrawer> {
  final TextEditingController _searchController = TextEditingController();
  bool _listsExpanded = true;
  bool _tagsExpanded = true;

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TaskProvider>();
    final settings = context.watch<SettingsProvider>();
    final theme = Theme.of(context);
    final query = _searchController.text.toLowerCase().trim();

    final lists = provider.listsWithCounts;
    final filteredLists = lists.entries.where((e) {
      if (query.isEmpty) return true;
      return e.key.toLowerCase().contains(query);
    }).toList()
      ..sort((a, b) => a.key.toLowerCase().compareTo(b.key.toLowerCase()));

    final tags = provider.tagsWithCounts;
    final filteredTags = tags.entries.where((e) {
      if (query.isEmpty) return true;
      return e.key.toLowerCase().contains(query);
    }).toList()
      ..sort((a, b) => a.key.toLowerCase().compareTo(b.key.toLowerCase()));

    final totalTasks = provider.pendingTasksCount;

    return Drawer(
      child: SafeArea(
        child: Column(
          children: [
            // Drawer Header
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                border: Border(
                  bottom: BorderSide(
                    color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5),
                  ),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Container(
                        padding: const EdgeInsets.all(6),
                        decoration: BoxDecoration(
                          color: theme.colorScheme.primary.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(Icons.check_box_outlined, color: theme.colorScheme.primary, size: 22),
                      ),
                      const SizedBox(width: 10),
                      Text(
                        'GTasks',
                        style: theme.textTheme.titleLarge?.copyWith(
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.settings_outlined, size: 20),
                        tooltip: 'Settings & Accounts',
                        onPressed: () {
                          Navigator.pop(context);
                          showDialog(
                            context: context,
                            builder: (_) => const SettingsModal(),
                          );
                        },
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  // Quick search input for lists & tags
                  TextField(
                    controller: _searchController,
                    onChanged: (_) => setState(() {}),
                    decoration: InputDecoration(
                      hintText: 'Filter lists & tags...',
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
                      contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 12),
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(8),
                        borderSide: BorderSide(color: theme.colorScheme.outlineVariant),
                      ),
                    ),
                  ),
                ],
              ),
            ),

            // Scrollable Menu Items
            Expanded(
              child: ListView(
                padding: const EdgeInsets.symmetric(vertical: 8),
                children: [
                  // All Tasks Entry
                  ListTile(
                    dense: true,
                    leading: const Icon(Icons.inbox_outlined, color: Colors.blueAccent),
                    title: const Text('All Tasks', style: TextStyle(fontWeight: FontWeight.w600)),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: provider.selectedLists.isEmpty && provider.selectedTags.isEmpty
                            ? theme.colorScheme.primary
                            : theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '$totalTasks',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: provider.selectedLists.isEmpty && provider.selectedTags.isEmpty
                              ? theme.colorScheme.onPrimary
                              : theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                    selected: provider.selectedLists.isEmpty && provider.selectedTags.isEmpty,
                    selectedTileColor: theme.colorScheme.primary.withValues(alpha: 0.1),
                    onTap: () {
                      provider.setSelectedLists({});
                      provider.setSelectedTags({});
                      Navigator.pop(context);
                    },
                  ),

                  const Divider(height: 16),

                  // Collapsible Lists Section
                  InkWell(
                    onTap: () => setState(() => _listsExpanded = !_listsExpanded),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                      child: Row(
                        children: [
                          Icon(Icons.folder_outlined, size: 18, color: theme.colorScheme.primary),
                          const SizedBox(width: 8),
                          Text(
                            'Lists (${lists.length})',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                          const Spacer(),
                          Icon(
                            _listsExpanded ? Icons.expand_less : Icons.expand_more,
                            size: 20,
                            color: theme.disabledColor,
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (_listsExpanded) ...[
                    if (filteredLists.isEmpty)
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 4),
                        child: Text('No matching lists', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      )
                    else
                      ...filteredLists.map((entry) {
                        final isSelected = provider.selectedLists.contains(entry.key);
                        return ListTile(
                          dense: true,
                          contentPadding: const EdgeInsets.only(left: 28, right: 16),
                          leading: Icon(
                            Icons.format_list_bulleted,
                            size: 16,
                            color: isSelected ? theme.colorScheme.primary : theme.disabledColor,
                          ),
                          title: Text(
                            entry.key,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                decoration: BoxDecoration(
                                  color: isSelected
                                      ? theme.colorScheme.primary
                                      : (provider.hiddenLists.contains(entry.key)
                                          ? Colors.red.withValues(alpha: 0.15)
                                          : theme.colorScheme.surfaceContainerHighest),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  '${entry.value}',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: isSelected
                                        ? theme.colorScheme.onPrimary
                                        : (provider.hiddenLists.contains(entry.key)
                                            ? Colors.red
                                            : theme.colorScheme.onSurfaceVariant),
                                  ),
                                ),
                              ),
                              IconButton(
                                icon: Icon(
                                  provider.hiddenLists.contains(entry.key)
                                      ? Icons.visibility_off
                                      : Icons.visibility_outlined,
                                  size: 16,
                                  color: provider.hiddenLists.contains(entry.key)
                                      ? Colors.redAccent
                                      : theme.disabledColor,
                                ),
                                tooltip: provider.hiddenLists.contains(entry.key)
                                    ? 'Unhide List'
                                    : 'Hide List',
                                onPressed: () {
                                  provider.toggleHiddenList(entry.key);
                                },
                              ),
                            ],
                          ),
                          selected: isSelected,
                          selectedTileColor: theme.colorScheme.primary.withValues(alpha: 0.1),
                          onTap: () {
                            provider.toggleSelectedList(entry.key);
                          },
                        );
                      }),
                  ],

                  const Divider(height: 16),

                  // Collapsible Tags Section
                  InkWell(
                    onTap: () => setState(() => _tagsExpanded = !_tagsExpanded),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                      child: Row(
                        children: [
                          Icon(Icons.label_outline, size: 18, color: Colors.teal),
                          const SizedBox(width: 8),
                          Text(
                            'Tags (${tags.length})',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                          const Spacer(),
                          Icon(
                            _tagsExpanded ? Icons.expand_less : Icons.expand_more,
                            size: 20,
                            color: theme.disabledColor,
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (_tagsExpanded) ...[
                    if (filteredTags.isEmpty)
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 4),
                        child: Text('No matching tags', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      )
                    else
                      ...filteredTags.map((entry) {
                        final isSelected = provider.selectedTags.contains(entry.key);
                        return ListTile(
                          dense: true,
                          contentPadding: const EdgeInsets.only(left: 28, right: 16),
                          leading: Text(
                            '#',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                              color: isSelected ? Colors.teal : theme.disabledColor,
                            ),
                          ),
                          title: Text(
                            entry.key,
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                decoration: BoxDecoration(
                                  color: isSelected
                                      ? Colors.teal
                                      : (provider.hiddenTags.contains(entry.key)
                                          ? Colors.red.withValues(alpha: 0.15)
                                          : theme.colorScheme.surfaceContainerHighest),
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  '${entry.value}',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: isSelected
                                        ? Colors.white
                                        : (provider.hiddenTags.contains(entry.key)
                                            ? Colors.red
                                            : theme.colorScheme.onSurfaceVariant),
                                  ),
                                ),
                              ),
                              IconButton(
                                icon: Icon(
                                  provider.hiddenTags.contains(entry.key)
                                      ? Icons.visibility_off
                                      : Icons.visibility_outlined,
                                  size: 16,
                                  color: provider.hiddenTags.contains(entry.key)
                                      ? Colors.redAccent
                                      : theme.disabledColor,
                                ),
                                tooltip: provider.hiddenTags.contains(entry.key)
                                    ? 'Unhide Tag'
                                    : 'Hide Tag',
                                onPressed: () {
                                  provider.toggleHiddenTag(entry.key);
                                },
                              ),
                            ],
                          ),
                          selected: isSelected,
                          selectedTileColor: Colors.teal.withValues(alpha: 0.1),
                          onTap: () {
                            provider.toggleSelectedTag(entry.key);
                          },
                        );
                      }),
                  ],
                ],
              ),
            ),

            // Drawer Footer
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
              decoration: BoxDecoration(
                border: Border(
                  top: BorderSide(
                    color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5),
                  ),
                ),
              ),
              child: Row(
                children: [
                  IconButton(
                    icon: Icon(
                      settings.themeMode == 'dark'
                          ? Icons.dark_mode
                          : (settings.themeMode == 'light' ? Icons.light_mode : Icons.brightness_auto),
                      size: 20,
                    ),
                    tooltip: 'Theme: ${settings.themeMode}',
                    onPressed: () {
                      final modes = ['system', 'light', 'dark'];
                      final next = modes[(modes.indexOf(settings.themeMode) + 1) % modes.length];
                      settings.setThemeMode(next);
                    },
                  ),
                  const Spacer(),
                  Text(
                    '${provider.tasks.length} showing',
                    style: TextStyle(fontSize: 12, color: theme.disabledColor),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
