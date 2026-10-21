import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'mandala_types.dart';

class CustomMandalaService {
  static const String _storageKey = 'gtasks_custom_mandalas';

  /// Load all saved custom mandalas
  static Future<List<CustomMandala>> loadCustomMandalas() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString(_storageKey);
    if (jsonStr == null || jsonStr.isEmpty) {
      // Seed default Harada 9x9 goal template on first run
      final initial = _createInitialSeedMandala();
      await saveCustomMandala(initial);
      return [initial];
    }

    try {
      final List decoded = jsonDecode(jsonStr);
      return decoded
          .map(
            (m) => CustomMandala.fromJson(Map<String, dynamic>.from(m as Map)),
          )
          .toList();
    } catch (_) {
      return [_createInitialSeedMandala()];
    }
  }

  /// Save or update a custom mandala
  static Future<void> saveCustomMandala(CustomMandala mandala) async {
    final prefs = await SharedPreferences.getInstance();
    final list = await loadCustomMandalasRaw();

    final index = list.indexWhere((m) => m.id == mandala.id);
    mandala.updatedAt = DateTime.now();

    if (index >= 0) {
      list[index] = mandala;
    } else {
      list.add(mandala);
    }

    final jsonStr = jsonEncode(list.map((m) => m.toJson()).toList());
    await prefs.setString(_storageKey, jsonStr);
  }

  /// Delete a custom mandala
  static Future<void> deleteCustomMandala(String id) async {
    final prefs = await SharedPreferences.getInstance();
    final list = await loadCustomMandalasRaw();
    list.removeWhere((m) => m.id == id);
    final jsonStr = jsonEncode(list.map((m) => m.toJson()).toList());
    await prefs.setString(_storageKey, jsonStr);
  }

  static Future<List<CustomMandala>> loadCustomMandalasRaw() async {
    final prefs = await SharedPreferences.getInstance();
    final jsonStr = prefs.getString(_storageKey);
    if (jsonStr == null || jsonStr.isEmpty) return [];
    try {
      final List decoded = jsonDecode(jsonStr);
      return decoded
          .map(
            (m) => CustomMandala.fromJson(Map<String, dynamic>.from(m as Map)),
          )
          .toList();
    } catch (_) {
      return [];
    }
  }

  // --- Pre-built Templates ---

  /// Harada 9x9 Goal Matrix (Mandalachart)
  static CustomMandala createHarada9x9Template({
    required String title,
    required String centralGoal,
    List<String>? pillars,
  }) {
    final String mandalaId = 'custom_${DateTime.now().millisecondsSinceEpoch}';
    const String rootId = 'center_goal';
    final List<MandalaNode> nodes = [];

    nodes.add(
      MandalaNode(
        id: rootId,
        label: centralGoal,
        details: 'Central core objective of the 9x9 Harada Mandalachart',
        geometry: GeometryId.chakra,
      ),
    );

    final defaultPillars = [
      'Mindset & Mental',
      'Physical Health',
      'Core Competence',
      'Execution Speed',
      'Finance & Wealth',
      'Network & Support',
      'Habit Architecture',
      'Environment & Tools',
    ];

    final pillarNames = pillars ?? defaultPillars;
    for (int i = 0; i < 8; i++) {
      final String pillarName = i < pillarNames.length
          ? pillarNames[i]
          : 'Pillar ${i + 1}';
      final String pillarId = 'pillar_$i';

      nodes.add(
        MandalaNode(
          id: pillarId,
          label: pillarName,
          parent: rootId,
          short: pillarName.length > 5
              ? pillarName.substring(0, 4)
              : pillarName,
          display: NodeDisplay.portal,
        ),
      );

      // 8 concrete action steps per pillar (64 total action items)
      for (int a = 1; a <= 8; a++) {
        nodes.add(
          MandalaNode(
            id: '${pillarId}_action_$a',
            label: 'Action $a: $pillarName',
            parent: pillarId,
            type: a <= 2 ? 'critical' : (a <= 5 ? 'high' : 'medium'),
            details: 'Key milestone $a supporting $pillarName',
          ),
        );
      }
    }

    return CustomMandala(
      id: mandalaId,
      title: title,
      centerGoal: centralGoal,
      geometry: GeometryId.chakra,
      symmetry: 8,
      template: 'harada_9x9',
      nodes: nodes,
    );
  }

  /// Bhupura 4-Domain Sacred Enclosure Template
  static CustomMandala createBhupura4GatesTemplate({
    required String title,
    required String centralFocus,
    List<String>? gateNames,
  }) {
    final String mandalaId = 'custom_${DateTime.now().millisecondsSinceEpoch}';
    const String rootId = 'center_focus';
    final List<MandalaNode> nodes = [];

    nodes.add(
      MandalaNode(
        id: rootId,
        label: centralFocus,
        details: 'Central core focus framed by 4 sacred gateways',
        geometry: GeometryId.bhupura,
      ),
    );

    final defaultGates = [
      'North: Career & Impact',
      'East: Mind & Wisdom',
      'South: Energy & Body',
      'West: Community & Soul',
    ];

    final gates = gateNames ?? defaultGates;
    for (int i = 0; i < 4; i++) {
      final String gateName = i < gates.length ? gates[i] : 'Gate ${i + 1}';
      final String gateId = 'gate_$i';

      nodes.add(
        MandalaNode(
          id: gateId,
          label: gateName,
          parent: rootId,
          short: gateName.split(':')[0],
          display: NodeDisplay.portal,
        ),
      );

      for (int k = 1; k <= 4; k++) {
        nodes.add(
          MandalaNode(
            id: '${gateId}_item_$k',
            label: 'Priority $k for ${gateName.split(':')[0]}',
            parent: gateId,
            type: k == 1 ? 'critical' : 'medium',
          ),
        );
      }
    }

    return CustomMandala(
      id: mandalaId,
      title: title,
      centerGoal: centralFocus,
      geometry: GeometryId.bhupura,
      symmetry: 4,
      template: 'bhupura_4gates',
      nodes: nodes,
    );
  }

  /// Blank Canvas Template
  static CustomMandala createBlankTemplate({
    required String title,
    required String centralGoal,
    GeometryId geometry = GeometryId.padma,
  }) {
    final String mandalaId = 'custom_${DateTime.now().millisecondsSinceEpoch}';
    const String rootId = 'center_node';
    final List<MandalaNode> nodes = [
      MandalaNode(
        id: rootId,
        label: centralGoal,
        details: 'Central core bindu of this custom mandala',
        geometry: geometry,
      ),
    ];

    return CustomMandala(
      id: mandalaId,
      title: title,
      centerGoal: centralGoal,
      geometry: geometry,
      symmetry: 0,
      template: 'blank',
      nodes: nodes,
    );
  }

  static CustomMandala _createInitialSeedMandala() {
    return createHarada9x9Template(
      title: '🎯 2026 Core Goals Mandalachart',
      centralGoal: 'Achieve Peak Clarity & Productivity',
    );
  }
}
