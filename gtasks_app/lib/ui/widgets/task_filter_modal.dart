import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/task_provider.dart';
import 'searchable_multiselect_modal.dart';

class TaskFilterModal extends StatefulWidget {
  const TaskFilterModal({super.key});

  @override
  State<TaskFilterModal> createState() => _TaskFilterModalState();
}

class _TaskFilterModalState extends State<TaskFilterModal> {
  late String _status;
  String? _selectedPriority;
  late Set<String> _selectedLists;
  late Set<String> _selectedTags;
  late Set<String> _hiddenLists;
  late Set<String> _hiddenTags;
  late bool _hideRecurring;
  late String _sortField;
  late bool _sortAscending;
  DateTimeRange? _dateRange;
  late String _dateField;

  @override
  void initState() {
    super.initState();
    final p = context.read<TaskProvider>();
    _status = p.statusFilter;
    _selectedPriority = p.selectedPriority;
    _selectedLists = Set.from(p.selectedLists);
    _selectedTags = Set.from(p.selectedTags);
    _hiddenLists = Set.from(p.hiddenLists);
    _hiddenTags = Set.from(p.hiddenTags);
    _hideRecurring = p.hideRecurring;
    _sortField = p.sortField;
    _sortAscending = p.sortAscending;
    _dateRange = p.dateRange;
    _dateField = p.dateField;
  }

  Widget _buildMultiSelectCard({
    required BuildContext context,
    required String title,
    required String subtitle,
    required IconData icon,
    required Set<String> selectedItems,
    required Map<String, int> optionsWithCounts,
    required bool isExclusion,
    required bool isTag,
    required ValueChanged<Set<String>> onSelectionChanged,
  }) {
    final theme = Theme.of(context);
    final count = selectedItems.length;

    return Container(
      decoration: BoxDecoration(
        border: Border.all(
          color: count > 0
              ? (isExclusion ? Colors.redAccent.withValues(alpha: 0.5) : theme.colorScheme.primary.withValues(alpha: 0.5))
              : theme.colorScheme.outlineVariant,
        ),
        borderRadius: BorderRadius.circular(10),
        color: count > 0
            ? (isExclusion ? Colors.red.withValues(alpha: 0.04) : theme.colorScheme.primary.withValues(alpha: 0.04))
            : null,
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(10),
          onTap: () async {
            final result = await SearchableMultiSelectModal.show(
              context: context,
              title: title,
              subtitle: subtitle,
              icon: icon,
              optionsWithCounts: optionsWithCounts,
              initialSelected: selectedItems,
              isExclusion: isExclusion,
              isTag: isTag,
            );
            if (result != null) {
              onSelectionChanged(result);
            }
          },
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(
                      icon,
                      size: 18,
                      color: count > 0
                          ? (isExclusion ? Colors.redAccent : theme.colorScheme.primary)
                          : theme.hintColor,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        title,
                        style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                      ),
                    ),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                      decoration: BoxDecoration(
                        color: count > 0
                            ? (isExclusion ? Colors.red : theme.colorScheme.primary)
                            : theme.colorScheme.surfaceContainerHighest,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(
                        count == 0 ? 'All' : '$count selected',
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: count > 0 ? Colors.white : theme.colorScheme.onSurfaceVariant,
                        ),
                      ),
                    ),
                    const SizedBox(width: 4),
                    const Icon(Icons.arrow_drop_down, size: 20),
                  ],
                ),
                if (selectedItems.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 6,
                    runSpacing: 4,
                    children: selectedItems.take(5).map((item) {
                      return Chip(
                        visualDensity: VisualDensity.compact,
                        padding: EdgeInsets.zero,
                        labelPadding: const EdgeInsets.symmetric(horizontal: 6),
                        avatar: isTag
                            ? const Text('#', style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.teal))
                            : null,
                        label: Text(
                          item,
                          style: TextStyle(
                            fontSize: 11,
                            color: isExclusion ? Colors.red : null,
                            decoration: isExclusion ? TextDecoration.lineThrough : null,
                          ),
                        ),
                        deleteIcon: const Icon(Icons.close, size: 12),
                        onDeleted: () {
                          setState(() {
                            selectedItems.remove(item);
                          });
                        },
                      );
                    }).toList()
                      ..addAll(
                        selectedItems.length > 5
                            ? [
                                Chip(
                                  visualDensity: VisualDensity.compact,
                                  label: Text('+${selectedItems.length - 5} more', style: const TextStyle(fontSize: 11)),
                                )
                              ]
                            : [],
                      ),
                  ),
                ],
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final provider = context.watch<TaskProvider>();
    final theme = Theme.of(context);
    final listsWithCounts = provider.listsWithCounts;
    final tagsWithCounts = provider.tagsWithCounts;

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
                    const Icon(Icons.filter_list, color: Colors.blueAccent),
                    const SizedBox(width: 8),
                    Text('Filter & Sort Tasks', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                    const Spacer(),
                    TextButton(
                      onPressed: () {
                        setState(() {
                          _status = 'pending';
                          _selectedPriority = null;
                          _selectedLists.clear();
                          _selectedTags.clear();
                          _hiddenLists.clear();
                          _hiddenTags.clear();
                          _hideRecurring = false;
                          _sortField = 'modified_at';
                          _sortAscending = false;
                          _dateRange = null;
                          _dateField = 'modified_at';
                        });
                      },
                      child: const Text('Reset'),
                    ),
                    IconButton(
                      icon: const Icon(Icons.close),
                      onPressed: () => Navigator.pop(context),
                    ),
                  ],
                ),
              ),

              // Content
              Expanded(
                child: ListView(
                  controller: scrollController,
                  padding: const EdgeInsets.all(16),
                  children: [
                    // Status Filter
                    const Text('Task Status', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    SegmentedButton<String>(
                      segments: const [
                        ButtonSegment(value: 'pending', label: Text('Pending')),
                        ButtonSegment(value: 'completed', label: Text('Completed')),
                        ButtonSegment(value: 'all', label: Text('All Tasks')),
                      ],
                      selected: {_status},
                      onSelectionChanged: (set) => setState(() => _status = set.first),
                    ),

                    const SizedBox(height: 16),

                    // Priority Filter
                    const Text('Priority Level', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      children: [
                        ChoiceChip(
                          label: const Text('All Priorities'),
                          selected: _selectedPriority == null,
                          onSelected: (_) => setState(() => _selectedPriority = null),
                        ),
                        ChoiceChip(
                          label: const Text('Critical'),
                          avatar: const Icon(Icons.warning_amber, size: 16, color: Colors.red),
                          selected: _selectedPriority == 'critical',
                          onSelected: (val) => setState(() => _selectedPriority = val ? 'critical' : null),
                        ),
                        ChoiceChip(
                          label: const Text('High'),
                          avatar: const Icon(Icons.bolt, size: 16, color: Colors.orange),
                          selected: _selectedPriority == 'high',
                          onSelected: (val) => setState(() => _selectedPriority = val ? 'high' : null),
                        ),
                        ChoiceChip(
                          label: const Text('Medium'),
                          avatar: const Icon(Icons.flag_outlined, size: 16, color: Colors.amber),
                          selected: _selectedPriority == 'medium',
                          onSelected: (val) => setState(() => _selectedPriority = val ? 'medium' : null),
                        ),
                        ChoiceChip(
                          label: const Text('Low'),
                          selected: _selectedPriority == 'low',
                          onSelected: (val) => setState(() => _selectedPriority = val ? 'low' : null),
                        ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // 1. Filter by Task List (Searchable Multi-Select)
                    _buildMultiSelectCard(
                      context: context,
                      title: 'Filter by Task List',
                      subtitle: 'Select one or more lists to include',
                      icon: Icons.folder,
                      selectedItems: _selectedLists,
                      optionsWithCounts: listsWithCounts,
                      isExclusion: false,
                      isTag: false,
                      onSelectionChanged: (res) => setState(() => _selectedLists = res),
                    ),

                    const SizedBox(height: 12),

                    // 2. Filter by Tags (Searchable Multi-Select)
                    _buildMultiSelectCard(
                      context: context,
                      title: 'Filter by Tags',
                      subtitle: 'Select tags to include in tasks view',
                      icon: Icons.tag,
                      selectedItems: _selectedTags,
                      optionsWithCounts: tagsWithCounts,
                      isExclusion: false,
                      isTag: true,
                      onSelectionChanged: (res) => setState(() => _selectedTags = res),
                    ),

                    const SizedBox(height: 16),

                    // Hide Recurring Tasks Toggle
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                      decoration: BoxDecoration(
                        border: Border.all(color: theme.colorScheme.outlineVariant),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: const Text('Hide Recurring Tasks', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                        subtitle: const Text('Exclude repeating routines & rent reminders', style: TextStyle(fontSize: 11)),
                        value: _hideRecurring,
                        onChanged: (val) => setState(() => _hideRecurring = val),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // 3. Hide Specific Lists (Searchable Multi-Select Exclude)
                    _buildMultiSelectCard(
                      context: context,
                      title: 'Hide Specific Lists (Exclude)',
                      subtitle: 'Select lists to exclude from view',
                      icon: Icons.visibility_off,
                      selectedItems: _hiddenLists,
                      optionsWithCounts: listsWithCounts,
                      isExclusion: true,
                      isTag: false,
                      onSelectionChanged: (res) => setState(() => _hiddenLists = res),
                    ),

                    const SizedBox(height: 12),

                    // 4. Hide Specific Tags (Searchable Multi-Select Exclude)
                    _buildMultiSelectCard(
                      context: context,
                      title: 'Hide Specific Tags (Exclude)',
                      subtitle: 'Select tags to exclude from view',
                      icon: Icons.label_off_outlined,
                      selectedItems: _hiddenTags,
                      optionsWithCounts: tagsWithCounts,
                      isExclusion: true,
                      isTag: true,
                      onSelectionChanged: (res) => setState(() => _hiddenTags = res),
                    ),

                    const SizedBox(height: 16),

                    // Date Field & Date Range
                    const Text('Date Window Filter', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: _dateField,
                            isDense: true,
                            decoration: const InputDecoration(
                              labelText: 'Date Type',
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                            ),
                            items: const [
                              DropdownMenuItem(value: 'modified_at', child: Text('Modified Date')),
                              DropdownMenuItem(value: 'created_at', child: Text('Created Date')),
                              DropdownMenuItem(value: 'due', child: Text('Due Date')),
                            ],
                            onChanged: (val) {
                              if (val != null) setState(() => _dateField = val);
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        Expanded(
                          child: OutlinedButton.icon(
                            icon: const Icon(Icons.date_range, size: 16),
                            label: Text(
                              _dateRange == null
                                  ? 'Pick Range'
                                  : '${_dateRange!.start.month}/${_dateRange!.start.day} - ${_dateRange!.end.month}/${_dateRange!.end.day}',
                              style: const TextStyle(fontSize: 12),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                            ),
                            onPressed: () async {
                              final picked = await showDateRangePicker(
                                context: context,
                                firstDate: DateTime(2020),
                                lastDate: DateTime.now().add(const Duration(days: 365)),
                                initialDateRange: _dateRange,
                              );
                              if (picked != null) {
                                setState(() => _dateRange = picked);
                              }
                            },
                          ),
                        ),
                        if (_dateRange != null)
                          IconButton(
                            icon: const Icon(Icons.clear, size: 18),
                            onPressed: () => setState(() => _dateRange = null),
                          ),
                      ],
                    ),

                    const SizedBox(height: 16),

                    // Sort By
                    const Text('Sort By', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
                    const SizedBox(height: 6),
                    Row(
                      children: [
                        Expanded(
                          child: DropdownButtonFormField<String>(
                            value: _sortField,
                            isDense: true,
                            decoration: const InputDecoration(
                              border: OutlineInputBorder(),
                              contentPadding: EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                            ),
                            items: const [
                              DropdownMenuItem(value: 'modified_at', child: Text('Modified Date')),
                              DropdownMenuItem(value: 'created_at', child: Text('Created Date')),
                              DropdownMenuItem(value: 'due', child: Text('Due Date')),
                              DropdownMenuItem(value: 'priority', child: Text('Priority')),
                              DropdownMenuItem(value: 'title', child: Text('Title (A-Z)')),
                            ],
                            onChanged: (val) {
                              if (val != null) setState(() => _sortField = val);
                            },
                          ),
                        ),
                        const SizedBox(width: 8),
                        IconButton.outlined(
                          icon: Icon(_sortAscending ? Icons.arrow_upward : Icons.arrow_downward),
                          tooltip: _sortAscending ? 'Ascending' : 'Descending',
                          onPressed: () => setState(() => _sortAscending = !_sortAscending),
                        ),
                      ],
                    ),
                  ],
                ),
              ),

              // Footer Action
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                decoration: BoxDecoration(
                  border: Border(
                    top: BorderSide(
                      color: theme.colorScheme.outlineVariant.withValues(alpha: 0.4),
                    ),
                  ),
                ),
                child: SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    icon: const Icon(Icons.done),
                    label: const Text('Apply Filters'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    onPressed: () {
                      provider.setStatusFilter(_status);
                      provider.setSelectedLists(_selectedLists);
                      provider.setSelectedTags(_selectedTags);
                      provider.setPriorityFilter(_selectedPriority);
                      provider.setHiddenLists(_hiddenLists);
                      provider.setHiddenTags(_hiddenTags);
                      provider.setHideRecurring(_hideRecurring);
                      provider.setDateFilter(_dateField, _dateRange);
                      provider.setSort(_sortField, _sortAscending);
                      Navigator.pop(context);
                    },
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
