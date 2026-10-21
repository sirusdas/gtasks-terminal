import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import '../../providers/settings_provider.dart';
import 'settings_modal.dart';
import '../screens/ai_chat_screen.dart';
import '../../mandala/mandala_screen.dart';

class TasksSidebarDrawer extends StatefulWidget {
  const TasksSidebarDrawer({super.key});

  @override
  State<TasksSidebarDrawer> createState() => _TasksSidebarDrawerState();
}

class _TasksSidebarDrawerState extends State<TasksSidebarDrawer> {
  final TextEditingController _searchController = TextEditingController();
  Timer? _debounce;
  bool _listsExpanded = true;
  bool _spacesExpanded = true;
  bool _tagsExpanded = true;

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  void _showSidebarItemOptions(
    BuildContext context,
    TaskProvider provider, {
    required String title,
    required IconData icon,
    String? list,
    String? space,
    String? subspace,
    String? tag,
  }) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      builder: (ctx) {
        final theme = Theme.of(ctx);
        return Container(
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          padding: const EdgeInsets.symmetric(vertical: 12),
          child: SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 36,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.outlineVariant,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 4),
                  child: Row(
                    children: [
                      Icon(icon, size: 20, color: theme.colorScheme.primary),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          title,
                          style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
                const Divider(height: 16),
                ListTile(
                  leading: const Icon(Icons.tab, color: Colors.blueAccent),
                  title: const Text('Open in New Tab', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: const Text('Creates a new live tab with these filters'),
                  onTap: () {
                    Navigator.pop(ctx);
                    Navigator.pop(context);
                    provider.addNewTab(
                      title: title,
                      iconCodePoint: icon.codePoint,
                      list: list,
                      space: space,
                      subspace: subspace,
                      tag: tag,
                      account: provider.selectedAccount,
                    );
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Opened "$title" in new tab'),
                        duration: const Duration(seconds: 2),
                      ),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.hub_outlined, color: Colors.purpleAccent),
                  title: const Text('Open in Mandala Focus', style: TextStyle(fontWeight: FontWeight.bold)),
                  subtitle: const Text('Visualize this focus branch as a sacred mandala'),
                  onTap: () {
                    Navigator.pop(ctx);
                    Navigator.pop(context);
                    Navigator.push(
                      context,
                      MaterialPageRoute(
                        builder: (_) => MandalaScreen(
                          title: title,
                        ),
                      ),
                    );
                  },
                ),
                ListTile(
                  leading: const Icon(Icons.filter_alt_outlined),
                  title: const Text('Filter in Current View'),
                  onTap: () {
                    Navigator.pop(ctx);
                    Navigator.pop(context);
                    if (list != null) {
                      provider.setSelectedLists({list});
                    } else if (space != null) {
                      provider.setSelectedSpace(space, subspace: subspace);
                    } else if (tag != null) {
                      provider.setSelectedTags({tag});
                    } else {
                      provider.clearAllFilters();
                    }
                  },
                ),
                if (space != null || tag != null)
                  ListTile(
                    leading: const Icon(Icons.delete_outline, color: Colors.redAccent),
                    title: Text(
                      tag != null
                          ? 'Delete Tag #$tag from All Tasks'
                          : (subspace != null
                              ? 'Delete Sub-space $subspace from All Tasks'
                              : 'Delete Space $space from All Tasks'),
                      style: const TextStyle(color: Colors.redAccent, fontWeight: FontWeight.w600),
                    ),
                    onTap: () {
                      Navigator.pop(ctx);
                      _confirmSidebarItemDelete(
                        context,
                        provider,
                        tag: tag,
                        space: space,
                        subspace: subspace,
                      );
                    },
                  ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _confirmSidebarItemDelete(
    BuildContext context,
    TaskProvider provider, {
    String? tag,
    String? space,
    String? subspace,
  }) {
    final label = tag != null
        ? "tag '#$tag'"
        : (subspace != null ? "sub-space '$space › $subspace'" : "space '$space'");

    showDialog(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.warning_amber_rounded, color: Colors.redAccent),
            SizedBox(width: 8),
            Text('Confirm Removal'),
          ],
        ),
        content: Text('Are you sure you want to remove $label from all tasks?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Cancel'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.redAccent),
            onPressed: () async {
              Navigator.pop(ctx);
              if (tag != null) {
                await provider.removeTagGlobally(tag);
              } else if (subspace != null) {
                await provider.removeSubspaceGlobally(space!, subspace);
              } else if (space != null) {
                await provider.removeSpaceGlobally(space);
              }
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Removed $label')),
                );
              }
            },
            child: const Text('Delete'),
          ),
        ],
      ),
    );
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

    final spaces = provider.spacesWithCounts;
    final subspaces = provider.subspacesWithCounts;
    final filteredSpaces = spaces.entries.where((e) {
      if (query.isEmpty) return true;
      final spaceMatch = e.key.toLowerCase().contains(query);
      final subsMatch = (subspaces[e.key]?.keys ?? []).any((s) => s.toLowerCase().contains(query));
      return spaceMatch || subsMatch;
    }).toList()
      ..sort((a, b) => a.key.toLowerCase().compareTo(b.key.toLowerCase()));

    final tags = provider.tagsWithCounts;
    final filteredTags = tags.entries.where((e) {
      if (query.isEmpty) return true;
      return e.key.toLowerCase().contains(query);
    }).toList()
      ..sort((a, b) => a.key.toLowerCase().compareTo(b.key.toLowerCase()));

    final totalTasks = provider.pendingTasksCount;
    final isAllSelected = provider.selectedLists.isEmpty &&
        provider.selectedTags.isEmpty &&
        provider.selectedSpace == null;

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
                    onChanged: (_) {
                      _debounce?.cancel();
                      _debounce = Timer(const Duration(milliseconds: 150), () {
                        if (mounted) setState(() {});
                      });
                    },
                    decoration: InputDecoration(
                      hintText: 'Filter lists & tags...',
                      prefixIcon: const Icon(Icons.search, size: 18),
                      suffixIcon: _searchController.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 16),
                              onPressed: () {
                                _debounce?.cancel();
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
                        color: isAllSelected
                            ? theme.colorScheme.primary
                            : theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        '$totalTasks',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: isAllSelected
                              ? theme.colorScheme.onPrimary
                              : theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                    selected: isAllSelected,
                    selectedTileColor: theme.colorScheme.primary.withValues(alpha: 0.1),
                    onTap: () {
                      provider.setSelectedLists({});
                      provider.setSelectedTags({});
                      provider.clearSpaceFilter();
                      Navigator.pop(context);
                    },
                    onLongPress: () => _showSidebarItemOptions(
                      context,
                      provider,
                      title: 'All Tasks',
                      icon: Icons.inbox_outlined,
                    ),
                  ),

                  // Mandala View Entry
                  ListTile(
                    dense: true,
                    leading: const Icon(Icons.hub_outlined, color: Colors.purpleAccent),
                    title: const Text('Mandala View', style: TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: const Text('Sacred radial task visualization', style: TextStyle(fontSize: 11)),
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (_) => MandalaScreen(
                            initialTasks: provider.tasks,
                          ),
                        ),
                      );
                    },
                  ),

                  ListTile(
                    dense: true,
                    leading: Container(
                      padding: const EdgeInsets.all(5),
                      decoration: BoxDecoration(
                        color: Colors.amber.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Icon(Icons.auto_awesome, color: Colors.amber, size: 18),
                    ),
                    title: const Text('AI Assistant', style: TextStyle(fontWeight: FontWeight.w600)),
                    subtitle: const Text('Chat & Smart Actions', style: TextStyle(fontSize: 11, color: Colors.grey)),
                    trailing: const Icon(Icons.chevron_right, size: 18, color: Colors.grey),
                    onTap: () {
                      Navigator.pop(context);
                      Navigator.push(
                        context,
                        MaterialPageRoute(builder: (_) => const AiChatScreen()),
                      );
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
                          onLongPress: () => _showSidebarItemOptions(
                            context,
                            provider,
                            title: entry.key,
                            icon: Icons.format_list_bulleted,
                            list: entry.key,
                          ),
                        );
                      }),
                  ],

                  const Divider(height: 16),

                  // Collapsible Spaces Section
                  InkWell(
                    onTap: () => setState(() => _spacesExpanded = !_spacesExpanded),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                      child: Row(
                        children: [
                          const Icon(Icons.rocket_launch_outlined, size: 18, color: Colors.deepPurpleAccent),
                          const SizedBox(width: 8),
                          Text(
                            'Spaces (${spaces.length})',
                            style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                          ),
                          const Spacer(),
                          Icon(
                            _spacesExpanded ? Icons.expand_less : Icons.expand_more,
                            size: 20,
                            color: theme.disabledColor,
                          ),
                        ],
                      ),
                    ),
                  ),
                  if (_spacesExpanded) ...[
                    if (filteredSpaces.isEmpty)
                      const Padding(
                        padding: EdgeInsets.symmetric(horizontal: 24, vertical: 4),
                        child: Text('No matching spaces', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      )
                    else
                      ...filteredSpaces.map((entry) {
                        final isSpaceSelected = provider.selectedSpace == entry.key && provider.selectedSubspace == null;
                        final spaceSubs = subspaces[entry.key] ?? {};
                        final filteredSubs = spaceSubs.entries.where((sub) {
                          if (query.isEmpty) return true;
                          return sub.key.toLowerCase().contains(query) || entry.key.toLowerCase().contains(query);
                        }).toList()
                          ..sort((a, b) => a.key.toLowerCase().compareTo(b.key.toLowerCase()));

                        return Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            ListTile(
                              dense: true,
                              contentPadding: const EdgeInsets.only(left: 28, right: 16),
                              leading: Icon(
                                Icons.circle,
                                size: 10,
                                color: isSpaceSelected ? Colors.deepPurpleAccent : theme.disabledColor,
                              ),
                              title: Text(
                                entry.key,
                                style: TextStyle(
                                  fontSize: 13,
                                  fontWeight: isSpaceSelected ? FontWeight.bold : FontWeight.normal,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                              trailing: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                decoration: BoxDecoration(
                                  color: isSpaceSelected
                                      ? Colors.deepPurpleAccent
                                      : theme.colorScheme.surfaceContainerHighest,
                                  borderRadius: BorderRadius.circular(10),
                                ),
                                child: Text(
                                  '${entry.value}',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.bold,
                                    color: isSpaceSelected
                                        ? Colors.white
                                        : theme.colorScheme.onSurfaceVariant,
                                  ),
                                ),
                              ),
                              selected: isSpaceSelected,
                              selectedTileColor: Colors.deepPurpleAccent.withValues(alpha: 0.1),
                              onTap: () {
                                provider.setSelectedSpace(entry.key);
                              },
                              onLongPress: () => _showSidebarItemOptions(
                                context,
                                provider,
                                title: entry.key,
                                icon: Icons.rocket_launch_rounded,
                                space: entry.key,
                              ),
                            ),
                            if (filteredSubs.isNotEmpty)
                              ...filteredSubs.map((subEntry) {
                                final isSubSelected = provider.selectedSpace == entry.key &&
                                    provider.selectedSubspace == subEntry.key;
                                return ListTile(
                                  dense: true,
                                  contentPadding: const EdgeInsets.only(left: 48, right: 16),
                                  leading: Icon(
                                    Icons.subdirectory_arrow_right,
                                    size: 14,
                                    color: isSubSelected ? Colors.deepPurpleAccent : theme.disabledColor,
                                  ),
                                  title: Text(
                                    subEntry.key,
                                    style: TextStyle(
                                      fontSize: 12,
                                      fontWeight: isSubSelected ? FontWeight.bold : FontWeight.normal,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                  trailing: Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                                    decoration: BoxDecoration(
                                      color: isSubSelected
                                          ? Colors.deepPurpleAccent
                                          : theme.colorScheme.surfaceContainerHighest,
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      '${subEntry.value}',
                                      style: TextStyle(
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                        color: isSubSelected
                                            ? Colors.white
                                            : theme.colorScheme.onSurfaceVariant,
                                      ),
                                    ),
                                  ),
                                  selected: isSubSelected,
                                  selectedTileColor: Colors.deepPurpleAccent.withValues(alpha: 0.08),
                                  onTap: () {
                                    provider.setSelectedSpace(entry.key, subspace: subEntry.key);
                                  },
                                  onLongPress: () => _showSidebarItemOptions(
                                    context,
                                    provider,
                                    title: '${entry.key} › ${subEntry.key}',
                                    icon: Icons.subdirectory_arrow_right,
                                    space: entry.key,
                                    subspace: subEntry.key,
                                  ),
                                );
                              }),
                          ],
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
                          onLongPress: () => _showSidebarItemOptions(
                            context,
                            provider,
                            title: '#${entry.key}',
                            icon: Icons.label_outline,
                            tag: entry.key,
                          ),
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
