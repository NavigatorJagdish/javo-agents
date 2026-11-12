package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.data.local.ApprovalEntity
import com.javo.agents.ui.components.BottomNavBar
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.AmberWarning
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.MidnightNavy
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun ApprovalInboxScreen(
    viewModel: MainViewModel,
    currentRoute: String?,
    onNavigate: (String) -> Unit
) {
    val approvals by viewModel.approvals.collectAsState()
    var editingItem by remember { mutableStateOf<ApprovalEntity?>(null) }

    if (editingItem != null) {
        val item = editingItem!!
        var editedText by remember(item.id) { mutableStateOf(item.previewContent) }
        var editedSchedule by remember(item.id) { mutableStateOf(item.scheduledFor) }

        AlertDialog(
            onDismissRequest = { editingItem = null },
            title = { Text("Edit / Reschedule") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = editedText,
                        onValueChange = { editedText = it },
                        label = { Text("Content") },
                        minLines = 3
                    )
                    OutlinedTextField(
                        value = editedSchedule,
                        onValueChange = { editedSchedule = it },
                        label = { Text("Schedule Slot") },
                        singleLine = true
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.decideApproval(item.id, "rescheduled", editedText, editedSchedule)
                        editingItem = null
                    }
                ) { Text("Save & Reschedule") }
            },
            dismissButton = {
                TextButton(onClick = { editingItem = null }) { Text("Cancel") }
            }
        )
    }

    JavoSubScreenScaffold(
        title = "Approval Inbox",
        bottomBar = {
            BottomNavBar(
                currentRoute = currentRoute,
                pendingApprovalsCount = approvals.count { it.status == "pending" },
                onNavigate = onNavigate
            )
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            item {
                StatusCard(highlightGradient = true) {
                    Text("Supervised Autopilot Gate", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Approve, edit, reschedule, or reject sensitive agent actions before anything goes live.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            items(approvals, key = { it.id }) { item ->
                val statusColor = when (item.status) {
                    "approved" -> EmeraldSuccess
                    "rejected" -> CoralDanger
                    "rescheduled" -> VioletAccent
                    else -> AmberWarning
                }
                StatusCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(item.title, style = MaterialTheme.typography.titleMedium)
                            Text("${item.agentName} • ${item.platform} • ${item.scheduledFor}", style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                        }
                        StatusPill(text = item.status.replaceFirstChar { it.uppercase() }, color = statusColor)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(item.previewContent, style = MaterialTheme.typography.bodyMedium)
                    Spacer(modifier = Modifier.height(10.dp))

                    Row(modifier = Modifier.fillMaxWidth()) {
                        Button(
                            onClick = {
                                viewModel.decideApproval(item.id, "approved", item.previewContent, item.scheduledFor)
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = ElectricCyan,
                                contentColor = MidnightNavy
                            ),
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Approve")
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        OutlinedButton(
                            onClick = { editingItem = item },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Edit")
                        }
                        Spacer(modifier = Modifier.width(8.dp))
                        OutlinedButton(
                            onClick = {
                                viewModel.decideApproval(item.id, "rejected", item.previewContent, item.scheduledFor)
                            },
                            modifier = Modifier.weight(1f)
                        ) {
                            Text("Reject", color = CoralDanger)
                        }
                    }
                }
            }
        }
    }
}
