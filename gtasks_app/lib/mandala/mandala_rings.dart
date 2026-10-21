import 'dart:math' as math;
import 'mandala_types.dart';
import 'mandala_math.dart';
import 'mandala_labels.dart';

enum RingShape { sector, petal }

class RingOptions {
  final double radius;
  final RingShape shape;
  final int symmetry;

  const RingOptions({
    required this.radius,
    required this.shape,
    required this.symmetry,
  });
}

List<Cell> ringCells(LocalNode input, RingOptions opts) {
  final LocalNode root = padSymmetry(input, opts.symmetry);
  final int rings = math.max(1, localHeight(root));
  final double R = opts.radius;
  final double b = R * (rings <= 1 ? 0.32 : 0.22);
  final double w = (R - b) / rings;
  final Map<String, Span> spans = assignSpans(root);
  final List<Cell> cells = [];
  final CellKind kind = opts.shape == RingShape.petal
      ? CellKind.petal
      : CellKind.sector;

  walkLocal(root, (n, parent) {
    if (parent == null) {
      final label = fitLabel(n, 0, 0, b * 1.6, b * 0.7, 0);
      cells.add(cellFor(n, null, CellKind.bindu, circlePath(b), [0, 0], label));
      return;
    }

    final Span? span = spans[n.id];
    if (span == null) return;
    final double a0 = span.a0;
    final double a1 = span.a1;
    final double r0 = b + (n.ring - 1) * w;
    final double r1 = r0 + w;
    final String path = opts.shape == RingShape.petal
        ? petalPath(r0, r1, a0, a1)
        : annularSectorPath(r0, r1, a0, a1);

    // Petals are narrow at the tip, so text sits nearer the base.
    final double rm = opts.shape == RingShape.petal
        ? r0 + w * 0.42
        : r0 + w / 2;
    final List<double> centroid = polar(rm, (a0 + a1) / 2);
    final CellLabel? label = n.ornament ? null : ringLabel(n, rm, w, a0, a1);

    cells.add(cellFor(n, parent, kind, path, centroid, label));
  });

  return cells;
}
