package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.DataProvenance
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.AmberWarning
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun AnalyticsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    // Subscribe to flows so counts refresh live
    val drafts by viewModel.drafts.collectAsState()
    val approvals by viewModel.approvals.collectAsState()
    val agents by viewModel.agents.collectAsState()
    val connection by viewModel.connectionState.collectAsState()

    val metrics = viewModel.getAnalyticsMetrics()

    JavoSubScreenScaffold(title = "Analytics & Provenance", onBack = onBack) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                StatusCard(highlightGradient = true) {
                    Text("Truthful Telemetry Policy", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Javo Agents strictly distinguishes real on-device/runtime metrics from unavailable external platform data. Current bridge: ${connection.label} (${agents.size} agents, ${drafts.size} drafts, ${approvals.size} approvals).",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            items(metrics, key = { it.id }) { metric ->
                val pillColor = when (metric.provenance) {
                    DataProvenance.REAL_RUNTIME -> EmeraldSuccess
                    DataProvenance.LOCAL_DEVICE -> ElectricCyan
                    DataProvenance.DEMO_UNAVAILABLE -> AmberWarning
                }
                StatusCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(metric.label, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                        StatusPill(text = metric.provenance.badge, color = pillColor)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(verticalAlignment = Alignment.Bottom) {
                        Text(metric.value, style = MaterialTheme.typography.headlineMedium, color = pillColor)
                        Spacer(modifier = Modifier.weight(1f))
                        Text(metric.delta, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(metric.note, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }
        }
    }
}
