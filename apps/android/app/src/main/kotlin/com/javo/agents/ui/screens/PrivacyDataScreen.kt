package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun PrivacyDataScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val snapshot by viewModel.exportedSnapshot.collectAsState()
    var confirmDelete by remember { mutableStateOf(false) }

    if (confirmDelete) {
        AlertDialog(
            onDismissRequest = { confirmDelete = false },
            title = { Text("Delete All Local Data?") },
            text = { Text("This wipes your Room database (drafts, goals, approvals, tasks, notifications) and clears Android Keystore tokens & API keys.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.deleteAllLocalData()
                        confirmDelete = false
                    }
                ) { Text("Delete Everything", color = CoralDanger) }
            },
            dismissButton = {
                TextButton(onClick = { confirmDelete = false }) { Text("Cancel") }
            }
        )
    }

    JavoSubScreenScaffold(title = "Privacy & Data", onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatusCard(highlightGradient = true) {
                Text("Google Play Data Safety Summary", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "• No third-party ad SDKs, tracking pixels, or analytics brokers.\n" +
                        "• Drafts, approvals, and goals are stored locally on your device and synced only with the Windows host you explicitly pair.\n" +
                        "• Microphone audio is only processed when you trigger Voice Mode.\n" +
                        "• Gemini API usage is strictly opt-in using your own key stored in Android Keystore.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            GradientButton(
                text = "Export Local Data Snapshot (JSON)",
                onClick = { viewModel.exportLocalData() }
            )

            if (!snapshot.isNullOrBlank()) {
                StatusCard {
                    Text("Local Export Preview", style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(snapshot!!, style = MaterialTheme.typography.bodyMedium)
                }
            }

            JavoOutlinedButton(
                text = "Delete All Local Data & Secrets",
                onClick = { confirmDelete = true },
                borderColor = CoralDanger
            )
        }
    }
}
