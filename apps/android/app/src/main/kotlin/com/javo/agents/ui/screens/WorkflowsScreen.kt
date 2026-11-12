package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AssistChip
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun WorkflowsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val workflows by viewModel.workflows.collectAsState()

    JavoSubScreenScaffold(title = "Workflows", onBack = onBack) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                StatusCard(highlightGradient = true) {
                    Text("Deterministic Node Pipelines", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Workflow graphs are authored on your Windows Desktop builder and can be monitored or toggled safely from Android.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            items(workflows, key = { it.id }) { wf ->
                StatusCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(wf.name, style = MaterialTheme.typography.titleMedium)
                            Spacer(modifier = Modifier.height(4.dp))
                            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                StatusPill(text = wf.triggerType, color = ElectricCyan)
                                if (wf.requiresApproval) {
                                    StatusPill(text = "Approval Gate", color = VioletAccent)
                                }
                            }
                        }
                        Switch(
                            checked = wf.isActive,
                            onCheckedChange = { viewModel.toggleWorkflow(wf.id) }
                        )
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        wf.lastRunSummary,
                        style = MaterialTheme.typography.bodyMedium,
                        color = if (wf.isActive) EmeraldSuccess else MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(8.dp))
                    FlowRow(
                        horizontalArrangement = Arrangement.spacedBy(6.dp),
                        verticalArrangement = Arrangement.spacedBy(4.dp)
                    ) {
                        wf.nodes.forEach { node ->
                            AssistChip(onClick = {}, label = { Text(node) })
                        }
                    }
                }
            }
        }
    }
}
