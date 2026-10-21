import 'package:flutter/material.dart';
import '../../providers/task_provider.dart';
import 'mandala_types.dart';
import 'custom_mandala_service.dart';

class CustomMandalaDialog extends StatefulWidget {
  final TaskProvider taskProvider;

  const CustomMandalaDialog({super.key, required this.taskProvider});

  @override
  State<CustomMandalaDialog> createState() => _CustomMandalaDialogState();
}

class _CustomMandalaDialogState extends State<CustomMandalaDialog> {
  final _formKey = GlobalKey<FormState>();
  final TextEditingController _titleController = TextEditingController();
  final TextEditingController _goalController = TextEditingController();

  String _template = 'harada_9x9'; // 'harada_9x9', 'bhupura_4gates', 'blank'
  GeometryId _geometry = GeometryId.chakra;
  String _seedSource = 'template'; // 'template', 'spaces', 'lists', 'tags'

  @override
  void initState() {
    super.initState();
    _titleController.text = 'My Focus Mandalachart';
    _goalController.text = 'Master My Core Objective';
  }

  @override
  void dispose() {
    _titleController.dispose();
    _goalController.dispose();
    super.dispose();
  }

  void _createAndSave() async {
    if (!_formKey.currentState!.validate()) return;

    final String title = _titleController.text.trim();
    final String goal = _goalController.text.trim();

    List<String>? seededPillars;
    if (_seedSource == 'spaces') {
      final spaces = widget.taskProvider.spacesWithCounts.keys.toList();
      if (spaces.isNotEmpty) {
        seededPillars = spaces.take(8).toList();
      }
    } else if (_seedSource == 'lists') {
      final lists = widget.taskProvider.listsWithCounts.keys.toList();
      if (lists.isNotEmpty) {
        seededPillars = lists.take(8).toList();
      }
    } else if (_seedSource == 'tags') {
      final tags = widget.taskProvider.tagsWithCounts.keys.toList();
      if (tags.isNotEmpty) {
        seededPillars = tags.take(8).map((t) => '#$t').toList();
      }
    }

    CustomMandala mandala;
    if (_template == 'harada_9x9') {
      mandala = CustomMandalaService.createHarada9x9Template(
        title: title,
        centralGoal: goal,
        pillars: seededPillars,
      );
    } else if (_template == 'bhupura_4gates') {
      mandala = CustomMandalaService.createBhupura4GatesTemplate(
        title: title,
        centralFocus: goal,
        gateNames: seededPillars?.take(4).toList(),
      );
    } else {
      mandala = CustomMandalaService.createBlankTemplate(
        title: title,
        centralGoal: goal,
        geometry: _geometry,
      );
    }

    await CustomMandalaService.saveCustomMandala(mandala);

    if (mounted) {
      Navigator.pop(context, mandala);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Dialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
      child: Container(
        width: 480,
        padding: const EdgeInsets.all(24),
        child: Form(
          key: _formKey,
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.all(8),
                      decoration: BoxDecoration(
                        color: theme.colorScheme.primary.withValues(
                          alpha: 0.15,
                        ),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Icon(
                        Icons.hub_outlined,
                        color: theme.colorScheme.primary,
                        size: 24,
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Create Custom Mandala',
                            style: theme.textTheme.titleMedium?.copyWith(
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          Text(
                            'Design your radial focus and goal hierarchy',
                            style: theme.textTheme.bodySmall?.copyWith(
                              color: theme.colorScheme.onSurfaceVariant,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 20),

                // Title Input
                TextFormField(
                  controller: _titleController,
                  decoration: const InputDecoration(
                    labelText: 'Mandala Title',
                    hintText: 'e.g., 2026 Core Goals, Q4 Product Launch',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  validator: (v) => v == null || v.trim().isEmpty
                      ? 'Please enter a title'
                      : null,
                ),
                const SizedBox(height: 14),

                // Central Bindu Input
                TextFormField(
                  controller: _goalController,
                  decoration: const InputDecoration(
                    labelText: 'Central Core Bindu (Goal / Objective)',
                    hintText: 'e.g., Master Flutter Architecture',
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  validator: (v) => v == null || v.trim().isEmpty
                      ? 'Please enter a central goal'
                      : null,
                ),
                const SizedBox(height: 18),

                // Template Selector
                Text(
                  'Structure Template',
                  style: theme.textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: _template,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: 'harada_9x9',
                      child: Text(
                        '☸️ 9×9 Harada Mandalachart (8 Pillars × 8 Actions)',
                      ),
                    ),
                    DropdownMenuItem(
                      value: 'bhupura_4gates',
                      child: Text(
                        '🏛️ Bhupura 4 Sacred Gateways (4 Life Domains)',
                      ),
                    ),
                    DropdownMenuItem(
                      value: 'blank',
                      child: Text('✨ Blank Custom Canvas'),
                    ),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _template = val);
                  },
                ),
                const SizedBox(height: 14),

                // Geometry Selector
                Text(
                  'Geometry Style',
                  style: theme.textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<GeometryId>(
                  initialValue: _geometry,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: GeometryId.chakra,
                      child: Text('☸️ Chakra (Radial Wheel)'),
                    ),
                    DropdownMenuItem(
                      value: GeometryId.padma,
                      child: Text('🌸 Padma (Concentric Lotus Petals)'),
                    ),
                    DropdownMenuItem(
                      value: GeometryId.bhupura,
                      child: Text('🏛️ Bhupura (Square Sacred Enclosure)'),
                    ),
                    DropdownMenuItem(
                      value: GeometryId.sriyantra,
                      child: Text('🔺 Sri Yantra (43 Triangles)'),
                    ),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _geometry = val);
                  },
                ),
                const SizedBox(height: 14),

                // Seed Source Selector
                Text(
                  'Seed Pillars / Petals From',
                  style: theme.textTheme.labelMedium?.copyWith(
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                DropdownButtonFormField<String>(
                  initialValue: _seedSource,
                  decoration: const InputDecoration(
                    border: OutlineInputBorder(),
                    isDense: true,
                  ),
                  items: [
                    const DropdownMenuItem(
                      value: 'template',
                      child: Text('Default Goal Archetype Pillars'),
                    ),
                    DropdownMenuItem(
                      value: 'spaces',
                      child: Text(
                        'My Existing Spaces (${widget.taskProvider.spacesWithCounts.length} available)',
                      ),
                    ),
                    DropdownMenuItem(
                      value: 'lists',
                      child: Text(
                        'My Existing Task Lists (${widget.taskProvider.listsWithCounts.length} available)',
                      ),
                    ),
                    DropdownMenuItem(
                      value: 'tags',
                      child: Text(
                        'My Top Tags (${widget.taskProvider.tagsWithCounts.length} available)',
                      ),
                    ),
                  ],
                  onChanged: (val) {
                    if (val != null) setState(() => _seedSource = val);
                  },
                ),
                const SizedBox(height: 24),

                // Actions
                Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  children: [
                    TextButton(
                      onPressed: () => Navigator.pop(context),
                      child: const Text('Cancel'),
                    ),
                    const SizedBox(width: 8),
                    FilledButton.icon(
                      icon: const Icon(Icons.check, size: 18),
                      label: const Text('Create Mandala'),
                      onPressed: _createAndSave,
                    ),
                  ],
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
