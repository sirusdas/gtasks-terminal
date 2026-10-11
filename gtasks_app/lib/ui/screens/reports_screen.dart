import 'package:flutter/material.dart';
import '../../api/api_client.dart';

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
  Map<String, dynamic>? _reportData;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isLoading = true);
    try {
      final types = await widget.apiClient.fetchReportTypes();
      _reportTypes = types;
      await _runReport(_selectedReport);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  Future<void> _runReport(String type) async {
    setState(() {
      _isLoading = true;
      _selectedReport = type;
      _error = null;
    });

    try {
      final data = await widget.apiClient.generateReport(type);
      setState(() => _reportData = data);
    } catch (e) {
      setState(() => _error = e.toString());
    } finally {
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Reports & Velocity'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _runReport(_selectedReport),
          ),
        ],
      ),
      body: Column(
        children: [
          // Report Selector Carousel / Dropdown
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            child: Card(
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              child: Padding(
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: DropdownButtonHideUnderline(
                  child: DropdownButton<String>(
                    isExpanded: true,
                    value: _reportTypes.containsKey(_selectedReport) ? _selectedReport : null,
                    hint: const Text('Select Report Type'),
                    items: _reportTypes.entries.map((e) {
                      final val = e.value as Map<String, dynamic>;
                      return DropdownMenuItem<String>(
                        value: e.key,
                        child: Text(val['name'] ?? e.key),
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

          if (_isLoading)
            const Expanded(
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    CircularProgressIndicator(),
                    SizedBox(height: 12),
                    Text('Calculating metrics & velocity...'),
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
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    childAspectRatio: 2.1,
                    children: [
                      _buildMetricCard(
                        'Total Tasks',
                        '${_reportData!['total_completed'] ?? _reportData!['total_tasks'] ?? (_reportData!['completed_tasks'] as List?)?.length ?? 0}',
                        Icons.check_circle_outline,
                        Colors.blueAccent,
                      ),
                      _buildMetricCard(
                        'Daily Velocity',
                        '${(_reportData!['average_per_day'] as num?)?.toStringAsFixed(1) ?? '0.0'}/day',
                        Icons.speed,
                        Colors.orangeAccent,
                      ),
                      _buildMetricCard(
                        'Days Analyzed',
                        '${_reportData!['days_analyzed'] ?? 30}',
                        Icons.date_range,
                        Colors.purpleAccent,
                      ),
                      _buildMetricCard(
                        'Status',
                        'Active',
                        Icons.trending_up,
                        Colors.green,
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Text('Data Breakdown', style: theme.textTheme.titleMedium),
                  const SizedBox(height: 10),
                  ...((_reportData!['completed_tasks'] as List?) ?? []).take(15).map((item) {
                    final task = item as Map<String, dynamic>;
                    return Card(
                      margin: const EdgeInsets.symmetric(vertical: 4),
                      child: ListTile(
                        dense: true,
                        leading: const Icon(Icons.task_alt, color: Colors.green),
                        title: Text(task['name'] ?? task['title'] ?? 'Task'),
                        subtitle: Text(
                          task['completed_at'] != null
                              ? 'Done: ${task['completed_at'].toString().substring(0, 10)}'
                              : (task['list_title'] ?? ''),
                        ),
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
