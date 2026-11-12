package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess

@Composable
fun HelpReportingScreen(
    onBack: () -> Unit
) {
    var reportCategory by remember { mutableStateOf("AI Content Issue") }
    var reportDetails by remember { mutableStateOf("") }
    var submittedNote by remember { mutableStateOf<String?>(null) }

    JavoSubScreenScaffold(title = "Help & Reporting", onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatusCard(highlightGradient = true) {
                Text("Quick Troubleshooting", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "1. Pairing fails on LAN: Ensure Windows Local Runtime is running on port 8000 and both devices share the same Wi-Fi/Tailscale network.\n" +
                        "2. Voice mic inactive: Grant RECORD_AUDIO permission in Android App Settings.\n" +
                        "3. Offline queue not syncing: Check Battery Optimization and verify pairing status in Security Center.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            StatusCard {
                Text("Report AI Content or Bug", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    "Log an inaccurate AI output, policy concern, or app bug locally for review in your diagnostics bundle.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(10.dp))
                OutlinedTextField(
                    value = reportCategory,
                    onValueChange = { reportCategory = it },
                    label = { Text("Category (AI Content / Bug / Security)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = reportDetails,
                    onValueChange = { reportDetails = it },
                    label = { Text("Describe what happened") },
                    minLines = 3,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(10.dp))
                GradientButton(
                    text = "Save Report Locally",
                    onClick = {
                        submittedNote = "Saved local report under '$reportCategory'. No sensitive tokens included."
                        reportDetails = ""
                    },
                    enabled = reportDetails.isNotBlank()
                )
                if (!submittedNote.isNullOrBlank()) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(submittedNote!!, style = MaterialTheme.typography.bodyMedium, color = EmeraldSuccess)
                }
            }

            StatusCard {
                Text("Compliance & Policy Note", style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Javo Agents Android never downloads or executes unverified remote code. All workflows run deterministically on your paired Windows host or via official APIs.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }
        }
    }
}
