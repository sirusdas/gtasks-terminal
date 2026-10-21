import 'package:flutter/material.dart';

enum MandalaThemeId {
  cyberpunk,
  gold,
  emerald,
  sapphire,
  obsidian,
}

class MandalaThemePalette {
  final MandalaThemeId id;
  final String name;
  final String icon;
  final Color background;
  final Color cardBg;
  final Color primary;
  final Color accent;
  final Color binduBg;
  final Color binduStroke;
  final Color textPrimary;
  final Color textSecondary;
  final Color haloColor;
  final List<Color> sliceColors;

  const MandalaThemePalette({
    required this.id,
    required this.name,
    required this.icon,
    required this.background,
    required this.cardBg,
    required this.primary,
    required this.accent,
    required this.binduBg,
    required this.binduStroke,
    required this.textPrimary,
    required this.textSecondary,
    required this.haloColor,
    required this.sliceColors,
  });

  static const MandalaThemePalette cyberpunk = MandalaThemePalette(
    id: MandalaThemeId.cyberpunk,
    name: 'Cyberpunk Neon',
    icon: '⚡',
    background: Color(0xFF090812),
    cardBg: Color(0xFF131024),
    primary: Color(0xFF00F0FF),
    accent: Color(0xFFD946EF),
    binduBg: Color(0xFF1B1130),
    binduStroke: Color(0xFF00F0FF),
    textPrimary: Color(0xFFFFFFFF),
    textSecondary: Color(0xFFE879F9),
    haloColor: Color(0x4400F0FF),
    sliceColors: [
      Color(0xFF00F0FF), // Neon Cyan
      Color(0xFFD946EF), // Hot Magenta
      Color(0xFF8B5CF6), // Electric Purple
      Color(0xFFEC4899), // Neon Pink
      Color(0xFF38BDF8), // Sky Blue
      Color(0xFFA855F7), // Violet
      Color(0xFF06B6D4), // Deep Cyan
      Color(0xFFF43F5E), // Rose Coral
    ],
  );

  static const MandalaThemePalette gold = MandalaThemePalette(
    id: MandalaThemeId.gold,
    name: 'Solar Gold',
    icon: '☀️',
    background: Color(0xFF0E0D0B),
    cardBg: Color(0xFF171510),
    primary: Color(0xFFFFD54F),
    accent: Color(0xFFFFA000),
    binduBg: Color(0xFF261E0A),
    binduStroke: Color(0xFFFFE082),
    textPrimary: Color(0xFFFFF8E1),
    textSecondary: Color(0xFFFFCA28),
    haloColor: Color(0x44FFA000),
    sliceColors: [
      Color(0xFFFFD54F), // Bright Gold
      Color(0xFFFFA726), // Amber Orange
      Color(0xFFFF7043), // Sunset Coral
      Color(0xFFFFCA28), // Golden Yellow
      Color(0xFFFFE082), // Soft Sand
      Color(0xFFFB8C00), // Tangerine
      Color(0xFFF57C00), // Deep Amber
      Color(0xFFFFB300), // Warm Honey
    ],
  );

  static const MandalaThemePalette emerald = MandalaThemePalette(
    id: MandalaThemeId.emerald,
    name: 'Mystic Jade',
    icon: '🌿',
    background: Color(0xFF06130D),
    cardBg: Color(0xFF0C2016),
    primary: Color(0xFF34D399),
    accent: Color(0xFF10B981),
    binduBg: Color(0xFF0E2A1E),
    binduStroke: Color(0xFF6EE7B7),
    textPrimary: Color(0xFFECFDF5),
    textSecondary: Color(0xFFA7F3D0),
    haloColor: Color(0x4410B981),
    sliceColors: [
      Color(0xFF34D399), // Mint Green
      Color(0xFF10B981), // Emerald
      Color(0xFF059669), // Forest Jade
      Color(0xFF6EE7B7), // Radiant Seafoam
      Color(0xFF14B8A6), // Teal
      Color(0xFF2DD4BF), // Light Aqua
      Color(0xFF047857), // Deep Spruce
      Color(0xFFA7F3D0), // Pale Mint
    ],
  );

  static const MandalaThemePalette sapphire = MandalaThemePalette(
    id: MandalaThemeId.sapphire,
    name: 'Royal Sapphire',
    icon: '💎',
    background: Color(0xFF070B16),
    cardBg: Color(0xFF0E1626),
    primary: Color(0xFF38BDF8),
    accent: Color(0xFF3B82F6),
    binduBg: Color(0xFF101C36),
    binduStroke: Color(0xFF93C5FD),
    textPrimary: Color(0xFFF0F9FF),
    textSecondary: Color(0xFF7DD3FC),
    haloColor: Color(0x4438BDF8),
    sliceColors: [
      Color(0xFF38BDF8), // Electric Azure
      Color(0xFF3B82F6), // Royal Blue
      Color(0xFF2563EB), // Deep Cobalt
      Color(0xFF60A5FA), // Sky Blue
      Color(0xFF0284C7), // Ocean Blue
      Color(0xFF6366F1), // Celestial Indigo
      Color(0xFF0EA5E9), // Bright Cyan
      Color(0xFF93C5FD), // Ice Blue
    ],
  );

  static const MandalaThemePalette obsidian = MandalaThemePalette(
    id: MandalaThemeId.obsidian,
    name: 'Cosmic Obsidian',
    icon: '🌑',
    background: Color(0xFF0C0C0E),
    cardBg: Color(0xFF16161A),
    primary: Color(0xFFE2E8F0),
    accent: Color(0xFFEF4444),
    binduBg: Color(0xFF1E1E24),
    binduStroke: Color(0xFFF1F5F9),
    textPrimary: Color(0xFFFFFFFF),
    textSecondary: Color(0xFF94A3B8),
    haloColor: Color(0x44E2E8F0),
    sliceColors: [
      Color(0xFFF43F5E), // Ruby Flame
      Color(0xFF64748B), // Slate Silver
      Color(0xFF94A3B8), // Metallic Platinum
      Color(0xFFE11D48), // Crimson Rose
      Color(0xFFCBD5E1), // Bright Silver
      Color(0xFFBE123C), // Deep Garnet
      Color(0xFFE2E8F0), // Pure Platinum
      Color(0xFFFB7185), // Soft Scarlet
    ],
  );

  static const List<MandalaThemePalette> allThemes = [
    cyberpunk,
    gold,
    emerald,
    sapphire,
    obsidian,
  ];

  static MandalaThemePalette getById(String? id) {
    if (id == null || id.isEmpty) return cyberpunk;
    return allThemes.firstWhere(
      (t) => t.id.name.toLowerCase() == id.toLowerCase(),
      orElse: () => cyberpunk,
    );
  }
}
