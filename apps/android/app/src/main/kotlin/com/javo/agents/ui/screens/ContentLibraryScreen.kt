package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.Sync
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
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
import com.javo.agents.ui.components.BottomNavBar
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.AmberWarning
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.MidnightNavy
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun ContentLibraryScreen(
    viewModel: MainViewModel,
    currentRoute: String?,
    onNavigate: (String) -> Unit
) {
    val drafts by viewModel.drafts.collectAsState()
    val approvals by viewModel.approvals.collectAsState()

    var showCreateDialog by remember { mutableStateOf(false) }
    var filterMode by remember { mutableStateOf("All") }

    val filtered = remember(drafts, filterMode) {
        when (filterMode) {
            "Offline Queue" -> drafts.filter { it.pendingSync }
            "Synced" -> drafts.filter { !it.pendingSync }
            else -> drafts
        }
    }

    if (showCreateDialog) {
        var title by remember { mutableStateOf("") }
        var body by remember { mutableStateOf("") }
        var platform by remember { mutableStateOf("Instagram") }
        var schedule by remember { mutableStateOf("") }

        AlertDialog(
            onDismissRequest = { showCreateDialog = false },
            title = { Text("New Offline Draft") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("Title / Hook") }, singleLine = true)
                    OutlinedTextField(value = body, onValueChange = { body = it }, label = { Text("Caption / Script") }, minLines = 3)
                    OutlinedTextField(value = platform, onValueChange = { platform = it }, label = { Text("Platform (Instagram/Facebook/YouTube)") }, singleLine = true)
                    OutlinedTextField(value = schedule, onValueChange = { schedule = it }, label = { Text("Target Date (optional)") }, singleLine = true)
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.createOfflineDraft(title, body, platform, schedule.ifBlank { null })
                        showCreateDialog = false
                    }
                ) { Text("Save Offline") }
            },
            dismissButton = {
                TextButton(onClick = { showCreateDialog = false }) { Text("Cancel") }
            }
        )
    }

    JavoSubScreenScaffold(
        title = "Content Studio",
        actions = {
            IconButton(onClick = { viewModel.syncNow() }) {
                Icon(Icons.Rounded.Sync, contentDescription = "Sync drafts", tint = ElectricCyan)
            }
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showCreateDialog = true },
                containerColor = ElectricCyan,
                contentColor = MidnightNavy
            ) {
                Icon(Icons.Rounded.Add, contentDescription = "Create draft")
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
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("All", "Offline Queue", "Synced").forEach { mode ->
                    FilterChip(
                        selected = filterMode == mode,
                        onClick = { filterMode = mode },
                        label = { Text(mode) }
                    )
                }
            }
            Spacer(modifier = Modifier.height(8.dp))
            LazyColumn(
                modifier = Modifier.fillMaxSize(),
                verticalArrangement = Arrangement.spacedBy(10.dp)
            ) {
                items(filtered, key = { it.id }) { draft ->
                    StatusCard {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(draft.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                            StatusPill(
                                text = if (draft.pendingSync) "Queued Sync" else "Synced",
                                color = if (draft.pendingSync) AmberWarning else EmeraldSuccess
                            )
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(draft.body, style = MaterialTheme.typography.bodyMedium)
                        Spacer(modifier = Modifier.height(6.dp))
                        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                            Text(draft.platform, style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                            Text(draft.scheduledDateLabel ?: "Unscheduled", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        }
                    }
                }
                item { Spacer(modifier = Modifier.height(72.dp)) }
            }
        }
    }
}
