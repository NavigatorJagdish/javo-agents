package com.javo.agents.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.WaveformState
import com.javo.agents.ui.components.JavoLogo
import com.javo.agents.ui.components.WaveformVisualizer
import com.javo.agents.ui.theme.DeepSpace
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.MidnightNavy
import com.javo.agents.ui.theme.VioletAccent
import kotlinx.coroutines.delay

@Composable
fun SplashScreen(
    isOnboardingComplete: Boolean,
    onNavigateNext: (Boolean) -> Unit
) {
    LaunchedEffect(Unit) {
        delay(1300)
        onNavigateNext(isOnboardingComplete)
    }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .background(
                Brush.verticalGradient(
                    listOf(MidnightNavy, DeepSpace, MidnightNavy)
                )
            )
            .padding(24.dp),
        contentAlignment = Alignment.Center
    ) {
        Column(
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            JavoLogo(size = 112.dp)
            Spacer(modifier = Modifier.height(20.dp))
            Text(
                text = "JAVO AGENTS",
                style = MaterialTheme.typography.displaySmall.copy(fontWeight = FontWeight.Bold),
                color = MaterialTheme.colorScheme.onSurface
            )
            Spacer(modifier = Modifier.height(6.dp))
            Text(
                text = "Your Fully Automated AI Team",
                style = MaterialTheme.typography.bodyLarge,
                color = ElectricCyan
            )
            Spacer(modifier = Modifier.height(28.dp))
            WaveformVisualizer(
                state = WaveformState.Thinking,
                barCount = 18,
                height = 44.dp,
                showStateLabel = false
            )
            Spacer(modifier = Modifier.height(12.dp))
            Text(
                text = "Initializing Keystore & Local Vault...",
                style = MaterialTheme.typography.labelMedium,
                color = VioletAccent
            )
        }
    }
}
