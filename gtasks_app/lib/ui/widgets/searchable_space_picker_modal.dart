import 'package:flutter/material.dart';

class SearchableSpacePickerModal extends StatefulWidget {
  final Map<String, int> spacesWithCounts;
  final Map<String, Map<String, int>> subspacesWithCounts;
  final Map<String, List<String>> initialSelected;
  final bool isSingleSelect;
  final ValueChanged<Map<String, List<String>>> onSelectionConfirmed;

  const SearchableSpacePickerModal({
    super.key,
    required this.spacesWithCounts,
    required this.subspacesWithCounts,
    required this.initialSelected,
    this.isSingleSelect = false,
    required this.onSelectionConfirmed,
  });

  static Future<Map<String, List<String>>?> show({
    required BuildContext context,
    required Map<String, int> spacesWithCounts,
    required Map<String, Map<String, int>> subspacesWithCounts,
    required Map<String, List<String>> initialSelected,
    bool isSingleSelect = false,
  }) {
    return showModalBottomSheet<Map<String, List<String>>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => SearchableSpacePickerModal(
        spacesWithCounts: spacesWithCounts,
        subspacesWithCounts: subspacesWithCounts,
        initialSelected: initialSelected,
        isSingleSelect: isSingleSelect,
        onSelectionConfirmed: (selected) => Navigator.pop(ctx, selected),
      ),
    );
  }

  @override
  State<SearchableSpacePickerModal> createState() => _SearchableSpacePickerModalState();
}

class _SearchableSpacePickerModalState extends State<SearchableSpacePickerModal> {
  // Map of selected space -> Set of selected sub-spaces (empty set = entire space selected)
  late Map<String, Set<String>> _selected;
  // Accordion state: which space cards are currently expanded
  final Set<String> _expandedSpaces = {};
  // Dynamic map of all spaces (including user-created ones during this session)
  late Map<String, int> _allSpaces;
  late Map<String, Map<String, int>> _allSubspaces;

  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _newSubspaceController = TextEditingController();
  String? _addingSubspaceForSpace;

  @override
  void initState() {
    super.initState();
    _selected = {};
    widget.initialSelected.forEach((space, subs) {
      _selected[space] = Set.from(subs);
      if (subs.isNotEmpty) {
        _expandedSpaces.add(space);
      }
    });

    _allSpaces = Map.from(widget.spacesWithCounts);
    _allSubspaces = {};
    widget.subspacesWithCounts.forEach((k, v) {
      _allSubspaces[k] = Map.from(v);
    });

    // Ensure all initially selected spaces and sub-spaces exist in the options maps
    for (final entry in _selected.entries) {
      _allSpaces.putIfAbsent(entry.key, () => 0);
      _allSubspaces.putIfAbsent(entry.key, () => {});
      for (final sub in entry.value) {
        _allSubspaces[entry.key]!.putIfAbsent(sub, () => 0);
      }
    }
  }

  @override
  void dispose() {
    _searchController.dispose();
    _newSubspaceController.dispose();
    super.dispose();
  }

  void _addNewSpace(String rawName) {
    final name = rawName.trim().toLowerCase();
    if (name.isEmpty) return;

    setState(() {
      _allSpaces.putIfAbsent(name, () => 0);
      _allSubspaces.putIfAbsent(name, () => {});
      if (widget.isSingleSelect) {
        _selected.clear();
      }
      _selected.putIfAbsent(name, () => {});
      _expandedSpaces.add(name);
      _searchController.clear();
    });
  }

  void _addNewSubspace(String spaceName) {
    final subName = _newSubspaceController.text.trim().toLowerCase();
    if (subName.isEmpty) return;

    setState(() {
      _allSubspaces.putIfAbsent(spaceName, () => {});
      _allSubspaces[spaceName]!.putIfAbsent(subName, () => 0);
      if (widget.isSingleSelect) {
        _selected.clear();
      }
      _selected.putIfAbsent(spaceName, () => {});
      _selected[spaceName]!.add(subName);
      _newSubspaceController.clear();
      _addingSubspaceForSpace = null;
    });
  }

  Map<String, List<String>> _buildResultMap() {
    final Map<String, List<String>> res = {};
    for (final entry in _selected.entries) {
      res[entry.key] = entry.value.toList()..sort();
    }
    return res;
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _searchController.text.toLowerCase().trim();

    // Filter spaces based on search query
    final filteredSpaces = _allSpaces.keys.where((space) {
      if (query.isEmpty) return true;
      if (space.toLowerCase().contains(query)) return true;
      final subs = _allSubspaces[space]?.keys ?? [];
      return subs.any((s) => s.toLowerCase().contains(query));
    }).toList()
      ..sort((a, b) => a.compareTo(b));

    final isExactSpaceMatch = _allSpaces.keys.any((s) => s.toLowerCase() == query);

    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      minChildSize: 0.5,
      maxChildSize: 0.95,
      expand: false,
      builder: (ctx, scrollController) {
        return Container(
          decoration: BoxDecoration(
            color: theme.scaffoldBackgroundColor,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(20)),
          ),
          child: Column(
            children: [
              // Header
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                    ),
                  ),
                ),
                child: Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        color: Colors.deepPurpleAccent.withValues(alpha: 0.15),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: const Icon(Icons.rocket_launch, color: Colors.deepPurpleAccent, size: 22),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Spaces & Sub-spaces',
                            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          Text(
                            'Select hierarchical spaces to categorize this task',
                            style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),

              // Search Bar & Add Space Input
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
                child: TextField(
                  controller: _searchController,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Search or type new space (e.g. work, personal)...',
                    prefixIcon: const Icon(Icons.search, size: 20),
                    suffixIcon: _searchController.text.isNotEmpty
                        ? IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () {
                              _searchController.clear();
                              setState(() {});
                            },
                          )
                        : null,
                    isDense: true,
                    contentPadding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(10)),
                  ),
                ),
              ),

              // Create New Space Quick Card
              if (query.isNotEmpty && !isExactSpaceMatch)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(8),
                    onTap: () => _addNewSpace(query),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: Colors.deepPurpleAccent.withValues(alpha: 0.08),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: Colors.deepPurpleAccent.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.add_circle_outline, color: Colors.deepPurpleAccent, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Create new space "$query"',
                              style: const TextStyle(
                                color: Colors.deepPurple,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          const Icon(Icons.arrow_forward_ios, size: 12, color: Colors.deepPurpleAccent),
                        ],
                      ),
                    ),
                  ),
                ),

              // Active Selection Badges Strip
              if (_selected.isNotEmpty) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  color: Colors.deepPurple.withValues(alpha: 0.04),
                  child: SingleChildScrollView(
                    scrollDirection: Axis.horizontal,
                    child: Row(
                      children: _selected.entries.map((entry) {
                        final space = entry.key;
                        final subs = entry.value;
                        final label = subs.isEmpty ? space : '$space › ${subs.join(', ')}';
                        return Padding(
                          padding: const EdgeInsets.only(right: 6),
                          child: Chip(
                            avatar: const Icon(Icons.rocket_launch, size: 12, color: Colors.deepPurpleAccent),
                            visualDensity: VisualDensity.compact,
                            label: Text(label, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: Colors.deepPurple)),
                            backgroundColor: Colors.deepPurple.withValues(alpha: 0.12),
                            deleteIcon: const Icon(Icons.close, size: 14),
                            onDeleted: () {
                              setState(() {
                                _selected.remove(space);
                              });
                            },
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ),
              ],

              // Spaces & Sub-spaces Tree List
              Expanded(
                child: filteredSpaces.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(Icons.rocket_launch_outlined, size: 48, color: theme.disabledColor),
                            const SizedBox(height: 12),
                            Text(
                              query.isEmpty ? 'No spaces available yet' : 'No space matching "$query"',
                              style: TextStyle(color: theme.hintColor),
                            ),
                            if (query.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              ElevatedButton.icon(
                                icon: const Icon(Icons.add, size: 16),
                                label: Text('Create space "$query"'),
                                onPressed: () => _addNewSpace(query),
                              ),
                            ],
                          ],
                        ),
                      )
                    : ListView.builder(
                        controller: scrollController,
                        itemCount: filteredSpaces.length,
                        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                        itemBuilder: (ctx, idx) {
                          final spaceName = filteredSpaces[idx];
                          final taskCount = _allSpaces[spaceName] ?? 0;
                          final isSpaceSelected = _selected.containsKey(spaceName);
                          final selectedSubs = _selected[spaceName] ?? {};
                          final allSubsMap = _allSubspaces[spaceName] ?? {};
                          final allSubs = allSubsMap.keys.toList()..sort();
                          final isExpanded = _expandedSpaces.contains(spaceName) ||
                              (query.isNotEmpty && allSubs.any((s) => s.toLowerCase().contains(query)));

                          return Card(
                            elevation: 0,
                            margin: const EdgeInsets.symmetric(vertical: 4),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(10),
                              side: BorderSide(
                                color: isSpaceSelected
                                    ? Colors.deepPurpleAccent.withValues(alpha: 0.5)
                                    : theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                                width: isSpaceSelected ? 1.5 : 1,
                              ),
                            ),
                            color: isSpaceSelected
                                ? Colors.deepPurpleAccent.withValues(alpha: 0.03)
                                : theme.colorScheme.surface,
                            child: Column(
                              children: [
                                // Parent Space ListTile
                                ListTile(
                                  dense: true,
                                  contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 0),
                                  leading: Checkbox(
                                    value: isSpaceSelected,
                                    activeColor: Colors.deepPurpleAccent,
                                    onChanged: (checked) {
                                      setState(() {
                                        if (checked == true) {
                                          if (widget.isSingleSelect) {
                                            _selected.clear();
                                          }
                                          _selected.putIfAbsent(spaceName, () => {});
                                          _expandedSpaces.add(spaceName);
                                        } else {
                                          _selected.remove(spaceName);
                                        }
                                      });
                                    },
                                  ),
                                  title: Row(
                                    children: [
                                      const Icon(Icons.rocket_launch, size: 16, color: Colors.deepPurpleAccent),
                                      const SizedBox(width: 8),
                                      Expanded(
                                        child: Text(
                                          spaceName,
                                          style: TextStyle(
                                            fontWeight: isSpaceSelected ? FontWeight.bold : FontWeight.w500,
                                            fontSize: 14,
                                            color: isSpaceSelected ? Colors.deepPurple : null,
                                          ),
                                        ),
                                      ),
                                    ],
                                  ),
                                  trailing: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      if (taskCount > 0)
                                        Container(
                                          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                          decoration: BoxDecoration(
                                            color: theme.colorScheme.surfaceContainerHighest,
                                            borderRadius: BorderRadius.circular(8),
                                          ),
                                          child: Text(
                                            '$taskCount tasks',
                                            style: TextStyle(fontSize: 10, color: theme.hintColor),
                                          ),
                                        ),
                                      const SizedBox(width: 4),
                                      IconButton(
                                        icon: Icon(
                                          isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                                          size: 20,
                                          color: theme.hintColor,
                                        ),
                                        tooltip: isExpanded ? 'Collapse sub-spaces' : 'Expand sub-spaces',
                                        onPressed: () {
                                          setState(() {
                                            if (isExpanded) {
                                              _expandedSpaces.remove(spaceName);
                                            } else {
                                              _expandedSpaces.add(spaceName);
                                            }
                                          });
                                        },
                                      ),
                                    ],
                                  ),
                                  onTap: () {
                                    setState(() {
                                      if (isSpaceSelected) {
                                        _selected.remove(spaceName);
                                      } else {
                                        if (widget.isSingleSelect) {
                                          _selected.clear();
                                        }
                                        _selected.putIfAbsent(spaceName, () => {});
                                        _expandedSpaces.add(spaceName);
                                      }
                                    });
                                  },
                                ),

                                // Expanded Sub-spaces Section
                                if (isExpanded) ...[
                                  Container(
                                    padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
                                    child: Column(
                                      crossAxisAlignment: CrossAxisAlignment.start,
                                      children: [
                                        const Divider(height: 1),
                                        const SizedBox(height: 8),
                                        if (allSubs.isEmpty && _addingSubspaceForSpace != spaceName)
                                          Padding(
                                            padding: const EdgeInsets.symmetric(vertical: 4),
                                            child: Text(
                                              'No sub-spaces under "$spaceName" yet.',
                                              style: TextStyle(fontSize: 11, color: theme.hintColor, fontStyle: FontStyle.italic),
                                            ),
                                          )
                                        else
                                          Wrap(
                                            spacing: 6,
                                            runSpacing: 6,
                                            children: allSubs.map((sub) {
                                              final isSubSelected = selectedSubs.contains(sub);
                                              final subCount = allSubsMap[sub] ?? 0;
                                              return FilterChip(
                                                selected: isSubSelected,
                                                showCheckmark: true,
                                                checkmarkColor: Colors.deepPurple,
                                                selectedColor: Colors.deepPurpleAccent.withValues(alpha: 0.15),
                                                backgroundColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
                                                label: Text(
                                                  subCount > 0 ? '$sub ($subCount)' : sub,
                                                  style: TextStyle(
                                                    fontSize: 12,
                                                    fontWeight: isSubSelected ? FontWeight.bold : FontWeight.normal,
                                                    color: isSubSelected ? Colors.deepPurple : null,
                                                  ),
                                                ),
                                                onSelected: (checked) {
                                                  setState(() {
                                                    if (widget.isSingleSelect) {
                                                      if (checked) {
                                                        _selected.clear();
                                                        _selected[spaceName] = {sub};
                                                      } else {
                                                        _selected.remove(spaceName);
                                                      }
                                                    } else {
                                                      _selected.putIfAbsent(spaceName, () => {});
                                                      if (checked) {
                                                        _selected[spaceName]!.add(sub);
                                                      } else {
                                                        _selected[spaceName]!.remove(sub);
                                                      }
                                                    }
                                                  });
                                                },
                                              );
                                            }).toList(),
                                          ),

                                        const SizedBox(height: 6),

                                        // Inline Sub-space Creator
                                        if (_addingSubspaceForSpace == spaceName) ...[
                                          Row(
                                            children: [
                                              Expanded(
                                                child: TextField(
                                                  controller: _newSubspaceController,
                                                  autofocus: true,
                                                  decoration: InputDecoration(
                                                    hintText: 'New sub-space name under $spaceName...',
                                                    isDense: true,
                                                    contentPadding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                                                    border: OutlineInputBorder(borderRadius: BorderRadius.circular(6)),
                                                  ),
                                                  onSubmitted: (_) => _addNewSubspace(spaceName),
                                                ),
                                              ),
                                              const SizedBox(width: 6),
                                              IconButton.filledTonal(
                                                icon: const Icon(Icons.check, size: 16),
                                                onPressed: () => _addNewSubspace(spaceName),
                                              ),
                                              IconButton(
                                                icon: const Icon(Icons.close, size: 16),
                                                onPressed: () {
                                                  setState(() {
                                                    _addingSubspaceForSpace = null;
                                                    _newSubspaceController.clear();
                                                  });
                                                },
                                              ),
                                            ],
                                          ),
                                        ] else ...[
                                          ActionChip(
                                            avatar: const Icon(Icons.add, size: 14, color: Colors.deepPurpleAccent),
                                            label: Text('Add sub-space under $spaceName', style: const TextStyle(fontSize: 11, color: Colors.deepPurpleAccent)),
                                            visualDensity: VisualDensity.compact,
                                            padding: const EdgeInsets.symmetric(horizontal: 4),
                                            onPressed: () {
                                              setState(() {
                                                _addingSubspaceForSpace = spaceName;
                                                _newSubspaceController.clear();
                                              });
                                            },
                                          ),
                                        ],
                                      ],
                                    ),
                                  ),
                                ],
                              ],
                            ),
                          );
                        },
                      ),
              ),

              // Footer Actions
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  border: Border(
                    top: BorderSide(
                      color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                    ),
                  ),
                ),
                child: Row(
                  children: [
                    if (_selected.isNotEmpty)
                      TextButton(
                        onPressed: () => setState(() => _selected.clear()),
                        child: const Text('Clear All', style: TextStyle(color: Colors.redAccent)),
                      ),
                    const Spacer(),
                    OutlinedButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Cancel'),
                    ),
                    const SizedBox(width: 8),
                    ElevatedButton.icon(
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.deepPurpleAccent,
                        foregroundColor: Colors.white,
                      ),
                      icon: const Icon(Icons.done),
                      label: Text(widget.isSingleSelect ? 'Apply Selection' : 'Apply Spaces (${_selected.length})'),
                      onPressed: () {
                        widget.onSelectionConfirmed(_buildResultMap());
                      },
                    ),
                  ],
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
