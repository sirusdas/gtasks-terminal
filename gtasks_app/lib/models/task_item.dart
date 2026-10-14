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
  final Map<String, List<String>> spaces;
  final String calculatedPriority;
  final String? createdAt;
  final String? completedAt;
  final bool isRecurring;
  final String? recurrenceType;
  final String cleanNotes;
  final List<String> allTags;

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
    Map<String, List<String>>? spaces,
    this.calculatedPriority = 'normal',
    this.createdAt,
    this.completedAt,
    this.isRecurring = false,
    this.recurrenceType,
    String? cleanNotes,
    List<String>? allTags,
  })  : cleanNotes = cleanNotes ?? NotesParser.splitNotesAndMetadata(description).cleanNotes,
        allTags = allTags ??
            (() {
              final extracted = NotesParser.splitNotesAndMetadata(description).tags;
              final set = <String>{...tags, ...extracted};
              return set.toList();
            })(),
        spaces = spaces ?? NotesParser.splitNotesAndMetadata(description).spaces;

  bool get isCompleted => status.toLowerCase() == 'completed';
  bool get hasSpaces => spaces.isNotEmpty;

  String get spacesDisplay {
    if (spaces.isEmpty) return '';
    return spaces.entries.map((e) {
      if (e.value.isEmpty) return e.key;
      return '${e.key} › ${e.value.join(', ')}';
    }).join(' | ');
  }

  factory TaskItem.fromJson(Map<String, dynamic> json) {
    Set<String> tagSet = {};
    if (json['tags'] is List) {
      tagSet.addAll((json['tags'] as List).map((e) => e.toString()));
    }
    if (json['hybrid_tags'] is Map) {
      final ht = json['hybrid_tags'] as Map;
      for (final key in ['bracket', 'hash', 'user']) {
        if (ht[key] is List) {
          tagSet.addAll((ht[key] as List).map((e) => e.toString()));
        }
      }
    }

    Map<String, List<String>> parsedSpaces = {};
    if (json['spaces'] is Map) {
      final map = json['spaces'] as Map;
      map.forEach((k, v) {
        if (v is List) {
          parsedSpaces[k.toString()] = v.map((e) => e.toString()).toList();
        } else {
          parsedSpaces[k.toString()] = [];
        }
      });
    }

    return TaskItem(
      id: json['id']?.toString() ?? '',
      title: json['title']?.toString() ?? 'Untitled Task',
      description: json['description']?.toString() ?? (json['notes']?.toString() ?? ''),
      status: json['status']?.toString() ?? 'pending',
      due: json['due']?.toString(),
      listId: json['list_id']?.toString() ?? json['tasklist_id']?.toString(),
      listTitle: json['list_title']?.toString() ?? json['list_name']?.toString(),
      account: json['account']?.toString() ?? 'default',
      tags: tagSet.toList(),
      spaces: parsedSpaces.isNotEmpty ? parsedSpaces : null,
      calculatedPriority: json['calculated_priority']?.toString() ?? (json['priority']?.toString() ?? 'medium'),
      createdAt: json['created_at']?.toString() ?? json['created']?.toString(),
      completedAt: json['completed_at']?.toString() ?? json['completed']?.toString(),
      isRecurring: json['is_recurring'] == true || json['is_recurring'] == 1,
      recurrenceType: json['recurrence_type']?.toString(),
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
      'list_title': listTitle,
      'account': account,
      'tags': tags,
      'spaces': spaces,
    };
  }

  TaskItem copyWith({
    String? id,
    String? title,
    String? description,
    String? status,
    String? due,
    String? listId,
    String? listTitle,
    String? account,
    List<String>? tags,
    Map<String, List<String>>? spaces,
    String? calculatedPriority,
    String? createdAt,
    String? completedAt,
    bool? isRecurring,
    String? recurrenceType,
  }) {
    return TaskItem(
      id: id ?? this.id,
      title: title ?? this.title,
      description: description ?? this.description,
      status: status ?? this.status,
      due: due ?? this.due,
      listId: listId ?? this.listId,
      listTitle: listTitle ?? this.listTitle,
      account: account ?? this.account,
      tags: tags ?? this.tags,
      spaces: spaces ?? this.spaces,
      calculatedPriority: calculatedPriority ?? this.calculatedPriority,
      createdAt: createdAt ?? this.createdAt,
      completedAt: completedAt ?? this.completedAt,
      isRecurring: isRecurring ?? this.isRecurring,
      recurrenceType: recurrenceType ?? this.recurrenceType,
    );
  }
}
