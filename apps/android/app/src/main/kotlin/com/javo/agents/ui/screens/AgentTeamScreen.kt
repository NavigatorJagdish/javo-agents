package com.javo.agents.ui.screens

import androidx.compose.foundation.horizontalScroll
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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilterChip
import androidx.compose.material3.MaterialTheme
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
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.AgentCategory
import com.javo.agents.data.model.AgentInfo
import com.javo.agents.ui.components.BottomNavBar
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun AgentTeamScreen(
    viewModel: MainViewModel,
    currentRoute: String?,
    onNavigate: (String) -> Unit
) {
    val agents by viewModel.agents.collectAsState()
    val templates by viewModel.templates.collectAsState()
    val approvals by viewModel.approvals.collectAsState()

    var selectedTab by remember { mutableIntStateOf(0) }
    var selectedCategory by remember { mutableStateOf<AgentCategory?>(null) }
    var inspectedAgent by remember { mutableStateOf<AgentInfo?>(null) }

    val filteredAgents = remember(agents, selectedCategory) {
        if (selectedCategory == null) agents else agents.filter { it.category == selectedCategory }
    }

    if (inspectedAgent != null) {
        val agent = inspectedAgent!!
        AlertDialog(
            onDismissRequest = { inspectedAgent = null },
            title = { Text("#${agent.number.toString().padStart(2, '0')} ${agent.displayName}") },
            text = {
                Column {
                    Text(agent.description, style = MaterialTheme.typography.bodyMedium)
                    Spacer(modifier = Modifier.height(10.dp))
                    Text("Capabilities:", style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                    agent.capabilities.forEach { cap ->
                        Text("• $cap", style = MaterialTheme.typography.bodyMedium)
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Permissions:", style = MaterialTheme.typography.labelMedium, color = VioletAccent)
                    Text(agent.requiredPermissions.joinToString(", "), style = MaterialTheme.typography.bodyMedium)
                }
            },
            confirmButton = {
                TextButton(onClick = { inspectedAgent = null }) { Text("Close") }
            }
        )
    }

    JavoSubScreenScaffold(
        title = "AI Agent Team (${agents.size})",
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
        ) {
            TabRow(selectedTabIndex = selectedTab) {
                Tab(
                    selected = selectedTab == 0,
                    onClick = { selectedTab = 0 },
                    text = { Text("My Agents (${agents.size})") }
                )
                Tab(
                    selected = selectedTab == 1,
                    onClick = { selectedTab = 1 },
                    text = { Text("Templates (${templates.size})") }
                )
            }

            if (selectedTab == 0) {
                Row(
                    modifier = Modifier
                        .fillMaxWidth()
                        .horizontalScroll(rememberScrollState())
                        .padding(horizontal = 16.dp, vertical = 8.dp),
                    horizontalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    FilterChip(
                        selected = selectedCategory == null,
                        onClick = { selectedCategory = null },
                        label = { Text("All") }
                    )
                    AgentCategory.entries.forEach { cat ->
                        FilterChip(
                            selected = selectedCategory == cat,
                            onClick = { selectedCategory = if (selectedCategory == cat) null else cat },
                            label = { Text(cat.label) }
                        )
                    }
                }

                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(filteredAgents, key = { it.slug }) { agent ->
                        StatusCard(onClick = { inspectedAgent = agent }) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Column(modifier = Modifier.weight(1f)) {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        Text(
                                            text = "${agent.number.toString().padStart(2, '0')}. ${agent.displayName}",
                                            style = MaterialTheme.typography.titleMedium
                                        )
                                        Spacer(modifier = Modifier.width(8.dp))
                                        StatusPill(
                                            text = agent.category.label,
                                            color = if (agent.isEnabled) EmeraldSuccess else VioletAccent
                                        )
                                    }
                                    Spacer(modifier = Modifier.height(4.dp))
                                    Text(
                                        text = agent.description,
                                        style = MaterialTheme.typography.bodyMedium,
                                        color = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                                Spacer(modifier = Modifier.width(8.dp))
                                Switch(
                                    checked = agent.isEnabled,
                                    onCheckedChange = { viewModel.toggleAgentEnabled(agent.slug) }
                                )
                            }
                        }
                    }
                    item { Spacer(modifier = Modifier.height(12.dp)) }
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .fillMaxSize()
                        .padding(16.dp),
                    verticalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    items(templates, key = { it.slug }) { tpl ->
                        StatusCard(highlightGradient = tpl.isEnabled) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(tpl.displayName, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                                StatusPill(
                                    text = tpl.status,
                                    color = if (tpl.isEnabled) EmeraldSuccess else ElectricCyan
                                )
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(
                                text = tpl.description,
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(modifier = Modifier.height(10.dp))
                            JavoOutlinedButton(
                                text = if (tpl.isEnabled) "Applied to Pipeline" else "Apply Template",
                                onClick = { viewModel.activateTemplate(tpl.slug) }
                            )
                        }
                    }
                }
            }
        }
    }
}
