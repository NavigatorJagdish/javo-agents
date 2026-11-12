package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
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
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.navigation.Routes
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun SettingsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit,
    onNavigate: (String) -> Unit
) {
    val darkTheme by viewModel.darkTheme.collectAsState()
    val voiceMode by viewModel.voiceModeEnabled.collectAsState()
    val autoRun by viewModel.autoRunEnabled.collectAsState()
    val diagnostics = viewModel.runDiagnostics()

    JavoSubScreenScaffold(title = "Settings & Diagnostics", onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatusCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Dark Theme (Midnight Navy)", style = MaterialTheme.typography.titleMedium)
                        Text("Switch between signature dark and light theme", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Switch(checked = darkTheme, onCheckedChange = viewModel::toggleDarkTheme)
                }
            }

            StatusCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Voice Mode", style = MaterialTheme.typography.titleMedium)
                        Text("Enable Hinglish / Hindi / English voice command hub", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Switch(checked = voiceMode, onCheckedChange = viewModel::toggleVoiceMode)
                }
            }

            StatusCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Auto-Run Sync", style = MaterialTheme.typography.titleMedium)
                        Text("Background WorkManager sync respecting battery & network", style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Switch(checked = autoRun, onCheckedChange = viewModel::toggleAutoRun)
                }
            }

            StatusCard(highlightGradient = true) {
                Text("System Diagnostics", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(8.dp))
                diagnostics.forEach { check ->
                    Row(
                        modifier = Modifier.padding(vertical = 4.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(check.name, style = MaterialTheme.typography.labelMedium)
                            Text(check.detail, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                        StatusPill(
                            text = check.status,
                            color = if (check.passed) EmeraldSuccess else CoralDanger
                        )
                    }
                }
            }

            Text("Workspace & Safety", style = MaterialTheme.typography.titleMedium)
            JavoOutlinedButton("Connected Accounts", { onNavigate(Routes.CONNECTED_ACCOUNTS) })
            JavoOutlinedButton("AI Providers & Gemini Vault", { onNavigate(Routes.AI_PROVIDERS) })
            JavoOutlinedButton("Security & Pairing Management", { onNavigate(Routes.SECURITY) })
            JavoOutlinedButton("Privacy & Data Export", { onNavigate(Routes.PRIVACY_DATA) }, borderColor = VioletAccent)
            JavoOutlinedButton("Help, Troubleshooting & Reporting", { onNavigate(Routes.HELP_REPORTING) }, borderColor = VioletAccent)
        }
    }
}
