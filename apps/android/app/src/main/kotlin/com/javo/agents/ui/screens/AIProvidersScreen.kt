package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.ProviderType
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun AIProvidersScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val config by viewModel.aiConfig.collectAsState()
    var geminiKeyInput by remember { mutableStateOf("") }

    JavoSubScreenScaffold(title = "AI Providers", onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatusCard(highlightGradient = true) {
                Text("Zero-Cost AI Router", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(6.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        "Enforce strict $0.00 spend guardrails (Local Ollama preferred)",
                        style = MaterialTheme.typography.bodyMedium,
                        modifier = Modifier.weight(1f)
                    )
                    Switch(
                        checked = config.zeroCostGuardEnabled,
                        onCheckedChange = viewModel::toggleZeroCostGuard
                    )
                }
            }

            ProviderType.entries.forEach { provider ->
                StatusCard(onClick = { viewModel.selectAIProvider(provider) }) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        RadioButton(
                            selected = config.activeProvider == provider,
                            onClick = { viewModel.selectAIProvider(provider) }
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            Text(provider.label, style = MaterialTheme.typography.titleMedium)
                            val subtitle = if (provider == ProviderType.LOCAL_PC_OLLAMA) {
                                "Model: ${config.localModelName} • Runs offline on paired Windows PC"
                            } else {
                                "Model: ${config.geminiModelName} • Free Developer API tier via encrypted Keystore"
                            }
                            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }

            StatusCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Gemini API Key Vault", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    StatusPill(
                        text = if (config.hasGeminiKeyStored) "Encrypted in Keystore" else "Not Set",
                        color = if (config.hasGeminiKeyStored) EmeraldSuccess else ElectricCyan
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    "Your key is encrypted with AES-256-GCM inside Android Keystore and never logged or shared with third-party analytics.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(10.dp))
                OutlinedTextField(
                    value = geminiKeyInput,
                    onValueChange = { geminiKeyInput = it },
                    label = { Text("Enter Gemini API Key") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(10.dp))
                GradientButton(
                    text = "Encrypt & Save Key",
                    onClick = {
                        viewModel.saveGeminiKey(geminiKeyInput)
                        geminiKeyInput = ""
                    },
                    enabled = geminiKeyInput.isNotBlank()
                )
                if (config.hasGeminiKeyStored) {
                    Spacer(modifier = Modifier.height(8.dp))
                    JavoOutlinedButton(
                        text = "Remove Stored Key",
                        onClick = { viewModel.saveGeminiKey("") },
                        borderColor = CoralDanger
                    )
                }
            }
        }
    }
}
