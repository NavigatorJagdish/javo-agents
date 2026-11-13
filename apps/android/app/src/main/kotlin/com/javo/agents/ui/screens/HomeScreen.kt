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
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AccountTree
import androidx.compose.material.icons.rounded.Analytics
import androidx.compose.material.icons.rounded.Assignment
import androidx.compose.material.icons.rounded.CalendarMonth
import androidx.compose.material.icons.rounded.Cloud
import androidx.compose.material.icons.rounded.Computer
import androidx.compose.material.icons.rounded.Flag
import androidx.compose.material.icons.rounded.GraphicEq
import androidx.compose.material.icons.rounded.Notifications
import androidx.compose.material.icons.rounded.PostAdd
import androidx.compose.material.icons.rounded.Security
import androidx.compose.material.icons.rounded.Settings
import androidx.compose.material.icons.rounded.Share
import androidx.compose.material.icons.rounded.Shield
import androidx.compose.material.icons.rounded.Smartphone
import androidx.compose.material.icons.rounded.SmartToy
import androidx.compose.material.icons.rounded.Sync
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.unit.dp
import com.javo.agents.data.model.OperatingMode
import com.javo.agents.data.model.WaveformState
import com.javo.agents.ui.components.BottomNavBar
import com.javo.agents.ui.components.EmergencyStopDialog
import com.javo.agents.ui.components.JavoLogo
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.components.WaveformVisualizer
import com.javo.agents.ui.navigation.Routes
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.PureWhite
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    viewModel: MainViewModel,
    currentRoute: String?,
    onNavigate: (String) -> Unit
) {
    val agents by viewModel.agents.collectAsState()
    val approvals by viewModel.approvals.collectAsState()
    val drafts by viewModel.drafts.collectAsState()
    val tasks by viewModel.tasks.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()
    val waveformState by viewModel.waveformState.collectAsState()
    val operatingMode by viewModel.operatingMode.collectAsState()

    var showEmergencyDialog by remember { mutableStateOf(false) }
    var showModeDialog by remember { mutableStateOf(false) }

    val activeAgentsCount = agents.count { it.isEnabled }
    val pendingApprovals = approvals.count { it.status == "pending" }
    val queuedSyncCount = drafts.count { it.pendingSync }

    if (showModeDialog) {
        AlertDialog(
            onDismissRequest = { showModeDialog = false },
            title = { Text("Select Operating Mode") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OperatingMode.entries.forEach { mode ->
                        Row(
                            verticalAlignment = Alignment.CenterVertically,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            RadioButton(
                                selected = operatingMode == mode,
                                onClick = {
                                    viewModel.setOperatingMode(mode)
                                    showModeDialog = false
                                }
                            )
                            Column(modifier = Modifier.padding(start = 4.dp)) {
                                Text(mode.badge + " " + mode.displayName, style = MaterialTheme.typography.titleSmall)
                                Text(mode.description, style = MaterialTheme.typography.bodySmall, color = MaterialTheme.colorScheme.onSurfaceVariant)
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { showModeDialog = false }) {
                    Text("Close")
                }
            }
        )
    }

    if (showEmergencyDialog) {
        EmergencyStopDialog(
            onConfirmStop = {
                showEmergencyDialog = false
                viewModel.triggerEmergencyStop()
            },
            onDismiss = { showEmergencyDialog = false }
        )
    }

    Scaffold(
        containerColor = MaterialTheme.colorScheme.background,
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        JavoLogo(size = 32.dp, showOrbitalRing = false)
                        Spacer(modifier = Modifier.width(10.dp))
                        Text("Javo Agents", style = MaterialTheme.typography.titleMedium)
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.syncNow() }) {
                        Icon(Icons.Rounded.Sync, contentDescription = "Sync now", tint = ElectricCyan)
                    }
                    IconButton(onClick = { onNavigate(Routes.NOTIFICATIONS) }) {
                        Icon(Icons.Rounded.Notifications, contentDescription = "Notifications")
                    }
                    IconButton(onClick = { onNavigate(Routes.SETTINGS) }) {
                        Icon(Icons.Rounded.Settings, contentDescription = "Settings")
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.background
                )
            )
        },
        bottomBar = {
            BottomNavBar(
                currentRoute = currentRoute,
                pendingApprovalsCount = pendingApprovals,
                onNavigate = onNavigate
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(horizontal = 16.dp, vertical = 8.dp)
        ) {
            // Good morning / operating mode banner card
            StatusCard(onClick = { showModeDialog = true }) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Column(modifier = Modifier.weight(1f)) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Text(
                                text = "Good morning, Creator",
                                style = MaterialTheme.typography.headlineSmall
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = when (operatingMode) {
                                OperatingMode.ANDROID_STANDALONE -> "Operating in Android Standalone mode. Autonomous AI on your phone."
                                OperatingMode.WINDOWS_ENHANCED -> "Operating in Windows Enhanced mode with local desktop automation."
                                OperatingMode.CLOUD_MODE -> "Operating in Cloud Mode with remote AI services."
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                    Spacer(modifier = Modifier.width(8.dp))
                    Column(horizontalAlignment = Alignment.End) {
                        StatusPill(
                            text = operatingMode.badge,
                            color = ElectricCyan
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        val isConnected = connectionState.name == "Connected"
                        StatusPill(
                            text = if (operatingMode == OperatingMode.ANDROID_STANDALONE) "Independent" else connectionState.label,
                            color = if (operatingMode == OperatingMode.ANDROID_STANDALONE || isConnected) EmeraldSuccess else VioletAccent
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // AI Agent Team Active Waveform Card
            StatusCard(highlightGradient = true, onClick = { onNavigate(Routes.VOICE_MODE) }) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(
                        text = "AI Agent Team",
                        style = MaterialTheme.typography.titleMedium,
                        modifier = Modifier.weight(1f)
                    )
                    val isConnected = connectionState.name == "Connected"
                    val statusText = when (operatingMode) {
                        OperatingMode.ANDROID_STANDALONE -> "📱 Standalone • $activeAgentsCount Active"
                        OperatingMode.WINDOWS_ENHANCED -> if (isConnected) "Connected • $activeAgentsCount Active" else "PC Offline • Standby"
                        OperatingMode.CLOUD_MODE -> "☁️ Cloud • $activeAgentsCount Active"
                    }
                    val statusColor = if (operatingMode == OperatingMode.ANDROID_STANDALONE || isConnected) EmeraldSuccess else VioletAccent
                    StatusPill(text = statusText, color = statusColor)
                }
                Spacer(modifier = Modifier.height(10.dp))
                WaveformVisualizer(
                    state = waveformState,
                    barCount = 26,
                    height = 60.dp,
                    showStateLabel = true
                )
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Tap to open Voice Mode • Hindi / Hinglish / English Audio Assistant",
                    style = MaterialTheme.typography.labelMedium,
                    color = ElectricCyan
                )
            }

            Spacer(modifier = Modifier.height(14.dp))
            Text("Quick Actions", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))

            // 2x3 Quick Actions Grid
            Row(modifier = Modifier.fillMaxWidth()) {
                QuickActionTile(
                    icon = Icons.Rounded.GraphicEq,
                    title = "Talk to Javo",
                    subtitle = "Multilingual voice",
                    onClick = { onNavigate(Routes.VOICE_MODE) },
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(
                    icon = Icons.Rounded.PostAdd,
                    title = "Content Studio",
                    subtitle = "${drafts.size} local drafts",
                    onClick = { onNavigate(Routes.CONTENT_LIBRARY) },
                    modifier = Modifier.weight(1f)
                )
            }
            Spacer(modifier = Modifier.height(10.dp))
            Row(modifier = Modifier.fillMaxWidth()) {
                QuickActionTile(
                    icon = Icons.Rounded.Assignment,
                    title = "Tasks (${tasks.size})",
                    subtitle = "Autonomous agent jobs",
                    onClick = { onNavigate(Routes.WORKFLOWS) },
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(
                    icon = Icons.Rounded.Shield,
                    title = "Approvals ($pendingApprovals)",
                    subtitle = "Supervised autopilot",
                    onClick = { onNavigate(Routes.APPROVAL_INBOX) },
                    modifier = Modifier.weight(1f)
                )
            }
            Spacer(modifier = Modifier.height(10.dp))
            Row(modifier = Modifier.fillMaxWidth()) {
                QuickActionTile(
                    icon = Icons.Rounded.Share,
                    title = "Social Channels",
                    subtitle = "Instagram, YouTube, FB",
                    onClick = { onNavigate(Routes.CONNECTED_ACCOUNTS) },
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(
                    icon = Icons.Rounded.SmartToy,
                    title = "AI Providers",
                    subtitle = "Gemini BYOK / Custom",
                    onClick = { onNavigate(Routes.AI_PROVIDERS) },
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Automation Stats
            StatusCard {
                Text("Automation Stats", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(10.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    StatColumn("Local Tasks", tasks.size.toString())
                    StatColumn("Offline Drafts", drafts.size.toString())
                    StatColumn("Pending", pendingApprovals.toString())
                    StatColumn("Zero-Cost Cap", "$0.00")
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Secondary Hub Shortcuts
            Row(modifier = Modifier.fillMaxWidth()) {
                QuickActionTile(Icons.Rounded.Flag, "Goals", "Milestones", { onNavigate(Routes.GOALS) }, Modifier.weight(1f))
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(Icons.Rounded.Analytics, "Analytics", "Real vs Demo", { onNavigate(Routes.ANALYTICS) }, Modifier.weight(1f))
            }
            Spacer(modifier = Modifier.height(10.dp))
            Row(modifier = Modifier.fillMaxWidth()) {
                QuickActionTile(Icons.Rounded.SmartToy, "AI Providers", "Ollama / Gemini", { onNavigate(Routes.AI_PROVIDERS) }, Modifier.weight(1f))
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(Icons.Rounded.Security, "Security", "Pairing & Keys", { onNavigate(Routes.SECURITY) }, Modifier.weight(1f))
            }

            Spacer(modifier = Modifier.height(16.dp))

            // Emergency Stop Button
            Button(
                onClick = { showEmergencyDialog = true },
                modifier = Modifier
                    .fillMaxWidth()
                    .height(50.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = CoralDanger,
                    contentColor = PureWhite
                )
            ) {
                Icon(Icons.Rounded.Warning, contentDescription = "Emergency Stop")
                Spacer(modifier = Modifier.width(8.dp))
                Text("Emergency Stop All Agents", style = MaterialTheme.typography.titleMedium)
            }

            Spacer(modifier = Modifier.height(16.dp))
        }
    }
}

@Composable
private fun QuickActionTile(
    icon: ImageVector,
    title: String,
    subtitle: String,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    StatusCard(modifier = modifier, onClick = onClick) {
        Icon(icon, contentDescription = title, tint = ElectricCyan)
        Spacer(modifier = Modifier.height(8.dp))
        Text(title, style = MaterialTheme.typography.titleMedium)
        Text(
            subtitle,
            style = MaterialTheme.typography.bodyMedium,
            color = MaterialTheme.colorScheme.onSurfaceVariant
        )
    }
}

@Composable
private fun StatColumn(label: String, value: String) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(value, style = MaterialTheme.typography.headlineSmall, color = ElectricCyan)
        Text(label, style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
    }
}
