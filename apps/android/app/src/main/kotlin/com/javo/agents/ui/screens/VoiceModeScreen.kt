package com.javo.agents.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.rounded.Send
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Stop
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.model.WaveformState
import com.javo.agents.ui.components.BottomNavBar
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.WaveformVisualizer
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.MidnightNavy
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun VoiceModeScreen(
    viewModel: MainViewModel,
    currentRoute: String?,
    hasAudioPermission: Boolean,
    onRequestAudioPermission: () -> Unit,
    onNavigate: (String) -> Unit
) {
    val waveformState by viewModel.waveformState.collectAsState()
    val messages by viewModel.voiceMessages.collectAsState()
    val selectedLanguage by viewModel.selectedVoiceLanguage.collectAsState()
    val approvals by viewModel.approvals.collectAsState()

    var commandDraft by remember { mutableStateOf("") }
    val isListening = waveformState == WaveformState.Listening

    JavoSubScreenScaffold(
        title = "Javo Voice Mode",
        bottomBar = {
            BottomNavBar(
                currentRoute = currentRoute,
                pendingApprovalsCount = approvals.count { it.status == "pending" },
                onNavigate = onNavigate
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
        ) {
            // Language Selector Chips
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                VoiceLanguage.entries.forEach { lang ->
                    FilterChip(
                        selected = selectedLanguage == lang,
                        onClick = { viewModel.setVoiceLanguage(lang) },
                        label = { Text(lang.displayName) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(6.dp))

            // Central Cyan-Violet Waveform Card
            StatusCard(highlightGradient = true) {
                WaveformVisualizer(
                    state = waveformState,
                    barCount = 28,
                    height = 88.dp,
                    showStateLabel = true
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = when (waveformState) {
                        WaveformState.Idle -> "Tap mic for Push-to-Talk (${selectedLanguage.displayName})"
                        WaveformState.Listening -> "Listening... Tap Stop to send to Voice Agent"
                        WaveformState.Thinking -> "Understanding ${selectedLanguage.displayName} intent..."
                        WaveformState.Executing -> "Coordinating specialist agents..."
                        WaveformState.Finished -> "Done! Ready for next command."
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Chat Bubbles (Hindi / Hinglish / English)
            LazyColumn(
                modifier = Modifier
                    .weight(1f)
                    .fillMaxWidth(),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(messages, key = { it.id }) { msg ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = if (msg.isUser) Arrangement.End else Arrangement.Start
                    ) {
                        Box(
                            modifier = Modifier
                                .fillMaxWidth(0.86f)
                                .clip(RoundedCornerShape(16.dp))
                                .background(
                                    if (msg.isUser) VioletAccent.copy(alpha = 0.24f)
                                    else MaterialTheme.colorScheme.surfaceVariant
                                )
                                .padding(12.dp)
                        ) {
                            Column {
                                Text(
                                    text = if (msg.isUser) "You (${msg.language.displayName})" else "Javo Voice Agent",
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (msg.isUser) VioletAccent else ElectricCyan
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(msg.text, style = MaterialTheme.typography.bodyMedium)
                                if (!msg.actionHint.isNullOrBlank()) {
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = msg.actionHint,
                                        style = MaterialTheme.typography.labelSmall,
                                        color = ElectricCyan
                                    )
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            // Input Row + Push-to-Talk Mic Button
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(bottom = 10.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = commandDraft,
                    onValueChange = { commandDraft = it },
                    placeholder = { Text("Type or speak in ${selectedLanguage.displayName}...") },
                    modifier = Modifier.weight(1f),
                    singleLine = true,
                    trailingIcon = {
                        IconButton(
                            onClick = {
                                if (commandDraft.isNotBlank()) {
                                    viewModel.stopAndProcessVoiceCommand(commandDraft)
                                    commandDraft = ""
                                }
                            }
                        ) {
                            Icon(Icons.AutoMirrored.Rounded.Send, contentDescription = "Send command", tint = ElectricCyan)
                        }
                    }
                )
                Spacer(modifier = Modifier.width(10.dp))
                FloatingActionButton(
                    onClick = {
                        if (!hasAudioPermission) {
                            onRequestAudioPermission()
                        } else if (!isListening) {
                            viewModel.startVoiceCapture(true)
                        } else {
                            val prompt = commandDraft.ifBlank {
                                when (selectedLanguage) {
                                    VoiceLanguage.Hindi -> "Aaj ke pending approvals aur reels status batao"
                                    VoiceLanguage.Hinglish -> "Instagram reel ke liye ek fresh Hinglish hook draft karo"
                                    VoiceLanguage.English -> "Summarize pending approvals and schedule status"
                                }
                            }
                            commandDraft = ""
                            viewModel.stopAndProcessVoiceCommand(prompt)
                        }
                    },
                    shape = CircleShape,
                    containerColor = if (isListening) CoralDanger else ElectricCyan,
                    contentColor = MidnightNavy,
                    modifier = Modifier.size(56.dp)
                ) {
                    Icon(
                        imageVector = if (isListening) Icons.Rounded.Stop else Icons.Rounded.Mic,
                        contentDescription = if (isListening) "Stop listening" else "Push to talk"
                    )
                }
            }
        }
    }
}
