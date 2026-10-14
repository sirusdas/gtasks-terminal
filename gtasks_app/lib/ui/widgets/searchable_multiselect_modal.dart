import 'package:flutter/material.dart';

class SearchableMultiSelectModal extends StatefulWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Map<String, int> optionsWithCounts;
  final Set<String> initialSelected;
  final bool isExclusion; // If true, items represent hidden/excluded (red tint, strike)
  final bool isTag; // If true, prefix with '#'
  final ValueChanged<Set<String>> onSelectionChanged;

  const SearchableMultiSelectModal({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.optionsWithCounts,
    required this.initialSelected,
    this.isExclusion = false,
    this.isTag = false,
    required this.onSelectionChanged,
  });

  static Future<Set<String>?> show({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required Map<String, int> optionsWithCounts,
    required Set<String> initialSelected,
    bool isExclusion = false,
    bool isTag = false,
  }) {
    return showModalBottomSheet<Set<String>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => SearchableMultiSelectModal(
        title: title,
        subtitle: subtitle,
        icon: icon,
        optionsWithCounts: optionsWithCounts,
        initialSelected: initialSelected,
        isExclusion: isExclusion,
        isTag: isTag,
        onSelectionChanged: (selected) => Navigator.pop(ctx, selected),
      ),
    );
  }

  @override
  State<SearchableMultiSelectModal> createState() => _SearchableMultiSelectModalState();
}

class _SearchableMultiSelectModalState extends State<SearchableMultiSelectModal> {
  late Set<String> _selected;
  late final List<String> _allOptions;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _selected = Set.from(widget.initialSelected);
    _allOptions = widget.optionsWithCounts.keys.toList()
      ..sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _searchController.text.toLowerCase().trim();

    final filteredOptions = _allOptions.where((opt) {
      if (query.isEmpty) return true;
      return opt.toLowerCase().contains(query);
    }).toList();

    return DraggableScrollableSheet(
      initialChildSize: 0.85,
      minChildSize: 0.45,
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
                    Icon(widget.icon, color: widget.isExclusion ? Colors.redAccent : theme.colorScheme.primary),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            widget.title,
                            style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
                          ),
                          Text(
                            widget.subtitle,
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

              // Search Bar & Action Buttons (Select All / Clear)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
                child: TextField(
                  controller: _searchController,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Search ${widget.title.toLowerCase()}...',
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

              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Row(
                  children: [
                    Text(
                      '${_selected.length} of ${_allOptions.length} selected',
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: _selected.isNotEmpty
                            ? (widget.isExclusion ? Colors.redAccent : theme.colorScheme.primary)
                            : theme.hintColor,
                      ),
                    ),
                    const Spacer(),
                    TextButton(
                      style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                      onPressed: filteredOptions.isEmpty
                          ? null
                          : () {
                              setState(() {
                                _selected.addAll(filteredOptions);
                              });
                            },
                      child: const Text('Select All', style: TextStyle(fontSize: 12)),
                    ),
                    const SizedBox(width: 4),
                    TextButton(
                      style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                      onPressed: _selected.isEmpty
                          ? null
                          : () {
                              setState(() {
                                _selected.clear();
                              });
                            },
                      child: const Text('Clear', style: TextStyle(fontSize: 12)),
                    ),
                  ],
                ),
              ),

              const Divider(height: 1),

              // Options List
              Expanded(
                child: filteredOptions.isEmpty
                    ? Center(
                        child: Text(
                          query.isEmpty ? 'No options available' : 'No matches for "$query"',
                          style: TextStyle(color: theme.hintColor, fontSize: 13),
                        ),
                      )
                    : ListView.builder(
                        controller: scrollController,
                        itemCount: filteredOptions.length,
                        itemBuilder: (context, index) {
                          final option = filteredOptions[index];
                          final count = widget.optionsWithCounts[option] ?? 0;
                          final isChecked = _selected.contains(option);

                          return CheckboxListTile(
                            dense: true,
                            value: isChecked,
                            activeColor: widget.isExclusion ? Colors.red : theme.colorScheme.primary,
                            title: Row(
                              children: [
                                if (widget.isTag)
                                  const Text('#', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.teal))
                                else if (widget.isExclusion)
                                  const Icon(Icons.visibility_off, size: 16, color: Colors.redAccent)
                                else
                                  const Icon(Icons.folder_outlined, size: 16, color: Colors.blueAccent),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    option,
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: isChecked ? FontWeight.bold : FontWeight.normal,
                                      decoration: widget.isExclusion && isChecked ? TextDecoration.lineThrough : null,
                                      color: widget.isExclusion && isChecked ? Colors.red : null,
                                    ),
                                    maxLines: 1,
                                    overflow: TextOverflow.ellipsis,
                                  ),
                                ),
                                Container(
                                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                  decoration: BoxDecoration(
                                    color: isChecked
                                        ? (widget.isExclusion
                                            ? Colors.red.withValues(alpha: 0.15)
                                            : theme.colorScheme.primary.withValues(alpha: 0.15))
                                        : theme.colorScheme.surfaceContainerHighest,
                                    borderRadius: BorderRadius.circular(10),
                                  ),
                                  child: Text(
                                    '$count',
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.bold,
                                      color: isChecked
                                          ? (widget.isExclusion ? Colors.red : theme.colorScheme.primary)
                                          : theme.colorScheme.onSurfaceVariant,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            onChanged: (bool? value) {
                              setState(() {
                                if (value == true) {
                                  _selected.add(option);
                                } else {
                                  _selected.remove(option);
                                }
                              });
                            },
                          );
                        },
                      ),
              ),

              // Bottom Apply Button
              SafeArea(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.check),
                      label: Text('Apply Selection (${_selected.length})'),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: widget.isExclusion && _selected.isNotEmpty
                            ? Colors.red.shade700
                            : theme.colorScheme.primary,
                        foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      ),
                      onPressed: () {
                        widget.onSelectionChanged(_selected);
                      },
                    ),
                  ),
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
