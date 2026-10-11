import 'package:flutter_test/flutter_test.dart';
import 'package:gtasks_app/utils/notes_parser.dart';

void main() {
  group('NotesParser Tests', () {
    test('Pure bracket tags are stripped from clean notes', () {
      const raw = '[work][urgent]';
      final parsed = NotesParser.splitNotesAndTags(raw);
      expect(parsed.cleanNotes, '');
      expect(parsed.tags, equals(['work', 'urgent']));
    });

    test('Standard divider format is parsed cleanly', () {
      const raw = 'Please review the client proposal.\n\n---\n[work][client]';
      final parsed = NotesParser.splitNotesAndTags(raw);
      expect(parsed.cleanNotes, 'Please review the client proposal.');
      expect(parsed.tags, equals(['work', 'client']));
    });

    test('Notes without tags return as clean notes', () {
      const raw = 'Just a regular note without tags';
      final parsed = NotesParser.splitNotesAndTags(raw);
      expect(parsed.cleanNotes, 'Just a regular note without tags');
      expect(parsed.tags, isEmpty);
    });

    test('combineNotesAndTags constructs proper divider format', () {
      final combined = NotesParser.combineNotesAndTags(
        'Call contractor',
        ['home', 'urgent'],
      );
      expect(combined, 'Call contractor\n\n---\n[home][urgent]');
    });
  });
}
