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
    val geminiFeedback by viewModel.geminiTestFeedback.collectAsState()
    val isTestingGemini by viewModel.isTestingGemini.collectAsState()
    val customAiConfig by viewModel.customAiConfig.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()

    var geminiKeyInput by remember { mutableStateOf("") }

    var customUrlInput by remember(customAiConfig) { mutableStateOf(customAiConfig?.endpointUrl.orEmpty()) }
    var customKeyInput by remember(customAiConfig) { mutableStateOf(customAiConfig?.apiKey.orEmpty()) }
    var customModelInput by remember(customAiConfig) { mutableStateOf(customAiConfig?.modelName.orEmpty().ifBlank { "gpt-4o-mini" }) }
    var customEnabledInput by remember(customAiConfig) { mutableStateOf(customAiConfig?.isEnabled ?: false) }

    val supportedGeminiModels = listOf(
        "gemini-3.5-flash-lite" to "Gemini 3.5 Flash-Lite (Lower-cost default)",
        "gemini-3.8-flash" to "Gemini 3.8 Flash (General conversational model)",
        "gemini-2.5-flash" to "Gemini 2.5 Flash (Legacy; access may be restricted)",
        "gemini-2.5-flash-lite" to "Gemini 2.5 Flash-Lite (Legacy; access may be restricted)"
    )

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
                val isWindowsConnected = connectionState.name == "Connected"
                StatusCard(onClick = { viewModel.selectAIProvider(provider) }) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        RadioButton(
                            selected = config.activeProvider == provider,
                            onClick = { viewModel.selectAIProvider(provider) }
                        )
                        Column(modifier = Modifier.weight(1f)) {
                            Text(provider.label, style = MaterialTheme.typography.titleMedium)
                            val subtitle = when (provider) {
                                ProviderType.LOCAL_PC_OLLAMA -> {
                                    if (isWindowsConnected) "Model: ${config.localModelName} • Windows Ollama online"
                                    else "Requires paired Windows PC running Ollama (currently offline/unpaired)"
                                }
                                ProviderType.GEMINI_DIRECT -> {
                                    "Model: ${config.geminiModelName} • Free Google Gemini Developer API on device"
                                }
                                ProviderType.CUSTOM_ENDPOINT -> {
                                    if (customAiConfig?.isEnabled == true) "Active: ${customAiConfig?.endpointUrl?.take(32)} (${customAiConfig?.modelName})"
                                    else "Configurable custom OpenAI-compatible / local proxy endpoint"
                                }
                            }
                            Text(subtitle, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
            }

            if (config.activeProvider == ProviderType.GEMINI_DIRECT || config.hasGeminiKeyStored) {
                StatusCard {
                    Text("Select Gemini Model", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "Choose the Google Gemini model for on-device voice queries and content generation. Check available models and quotas for your own Google AI project; a model may be unavailable even if listed here.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    supportedGeminiModels.forEach { (modelId, displayLabel) ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier
                                .fillMaxWidth()
                                .padding(vertical = 4.dp)
                        ) {
                            RadioButton(
                                selected = config.geminiModelName == modelId,
                                onClick = { viewModel.selectGeminiModel(modelId) }
                            )
                            Text(
                                text = displayLabel,
                                style = MaterialTheme.typography.bodyMedium,
                                modifier = Modifier.weight(1f)
                            )
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
                        text = if (isTestingGemini) "Testing..." else "Test Connection (${config.geminiModelName})",
                        onClick = { viewModel.testGeminiConnection() },
                        borderColor = ElectricCyan
                    )
                    if (geminiFeedback != null) {
                        Spacer(modifier = Modifier.height(8.dp))
                        Text(
                            text = geminiFeedback.orEmpty(),
                            style = MaterialTheme.typography.bodySmall,
                            color = if (geminiFeedback?.startsWith("Connected") == true) EmeraldSuccess else CoralDanger
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    JavoOutlinedButton(
                        text = "Remove Stored Key",
                        onClick = { viewModel.saveGeminiKey("") },
                        borderColor = CoralDanger
                    )
                }
            }

            // Custom AI Endpoint Adapter Card
            StatusCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Custom AI Endpoint Adapter", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    StatusPill(
                        text = if (customAiConfig?.isEnabled == true) "Active" else "Disabled",
                        color = if (customAiConfig?.isEnabled == true) EmeraldSuccess else ElectricCyan
                    )
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "Connect an OpenAI-compatible endpoint, LM Studio, or local proxy. Secrets stay encrypted via Android Keystore AES-256-GCM.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(10.dp))
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Enable Custom Endpoint", style = MaterialTheme.typography.bodyMedium, modifier = Modifier.weight(1f))
                    Switch(
                        checked = customEnabledInput,
                        onCheckedChange = { customEnabledInput = it }
                    )
                }
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = customUrlInput,
                    onValueChange = { customUrlInput = it },
                    label = { Text("Endpoint URL (e.g. https://api.openai.com/v1/chat/completions)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = customModelInput,
                    onValueChange = { customModelInput = it },
                    label = { Text("Model Name (e.g. gpt-4o-mini, llama-3.2)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = customKeyInput,
                    onValueChange = { customKeyInput = it },
                    label = { Text("API Key (Optional / Bearer)") },
                    visualTransformation = PasswordVisualTransformation(),
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(10.dp))
                GradientButton(
                    text = "Save Custom Endpoint Config",
                    onClick = {
                        viewModel.saveCustomAiEndpoint(
                            url = customUrlInput,
                            apiKey = customKeyInput,
                            model = customModelInput,
                            enabled = customEnabledInput
                        )
                    },
                    enabled = customUrlInput.isNotBlank() || !customEnabledInput
                )
            }
        }
    }
}
