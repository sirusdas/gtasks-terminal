import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../api/api_client.dart';
import '../../models/task_item.dart';
import '../../providers/task_provider.dart';

class ReportsScreen extends StatefulWidget {
  final ApiClient apiClient;

  const ReportsScreen({super.key, required this.apiClient});

  @override
  State<ReportsScreen> createState() => _ReportsScreenState();
}

class _ReportsScreenState extends State<ReportsScreen> {
  bool _isLoading = false;
  Map<String, dynamic> _reportTypes = {};
  String _selectedReport = 'task_completion';
  String _selectedAccount = 'all';
  Map<String, dynamic>? _reportData;
  String? _error;

  static const Map<String, String> _builtinReportNames = {
    'task_completion': 'Task Completion & Velocity',
    'pending_tasks': 'Pending Tasks & Urgency',
    'task_distribution': 'Task & Tag Distribution',
    'completion_rate': 'Completion Rate Metrics',
    'overdue_tasks': 'Overdue Tasks Analysis',
    'future_timeline': 'Future Timeline & Schedule',
  };

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    final provider = context.read<TaskProvider>();
    _selectedAccount = provider.selectedAccount;

    try {
      final types = await widget.apiClient.fetchReportTypes();
      if (types.isNotEmpty) {
        _reportTypes = types;
      } else {
        _reportTypes = _builtinReportNames.map((k, v) => MapEntry(k, {'name': v}));
      }
    } catch (_) {
      _reportTypes = _builtinReportNames.map((k, v) => MapEntry(k, {'name': v}));
    }

    await _runReport(_selectedReport);
  }

  Future<void> _runReport(String type) async {
    setState(() {
      _isLoading = true;
      _selectedReport = type;
      _error = null;
    });

    final provider = context.read<TaskProvider>();

    try {
      // First attempt backend report generation
      final data = await widget.apiClient.generateReport(type, account: _selectedAccount);
      setState(() => _reportData = data);
    } catch (e) {
      // Fallback: Compute report locally from provider tasks for 100% resilience
      final localData = _computeLocalReport(type, provider.allTasksUnfiltered, _selectedAccount);
      setState(() {
        _reportData = localData;
        _error = null;
      });
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Map<String, dynamic> _computeLocalReport(String type, List<TaskItem> allTasks, String account) {
    final filtered = allTasks.where((t) {
      if (account != 'all' && t.account != account) return false;
      return true;
    }).toList();

    final completed = filtered.where((t) => t.isCompleted).toList();
    final pending = filtered.where((t) => !t.isCompleted).toList();

    final now = DateTime.now();
    final overdue = pending.where((t) {
      if (t.due == null || t.due!.isEmpty) return false;
      try {
        final d = DateTime.parse(t.due!);
        return d.isBefore(now);
      } catch (_) {
        return false;
      }
    }).toList();

    final Map<String, int> priorityDist = {};
    final Map<String, int> tagDist = {};
    final Map<String, int> listDist = {};

    for (final t in filtered) {
      final p = t.calculatedPriority.toLowerCase();
      priorityDist[p] = (priorityDist[p] ?? 0) + 1;

      final l = (t.listTitle != null && t.listTitle!.isNotEmpty) ? t.listTitle! : 'My Tasks';
      listDist[l] = (listDist[l] ?? 0) + 1;

      for (final tg in t.allTags) {
        if (tg.isNotEmpty) {
          tagDist[tg] = (tagDist[tg] ?? 0) + 1;
        }
      }
    }

    final total = filtered.length;
    final rate = total > 0 ? ((completed.length / total) * 100).round() : 0;
    final avgPerDay = (completed.length / 30.0);

    return {
      'report_type': type,
      'report_name': _builtinReportNames[type] ?? type,
      'total_tasks': total,
      'total_completed': completed.length,
      'total_pending': pending.length,
      'total_overdue': overdue.length,
      'completion_rate': rate,
      'average_per_day': avgPerDay,
      'priority_distribution': priorityDist,
      'tag_distribution': tagDist,
      'list_distribution': listDist,
      'completed_tasks': completed.map((t) => {
        'id': t.id,
        'title': t.title,
        'completed_at': t.completedAt ?? t.createdAt,
        'list_title': t.listTitle,
        'priority': t.calculatedPriority,
      }).toList(),
      'pending_tasks': pending.map((t) => {
        'id': t.id,
        'title': t.title,
        'due': t.due,
        'list_title': t.listTitle,
        'priority': t.calculatedPriority,
      }).toList(),
    };
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final provider = context.watch<TaskProvider>();
    final accounts = provider.accounts;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Reports & Analytics'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Report',
            onPressed: () => _runReport(_selectedReport),
          ),
        ],
      ),
      body: Column(
        children: [
          // Selectors Row (Report Type & Account Filter)
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Row(
              children: [
                // Report Type Dropdown
                Expanded(
                  flex: 3,
                  child: Card(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 12),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          isExpanded: true,
                          value: _reportTypes.containsKey(_selectedReport) ? _selectedReport : 'task_completion',
                          items: _reportTypes.entries.map((e) {
                            final val = e.value as Map<String, dynamic>;
                            final name = val['name']?.toString() ?? _builtinReportNames[e.key] ?? e.key;
                            return DropdownMenuItem<String>(
                              value: e.key,
                              child: Text(name, overflow: TextOverflow.ellipsis),
                            );
                          }).toList(),
                          onChanged: (val) {
                            if (val != null) _runReport(val);
                          },
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 8),
                // Account Filter
                Expanded(
                  flex: 2,
                  child: Card(
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 10),
                      child: DropdownButtonHideUnderline(
                        child: DropdownButton<String>(
                          isExpanded: true,
                          value: (accounts.any((a) => a.id == _selectedAccount) || _selectedAccount == 'all')
                              ? _selectedAccount
                              : 'all',
                          items: [
                            const DropdownMenuItem(value: 'all', child: Text('All Accounts')),
                            ...accounts.map(
                              (a) => DropdownMenuItem(value: a.id, child: Text(a.name, overflow: TextOverflow.ellipsis)),
                            ),
                          ],
                          onChanged: (val) {
                            if (val != null) {
                              setState(() => _selectedAccount = val);
                              _runReport(_selectedReport);
                            }
                          },
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),

          if (_isLoading)
            const Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 12),
                    Text('Analyzing velocity & performance metrics...'),
                  ],
                ),
              ),
            )
          else if (_error != null)
            Expanded(
              child: Center(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Text('Error: $_error', style: const TextStyle(color: Colors.red)),
                ),
              ),
            )
          else if (_reportData != null)
            Expanded(
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  // KPI Metric Grid
                  GridView.count(
                    crossAxisCount: 2,
                    crossAxisSpacing: 10,
                    mainAxisSpacing: 10,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    childAspectRatio: 2.2,
                    children: [
                      _buildMetricCard(
                        'Total Tasks',
                        '${_reportData!['total_tasks'] ?? _reportData!['total_completed'] ?? 0}',
                        Icons.inbox_outlined,
                        Colors.blueAccent,
                      ),
                      _buildMetricCard(
                        'Completed',
                        '${_reportData!['total_completed'] ?? (_reportData!['completed_tasks'] as List?)?.length ?? 0}',
                        Icons.check_circle_outline,
                        Colors.green,
                      ),
                      _buildMetricCard(
                        'Completion Rate',
                        '${_reportData!['completion_rate'] ?? 0}%',
                        Icons.pie_chart_outline,
                        Colors.purpleAccent,
                      ),
                      _buildMetricCard(
                        'Daily Velocity',
                        '${(_reportData!['average_per_day'] as num?)?.toStringAsFixed(1) ?? '0.0'}/day',
                        Icons.speed,
                        Colors.orangeAccent,
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),

                  // Priority & Distribution Breakdown Chips
                  if (_reportData!['priority_distribution'] != null &&
                      (_reportData!['priority_distribution'] as Map).isNotEmpty) ...[
                    Text('Priority Breakdown', style: theme.textTheme.titleSmall?.copyWith(fontWeight: FontWeight.bold)),
                    const SizedBox(height: 6),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: (_reportData!['priority_distribution'] as Map).entries.map((e) {
                        return Chip(
                          label: Text('${e.key.toString().toUpperCase()}: ${e.value}'),
                          visualDensity: VisualDensity.compact,
                        );
                      }).toList(),
                    ),
                    const SizedBox(height: 14),
                  ],

                  // Task List Breakdown
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Recent Tasks Activity', style: theme.textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      Text(
                        'Account: ${_selectedAccount == 'all' ? 'All' : _selectedAccount}',
                        style: theme.textTheme.bodySmall?.copyWith(color: theme.hintColor),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  ...((_reportData!['completed_tasks'] as List?) ??
                          (_reportData!['tasks'] as List?) ??
                          (_reportData!['pending_tasks'] as List?) ??
                          [])
                      .take(20)
                      .map((item) {
                    final task = item as Map<String, dynamic>;
                    final isDone = task['status'] == 'completed' || task['completed_at'] != null;
                    return Card(
                      margin: const EdgeInsets.symmetric(vertical: 4),
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: BorderSide(color: theme.colorScheme.outlineVariant.withValues(alpha: 0.5)),
                      ),
                      child: ListTile(
                        dense: true,
                        leading: Icon(
                          isDone ? Icons.check_circle : Icons.radio_button_unchecked,
                          color: isDone ? Colors.green : Colors.grey,
                        ),
                        title: Text(task['name'] ?? task['title'] ?? 'Task', style: const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: Text(
                          task['completed_at'] != null
                              ? 'Done: ${task['completed_at'].toString().substring(0, 10)}'
                              : (task['list_title'] ?? task['due'] ?? 'Pending'),
                        ),
                        trailing: (task['priority'] != null)
                            ? Chip(
                                label: Text(task['priority'].toString().toUpperCase(), style: const TextStyle(fontSize: 10)),
                                visualDensity: VisualDensity.compact,
                                padding: EdgeInsets.zero,
                              )
                            : null,
                      ),
                    );
                  }),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _buildMetricCard(String label, String value, IconData icon, Color color) {
    return Card(
      elevation: 0.5,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: color.withValues(alpha: 0.2)),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          children: [
            CircleAvatar(
              radius: 18,
              backgroundColor: color.withValues(alpha: 0.15),
              child: Icon(icon, color: color, size: 20),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    value,
                    style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                  ),
                  Text(
                    label,
                    style: const TextStyle(fontSize: 11, color: Colors.grey),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
