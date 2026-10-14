class ParsedNotes {
  final String cleanNotes;
  final List<String> tags;
  final Map<String, List<String>> spaces;

  ParsedNotes({
    required this.cleanNotes,
    required this.tags,
    this.spaces = const {},
  });
}

class NotesParser {
  static final RegExp _bracketRegex = RegExp(r'\[([^\]\r\n]+)\]');
  static final RegExp _invalidCharsRegex = RegExp(r'[{}\"\\:\r\n\t,]');
  static final RegExp _invalidSpaceCharsRegex = RegExp(r'[{}\"\\:\r\n\t,()]');

  static final RegExp _spacesDividerRegex = RegExp(
    r'(?:^|\r?\n)[ \t]*---[ \t]*\{spaces\}[ \t]*(?:\r?\n)([\s\S]*?)(?=(?:\r?\n[ \t]*---[ \t]*[^\r\n]*)|$)',
    caseSensitive: false,
  );

  static final RegExp _tagsDividerRegex = RegExp(
    r'(?:^|\r?\n)[ \t]*---[ \t]*(?:\r?\n)((?:[ \t]*(?:\[[^\]\r\n]+\])[\s]*)+)(?=(?:\r?\n[ \t]*---[ \t]*[^\r\n]*)|$)',
    caseSensitive: false,
  );

  static final RegExp _spaceItemRegex = RegExp(
    r'\{spa::([a-zA-Z0-9_\-\s]+?)(?::\(([^)]*)\))?\}',
    caseSensitive: false,
  );

  static final RegExp _pureTagsRegex = RegExp(r'^(?:[ \t]*(?:\[[^\]\r\n]+\])[ \t]*)+$');
  static final RegExp _trailingTagsRegex = RegExp(r'(?:\r?\n)+((?:[ \t]*(?:\[[^\]\r\n]+\])[ \t]*)+)$');
  static final RegExp _leftoverDividerRegex = RegExp(r'(?:^|\r?\n)[ \t]*---[ \t]*(?:\{spaces\})?[ \t]*$', multiLine: true);

  static bool isValidTag(String tag) {
    final t = tag.trim();
    if (t.isEmpty || t.length > 40) return false;
    if (_invalidCharsRegex.hasMatch(t)) return false;
    return true;
  }

  static bool isValidSpaceIdentifier(String name) {
    final t = name.trim();
    if (t.isEmpty || t.length > 50) return false;
    if (_invalidSpaceCharsRegex.hasMatch(t)) return false;
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

  /// Extracts spaces and their sub-spaces from text notes.
  /// Returns a `Map<String, List<String>>` e.g. `{'work': ['dev', 'ops'], 'personal': []}`
  static Map<String, List<String>> extractSpaces(String? text) {
    if (text == null || text.isEmpty) {
      return {};
    }

    final Map<String, List<String>> spaces = {};
    final dividerMatch = _spacesDividerRegex.firstMatch(text);
    final searchChunk = dividerMatch != null ? (dividerMatch.group(1) ?? '') : text;

    for (final match in _spaceItemRegex.allMatches(searchChunk)) {
      final rawSpace = match.group(1)?.trim() ?? '';
      if (!isValidSpaceIdentifier(rawSpace)) continue;

      final rawSubspaces = match.group(2) ?? '';
      final List<String> subspaces = [];

      if (rawSubspaces.trim().isNotEmpty) {
        for (final item in rawSubspaces.split(',')) {
          var sub = item.trim();
          if (sub.toLowerCase().startsWith('sub::')) {
            sub = sub.substring(5).trim();
          }
          if (sub.isNotEmpty && isValidSpaceIdentifier(sub) && !subspaces.contains(sub)) {
            subspaces.add(sub);
          }
        }
      }

      if (spaces.containsKey(rawSpace)) {
        for (final s in subspaces) {
          if (!spaces[rawSpace]!.contains(s)) {
            spaces[rawSpace]!.add(s);
          }
        }
      } else {
        spaces[rawSpace] = subspaces;
      }
    }

    return spaces;
  }

  /// Splits raw task notes into user-readable clean notes, extracted tags, and spaces,
  /// stripping metadata dividers (--- and ---{spaces}).
  static ParsedNotes splitNotesAndTags(String? rawText) {
    return splitNotesAndMetadata(rawText);
  }

  /// Full metadata splitter returning ParsedNotes
  static ParsedNotes splitNotesAndMetadata(String? rawText) {
    if (rawText == null || rawText.isEmpty) {
      return ParsedNotes(cleanNotes: '', tags: [], spaces: const {});
    }

    final str = rawText;
    final spaces = extractSpaces(str);

    // Extract tags
    List<String> tags = [];
    final tagDividerMatch = _tagsDividerRegex.firstMatch(str);
    if (tagDividerMatch != null) {
      tags = extractTags(tagDividerMatch.group(1) ?? '');
    } else {
      // Check trailing tags or pure tags
      final trailingMatch = _trailingTagsRegex.firstMatch(str);
      if (trailingMatch != null) {
        tags = extractTags(trailingMatch.group(1) ?? '');
      } else if (_pureTagsRegex.hasMatch(str.trim())) {
        tags = extractTags(str);
      } else {
        tags = extractTags(str);
      }
    }

    // Strip sections for clean notes
    var clean = str;
    clean = clean.replaceAll(_spacesDividerRegex, '');
    clean = clean.replaceAll(_tagsDividerRegex, '');

    // If pure tags or trailing tags matched without divider, strip them
    if (tagDividerMatch == null) {
      if (_pureTagsRegex.hasMatch(clean.trim())) {
        clean = '';
      } else {
        final trailingMatch = _trailingTagsRegex.firstMatch(clean);
        if (trailingMatch != null) {
          clean = clean.substring(0, trailingMatch.start);
        }
      }
    }

    // Clean leftover divider markers and trailing whitespace
    clean = clean.replaceAll(_leftoverDividerRegex, '');
    clean = clean.replaceAll(RegExp(r'[\r\n]+$'), '').trim();

    return ParsedNotes(
      cleanNotes: clean,
      tags: tags,
      spaces: spaces,
    );
  }

  /// Combines clean user notes and tags using the standard divider format.
  /// Also accepts optional [spaces].
  static String combineNotesAndTags(
    String cleanNotes,
    List<String> tags, {
    Map<String, List<String>>? spaces,
  }) {
    return combineNotesAndMetadata(cleanNotes, tags, spaces: spaces ?? const {});
  }

  /// Combines clean user notes, tags, and spaces into the canonical format:
  /// `cleanNotes`
  ///
  /// ---
  /// [tag1][tag2]
  ///
  /// ---{spaces}
  /// {spa::space1:(sub::sub1,sub::sub2)}
  /// {spa::space2}
  static String combineNotesAndMetadata(
    String cleanNotes,
    List<String> tags, {
    Map<String, List<String>> spaces = const {},
  }) {
    final clean = cleanNotes.trim();
    final List<String> sections = [];

    if (clean.isNotEmpty) {
      sections.add(clean);
    }

    final cleanTags = tags
        .map((t) => t.trim().replaceAll(RegExp(r'^[\[#]+|[\]]+$'), ''))
        .where((t) => t.isNotEmpty && isValidTag(t))
        .toSet()
        .toList();

    if (cleanTags.isNotEmpty) {
      final tagsLine = cleanTags.map((t) => '[$t]').join('');
      sections.add('---\n$tagsLine');
    }

    if (spaces.isNotEmpty) {
      final List<String> spaceLines = [];
      for (final entry in spaces.entries) {
        final spa = entry.key.trim();
        if (!isValidSpaceIdentifier(spa)) continue;

        final validSubs = entry.value
            .map((s) {
              var str = s.trim();
              if (str.toLowerCase().startsWith('sub::')) {
                str = str.substring(5).trim();
              }
              return str;
            })
            .where((s) => isValidSpaceIdentifier(s))
            .toSet()
            .toList();

        if (validSubs.isNotEmpty) {
          final subsFormatted = validSubs.map((s) => 'sub::$s').join(',');
          spaceLines.add('{spa::$spa:($subsFormatted)}');
        } else {
          spaceLines.add('{spa::$spa}');
        }
      }

      if (spaceLines.isNotEmpty) {
        sections.add('---{spaces}\n${spaceLines.join('\n')}');
      }
    }

    return sections.join('\n\n').trim();
  }

  /// Parses human-friendly space input format, e.g.:
  /// `work: frontend, backend | personal`
  /// or `{spa::work:(sub::frontend,sub::backend)}`
  static Map<String, List<String>> parseSpacesInput(String inputStr) {
    if (inputStr.trim().isEmpty) return {};
    final Map<String, List<String>> spaces = {};
    final chunks = inputStr.split(RegExp(r'[|\n;]+'));
    for (final chunk in chunks) {
      final trimmed = chunk.trim();
      if (trimmed.isEmpty) continue;
      final colonIdx = trimmed.indexOf(':');
      if (colonIdx != -1) {
        var spa = trimmed.substring(0, colonIdx).trim();
        if (spa.toLowerCase().startsWith('spa::')) {
          spa = spa.substring(5).trim();
        }
        var rawSubs = trimmed.substring(colonIdx + 1).trim();
        if (rawSubs.startsWith('(') && rawSubs.endsWith(')')) {
          rawSubs = rawSubs.substring(1, rawSubs.length - 1).trim();
        }
        final subs = rawSubs
            .split(',')
            .map((s) {
              var str = s.trim();
              if (str.toLowerCase().startsWith('sub::')) {
                str = str.substring(5).trim();
              }
              return str;
            })
            .where((s) => s.isNotEmpty && isValidSpaceIdentifier(s))
            .toSet()
            .toList();
        if (spa.isNotEmpty && isValidSpaceIdentifier(spa)) {
          spaces[spa] = subs;
        }
      } else {
        var spa = trimmed;
        if (spa.toLowerCase().startsWith('spa::')) {
          spa = spa.substring(5).trim();
        }
        if (spa.isNotEmpty && isValidSpaceIdentifier(spa)) {
          spaces[spa] = [];
        }
      }
    }
    return spaces;
  }

  /// Formats spaces dictionary into user-friendly text string:
  /// `work: frontend, backend | personal`
  static String formatSpacesInput(Map<String, List<String>> spaces) {
    if (spaces.isEmpty) return '';
    final List<String> parts = [];
    spaces.forEach((spa, subs) {
      if (subs.isNotEmpty) {
        parts.add('$spa: ${subs.join(', ')}');
      } else {
        parts.add(spa);
      }
    });
    return parts.join(' | ');
  }
}
