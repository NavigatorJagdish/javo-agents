package com.javo.agents.ui.components

import androidx.compose.animation.core.LinearEasing
import androidx.compose.animation.core.RepeatMode
import androidx.compose.animation.core.animateFloat
import androidx.compose.animation.core.infiniteRepeatable
import androidx.compose.animation.core.rememberInfiniteTransition
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Canvas
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.CornerRadius
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.Dp
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.WaveformState
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import kotlin.math.PI
import kotlin.math.sin

@Composable
fun WaveformVisualizer(
    state: WaveformState,
    modifier: Modifier = Modifier,
    barCount: Int = 24,
    height: Dp = 76.dp,
    showStateLabel: Boolean = true
) {
    val durationMs = when (state) {
        WaveformState.Idle -> 2400
        WaveformState.Listening -> 750
        WaveformState.Thinking -> 1100
        WaveformState.Executing -> 550
        WaveformState.Finished -> 1800
    }

    val infiniteTransition = rememberInfiniteTransition(label = "waveform_phase")
    val phase by infiniteTransition.animateFloat(
        initialValue = 0f,
        targetValue = (2f * PI).toFloat(),
        animationSpec = infiniteRepeatable(
            animation = tween(durationMillis = durationMs, easing = LinearEasing),
            repeatMode = RepeatMode.Restart
        ),
        label = "phase"
    )

    val dotColor = when (state) {
        WaveformState.Idle -> MaterialTheme.colorScheme.onSurfaceVariant
        WaveformState.Listening -> ElectricCyan
        WaveformState.Thinking -> VioletAccent
        WaveformState.Executing -> ElectricCyan
        WaveformState.Finished -> EmeraldSuccess
    }

    Column(
        modifier = modifier.fillMaxWidth(),
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Canvas(
            modifier = Modifier
                .fillMaxWidth()
                .height(height)
        ) {
            val w = size.width
            val h = size.height
            val slotWidth = w / barCount
            val barWidth = (slotWidth * 0.56f).coerceAtLeast(4f)
            val centerY = h / 2f

            val brush = when (state) {
                WaveformState.Finished -> Brush.horizontalGradient(
                    listOf(ElectricCyan, EmeraldSuccess)
                )
                WaveformState.Thinking -> Brush.horizontalGradient(
                    listOf(VioletAccent, ElectricCyan, VioletAccent)
                )
                else -> Brush.horizontalGradient(
                    listOf(ElectricCyan, VioletAccent)
                )
            }

            for (i in 0 until barCount) {
                val normPos = i.toFloat() / (barCount - 1).coerceAtLeast(1)
                val envelope = sin(normPos * PI).toFloat().coerceAtLeast(0.18f)

                val amplitude = when (state) {
                    WaveformState.Idle -> 0.16f + 0.12f * ((sin(phase + i * 0.45f) + 1f) / 2f)
                    WaveformState.Listening -> 0.25f + 0.68f * ((sin(phase * 1.8f + i * 0.65f) + 1f) / 2f) * envelope
                    WaveformState.Thinking -> 0.22f + 0.45f * ((sin(phase + i * 0.9f) + 1f) / 2f) * envelope
                    WaveformState.Executing -> 0.35f + 0.60f * ((sin(phase * 2.2f + i * 0.8f) + 1f) / 2f)
                    WaveformState.Finished -> 0.22f + 0.22f * envelope
                }

                val barHeight = (h * amplitude).coerceIn(8f, h * 0.92f)
                val left = i * slotWidth + (slotWidth - barWidth) / 2f

                drawRoundRect(
                    brush = brush,
                    topLeft = Offset(left, centerY - barHeight / 2f),
                    size = Size(barWidth, barHeight),
                    cornerRadius = CornerRadius(barWidth / 2f, barWidth / 2f),
                    alpha = if (state == WaveformState.Idle) 0.55f else 0.95f
                )
            }
        }

        if (showStateLabel) {
            Spacer(modifier = Modifier.height(8.dp))
            Row(
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.Center,
                modifier = Modifier
                    .clip(RoundedCornerShape(50))
                    .background(dotColor.copy(alpha = 0.14f))
                    .padding(horizontal = 12.dp, vertical = 4.dp)
            ) {
                Box(
                    modifier = Modifier
                        .size(8.dp)
                        .clip(CircleShape)
                        .background(dotColor)
                )
                Spacer(modifier = Modifier.width(6.dp))
                Text(
                    text = state.label,
                    style = MaterialTheme.typography.labelMedium,
                    color = dotColor
                )
            }
        }
    }
}
