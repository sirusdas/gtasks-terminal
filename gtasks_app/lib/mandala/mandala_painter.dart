import 'dart:math' as math;
import 'dart:ui' as ui;
import 'package:flutter/material.dart';
import 'mandala_types.dart';
import 'mandala_path_parser.dart';

class MandalaPainter extends CustomPainter {
  final MandalaLayout layout;
  final String? selectedCellId;
  final bool isDark;
  final Color primaryColor;
  final Map<String, ui.Path> _pathCache;

  MandalaPainter({
    required this.layout,
    this.selectedCellId,
    required this.isDark,
    required this.primaryColor,
    Map<String, ui.Path>? pathCache,
  }) : _pathCache = pathCache ?? {};

  ui.Path _getPath(Cell cell) {
    return _pathCache.putIfAbsent(
      cell.id,
      () => MandalaPathParser.parse(cell.path),
    );
  }

  Color _getCellColor(Cell cell) {
    if (cell.kind == CellKind.bindu) {
      return isDark ? const Color(0xFF1E293B) : const Color(0xFFF1F5F9);
    }
    if (cell.kind == CellKind.ornament || cell.kind == CellKind.gate) {
      return isDark
          ? const Color(0xFF0F172A).withValues(alpha: 0.6)
          : const Color(0xFFE2E8F0).withValues(alpha: 0.6);
    }
    if (cell.portal != null) {
      return isDark
          ? const Color(0xFF6D28D9).withValues(alpha: 0.35)
          : const Color(0xFFDDD6FE);
    }

    final type = cell.type?.toLowerCase() ?? '';
    if (type == 'completed') {
      return isDark
          ? const Color(0xFF065F46).withValues(alpha: 0.35)
          : const Color(0xFFD1FAE5);
    }
    if (type == 'critical') {
      return isDark
          ? const Color(0xFF991B1B).withValues(alpha: 0.4)
          : const Color(0xFFFEE2E2);
    }
    if (type == 'high') {
      return isDark
          ? const Color(0xFF92400E).withValues(alpha: 0.4)
          : const Color(0xFFFEF3C7);
    }
    if (type == 'low') {
      return isDark
          ? const Color(0xFF334155).withValues(alpha: 0.4)
          : const Color(0xFFF1F5F9);
    }
    // medium / default
    return isDark
        ? const Color(0xFF155E75).withValues(alpha: 0.4)
        : const Color(0xFFCFFAFE);
  }

  Color _getStrokeColor(Cell cell) {
    if (cell.id == selectedCellId) {
      return Colors.amberAccent;
    }
    if (cell.portal != null) {
      return isDark ? const Color(0xFFA78BFA) : const Color(0xFF7C3AED);
    }
    if (cell.kind == CellKind.bindu) {
      return isDark ? const Color(0xFF38BDF8) : const Color(0xFF0284C7);
    }
    if (cell.kind == CellKind.ornament || cell.kind == CellKind.gate) {
      return isDark
          ? const Color(0xFF334155).withValues(alpha: 0.4)
          : const Color(0xFFCBD5E1).withValues(alpha: 0.6);
    }

    final type = cell.type?.toLowerCase() ?? '';
    if (type == 'critical') {
      return isDark ? const Color(0xFFF87171) : const Color(0xFFDC2626);
    }
    if (type == 'high') {
      return isDark ? const Color(0xFFFBBF24) : const Color(0xFFD97706);
    }
    if (type == 'completed') {
      return isDark ? const Color(0xFF34D399) : const Color(0xFF059669);
    }
    return isDark ? const Color(0xFF475569) : const Color(0xFF94A3B8);
  }

  Color _getTextColor(Cell cell) {
    if (cell.id == selectedCellId) {
      return isDark ? Colors.white : Colors.black;
    }
    if (cell.kind == CellKind.bindu) {
      return isDark ? Colors.white : Colors.black87;
    }
    return isDark ? const Color(0xFFE2E8F0) : const Color(0xFF1E293B);
  }

  @override
  void paint(Canvas canvas, Size size) {
    // Canvas is centered at (size.width / 2, size.height / 2)
    canvas.save();
    canvas.translate(size.width / 2, size.height / 2);

    final double scale = math.min(size.width, size.height) / layout.size;
    canvas.scale(scale, scale);

    final Paint fillPaint = Paint()..style = PaintingStyle.fill;
    final Paint strokePaint = Paint()
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.0;

    // 1. Draw Cells
    for (final cell in layout.cells) {
      final ui.Path path = _getPath(cell);

      // Fill
      fillPaint.color = _getCellColor(cell);
      canvas.drawPath(path, fillPaint);

      // Stroke
      strokePaint.color = _getStrokeColor(cell);
      strokePaint.strokeWidth = cell.id == selectedCellId
          ? 2.8
          : (cell.kind == CellKind.bindu || cell.portal != null ? 1.8 : 0.9);
      canvas.drawPath(path, strokePaint);

      // Highlight selected halo
      if (cell.id == selectedCellId) {
        final Paint glowPaint = Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 5.0
          ..color = Colors.amberAccent.withValues(alpha: 0.35);
        canvas.drawPath(path, glowPaint);
      }
    }

    // 2. Draw Relation Threads
    for (final thread in layout.threads) {
      final ui.Path threadPath = MandalaPathParser.parse(thread.path);
      final Paint threadPaint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 1.5
        ..color = isDark
            ? const Color(0xFF38BDF8).withValues(alpha: 0.7)
            : const Color(0xFF0284C7).withValues(alpha: 0.7);
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
        maxLines: 1,
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
        oldDelegate.primaryColor != primaryColor;
  }
}
