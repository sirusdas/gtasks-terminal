import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/models/account.dart';
import 'package:gtasks_app/api/microsoft_todo_direct_client.dart';
import 'package:gtasks_app/utils/notes_parser.dart';

void main() {
  group('GTasksAccount Provider Tests', () {
    test('Default account provider is google', () {
      final acc = GTasksAccount(id: 'personal', name: 'Personal Account');
      expect(acc.provider, equals('google'));
      expect(acc.isGoogle, isTrue);
      expect(acc.isMicrosoft, isFalse);
    });

    test('Microsoft account provider detection', () {
      final acc = GTasksAccount(
        id: 'outlook_work',
        name: 'Work (MS)',
        email: 'user@outlook.com',
        provider: 'microsoft',
      );
      expect(acc.provider, equals('microsoft'));
      expect(acc.isMicrosoft, isTrue);
      expect(acc.isGoogle, isFalse);
      expect(acc.email, equals('user@outlook.com'));

      final json = acc.toJson();
      expect(json['provider'], equals('microsoft'));
      expect(json['email'], equals('user@outlook.com'));

      final fromJson = GTasksAccount.fromJson(json);
      expect(fromJson.isMicrosoft, isTrue);
      expect(fromJson.name, equals('Work (MS)'));
    });
  });

  group('MicrosoftTodoDirectClient Priority Calculations', () {
    test('Calculates critical priority from tags', () {
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['critical']), equals('critical'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['[******]']), equals('critical'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['p0']), equals('critical'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['urgent']), equals('critical'));
    });

    test('Calculates high priority from tags', () {
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['high']), equals('high'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['[****]']), equals('high'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['p1']), equals('high'));
    });

    test('Calculates medium and low priority from tags', () {
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['medium']), equals('medium'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['p2']), equals('medium'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['low']), equals('low'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['p3']), equals('low'));
      expect(MicrosoftTodoDirectClient.calculatePriorityFromTags(['someday']), equals('low'));
    });

    test('Uses fallback priority when no priority tags are found', () {
      expect(
        MicrosoftTodoDirectClient.calculatePriorityFromTags(['work', 'backend'], fallback: 'high'),
        equals('high'),
      );
      expect(
        MicrosoftTodoDirectClient.calculatePriorityFromTags([], fallback: 'low'),
        equals('low'),
      );
      expect(
        MicrosoftTodoDirectClient.calculatePriorityFromTags([], fallback: 'medium'),
        equals('medium'),
      );
    });
  });

  group('Microsoft To Do Notes and Metadata Parsing', () {
    test('Parses Microsoft To Do task body containing tags and spaces', () {
      const msBody = '''
Prepare Q4 report for leadership
---
[finance][urgent]
---{spaces}
{spa::work:(sub::accounting)}
''';

      final parsed = NotesParser.splitNotesAndMetadata(msBody);
      expect(parsed.cleanNotes, equals('Prepare Q4 report for leadership'));
      expect(parsed.tags, containsAll(['finance', 'urgent']));
      expect(parsed.spaces.containsKey('work'), isTrue);
      expect(parsed.spaces['work'], contains('accounting'));

      final prio = MicrosoftTodoDirectClient.calculatePriorityFromTags(parsed.tags, fallback: 'medium');
      expect(prio, equals('critical'));
    });
  });
}
