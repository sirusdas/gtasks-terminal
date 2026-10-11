class ParsedNotes {
  final String cleanNotes;
  final List<String> tags;

  ParsedNotes({required this.cleanNotes, required this.tags});
}

class NotesParser {
  static final RegExp _bracketRegex = RegExp(r'\[([^\]\r\n]+)\]');
  static final RegExp _invalidCharsRegex = RegExp(r'[{}\"\\:\r\n\t,]');
  static final RegExp _dividerRegex = RegExp(
    r'(?:^|\r?\n)[ \t]*---[ \t]*(?:\r?\n)((?:[ \t]*(?:\[[^\]\r\n]+\])[\s]*)+)$',
  );
  static final RegExp _pureTagsRegex = RegExp(r'^(?:[ \t]*(?:\[[^\]\r\n]+\])[ \t]*)+$');
  static final RegExp _trailingTagsRegex = RegExp(r'(?:\r?\n)+((?:[ \t]*(?:\[[^\]\r\n]+\])[ \t]*)+)$');

  static bool isValidTag(String tag) {
    final t = tag.trim();
    if (t.isEmpty || t.length > 40) return false;
    if (_invalidCharsRegex.hasMatch(t)) return false;
    return true;
  }

  static List<String> extractTags(String chunk) {
    final List<String> result = [];
    final matches = _bracketRegex.allMatches(chunk);
    for (final m in matches) {
      final tag = m.group(1)?.trim();
      if (tag != null && tag.isNotEmpty && isValidTag(tag) && !result.contains(tag)) {
        result.add(tag);
      }
    }
    return result;
  }

  /// Splits raw task notes into user-readable clean notes and extracted tags,
  /// stripping dividers (---) and bracket tags ([work][p1]).
  static ParsedNotes splitNotesAndTags(String? rawText) {
    if (rawText == null || rawText.isEmpty) {
      return ParsedNotes(cleanNotes: '', tags: []);
    }

    final str = rawText;

    // Case 1: Standard divider format (--- followed strictly by bracket tags at the end)
    final dividerMatch = _dividerRegex.firstMatch(str);
    if (dividerMatch != null) {
      final tagsGroup = dividerMatch.group(1) ?? '';
      final extracted = extractTags(tagsGroup);
      if (extracted.isNotEmpty) {
        final clean = str.substring(0, dividerMatch.start).replaceAll(RegExp(r'[\r\n]+$'), '');
        return ParsedNotes(cleanNotes: clean, tags: extracted);
      }
    }

    // Case 2: Pure bracket tags string (e.g. "[work][urgent]")
    if (_pureTagsRegex.hasMatch(str.trim())) {
      final extracted = extractTags(str);
      if (extracted.isNotEmpty) {
        return ParsedNotes(cleanNotes: '', tags: extracted);
      }
    }

    // Case 3: Trailing block of bracket tags preceded by newline(s)
    final trailingMatch = _trailingTagsRegex.firstMatch(str);
    if (trailingMatch != null) {
      final tagsGroup = trailingMatch.group(1) ?? '';
      final extracted = extractTags(tagsGroup);
      if (extracted.isNotEmpty) {
        final clean = str.substring(0, trailingMatch.start).replaceAll(RegExp(r'[\r\n]+$'), '');
        return ParsedNotes(cleanNotes: clean, tags: extracted);
      }
    }

    return ParsedNotes(cleanNotes: str, tags: []);
  }

  /// Combines clean user notes and tags using the standard '---' divider format.
  /// Format:
  /// `cleanNotes`
  ///
  /// `---`
  /// `[tag1][tag2]`
  static String combineNotesAndTags(String cleanNotes, List<String> tags) {
    final clean = cleanNotes.trim();
    final cleanTags = tags
        .map((t) => t.trim().replaceAll(RegExp(r'^[\[#]+|[\]]+$'), ''))
        .where((t) => t.isNotEmpty && isValidTag(t))
        .toSet()
        .toList();

    if (cleanTags.isEmpty) {
      return clean;
    }

    final tagsLine = cleanTags.map((t) => '[$t]').join('');

    if (clean.isEmpty) {
      return '---\n$tagsLine';
    }

    return '$clean\n\n---\n$tagsLine';
  }
}
