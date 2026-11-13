package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Smartphone
import androidx.compose.material.icons.rounded.Sync
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoLogo
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.VioletAccent

@Composable
fun WelcomeScreen(
    onGetStarted: () -> Unit,
    onPairWindows: () -> Unit,
    onSkipToHome: () -> Unit
) {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .safeDrawingPadding()
                .verticalScroll(rememberScrollState())
                .padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.SpaceBetween
        ) {
            Column(horizontalAlignment = Alignment.CenterHorizontally) {
                Spacer(modifier = Modifier.height(16.dp))
                JavoLogo(size = 88.dp)
                Spacer(modifier = Modifier.height(20.dp))
                Text(
                    text = "Welcome to Javo Agents",
                    style = MaterialTheme.typography.headlineMedium,
                    color = MaterialTheme.colorScheme.onBackground
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Your autonomous AI creator team. Operates completely independently on your Android phone, or enhanced by connecting Windows.",
                    style = MaterialTheme.typography.bodyLarge,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(24.dp))

                WelcomeFeatureRow(
                    icon = Icons.Rounded.Smartphone,
                    title = "Android Standalone First",
                    body = "Execute 23+ mobile AI agents, manage tasks, and draft content directly on your device with your free Gemini key."
                )
                Spacer(modifier = Modifier.height(12.dp))
                WelcomeFeatureRow(
                    icon = Icons.Rounded.Mic,
                    title = "Hindi, Hinglish & English Voice",
                    body = "Push-to-talk multilingual assistant with automatic language recognition and audio voice responses."
                )
                Spacer(modifier = Modifier.height(12.dp))
                WelcomeFeatureRow(
                    icon = Icons.Rounded.Sync,
                    title = "Optional Windows Enhancement",
                    body = "Pair with your Windows PC anytime to unlock local Ollama models and heavier desktop workflow automation."
                )
            }

            Column(modifier = Modifier.padding(top = 24.dp)) {
                GradientButton(
                    text = "Continue with Android Standalone",
                    onClick = onSkipToHome
                )
                Spacer(modifier = Modifier.height(10.dp))
                JavoOutlinedButton(
                    text = "Connect Windows Desktop",
                    onClick = onPairWindows
                )
                Spacer(modifier = Modifier.height(8.dp))
                JavoOutlinedButton(
                    text = "Configure Preferences & AI",
                    onClick = onGetStarted,
                    borderColor = VioletAccent
                )
            }
        }
    }
}

@Composable
private fun WelcomeFeatureRow(
    icon: ImageVector,
    title: String,
    body: String
) {
    StatusCard {
        Row(verticalAlignment = Alignment.Top) {
            Icon(icon, contentDescription = title, tint = ElectricCyan)
            Spacer(modifier = Modifier.width(12.dp))
            Column {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    body,
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
