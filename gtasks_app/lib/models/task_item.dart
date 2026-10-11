import '../utils/notes_parser.dart';

class TaskItem {
  final String id;
  final String title;
  final String description;
  final String status;
  final String? due;
  final String? listId;
  final String? listTitle;
  final String account;
  final List<String> tags;
  final String calculatedPriority;
  final String? createdAt;
  final String? completedAt;

  TaskItem({
    required this.id,
    required this.title,
    this.description = '',
    required this.status,
    this.due,
    this.listId,
    this.listTitle,
    this.account = 'default',
    this.tags = const [],
    this.calculatedPriority = 'normal',
    this.createdAt,
    this.completedAt,
  });

  bool get isCompleted => status.toLowerCase() == 'completed';

  String get cleanNotes => NotesParser.splitNotesAndTags(description).cleanNotes;

  List<String> get allTags {
    final extracted = NotesParser.splitNotesAndTags(description).tags;
    final set = <String>{...tags, ...extracted};
    return set.toList();
  }

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    List<String> parsedTags = [];
    if (json['tags'] is List) {
      parsedTags = (json['tags'] as List).map((e) => e.toString()).toList();
    }

    return TaskItem(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? 'Untitled Task',
      description: json['description']?.toString() ?? (json['notes']?.toString() ?? ''),
      status: json['status']?.toString() ?? 'needsAction',
      due: json['due']?.toString(),
      listId: json['list_id']?.toString(),
      listTitle: json['list_title']?.toString() ?? json['list_name']?.toString(),
      account: json['account']?.toString() ?? 'default',
      tags: parsedTags,
      calculatedPriority: json['calculated_priority']?.toString() ?? 'normal',
      createdAt: json['created_at']?.toString() ?? json['created']?.toString(),
      completedAt: json['completed_at']?.toString() ?? json['completed']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'notes': description,
      'status': status,
      'due': due,
      'list_id': listId,
      'account': account,
      'tags': tags,
    };
  }
}
