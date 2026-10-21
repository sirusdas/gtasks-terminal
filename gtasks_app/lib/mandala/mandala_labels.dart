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

  final words = t.split(wordSplit).where((w) => w.isNotEmpty).toList();
  final String ellipsis = maxChars >= 4
      ? '${all.take(maxChars - 1).join().trimRight()}…'
      : '';
  final List<String> candidates = [];

  if (ellipsis.isNotEmpty && (maxChars >= 8 || words.length <= 1)) {
    candidates.add(ellipsis);
  }
  if (words.length > 1) {
    candidates.add(words.map((w) => capitalize(syllable(w))).join());
    candidates.add(words.map((w) => getChars(w)[0].toUpperCase()).join());
  } else if (words.length == 1) {
    candidates.add(capitalize(syllable(words[0])));
  }
  if (ellipsis.isNotEmpty) {
    candidates.add(ellipsis);
  }

  for (final c in candidates) {
    if (c.isNotEmpty && getChars(c).length <= maxChars) {
      return c;
    }
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
  final int len = math.max(1, math.min(getChars(source).length, 12));
  final double fontSize = round3(
    math.max(minFont, math.min(maxFont, math.min(h * 0.55, w / (charW * len)))),
  );
  final int maxChars = math.max(1, ((w / (fontSize * charW)) + 0.01).floor());

  double rot = rotate % 360;
  if (rot > 180) rot -= 360;
  if (rot <= -180) rot += 360;

  return CellLabel(
    text: shortLabel(source, maxChars),
    full: full,
    x: round3(x),
    y: round3(y),
    rotate: round3(rot),
    fontSize: fontSize,
    maxChars: maxChars,
  );
}
