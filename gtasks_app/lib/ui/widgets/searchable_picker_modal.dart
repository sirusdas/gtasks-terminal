import 'package:flutter/material.dart';

class SearchablePickerModal extends StatefulWidget {
  final String title;
  final String subtitle;
  final IconData icon;
  final Map<String, int> optionsWithCounts;
  final Set<String> initialSelected;
  final bool isMultiSelect;
  final bool isTag;
  final ValueChanged<Set<String>> onSelectionConfirmed;

  const SearchablePickerModal({
    super.key,
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.optionsWithCounts,
    required this.initialSelected,
    this.isMultiSelect = true,
    this.isTag = false,
    required this.onSelectionConfirmed,
  });

  static Future<Set<String>?> show({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required Map<String, int> optionsWithCounts,
    required Set<String> initialSelected,
    bool isMultiSelect = true,
    bool isTag = false,
  }) {
    return showModalBottomSheet<Set<String>>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => SearchablePickerModal(
        title: title,
        subtitle: subtitle,
        icon: icon,
        optionsWithCounts: optionsWithCounts,
        initialSelected: initialSelected,
        isMultiSelect: isMultiSelect,
        isTag: isTag,
        onSelectionConfirmed: (selected) => Navigator.pop(ctx, selected),
      ),
    );
  }

  @override
  State<SearchablePickerModal> createState() => _SearchablePickerModalState();
}

class _SearchablePickerModalState extends State<SearchablePickerModal> {
  late Set<String> _selected;
  final TextEditingController _searchController = TextEditingController();
  final TextEditingController _addNewController = TextEditingController();
  bool _isAddingCustom = false;

  @override
  void initState() {
    super.initState();
    _selected = Set.from(widget.initialSelected);
  }

  @override
  void dispose() {
    _searchController.dispose();
    _addNewController.dispose();
    super.dispose();
  }

  void _addNewItem() {
    final newItem = _addNewController.text.trim();
    if (newItem.isEmpty) return;

    setState(() {
      if (widget.isMultiSelect) {
        _selected.add(newItem);
      } else {
        _selected = {newItem};
      }
      _addNewController.clear();
      _isAddingCustom = false;
    });

    if (!widget.isMultiSelect) {
      widget.onSelectionConfirmed(_selected);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final query = _searchController.text.toLowerCase().trim();

    // Ensure all currently selected items are part of the displayed options
    final allOptionsMap = Map<String, int>.from(widget.optionsWithCounts);
    for (final sel in _selected) {
      allOptionsMap.putIfAbsent(sel, () => 0);
    }

    final allOptions = allOptionsMap.keys.toList()
      ..sort((a, b) => a.toLowerCase().compareTo(b.toLowerCase()));

    final filteredOptions = allOptions.where((opt) {
      if (query.isEmpty) return true;
      return opt.toLowerCase().contains(query);
    }).toList();

    final isExactMatch = allOptions.any((opt) => opt.toLowerCase() == query);

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
                    Icon(widget.icon, color: theme.colorScheme.primary),
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

              // Search Input
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 6),
                child: TextField(
                  controller: _searchController,
                  autofocus: false,
                  onChanged: (_) => setState(() {}),
                  decoration: InputDecoration(
                    hintText: 'Search or filter ${widget.title.toLowerCase()}...',
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

              // Add New Quick Bar (when query has no exact match or user clicks + Add)
              if (query.isNotEmpty && !isExactMatch)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(8),
                    onTap: () {
                      _addNewController.text = _searchController.text.trim();
                      _addNewItem();
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: theme.colorScheme.primary.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          Icon(Icons.add_circle_outline, color: theme.colorScheme.primary, size: 18),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              'Add new "${_searchController.text.trim()}"',
                              style: TextStyle(
                                color: theme.colorScheme.primary,
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                              ),
                            ),
                          ),
                          const Text('Tap to add', style: TextStyle(fontSize: 11, color: Colors.grey)),
                        ],
                      ),
                    ),
                  ),
                ),

              // Custom Add Input Field (if user clicked "+ Custom")
              if (_isAddingCustom)
                Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  child: Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _addNewController,
                          autofocus: true,
                          decoration: InputDecoration(
                            hintText: widget.isTag ? 'New tag name...' : 'New list name...',
                            isDense: true,
                            contentPadding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
                            border: const OutlineInputBorder(),
                          ),
                          onSubmitted: (_) => _addNewItem(),
                        ),
                      ),
                      const SizedBox(width: 6),
                      ElevatedButton(
                        style: ElevatedButton.styleFrom(visualDensity: VisualDensity.compact),
                        onPressed: _addNewItem,
                        child: const Text('Add'),
                      ),
                      IconButton(
                        icon: const Icon(Icons.close, size: 18),
                        onPressed: () => setState(() => _isAddingCustom = false),
                      ),
                    ],
                  ),
                ),

              // Info & Action Bar
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                child: Row(
                  children: [
                    Text(
                      widget.isMultiSelect
                          ? '${_selected.length} selected'
                          : (_selected.isEmpty ? 'None selected' : 'Selected: ${_selected.first}'),
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: _selected.isNotEmpty ? theme.colorScheme.primary : theme.hintColor,
                      ),
                    ),
                    const Spacer(),
                    if (!_isAddingCustom)
                      TextButton.icon(
                        style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                        icon: const Icon(Icons.add, size: 16),
                        label: Text(widget.isTag ? 'Add Tag' : 'Add List', style: const TextStyle(fontSize: 12)),
                        onPressed: () => setState(() => _isAddingCustom = true),
                      ),
                    if (widget.isMultiSelect && _selected.isNotEmpty) ...[
                      const SizedBox(width: 4),
                      TextButton(
                        style: TextButton.styleFrom(visualDensity: VisualDensity.compact),
                        onPressed: () => setState(() => _selected.clear()),
                        child: const Text('Clear', style: TextStyle(fontSize: 12)),
                      ),
                    ],
                  ],
                ),
              ),

              const Divider(height: 1),

              // Options List
              Expanded(
                child: filteredOptions.isEmpty
                    ? Center(
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              query.isEmpty ? 'No items available' : 'No matches for "$query"',
                              style: TextStyle(color: theme.hintColor, fontSize: 13),
                            ),
                            if (query.isNotEmpty) ...[
                              const SizedBox(height: 8),
                              ElevatedButton.icon(
                                icon: const Icon(Icons.add, size: 16),
                                label: Text('Add "$query"'),
                                onPressed: () {
                                  _addNewController.text = query;
                                  _addNewItem();
                                },
                              ),
                            ],
                          ],
                        ),
                      )
                    : ListView.builder(
                        controller: scrollController,
                        itemCount: filteredOptions.length,
                        itemBuilder: (context, index) {
                          final option = filteredOptions[index];
                          final count = allOptionsMap[option] ?? 0;
                          final isChecked = _selected.contains(option);

                          if (widget.isMultiSelect) {
                            return CheckboxListTile(
                              dense: true,
                              value: isChecked,
                              activeColor: theme.colorScheme.primary,
                              title: Row(
                                children: [
                                  if (widget.isTag)
                                    const Text('#', style: TextStyle(fontWeight: FontWeight.bold, color: Colors.teal))
                                  else
                                    const Icon(Icons.list_alt, size: 16, color: Colors.blueAccent),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      option,
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: isChecked ? FontWeight.bold : FontWeight.normal,
                                      ),
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                  ),
                                  if (count > 0)
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                      decoration: BoxDecoration(
                                        color: isChecked
                                            ? theme.colorScheme.primary.withValues(alpha: 0.15)
                                            : theme.colorScheme.surfaceContainerHighest,
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: Text(
                                        '$count',
                                        style: TextStyle(
                                          fontSize: 11,
                                          fontWeight: FontWeight.bold,
                                          color: isChecked ? theme.colorScheme.primary : theme.colorScheme.onSurfaceVariant,
                                        ),
                                      ),
                                    ),
                                ],
                              ),
                              onChanged: (bool? val) {
                                setState(() {
                                  if (val == true) {
                                    _selected.add(option);
                                  } else {
                                    _selected.remove(option);
                                  }
                                });
                              },
                            );
                          } else {
                            // Single Select (Radio tile style)
                            return ListTile(
                              dense: true,
                              leading: Icon(
                                isChecked ? Icons.radio_button_checked : Icons.radio_button_unchecked,
                                color: isChecked ? theme.colorScheme.primary : Colors.grey,
                                size: 20,
                              ),
                              title: Row(
                                children: [
                                  const Icon(Icons.list_alt, size: 16, color: Colors.blueAccent),
                                  const SizedBox(width: 8),
                                  Expanded(
                                    child: Text(
                                      option,
                                      style: TextStyle(
                                        fontSize: 13,
                                        fontWeight: isChecked ? FontWeight.bold : FontWeight.normal,
                                        color: isChecked ? theme.colorScheme.primary : null,
                                      ),
                                    ),
                                  ),
                                  if (count > 0)
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
                                      decoration: BoxDecoration(
                                        color: theme.colorScheme.surfaceContainerHighest,
                                        borderRadius: BorderRadius.circular(10),
                                      ),
                                      child: Text(
                                        '$count',
                                        style: TextStyle(fontSize: 11, color: theme.colorScheme.onSurfaceVariant),
                                      ),
                                    ),
                                ],
                              ),
                              onTap: () {
                                setState(() {
                                  _selected = {option};
                                });
                                widget.onSelectionConfirmed(_selected);
                              },
                            );
                          }
                        },
                      ),
              ),

              // Bottom Confirmation Button for Multi-Select
              if (widget.isMultiSelect)
                SafeArea(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: SizedBox(
                      width: double.infinity,
                      child: ElevatedButton.icon(
                        icon: const Icon(Icons.check),
                        label: Text('Done (${_selected.length} Selected)'),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: theme.colorScheme.primary,
                          foregroundColor: Colors.white,
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        ),
                        onPressed: () {
                          widget.onSelectionConfirmed(_selected);
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
