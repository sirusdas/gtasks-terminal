import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/utils/notes_parser.dart';

void main() {
  group('Space Parser Tests in Dart', () {
    test('Extract spaces with multiple sub-spaces', () {
      const raw = 'Meeting notes\n\n---{spaces}\n{spa::work:(sub::frontend,sub::backend)}';
      final spaces = NotesParser.extractSpaces(raw);
      expect(spaces['work'], equals(['frontend', 'backend']));
    });

    test('Extract spaces with empty sub-spaces and no parentheses', () {
      const raw1 = '---{spaces}\n{spa::personal:()}';
      final spaces1 = NotesParser.extractSpaces(raw1);
      expect(spaces1['personal'], equals([]));

      const raw2 = '---{spaces}\n{spa::home}';
      final spaces2 = NotesParser.extractSpaces(raw2);
      expect(spaces2['home'], equals([]));
    });

    test('Extract multiple spaces', () {
      const raw = '''
Project overview

---{spaces}
{spa::work:(sub::dev,sub::ops)}
{spa::learning:(sub::flutter)}
{spa::personal}
''';
      final spaces = NotesParser.extractSpaces(raw);
      expect(spaces['work'], equals(['dev', 'ops']));
      expect(spaces['learning'], equals(['flutter']));
      expect(spaces['personal'], equals([]));
    });

    test('Split notes and metadata with both tags and spaces', () {
      const raw = '''
Refactor authentication module

---
[security][p1]

---{spaces}
{spa::work:(sub::backend,sub::auth)}
''';
      final parsed = NotesParser.splitNotesAndMetadata(raw);
      expect(parsed.cleanNotes, equals('Refactor authentication module'));
      expect(parsed.tags, equals(['security', 'p1']));
      expect(parsed.spaces['work'], equals(['backend', 'auth']));
    });

    test('Round-trip combineNotesAndMetadata preserves clean text', () {
      const originalClean = 'Write quarterly report';
      final tags = ['work', 'q3'];
      final spaces = {
        'finance': ['planning', 'budget'],
        'executive': <String>[],
      };

      final formatted = NotesParser.combineNotesAndMetadata(
        originalClean,
        tags,
        spaces: spaces,
      );

      final parsed = NotesParser.splitNotesAndMetadata(formatted);
      expect(parsed.cleanNotes, equals(originalClean));
      expect(parsed.tags, equals(tags));
      expect(parsed.spaces['finance'], equals(['planning', 'budget']));
      expect(parsed.spaces['executive'], equals([]));
    });

    test('Handles malformed space tokens gracefully', () {
      const raw = '---{spaces}\n{spa::valid:(sub::ok)}\n{spa:::(sub::bad)}\n{not_a_space}';
      final spaces = NotesParser.extractSpaces(raw);
      expect(spaces.containsKey('valid'), isTrue);
      expect(spaces['valid'], equals(['ok']));
      expect(spaces.containsKey(''), isFalse);
    });

    test('Clean notes retains pure notes when no dividers exist', () {
      const raw = 'Simple note with {spa::inline:(sub::test)} without divider';
      final parsed = NotesParser.splitNotesAndMetadata(raw);
      expect(parsed.spaces['inline'], equals(['test']));
    });

    test('parseSpacesInput and formatSpacesInput work seamlessly', () {
      const inputStr = 'work: frontend, backend | personal';
      final parsed = NotesParser.parseSpacesInput(inputStr);
      expect(parsed['work'], equals(['frontend', 'backend']));
      expect(parsed['personal'], equals([]));

      final formatted = NotesParser.formatSpacesInput(parsed);
      expect(formatted, equals('work: frontend, backend | personal'));
    });
  });
}
