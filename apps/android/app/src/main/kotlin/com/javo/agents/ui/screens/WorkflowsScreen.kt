package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.ExperimentalLayoutApi
import androidx.compose.foundation.layout.FlowRow
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.Alarm
import androidx.compose.material.icons.rounded.DeleteOutline
import androidx.compose.material.icons.rounded.PlayArrow
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.AssistChip
import androidx.compose.material3.Checkbox
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Switch
import androidx.compose.material3.Tab
import androidx.compose.material3.TabRow
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.javo.agents.data.local.TaskEntity
import com.javo.agents.data.model.AgentInfo
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoOutlinedButton
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

@OptIn(ExperimentalLayoutApi::class)
@Composable
fun WorkflowsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val workflows by viewModel.workflows.collectAsState()
    val tasks by viewModel.tasks.collectAsState()
    val agents by viewModel.agents.collectAsState()
    val isExecutingTaskId by viewModel.isExecutingTask.collectAsState()

    var selectedTabIndex by remember { mutableIntStateOf(0) }
    var showCreateTaskDialog by remember { mutableStateOf(false) }

    if (showCreateTaskDialog) {
        var taskTitle by remember { mutableStateOf("") }
        var taskDesc by remember { mutableStateOf("") }
        var selectedAgent by remember { mutableStateOf(agents.firstOrNull { it.capability.isAndroidCompatible } ?: agents.first()) }
        var enableReminder by remember { mutableStateOf(true) }
        var scheduleDelayOption by remember { mutableIntStateOf(0) } // 0 = Now, 1 = 1 Hour, 2 = Tomorrow (24h)

        AlertDialog(
            onDismissRequest = { showCreateTaskDialog = false },
            title = { Text("Create Autonomous Task") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = taskTitle,
                        onValueChange = { taskTitle = it },
                        label = { Text("Task Goal / Objective") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = taskDesc,
                        onValueChange = { taskDesc = it },
                        label = { Text("Details & Context (Optional)") },
                        minLines = 2,
                        modifier = Modifier.fillMaxWidth()
                    )

                    Spacer(modifier = Modifier.height(4.dp))
                    Text("Assign Autonomous Agent", style = MaterialTheme.typography.titleSmall)

                    // Agent selector list (first 5 mobile friendly)
                    val candidateAgents = agents.filter { it.capability.isAndroidCompatible }.take(4) +
                        agents.filter { it.capability.requiresWindows }.take(1)

                    candidateAgents.forEach { agent ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            RadioButton(
                                selected = selectedAgent.slug == agent.slug,
                                onClick = { selectedAgent = agent }
                            )
                            Column(modifier = Modifier.weight(1f)) {
                                Text(agent.displayName, style = MaterialTheme.typography.titleSmall)
                                Text(
                                    agent.capability.executionPlatform,
                                    style = MaterialTheme.typography.labelSmall,
                                    color = if (agent.capability.isAndroidCompatible) EmeraldSuccess else CoralDanger
                                )
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(4.dp))
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(
                            checked = enableReminder,
                            onCheckedChange = { enableReminder = it }
                        )
                        Text("WorkManager Autonomous Reminder", style = MaterialTheme.typography.bodyMedium)
                    }

                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(6.dp)
                    ) {
                        listOf("Run Now", "In 1 Hour", "Tomorrow").forEachIndexed { idx, label ->
                            AssistChip(
                                onClick = { scheduleDelayOption = idx },
                                label = { Text(label) }
                            )
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        if (taskTitle.isNotBlank()) {
                            val scheduledMs: Long? = when (scheduleDelayOption) {
                                1 -> System.currentTimeMillis() + 3600000L
                                2 -> System.currentTimeMillis() + 86400000L
                                else -> null
                            }
                            viewModel.createLocalTask(
                                title = taskTitle,
                                assignedAgent = selectedAgent.slug,
                                priority = "normal",
                                description = taskDesc,
                                scheduledEpochMs = scheduledMs,
                                isReminderEnabled = enableReminder
                            )
                            showCreateTaskDialog = false
                        }
                    }
                ) { Text("Create Task") }
            },
            dismissButton = {
                TextButton(onClick = { showCreateTaskDialog = false }) { Text("Cancel") }
            }
        )
    }

    JavoSubScreenScaffold(
        title = "Tasks & Workflows",
        onBack = onBack,
        floatingActionButton = {
            if (selectedTabIndex == 0) {
                FloatingActionButton(
                    onClick = { showCreateTaskDialog = true },
                    containerColor = ElectricCyan,
                    contentColor = MidnightNavy
                ) {
                    Icon(Icons.Rounded.Add, contentDescription = "Create Task")
                }
            }
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
        ) {
            TabRow(selectedTabIndex = selectedTabIndex) {
                Tab(
                    selected = selectedTabIndex == 0,
                    onClick = { selectedTabIndex = 0 },
                    text = { Text("Autonomous Tasks (${tasks.size})") }
                )
                Tab(
                    selected = selectedTabIndex == 1,
                    onClick = { selectedTabIndex = 1 },
                    text = { Text("Windows Graphs") }
                )
            }

            if (selectedTabIndex == 0) {
                // Tasks List
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    item {
                        StatusCard(highlightGradient = true) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text("Autonomous Mobile Execution", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                                StatusPill(text = "📱 On-Device", color = EmeraldSuccess)
                            }
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                "Tasks assigned to Android-compatible agents can be executed directly on your phone using Google Gemini BYOK or Custom Endpoint.",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                    }

                    if (tasks.isEmpty()) {
                        item {
                            StatusCard {
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 24.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally
                                ) {
                                    Text("No Active Tasks", style = MaterialTheme.typography.titleMedium)
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        "0 queued tasks. Tap '+' to create an autonomous agent goal with optional WorkManager scheduling.",
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                        }
                    }

                    items(tasks, key = { it.id }) { task ->
                        val isExecutingThis = isExecutingTaskId == task.id
                        val agent = agents.find { it.slug == task.assignedAgent }
                        val isAndroidReady = agent?.capability?.isAndroidCompatible ?: true

                        StatusCard {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Text(task.title, style = MaterialTheme.typography.titleMedium)
                                    Spacer(modifier = Modifier.height(2.dp))
                                    Text(
                                        "Assigned: ${agent?.displayName ?: task.assignedAgent} • ${if (isAndroidReady) "Android Ready" else "Requires Windows"}",
                                        style = MaterialTheme.typography.bodySmall,
                                        color = if (isAndroidReady) ElectricCyan else CoralDanger
                                    )
                                }
                                val statusColor = when (task.state) {
                                    "completed" -> EmeraldSuccess
                                    "running" -> ElectricCyan
                                    "failed" -> CoralDanger
                                    else -> AmberWarning
                                }
                                StatusPill(text = task.state.replaceFirstChar { it.uppercase() }, color = statusColor)
                                IconButton(onClick = { viewModel.deleteTask(task.id) }) {
                                    Icon(Icons.Rounded.DeleteOutline, contentDescription = "Delete", tint = MaterialTheme.colorScheme.onSurfaceVariant)
                                }
                            }

                            if (task.description.isNotBlank()) {
                                Spacer(modifier = Modifier.height(6.dp))
                                Text(task.description, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }

                            if (task.scheduledEpochMs != null) {
                                Spacer(modifier = Modifier.height(6.dp))
                                Row(verticalAlignment = Alignment.CenterVertically) {
                                    Icon(Icons.Rounded.Alarm, contentDescription = "Alarm", tint = ElectricCyan, modifier = Modifier.padding(end = 4.dp))
                                    Text("Scheduled Reminder Enabled", style = MaterialTheme.typography.labelSmall, color = ElectricCyan)
                                }
                            }

                            // Output section
                            if (!task.resultOutput.isNullOrBlank()) {
                                Spacer(modifier = Modifier.height(8.dp))
                                Text("Execution Result:", style = MaterialTheme.typography.titleSmall, color = EmeraldSuccess)
                                Spacer(modifier = Modifier.height(2.dp))
                                Text(
                                    task.resultOutput,
                                    style = MaterialTheme.typography.bodySmall,
                                    color = MaterialTheme.colorScheme.onSurface
                                )
                            }

                            if (!task.errorMessage.isNullOrBlank()) {
                                Spacer(modifier = Modifier.height(8.dp))
                                Text("Error: ${task.errorMessage}", style = MaterialTheme.typography.bodySmall, color = CoralDanger)
                            }

                            if (task.state == "pending" || task.state == "failed") {
                                Spacer(modifier = Modifier.height(10.dp))
                                GradientButton(
                                    text = if (isExecutingThis) "Executing on Phone..." else if (isAndroidReady) "Run on Phone ▶" else "Requires Windows PC",
                                    onClick = { viewModel.executeTaskLocally(task.id) },
                                    enabled = !isExecutingThis && isAndroidReady
                                )
                            }
                        }
                    }
                    item { Spacer(modifier = Modifier.height(80.dp)) }
                }
            } else {
                // Windows Graphs List
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
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

                    if (workflows.isEmpty()) {
                        item {
                            StatusCard {
                                Column(
                                    modifier = Modifier
                                        .fillMaxWidth()
                                        .padding(vertical = 24.dp),
                                    horizontalAlignment = Alignment.CenterHorizontally
                                ) {
                                    Text("No Workflows Configured", style = MaterialTheme.typography.titleMedium)
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        "0 active automation graphs. Author deterministic pipelines on your Windows desktop builder or enable Demo Mode in Settings.",
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                                        textAlign = androidx.compose.ui.text.style.TextAlign.Center
                                    )
                                }
                            }
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
                    item { Spacer(modifier = Modifier.height(80.dp)) }
                }
            }
        }
    }
}
