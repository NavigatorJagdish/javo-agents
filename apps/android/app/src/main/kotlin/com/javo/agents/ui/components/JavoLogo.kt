package com.javo.agents.ui.components

import androidx.compose.foundation.Canvas
import androidx.compose.foundation.layout.size
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.StrokeCap
import androidx.compose.ui.graphics.StrokeJoin
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.theme.DeepSpace
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.PureWhite
import com.javo.agents.ui.theme.VioletAccent

@Composable
fun JavoLogo(
    modifier: Modifier = Modifier,
    size: Dp = 72.dp,
    showOrbitalRing: Boolean = true
) {
    Canvas(modifier = modifier.size(size)) {
        val w = this.size.width
        val h = this.size.height
        val cx = w / 2f
        val cy = h / 2f

        val cyanVioletBrush = Brush.linearGradient(
            colors = listOf(ElectricCyan, VioletAccent),
            start = Offset(0f, 0f),
            end = Offset(w, h)
        )

        // Glowing outer orbital ring
        if (showOrbitalRing) {
            drawCircle(
                brush = Brush.sweepGradient(
                    colors = listOf(
                        ElectricCyan.copy(alpha = 0.65f),
                        VioletAccent.copy(alpha = 0.55f),
                        ElectricCyan.copy(alpha = 0.12f),
                        ElectricCyan.copy(alpha = 0.65f)
                    )
                ),
                radius = w * 0.46f,
                center = Offset(cx, cy),
                style = Stroke(width = w * 0.022f)
            )
        }

        // Hexagonal shield path
        val hexPath = Path().apply {
            moveTo(cx, h * 0.14f)
            lineTo(w * 0.80f, h * 0.30f)
            lineTo(w * 0.80f, h * 0.66f)
            lineTo(cx, h * 0.86f)
            lineTo(w * 0.20f, h * 0.66f)
            lineTo(w * 0.20f, h * 0.30f)
            close()
        }

        drawPath(
            path = hexPath,
            color = DeepSpace.copy(alpha = 0.92f)
        )
        drawPath(
            path = hexPath,
            brush = cyanVioletBrush,
            style = Stroke(
                width = w * 0.036f,
                join = StrokeJoin.Round
            )
        )

        // Inner connected-node graph (3 nodes connected to waveform center)
        val topNode = Offset(cx, h * 0.28f)
        val leftNode = Offset(w * 0.34f, h * 0.41f)
        val rightNode = Offset(w * 0.66f, h * 0.41f)
        val centerAnchor = Offset(cx, h * 0.47f)

        val lineColor = VioletAccent.copy(alpha = 0.78f)
        drawLine(lineColor, topNode, leftNode, strokeWidth = w * 0.02f, cap = StrokeCap.Round)
        drawLine(lineColor, topNode, rightNode, strokeWidth = w * 0.02f, cap = StrokeCap.Round)
        drawLine(ElectricCyan.copy(alpha = 0.75f), leftNode, centerAnchor, strokeWidth = w * 0.02f, cap = StrokeCap.Round)
        drawLine(ElectricCyan.copy(alpha = 0.75f), rightNode, centerAnchor, strokeWidth = w * 0.02f, cap = StrokeCap.Round)

        val nodeRadius = w * 0.032f
        drawCircle(ElectricCyan, radius = nodeRadius, center = topNode)
        drawCircle(VioletAccent, radius = nodeRadius, center = leftNode)
        drawCircle(VioletAccent, radius = nodeRadius, center = rightNode)

        // Equalizer / waveform bars inside lower shield
        val barHeights = listOf(0.11f, 0.20f, 0.27f, 0.19f, 0.11f)
        val barWidth = w * 0.042f
        val barGap = w * 0.032f
        val totalBarsWidth = barHeights.size * barWidth + (barHeights.size - 1) * barGap
        val startX = cx - totalBarsWidth / 2f
        val baselineY = h * 0.73f

        barHeights.forEachIndexed { index, heightRatio ->
            val barH = h * heightRatio
            val x = startX + index * (barWidth + barGap)
            val barColor = when (index) {
                0, 1 -> ElectricCyan
                2 -> PureWhite
                else -> VioletAccent
            }
            drawRoundRect(
                color = barColor,
                topLeft = Offset(x, baselineY - barH),
                size = Size(barWidth, barH),
                cornerRadius = CornerRadius(barWidth / 2f, barWidth / 2f)
            )
        }
    }
}
