import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';
import '../ui/widgets/task_editor_dialog.dart';
import 'mandala_types.dart';
import 'mandala_adapter.dart';
import 'mandala_partition.dart';
import 'mandala_layout.dart';
import 'mandala_painter.dart';
import 'mandala_path_parser.dart';
import 'mandala_themes.dart';
import 'custom_mandala_service.dart';
import 'custom_mandala_dialog.dart';
import '../../models/task_tab.dart';
import '../ui/widgets/task_filter_modal.dart';

class MandalaScreen extends StatefulWidget {
  final List<TaskItem>? initialTasks;
  final String? title;
  final MandalaGrouping? initialGrouping;
  final GeometryId? initialGeometry;
  final String? initialCustomMandalaId;
  final String? initialFocusItem;
  final String? initialThemeName;
  final TaskTab? initialTab;
  final bool isEmbedded;

  const MandalaScreen({
    super.key,
    this.initialTasks,
    this.title,
    this.initialGrouping,
    this.initialGeometry,
    this.initialCustomMandalaId,
    this.initialFocusItem,
    this.initialThemeName,
    this.initialTab,
    this.isEmbedded = false,
  });

  @override
  State<MandalaScreen> createState() => _MandalaScreenState();
}

class _MandalaScreenState extends State<MandalaScreen> {
  MandalaGrouping _grouping = MandalaGrouping.spaces;
  MandalaNestingMode _nestingMode = MandalaNestingMode.hierarchicalPortals;
  GeometryId? _forcedGeometry;
  String? _currentMandalaId;
  String? _selectedCellId;

  late TaskTab _mandalaTab;

  // Custom Mandalas
  List<CustomMandala> _customMandalas = [];
  CustomMandala? _activeCustomMandala;
  MandalaThemePalette _activeTheme = MandalaThemePalette.cyberpunk;

  late MandalaDoc _doc;
  late MandalaAtlas _atlas;
  late MandalaLayout _layout;

  final Map<String, ui.Path> _pathCache = {};
  final TransformationController _transformController =
      TransformationController();

  @override
  void initState() {
    super.initState();
    final p = context.read<TaskProvider>();
    final baseTab = widget.initialTab ?? p.activeTab ?? TaskTab(id: 'mandala', title: widget.title ?? 'Mandala');
    _mandalaTab = widget.isEmbedded ? baseTab : baseTab.copyWith(
      id: 'mandala_${DateTime.now().millisecondsSinceEpoch}',
    );
    if (widget.initialGrouping != null) {
      _grouping = widget.initialGrouping!;
    }
    if (widget.initialGeometry != null) {
      _forcedGeometry = widget.initialGeometry!;
    }
    if (widget.initialThemeName != null && widget.initialThemeName!.isNotEmpty) {
      _activeTheme = MandalaThemePalette.getById(widget.initialThemeName!);
    } else {
      _loadTheme();
    }
    _loadCustomMandalas().then((_) {
      if (widget.initialCustomMandalaId != null && mounted) {
        final match = _customMandalas.firstWhere(
          (m) => m.id == widget.initialCustomMandalaId,
          orElse: () => _customMandalas.first,
        );
        setState(() {
          _activeCustomMandala = match;
          _currentMandalaId = match.id;
          _rebuildEngine();
        });
      }
      if (widget.initialFocusItem != null &&
          widget.initialFocusItem!.isNotEmpty &&
          mounted) {
        _navigateToFocusItem(widget.initialFocusItem!);
      }
    });
    _rebuildEngine();
  }

  @override
  void didUpdateWidget(covariant MandalaScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isEmbedded && widget.initialTab != null && widget.initialTab != _mandalaTab) {
      setState(() {
        _mandalaTab = widget.initialTab!;
        _rebuildEngine(targetMandalaId: _currentMandalaId);
      });
    }
  }

  Future<void> _loadTheme() async {
    final prefs = await SharedPreferences.getInstance();
    final themeName = prefs.getString('mandala_theme');
    if (themeName != null && mounted) {
      setState(() {
        _activeTheme = MandalaThemePalette.getById(themeName);
      });
    }
  }

  Future<void> _setTheme(MandalaThemePalette theme) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('mandala_theme', theme.id.name);
    if (mounted) {
      setState(() {
        _activeTheme = theme;
      });
    }
  }

  void _navigateToFocusItem(String target) {
    final cleanTarget = target
        .replaceAll(RegExp(r'\s*\(\d+\)$'), '')
        .trim()
        .toLowerCase();

    // 1. Search in atlas mandalas directly for a part matching this domain/space
    final matchingPart = _atlas.mandalas.values.cast<MandalaPart?>().firstWhere((p) {
      if (p == null) return false;
      final partTitle = p.title.replaceAll(RegExp(r'\s*\(\d+\)$'), '').trim().toLowerCase();
      final partId = p.id.toLowerCase();
      return partTitle == cleanTarget ||
          partId == cleanTarget ||
          partId.endsWith('_$cleanTarget') ||
          partId == 'space_$cleanTarget' ||
          partId == 'list_$cleanTarget';
    }, orElse: () => null);

    if (matchingPart != null && matchingPart.id != _atlas.rootMandala) {
      _switchMandala(matchingPart.id);
      return;
    }

    // 2. Search for matching portal cell in the active layout
    for (final cell in _layout.cells) {
      final cellLabel = (cell.label?.full ?? cell.label?.text ?? cell.id)
          .replaceAll(RegExp(r'\s*\(\d+\)$'), '')
          .trim()
          .toLowerCase();
      if (cellLabel == cleanTarget || cell.id.toLowerCase().contains(cleanTarget)) {
        if (cell.portal != null && _atlas.mandalas.containsKey(cell.portal)) {
          _switchMandala(cell.portal!);
          return;
        } else {
          setState(() {
            _selectedCellId = cell.id;
          });
          return;
        }
      }
    }
  }

  Future<void> _loadCustomMandalas() async {
    final list = await CustomMandalaService.loadCustomMandalas();
    if (mounted) {
      setState(() {
        _customMandalas = list;
      });
    }
  }

  void _rebuildEngine({String? targetMandalaId}) {
    if (_activeCustomMandala != null) {
      _doc = _activeCustomMandala!.toDoc(nestingMode: _nestingMode);
      if (_forcedGeometry != null) {
        _doc = MandalaDoc(
          title: _doc.title,
          nodes: _doc.nodes,
          relations: _doc.relations,
          settings: DocSettings(
            geometry: _forcedGeometry,
            fit: _nestingMode == MandalaNestingMode.flat ? 'all' : 'auto',
          ),
        );
      }
    } else {
      final allTasks = context.read<TaskProvider>().allTasksUnfiltered;
      final tasks = widget.initialTasks != null && widget.initialTab == null
          ? widget.initialTasks!
          : _mandalaTab.filterTasks(allTasks);

      final tabTitle = _mandalaTab.title;
      final focusTitle = widget.title ?? (tabTitle != 'All Tasks' && tabTitle != 'Tab' && tabTitle != 'Mandala' ? tabTitle : null);

      _doc = MandalaAdapter.fromTasks(
        tasks: tasks,
        grouping: _grouping,
        focusTitle: focusTitle,
        forcedGeometry: _forcedGeometry,
        nestingMode: _nestingMode,
      );
    }

    _atlas = buildAtlas(_doc);
    _pathCache.clear();

    final String initialId = targetMandalaId ?? _atlas.rootMandala;
    _currentMandalaId = _atlas.mandalas.containsKey(initialId)
        ? initialId
        : _atlas.rootMandala;

    _layout = layoutMandala(_atlas, _currentMandalaId!);
  }

  void _switchMandala(String mandalaId) {
    if (!_atlas.mandalas.containsKey(mandalaId)) return;
    setState(() {
      _currentMandalaId = mandalaId;
      _selectedCellId = null;
      _pathCache.clear();
      _layout = layoutMandala(_atlas, mandalaId);
      _transformController.value = Matrix4.identity();
    });
  }

  void _handleTapUp(TapUpDetails details, Size canvasSize) {
    final Offset local = details.localPosition;
    final double midX = canvasSize.width / 2;
    final double midY = canvasSize.height / 2;
    final double scale =
        math.min(canvasSize.width, canvasSize.height) / _layout.size;

    final Offset layoutPt = Offset(
      (local.dx - midX) / scale,
      (local.dy - midY) / scale,
    );

    Cell? hitCell;
    for (int i = _layout.cells.length - 1; i >= 0; i--) {
      final cell = _layout.cells[i];
      final path = _pathCache.putIfAbsent(
        cell.id,
        () => MandalaPathParser.parse(cell.path),
      );
      if (path.contains(layoutPt)) {
        hitCell = cell;
        break;
      }
    }

    if (hitCell == null) {
      setState(() => _selectedCellId = null);
      return;
    }

    setState(() => _selectedCellId = hitCell!.id);

    // If portal, dive into inner mandala!
    if (hitCell.portal != null) {
      _switchMandala(hitCell.portal!);
      return;
    }

    // If center bindu and not at root, double tap or tap goes up
    if (hitCell.kind == CellKind.bindu &&
        _currentMandalaId != _atlas.rootMandala) {
      final parentId = _atlas.mandalas[_currentMandalaId]?.parentMandala;
      if (parentId != null) {
        _switchMandala(parentId);
        return;
      }
    }

    // If real node, show modal sheet
    if (hitCell.nodeId != null) {
      _showNodeModal(hitCell);
    }
  }

  TaskItem? _findTaskForCell(Cell cell) {
    final tasks = context.read<TaskProvider>().allTasksUnfiltered;
    return tasks.cast<TaskItem?>().firstWhere((t) {
      if (t == null) return false;
      if (t.id == cell.nodeId) return true;
      if (cell.nodeId != null && cell.nodeId!.endsWith('_${t.id}')) return true;
      return false;
    }, orElse: () => null);
  }

  void _showNodeModal(Cell cell) {
    final task = _findTaskForCell(cell);
    final theme = Theme.of(context);
    final isCustom = _activeCustomMandala != null;

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.transparent,
      isScrollControlled: true,
      builder: (ctx) {
        return Container(
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: theme.colorScheme.surface,
            borderRadius: const BorderRadius.vertical(top: Radius.circular(24)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.2),
                blurRadius: 16,
                offset: const Offset(0, -4),
              ),
            ],
          ),
          child: SafeArea(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    margin: const EdgeInsets.only(bottom: 16),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.outlineVariant,
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 8,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: _getPriorityColor(
                          cell.type,
                        ).withValues(alpha: 0.2),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Text(
                        (cell.type ?? (task != null ? 'TASK' : 'NODE'))
                            .toUpperCase(),
                        style: TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: _getPriorityColor(cell.type),
                        ),
                      ),
                    ),
                    const SizedBox(width: 8),
                    if (task?.isCompleted == true)
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 4,
                        ),
                        decoration: BoxDecoration(
                          color: Colors.green.withValues(alpha: 0.2),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: const Text(
                          'COMPLETED',
                          style: TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.bold,
                            color: Colors.green,
                          ),
                        ),
                      ),
                    const Spacer(),
                    IconButton(
                      icon: const Icon(Icons.close, size: 20),
                      onPressed: () => Navigator.pop(ctx),
                    ),
                  ],
                ),
                const SizedBox(height: 10),
                Text(
                  cell.label?.full ?? cell.id,
                  style: theme.textTheme.titleLarge?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                if (cell.details != null && cell.details!.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    cell.details!,
                    style: theme.textTheme.bodyMedium?.copyWith(
                      color: theme.colorScheme.onSurfaceVariant,
                    ),
                  ),
                ],
                const SizedBox(height: 20),

                // Action Buttons
                Wrap(
                  spacing: 8,
                  runSpacing: 8,
                  children: [
                    if (task != null) ...[
                      OutlinedButton.icon(
                        icon: Icon(
                          task.isCompleted
                              ? Icons.restart_alt
                              : Icons.check_circle_outline,
                          size: 18,
                        ),
                        label: Text(
                          task.isCompleted ? 'Mark Pending' : 'Complete',
                        ),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          await context.read<TaskProvider>().completeTask(
                            task.id,
                          );
                          setState(() {
                            _rebuildEngine(targetMandalaId: _currentMandalaId);
                          });
                        },
                      ),
                      FilledButton.icon(
                        icon: const Icon(Icons.edit_outlined, size: 18),
                        label: const Text('Edit Task'),
                        onPressed: () {
                          Navigator.pop(ctx);
                          showDialog(
                            context: context,
                            builder: (_) => TaskEditorDialog(task: task),
                          ).then((_) {
                            setState(() {
                              _rebuildEngine(
                                targetMandalaId: _currentMandalaId,
                              );
                            });
                          });
                        },
                      ),
                    ],

                    // In Custom Mandala: Node Editing Options
                    if (isCustom) ...[
                      FilledButton.tonalIcon(
                        icon: const Icon(Icons.add_circle_outline, size: 18),
                        label: const Text('Add Sub-Petal'),
                        onPressed: () {
                          Navigator.pop(ctx);
                          _showAddCustomNodeDialog(parentId: cell.nodeId!);
                        },
                      ),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.call_split, size: 18),
                        label: const Text('Extract as Standalone'),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          await _extractNodeAsNewMandala(cell);
                        },
                      ),
                      OutlinedButton.icon(
                        icon: const Icon(Icons.link, size: 18),
                        label: const Text('Link GTask'),
                        onPressed: () {
                          Navigator.pop(ctx);
                          _showLinkTaskDialog(parentId: cell.nodeId!);
                        },
                      ),
                      OutlinedButton.icon(
                        icon: const Icon(
                          Icons.delete_outline,
                          color: Colors.redAccent,
                          size: 18,
                        ),
                        label: const Text(
                          'Delete Node',
                          style: TextStyle(color: Colors.redAccent),
                        ),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          await _deleteCustomNode(cell.nodeId!);
                        },
                      ),
                    ] else if (cell.kind != CellKind.bindu) ...[
                      OutlinedButton.icon(
                        icon: const Icon(Icons.call_split, size: 18),
                        label: const Text('Extract Pillar as Mandala'),
                        onPressed: () async {
                          Navigator.pop(ctx);
                          await _extractPillarFromTasks(cell);
                        },
                      ),
                    ],
                  ],
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  // --- Custom Node Operations ---
  void _showAddCustomNodeDialog({required String parentId}) {
    final titleCtrl = TextEditingController();
    final detailsCtrl = TextEditingController();
    String priority = 'medium';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) => AlertDialog(
          title: const Text('Add Petal / Child Node'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: titleCtrl,
                autofocus: true,
                decoration: const InputDecoration(
                  labelText: 'Title / Action',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: detailsCtrl,
                decoration: const InputDecoration(
                  labelText: 'Notes / Details (Optional)',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              DropdownButtonFormField<String>(
                initialValue: priority,
                decoration: const InputDecoration(
                  labelText: 'Priority / Color',
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(
                    value: 'critical',
                    child: Text('🚨 Critical (Red)'),
                  ),
                  DropdownMenuItem(
                    value: 'high',
                    child: Text('🔥 High (Orange)'),
                  ),
                  DropdownMenuItem(
                    value: 'medium',
                    child: Text('⚡ Medium (Cyan)'),
                  ),
                  DropdownMenuItem(value: 'low', child: Text('🌱 Low (Slate)')),
                ],
                onChanged: (val) {
                  if (val != null) setDlgState(() => priority = val);
                },
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                final text = titleCtrl.text.trim();
                if (text.isEmpty) return;
                Navigator.pop(ctx);

                final newNodeId =
                    'node_${DateTime.now().millisecondsSinceEpoch}';
                final newNode = MandalaNode(
                  id: newNodeId,
                  label: text,
                  parent: parentId,
                  type: priority,
                  details: detailsCtrl.text.trim(),
                );

                _activeCustomMandala!.nodes.add(newNode);
                await CustomMandalaService.saveCustomMandala(
                  _activeCustomMandala!,
                );
                setState(() {
                  _rebuildEngine(targetMandalaId: _currentMandalaId);
                });
              },
              child: const Text('Add Petal'),
            ),
          ],
        ),
      ),
    );
  }

  void _showLinkTaskDialog({required String parentId}) {
    final tasks = widget.initialTasks ?? context.read<TaskProvider>().tasks;
    final searchCtrl = TextEditingController();
    String query = '';

    showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDlgState) {
          final filtered = tasks
              .where((t) => t.title.toLowerCase().contains(query.toLowerCase()))
              .toList();

          return AlertDialog(
            title: const Text('Link GTasks Task to Petal'),
            content: SizedBox(
              width: 400,
              height: 400,
              child: Column(
                children: [
                  TextField(
                    controller: searchCtrl,
                    decoration: const InputDecoration(
                      prefixIcon: Icon(Icons.search),
                      hintText: 'Search tasks...',
                      border: OutlineInputBorder(),
                    ),
                    onChanged: (val) => setDlgState(() => query = val),
                  ),
                  const SizedBox(height: 10),
                  Expanded(
                    child: ListView.builder(
                      itemCount: filtered.length,
                      itemBuilder: (context, index) {
                        final task = filtered[index];
                        return ListTile(
                          title: Text(
                            task.title,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          subtitle: Text(task.listTitle ?? 'Default List'),
                          trailing: Icon(
                            task.isCompleted
                                ? Icons.check_circle
                                : Icons.circle_outlined,
                            size: 16,
                            color: task.isCompleted
                                ? Colors.green
                                : Colors.grey,
                          ),
                          onTap: () async {
                            Navigator.pop(ctx);
                            final newNode = MandalaNode(
                              id: 'link_${task.id}_${DateTime.now().millisecondsSinceEpoch}',
                              label: task.title,
                              parent: parentId,
                              type: task.isCompleted
                                  ? 'completed'
                                  : task.calculatedPriority.toLowerCase(),
                              details: task.description,
                              data: {'taskId': task.id},
                            );

                            _activeCustomMandala!.nodes.add(newNode);
                            await CustomMandalaService.saveCustomMandala(
                              _activeCustomMandala!,
                            );
                            setState(() {
                              _rebuildEngine(
                                targetMandalaId: _currentMandalaId,
                              );
                            });
                          },
                        );
                      },
                    ),
                  ),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Cancel'),
              ),
            ],
          );
        },
      ),
    );
  }

  Future<void> _deleteCustomNode(String nodeId) async {
    if (_activeCustomMandala == null) return;
    final Set<String> toRemove = {nodeId};

    // Cascade delete children
    bool changed = true;
    while (changed) {
      changed = false;
      for (final n in _activeCustomMandala!.nodes) {
        if (n.parent != null &&
            toRemove.contains(n.parent) &&
            !toRemove.contains(n.id)) {
          toRemove.add(n.id);
          changed = true;
        }
      }
    }

    _activeCustomMandala!.nodes.removeWhere((n) => toRemove.contains(n.id));
    await CustomMandalaService.saveCustomMandala(_activeCustomMandala!);
    setState(() {
      _selectedCellId = null;
      _rebuildEngine(targetMandalaId: _currentMandalaId);
    });
  }

  Future<void> _extractNodeAsNewMandala(Cell cell) async {
    if (_activeCustomMandala == null || cell.nodeId == null) return;
    final extracted = CustomMandalaService.extractSubMandala(
      source: _activeCustomMandala!,
      rootNodeId: cell.nodeId!,
    );
    await CustomMandalaService.saveCustomMandala(extracted);
    final updatedList = await CustomMandalaService.loadCustomMandalas();
    if (!mounted) return;
    setState(() {
      _customMandalas = updatedList;
      _activeCustomMandala = extracted;
      _currentMandalaId = extracted.id;
      _selectedCellId = null;
      _rebuildEngine();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(
          '✨ Extracted "${extracted.title}" as independent mandala!',
        ),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Future<void> _extractPillarFromTasks(Cell cell) async {
    final allTasks = context.read<TaskProvider>().allTasksUnfiltered;
    final tasks = widget.initialTasks != null && widget.initialTab == null
        ? widget.initialTasks!
        : _mandalaTab.filterTasks(allTasks);
    final rawLabel = cell.label?.full ?? cell.id;
    final pillarName = rawLabel.replaceAll(RegExp(r'\s*\(\d+\)$'), '').trim();

    List<TaskItem> matchingTasks = tasks.where((t) {
      if (t.spaces.containsKey(pillarName)) return true;
      if (t.listTitle == pillarName) return true;
      if (t.allTags.contains(pillarName.replaceFirst('#', ''))) return true;
      return false;
    }).toList();

    if (matchingTasks.isEmpty) {
      matchingTasks = tasks.take(8).toList();
    }

    final extracted = CustomMandalaService.extractFromTasks(
      title: '$pillarName Mandala',
      centerGoal: pillarName,
      tasks: matchingTasks,
      geometry: _forcedGeometry ?? GeometryId.padma,
    );
    await CustomMandalaService.saveCustomMandala(extracted);
    final updatedList = await CustomMandalaService.loadCustomMandalas();
    if (!mounted) return;
    setState(() {
      _customMandalas = updatedList;
      _activeCustomMandala = extracted;
      _currentMandalaId = extracted.id;
      _selectedCellId = null;
      _rebuildEngine();
    });
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('✨ Created new focused mandala for "$pillarName"!'),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  Color _getPriorityColor(String? type) {
    final t = type?.toLowerCase() ?? '';
    if (t == 'critical') return Colors.redAccent;
    if (t == 'high') return Colors.orangeAccent;
    if (t == 'completed') return Colors.greenAccent;
    if (t == 'low') return Colors.blueGrey;
    return Colors.cyan;
  }

  void _updateMandalaTab(TaskTab newTab) {
    setState(() {
      _mandalaTab = newTab;
      _rebuildEngine(targetMandalaId: _currentMandalaId);
    });
    if (widget.isEmbedded) {
      context.read<TaskProvider>().updateActiveTab(newTab);
    }
  }

  void _openFilterModal() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (_) => TaskFilterModal(
        initialTab: _mandalaTab,
        onApplyTab: (newTab) {
          _updateMandalaTab(newTab);
        },
      ),
    );
  }

  void _openAsBrowserTab() {
    final provider = context.read<TaskProvider>();
    final tabTitle = _mandalaTab.title.isNotEmpty && _mandalaTab.title != 'Mandala' && _mandalaTab.title != 'All Tasks'
        ? '${_mandalaTab.title} (Mandala)'
        : 'Mandala';
    final newTab = _mandalaTab.copyWith(
      id: 'tab_${DateTime.now().millisecondsSinceEpoch}',
      title: tabTitle,
      viewMode: 'mandala',
      iconCodePoint: Icons.hub_outlined.codePoint,
    );
    provider.addTab(newTab);
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text('✨ Opened "$tabTitle" as a new tab!'),
        behavior: SnackBarBehavior.floating,
        action: SnackBarAction(
          label: 'Switch to Tab',
          onPressed: () {
            if (Navigator.canPop(context)) {
              Navigator.pop(context);
            }
            provider.switchToTab(provider.tabs.length - 1);
          },
        ),
      ),
    );
  }

  Widget _buildFilterChipsBar(ThemeData theme) {
    if (!_mandalaTab.hasActiveFilters) return const SizedBox.shrink();

    return Container(
      height: 32,
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.25),
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outlineVariant.withValues(alpha: 0.3),
          ),
        ),
      ),
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
        child: Row(
          children: [
            ..._mandalaTab.selectedLists.map((l) => _buildMicroPill(
                  label: 'List: $l',
                  icon: Icons.folder,
                  onDeleted: () {
                    final next = Set<String>.from(_mandalaTab.selectedLists)..remove(l);
                    _updateMandalaTab(_mandalaTab.copyWith(selectedLists: next));
                  },
                  color: Colors.blueAccent,
                )),
            ..._mandalaTab.selectedTags.map((t) => _buildMicroPill(
                  label: '#$t',
                  icon: Icons.tag,
                  onDeleted: () {
                    final next = Set<String>.from(_mandalaTab.selectedTags)..remove(t);
                    _updateMandalaTab(_mandalaTab.copyWith(selectedTags: next));
                  },
                  color: Colors.teal,
                )),
            if (_mandalaTab.selectedSpace != null)
              _buildMicroPill(
                label: _mandalaTab.selectedSubspace != null
                    ? '${_mandalaTab.selectedSpace} › ${_mandalaTab.selectedSubspace}'
                    : _mandalaTab.selectedSpace!,
                icon: Icons.rocket_launch,
                onDeleted: () {
                  _updateMandalaTab(_mandalaTab.copyWith(clearSpace: true));
                },
                color: Colors.deepPurpleAccent,
              ),
            if (_mandalaTab.selectedPriority != null)
              _buildMicroPill(
                label: 'Priority: ${_mandalaTab.selectedPriority}',
                icon: Icons.flag,
                onDeleted: () {
                  _updateMandalaTab(_mandalaTab.copyWith(clearPriority: true));
                },
                color: Colors.deepOrangeAccent,
              ),
            if (_mandalaTab.statusFilter != 'pending')
              _buildMicroPill(
                label: 'Status: ${_mandalaTab.statusFilter}',
                icon: Icons.check_circle_outline,
                onDeleted: () {
                  _updateMandalaTab(_mandalaTab.copyWith(statusFilter: 'pending'));
                },
                color: Colors.indigoAccent,
              ),
            if (_mandalaTab.hideRecurring)
              _buildMicroPill(
                label: 'Hide Recurring',
                icon: Icons.redo_outlined,
                onDeleted: () {
                  _updateMandalaTab(_mandalaTab.copyWith(hideRecurring: false));
                },
                color: Colors.orange,
              ),
            ..._mandalaTab.hiddenLists.map((hl) => _buildMicroPill(
                  label: 'Hide: $hl',
                  icon: Icons.visibility_off,
                  onDeleted: () {
                    final next = Set<String>.from(_mandalaTab.hiddenLists)..remove(hl);
                    _updateMandalaTab(_mandalaTab.copyWith(hiddenLists: next));
                  },
                  color: Colors.redAccent,
                )),
            ..._mandalaTab.hiddenTags.map((ht) => _buildMicroPill(
                  label: 'Hide: #$ht',
                  icon: Icons.visibility_off,
                  onDeleted: () {
                    final next = Set<String>.from(_mandalaTab.hiddenTags)..remove(ht);
                    _updateMandalaTab(_mandalaTab.copyWith(hiddenTags: next));
                  },
                  color: Colors.redAccent,
                )),
            if (_mandalaTab.dateRange != null)
              _buildMicroPill(
                label: '${_mandalaTab.dateField}: ${_mandalaTab.dateRange!.start.month}/${_mandalaTab.dateRange!.start.day} - ${_mandalaTab.dateRange!.end.month}/${_mandalaTab.dateRange!.end.day}',
                icon: Icons.date_range,
                onDeleted: () {
                  _updateMandalaTab(_mandalaTab.copyWith(clearDateRange: true));
                },
                color: Colors.indigoAccent,
              ),
            InkWell(
              borderRadius: BorderRadius.circular(10),
              onTap: () {
                _updateMandalaTab(_mandalaTab.copyWith(
                  selectedLists: {},
                  selectedTags: {},
                  clearSpace: true,
                  clearPriority: true,
                  statusFilter: 'pending',
                  hideRecurring: false,
                  hiddenLists: {},
                  hiddenTags: {},
                  clearDateRange: true,
                ));
              },
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                child: Text(
                  'Clear All',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.bold,
                    color: theme.colorScheme.error,
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMicroPill({
    required String label,
    required IconData icon,
    required VoidCallback onDeleted,
    Color? color,
  }) {
    final pillColor = color ?? Colors.blueAccent;
    return Container(
      margin: const EdgeInsets.only(right: 6),
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: pillColor.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: pillColor.withValues(alpha: 0.35),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: pillColor),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: pillColor,
            ),
          ),
          const SizedBox(width: 4),
          GestureDetector(
            onTap: onDeleted,
            child: Icon(Icons.close_rounded, size: 13, color: pillColor),
          ),
        ],
      ),
    );
  }

  Widget _buildGroupingButton() {
    return PopupMenuButton<String>(
      icon: const Icon(Icons.filter_vintage_outlined),
      tooltip: 'Grouping & Custom Mandalas',
      onSelected: (action) async {
        if (action == 'new_custom') {
          final custom = await showDialog<CustomMandala>(
            context: context,
            builder: (_) => CustomMandalaDialog(
              taskProvider: context.read<TaskProvider>(),
            ),
          );
          if (custom != null) {
            await _loadCustomMandalas();
            setState(() {
              _activeCustomMandala = custom;
              _rebuildEngine();
            });
          }
          return;
        }

        if (action.startsWith('custom:')) {
          final id = action.substring(7);
          final found = _customMandalas.firstWhere((m) => m.id == id);
          setState(() {
            _activeCustomMandala = found;
            _rebuildEngine();
          });
          return;
        }

        // Standard Projections
        setState(() {
          _activeCustomMandala = null;
          if (action == 'spaces') {
            _grouping = MandalaGrouping.spaces;
          } else if (action == 'lists') {
            _grouping = MandalaGrouping.lists;
          } else if (action == 'tags') {
            _grouping = MandalaGrouping.tags;
          } else if (action == 'priorities') {
            _grouping = MandalaGrouping.priorities;
          } else if (action == 'mandalachart') {
            _grouping = MandalaGrouping.mandalachart;
          }
          _rebuildEngine();
        });
      },
      itemBuilder: (context) {
        final List<PopupMenuEntry<String>> items = [
          const PopupMenuItem(
            enabled: false,
            child: Text(
              'STANDARDS PERSPECTIVES',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
          PopupMenuItem(
            value: 'spaces',
            child: Row(
              children: [
                const Icon(Icons.folder_copy_outlined, size: 18),
                const SizedBox(width: 8),
                const Text('📂 By Spaces & Sub-spaces'),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.spaces)
                  const Spacer(),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.spaces)
                  const Icon(Icons.check, size: 16),
              ],
            ),
          ),
          PopupMenuItem(
            value: 'lists',
            child: Row(
              children: [
                const Icon(Icons.format_list_bulleted, size: 18),
                const SizedBox(width: 8),
                const Text('📋 By Task Lists'),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.lists)
                  const Spacer(),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.lists)
                  const Icon(Icons.check, size: 16),
              ],
            ),
          ),
          PopupMenuItem(
            value: 'tags',
            child: Row(
              children: [
                const Icon(Icons.label_outline, size: 18),
                const SizedBox(width: 8),
                const Text('🏷️ By Tags & Topics'),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.tags)
                  const Spacer(),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.tags)
                  const Icon(Icons.check, size: 16),
              ],
            ),
          ),
          PopupMenuItem(
            value: 'priorities',
            child: Row(
              children: [
                const Icon(Icons.priority_high, size: 18),
                const SizedBox(width: 8),
                const Text('🎯 By Priority Urgency'),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.priorities)
                  const Spacer(),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.priorities)
                  const Icon(Icons.check, size: 16),
              ],
            ),
          ),
          PopupMenuItem(
            value: 'mandalachart',
            child: Row(
              children: [
                const Icon(Icons.hub_outlined, size: 18),
                const SizedBox(width: 8),
                const Text('☸️ 9×9 Goal Mandalachart'),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.mandalachart)
                  const Spacer(),
                if (_activeCustomMandala == null &&
                    _grouping == MandalaGrouping.mandalachart)
                  const Icon(Icons.check, size: 16),
              ],
            ),
          ),
          const PopupMenuDivider(),
          const PopupMenuItem(
            enabled: false,
            child: Text(
              'MY CUSTOM MANDALAS',
              style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold),
            ),
          ),
        ];

        for (final cm in _customMandalas) {
          final isCurrent = _activeCustomMandala?.id == cm.id;
          items.add(
            PopupMenuItem(
              value: 'custom:${cm.id}',
              child: Row(
                children: [
                  const Icon(
                    Icons.auto_awesome,
                    size: 18,
                    color: Colors.amber,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      cm.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  if (isCurrent) const Icon(Icons.check, size: 16),
                ],
              ),
            ),
          );
        }

        items.add(const PopupMenuDivider());
        items.add(
          const PopupMenuItem(
            value: 'new_custom',
            child: Row(
              children: [
                Icon(
                  Icons.add_circle_outline,
                  color: Colors.blueAccent,
                  size: 18,
                ),
                SizedBox(width: 8),
                Text(
                  '+ Create Custom Mandala',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: Colors.blueAccent,
                  ),
                ),
              ],
            ),
          ),
        );

        return items;
      },
    );
  }

  Widget _buildNestingButton() {
    return PopupMenuButton<MandalaNestingMode>(
      icon: Icon(
        _nestingMode == MandalaNestingMode.hierarchicalPortals
            ? Icons.account_tree_outlined
            : (_nestingMode == MandalaNestingMode.flat
                  ? Icons.circle_outlined
                  : Icons.layers_outlined),
      ),
      tooltip: 'Nesting Mode',
      initialValue: _nestingMode,
      onSelected: (mode) {
        setState(() {
          _nestingMode = mode;
          _rebuildEngine();
        });
      },
      itemBuilder: (context) => const [
        PopupMenuItem(
          value: MandalaNestingMode.hierarchicalPortals,
          child: Text('🌀 Hierarchical Portals (Deep Drill-down)'),
        ),
        PopupMenuItem(
          value: MandalaNestingMode.adaptive,
          child: Text('🌿 Adaptive Budget (Auto-Portals)'),
        ),
        PopupMenuItem(
          value: MandalaNestingMode.flat,
          child: Text('🌐 Flat Single Canvas (No Portals)'),
        ),
      ],
    );
  }

  Widget _buildGeometryButton() {
    return PopupMenuButton<GeometryId?>(
      icon: const Icon(Icons.shape_line_outlined),
      tooltip: 'Mandala Geometry',
      initialValue: _forcedGeometry,
      onSelected: (geom) {
        setState(() {
          _forcedGeometry = geom;
          _rebuildEngine(targetMandalaId: _currentMandalaId);
        });
      },
      itemBuilder: (context) => const [
        PopupMenuItem(
          value: null,
          child: Text('✨ Auto-Suggest Geometry'),
        ),
        PopupMenuItem(
          value: GeometryId.padma,
          child: Text('🌸 Padma (Lotus)'),
        ),
        PopupMenuItem(
          value: GeometryId.chakra,
          child: Text('☸️ Chakra (Wheel)'),
        ),
        PopupMenuItem(
          value: GeometryId.bhupura,
          child: Text('🏛️ Bhupura (Temple Gate)'),
        ),
        PopupMenuItem(
          value: GeometryId.sriyantra,
          child: Text('🔺 Sri Yantra (43 Triangles)'),
        ),
      ],
    );
  }

  Widget _buildThemeButton() {
    return PopupMenuButton<MandalaThemePalette>(
      icon: const Icon(Icons.palette_outlined),
      tooltip: 'Sacred Color Theme',
      initialValue: _activeTheme,
      onSelected: (theme) async {
        await _setTheme(theme);
      },
      itemBuilder: (context) => MandalaThemePalette.allThemes.map((theme) {
        final isCurrent = theme.id == _activeTheme.id;
        return PopupMenuItem<MandalaThemePalette>(
          value: theme,
          child: Row(
            children: [
              Text(theme.icon, style: const TextStyle(fontSize: 16)),
              const SizedBox(width: 8),
              Container(
                width: 14,
                height: 14,
                decoration: BoxDecoration(
                  color: theme.primary,
                  shape: BoxShape.circle,
                  border: Border.all(color: Colors.white, width: 1.5),
                ),
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  theme.name,
                  style: TextStyle(
                    fontWeight: isCurrent ? FontWeight.bold : FontWeight.normal,
                    color: isCurrent ? theme.primary : null,
                  ),
                ),
              ),
              if (isCurrent) const Icon(Icons.check, size: 16),
            ],
          ),
        );
      }).toList(),
    );
  }

  Widget _buildEmbeddedToolbar(ThemeData theme, bool isDark) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
      decoration: BoxDecoration(
        color: isDark ? _activeTheme.cardBg : const Color(0xFFF1F5F9),
        border: Border(
          bottom: BorderSide(
            color: theme.colorScheme.outlineVariant.withValues(alpha: 0.3),
          ),
        ),
      ),
      child: Row(
        children: [
          Icon(Icons.hub_outlined, size: 18, color: theme.colorScheme.primary),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              '${_layout.title} (${_layout.geometry.name.toUpperCase()} · ${_layout.cells.length})',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          ),
          Badge(
            isLabelVisible: _mandalaTab.activeFilterCount > 0,
            label: Text('${_mandalaTab.activeFilterCount}'),
            child: IconButton(
              icon: const Icon(Icons.filter_list, size: 20),
              visualDensity: VisualDensity.compact,
              tooltip: 'Mandala Filters',
              onPressed: _openFilterModal,
            ),
          ),
          _buildGroupingButton(),
          _buildNestingButton(),
          _buildGeometryButton(),
          _buildThemeButton(),
          IconButton(
            icon: const Icon(Icons.list_alt_rounded, size: 20),
            visualDensity: VisualDensity.compact,
            tooltip: 'Switch to Task List View',
            onPressed: () {
              final p = context.read<TaskProvider>();
              if (widget.isEmbedded) {
                p.setTabViewMode(p.activeTabIndex, null);
              } else if (Navigator.canPop(context)) {
                Navigator.pop(context);
              } else {
                p.setTabViewMode(p.activeTabIndex, null);
              }
            },
          ),
        ],
      ),
    );
  }

  Widget _buildBreadcrumbs(ThemeData theme, bool isDark, List<String> crumbs) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      color: isDark ? _activeTheme.cardBg : const Color(0xFFF1F5F9),
      child: SizedBox(
        height: 32,
        child: ListView.separated(
          scrollDirection: Axis.horizontal,
          itemCount: crumbs.length,
          separatorBuilder: (context, index) => const Padding(
            padding: EdgeInsets.symmetric(horizontal: 4),
            child: Icon(
              Icons.chevron_right,
              size: 16,
              color: Colors.grey,
            ),
          ),
          itemBuilder: (context, index) {
            final id = crumbs[index];
            final part = _atlas.mandalas[id];
            final title = part?.title ?? id;
            final isCurrent = id == _currentMandalaId;

            return ActionChip(
              visualDensity: VisualDensity.compact,
              label: Text(
                title,
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: isCurrent
                      ? FontWeight.bold
                      : FontWeight.normal,
                  color: isCurrent
                      ? theme.colorScheme.primary
                      : theme.colorScheme.onSurface,
                ),
              ),
              onPressed: () => _switchMandala(id),
            );
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final List<String> crumbs = _layout.breadcrumb;

    final content = Column(
      children: [
        if (widget.isEmbedded)
          _buildEmbeddedToolbar(theme, isDark),
        _buildFilterChipsBar(theme),
        if (crumbs.length > 1)
          _buildBreadcrumbs(theme, isDark, crumbs),

        // Main Interactive Canvas
        Expanded(
          child: LayoutBuilder(
            builder: (context, constraints) {
              final canvasSize = Size(
                constraints.maxWidth,
                constraints.maxHeight,
              );

              return Stack(
                children: [
                  InteractiveViewer(
                    transformationController: _transformController,
                    minScale: 0.5,
                    maxScale: 6.0,
                    boundaryMargin: const EdgeInsets.all(300),
                    child: GestureDetector(
                      onTapUp: (details) => _handleTapUp(details, canvasSize),
                      child: CustomPaint(
                        size: canvasSize,
                        painter: MandalaPainter(
                          layout: _layout,
                          selectedCellId: _selectedCellId,
                          isDark: isDark,
                          primaryColor: _activeTheme.primary,
                          palette: _activeTheme,
                          pathCache: _pathCache,
                        ),
                      ),
                    ),
                  ),

                  // Reset Zoom Button
                  Positioned(
                    bottom: 16,
                    right: 16,
                    child: FloatingActionButton.small(
                      heroTag: 'mandala_reset_zoom',
                      tooltip: 'Reset Zoom & Center',
                      backgroundColor: isDark
                          ? const Color(0xFF1E293B)
                          : const Color(0xFFFFFFFF),
                      child: const Icon(Icons.center_focus_strong, size: 18),
                      onPressed: () {
                        _transformController.value = Matrix4.identity();
                      },
                    ),
                  ),

                  // Up Navigation Button if nested
                  if (crumbs.length > 1)
                    Positioned(
                      bottom: 16,
                      left: 16,
                      child: FloatingActionButton.extended(
                        heroTag: 'mandala_up',
                        icon: const Icon(Icons.arrow_upward, size: 18),
                        label: const Text('Up Level'),
                        onPressed: () {
                          final parentId = _atlas
                              .mandalas[_currentMandalaId]
                              ?.parentMandala;
                          if (parentId != null) _switchMandala(parentId);
                        },
                      ),
                    ),

                  // Custom Mandala Floating Action: Add Petal to Center
                  if (_activeCustomMandala != null)
                    Positioned(
                      top: 16,
                      right: 16,
                      child: FilledButton.tonalIcon(
                        icon: const Icon(Icons.add, size: 18),
                        label: const Text('Add Petal'),
                        onPressed: () {
                          _showAddCustomNodeDialog(
                            parentId: _currentMandalaId ?? 'center_goal',
                          );
                        },
                      ),
                    ),
                ],
              );
            },
          ),
        ),
      ],
    );

    if (widget.isEmbedded) {
      return Container(
        color: isDark ? _activeTheme.background : const Color(0xFFF8FAFC),
        child: content,
      );
    }

    return Scaffold(
      backgroundColor: isDark
          ? _activeTheme.background
          : const Color(0xFFF8FAFC),
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _layout.title,
              style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
            Text(
              '${_layout.geometry.name.toUpperCase()} · ${_layout.cells.length} cells · ${_nestingMode == MandalaNestingMode.hierarchicalPortals ? "Hierarchical Portals" : (_nestingMode == MandalaNestingMode.flat ? "Flat" : "Adaptive")}',
              style: TextStyle(
                fontSize: 11,
                color: theme.colorScheme.onSurfaceVariant,
              ),
            ),
          ],
        ),
        actions: [
          Badge(
            isLabelVisible: _mandalaTab.activeFilterCount > 0,
            label: Text('${_mandalaTab.activeFilterCount}'),
            child: IconButton(
              icon: const Icon(Icons.filter_list),
              tooltip: 'Mandala Filters',
              onPressed: _openFilterModal,
            ),
          ),
          IconButton(
            icon: const Icon(Icons.tab_outlined),
            tooltip: 'Open as Tab',
            onPressed: _openAsBrowserTab,
          ),
          _buildGroupingButton(),
          _buildNestingButton(),
          _buildGeometryButton(),
          _buildThemeButton(),
        ],
      ),
      body: content,
    );
  }
}
