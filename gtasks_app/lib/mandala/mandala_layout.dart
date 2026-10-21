import 'mandala_types.dart';
import 'mandala_geometries.dart';
import 'mandala_math.dart';
import 'mandala_partition.dart';

const double defaultMandalaSize = 1000.0;

List<MandalaThread> _buildThreads(MandalaAtlas atlas, List<Cell> cells) {
  final Map<String, Cell> at = {};
  for (final c in cells) {
    if (c.nodeId != null) at[c.nodeId!] = c;
  }
  final List<MandalaThread> out = [];
  for (final r in atlas.relations) {
    final a = at[r.source];
    final b = at[r.target];
    if (a == null || b == null || a == b) continue;
    final List<double> ctrl = [
      ((a.centroid[0] + b.centroid[0]) / 2) * 0.35,
      ((a.centroid[1] + b.centroid[1]) / 2) * 0.35,
    ];
    final path = PathBuilder().M(a.centroid).Q(ctrl, b.centroid).toString();
    out.add(
      MandalaThread(source: a.id, target: b.id, type: r.type, path: path),
    );
  }
  return out;
}

MandalaLayout layoutMandala(
  MandalaAtlas atlas,
  String mandalaId, {
  double size = defaultMandalaSize,
  int? symmetry,
}) {
  final MandalaPart? part = atlas.mandalas[mandalaId];
  if (part == null) {
    throw ArgumentError('Unknown mandala "$mandalaId"');
  }

  final MandalaGeometry geom = getGeometry(part.geometry);
  final List<Cell> cells = geom.layout(
    part.root,
    GeometryContext(size: size, symmetry: symmetry ?? atlas.settings.symmetry),
  );

  return MandalaLayout(
    mandalaId: part.id,
    centerId: part.centerId,
    title: part.title,
    geometry: part.geometry,
    size: size,
    viewBox: [-size / 2, -size / 2, size, size],
    cells: cells,
    threads: _buildThreads(atlas, cells),
    breadcrumb: breadcrumb(atlas, part.id),
  );
}
