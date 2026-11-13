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
import androidx.compose.material.icons.rounded.DeleteOutline
import androidx.compose.material.icons.rounded.GraphicEq
import androidx.compose.material.icons.rounded.Mic
import androidx.compose.material.icons.rounded.Stop
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.SuggestionChip
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
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.model.WaveformState
import com.javo.agents.ui.components.BottomNavBar
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.WaveformVisualizer
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
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
    val liveTranscript by viewModel.liveSpeechTranscript.collectAsState()
    val liveRmsAmplitude by viewModel.liveRmsAmplitude.collectAsState()

    var commandDraft by remember { mutableStateOf("") }
    val isListening = waveformState == WaveformState.Listening

    JavoSubScreenScaffold(
        title = "Voice Mode & Assistant",
        actions = {
            if (messages.isNotEmpty()) {
                IconButton(onClick = { viewModel.clearVoiceHistory() }) {
                    Icon(
                        Icons.Rounded.DeleteOutline,
                        contentDescription = "Clear conversation",
                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }
        },
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
                    height = 84.dp,
                    showStateLabel = true,
                    liveAmplitude = if (isListening) liveRmsAmplitude else null
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = when {
                        isListening && liveTranscript.isNotBlank() -> "\"$liveTranscript\""
                        isListening -> "Listening in ${selectedLanguage.displayName}... Speak now"
                        waveformState == WaveformState.Thinking -> "Processing ${selectedLanguage.displayName} intent with AI..."
                        waveformState == WaveformState.Executing -> "Coordinating agent response..."
                        waveformState == WaveformState.Finished -> "Done! Ready for next command."
                        else -> "Tap mic for Push-to-Talk (${selectedLanguage.displayName}) or type below"
                    },
                    style = MaterialTheme.typography.bodyMedium,
                    fontWeight = if (isListening && liveTranscript.isNotBlank()) FontWeight.Medium else FontWeight.Normal,
                    color = if (isListening && liveTranscript.isNotBlank()) ElectricCyan else MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(10.dp))

            // Conversation Messages Area
            if (messages.isEmpty()) {
                // Clean empty state with interactive prompts
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                        modifier = Modifier.padding(16.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.GraphicEq,
                            contentDescription = "Voice Assistant",
                            modifier = Modifier.size(48.dp),
                            tint = ElectricCyan.copy(alpha = 0.6f)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = "Javo Voice & Chat",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = "Ask questions or create content in English, Hindi, or Hinglish.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                        Spacer(modifier = Modifier.height(16.dp))
                        Text(
                            text = "Quick suggestions:",
                            style = MaterialTheme.typography.labelSmall,
                            color = VioletAccent
                        )
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.Center
                        ) {
                            SuggestionChip(
                                onClick = { commandDraft = "Who are you and what can you do?" },
                                label = { Text("What can you do?") }
                            )
                            Spacer(modifier = Modifier.width(8.dp))
                            SuggestionChip(
                                onClick = { commandDraft = "Draft a Hinglish reel hook about local AI" },
                                label = { Text("Draft Hinglish Reel") }
                            )
                        }
                    }
                }
            } else {
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
                                        text = if (msg.isUser) "You (${msg.language.displayName})" else "Javo Agent",
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
                                            color = if (msg.actionHint.contains("Error", ignoreCase = true)) CoralDanger else EmeraldSuccess
                                        )
                                    }
                                }
                            }
                        }
                    }

                    // Live transcript bubble while listening
                    if (isListening && liveTranscript.isNotBlank()) {
                        item {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.End
                            ) {
                                Box(
                                    modifier = Modifier
                                        .fillMaxWidth(0.86f)
                                        .clip(RoundedCornerShape(16.dp))
                                        .background(ElectricCyan.copy(alpha = 0.16f))
                                        .padding(12.dp)
                                ) {
                                    Column {
                                        Text(
                                            text = "Listening (${selectedLanguage.displayName})...",
                                            style = MaterialTheme.typography.labelSmall,
                                            color = ElectricCyan
                                        )
                                        Spacer(modifier = Modifier.height(4.dp))
                                        Text(liveTranscript, style = MaterialTheme.typography.bodyMedium)
                                    }
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
                            val candidate = if (commandDraft.isNotBlank()) commandDraft else liveTranscript
                            commandDraft = ""
                            viewModel.stopVoiceListening()
                            if (candidate.isNotBlank()) {
                                viewModel.stopAndProcessVoiceCommand(candidate)
                            }
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
