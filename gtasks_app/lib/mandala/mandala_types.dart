// Mandala Engine Types for GTasks Flutter App
// Modeled after @vaultgraph/mandala-core spec

enum GeometryId { padma, chakra, bhupura, sriyantra }

enum NodeDisplay { auto, inline, portal }

enum CellKind { bindu, petal, sector, triangle, gate, ornament, portal }

class MandalaNode {
  final String id;
  final String label;
  final String? short;
  final String? details;
  final String? type;
  final String? parent;
  final int? order;
  final NodeDisplay? display;
  final GeometryId? geometry;
  final Map<String, dynamic>? data;

  const MandalaNode({
    required this.id,
    required this.label,
    this.short,
    this.details,
    this.type,
    this.parent,
    this.order,
    this.display,
    this.geometry,
    this.data,
  });

  factory MandalaNode.fromJson(Map<String, dynamic> json) {
    GeometryId? geom;
    if (json['geometry'] != null) {
      geom = GeometryId.values.cast<GeometryId?>().firstWhere(
        (g) => g?.name == json['geometry'],
        orElse: () => null,
      );
    }
    NodeDisplay? disp;
    if (json['display'] != null) {
      disp = NodeDisplay.values.cast<NodeDisplay?>().firstWhere(
        (d) => d?.name == json['display'],
        orElse: () => null,
      );
    }

    return MandalaNode(
      id: json['id'] as String,
      label: json['label'] as String,
      short: json['short'] as String?,
      details: json['details'] as String?,
      type: json['type'] as String?,
      parent: json['parent'] as String?,
      order: json['order'] as int?,
      display: disp,
      geometry: geom,
      data: json['data'] is Map
          ? Map<String, dynamic>.from(json['data'])
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'label': label,
    if (short != null) 'short': short,
    if (details != null) 'details': details,
    if (type != null) 'type': type,
    if (parent != null) 'parent': parent,
    if (order != null) 'order': order,
    if (display != null) 'display': display!.name,
    if (geometry != null) 'geometry': geometry!.name,
    if (data != null) 'data': data,
  };
}

class MandalaRelation {
  final String? id;
  final String source;
  final String target;
  final String type;

  const MandalaRelation({
    this.id,
    required this.source,
    required this.target,
    required this.type,
  });

  factory MandalaRelation.fromJson(Map<String, dynamic> json) {
    return MandalaRelation(
      id: json['id'] as String?,
      source: json['source'] as String,
      target: json['target'] as String,
      type: json['type'] as String,
    );
  }

  Map<String, dynamic> toJson() => {
    if (id != null) 'id': id,
    'source': source,
    'target': target,
    'type': type,
  };
}

enum MandalaNestingMode {
  hierarchicalPortals, // Always turn spaces, subspaces, lists & tags into drillable portals
  adaptive, // Engine dynamically decides based on cell budget
  flat, // Fit everything in one single mandala without portals
}

class CustomMandala {
  final String id;
  String title;
  String centerGoal;
  GeometryId geometry;
  int symmetry;
  String template; // 'blank', 'harada_9x9', 'bhupura_4gates', 'okr'
  List<MandalaNode> nodes;
  List<MandalaRelation> relations;
  final DateTime createdAt;
  DateTime updatedAt;

  CustomMandala({
    required this.id,
    required this.title,
    required this.centerGoal,
    this.geometry = GeometryId.padma,
    this.symmetry = 0,
    this.template = 'custom',
    required this.nodes,
    this.relations = const [],
    DateTime? createdAt,
    DateTime? updatedAt,
  }) : createdAt = createdAt ?? DateTime.now(),
       updatedAt = updatedAt ?? DateTime.now();

  factory CustomMandala.fromJson(Map<String, dynamic> json) {
    GeometryId geom = GeometryId.padma;
    if (json['geometry'] != null) {
      geom = GeometryId.values.firstWhere(
        (g) => g.name == json['geometry'],
        orElse: () => GeometryId.padma,
      );
    }

    final rawNodes = (json['nodes'] as List?) ?? [];
    final nodesList = rawNodes
        .map((n) => MandalaNode.fromJson(Map<String, dynamic>.from(n as Map)))
        .toList();

    final rawRels = (json['relations'] as List?) ?? [];
    final relsList = rawRels
        .map(
          (r) => MandalaRelation.fromJson(Map<String, dynamic>.from(r as Map)),
        )
        .toList();

    return CustomMandala(
      id: json['id'] as String,
      title: json['title'] as String,
      centerGoal: json['centerGoal'] as String? ?? 'Core Focus',
      geometry: geom,
      symmetry: json['symmetry'] as int? ?? 0,
      template: json['template'] as String? ?? 'custom',
      nodes: nodesList,
      relations: relsList,
      createdAt: json['createdAt'] != null
          ? DateTime.tryParse(json['createdAt'])
          : null,
      updatedAt: json['updatedAt'] != null
          ? DateTime.tryParse(json['updatedAt'])
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'title': title,
    'centerGoal': centerGoal,
    'geometry': geometry.name,
    'symmetry': symmetry,
    'template': template,
    'nodes': nodes.map((n) => n.toJson()).toList(),
    'relations': relations.map((r) => r.toJson()).toList(),
    'createdAt': createdAt.toIso8601String(),
    'updatedAt': updatedAt.toIso8601String(),
  };

  MandalaDoc toDoc({
    MandalaNestingMode nestingMode = MandalaNestingMode.adaptive,
  }) {
    return MandalaDoc(
      title: title,
      nodes: nodes,
      relations: relations,
      settings: DocSettings(
        geometry: geometry,
        symmetry: symmetry,
        fit: nestingMode == MandalaNestingMode.flat ? 'all' : 'auto',
      ),
    );
  }
}

class DocSettings {
  final GeometryId? geometry;
  final String fit; // 'auto' or 'all'
  final int symmetry;
  final int maxCellsPerMandala;
  final int maxRings;

  const DocSettings({
    this.geometry,
    this.fit = 'auto',
    this.symmetry = 0,
    this.maxCellsPerMandala = 64,
    this.maxRings = 4,
  });
}

class ResolvedSettings {
  final GeometryId? geometry; // null means 'auto'
  final String fit;
  final int symmetry;
  final int maxCellsPerMandala;
  final int maxRings;

  const ResolvedSettings({
    this.geometry,
    required this.fit,
    required this.symmetry,
    required this.maxCellsPerMandala,
    required this.maxRings,
  });
}

class MandalaDoc {
  final int version;
  final String? title;
  final List<MandalaNode> nodes;
  final List<MandalaRelation> relations;
  final DocSettings? settings;

  const MandalaDoc({
    this.version = 1,
    this.title,
    required this.nodes,
    this.relations = const [],
    this.settings,
  });
}

class TreeNode {
  final String id;
  final MandalaNode node;
  final bool virtual;
  TreeNode? parent;
  List<TreeNode> children;
  int depth;
  int size;
  int height;
  int leaves;

  TreeNode({
    required this.id,
    required this.node,
    required this.virtual,
    this.parent,
    List<TreeNode>? children,
    this.depth = 0,
    this.size = 1,
    this.height = 0,
    this.leaves = 1,
  }) : children = children ?? [];
}

class LocalNode {
  final String id;
  final String label;
  final String? short;
  final String? details;
  final String? type;
  final int ring;
  List<LocalNode> children;
  double weight;
  String? portal;
  int? hidden;
  bool group;
  bool ornament;

  LocalNode({
    required this.id,
    required this.label,
    this.short,
    this.details,
    this.type,
    required this.ring,
    List<LocalNode>? children,
    this.weight = 1.0,
    this.portal,
    this.hidden,
    this.group = false,
    this.ornament = false,
  }) : children = children ?? [];
}

class TreeStats {
  final int size;
  final int height;
  final int leaves;
  final int rootFanOut;
  final int maxFanOut;
  final double meanFanOut;
  final Map<String, int> fanOutHistogram;
  final int rootSymmetry;

  const TreeStats({
    required this.size,
    required this.height,
    required this.leaves,
    required this.rootFanOut,
    required this.maxFanOut,
    required this.meanFanOut,
    required this.fanOutHistogram,
    required this.rootSymmetry,
  });
}

class CellLabel {
  final String text;
  final String full;
  final double x;
  final double y;
  final double rotate;
  final double fontSize;
  final int maxChars;

  const CellLabel({
    required this.text,
    required this.full,
    required this.x,
    required this.y,
    required this.rotate,
    required this.fontSize,
    required this.maxChars,
  });
}

class Cell {
  final String id;
  final String? nodeId;
  final String? parentNodeId;
  final CellKind kind;
  final int ring;
  final String path;
  final List<double> centroid; // [x, y]
  final CellLabel? label;
  final String? portal;
  final int? hidden;
  final String? details;
  final String? type;

  const Cell({
    required this.id,
    this.nodeId,
    this.parentNodeId,
    required this.kind,
    required this.ring,
    required this.path,
    required this.centroid,
    this.label,
    this.portal,
    this.hidden,
    this.details,
    this.type,
  });
}

class MandalaThread {
  final String source;
  final String target;
  final String type;
  final String path;

  const MandalaThread({
    required this.source,
    required this.target,
    required this.type,
    required this.path,
  });
}

class MandalaPart {
  final String id;
  final String centerId;
  final String title;
  final String? parentMandala;
  final String? viaNodeId;
  final int depth;
  final LocalNode root;
  final List<String> nodeIds;
  final GeometryId geometry;

  const MandalaPart({
    required this.id,
    required this.centerId,
    required this.title,
    this.parentMandala,
    this.viaNodeId,
    required this.depth,
    required this.root,
    required this.nodeIds,
    required this.geometry,
  });
}

class AtlasLink {
  final String from;
  final String to;
  final String kind; // 'nest' or 'relation'
  final String? viaNodeId;
  final int count;

  const AtlasLink({
    required this.from,
    required this.to,
    required this.kind,
    this.viaNodeId,
    this.count = 1,
  });
}

class MandalaAtlas {
  final String rootMandala;
  final Map<String, MandalaPart> mandalas;
  final Map<String, String> homeOf;
  final List<AtlasLink> links;
  final List<MandalaRelation> relations;
  final ResolvedSettings settings;
  final List<String> warnings;

  const MandalaAtlas({
    required this.rootMandala,
    required this.mandalas,
    required this.homeOf,
    required this.links,
    required this.relations,
    required this.settings,
    required this.warnings,
  });
}

class MandalaLayout {
  final String mandalaId;
  final String centerId;
  final String title;
  final GeometryId geometry;
  final double size;
  final List<double> viewBox; // [-size/2, -size/2, size, size]
  final List<Cell> cells;
  final List<MandalaThread> threads;
  final List<String> breadcrumb;

  const MandalaLayout({
    required this.mandalaId,
    required this.centerId,
    required this.title,
    required this.geometry,
    required this.size,
    required this.viewBox,
    required this.cells,
    required this.threads,
    required this.breadcrumb,
  });
}

class GeometryContext {
  final double size;
  final int symmetry;

  const GeometryContext({required this.size, required this.symmetry});
}

abstract class MandalaGeometry {
  GeometryId get id;
  String get name;
  String get description;
  int capacity(TreeStats stats, int maxCells);
  ({double score, List<String> reasons}) fit(TreeStats stats);
  List<Cell> layout(LocalNode root, GeometryContext ctx);
}

class GeometrySuggestion {
  final GeometryId geometry;
  final String name;
  final double score;
  final List<String> reasons;
  final bool needsNesting;

  const GeometrySuggestion({
    required this.geometry,
    required this.name,
    required this.score,
    required this.reasons,
    required this.needsNesting,
  });
}
