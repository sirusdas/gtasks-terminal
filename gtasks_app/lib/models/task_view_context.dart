import 'package:flutter/material.dart';
import 'task_item.dart';

/// Encapsulates the active view scope and filters from the Tasks list screen,
/// allowing the AI Assistant to provide context-grounded analysis and scoped actions.
class TaskViewContext {
  final List<TaskItem> visibleTasks;
  final int totalTasksCount;
  final String? searchQuery;
  final String? selectedSpace;
  final String? selectedSubspace;
  final String? selectedPriority;
  final Set<String> selectedLists;
  final Set<String> selectedTags;
  final String statusFilter; // 'pending', 'completed', 'all'
  final DateTimeRange? dateRange;
  final String? dateField;

  const TaskViewContext({
    required this.visibleTasks,
    required this.totalTasksCount,
    this.searchQuery,
    this.selectedSpace,
    this.selectedSubspace,
    this.selectedPriority,
    this.selectedLists = const {},
    this.selectedTags = const {},
    this.statusFilter = 'pending',
    this.dateRange,
    this.dateField,
  });

  int get visibleCount => visibleTasks.length;

  bool get hasAnyFilter {
    return (searchQuery != null && searchQuery!.trim().isNotEmpty) ||
        selectedSpace != null ||
        selectedSubspace != null ||
        selectedPriority != null ||
        selectedLists.isNotEmpty ||
        selectedTags.isNotEmpty ||
        statusFilter != 'pending' ||
        dateRange != null;
  }

  /// Human-readable description of the active view filters
  String get filterDescription {
    final List<String> parts = [];
    if (selectedSpace != null) {
      if (selectedSubspace != null && selectedSubspace!.isNotEmpty) {
        parts.add('Space: $selectedSpace / $selectedSubspace');
      } else {
        parts.add('Space: $selectedSpace');
      }
    }
    if (selectedPriority != null) {
      parts.add('Priority: ${selectedPriority!.toUpperCase()}');
    }
    if (selectedLists.isNotEmpty) {
      parts.add('List: ${selectedLists.join(", ")}');
    }
    if (selectedTags.isNotEmpty) {
      parts.add('Tags: ${selectedTags.map((t) => "#$t").join(", ")}');
    }
    if (searchQuery != null && searchQuery!.trim().isNotEmpty) {
      parts.add('Search: "$searchQuery"');
    }
    if (statusFilter != 'pending') {
      parts.add('Status: ${statusFilter.toUpperCase()}');
    }
    if (dateRange != null) {
      parts.add('Date Filter');
    }
    if (parts.isEmpty) {
      return 'All Pending Tasks';
    }
    return parts.join(' • ');
  }

  String get shortLabel {
    if (selectedSpace != null) {
      return (selectedSubspace != null && selectedSubspace!.isNotEmpty)
          ? '$selectedSpace / $selectedSubspace'
          : selectedSpace!;
    }
    if (selectedPriority != null) return '${selectedPriority!.toUpperCase()} Priority';
    if (searchQuery != null && searchQuery!.trim().isNotEmpty) return '"$searchQuery"';
    if (selectedLists.isNotEmpty) return selectedLists.first;
    if (selectedTags.isNotEmpty) return '#${selectedTags.first}';
    return '$visibleCount tasks';
  }
}
