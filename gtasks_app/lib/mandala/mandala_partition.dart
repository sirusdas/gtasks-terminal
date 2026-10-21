import 'dart:math' as math;
import 'mandala_types.dart';
import 'mandala_geometries.dart';
import 'mandala_math.dart';

const String virtualRootId = '__root__';

const ResolvedSettings defaultSettings = ResolvedSettings(
  geometry: null, // 'auto'
  fit: 'auto',
  symmetry: 0,
  maxCellsPerMandala: 64,
  maxRings: 4,
);

ResolvedSettings resolveSettings(DocSettings? s) {
  if (s == null) return defaultSettings;
  return ResolvedSettings(
    geometry: s.geometry,
    fit: s.fit,
    symmetry: math.max(0, s.symmetry),
    maxCellsPerMandala: math.max(4, s.maxCellsPerMandala),
    maxRings: math.max(1, s.maxRings),
  );
}

int compareStrings(String a, String b) {
  return a.compareTo(b);
}

int compareSiblings(MandalaNode a, MandalaNode b) {
  final int oa = a.order ?? 999999;
  final int ob = b.order ?? 999999;
  if (oa != ob) return oa.compareTo(ob);
  final int c = a.label.compareTo(b.label);
  if (c != 0) return c;
  return a.id.compareTo(b.id);
}

TreeStats analyze(dynamic root) {
  int size = 0;
  int leaves = 0;
  int internal = 0;
  int fanSum = 0;
  int maxFanOut = 0;
  final Map<String, int> fanOutHistogram = {};

  int walk(dynamic n) {
    size++;
    final List children = (n is TreeNode
        ? n.children
        : (n as LocalNode).children);
    final int k = children.length;
    if (k == 0) {
      leaves++;
      return 0;
    }
    internal++;
    fanSum += k;
    if (k > maxFanOut) maxFanOut = k;
    fanOutHistogram['$k'] = (fanOutHistogram['$k'] ?? 0) + 1;
    int h = 0;
    for (final c in children) {
      final ch = walk(c) + 1;
      if (ch > h) h = ch;
    }
    return h;
  }

  final int height = walk(root);
  final int rootFanOut = (root is TreeNode
      ? root.children.length
      : (root as LocalNode).children.length);
  int rootSymmetry = 1;
  for (final s in [16, 8, 4, 2]) {
    if (rootFanOut > 0 && rootFanOut % s == 0) {
      rootSymmetry = s;
      break;
    }
  }

  return TreeStats(
    size: size,
    height: height,
    leaves: leaves,
    rootFanOut: rootFanOut,
    maxFanOut: maxFanOut,
    meanFanOut: internal > 0 ? round3(fanSum / internal) : 0.0,
    fanOutHistogram: fanOutHistogram,
    rootSymmetry: rootSymmetry,
  );
}

({TreeNode root, List<String> warnings}) normalize(MandalaDoc doc) {
  final List<String> warnings = [];
  final Map<String, MandalaNode> nodes = {};

  for (final n in doc.nodes) {
    if (nodes.containsKey(n.id)) {
      warnings.add('duplicate node id "${n.id}" ignored');
      continue;
    }
    nodes[n.id] = n;
  }

  final Map<String, String?> parentOf = {};
  for (final n in nodes.values) {
    String? p = n.parent;
    if (p != null && !nodes.containsKey(p)) {
      warnings.add('node "${n.id}" has unknown parent "$p"; treated as root');
      p = null;
    }
    if (p == n.id) {
      warnings.add('node "${n.id}" is its own parent; treated as root');
      p = null;
    }
    parentOf[n.id] = p;
  }

  // Break cycles
  final List<String> sortedIds = nodes.keys.toList()..sort(compareStrings);
  for (final id in sortedIds) {
    final Set<String> seen = {};
    String? cur = id;
    while (cur != null) {
      if (seen.contains(cur)) {
        warnings.add('nesting cycle through "$cur"; made a root');
        parentOf[cur] = null;
        break;
      }
      seen.add(cur);
      cur = parentOf[cur];
    }
  }

  final Map<String, TreeNode> byId = {};
  TreeNode make(MandalaNode node, bool virtual) =>
      TreeNode(id: node.id, node: node, virtual: virtual);

  for (final n in nodes.values) {
    byId[n.id] = make(n, false);
  }

  final List<TreeNode> roots = [];
  for (final t in byId.values) {
    final String? p = parentOf[t.id];
    if (p == null) {
      roots.add(t);
    } else {
      final pt = byId[p]!;
      t.parent = pt;
      pt.children.add(t);
    }
  }

  TreeNode root;
  if (roots.length == 1) {
    root = roots[0];
  } else {
    root = make(
      MandalaNode(id: virtualRootId, label: doc.title ?? 'Mandala Focus'),
      true,
    );
    for (final r in roots) {
      r.parent = root;
      root.children.add(r);
    }
    byId[root.id] = root;
  }

  void finish(TreeNode t, int depth) {
    t.depth = depth;
    t.children.sort((a, b) => compareSiblings(a.node, b.node));
    t.size = 1;
    t.height = 0;
    t.leaves = t.children.isEmpty ? 1 : 0;
    for (final c in t.children) {
      finish(c, depth + 1);
      t.size += c.size;
      t.height = math.max(t.height, c.height + 1);
      t.leaves += c.leaves;
    }
  }

  finish(root, 0);
  return (root: root, warnings: warnings);
}

class _Job {
  final TreeNode center;
  final String? parentMandala;
  final String? via;
  final int depth;

  const _Job({
    required this.center,
    required this.parentMandala,
    required this.via,
    required this.depth,
  });
}

TreeNode _makeGroup(TreeNode parent, List<TreeNode> slice, int index) {
  final String first = slice[0].node.label;
  final String last = slice.last.node.label;
  final String label = slice.length == 1 ? first : '$first – $last';
  final g = TreeNode(
    id: '${parent.id}#g$index',
    node: MandalaNode(id: '${parent.id}#g$index', label: label),
    virtual: true,
    parent: parent,
    children: slice,
    depth: parent.depth + 1,
    size: 1,
    height: 0,
    leaves: 0,
  );
  for (final c in slice) {
    g.size += c.size;
    g.height = math.max(g.height, c.height + 1);
    g.leaves += c.leaves;
  }
  return g;
}

MandalaAtlas buildAtlas(MandalaDoc doc) {
  final ResolvedSettings settings = resolveSettings(doc.settings);
  final norm = normalize(doc);
  final TreeNode root = norm.root;
  final List<String> warnings = List.from(norm.warnings);

  final Map<String, MandalaPart> mandalas = {};
  final Map<String, String> homeOf = {};
  final List<AtlasLink> links = [];

  final bool fitAll = settings.fit == 'all';
  final List<_Job> queue = [
    _Job(center: root, parentMandala: null, via: null, depth: 0),
  ];

  while (queue.isNotEmpty) {
    final _Job job = queue.removeAt(0);
    final TreeNode C = job.center;
    final GeometryId? forced = C.node.geometry ?? settings.geometry;

    int maxCells = settings.maxCellsPerMandala;
    if (forced != null && !fitAll) {
      maxCells = math.min(
        maxCells,
        getGeometry(forced).capacity(analyze(C), maxCells),
      );
    }
    final int slots = math.max(1, maxCells - 1);

    final Map<TreeNode, List<TreeNode>> kidsOverride = {};
    int ringLimit = 999999;

    if (!fitAll) {
      if (C.children.length > slots) {
        final int n = C.children.length;
        final int k = math.min((n / slots).ceil(), slots);
        final int chunk = (n / k).ceil();
        final List<TreeNode> groups = [];
        for (int i = 0; i * chunk < n; i++) {
          final int end = math.min((i + 1) * chunk, n);
          groups.add(_makeGroup(C, C.children.sublist(i * chunk, end), i));
        }
        kidsOverride[C] = groups;
        ringLimit = 1;
      } else {
        List<TreeNode> level = [C];
        int total = 0;
        ringLimit = 1;
        for (int d = 1; d <= settings.maxRings; d++) {
          final List<TreeNode> next = [];
          for (final t in level) {
            next.addAll(t.children);
          }
          if (next.isEmpty || total + next.length > slots) break;
          total += next.length;
          ringLimit = d;
          level = next;
        }
      }
    }

    List<TreeNode> kids(TreeNode t) => kidsOverride[t] ?? t.children;

    final List<String> nodeIds = [];
    LocalNode build(TreeNode t, int ring) {
      final LocalNode local = LocalNode(
        id: t.id,
        label: t.node.label,
        short: t.node.short,
        details: t.node.details,
        type: t.node.type,
        ring: ring,
      );
      if (t.virtual && t.id != root.id) {
        local.group = true;
      }
      nodeIds.add(t.id);

      final List<TreeNode> ks = kids(t);
      final bool pinned =
          !fitAll &&
          t.node.display == NodeDisplay.inline &&
          ring < settings.maxRings;
      final bool forcePortal =
          !fitAll && ring > 0 && t.node.display == NodeDisplay.portal;
      final bool expand =
          ks.isNotEmpty && !forcePortal && (ring < ringLimit || pinned);

      if (ring > 0 && ks.isNotEmpty && !expand) {
        local.portal = t.id;
        local.hidden = t.size - 1;
        queue.add(
          _Job(center: t, parentMandala: C.id, via: t.id, depth: job.depth + 1),
        );
        links.add(
          AtlasLink(from: C.id, to: t.id, kind: 'nest', viaNodeId: t.id),
        );
      } else {
        if (!t.virtual && !homeOf.containsKey(t.id)) {
          homeOf[t.id] = C.id;
        }
        local.children = ks.map((k) => build(k, ring + 1)).toList();
        if (local.children.isNotEmpty) {
          local.weight = local.children.fold(0.0, (a, c) => a + c.weight);
        }
      }
      return local;
    }

    final LocalNode localRoot = build(C, 0);

    GeometryId geometry =
        forced ??
        suggestGeometries(analyze(localRoot), maxCells).first.geometry;
    final int cap = getGeometry(geometry).capacity(analyze(localRoot), 999999);
    if (nodeIds.length > cap) {
      warnings.add(
        'mandala "${C.id}" has ${nodeIds.length} nodes, more than $geometry can hold ($cap); using chakra',
      );
      geometry = GeometryId.chakra;
    }

    final part = MandalaPart(
      id: C.id,
      centerId: C.id,
      title: C.id == root.id && C.virtual
          ? (doc.title ?? 'Mandala Focus')
          : C.node.label,
      parentMandala: job.parentMandala,
      viaNodeId: job.via,
      depth: job.depth,
      root: localRoot,
      nodeIds: nodeIds,
      geometry: geometry,
    );
    mandalas[part.id] = part;
  }

  // Cross-mandala relations
  final Map<String, AtlasLink> counts = {};
  for (final r in doc.relations) {
    final a = homeOf[r.source];
    final b = homeOf[r.target];
    if (a == null || b == null || a == b) continue;
    final key = '$a\u0000$b';
    final existing = counts[key];
    if (existing != null) {
      counts[key] = AtlasLink(
        from: existing.from,
        to: existing.to,
        kind: 'relation',
        count: existing.count + 1,
      );
    } else {
      counts[key] = AtlasLink(from: a, to: b, kind: 'relation', count: 1);
    }
  }

  final List<AtlasLink> rel = counts.values.toList()
    ..sort((x, y) {
      final c = compareStrings(x.from, y.from);
      if (c != 0) return c;
      return compareStrings(x.to, y.to);
    });
  links.addAll(rel);

  return MandalaAtlas(
    rootMandala: root.id,
    mandalas: mandalas,
    homeOf: homeOf,
    links: links,
    relations: doc.relations,
    settings: settings,
    warnings: warnings,
  );
}

List<String> breadcrumb(MandalaAtlas atlas, String mandalaId) {
  final List<String> out = [];
  String? cur = mandalaId;
  while (cur != null) {
    out.insert(0, cur);
    cur = atlas.mandalas[cur]?.parentMandala;
  }
  return out;
}

String? mandalaOf(MandalaAtlas atlas, String nodeId) {
  return atlas.homeOf[nodeId];
}
