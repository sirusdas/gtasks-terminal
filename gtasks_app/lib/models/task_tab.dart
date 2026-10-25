// ignore_for_file: non_const_argument_for_const_parameter
import 'package:flutter/material.dart';
import 'task_item.dart';

class TaskTab {
  final String id;
  String title;
  int? iconCodePoint;
  int? colorValue;

  // Independent Filter State
  String? selectedAccount;
  Set<String> selectedAccounts;
  String statusFilter; // 'pending', 'completed', 'all'
  String? selectedSpace;
  String? selectedSubspace;
  String? selectedPriority;
  Set<String> selectedLists;
  Set<String> selectedTags;
  String searchQuery;
  String? dateField; // 'due' or 'completed'
  DateTimeRange? dateRange;
  bool hideRecurring;
  Set<String> hiddenLists;
  Set<String> hiddenTags;
  String sortField;
  bool sortAscending;
  String? viewMode; // optional override: 'detailed', 'compact', 'two_column', 'two_column_compact'
  String? mandalaGrouping;
  String? mandalaGeometry;
  String? mandalaTheme;

  TaskTab({
    required this.id,
    required this.title,
    this.iconCodePoint,
    this.colorValue,
    this.selectedAccount,
    Set<String>? selectedAccounts,
    this.statusFilter = 'pending',
    this.selectedSpace,
    this.selectedSubspace,
    this.selectedPriority,
    Set<String>? selectedLists,
    Set<String>? selectedTags,
    this.searchQuery = '',
    this.dateField,
    this.dateRange,
    this.hideRecurring = false,
    Set<String>? hiddenLists,
    Set<String>? hiddenTags,
    this.sortField = 'priority',
    this.sortAscending = true,
    this.viewMode,
    this.mandalaGrouping,
    this.mandalaGeometry,
    this.mandalaTheme,
  })  : selectedAccounts = selectedAccounts != null
            ? Set.from(selectedAccounts)
            : (selectedAccount != null && selectedAccount != 'all' ? {selectedAccount} : {}),
        selectedLists = selectedLists != null ? Set.from(selectedLists) : {},
        selectedTags = selectedTags != null ? Set.from(selectedTags) : {},
        hiddenLists = hiddenLists != null ? Set.from(hiddenLists) : {},
        hiddenTags = hiddenTags != null ? Set.from(hiddenTags) : {};

  Set<String> get effectiveAccounts {
    if (selectedAccounts.isNotEmpty) {
      return selectedAccounts;
    }
    if (selectedAccount != null && selectedAccount!.isNotEmpty && selectedAccount != 'all') {
      return {selectedAccount!};
    }
    return {};
  }

  IconData get icon {
    if (iconCodePoint != null) {
      return IconData(iconCodePoint!, fontFamily: 'MaterialIcons');
    }
    if (viewMode == 'mandala') return Icons.hub_outlined;
    if (selectedSpace != null) return Icons.rocket_launch_rounded;
    if (selectedPriority != null && (selectedPriority == 'critical' || selectedPriority == 'high')) {
      return Icons.local_fire_department_rounded;
    }
    if (dateRange != null) return Icons.today_rounded;
    if (selectedTags.isNotEmpty) return Icons.tag_rounded;
    if (selectedLists.isNotEmpty) return Icons.folder_rounded;
    if (statusFilter == 'completed') return Icons.check_circle_outline_rounded;
    return Icons.inbox_rounded;
  }

  Color? get accentColor => colorValue != null ? Color(colorValue!) : null;

  bool get hasActiveFilters {
    return selectedLists.isNotEmpty ||
        selectedTags.isNotEmpty ||
        selectedSpace != null ||
        selectedSubspace != null ||
        selectedPriority != null ||
        hiddenLists.isNotEmpty ||
        hiddenTags.isNotEmpty ||
        hideRecurring ||
        dateRange != null ||
        (selectedAccount != null && selectedAccount != 'all') ||
        selectedAccounts.isNotEmpty ||
        statusFilter != 'pending' ||
        searchQuery.isNotEmpty;
  }

  int get activeFilterCount {
    int count = 0;
    if (selectedLists.isNotEmpty) count += selectedLists.length;
    if (selectedTags.isNotEmpty) count += selectedTags.length;
    if (selectedSpace != null) count++;
    if (selectedSubspace != null) count++;
    if (selectedPriority != null) count++;
    if (hiddenLists.isNotEmpty) count += hiddenLists.length;
    if (hiddenTags.isNotEmpty) count += hiddenTags.length;
    if (hideRecurring) count++;
    if (dateRange != null) count++;
    if (statusFilter != 'pending') count++;
    if (effectiveAccounts.isNotEmpty) count += effectiveAccounts.length;
    if (searchQuery.isNotEmpty) count++;
    return count;
  }

  TaskTab copyWith({
    String? id,
    String? title,
    int? iconCodePoint,
    int? colorValue,
    String? selectedAccount,
    bool clearAccount = false,
    Set<String>? selectedAccounts,
    bool clearAccounts = false,
    String? statusFilter,
    String? selectedSpace,
    bool clearSpace = false,
    String? selectedSubspace,
    bool clearSubspace = false,
    String? selectedPriority,
    bool clearPriority = false,
    Set<String>? selectedLists,
    Set<String>? selectedTags,
    String? searchQuery,
    String? dateField,
    DateTimeRange? dateRange,
    bool clearDateRange = false,
    bool? hideRecurring,
    Set<String>? hiddenLists,
    Set<String>? hiddenTags,
    String? sortField,
    bool? sortAscending,
    String? viewMode,
    bool clearViewMode = false,
    String? mandalaGrouping,
    bool clearMandalaGrouping = false,
    String? mandalaGeometry,
    bool clearMandalaGeometry = false,
    String? mandalaTheme,
    bool clearMandalaTheme = false,
  }) {
    return TaskTab(
      id: id ?? this.id,
      title: title ?? this.title,
      iconCodePoint: iconCodePoint ?? this.iconCodePoint,
      colorValue: colorValue ?? this.colorValue,
      selectedAccount: clearAccount ? null : (selectedAccount ?? this.selectedAccount),
      selectedAccounts: clearAccounts ? {} : (selectedAccounts != null ? Set.from(selectedAccounts) : Set.from(this.selectedAccounts)),
      statusFilter: statusFilter ?? this.statusFilter,
      selectedSpace: clearSpace ? null : (selectedSpace ?? this.selectedSpace),
      selectedSubspace: (clearSpace || clearSubspace) ? null : (selectedSubspace ?? this.selectedSubspace),
      selectedPriority: clearPriority ? null : (selectedPriority ?? this.selectedPriority),
      selectedLists: selectedLists != null ? Set.from(selectedLists) : Set.from(this.selectedLists),
      selectedTags: selectedTags != null ? Set.from(selectedTags) : Set.from(this.selectedTags),
      searchQuery: searchQuery ?? this.searchQuery,
      dateField: dateField ?? this.dateField,
      dateRange: clearDateRange ? null : (dateRange ?? this.dateRange),
      hideRecurring: hideRecurring ?? this.hideRecurring,
      hiddenLists: hiddenLists != null ? Set.from(hiddenLists) : Set.from(this.hiddenLists),
      hiddenTags: hiddenTags != null ? Set.from(hiddenTags) : Set.from(this.hiddenTags),
      sortField: sortField ?? this.sortField,
      sortAscending: sortAscending ?? this.sortAscending,
      viewMode: clearViewMode ? null : (viewMode ?? this.viewMode),
      mandalaGrouping: clearMandalaGrouping ? null : (mandalaGrouping ?? this.mandalaGrouping),
      mandalaGeometry: clearMandalaGeometry ? null : (mandalaGeometry ?? this.mandalaGeometry),
      mandalaTheme: clearMandalaTheme ? null : (mandalaTheme ?? this.mandalaTheme),
    );
  }

  List<TaskItem> filterTasks(List<TaskItem> allTasks) {
    final now = DateTime.now();
    final todayStr = '${now.year}-${now.month.toString().padLeft(2, '0')}-${now.day.toString().padLeft(2, '0')}';
    final effAccs = effectiveAccounts;

    return allTasks.where((t) {
      if (effAccs.isNotEmpty && !effAccs.contains('all')) {
        if (!effAccs.contains(t.account)) return false;
      } else if (selectedAccount != null && selectedAccount != 'all' && t.account != selectedAccount) {
        return false;
      }
      if (statusFilter == 'pending' && t.isCompleted) return false;
      if (statusFilter == 'completed' && !t.isCompleted) return false;

      // Exclusions
      if (hiddenLists.isNotEmpty && t.listTitle != null && hiddenLists.contains(t.listTitle)) return false;
      if (hiddenTags.isNotEmpty && t.allTags.any((tag) => hiddenTags.contains(tag))) return false;
      if (hideRecurring && t.isRecurring) return false;

      if (selectedSpace != null) {
        if (!t.spaces.containsKey(selectedSpace)) return false;
        if (selectedSubspace != null && selectedSubspace!.isNotEmpty) {
          final subs = t.spaces[selectedSpace];
          if (subs == null || !subs.contains(selectedSubspace)) return false;
        }
      }

      if (selectedPriority != null) {
        final p = t.calculatedPriority.toLowerCase();
        if (selectedPriority == 'high' && p != 'critical' && p != 'high') return false;
        if (selectedPriority != 'high' && p != selectedPriority) return false;
      }

      if (selectedLists.isNotEmpty) {
        if (t.listTitle == null || !selectedLists.contains(t.listTitle)) return false;
      }

      if (selectedTags.isNotEmpty) {
        if (!t.allTags.any((tag) => selectedTags.contains(tag))) return false;
      }

      if (dateRange != null) {
        if (t.due == null || t.due!.isEmpty) return false;
        final duePart = t.due!.length >= 10 ? t.due!.substring(0, 10) : t.due!;
        if (dateField == 'due' && dateRange!.start.year == 2000) {
          // 'Today & Due' convention
          if (duePart.compareTo(todayStr) > 0) return false;
        } else {
          final dueDt = DateTime.tryParse(duePart);
          if (dueDt == null) return false;
          if (dueDt.isBefore(dateRange!.start) || dueDt.isAfter(dateRange!.end)) return false;
        }
      }

      if (searchQuery.isNotEmpty) {
        final q = searchQuery.toLowerCase();
        final inTitle = t.title.toLowerCase().contains(q);
        final inNotes = t.description.toLowerCase().contains(q);
        final inTags = t.allTags.any((tag) => tag.toLowerCase().contains(q));
        if (!inTitle && !inNotes && !inTags) return false;
      }

      return true;
    }).toList();
  }

  int computeTaskCount(List<TaskItem> allTasks) {
    return filterTasks(allTasks).length;
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'iconCodePoint': iconCodePoint,
      'colorValue': colorValue,
      'selectedAccount': selectedAccount,
      'selectedAccounts': effectiveAccounts.toList(),
      'statusFilter': statusFilter,
      'selectedSpace': selectedSpace,
      'selectedSubspace': selectedSubspace,
      'selectedPriority': selectedPriority,
      'selectedLists': selectedLists.toList(),
      'selectedTags': selectedTags.toList(),
      'searchQuery': searchQuery,
      'dateField': dateField,
      'dateRangeStart': dateRange?.start.toIso8601String(),
      'dateRangeEnd': dateRange?.end.toIso8601String(),
      'hideRecurring': hideRecurring,
      'hiddenLists': hiddenLists.toList(),
      'hiddenTags': hiddenTags.toList(),
      'sortField': sortField,
      'sortAscending': sortAscending,
      'viewMode': viewMode,
      'mandalaGrouping': mandalaGrouping,
      'mandalaGeometry': mandalaGeometry,
      'mandalaTheme': mandalaTheme,
    };
  }

  factory TaskTab.fromJson(Map<String, dynamic> json) {
    DateTimeRange? range;
    if (json['dateRangeStart'] != null && json['dateRangeEnd'] != null) {
      final start = DateTime.tryParse(json['dateRangeStart']);
      final end = DateTime.tryParse(json['dateRangeEnd']);
      if (start != null && end != null) {
        range = DateTimeRange(start: start, end: end);
      }
    }

    final rawAccounts = json['selectedAccounts'] as List?;
    Set<String> accs = {};
    if (rawAccounts != null) {
      accs = rawAccounts.map((e) => e.toString()).toSet();
    } else if (json['selectedAccount'] != null && json['selectedAccount'] != 'all') {
      accs = {json['selectedAccount'].toString()};
    }

    return TaskTab(
      id: json['id'] ?? 'tab_${DateTime.now().millisecondsSinceEpoch}',
      title: json['title'] ?? 'Tab',
      iconCodePoint: json['iconCodePoint'] as int?,
      colorValue: json['colorValue'] as int?,
      selectedAccount: json['selectedAccount'] as String?,
      selectedAccounts: accs,
      statusFilter: json['statusFilter'] as String? ?? 'pending',
      selectedSpace: json['selectedSpace'] as String?,
      selectedSubspace: json['selectedSubspace'] as String?,
      selectedPriority: json['selectedPriority'] as String?,
      selectedLists: (json['selectedLists'] as List?)?.map((e) => e.toString()).toSet(),
      selectedTags: (json['selectedTags'] as List?)?.map((e) => e.toString()).toSet(),
      searchQuery: json['searchQuery'] as String? ?? '',
      dateField: json['dateField'] as String?,
      dateRange: range,
      hideRecurring: json['hideRecurring'] as bool? ?? false,
      hiddenLists: (json['hiddenLists'] as List?)?.map((e) => e.toString()).toSet(),
      hiddenTags: (json['hiddenTags'] as List?)?.map((e) => e.toString()).toSet(),
      sortField: json['sortField'] as String? ?? 'priority',
      sortAscending: json['sortAscending'] as bool? ?? true,
      viewMode: json['viewMode'] as String?,
      mandalaGrouping: json['mandalaGrouping'] as String?,
      mandalaGeometry: json['mandalaGeometry'] as String?,
      mandalaTheme: json['mandalaTheme'] as String?,
    );
  }

  /// Compact mapping for the native Android Widget
  Map<String, dynamic> toWidgetJson({bool isActive = false}) {
    String? filterType;
    String? filterVal;
    if (selectedSpace != null && selectedSpace!.isNotEmpty) {
      filterType = 'space';
      filterVal = (selectedSubspace != null && selectedSubspace!.isNotEmpty)
          ? '$selectedSpace › $selectedSubspace'
          : selectedSpace;
    } else if (selectedPriority != null && selectedPriority!.isNotEmpty) {
      filterType = 'priority';
      filterVal = selectedPriority;
    } else if (selectedLists.isNotEmpty) {
      filterType = 'list';
      filterVal = selectedLists.first;
    } else if (selectedTags.isNotEmpty) {
      filterType = 'tag';
      filterVal = selectedTags.first;
    } else if (dateRange != null && dateField == 'due') {
      filterType = 'date';
      filterVal = 'today';
    }

    final data = <String, dynamic>{
      'id': id,
      'title': title,
      'statusFilter': statusFilter,
      'hideRecurring': hideRecurring,
      'sortField': sortField,
      'sortAscending': sortAscending,
      'isActive': isActive,
    };

    if (dateRange != null) {
      data['dateRangeStart'] = dateRange!.start.toIso8601String();
      data['dateRangeEnd'] = dateRange!.end.toIso8601String();
      if (dateField != null && dateField!.isNotEmpty) {
        data['dateField'] = dateField;
      }
    }

    if (selectedAccount != null && selectedAccount!.isNotEmpty) {
      data['account'] = selectedAccount;
    }
    if (effectiveAccounts.isNotEmpty) {
      data['accounts'] = effectiveAccounts.toList();
    }
    if (selectedLists.isNotEmpty) {
      data['selectedLists'] = selectedLists.toList();
    }
    if (selectedTags.isNotEmpty) {
      data['selectedTags'] = selectedTags.toList();
    }
    if (selectedSpace != null && selectedSpace!.isNotEmpty) {
      data['selectedSpace'] = selectedSpace;
    }
    if (selectedSubspace != null && selectedSubspace!.isNotEmpty) {
      data['selectedSubspace'] = selectedSubspace;
    }
    if (selectedPriority != null && selectedPriority!.isNotEmpty) {
      data['selectedPriority'] = selectedPriority;
    }
    if (hiddenLists.isNotEmpty) {
      data['hiddenLists'] = hiddenLists.toList();
    }
    if (hiddenTags.isNotEmpty) {
      data['hiddenTags'] = hiddenTags.toList();
    }
    if (filterType != null && filterType.isNotEmpty) {
      data['filterType'] = filterType;
    }
    if (filterVal != null && filterVal.isNotEmpty) {
      data['filterVal'] = filterVal;
    }
    if (viewMode != null && viewMode!.isNotEmpty) {
      data['viewMode'] = viewMode;
    }
    if (mandalaGrouping != null && mandalaGrouping!.isNotEmpty) {
      data['mandalaGrouping'] = mandalaGrouping;
    }
    if (mandalaGeometry != null && mandalaGeometry!.isNotEmpty) {
      data['mandalaGeometry'] = mandalaGeometry;
    }
    if (mandalaTheme != null && mandalaTheme!.isNotEmpty) {
      data['mandalaTheme'] = mandalaTheme;
    }

    return data;
  }
}
