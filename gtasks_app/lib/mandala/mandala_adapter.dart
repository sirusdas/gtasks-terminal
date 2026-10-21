import 'dart:math' as math;
import '../models/task_item.dart';
import 'mandala_types.dart';

enum MandalaGrouping { spaces, lists, tags, priorities, mandalachart }

class MandalaAdapter {
  static MandalaDoc fromTasks({
    required List<TaskItem> tasks,
    MandalaGrouping grouping = MandalaGrouping.spaces,
    String? focusTitle,
    GeometryId? forcedGeometry,
    MandalaNestingMode nestingMode = MandalaNestingMode.hierarchicalPortals,
    int maxCells = 64,
  }) {
    switch (grouping) {
      case MandalaGrouping.spaces:
        return _buildBySpaces(
          tasks,
          focusTitle,
          forcedGeometry,
          nestingMode,
          maxCells,
        );
      case MandalaGrouping.lists:
        return _buildByLists(
          tasks,
          focusTitle,
          forcedGeometry,
          nestingMode,
          maxCells,
        );
      case MandalaGrouping.tags:
        return _buildByTags(
          tasks,
          focusTitle,
          forcedGeometry,
          nestingMode,
          maxCells,
        );
      case MandalaGrouping.priorities:
        return _buildByPriorities(
          tasks,
          focusTitle,
          forcedGeometry,
          nestingMode,
          maxCells,
        );
      case MandalaGrouping.mandalachart:
        return _buildMandalachart(
          tasks,
          focusTitle,
          forcedGeometry,
          nestingMode,
          maxCells,
        );
    }
  }

  // --- Grouping by Space / Subspace ---
  static MandalaDoc _buildBySpaces(
    List<TaskItem> tasks,
    String? title,
    GeometryId? forcedGeometry,
    MandalaNestingMode nestingMode,
    int maxCells,
  ) {
    final List<MandalaNode> nodes = [];
    const String rootId = 'root_spaces';
    final bool forcePortals =
        nestingMode == MandalaNestingMode.hierarchicalPortals;

    nodes.add(
      MandalaNode(
        id: rootId,
        label: title ?? 'Spaces & Domains',
        details: '${tasks.length} total tasks organized by Space and Sub-space',
        geometry: forcedGeometry,
      ),
    );

    final Map<String, List<TaskItem>> spaceDirectTasks = {};
    final Map<String, List<TaskItem>> subspaceTasks = {};
    final Set<String> registeredSpaceIds = {};
    final Set<String> registeredSubspaceIds = {};
    final Map<String, int> spaceCounts = {};
    final Map<String, int> subspaceCounts = {};

    // Count and group tasks
    for (final task in tasks) {
      if (task.spaces.isEmpty) {
        spaceCounts['General'] = (spaceCounts['General'] ?? 0) + 1;
        spaceDirectTasks.putIfAbsent('space_general', () => []).add(task);
      } else {
        task.spaces.forEach((s, subs) {
          spaceCounts[s] = (spaceCounts[s] ?? 0) + 1;
          final String spaceId = 'space_${s.toLowerCase()}';
          if (subs.isEmpty) {
            subspaceCounts['$s/Main'] = (subspaceCounts['$s/Main'] ?? 0) + 1;
            spaceDirectTasks.putIfAbsent(spaceId, () => []).add(task);
          } else {
            for (final sub in subs) {
              subspaceCounts['$s/$sub'] = (subspaceCounts['$s/$sub'] ?? 0) + 1;
              final String subId = '${spaceId}_sub_${sub.toLowerCase()}';
              subspaceTasks.putIfAbsent(subId, () => []).add(task);
            }
          }
        });
      }
    }

    if (spaceDirectTasks.containsKey('space_general')) {
      const String spaceId = 'space_general';
      final gTasks = spaceDirectTasks[spaceId]!;
      registeredSpaceIds.add(spaceId);
      nodes.add(
        MandalaNode(
          id: spaceId,
          label: 'General / Inbox (${gTasks.length})',
          parent: rootId,
          short: 'Inbox',
          display: forcePortals ? NodeDisplay.portal : NodeDisplay.auto,
        ),
      );
      if (gTasks.length <= 12) {
        for (final task in gTasks) {
          nodes.add(_taskNode(task, parentId: spaceId));
        }
      } else {
        _decomposeTasksIntoSubMandala(
          tasks: gTasks,
          parentId: spaceId,
          nodes: nodes,
          forcePortals: forcePortals,
        );
      }
    }

    spaceCounts.forEach((spaceName, count) {
      if (spaceName == 'General') return;
      final String spaceId = 'space_${spaceName.toLowerCase()}';
      if (!registeredSpaceIds.contains(spaceId)) {
        registeredSpaceIds.add(spaceId);
        nodes.add(
          MandalaNode(
            id: spaceId,
            label: '$spaceName ($count)',
            parent: rootId,
            short: spaceName,
            display: forcePortals ? NodeDisplay.portal : NodeDisplay.auto,
          ),
        );
      }

      final direct = spaceDirectTasks[spaceId];
      if (direct != null && direct.isNotEmpty) {
        if (direct.length <= 12) {
          for (final task in direct) {
            nodes.add(_taskNode(task, parentId: spaceId));
          }
        } else {
          _decomposeTasksIntoSubMandala(
            tasks: direct,
            parentId: spaceId,
            nodes: nodes,
            forcePortals: forcePortals,
          );
        }
      }
    });

    subspaceCounts.forEach((fullSub, count) {
      final parts = fullSub.split('/');
      final sName = parts[0];
      final subName = parts[1];
      if (subName == 'Main') return;
      final String spaceId = 'space_${sName.toLowerCase()}';
      final String subId = '${spaceId}_sub_${subName.toLowerCase()}';
      if (!registeredSubspaceIds.contains(subId)) {
        registeredSubspaceIds.add(subId);
        nodes.add(
          MandalaNode(
            id: subId,
            label: '$subName ($count)',
            parent: spaceId,
            short: subName,
            display: forcePortals
                ? NodeDisplay.portal
                : NodeDisplay.auto,
          ),
        );
      }
      final sTasks = subspaceTasks[subId];
      if (sTasks != null && sTasks.isNotEmpty) {
        if (sTasks.length <= 12) {
          for (final task in sTasks) {
            nodes.add(_taskNode(task, parentId: subId));
          }
        } else {
          _decomposeTasksIntoSubMandala(
            tasks: sTasks,
            parentId: subId,
            nodes: nodes,
            forcePortals: forcePortals,
          );
        }
      }
    });

    return MandalaDoc(
      title: title ?? 'Spaces Mandala',
      nodes: nodes,
      relations: _extractRelations(tasks),
      settings: DocSettings(
        geometry: forcedGeometry,
        fit: nestingMode == MandalaNestingMode.flat ? 'all' : 'auto',
        maxCellsPerMandala: maxCells,
      ),
    );
  }

  // --- Grouping by Task List ---
  static MandalaDoc _buildByLists(
    List<TaskItem> tasks,
    String? title,
    GeometryId? forcedGeometry,
    MandalaNestingMode nestingMode,
    int maxCells,
  ) {
    final List<MandalaNode> nodes = [];
    const String rootId = 'root_lists';
    final bool forcePortals =
        nestingMode == MandalaNestingMode.hierarchicalPortals;

    nodes.add(
      MandalaNode(
        id: rootId,
        label: title ?? 'Task Lists',
        details: '${tasks.length} total tasks across lists',
        geometry: forcedGeometry,
      ),
    );

    final Map<String, List<TaskItem>> listGroups = {};
    for (final task in tasks) {
      final String listName = task.listTitle ?? 'Default List';
      listGroups.putIfAbsent(listName, () => []).add(task);
    }

    listGroups.forEach((listName, listTasks) {
      final String listId =
          'list_${listName.toLowerCase().replaceAll(RegExp(r'\s+'), '_')}';
      nodes.add(
        MandalaNode(
          id: listId,
          label: '$listName (${listTasks.length})',
          parent: rootId,
          short: listName,
          display: forcePortals ? NodeDisplay.portal : NodeDisplay.auto,
        ),
      );

      if (listTasks.length <= 12) {
        for (final task in listTasks) {
          nodes.add(_taskNode(task, parentId: listId));
        }
      } else {
        _decomposeTasksIntoSubMandala(
          tasks: listTasks,
          parentId: listId,
          nodes: nodes,
          forcePortals: forcePortals,
        );
      }
    });

    return MandalaDoc(
      title: title ?? 'Lists Mandala',
      nodes: nodes,
      relations: _extractRelations(tasks),
      settings: DocSettings(
        geometry: forcedGeometry,
        fit: nestingMode == MandalaNestingMode.flat ? 'all' : 'auto',
        maxCellsPerMandala: maxCells,
      ),
    );
  }

  // --- Grouping by Tags ---
  static MandalaDoc _buildByTags(
    List<TaskItem> tasks,
    String? title,
    GeometryId? forcedGeometry,
    MandalaNestingMode nestingMode,
    int maxCells,
  ) {
    final List<MandalaNode> nodes = [];
    const String rootId = 'root_tags';
    final bool forcePortals =
        nestingMode == MandalaNestingMode.hierarchicalPortals;

    nodes.add(
      MandalaNode(
        id: rootId,
        label: title ?? 'Tags & Categories',
        details: '${tasks.length} total tasks organized by tags',
        geometry: forcedGeometry,
      ),
    );

    final Map<String, List<TaskItem>> tagGroups = {};
    final List<TaskItem> untagged = [];

    for (final task in tasks) {
      if (task.allTags.isEmpty) {
        untagged.add(task);
      } else {
        for (final tag in task.allTags) {
          tagGroups.putIfAbsent(tag, () => []).add(task);
        }
      }
    }

    // Sort tags by frequency
    final sortedTags = tagGroups.entries.toList()
      ..sort((a, b) => b.value.length.compareTo(a.value.length));

    for (final entry in sortedTags) {
      final String tag = entry.key;
      final String tagId = 'tag_${tag.toLowerCase()}';
      nodes.add(
        MandalaNode(
          id: tagId,
          label: '#$tag (${entry.value.length})',
          parent: rootId,
          short: '#$tag',
          display: forcePortals ? NodeDisplay.portal : NodeDisplay.auto,
        ),
      );

      if (entry.value.length <= 12) {
        for (final task in entry.value) {
          nodes.add(_taskNode(task, parentId: tagId));
        }
      } else {
        _decomposeTasksIntoSubMandala(
          tasks: entry.value,
          parentId: tagId,
          nodes: nodes,
          forcePortals: forcePortals,
        );
      }
    }

    if (untagged.isNotEmpty) {
      const String untaggedId = 'tag_untagged';
      nodes.add(
        MandalaNode(
          id: untaggedId,
          label: 'Untagged (${untagged.length})',
          parent: rootId,
          short: 'None',
          display: forcePortals ? NodeDisplay.portal : NodeDisplay.auto,
        ),
      );

      if (untagged.length <= 12) {
        for (final task in untagged) {
          nodes.add(_taskNode(task, parentId: untaggedId));
        }
      } else {
        _decomposeTasksIntoSubMandala(
          tasks: untagged,
          parentId: untaggedId,
          nodes: nodes,
          forcePortals: forcePortals,
        );
      }
    }

    return MandalaDoc(
      title: title ?? 'Tags Mandala',
      nodes: nodes,
      relations: _extractRelations(tasks),
      settings: DocSettings(
        geometry: forcedGeometry,
        fit: nestingMode == MandalaNestingMode.flat ? 'all' : 'auto',
        maxCellsPerMandala: maxCells,
      ),
    );
  }

  // --- Grouping by Priority ---
  static MandalaDoc _buildByPriorities(
    List<TaskItem> tasks,
    String? title,
    GeometryId? forcedGeometry,
    MandalaNestingMode nestingMode,
    int maxCells,
  ) {
    final List<MandalaNode> nodes = [];
    const String rootId = 'root_priority';
    final bool forcePortals =
        nestingMode == MandalaNestingMode.hierarchicalPortals;

    nodes.add(
      MandalaNode(
        id: rootId,
        label: title ?? 'Priority Overview',
        details: '${tasks.length} tasks categorized by urgency',
        geometry: forcedGeometry,
      ),
    );

    final Map<String, String> priorityLabels = {
      'critical': '🚨 Critical',
      'high': '🔥 High',
      'medium': '⚡ Medium',
      'low': '🌱 Low',
    };

    final Map<String, List<TaskItem>> priorityBuckets = {
      'critical': [],
      'high': [],
      'medium': [],
      'low': [],
    };

    for (final task in tasks) {
      final String p = task.calculatedPriority.toLowerCase();
      if (priorityBuckets.containsKey(p)) {
        priorityBuckets[p]!.add(task);
      } else {
        priorityBuckets['medium']!.add(task);
      }
    }

    priorityBuckets.forEach((prioKey, pTasks) {
      if (pTasks.isEmpty) return;
      final String prioId = 'prio_$prioKey';
      nodes.add(
        MandalaNode(
          id: prioId,
          label: '${priorityLabels[prioKey]} (${pTasks.length})',
          parent: rootId,
          type: prioKey,
          short: prioKey[0].toUpperCase(),
          display: forcePortals ? NodeDisplay.portal : NodeDisplay.auto,
        ),
      );

      if (pTasks.length <= 12) {
        for (final task in pTasks) {
          nodes.add(_taskNode(task, parentId: prioId));
        }
      } else {
        _decomposeTasksIntoSubMandala(
          tasks: pTasks,
          parentId: prioId,
          nodes: nodes,
          forcePortals: forcePortals,
        );
      }
    });

    return MandalaDoc(
      title: title ?? 'Priority Mandala',
      nodes: nodes,
      relations: _extractRelations(tasks),
      settings: DocSettings(
        geometry: forcedGeometry,
        fit: nestingMode == MandalaNestingMode.flat ? 'all' : 'auto',
        maxCellsPerMandala: maxCells,
      ),
    );
  }

  // --- Harada Method / 9x9 Mandalachart Mode ---
  static MandalaDoc _buildMandalachart(
    List<TaskItem> tasks,
    String? title,
    GeometryId? forcedGeometry,
    MandalaNestingMode nestingMode,
    int maxCells,
  ) {
    final List<MandalaNode> nodes = [];
    const String rootId = 'mandalachart_goal';
    nodes.add(
      MandalaNode(
        id: rootId,
        label: title ?? 'Core Goal Focus',
        details: 'Central objective surrounded by 8 core pillars',
        geometry: forcedGeometry ?? GeometryId.chakra,
      ),
    );

    // Discover 8 core pillars
    final Map<String, List<TaskItem>> pillars = {};
    for (final task in tasks) {
      String pillarName = 'Core';
      if (task.spaces.isNotEmpty) {
        pillarName = task.spaces.keys.first;
      } else if (task.listTitle != null && task.listTitle!.isNotEmpty) {
        pillarName = task.listTitle!;
      } else if (task.allTags.isNotEmpty) {
        pillarName = task.allTags.first;
      }
      pillars.putIfAbsent(pillarName, () => []).add(task);
    }

    final List<MapEntry<String, List<TaskItem>>> sortedPillars =
        pillars.entries.toList()
          ..sort((a, b) => b.value.length.compareTo(a.value.length));

    // Up to 8 pillars
    final int pillarLimit = sortedPillars.length > 8 ? 8 : sortedPillars.length;
    for (int i = 0; i < pillarLimit; i++) {
      final entry = sortedPillars[i];
      final String pillarId = 'pillar_$i';
      nodes.add(
        MandalaNode(
          id: pillarId,
          label: '${entry.key} (${entry.value.length})',
          parent: rootId,
          short: entry.key,
          display: nestingMode == MandalaNestingMode.hierarchicalPortals
              ? NodeDisplay.portal
              : NodeDisplay.auto,
        ),
      );

      // Up to 8 tasks per pillar in 9x9 matrix
      final List<TaskItem> pillarTasks = entry.value.take(8).toList();
      for (final task in pillarTasks) {
        nodes.add(_taskNode(task, parentId: pillarId));
      }
    }

    return MandalaDoc(
      title: title ?? '9x9 Goal Mandalachart',
      nodes: nodes,
      relations: _extractRelations(tasks),
      settings: DocSettings(
        geometry: forcedGeometry ?? GeometryId.chakra,
        fit: nestingMode == MandalaNestingMode.flat ? 'all' : 'auto',
        symmetry: 8,
        maxCellsPerMandala: 73,
      ),
    );
  }

  static void _decomposeTasksIntoSubMandala({
    required List<TaskItem> tasks,
    required String parentId,
    required List<MandalaNode> nodes,
    required bool forcePortals,
  }) {
    final pendingTasks = tasks.where((t) => !t.isCompleted).toList();
    final completedTasks = tasks.where((t) => t.isCompleted).toList();
    final bool isAlreadyPriority = parentId.startsWith('prio_');

    // 1. Analyze Priority Distribution
    final Map<String, List<TaskItem>> prioBuckets = {
      'critical': [],
      'high': [],
      'medium': [],
      'low': [],
    };
    for (final t in pendingTasks) {
      final p = t.calculatedPriority.toLowerCase();
      if (prioBuckets.containsKey(p)) {
        prioBuckets[p]!.add(t);
      } else {
        prioBuckets['medium']!.add(t);
      }
    }

    final activePrios =
        prioBuckets.entries.where((e) => e.value.isNotEmpty).toList();
    final int maxPrioCount = activePrios.isEmpty
        ? 0
        : activePrios.map((e) => e.value.length).reduce(math.max);
    final bool isPriorityDiverse = !isAlreadyPriority &&
        activePrios.length > 1 &&
        pendingTasks.isNotEmpty &&
        (maxPrioCount / pendingTasks.length) < 0.85;

    if (isPriorityDiverse) {
      // Group by Priority
      final Map<String, String> prioLabels = {
        'critical': '🚨 Critical',
        'high': '🔥 High',
        'medium': '⚡ Medium',
        'low': '🌱 Low',
      };
      for (final entry in activePrios) {
        final pKey = entry.key;
        final pTasks = entry.value;
        final portalId = '${parentId}_prio_$pKey';
        nodes.add(
          MandalaNode(
            id: portalId,
            label: '${prioLabels[pKey]} (${pTasks.length})',
            parent: parentId,
            type: pKey,
            short: pKey[0].toUpperCase(),
            display: NodeDisplay.portal,
          ),
        );
        _batchTasksIfLarge(
          tasks: pTasks,
          parentId: portalId,
          nodes: nodes,
          forcePortals: forcePortals,
        );
      }
    } else {
      // Group by Temporal Horizons (Overdue, Due Today, This Week, Upcoming, Someday)
      final now = DateTime.now();
      final today = DateTime(now.year, now.month, now.day);
      final nextWeek = today.add(const Duration(days: 7));

      final List<TaskItem> overdue = [];
      final List<TaskItem> dueToday = [];
      final List<TaskItem> thisWeek = [];
      final List<TaskItem> upcoming = [];
      final List<TaskItem> noDue = [];

      for (final t in pendingTasks) {
        if (t.due == null || t.due!.isEmpty) {
          noDue.add(t);
        } else {
          final parsed = DateTime.tryParse(t.due!);
          if (parsed == null) {
            noDue.add(t);
          } else {
            final d = DateTime(parsed.year, parsed.month, parsed.day);
            if (d.isBefore(today)) {
              overdue.add(t);
            } else if (d.isAtSameMomentAs(today)) {
              dueToday.add(t);
            } else if (d.isBefore(nextWeek) || d.isAtSameMomentAs(nextWeek)) {
              thisWeek.add(t);
            } else {
              upcoming.add(t);
            }
          }
        }
      }

      final timeBuckets = [
        if (overdue.isNotEmpty)
          ('overdue', '🚨 Overdue (${overdue.length})', overdue, 'critical'),
        if (dueToday.isNotEmpty)
          ('today', '📅 Due Today (${dueToday.length})', dueToday, 'high'),
        if (thisWeek.isNotEmpty)
          ('week', '🌅 This Week (${thisWeek.length})', thisWeek, 'medium'),
        if (upcoming.isNotEmpty)
          ('upcoming', '📆 Upcoming (${upcoming.length})', upcoming, 'low'),
        if (noDue.isNotEmpty)
          ('nodue', '📥 Someday (${noDue.length})', noDue, 'medium'),
      ];

      for (final item in timeBuckets) {
        final key = item.$1;
        final label = item.$2;
        final bTasks = item.$3;
        final typeStr = item.$4;
        final portalId = '${parentId}_time_$key';
        nodes.add(
          MandalaNode(
            id: portalId,
            label: label,
            parent: parentId,
            type: typeStr,
            short: key,
            display: NodeDisplay.portal,
          ),
        );
        _batchTasksIfLarge(
          tasks: bTasks,
          parentId: portalId,
          nodes: nodes,
          forcePortals: forcePortals,
        );
      }
    }

    // Completed Tasks Portal
    if (completedTasks.isNotEmpty) {
      final compId = '${parentId}_completed';
      nodes.add(
        MandalaNode(
          id: compId,
          label: '✓ Completed (${completedTasks.length})',
          parent: parentId,
          type: 'completed',
          short: 'Done',
          display: NodeDisplay.portal,
        ),
      );
      _batchTasksIfLarge(
        tasks: completedTasks,
        parentId: compId,
        nodes: nodes,
        forcePortals: forcePortals,
      );
    }
  }

  static void _batchTasksIfLarge({
    required List<TaskItem> tasks,
    required String parentId,
    required List<MandalaNode> nodes,
    required bool forcePortals,
  }) {
    if (tasks.length <= 12) {
      for (final task in tasks) {
        nodes.add(_taskNode(task, parentId: parentId));
      }
    } else {
      const int batchSize = 8;
      final int numBatches = (tasks.length + batchSize - 1) ~/ batchSize;
      for (int b = 0; b < numBatches; b++) {
        final int start = b * batchSize;
        final int end = math.min(start + batchSize, tasks.length);
        final batchTasks = tasks.sublist(start, end);
        final batchId = '${parentId}_batch_$b';
        nodes.add(
          MandalaNode(
            id: batchId,
            label: '🎯 Focus Batch ${b + 1} (${batchTasks.length})',
            parent: parentId,
            short: 'Batch ${b + 1}',
            display: NodeDisplay.portal,
          ),
        );
        for (final task in batchTasks) {
          nodes.add(_taskNode(task, parentId: batchId));
        }
      }
    }
  }

  static MandalaNode _taskNode(TaskItem task, {required String parentId}) {
    final String p = task.calculatedPriority.toLowerCase();
    final String displayType = task.isCompleted ? 'completed' : p;
    final List<String> detailParts = [];
    if (task.status.isNotEmpty) detailParts.add('Status: ${task.status}');
    if (task.calculatedPriority.isNotEmpty) {
      detailParts.add('Priority: ${task.calculatedPriority}');
    }
    if (task.formattedDueDate != null) {
      detailParts.add('Due: ${task.formattedDueDate}');
    }
    if (task.cleanNotes.isNotEmpty) {
      detailParts.add('\n${task.cleanNotes}');
    }

    return MandalaNode(
      id: '${parentId}_${task.id}',
      label: task.title,
      parent: parentId,
      type: displayType,
      details: detailParts.join(' | '),
      data: {'task': task, 'taskId': task.id},
    );
  }

  static List<MandalaRelation> _extractRelations(List<TaskItem> tasks) {
    final List<MandalaRelation> relations = [];
    final Set<String> allIds = tasks.map((t) => t.id).toSet();

    for (final task in tasks) {
      final regex = RegExp(
        r'depends_on:\s*([a-zA-Z0-9_\-]+)',
        caseSensitive: false,
      );
      final matches = regex.allMatches(task.description);
      for (final m in matches) {
        final targetId = m.group(1);
        if (targetId != null &&
            allIds.contains(targetId) &&
            targetId != task.id) {
          relations.add(
            MandalaRelation(
              source: task.id,
              target: targetId,
              type: 'depends_on',
            ),
          );
        }
      }
    }
    return relations;
  }
}
