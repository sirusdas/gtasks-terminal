import 'dart:math' as math;
import 'mandala_types.dart';
import 'mandala_math.dart';
import 'mandala_labels.dart';
import 'mandala_rings.dart';

// --- Padma (Lotus) Geometry ---

class PadmaGeometry implements MandalaGeometry {
  @override
  GeometryId get id => GeometryId.padma;

  @override
  String get name => 'Padma (Lotus)';

  @override
  String get description =>
      'Rings of lotus petals opening from the bindu; best for shallow trees with moderate fan-out.';

  @override
  int capacity(TreeStats stats, int maxCells) => maxCells;

  @override
  ({double score, List<String> reasons}) fit(TreeStats stats) {
    double score = 0.7;
    final List<String> reasons = [];
    if (stats.height <= 3) {
      score += 0.1;
      reasons.add('shallow tree (${stats.height} rings) keeps petals large');
    }
    if (stats.height > 4) {
      score -= 0.2;
      reasons.add('more than 4 rings makes outer petals thin');
    }
    if (stats.maxFanOut >= 3 && stats.maxFanOut <= 16) {
      score += 0.1;
      reasons.add('moderate fan-out gives well-shaped petals');
    }
    if (stats.maxFanOut > 24) {
      score -= 0.3;
      reasons.add('fan-out of ${stats.maxFanOut} makes petals too thin');
    }
    return (score: score.clamp(0.0, 1.0), reasons: reasons);
  }

  @override
  List<Cell> layout(LocalNode root, GeometryContext ctx) {
    return ringCells(
      root,
      RingOptions(
        radius: ctx.size * 0.47,
        shape: RingShape.petal,
        symmetry: ctx.symmetry,
      ),
    );
  }
}

// --- Chakra (Wheel) Geometry ---

class ChakraGeometry implements MandalaGeometry {
  @override
  GeometryId get id => GeometryId.chakra;

  @override
  String get name => 'Chakra (Wheel)';

  @override
  String get description =>
      'Concentric sector rings around a bindu; every depth is a ring. Fits any tree shape.';

  @override
  int capacity(TreeStats stats, int maxCells) => maxCells;

  @override
  ({double score, List<String> reasons}) fit(TreeStats stats) {
    double score = 0.6;
    final List<String> reasons = ['works for any tree shape'];
    if (stats.height >= 3) {
      score += 0.15;
      reasons.add('deep tree: sector rings show depth compactly');
    }
    if (stats.maxFanOut > 16) {
      score += 0.1;
      reasons.add(
        'wide fan-out (${stats.maxFanOut}) still gets a readable sector each',
      );
    }
    return (score: score.clamp(0.0, 0.9), reasons: reasons);
  }

  @override
  List<Cell> layout(LocalNode root, GeometryContext ctx) {
    return ringCells(
      root,
      RingOptions(
        radius: ctx.size * 0.47,
        shape: RingShape.sector,
        symmetry: ctx.symmetry,
      ),
    );
  }
}

// --- Bhupura (Gate Enclosure) Geometry ---

List<double> _quarter(List<double> p, int k) {
  double x = p[0];
  double y = p[1];
  for (int i = 0; i < k; i++) {
    final double nx = -y;
    final double ny = x;
    x = nx;
    y = ny;
  }
  return [x, y];
}

class BhupuraGeometry implements MandalaGeometry {
  static const List<String> sides = ['n', 'e', 's', 'w'];

  @override
  GeometryId get id => GeometryId.bhupura;

  @override
  String get name => 'Bhupura (Sacred Enclosure)';

  @override
  String get description =>
      'Lotus rings enclosed by a square with four gates; 4-fold symmetric.';

  @override
  int capacity(TreeStats stats, int maxCells) => maxCells;

  @override
  ({double score, List<String> reasons}) fit(TreeStats stats) {
    double score = 0.55;
    final List<String> reasons = [];
    if (stats.rootSymmetry >= 4) {
      score += 0.3;
      reasons.add(
        '${stats.rootFanOut} first-ring nodes sit symmetrically between the 4 gates',
      );
    } else {
      reasons.add('first ring is padded to 4-fold symmetry');
    }
    if (stats.height > 3) {
      score -= 0.2;
      reasons.add('the square frame leaves less room for deep trees');
    }
    if (stats.size <= 48) score += 0.05;
    return (score: score.clamp(0.0, 1.0), reasons: reasons);
  }

  ({List<Cell> cells, double innerRadius}) _frameCells(double size) {
    final double s = size * 0.4;
    final double s2 = s * 0.86;
    final double g = s * 0.16;
    final double d = size * 0.06;
    final List<Cell> cells = [];

    for (int k = 0; k < 4; k++) {
      final List<List<double>> band = [
        [-s, -s],
        [s, -s],
        [s2, -s2],
        [-s2, -s2],
      ].map((p) => _quarter(p, k)).toList();

      final List<List<double>> gate = [
        [-g, -s],
        [-g, -s - d * 0.5],
        [-g * 1.5, -s - d * 0.5],
        [-g * 1.5, -s - d],
        [g * 1.5, -s - d],
        [g * 1.5, -s - d * 0.5],
        [g, -s - d * 0.5],
        [g, -s],
      ].map((p) => _quarter(p, k)).toList();

      final List<double> bandC = _quarter([0, -(s + s2) / 2], k);
      final List<double> gateC = _quarter([0, -s - d * 0.6], k);

      cells.add(
        Cell(
          id: '~band-${sides[k]}',
          nodeId: null,
          parentNodeId: null,
          kind: CellKind.ornament,
          ring: -1,
          path: polygonPath(band),
          centroid: [round3(bandC[0]), round3(bandC[1])],
        ),
      );

      cells.add(
        Cell(
          id: '~gate-${sides[k]}',
          nodeId: null,
          parentNodeId: null,
          kind: CellKind.gate,
          ring: -1,
          path: polygonPath(gate),
          centroid: [round3(gateC[0]), round3(gateC[1])],
        ),
      );
    }

    return (cells: cells, innerRadius: s2 * 0.97);
  }

  @override
  List<Cell> layout(LocalNode root, GeometryContext ctx) {
    final frame = _frameCells(ctx.size);
    final inner = ringCells(
      root,
      RingOptions(
        radius: frame.innerRadius,
        shape: RingShape.petal,
        symmetry: ctx.symmetry != 0 ? ctx.symmetry : 4,
      ),
    );
    return [...frame.cells, ...inner];
  }
}

// --- Sri Yantra Geometry ---

const List<int> sriYantraBands = [8, 10, 10, 14];
const List<int> sriYantraPetals = [8, 16];
const int sriYantraSlotsCount = 1 + 1 + (8 + 10 + 10 + 14) + (8 + 16); // 68

class _Slot {
  final CellKind kind;
  final String path;
  final List<double> centroid;
  final ({double w, double h})? box;
  final ({double rm, double w, double a0, double a1})? ring;

  _Slot({
    required this.kind,
    required this.path,
    required this.centroid,
    this.box,
    this.ring,
  });
}

List<double> _centroidOf(List<List<double>> pts) {
  return [
    (pts[0][0] + pts[1][0] + pts[2][0]) / 3,
    (pts[0][1] + pts[1][1] + pts[2][1]) / 3,
  ];
}

class SriYantraGeometry implements MandalaGeometry {
  @override
  GeometryId get id => GeometryId.sriyantra;

  @override
  String get name => 'Sri Yantra';

  @override
  String get description =>
      '43 interlocking triangles plus 8 and 16 petal rings around a bindu; 68 sacred slots.';

  @override
  int capacity(TreeStats stats, int maxCells) =>
      math.min(maxCells, sriYantraSlotsCount);

  @override
  ({double score, List<String> reasons}) fit(TreeStats stats) {
    if (stats.size > sriYantraSlotsCount) {
      return (
        score: 0.05,
        reasons: [
          '${stats.size} nodes exceed the $sriYantraSlotsCount fixed slots',
        ],
      );
    }
    if (stats.size >= 16) {
      return (
        score: 0.85,
        reasons: [
          '${stats.size} nodes fill the 43 triangles and petal rings',
          'depth is shown as distance from the bindu',
        ],
      );
    }
    return (
      score: 0.4,
      reasons: ['few nodes: most triangles would stay empty'],
    );
  }

  ({double bindu, List<_Slot> list}) _slots(double size) {
    final double R = size * 0.47;
    final List<double> radii = [
      0.2,
      0.32,
      0.44,
      0.55,
      0.65,
    ].map((f) => f * R).toList();
    final List<_Slot> list = [];

    final double rc = radii[0];
    final List<List<double>> central = [
      polar(rc, math.pi / 3),
      polar(rc, math.pi),
      polar(rc, (5 * math.pi) / 3),
    ];
    list.add(
      _Slot(
        kind: CellKind.triangle,
        path: polygonPath(central),
        centroid: _centroidOf(central),
        box: (w: rc * math.sqrt(3) * 0.5, h: rc * 1.5 * 0.45),
      ),
    );

    for (int band = 0; band < sriYantraBands.length; band++) {
      final int n = sriYantraBands[band];
      final double r0 = radii[band];
      final double r1 = radii[band + 1];
      final int m = n ~/ 2;
      final double step = tau / m;
      final double offset = (band * step) / 4;

      for (int i = 0; i < m; i++) {
        final double t = offset + i * step;

        // Upward tooth
        final p0 = polar(r0, t - step / 2);
        final p1 = polar(r0, t + step / 2);
        final apex = polar(r1, t);
        final pathUp = PathBuilder()
            .M(p0)
            .A(r0, false, true, p1)
            .L(apex)
            .Z()
            .toString();
        final baseLenUp = 2 * r0 * math.sin(step / 2);
        list.add(
          _Slot(
            kind: CellKind.triangle,
            path: pathUp,
            centroid: _centroidOf([p0, p1, apex]),
            box: (w: baseLenUp * 0.5, h: (r1 - r0).abs() * 0.45),
          ),
        );

        // Downward tooth
        final q0 = polar(r1, t);
        final q1 = polar(r1, t + step);
        final apexDown = polar(r0, t + step / 2);
        final pathDown = PathBuilder()
            .M(q0)
            .A(r1, false, true, q1)
            .L(apexDown)
            .Z()
            .toString();
        final baseLenDown = 2 * r1 * math.sin(step / 2);
        list.add(
          _Slot(
            kind: CellKind.triangle,
            path: pathDown,
            centroid: _centroidOf([q0, q1, apexDown]),
            box: (w: baseLenDown * 0.5, h: (r1 - r0).abs() * 0.45),
          ),
        );
      }
    }

    final List<double> petalRadii = [0.65 * R, 0.8 * R, 0.95 * R];
    for (int k = 0; k < sriYantraPetals.length; k++) {
      final int n = sriYantraPetals[k];
      final double r0 = petalRadii[k];
      final double r1 = petalRadii[k + 1];
      final double step = tau / n;
      for (int i = 0; i < n; i++) {
        final double a0 = i * step - step / 2;
        final double a1 = a0 + step;
        final double rm = r0 + (r1 - r0) * 0.42;
        list.add(
          _Slot(
            kind: CellKind.petal,
            path: petalPath(r0, r1, a0, a1),
            centroid: polar(rm, (a0 + a1) / 2),
            ring: (rm: rm, w: r1 - r0, a0: a0, a1: a1),
          ),
        );
      }
    }

    return (bindu: R * 0.07, list: list);
  }

  @override
  List<Cell> layout(LocalNode root, GeometryContext ctx) {
    final s = _slots(ctx.size);
    final double bindu = s.bindu;
    final List<_Slot> list = s.list;

    final List<({LocalNode n, LocalNode parent})> order = [];
    final List<LocalNode> queue = [root];
    while (queue.isNotEmpty) {
      final p = queue.removeAt(0);
      for (final c in p.children) {
        order.add((n: c, parent: p));
        queue.add(c);
      }
    }

    final List<Cell> cells = [];
    for (int i = 0; i < list.length; i++) {
      final slot = list[i];
      final c = [round3(slot.centroid[0]), round3(slot.centroid[1])];
      if (i >= order.length) {
        cells.add(
          Cell(
            id: '~slot-$i',
            nodeId: null,
            parentNodeId: null,
            kind: CellKind.ornament,
            ring: -1,
            path: slot.path,
            centroid: c,
          ),
        );
        continue;
      }
      final entry = order[i];
      final CellLabel label = slot.ring != null
          ? ringLabel(
              entry.n,
              slot.ring!.rm,
              slot.ring!.w,
              slot.ring!.a0,
              slot.ring!.a1,
            )
          : fitLabel(
              entry.n,
              slot.centroid[0],
              slot.centroid[1],
              slot.box!.w,
              slot.box!.h,
              0,
            );

      cells.add(
        cellFor(
          entry.n,
          entry.parent,
          slot.kind,
          slot.path,
          slot.centroid,
          label,
        ),
      );
      if (i == 0) {
        cells.add(
          cellFor(
            root,
            null,
            CellKind.bindu,
            circlePath(bindu),
            [0, 0],
            fitLabel(root, 0, 0, bindu * 1.6, bindu * 0.8, 0),
          ),
        );
      }
    }

    if (order.isEmpty) {
      cells.add(
        cellFor(
          root,
          null,
          CellKind.bindu,
          circlePath(bindu),
          [0, 0],
          fitLabel(root, 0, 0, bindu * 1.6, bindu * 0.8, 0),
        ),
      );
    }

    return cells;
  }
}

// --- Registry & Suggestions ---

final Map<GeometryId, MandalaGeometry> geometries = {
  GeometryId.padma: PadmaGeometry(),
  GeometryId.chakra: ChakraGeometry(),
  GeometryId.bhupura: BhupuraGeometry(),
  GeometryId.sriyantra: SriYantraGeometry(),
};

MandalaGeometry getGeometry(GeometryId id) {
  final g = geometries[id];
  if (g == null) throw ArgumentError('Unknown geometry: $id');
  return g;
}

List<MandalaGeometry> listGeometries() => geometries.values.toList();

List<GeometrySuggestion> suggestGeometries(
  TreeStats stats, [
  int maxCells = 64,
]) {
  final list = listGeometries().map((g) {
    final fit = g.fit(stats);
    return GeometrySuggestion(
      geometry: g.id,
      name: g.name,
      score: round3(fit.score),
      reasons: fit.reasons,
      needsNesting: stats.size > g.capacity(stats, maxCells),
    );
  }).toList();

  list.sort((a, b) => b.score.compareTo(a.score));
  return list;
}
