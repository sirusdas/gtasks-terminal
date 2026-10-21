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

    final Set<String> registeredSpaceIds = {};
    final Set<String> registeredSubspaceIds = {};
    final Map<String, int> spaceCounts = {};
    final Map<String, int> subspaceCounts = {};

    // Count first
    for (final task in tasks) {
      if (task.spaces.isEmpty) {
        spaceCounts['General'] = (spaceCounts['General'] ?? 0) + 1;
      } else {
        task.spaces.forEach((s, subs) {
          spaceCounts[s] = (spaceCounts[s] ?? 0) + 1;
          if (subs.isEmpty) {
            subspaceCounts['$s/Main'] = (subspaceCounts['$s/Main'] ?? 0) + 1;
          } else {
            for (final sub in subs) {
              subspaceCounts['$s/$sub'] = (subspaceCounts['$s/$sub'] ?? 0) + 1;
            }
          }
        });
      }
    }

    for (final task in tasks) {
      if (task.spaces.isEmpty) {
        const String spaceId = 'space_general';
        if (!registeredSpaceIds.contains(spaceId)) {
          registeredSpaceIds.add(spaceId);
          nodes.add(
            MandalaNode(
              id: spaceId,
              label: 'General / Inbox (${spaceCounts['General'] ?? 0})',
              parent: rootId,
              short: 'Inbox',
              display: forcePortals ? NodeDisplay.portal : NodeDisplay.auto,
            ),
          );
        }
        nodes.add(_taskNode(task, parentId: spaceId));
      } else {
        task.spaces.forEach((spaceName, subList) {
          final String spaceId = 'space_${spaceName.toLowerCase()}';
          if (!registeredSpaceIds.contains(spaceId)) {
            registeredSpaceIds.add(spaceId);
            final int count = spaceCounts[spaceName] ?? 0;
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

          if (subList.isEmpty) {
            nodes.add(_taskNode(task, parentId: spaceId));
          } else {
            for (final subName in subList) {
              final String subId = '${spaceId}_sub_${subName.toLowerCase()}';
              if (!registeredSubspaceIds.contains(subId)) {
                registeredSubspaceIds.add(subId);
                final int subCount = subspaceCounts['$spaceName/$subName'] ?? 0;
                nodes.add(
                  MandalaNode(
                    id: subId,
                    label: '$subName ($subCount)',
                    parent: spaceId,
                    short: subName,
                    display: forcePortals
                        ? NodeDisplay.portal
                        : NodeDisplay.auto,
                  ),
                );
              }
              nodes.add(_taskNode(task, parentId: subId));
            }
          }
        });
      }
    }

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

      for (final task in listTasks) {
        nodes.add(_taskNode(task, parentId: listId));
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

      for (final task in entry.value) {
        nodes.add(_taskNode(task, parentId: tagId));
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

      for (final task in untagged) {
        nodes.add(_taskNode(task, parentId: untaggedId));
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

      for (final task in pTasks) {
        nodes.add(_taskNode(task, parentId: prioId));
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
