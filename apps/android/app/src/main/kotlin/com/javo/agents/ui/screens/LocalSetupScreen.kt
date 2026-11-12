package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun LocalSetupScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit,
    onContinueToPairing: () -> Unit,
    onFinishOffline: () -> Unit
) {
    val autoRun by viewModel.autoRunEnabled.collectAsState()
    val voiceMode by viewModel.voiceModeEnabled.collectAsState()
    val darkTheme by viewModel.darkTheme.collectAsState()
    val keystoreStatus = viewModel.getKeystoreHealth()

    JavoSubScreenScaffold(title = "Local Setup", onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            StatusCard(highlightGradient = true) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Device Vault Ready", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    StatusPill(
                        text = if (keystoreStatus.keystoreActive) "AES-256-GCM" else "Check",
                        color = EmeraldSuccess
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = "Device ID: ${keystoreStatus.deviceId}",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Text(
                    text = "All local drafts & approvals are stored on-device in Room. Nothing is published without your approval.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            SetupToggleCard(
                title = "Midnight Navy Dark Theme",
                subtitle = "Signature high-contrast dark palette with Electric Cyan accents",
                checked = darkTheme,
                onCheckedChange = viewModel::toggleDarkTheme
            )
            Spacer(modifier = Modifier.height(10.dp))
            SetupToggleCard(
                title = "Voice Mode Ready",
                subtitle = "Enable push-to-talk English, Hindi & Hinglish assistant",
                checked = voiceMode,
                onCheckedChange = viewModel::toggleVoiceMode
            )
            Spacer(modifier = Modifier.height(10.dp))
            SetupToggleCard(
                title = "Supervised Auto-Sync",
                subtitle = "Allow WorkManager to sync drafts when battery & network allow",
                checked = autoRun,
                onCheckedChange = viewModel::toggleAutoRun
            )

            Spacer(modifier = Modifier.height(22.dp))
            GradientButton(
                text = "Next: Pair Windows Runtime",
                onClick = {
                    viewModel.completeOnboarding()
                    onContinueToPairing()
                }
            )
            Spacer(modifier = Modifier.height(10.dp))
            JavoOutlinedButton(
                text = "Finish & Start Offline",
                onClick = {
                    viewModel.completeOnboarding()
                    onFinishOffline()
                },
                borderColor = VioletAccent
            )
        }
    }
}

@Composable
private fun SetupToggleCard(
    title: String,
    subtitle: String,
    checked: Boolean,
    onCheckedChange: (Boolean) -> Unit
) {
    StatusCard {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Text(title, style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(2.dp))
                Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            Switch(checked = checked, onCheckedChange = onCheckedChange)
        }
    }
}
