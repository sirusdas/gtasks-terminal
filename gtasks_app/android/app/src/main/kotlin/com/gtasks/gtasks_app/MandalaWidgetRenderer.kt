package com.gtasks.gtasks_app

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.DashPathEffect
import android.graphics.LinearGradient
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PointF
import android.graphics.RadialGradient
import android.graphics.Rect
import android.graphics.RectF
import android.graphics.Shader
import android.graphics.Typeface
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sin

object MandalaWidgetRenderer {

    enum class GeometryType {
        PADMA,      // Lotus petals
        CHAKRA,     // Sacred spoke wheel
        BHUPURA,    // 4-Gate temple enclosure
        SRIYANTRA   // Interlocking star triangles
    }

    enum class ThemeType {
        GOLD,       // Sacred Solar Gold & Amber
        CYBERPUNK,  // Neon Cyan & Electric Magenta
        EMERALD,    // Jade & Mint Oasis
        SAPPHIRE,   // Cosmic Indigo & Deep Cyan
        OBSIDIAN    // Sleek Titanium & Monochrome
    }

    data class MandalaSlice(
        val id: String,
        val label: String,
        val count: Int,
        val completedCount: Int,
        val color: Int,
        val subLabels: List<String> = emptyList()
    )

    data class MandalaRenderData(
        val title: String,
        val centerGoal: String,
        val totalCount: Int,
        val completedCount: Int,
        val slices: List<MandalaSlice>
    )

    private data class Palette(
        val background: Int,
        val cardBg: Int,
        val primary: Int,
        val accent: Int,
        val binduBg: Int,
        val binduStroke: Int,
        val textPrimary: Int,
        val textSecondary: Int,
        val haloColor: Int,
        val sliceColors: List<Int>
    )

    private fun getPalette(theme: ThemeType): Palette {
        return when (theme) {
            ThemeType.GOLD -> Palette(
                background = Color.parseColor("#0E0D0B"),
                cardBg = Color.parseColor("#171510"),
                primary = Color.parseColor("#FFD54F"),
                accent = Color.parseColor("#FFA000"),
                binduBg = Color.parseColor("#261E0A"),
                binduStroke = Color.parseColor("#FFE082"),
                textPrimary = Color.parseColor("#FFF8E1"),
                textSecondary = Color.parseColor("#FFCA28"),
                haloColor = Color.parseColor("#44FFA000"),
                sliceColors = listOf(
                    Color.parseColor("#FFD54F"),
                    Color.parseColor("#FFA726"),
                    Color.parseColor("#FF7043"),
                    Color.parseColor("#FFCA28"),
                    Color.parseColor("#FFE082"),
                    Color.parseColor("#FB8C00"),
                    Color.parseColor("#F57C00"),
                    Color.parseColor("#FFB300")
                )
            )
            ThemeType.CYBERPUNK -> Palette(
                background = Color.parseColor("#090812"),
                cardBg = Color.parseColor("#131024"),
                primary = Color.parseColor("#00F0FF"),
                accent = Color.parseColor("#D946EF"),
                binduBg = Color.parseColor("#1B1130"),
                binduStroke = Color.parseColor("#00F0FF"),
                textPrimary = Color.parseColor("#FFFFFF"),
                textSecondary = Color.parseColor("#E879F9"),
                haloColor = Color.parseColor("#4400F0FF"),
                sliceColors = listOf(
                    Color.parseColor("#00F0FF"),
                    Color.parseColor("#D946EF"),
                    Color.parseColor("#8B5CF6"),
                    Color.parseColor("#EC4899"),
                    Color.parseColor("#38BDF8"),
                    Color.parseColor("#A855F7"),
                    Color.parseColor("#06B6D4"),
                    Color.parseColor("#F43F5E")
                )
            )
            ThemeType.EMERALD -> Palette(
                background = Color.parseColor("#06130D"),
                cardBg = Color.parseColor("#0C2016"),
                primary = Color.parseColor("#34D399"),
                accent = Color.parseColor("#10B981"),
                binduBg = Color.parseColor("#0E2A1E"),
                binduStroke = Color.parseColor("#6EE7B7"),
                textPrimary = Color.parseColor("#ECFDF5"),
                textSecondary = Color.parseColor("#A7F3D0"),
                haloColor = Color.parseColor("#4410B981"),
                sliceColors = listOf(
                    Color.parseColor("#34D399"),
                    Color.parseColor("#10B981"),
                    Color.parseColor("#059669"),
                    Color.parseColor("#6EE7B7"),
                    Color.parseColor("#14B8A6"),
                    Color.parseColor("#2DD4BF"),
                    Color.parseColor("#047857"),
                    Color.parseColor("#A7F3D0")
                )
            )
            ThemeType.SAPPHIRE -> Palette(
                background = Color.parseColor("#070B16"),
                cardBg = Color.parseColor("#0F172A"),
                primary = Color.parseColor("#38BDF8"),
                accent = Color.parseColor("#6366F1"),
                binduBg = Color.parseColor("#151E3D"),
                binduStroke = Color.parseColor("#7DD3FC"),
                textPrimary = Color.parseColor("#F0F9FF"),
                textSecondary = Color.parseColor("#BAE6FD"),
                haloColor = Color.parseColor("#4438BDF8"),
                sliceColors = listOf(
                    Color.parseColor("#38BDF8"),
                    Color.parseColor("#6366F1"),
                    Color.parseColor("#3B82F6"),
                    Color.parseColor("#818CF8"),
                    Color.parseColor("#60A5FA"),
                    Color.parseColor("#4F46E5"),
                    Color.parseColor("#0284C7"),
                    Color.parseColor("#93C5FD")
                )
            )
            ThemeType.OBSIDIAN -> Palette(
                background = Color.parseColor("#0D0E11"),
                cardBg = Color.parseColor("#181920"),
                primary = Color.parseColor("#F1F5F9"),
                accent = Color.parseColor("#94A3B8"),
                binduBg = Color.parseColor("#22242F"),
                binduStroke = Color.parseColor("#CBD5E1"),
                textPrimary = Color.parseColor("#FFFFFF"),
                textSecondary = Color.parseColor("#94A3B8"),
                haloColor = Color.parseColor("#33FFFFFF"),
                sliceColors = listOf(
                    Color.parseColor("#E2E8F0"),
                    Color.parseColor("#CBD5E1"),
                    Color.parseColor("#94A3B8"),
                    Color.parseColor("#64748B"),
                    Color.parseColor("#F8FAFC"),
                    Color.parseColor("#A1A1AA"),
                    Color.parseColor("#D4D4D8"),
                    Color.parseColor("#71717A")
                )
            )
        }
    }

    /**
     * Renders a high-resolution, anti-aliased sacred Mandala Bitmap.
     */
    fun render(
        width: Int,
        height: Int,
        data: MandalaRenderData,
        geometry: GeometryType = GeometryType.PADMA,
        theme: ThemeType = ThemeType.GOLD,
        focusedIndex: Int = -1
    ): Bitmap {
        val w = max(360, width)
        val h = max(360, height)
        val bitmap = Bitmap.createBitmap(w, h, Bitmap.Config.ARGB_8888)
        val canvas = Canvas(bitmap)

        val palette = getPalette(theme)

        // Clear transparent/dark background
        canvas.drawColor(Color.TRANSPARENT)

        val cx = w / 2f
        val cy = h / 2f
        val maxR = min(cx, cy) * 0.94f
        val binduR = maxR * 0.28f

        // 1. Draw glowing cosmic radial halo in background
        val haloPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            shader = RadialGradient(
                cx, cy, maxR,
                intArrayOf(palette.haloColor, palette.cardBg, Color.TRANSPARENT),
                floatArrayOf(0.0f, 0.75f, 1.0f),
                Shader.TileMode.CLAMP
            )
        }
        canvas.drawCircle(cx, cy, maxR, haloPaint)

        // 2. Prepare slices directly from data (no dummy duplicates)
        val displaySlices = data.slices

        // 3. Render Geometry-specific layers
        when (geometry) {
            GeometryType.PADMA -> renderPadma(canvas, cx, cy, binduR, maxR, displaySlices, palette, focusedIndex)
            GeometryType.CHAKRA -> renderChakra(canvas, cx, cy, binduR, maxR, displaySlices, palette, focusedIndex)
            GeometryType.BHUPURA -> renderBhupura(canvas, cx, cy, binduR, maxR, displaySlices, palette, focusedIndex)
            GeometryType.SRIYANTRA -> renderSriYantra(canvas, cx, cy, binduR, maxR, displaySlices, palette, focusedIndex)
        }

        // 4. Render Central Bindu (Cosmic Core Hub)
        renderBindu(canvas, cx, cy, binduR, data, displaySlices, geometry, palette, focusedIndex)

        return bitmap
    }

    // --- PADMA (LOTUS) GEOMETRY DISPATCHER ---
    private fun renderPadma(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        if (slices.isEmpty()) {
            renderEmptyCosmicState(canvas, cx, cy, r0, r1, palette)
            return
        }

        when (slices.size) {
            1 -> renderCosmicMonad(canvas, cx, cy, r0, r1, slices[0], palette, focusedIndex == 0, isLotus = true)
            2 -> renderDualHemispheres(canvas, cx, cy, r0, r1, slices, palette, focusedIndex, isLotus = true)
            3 -> renderTrifoldTriad(canvas, cx, cy, r0, r1, slices, palette, focusedIndex, isLotus = true)
            in 4..8 -> renderSingleTierPadma(canvas, cx, cy, r0, r1, slices, palette, focusedIndex)
            else -> renderConcentricTiersPadma(canvas, cx, cy, r0, r1, slices, palette, focusedIndex)
        }
    }

    // --- CHAKRA (SACRED WHEEL) GEOMETRY DISPATCHER ---
    private fun renderChakra(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        if (slices.isEmpty()) {
            renderEmptyCosmicState(canvas, cx, cy, r0, r1, palette)
            return
        }

        when (slices.size) {
            1 -> renderCosmicMonad(canvas, cx, cy, r0, r1, slices[0], palette, focusedIndex == 0, isLotus = false)
            2 -> renderDualHemispheres(canvas, cx, cy, r0, r1, slices, palette, focusedIndex, isLotus = false)
            3 -> renderTrifoldTriad(canvas, cx, cy, r0, r1, slices, palette, focusedIndex, isLotus = false)
            in 4..8 -> renderSingleTierChakra(canvas, cx, cy, r0, r1, slices, palette, focusedIndex)
            else -> renderConcentricTiersChakra(canvas, cx, cy, r0, r1, slices, palette, focusedIndex)
        }
    }

    // --- 0. COSMIC EMPTY STATE (N == 0) ---
    private fun renderEmptyCosmicState(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        palette: Palette
    ) {
        val orbitPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 1.6f
            this.color = palette.primary
            alpha = 85
        }
        canvas.drawCircle(cx, cy, r1, orbitPaint)

        val dashedOrbit = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 1.3f
            this.color = palette.accent
            alpha = 95
            pathEffect = DashPathEffect(floatArrayOf(10f, 14f), 0f)
        }
        val midR = (r0 + r1) * 0.52f
        canvas.drawCircle(cx, cy, midR, dashedOrbit)
        canvas.drawCircle(cx, cy, r0 * 1.08f, orbitPaint.apply { strokeWidth = 1.0f; alpha = 50 })

        // 8 Starlight cosmic sparkles around the dashed orbit
        val sparkPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            this.color = palette.accent
            alpha = 140
        }
        for (k in 0 until 8) {
            val a = (k * 2 * PI / 8).toFloat()
            val pt = polar(cx, cy, midR, a)
            canvas.drawCircle(pt.x, pt.y, 2.6f, sparkPaint)
        }
    }

    // --- 1. COSMIC MONAD (N == 1) ---
    private fun renderCosmicMonad(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slice: MandalaSlice,
        palette: Palette,
        isFocused: Boolean,
        isLotus: Boolean
    ) {
        val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[0]
        val rMid = (r0 + r1) * 0.52f

        // Outer and inner celestial rings
        val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = if (isFocused) 2.8f else 1.8f
            this.color = if (isFocused) Color.WHITE else palette.primary
            alpha = if (isFocused) 220 else 130
        }
        canvas.drawCircle(cx, cy, r1, ringPaint)
        canvas.drawCircle(cx, cy, r0, ringPaint.apply { strokeWidth = 1.4f; alpha = 90 })

        // Glowing orbital corona
        val coronaPath = Path().apply {
            addCircle(cx, cy, r1 * 0.97f, Path.Direction.CW)
            addCircle(cx, cy, r0 * 1.03f, Path.Direction.CCW)
        }
        val coronaFill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            shader = RadialGradient(
                cx, cy, r1,
                intArrayOf(adjustAlpha(sliceColor, if (isFocused) 0.65f else 0.35f), adjustAlpha(sliceColor, 0.12f)),
                floatArrayOf(0.45f, 1.0f),
                Shader.TileMode.CLAMP
            )
        }
        canvas.drawPath(coronaPath, coronaFill)

        // 12 Orbital Starlight Gems
        val gemCount = 12
        val gemPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            this.color = if (isLotus) palette.accent else palette.primary
        }
        for (k in 0 until gemCount) {
            val ang = (k * 2 * PI / gemCount).toFloat()
            val pt = polar(cx, cy, r1 * 0.97f, ang)
            canvas.drawCircle(pt.x, pt.y, if (k % 3 == 0) 3.6f else 2.2f, gemPaint)
        }

        if (isFocused) {
            val focusHalo = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.STROKE
                strokeWidth = 3f
                this.color = Color.WHITE
            }
            canvas.drawCircle(cx, cy, r1 * 0.97f, focusHalo)
        }

        // Display the single focus item with generous typography
        drawSliceLabel(canvas, cx, cy, rMid, (-PI / 2).toFloat(), slice, isFocused, palette, totalSlices = 1)
    }

    // --- 2. DUAL HEMISPHERES (N == 2) ---
    private fun renderDualHemispheres(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int,
        isLotus: Boolean
    ) {
        val sweep = PI.toFloat()
        val startOffset = (-PI).toFloat() // Top is i=0 (-PI to 0), Bottom is i=1 (0 to PI)
        val rMid = (r0 + r1) * 0.52f

        val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 2.0f
            this.color = palette.primary
            alpha = 140
        }
        canvas.drawCircle(cx, cy, r1, ringPaint)

        for (i in 0 until 2) {
            val slice = slices[i]
            val a0 = startOffset + i * sweep
            val a1 = a0 + sweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (i == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[i % palette.sliceColors.size]

            if (isLotus) {
                val petalPath = Path()
                val p0 = polar(cx, cy, r0, a0)
                val p1 = polar(cx, cy, r0, a1)
                val tip = polar(cx, cy, r1 * 0.96f, aMid)

                val ctrlDist = r1 * 0.88f
                val ctrl0 = polar(cx, cy, ctrlDist, aMid - sweep * 0.35f)
                val ctrl1 = polar(cx, cy, ctrlDist, aMid + sweep * 0.35f)

                petalPath.moveTo(p0.x, p0.y)
                petalPath.cubicTo(ctrl0.x, ctrl0.y, tip.x, tip.y, tip.x, tip.y)
                petalPath.cubicTo(tip.x, tip.y, ctrl1.x, ctrl1.y, p1.x, p1.y)
                petalPath.close()

                val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.FILL
                    shader = LinearGradient(
                        p0.x, p0.y, tip.x, tip.y,
                        sliceColor,
                        adjustAlpha(sliceColor, if (isFocused) 0.85f else 0.45f),
                        Shader.TileMode.CLAMP
                    )
                }
                canvas.drawPath(petalPath, fillPaint)

                // Spine vein
                val spinePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = if (isFocused) 2.5f else 1.4f
                    this.color = if (isFocused) Color.WHITE else adjustAlpha(sliceColor, 0.7f)
                }
                val spineStart = polar(cx, cy, r0 * 1.05f, aMid)
                val spineEnd = polar(cx, cy, r1 * 0.85f, aMid)
                canvas.drawLine(spineStart.x, spineStart.y, spineEnd.x, spineEnd.y, spinePaint)

                val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = if (isFocused) 3.5f else 1.8f
                    this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.75f)
                }
                canvas.drawPath(petalPath, strokePaint)
            } else {
                val sectorPath = Path()
                val degStart = Math.toDegrees(a0.toDouble()).toFloat()
                val rectOuter = RectF(cx - r1, cy - r1, cx + r1, cy + r1)
                val rectInner = RectF(cx - r0, cy - r0, cx + r0, cy + r0)

                sectorPath.arcTo(rectOuter, degStart, 180f, true)
                sectorPath.arcTo(rectInner, degStart + 180f, -180f, false)
                sectorPath.close()

                val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.FILL
                    this.color = adjustAlpha(sliceColor, if (isFocused) 0.75f else 0.40f)
                }
                canvas.drawPath(sectorPath, fillPaint)

                // Dividing spoke lines
                val spokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = if (isFocused) 3f else 1.6f
                    this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.7f)
                }
                val spokeP0 = polar(cx, cy, r0, a0)
                val spokeP1 = polar(cx, cy, r1, a0)
                canvas.drawLine(spokeP0.x, spokeP0.y, spokeP1.x, spokeP1.y, spokePaint)

                if (isFocused) {
                    val focusStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                        style = Paint.Style.STROKE
                        strokeWidth = 3f
                        this.color = Color.WHITE
                    }
                    canvas.drawPath(sectorPath, focusStroke)
                }
            }

            drawSliceLabel(canvas, cx, cy, rMid, aMid, slice, isFocused, palette, totalSlices = 2)
        }
    }

    // --- 3. TRIFOLD SACRED TRIAD (N == 3) ---
    private fun renderTrifoldTriad(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int,
        isLotus: Boolean
    ) {
        val sweep = (2 * PI / 3).toFloat() // 120 deg
        val sweepDeg = 120f
        val startOffset = (-PI / 2 - sweep / 2).toFloat() // Symmetrical top triad
        val rMid = (r0 + r1) * 0.54f

        val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 2.0f
            this.color = palette.primary
            alpha = 130
        }
        canvas.drawCircle(cx, cy, r1, ringPaint)

        for (i in 0 until 3) {
            val slice = slices[i]
            val a0 = startOffset + i * sweep
            val a1 = a0 + sweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (i == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[i % palette.sliceColors.size]

            if (isLotus) {
                val petalPath = Path()
                val p0 = polar(cx, cy, r0, a0)
                val p1 = polar(cx, cy, r0, a1)
                val tip = polar(cx, cy, r1 * 0.96f, aMid)

                val ctrlDist = r1 * 0.82f
                val ctrl0 = polar(cx, cy, ctrlDist, aMid - sweep * 0.38f)
                val ctrl1 = polar(cx, cy, ctrlDist, aMid + sweep * 0.38f)

                petalPath.moveTo(p0.x, p0.y)
                petalPath.cubicTo(ctrl0.x, ctrl0.y, tip.x, tip.y, tip.x, tip.y)
                petalPath.cubicTo(tip.x, tip.y, ctrl1.x, ctrl1.y, p1.x, p1.y)
                petalPath.close()

                val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.FILL
                    shader = LinearGradient(
                        p0.x, p0.y, tip.x, tip.y,
                        sliceColor,
                        adjustAlpha(sliceColor, if (isFocused) 0.85f else 0.42f),
                        Shader.TileMode.CLAMP
                    )
                }
                canvas.drawPath(petalPath, fillPaint)

                val spinePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = if (isFocused) 2.5f else 1.3f
                    this.color = if (isFocused) Color.WHITE else adjustAlpha(sliceColor, 0.7f)
                }
                val spineStart = polar(cx, cy, r0 * 1.05f, aMid)
                val spineEnd = polar(cx, cy, r1 * 0.85f, aMid)
                canvas.drawLine(spineStart.x, spineStart.y, spineEnd.x, spineEnd.y, spinePaint)

                val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = if (isFocused) 3.5f else 1.8f
                    this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.75f)
                }
                canvas.drawPath(petalPath, strokePaint)
            } else {
                val sectorPath = Path()
                val degStart = Math.toDegrees(a0.toDouble()).toFloat()
                val rectOuter = RectF(cx - r1, cy - r1, cx + r1, cy + r1)
                val rectInner = RectF(cx - r0, cy - r0, cx + r0, cy + r0)

                sectorPath.arcTo(rectOuter, degStart, sweepDeg, true)
                sectorPath.arcTo(rectInner, degStart + sweepDeg, -sweepDeg, false)
                sectorPath.close()

                val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.FILL
                    this.color = adjustAlpha(sliceColor, if (isFocused) 0.75f else 0.38f)
                }
                canvas.drawPath(sectorPath, fillPaint)

                val spokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = if (isFocused) 3f else 1.5f
                    this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.6f)
                }
                val spokeP0 = polar(cx, cy, r0, a0)
                val spokeP1 = polar(cx, cy, r1, a0)
                canvas.drawLine(spokeP0.x, spokeP0.y, spokeP1.x, spokeP1.y, spokePaint)

                if (isFocused) {
                    val focusStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                        style = Paint.Style.STROKE
                        strokeWidth = 3f
                        this.color = Color.WHITE
                    }
                    canvas.drawPath(sectorPath, focusStroke)
                }
            }

            drawSliceLabel(canvas, cx, cy, rMid, aMid, slice, isFocused, palette, totalSlices = 3)
        }
    }

    // --- 4. SINGLE TIER SACRED GEOMETRY (N in 4..8) ---
    private fun renderSingleTierPadma(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        val n = slices.size
        val sweep = (2 * PI / n).toFloat()
        val startOffset = (-PI / 2).toFloat()

        val ringPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 1.5f
            this.color = palette.binduStroke
            alpha = 70
        }
        canvas.drawCircle(cx, cy, r1, ringPaint)
        canvas.drawCircle(cx, cy, r1 * 0.94f, ringPaint)

        for (i in 0 until n) {
            val slice = slices[i]
            val a0 = startOffset + i * sweep
            val a1 = a0 + sweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (i == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[i % palette.sliceColors.size]

            val petalPath = Path()
            val p0 = polar(cx, cy, r0, a0)
            val p1 = polar(cx, cy, r0, a1)
            val tip = polar(cx, cy, r1 * 0.96f, aMid)

            val ctrlDist = r1 * 0.76f
            val ctrl0 = polar(cx, cy, ctrlDist, aMid - sweep * 0.42f)
            val ctrl1 = polar(cx, cy, ctrlDist, aMid + sweep * 0.42f)

            petalPath.moveTo(p0.x, p0.y)
            petalPath.cubicTo(ctrl0.x, ctrl0.y, tip.x, tip.y, tip.x, tip.y)
            petalPath.cubicTo(tip.x, tip.y, ctrl1.x, ctrl1.y, p1.x, p1.y)
            petalPath.close()

            val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.FILL
                shader = LinearGradient(
                    p0.x, p0.y, tip.x, tip.y,
                    sliceColor,
                    adjustAlpha(sliceColor, if (isFocused) 0.85f else 0.40f),
                    Shader.TileMode.CLAMP
                )
            }
            canvas.drawPath(petalPath, fillPaint)

            val spinePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.STROKE
                strokeWidth = if (isFocused) 2.5f else 1.2f
                this.color = if (isFocused) Color.WHITE else adjustAlpha(sliceColor, 0.7f)
            }
            val spineStart = polar(cx, cy, r0 * 1.05f, aMid)
            val spineEnd = polar(cx, cy, r1 * 0.85f, aMid)
            canvas.drawLine(spineStart.x, spineStart.y, spineEnd.x, spineEnd.y, spinePaint)

            val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.STROKE
                strokeWidth = if (isFocused) 3.5f else 1.8f
                this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.75f)
            }
            canvas.drawPath(petalPath, strokePaint)

            drawSliceLabel(canvas, cx, cy, (r0 + r1) * 0.54f, aMid, slice, isFocused, palette, totalSlices = n)
        }
    }

    private fun renderSingleTierChakra(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        val n = slices.size
        val sweep = (2 * PI / n).toFloat()
        val sweepDeg = Math.toDegrees(sweep.toDouble()).toFloat()
        val startOffset = (-PI / 2).toFloat()
        val rMid = (r0 + r1) * 0.65f

        val rimPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 3f
            this.color = palette.primary
            alpha = 180
        }
        canvas.drawCircle(cx, cy, r1, rimPaint)
        canvas.drawCircle(cx, cy, r1 * 0.95f, rimPaint)
        canvas.drawCircle(cx, cy, rMid, rimPaint.apply { strokeWidth = 1.2f; alpha = 100 })

        val studCount = n * 4
        val studPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            this.color = palette.accent
        }
        for (k in 0 until studCount) {
            val ang = (k * 2 * PI / studCount).toFloat()
            val pt = polar(cx, cy, r1 * 0.975f, ang)
            canvas.drawCircle(pt.x, pt.y, 2.2f, studPaint)
        }

        for (i in 0 until n) {
            val slice = slices[i]
            val a0 = startOffset + i * sweep
            val a1 = a0 + sweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (i == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[i % palette.sliceColors.size]

            val sectorPath = Path()
            val degStart = Math.toDegrees(a0.toDouble()).toFloat()
            val rectOuter = RectF(cx - r1, cy - r1, cx + r1, cy + r1)
            val rectInner = RectF(cx - r0, cy - r0, cx + r0, cy + r0)

            sectorPath.arcTo(rectOuter, degStart, sweepDeg, true)
            sectorPath.arcTo(rectInner, degStart + sweepDeg, -sweepDeg, false)
            sectorPath.close()

            val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.FILL
                this.color = adjustAlpha(sliceColor, if (isFocused) 0.70f else 0.32f)
            }
            canvas.drawPath(sectorPath, fillPaint)

            val spokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.STROKE
                strokeWidth = if (isFocused) 3f else 1.5f
                this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.6f)
            }
            val spokeP0 = polar(cx, cy, r0, a0)
            val spokeP1 = polar(cx, cy, r1, a0)
            canvas.drawLine(spokeP0.x, spokeP0.y, spokeP1.x, spokeP1.y, spokePaint)

            if (isFocused) {
                val focusStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = 3f
                    this.color = Color.WHITE
                }
                canvas.drawPath(sectorPath, focusStroke)
            }

            drawSliceLabel(canvas, cx, cy, (r0 + rMid) * 0.5f, aMid, slice, isFocused, palette, totalSlices = n)
        }
    }

    // --- 5. CONCENTRIC TWO-TIER MULTI-RING GEOMETRY (N > 8) ---
    private fun renderConcentricTiersPadma(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        val n = slices.size
        val kInner = min(6, (n + 1) / 2)
        val kOuter = n - kInner
        val rMid = r0 + (r1 - r0) * 0.52f

        // Delineation rings
        val tierRingPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 1.4f
            this.color = palette.binduStroke
            alpha = 80
        }
        canvas.drawCircle(cx, cy, rMid, tierRingPaint)
        canvas.drawCircle(cx, cy, r1, tierRingPaint.apply { strokeWidth = 1.8f; alpha = 100 })

        // Inner Tier
        val innerSweep = (2 * PI / kInner).toFloat()
        val startInner = (-PI / 2).toFloat()
        for (i in 0 until kInner) {
            val slice = slices[i]
            val a0 = startInner + i * innerSweep
            val a1 = a0 + innerSweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (i == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[i % palette.sliceColors.size]

            val petalPath = Path()
            val p0 = polar(cx, cy, r0, a0)
            val p1 = polar(cx, cy, r0, a1)
            val tip = polar(cx, cy, rMid * 0.96f, aMid)
            val ctrlDist = rMid * 0.78f
            val ctrl0 = polar(cx, cy, ctrlDist, aMid - innerSweep * 0.40f)
            val ctrl1 = polar(cx, cy, ctrlDist, aMid + innerSweep * 0.40f)

            petalPath.moveTo(p0.x, p0.y)
            petalPath.cubicTo(ctrl0.x, ctrl0.y, tip.x, tip.y, tip.x, tip.y)
            petalPath.cubicTo(tip.x, tip.y, ctrl1.x, ctrl1.y, p1.x, p1.y)
            petalPath.close()

            val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.FILL
                shader = LinearGradient(
                    p0.x, p0.y, tip.x, tip.y,
                    sliceColor,
                    adjustAlpha(sliceColor, if (isFocused) 0.85f else 0.45f),
                    Shader.TileMode.CLAMP
                )
            }
            canvas.drawPath(petalPath, fillPaint)

            val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.STROKE
                strokeWidth = if (isFocused) 3f else 1.5f
                this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.75f)
            }
            canvas.drawPath(petalPath, strokePaint)

            drawSliceLabel(canvas, cx, cy, (r0 + rMid) * 0.52f, aMid, slice, isFocused, palette, totalSlices = kInner)
        }

        // Outer Tier (staggered by half-sweep)
        val outerSweep = (2 * PI / kOuter).toFloat()
        val startOuter = (-PI / 2 + outerSweep / 2f).toFloat()
        for (j in 0 until kOuter) {
            val idx = kInner + j
            val slice = slices[idx]
            val a0 = startOuter + j * outerSweep
            val a1 = a0 + outerSweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (idx == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[idx % palette.sliceColors.size]

            val petalPath = Path()
            val p0 = polar(cx, cy, rMid, a0)
            val p1 = polar(cx, cy, rMid, a1)
            val tip = polar(cx, cy, r1 * 0.97f, aMid)
            val ctrlDist = r1 * 0.84f
            val ctrl0 = polar(cx, cy, ctrlDist, aMid - outerSweep * 0.40f)
            val ctrl1 = polar(cx, cy, ctrlDist, aMid + outerSweep * 0.40f)

            petalPath.moveTo(p0.x, p0.y)
            petalPath.cubicTo(ctrl0.x, ctrl0.y, tip.x, tip.y, tip.x, tip.y)
            petalPath.cubicTo(tip.x, tip.y, ctrl1.x, ctrl1.y, p1.x, p1.y)
            petalPath.close()

            val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.FILL
                shader = LinearGradient(
                    p0.x, p0.y, tip.x, tip.y,
                    sliceColor,
                    adjustAlpha(sliceColor, if (isFocused) 0.85f else 0.38f),
                    Shader.TileMode.CLAMP
                )
            }
            canvas.drawPath(petalPath, fillPaint)

            val strokePaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.STROKE
                strokeWidth = if (isFocused) 3f else 1.5f
                this.color = if (isFocused) Color.WHITE else adjustAlpha(palette.primary, 0.70f)
            }
            canvas.drawPath(petalPath, strokePaint)

            drawSliceLabel(canvas, cx, cy, (rMid + r1) * 0.54f, aMid, slice, isFocused, palette, totalSlices = kOuter)
        }
    }

    private fun renderConcentricTiersChakra(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        val n = slices.size
        val kInner = min(6, (n + 1) / 2)
        val kOuter = n - kInner
        val rMid = r0 + (r1 - r0) * 0.52f

        // Delineation rings
        val rimPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 2.2f
            this.color = palette.primary
            alpha = 150
        }
        canvas.drawCircle(cx, cy, rMid, rimPaint)
        canvas.drawCircle(cx, cy, r1, rimPaint.apply { strokeWidth = 2.8f; alpha = 180 })

        // Inner Tier
        val innerSweep = (2 * PI / kInner).toFloat()
        val innerSweepDeg = Math.toDegrees(innerSweep.toDouble()).toFloat()
        val startInner = (-PI / 2).toFloat()
        for (i in 0 until kInner) {
            val slice = slices[i]
            val a0 = startInner + i * innerSweep
            val a1 = a0 + innerSweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (i == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[i % palette.sliceColors.size]

            val sectorPath = Path()
            val degStart = Math.toDegrees(a0.toDouble()).toFloat()
            val rectOuter = RectF(cx - rMid, cy - rMid, cx + rMid, cy + rMid)
            val rectInner = RectF(cx - r0, cy - r0, cx + r0, cy + r0)

            sectorPath.arcTo(rectOuter, degStart, innerSweepDeg, true)
            sectorPath.arcTo(rectInner, degStart + innerSweepDeg, -innerSweepDeg, false)
            sectorPath.close()

            val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.FILL
                this.color = adjustAlpha(sliceColor, if (isFocused) 0.75f else 0.36f)
            }
            canvas.drawPath(sectorPath, fillPaint)

            if (isFocused) {
                val focusStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = 3f
                    this.color = Color.WHITE
                }
                canvas.drawPath(sectorPath, focusStroke)
            }

            drawSliceLabel(canvas, cx, cy, (r0 + rMid) * 0.52f, aMid, slice, isFocused, palette, totalSlices = kInner)
        }

        // Outer Tier
        val outerSweep = (2 * PI / kOuter).toFloat()
        val outerSweepDeg = Math.toDegrees(outerSweep.toDouble()).toFloat()
        val startOuter = (-PI / 2 + outerSweep / 2f).toFloat()
        for (j in 0 until kOuter) {
            val idx = kInner + j
            val slice = slices[idx]
            val a0 = startOuter + j * outerSweep
            val a1 = a0 + outerSweep
            val aMid = (a0 + a1) / 2f
            val isFocused = (idx == focusedIndex)
            val sliceColor = if (slice.color != 0) slice.color else palette.sliceColors[idx % palette.sliceColors.size]

            val sectorPath = Path()
            val degStart = Math.toDegrees(a0.toDouble()).toFloat()
            val rectOuter = RectF(cx - r1, cy - r1, cx + r1, cy + r1)
            val rectInner = RectF(cx - rMid, cy - rMid, cx + rMid, cy + rMid)

            sectorPath.arcTo(rectOuter, degStart, outerSweepDeg, true)
            sectorPath.arcTo(rectInner, degStart + outerSweepDeg, -outerSweepDeg, false)
            sectorPath.close()

            val fillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.FILL
                this.color = adjustAlpha(sliceColor, if (isFocused) 0.70f else 0.30f)
            }
            canvas.drawPath(sectorPath, fillPaint)

            if (isFocused) {
                val focusStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                    style = Paint.Style.STROKE
                    strokeWidth = 3f
                    this.color = Color.WHITE
                }
                canvas.drawPath(sectorPath, focusStroke)
            }

            drawSliceLabel(canvas, cx, cy, (rMid + r1) * 0.54f, aMid, slice, isFocused, palette, totalSlices = kOuter)
        }
    }

    // --- BHUPURA (4-GATE SACRED ENCLOSURE) GEOMETRY ---
    private fun renderBhupura(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        val s = r1 * 0.90f
        val gateW = s * 0.28f
        val gateD = s * 0.12f

        // Draw sacred 4-gate square enclosure
        val bhupuraPath = Path()
        // Start top-left
        bhupuraPath.moveTo(cx - s, cy - s)

        // North gate (Top)
        bhupuraPath.lineTo(cx - gateW, cy - s)
        bhupuraPath.lineTo(cx - gateW, cy - s - gateD)
        bhupuraPath.lineTo(cx + gateW, cy - s - gateD)
        bhupuraPath.lineTo(cx + gateW, cy - s)
        bhupuraPath.lineTo(cx + s, cy - s)

        // East gate (Right)
        bhupuraPath.lineTo(cx + s, cy - gateW)
        bhupuraPath.lineTo(cx + s + gateD, cy - gateW)
        bhupuraPath.lineTo(cx + s + gateD, cy + gateW)
        bhupuraPath.lineTo(cx + s, cy + gateW)
        bhupuraPath.lineTo(cx + s, cy + s)

        // South gate (Bottom)
        bhupuraPath.lineTo(cx + gateW, cy + s)
        bhupuraPath.lineTo(cx + gateW, cy + s + gateD)
        bhupuraPath.lineTo(cx - gateW, cy + s + gateD)
        bhupuraPath.lineTo(cx - gateW, cy + s)
        bhupuraPath.lineTo(cx - s, cy + s)

        // West gate (Left)
        bhupuraPath.lineTo(cx - s, cy + gateW)
        bhupuraPath.lineTo(cx - s - gateD, cy + gateW)
        bhupuraPath.lineTo(cx - s - gateD, cy - gateW)
        bhupuraPath.lineTo(cx - s, cy - gateW)
        bhupuraPath.close()

        val wallFill = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            this.color = adjustAlpha(palette.accent, 0.15f)
        }
        canvas.drawPath(bhupuraPath, wallFill)

        val wallStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 2.5f
            this.color = palette.primary
        }
        canvas.drawPath(bhupuraPath, wallStroke)

        // Inner circular sanctum
        val innerSanctumR = s * 0.78f
        canvas.drawCircle(cx, cy, innerSanctumR, wallStroke.apply { strokeWidth = 1.5f; alpha = 160 })

        // Render quadrant slices
        renderPadma(canvas, cx, cy, r0, innerSanctumR, slices, palette, focusedIndex)
    }

    // --- SRI YANTRA (STAR MATRIX) GEOMETRY ---
    private fun renderSriYantra(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r0: Float,
        r1: Float,
        slices: List<MandalaSlice>,
        palette: Palette,
        focusedIndex: Int
    ) {
        val yantraR = r1 * 0.88f

        // Concentric Lotus petal rings surrounding the triangles
        renderPadma(canvas, cx, cy, r0 * 1.15f, yantraR, slices, palette, focusedIndex)

        // Draw 9 Interlocking Sri Yantra triangles
        val triPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 1.6f
            this.color = palette.accent
            alpha = 180
        }

        val triFills = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            this.color = adjustAlpha(palette.primary, 0.08f)
        }

        // 4 Upward Triangles
        val upOffsets = listOf(0.40f, 0.55f, 0.70f, 0.82f)
        for (frac in upOffsets) {
            val path = Path()
            val top = PointF(cx, cy - yantraR * frac)
            val bLeft = PointF(cx - yantraR * frac * 0.866f, cy + yantraR * frac * 0.5f)
            val bRight = PointF(cx + yantraR * frac * 0.866f, cy + yantraR * frac * 0.5f)
            path.moveTo(top.x, top.y)
            path.lineTo(bRight.x, bRight.y)
            path.lineTo(bLeft.x, bLeft.y)
            path.close()
            canvas.drawPath(path, triFills)
            canvas.drawPath(path, triPaint)
        }

        // 5 Downward Triangles
        val downOffsets = listOf(0.35f, 0.48f, 0.62f, 0.75f, 0.85f)
        for (frac in downOffsets) {
            val path = Path()
            val bot = PointF(cx, cy + yantraR * frac)
            val tLeft = PointF(cx - yantraR * frac * 0.866f, cy - yantraR * frac * 0.5f)
            val tRight = PointF(cx + yantraR * frac * 0.866f, cy - yantraR * frac * 0.5f)
            path.moveTo(bot.x, bot.y)
            path.lineTo(tRight.x, tRight.y)
            path.lineTo(tLeft.x, tLeft.y)
            path.close()
            canvas.drawPath(path, triFills)
            canvas.drawPath(path, triPaint)
        }
    }

    // --- CENTRAL BINDU (COSMIC CORE HUB) ---
    private fun renderBindu(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r: Float,
        data: MandalaRenderData,
        slices: List<MandalaSlice>,
        geometry: GeometryType,
        palette: Palette,
        focusedIndex: Int
    ) {
        // Glowing halo
        val haloPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            shader = RadialGradient(
                cx, cy, r * 1.35f,
                intArrayOf(palette.haloColor, Color.TRANSPARENT),
                floatArrayOf(0.6f, 1.0f),
                Shader.TileMode.CLAMP
            )
        }
        canvas.drawCircle(cx, cy, r * 1.35f, haloPaint)

        // Bindu disc
        val binduPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            this.color = palette.binduBg
        }
        canvas.drawCircle(cx, cy, r, binduPaint)

        // Bindu border rings
        val borderPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.STROKE
            strokeWidth = 2.5f
            this.color = palette.binduStroke
        }
        canvas.drawCircle(cx, cy, r, borderPaint)
        canvas.drawCircle(cx, cy, r * 0.92f, borderPaint.apply { strokeWidth = 1f; alpha = 130 })

        // Central text & glyph
        val glyph = when (geometry) {
            GeometryType.PADMA -> "🌸"
            GeometryType.CHAKRA -> "☸"
            GeometryType.BHUPURA -> "🏛"
            GeometryType.SRIYANTRA -> "🔯"
        }

        val focusedSlice = if (focusedIndex in slices.indices) slices[focusedIndex] else null

        // 1. Glyph symbol
        val glyphPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = r * 0.32f
            textAlign = Paint.Align.CENTER
        }
        canvas.drawText(glyph, cx, cy - r * 0.30f, glyphPaint)

        // 2. Main Metric (Count or Slice Count)
        val metricText = if (focusedSlice != null) {
            "${focusedSlice.count}"
        } else {
            "${data.totalCount}"
        }

        val metricPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = r * 0.46f
            textAlign = Paint.Align.CENTER
            this.color = palette.textPrimary
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
        }
        canvas.drawText(metricText, cx, cy + r * 0.16f, metricPaint)

        // 3. Sub-label (Slice label or "TASKS" / Completion %)
        val subLabel = if (focusedSlice != null) {
            truncate(focusedSlice.label, 18)
        } else if (slices.isEmpty()) {
            "EMPTY"
        } else if (data.completedCount > 0 && data.totalCount > 0) {
            val pct = (data.completedCount * 100) / (data.totalCount + data.completedCount)
            "$pct% DONE"
        } else {
            if (data.totalCount == 1) "TASK" else "TASKS"
        }

        val subPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = r * 0.22f
            textAlign = Paint.Align.CENTER
            this.color = palette.textSecondary
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.NORMAL)
        }
        canvas.drawText(subLabel, cx, cy + r * 0.48f, subPaint)
    }

    // --- SLICE LABEL DRAWING ---
    private fun drawSliceLabel(
        canvas: Canvas,
        cx: Float,
        cy: Float,
        r: Float,
        angle: Float,
        slice: MandalaSlice,
        isFocused: Boolean,
        palette: Palette,
        totalSlices: Int
    ) {
        val pt = polar(cx, cy, r, angle)

        // Dynamic typography & capacity adapting to petal density
        val (maxChars, baseTextSize) = when {
            totalSlices == 1 -> Pair(32, if (isFocused) 18f else 16.5f)
            totalSlices == 2 -> Pair(26, if (isFocused) 17f else 15.5f)
            totalSlices <= 3 -> Pair(22, if (isFocused) 16f else 14.5f)
            totalSlices <= 4 -> Pair(18, if (isFocused) 15f else 13.5f)
            totalSlices <= 6 -> Pair(14, if (isFocused) 14f else 12.5f)
            else -> Pair(11, if (isFocused) 12.5f else 11.0f)
        }

        val cleanLabel = truncate(slice.label, maxChars)
        val hasCount = slice.count > 0
        val isMultiLine = (totalSlices <= 4 && (cleanLabel.length >= 7 || hasCount || totalSlices == 1))

        val line1: String
        val line2: String?

        if (totalSlices == 1) {
            line1 = cleanLabel
            line2 = if (hasCount && slice.count > 1) "${slice.count} tasks" else "★ Single Focus"
        } else if (isMultiLine) {
            if (hasCount) {
                line1 = cleanLabel
                line2 = "${slice.count} task${if (slice.count == 1) "" else "s"}"
            } else if (cleanLabel.contains(' ')) {
                val words = cleanLabel.split(' ')
                val mid = (words.size + 1) / 2
                line1 = words.take(mid).joinToString(" ")
                line2 = words.drop(mid).joinToString(" ")
            } else {
                line1 = cleanLabel
                line2 = null
            }
        } else {
            val countText = if (hasCount) " (${slice.count})" else ""
            line1 = "$cleanLabel$countText"
            line2 = null
        }

        val textPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = baseTextSize
            textAlign = Paint.Align.CENTER
            this.color = if (isFocused) Color.WHITE else palette.textPrimary
            typeface = Typeface.create(Typeface.DEFAULT, if (isFocused) Typeface.BOLD else Typeface.NORMAL)
        }

        val subPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            textSize = baseTextSize * 0.85f
            textAlign = Paint.Align.CENTER
            this.color = if (isFocused) adjustAlpha(palette.primary, 0.95f) else palette.textSecondary
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.NORMAL)
        }

        val bounds1 = Rect()
        textPaint.getTextBounds(line1, 0, line1.length, bounds1)
        val w1 = bounds1.width()
        val h1 = bounds1.height()

        var w2 = 0
        var h2 = 0
        if (line2 != null) {
            val bounds2 = Rect()
            subPaint.getTextBounds(line2, 0, line2.length, bounds2)
            w2 = bounds2.width()
            h2 = bounds2.height()
        }

        val totalW = maxOf(w1, w2)
        val gap = if (line2 != null) 4f else 0f
        val totalH = if (line2 != null) (h1 + h2 + gap) else h1.toFloat()
        val padX = if (totalSlices <= 4) 10f else 6f
        val padY = if (totalSlices <= 4) 6f else 3.5f

        val pillRect = RectF(
            pt.x - totalW / 2f - padX,
            pt.y - totalH / 2f - padY,
            pt.x + totalW / 2f + padX,
            pt.y + totalH / 2f + padY
        )

        val pillPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
            style = Paint.Style.FILL
            this.color = if (isFocused) palette.cardBg else Color.parseColor("#CC121319")
        }
        canvas.drawRoundRect(pillRect, 8f, 8f, pillPaint)

        if (isFocused) {
            val pillStroke = Paint(Paint.ANTI_ALIAS_FLAG).apply {
                style = Paint.Style.STROKE
                strokeWidth = 1.4f
                this.color = palette.primary
            }
            canvas.drawRoundRect(pillRect, 8f, 8f, pillStroke)
        }

        if (line2 != null) {
            val y1 = pt.y - totalH / 2f + h1
            val y2 = y1 + h2 + gap
            canvas.drawText(line1, pt.x, y1, textPaint)
            canvas.drawText(line2, pt.x, y2, subPaint)
        } else {
            val y1 = pt.y + h1 / 2f
            canvas.drawText(line1, pt.x, y1, textPaint)
        }
    }

    // --- HELPER MATH ---
    private fun polar(cx: Float, cy: Float, r: Float, a: Float): PointF {
        return PointF(
            cx + r * cos(a),
            cy + r * sin(a)
        )
    }

    private fun adjustAlpha(color: Int, factor: Float): Int {
        val alpha = (Color.alpha(color) * factor).toInt().coerceIn(0, 255)
        return Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color))
    }

    private fun truncate(str: String, maxLen: Int): String {
        return if (str.length <= maxLen) str else str.substring(0, maxLen - 1) + "…"
    }
}
