import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'mandala_types.dart';
import 'mandala_path_parser.dart';
import 'mandala_themes.dart';

class MandalaPainter extends CustomPainter {
  final MandalaLayout layout;
  final String? selectedCellId;
  final bool isDark;
  final Color primaryColor;
  final MandalaThemePalette palette;
  final Map<String, ui.Path> _pathCache;

  MandalaPainter({
    required this.layout,
    this.selectedCellId,
    required this.isDark,
    required this.primaryColor,
    MandalaThemePalette? palette,
    Map<String, ui.Path>? pathCache,
  })  : palette = palette ?? MandalaThemePalette.cyberpunk,
        _pathCache = pathCache ?? {};

  ui.Path _getPath(Cell cell) {
    return _pathCache.putIfAbsent(
      cell.id,
      () => MandalaPathParser.parse(cell.path),
    );
  }

  Color _getCellColor(Cell cell, int cellIndex) {
    if (cell.kind == CellKind.bindu) {
      return palette.binduBg;
    }
    if (cell.kind == CellKind.ornament || cell.kind == CellKind.gate) {
      return palette.background.withValues(alpha: 0.7);
    }

    final type = cell.type?.toLowerCase() ?? '';
    if (type == 'completed') {
      return const Color(0xFF10B981).withValues(alpha: isDark ? 0.55 : 0.7);
    }
    if (type == 'critical') {
      return const Color(0xFFEF4444).withValues(alpha: isDark ? 0.6 : 0.75);
    }
    if (type == 'high') {
      return const Color(0xFFF59E0B).withValues(alpha: isDark ? 0.6 : 0.75);
    }

    // Sacred harmonic slice color from the active theme
    final Color baseColor =
        palette.sliceColors[cellIndex % palette.sliceColors.length];
    return baseColor.withValues(alpha: isDark ? 0.75 : 0.85);
  }

  Color _getStrokeColor(Cell cell, int cellIndex) {
    if (cell.id == selectedCellId) {
      return Colors.white;
    }
    if (cell.kind == CellKind.bindu) {
      return palette.binduStroke;
    }
    if (cell.kind == CellKind.ornament || cell.kind == CellKind.gate) {
      return palette.primary.withValues(alpha: 0.5);
    }

    final Color baseColor =
        palette.sliceColors[cellIndex % palette.sliceColors.length];
    return baseColor.withValues(alpha: isDark ? 0.95 : 0.90);
  }

  Color _getTextColor(Cell cell) {
    if (cell.id == selectedCellId) {
      return Colors.white;
    }
    if (cell.kind == CellKind.bindu) {
      return palette.textPrimary;
    }
    return isDark ? Colors.white : const Color(0xFF0F172A);
  }

  @override
  void paint(Canvas canvas, Size size) {
    // Canvas is centered at (size.width / 2, size.height / 2)
    canvas.save();
    canvas.translate(size.width / 2, size.height / 2);

    final double scale = math.min(size.width, size.height) / layout.size;
    canvas.scale(scale, scale);

    // 0. Draw Cosmic Aura / Ambient Halo behind mandala
    final double radius = layout.size * 0.46;
    final Paint haloPaint = Paint()
      ..style = PaintingStyle.fill
      ..shader = ui.Gradient.radial(
        Offset.zero,
        radius,
        [
          palette.haloColor,
          palette.haloColor.withValues(alpha: 0.0),
        ],
      );
    canvas.drawCircle(Offset.zero, radius, haloPaint);

    final Paint fillPaint = Paint()..style = PaintingStyle.fill;
    final Paint strokePaint = Paint()..style = PaintingStyle.stroke;

    // 1. Draw Cells with rich harmonic colors
    for (int i = 0; i < layout.cells.length; i++) {
      final cell = layout.cells[i];
      final ui.Path path = _getPath(cell);

      // Fill with vibrant luminous depth
      if (cell.kind != CellKind.bindu && cell.kind != CellKind.ornament) {
        final Color cellBase = _getCellColor(cell, i);
        final bool isSelected = cell.id == selectedCellId;
        final Offset centroid = Offset(cell.centroid[0], cell.centroid[1]);
        fillPaint.shader = ui.Gradient.radial(
          centroid,
          layout.size * 0.28,
          [
            cellBase.withValues(alpha: isSelected ? 0.95 : 0.82),
            cellBase.withValues(alpha: isSelected ? 0.70 : 0.48),
          ],
        );
      } else {
        fillPaint.shader = null;
        fillPaint.color = _getCellColor(cell, i);
      }
      canvas.drawPath(path, fillPaint);

      // Stroke
      final bool isSelected = cell.id == selectedCellId;
      strokePaint.color = _getStrokeColor(cell, i);
      strokePaint.strokeWidth = isSelected
          ? 3.2
          : (cell.kind == CellKind.bindu ? 2.5 : 1.8);
      canvas.drawPath(path, strokePaint);

      // Highlight selected halo
      if (isSelected) {
        final Paint glowPaint = Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 6.0
          ..color = Colors.white.withValues(alpha: 0.6);
        canvas.drawPath(path, glowPaint);
      }
    }

    // 2. Draw Relation Threads
    for (final thread in layout.threads) {
      final ui.Path threadPath = MandalaPathParser.parse(thread.path);
      final Paint threadPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.8
        ..color = palette.accent.withValues(alpha: 0.75);
      canvas.drawPath(threadPath, threadPaint);
    }

    // 3. Draw Labels
    for (final cell in layout.cells) {
      final label = cell.label;
      if (label == null || label.text.isEmpty) continue;

      canvas.save();
      canvas.translate(label.x, label.y);
      canvas.rotate((label.rotate * math.pi) / 180);

      final TextStyle style = TextStyle(
        fontSize: label.fontSize,
        fontWeight: cell.kind == CellKind.bindu
            ? FontWeight.bold
            : (cell.portal != null ? FontWeight.w600 : FontWeight.w500),
        color: _getTextColor(cell),
      );

      final textSpan = TextSpan(text: label.text, style: style);
      final textPainter = TextPainter(
        text: textSpan,
        textDirection: TextDirection.ltr,
        textAlign: TextAlign.center,
        maxLines: 3,
      );
      textPainter.layout();

      textPainter.paint(
        canvas,
        Offset(-textPainter.width / 2, -textPainter.height / 2),
      );

      // If portal, draw small "+N" indicator below label
      if (cell.portal != null && cell.hidden != null && cell.hidden! > 0) {
        final badgeSpan = TextSpan(
          text: ' +${cell.hidden}',
          style: TextStyle(
            fontSize: math.max(6.0, label.fontSize * 0.7),
            fontWeight: FontWeight.bold,
            color: isDark ? const Color(0xFFA78BFA) : const Color(0xFF7C3AED),
          ),
        );
        final badgePainter = TextPainter(
          text: badgeSpan,
          textDirection: TextDirection.ltr,
        );
        badgePainter.layout();
        badgePainter.paint(
          canvas,
          Offset(-badgePainter.width / 2, (textPainter.height / 2) + 1),
        );
      }

      canvas.restore();
    }

    canvas.restore();
  }

  @override
  bool shouldRepaint(covariant MandalaPainter oldDelegate) {
    return oldDelegate.layout != layout ||
        oldDelegate.selectedCellId != selectedCellId ||
        oldDelegate.isDark != isDark ||
        oldDelegate.palette != palette ||
        oldDelegate.primaryColor != primaryColor;
  }
}
