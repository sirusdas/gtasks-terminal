class ReportMetric {
  final String label;
  final String value;

  ReportMetric({required this.label, required this.value});
}

class ReportResult {
  final String reportType;
  final int totalCount;
  final double averagePerDay;
  final List<Map<String, dynamic>> items;

  ReportResult({
    required this.reportType,
    required this.totalCount,
    required this.averagePerDay,
    required this.items,
  });

  factory ReportResult.fromJson(String type, Map<String, dynamic> json) {
    final completed = (json['completed_tasks'] as List?) ?? [];
    final total = json['total_completed'] ?? (json['total_tasks'] ?? completed.length);
    final avg = (json['average_per_day'] is num)
        ? (json['average_per_day'] as num).toDouble()
        : 0.0;

    return ReportResult(
      reportType: type,
      totalCount: total is int ? total : int.tryParse(total.toString()) ?? 0,
      averagePerDay: avg,
      items: completed.map((e) => e as Map<String, dynamic>).toList(),
    );
  }
}
