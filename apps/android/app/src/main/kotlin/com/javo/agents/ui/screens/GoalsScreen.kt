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
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.LinearProgressIndicator
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
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.MidnightNavy
import com.javo.agents.ui.viewmodel.MainViewModel
import kotlin.math.roundToInt

@Composable
fun GoalsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val goals by viewModel.goals.collectAsState()
    var showAddDialog by remember { mutableStateOf(false) }

    if (showAddDialog) {
        var title by remember { mutableStateOf("") }
        var desc by remember { mutableStateOf("") }
        var deadline by remember { mutableStateOf("") }

        AlertDialog(
            onDismissRequest = { showAddDialog = false },
            title = { Text("Create Growth Goal") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = title, onValueChange = { title = it }, label = { Text("Goal Title") }, singleLine = true)
                    OutlinedTextField(value = desc, onValueChange = { desc = it }, label = { Text("Description") }, minLines = 2)
                    OutlinedTextField(value = deadline, onValueChange = { deadline = it }, label = { Text("Target Date") }, singleLine = true)
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.addGoal(title, desc, deadline)
                        showAddDialog = false
                    }
                ) { Text("Save Goal") }
            },
            dismissButton = {
                TextButton(onClick = { showAddDialog = false }) { Text("Cancel") }
            }
        )
    }

    JavoSubScreenScaffold(
        title = "Goals & Milestones",
        onBack = onBack,
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddDialog = true },
                containerColor = ElectricCyan,
                contentColor = MidnightNavy
            ) {
                Icon(Icons.Rounded.Add, contentDescription = "Add goal")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(goals, key = { it.id }) { goal ->
                StatusCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(goal.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                        StatusPill(text = goal.deadlineLabel, color = EmeraldSuccess)
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(goal.description, style = MaterialTheme.typography.bodyMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                    Spacer(modifier = Modifier.height(10.dp))
                    LinearProgressIndicator(
                        progress = { goal.progress.coerceIn(0f, 1f) },
                        modifier = Modifier.fillMaxWidth(),
                        color = ElectricCyan
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(goal.milestoneSummary, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
                        Text("${(goal.progress * 100).roundToInt()}%", style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                    }
                }
            }
        }
    }
}
