import 'dart:math' as math;
import 'mandala_types.dart';
import 'mandala_math.dart';

const double charW = 0.6;
const double minFont = 6.0;
const double maxFont = 24.0;

final RegExp wordSplit = RegExp(r'[^\p{L}\p{N}]+', unicode: true);
final RegExp syllableRegex = RegExp(r'^[^aeiouAEIOU]{0,2}[aeiouAEIOU]');

List<String> getChars(String s) {
  return s.runes.map((r) => String.fromCharCode(r)).toList();
}

String capitalize(String s) {
  final c = getChars(s);
  if (c.isEmpty) return s;
  return c[0].toUpperCase() + c.sublist(1).join();
}

String syllable(String word) {
  final m = syllableRegex.firstMatch(word);
  if (m != null) return m.group(0)!;
  final c = getChars(word);
  return c.take(2).join();
}

String shortLabel(String text, int maxChars) {
  final String t = text.trim().replaceAll(RegExp(r'\s+'), ' ');
  final all = getChars(t);
  if (maxChars <= 0) return '';
  if (all.length <= maxChars) return t;

  // If text already has newline (multi-line layout), don't truncate unless lines exceed maxChars
  if (t.contains('\n')) {
    final lines = t.split('\n');
    final fitLines = lines.map((l) => shortLabel(l, maxChars)).join('\n');
    return fitLines;
  }

  // Proper word-boundary ellipsis
  if (maxChars >= 5) {
    // Try truncating at last space before maxChars - 1
    final sub = all.take(maxChars - 1).join().trimRight();
    final lastSpace = sub.lastIndexOf(' ');
    if (lastSpace >= 3) {
      return '${sub.substring(0, lastSpace)}…';
    }
    return '$sub…';
  }

  // Very constrained space: return initials or first few chars
  final words = t.split(wordSplit).where((w) => w.isNotEmpty).toList();
  if (words.length > 1 && maxChars >= words.length) {
    return words.map((w) => getChars(w)[0].toUpperCase()).join();
  }

  return all.take(maxChars).join();
}

CellLabel fitLabel(
  LocalNode n,
  double x,
  double y,
  double w,
  double h,
  double rotate,
) {
  final String full = n.label;
  final String source = n.short ?? full;
  final int len = math.max(1, getChars(source).length);

  // Check if 2-line layout is beneficial (generous height, multiple words or long label)
  String candidateText = source;
  double effectiveLen = len.toDouble();

  if (h >= 26.0 && source.length >= 8 && !source.contains('\n')) {
    // Check for natural split points: space, or parenthesized count like " (5)"
    final countMatch = RegExp(r'\s*(\(\d+\))$').firstMatch(source);
    if (countMatch != null) {
      final namePart = source.substring(0, countMatch.start).trim();
      final countPart = countMatch.group(1)!;
      candidateText = '$namePart\n$countPart';
      effectiveLen = math.max(namePart.length, countPart.length).toDouble();
    } else {
      final words = source.split(' ');
      if (words.length >= 2) {
        final mid = (words.length / 2).ceil();
        final line1 = words.take(mid).join(' ');
        final line2 = words.skip(mid).join(' ');
        candidateText = '$line1\n$line2';
        effectiveLen = math.max(line1.length, line2.length).toDouble();
      }
    }
  }

  final bool isMultiLine = candidateText.contains('\n');
  final double lineH = isMultiLine ? h * 0.38 : h * 0.55;

  final double fontSize = round3(
    math.max(minFont, math.min(maxFont, math.min(lineH, w / (charW * math.max(1, effectiveLen))))),
  );
  final int maxChars = math.max(1, ((w / (fontSize * charW)) + 0.01).floor());

  double rot = rotate % 360;
  if (rot > 180) rot -= 360;
  if (rot <= -180) rot += 360;

  return CellLabel(
    text: shortLabel(candidateText, maxChars),
    full: full,
    x: round3(x),
    y: round3(y),
    rotate: round3(rot),
    fontSize: fontSize,
    maxChars: maxChars,
  );
}
