import 'dart:math' as math;
import 'mandala_types.dart';
import 'mandala_labels.dart';

const double tau = math.pi * 2;

/// Round to 3 decimals and format without exponent (matches TypeScript fmt()).
String fmt(double n) {
  final int r = (n * 1000 + (n >= 0 ? 0.5 : -0.5)).toInt();
  if (r == 0) return '0';
  final bool neg = r < 0;
  final int a = r.abs();
  final int intPart = a ~/ 1000;
  final int rem = a % 1000;
  String frac = rem.toString().padLeft(3, '0');
  frac = frac.replaceAll(RegExp(r'0+$'), '');
  return '${neg ? '-' : ''}$intPart${frac.isNotEmpty ? '.$frac' : ''}';
}

double round3(double n) {
  return (n * 1000 + (n >= 0 ? 0.5 : -0.5)).toInt() / 1000;
}

/// Angle 0 = up (12 o'clock), increasing clockwise.
List<double> polar(double r, double a) {
  return [r * math.sin(a), -r * math.cos(a)];
}

class PathBuilder {
  final List<String> _parts = [];

  PathBuilder M(List<double> p) {
    _parts.add('M${fmt(p[0])} ${fmt(p[1])}');
    return this;
  }

  PathBuilder L(List<double> p) {
    _parts.add('L${fmt(p[0])} ${fmt(p[1])}');
    return this;
  }

  PathBuilder Q(List<double> c, List<double> p) {
    _parts.add('Q${fmt(c[0])} ${fmt(c[1])} ${fmt(p[0])} ${fmt(p[1])}');
    return this;
  }

  PathBuilder A(double r, bool large, bool clockwise, List<double> p) {
    _parts.add(
      'A${fmt(r)} ${fmt(r)} 0 ${large ? 1 : 0} ${clockwise ? 1 : 0} ${fmt(p[0])} ${fmt(p[1])}',
    );
    return this;
  }

  PathBuilder Z() {
    _parts.add('Z');
    return this;
  }

  @override
  String toString() => _parts.join('');
}

String circlePath(double r, [double cx = 0, double cy = 0]) {
  return PathBuilder()
      .M([cx, cy - r])
      .A(r, false, true, [cx, cy + r])
      .A(r, false, true, [cx, cy - r])
      .Z()
      .toString();
}

String polygonPath(List<List<double>> points) {
  if (points.isEmpty) return '';
  final b = PathBuilder().M(points[0]);
  for (int i = 1; i < points.length; i++) {
    b.L(points[i]);
  }
  return b.Z().toString();
}

String annularSectorPath(double r0, double r1, double a0, double a1) {
  final double span = a1 - a0;
  if (span >= tau - 1e-9) {
    final b = PathBuilder()
        .M(polar(r1, 0))
        .A(r1, false, true, polar(r1, math.pi))
        .A(r1, false, true, polar(r1, 0));
    if (r0 > 0) {
      b
          .M(polar(r0, 0))
          .A(r0, false, false, polar(r0, math.pi))
          .A(r0, false, false, polar(r0, 0));
    }
    return b.Z().toString();
  }
  final bool large = span > math.pi;
  final b = PathBuilder().M(polar(r1, a0)).A(r1, large, true, polar(r1, a1));
  if (r0 > 0) {
    b.L(polar(r0, a1)).A(r0, large, false, polar(r0, a0));
  } else {
    b.L([0, 0]);
  }
  return b.Z().toString();
}

String petalPath(double r0, double r1, double a0, double a1) {
  final double span = a1 - a0;
  if (span > tau * 0.75) return annularSectorPath(r0, r1, a0, a1);
  final double am = (a0 + a1) / 2;
  final double bulge = r0 + (r1 - r0) * 0.72;
  final b = PathBuilder()
      .M(polar(r0, a0))
      .Q(polar(bulge, a0), polar(r1, am))
      .Q(polar(bulge, a1), polar(r0, a1));
  if (r0 > 0) {
    b.A(r0, span > math.pi, false, polar(r0, a0));
  }
  return b.Z().toString();
}

class Span {
  final double a0;
  final double a1;
  const Span({required this.a0, required this.a1});
}

Map<String, Span> assignSpans(
  LocalNode root, [
  double a0 = 0,
  double a1 = tau,
]) {
  final spans = <String, Span>{};
  void walk(LocalNode n, double s0, double s1) {
    spans[n.id] = Span(a0: s0, a1: s1);
    final double total = n.children.fold(0.0, (acc, c) => acc + c.weight);
    double cur = s0;
    for (final c in n.children) {
      final double next = total > 0
          ? cur + ((s1 - s0) * c.weight) / total
          : cur;
      walk(c, cur, next);
      cur = next;
    }
  }

  walk(root, a0, a1);
  return spans;
}

int localHeight(LocalNode n) {
  int h = 0;
  for (final c in n.children) {
    final ch = localHeight(c) + 1;
    if (ch > h) h = ch;
  }
  return h;
}

void walkLocal(
  LocalNode n,
  void Function(LocalNode node, LocalNode? parent) fn, [
  LocalNode? parent,
]) {
  fn(n, parent);
  for (final c in n.children) {
    walkLocal(c, fn, n);
  }
}

LocalNode padSymmetry(LocalNode root, int n) {
  final int count = root.children.length;
  if (n <= 1 || count == 0 || count % n == 0) return root;
  final int extra = n - (count % n);
  final List<LocalNode> children = List.from(root.children);
  for (int i = 0; i < extra; i++) {
    children.add(
      LocalNode(
        id: '${root.id}~o$i',
        label: '',
        ring: 1,
        children: [],
        weight: 1.0,
        ornament: true,
      ),
    );
  }

  final List<LocalNode> real = root.children;
  final List<LocalNode> out = [];
  final int total = children.length;
  int r = 0;
  int o = 0;
  for (int i = 0; i < total; i++) {
    final bool wantReal = (((i + 1) * real.length) ~/ total) > r;
    if (wantReal && r < real.length) {
      out.add(real[r++]);
    } else if (real.length + o < children.length) {
      out.add(children[real.length + o++]);
    }
  }

  return LocalNode(
    id: root.id,
    label: root.label,
    short: root.short,
    details: root.details,
    type: root.type,
    ring: root.ring,
    children: out,
    weight: out.fold(0.0, (a, c) => a + c.weight),
    portal: root.portal,
    hidden: root.hidden,
    group: root.group,
    ornament: root.ornament,
  );
}

CellLabel ringLabel(LocalNode n, double rm, double w, double a0, double a1) {
  final double am = (a0 + a1) / 2;
  final List<double> pos = polar(rm, am);
  final double arc = rm * (a1 - a0);
  final double deg = (am * 180) / math.pi;
  double rotate;
  double boxW;
  double boxH;
  if (arc >= w) {
    rotate = deg;
    if (deg > 90 && deg < 270) rotate -= 180;
    boxW = arc * 0.8;
    boxH = w * 0.7;
  } else {
    rotate = deg - 90;
    if (deg > 180) rotate -= 180;
    boxW = w * 0.85;
    boxH = arc * 0.8;
  }
  return fitLabel(n, pos[0], pos[1], boxW, boxH, rotate);
}

Cell cellFor(
  LocalNode n,
  LocalNode? parent,
  CellKind kind,
  String path,
  List<double> centroid,
  CellLabel? label,
) {
  if (n.ornament) {
    return Cell(
      id: n.id,
      nodeId: null,
      parentNodeId: parent?.id,
      kind: CellKind.ornament,
      ring: n.ring,
      path: path,
      centroid: [round3(centroid[0]), round3(centroid[1])],
    );
  }
  return Cell(
    id: n.id,
    nodeId: n.group ? null : n.id,
    parentNodeId: parent?.id,
    kind: n.portal != null ? CellKind.portal : kind,
    ring: n.ring,
    path: path,
    centroid: [round3(centroid[0]), round3(centroid[1])],
    label: label,
    portal: n.portal,
    hidden: n.hidden,
    details: n.details,
    type: n.type,
  );
}
