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
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun CalendarScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val drafts by viewModel.drafts.collectAsState()
    val approvals by viewModel.approvals.collectAsState()

    val scheduledDrafts = drafts.filter { !it.scheduledDateLabel.isNullOrBlank() }

    JavoSubScreenScaffold(title = "Publishing Calendar", onBack = onBack) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                StatusCard(highlightGradient = true) {
                    Text("Supervised Publishing Schedule", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Items publish through Windows Content Publisher only after passing Approval Manager gates.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            items(scheduledDrafts, key = { it.id }) { item ->
                StatusCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(item.scheduledDateLabel.orEmpty(), style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                            Spacer(modifier = Modifier.height(2.dp))
                            Text(item.title, style = MaterialTheme.typography.titleMedium)
                        }
                        StatusPill(text = item.platform, color = VioletAccent)
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(item.body, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                }
            }

            item {
                Text("Approval-Gated Slots", style = MaterialTheme.typography.titleMedium)
            }

            items(approvals, key = { it.id }) { apr ->
                StatusCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(apr.scheduledFor, style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                            Text(apr.title, style = MaterialTheme.typography.titleMedium)
                        }
                        StatusPill(
                            text = apr.status.replaceFirstChar { it.uppercase() },
                            color = if (apr.status == "approved") EmeraldSuccess else VioletAccent
                        )
                    }
                }
            }
        }
    }
}
