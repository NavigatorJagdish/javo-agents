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
import androidx.compose.material.icons.rounded.Mic
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
import androidx.compose.material3.OutlinedButton
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
import com.javo.agents.data.model.ProviderType
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
    val approvals by viewModel.approvals.collectAsState()
    val drafts by viewModel.drafts.collectAsState()
    val tasks by viewModel.tasks.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()
    val waveformState by viewModel.waveformState.collectAsState()
    val operatingMode by viewModel.operatingMode.collectAsState()
    val aiConfig by viewModel.aiConfig.collectAsState()
    val customAiConfig by viewModel.customAiConfig.collectAsState()
    val socialConnections by viewModel.socialConnections.collectAsState()

    var showEmergencyDialog by remember { mutableStateOf(false) }
    var showModeDialog by remember { mutableStateOf(false) }

    // Configured agents are not counted as actively executing jobs.
    val pendingApprovals = approvals.count { it.status == "pending" }
    val verifiedSocialAccounts = socialConnections.count { it.isConnected }
    // A stored key for an unrelated provider is NOT evidence that the
    // user-selected provider can process a request.
    val mobileAiReady = when (aiConfig.activeProvider) {
        ProviderType.GEMINI_DIRECT -> aiConfig.hasGeminiKeyStored
        ProviderType.CUSTOM_ENDPOINT -> customAiConfig?.isEnabled == true &&
            !customAiConfig?.endpointUrl.isNullOrBlank()
        ProviderType.LOCAL_PC_OLLAMA -> operatingMode == OperatingMode.WINDOWS_ENHANCED &&
            connectionState.name == "Connected"
    }

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
                                text = "Javo • Your AI companion",
                                style = MaterialTheme.typography.headlineSmall
                            )
                        }
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = when (operatingMode) {
                                OperatingMode.ANDROID_STANDALONE -> "Talk, create and organize directly on your phone. No PC required."
                                OperatingMode.WINDOWS_ENHANCED -> "Desktop-enhanced features are optional. Your mobile workspace stays available."
                                OperatingMode.CLOUD_MODE -> "Use configured cloud services for supported tasks."
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
                            text = when {
                                mobileAiReady -> "Selected AI configured"
                                operatingMode == OperatingMode.WINDOWS_ENHANCED && isConnected -> "Windows online"
                                else -> "Set up selected AI"
                            },
                            color = if (mobileAiReady || (operatingMode == OperatingMode.WINDOWS_ENHANCED && isConnected)) EmeraldSuccess else VioletAccent
                        )
                    }
                }
            }

            Spacer(modifier = Modifier.height(12.dp))

            // Voice-first entry point: the assistant is the product, not a fake agent activity monitor.
            StatusCard(highlightGradient = true) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    JavoLogo(size = 72.dp, showOrbitalRing = true)
                    Spacer(modifier = Modifier.width(14.dp))
                    Column(modifier = Modifier.weight(1f)) {
                        Text("Hello, I'm Javo", style = MaterialTheme.typography.headlineSmall)
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            "Bolo, aaj kya karna hai? Ask naturally in Hindi, Hinglish or English.",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
                Spacer(modifier = Modifier.height(14.dp))
                WaveformVisualizer(
                    state = waveformState,
                    barCount = 26,
                    height = 58.dp,
                    showStateLabel = true
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = if (waveformState == WaveformState.Idle)
                        "Ready for your next conversation"
                    else waveformState.label,
                    color = ElectricCyan,
                    style = MaterialTheme.typography.labelMedium
                )
                Spacer(modifier = Modifier.height(12.dp))
                Button(
                    onClick = { onNavigate(Routes.VOICE_MODE) },
                    modifier = Modifier.fillMaxWidth().height(54.dp),
                    colors = ButtonDefaults.buttonColors(containerColor = ElectricCyan)
                ) {
                    Icon(Icons.Rounded.Mic, contentDescription = null)
                    Spacer(modifier = Modifier.width(10.dp))
                    Text("Talk to Javo", style = MaterialTheme.typography.titleMedium)
                }
                if (!mobileAiReady) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        "To get real AI replies, first connect a provider. Voice recognition alone is not AI.",
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    Spacer(modifier = Modifier.height(6.dp))
                    OutlinedButton(
                        onClick = { onNavigate(Routes.AI_PROVIDERS) },
                        modifier = Modifier.fillMaxWidth()
                    ) { Text("Connect an AI provider") }
                }
            }

            Spacer(modifier = Modifier.height(14.dp))
            Text("What would you like to do?", style = MaterialTheme.typography.titleMedium)
            Spacer(modifier = Modifier.height(8.dp))

            // 2x3 Quick Actions Grid
            Row(modifier = Modifier.fillMaxWidth()) {
                QuickActionTile(
                    icon = Icons.Rounded.GraphicEq,
                    title = "AI Team",
                    subtitle = "Explore specialists",
                    onClick = { onNavigate(Routes.AGENT_TEAM) },
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(
                    icon = Icons.Rounded.PostAdd,
                    title = "Create Content",
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
                    subtitle = "Create or run phone tasks",
                    onClick = { onNavigate(Routes.WORKFLOWS) },
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(
                    icon = Icons.Rounded.Shield,
                    title = "Approvals ($pendingApprovals)",
                    subtitle = "Review real pending actions",
                    onClick = { onNavigate(Routes.APPROVAL_INBOX) },
                    modifier = Modifier.weight(1f)
                )
            }
            Spacer(modifier = Modifier.height(10.dp))
            Row(modifier = Modifier.fillMaxWidth()) {
                QuickActionTile(
                    icon = Icons.Rounded.Share,
                    title = "Social Channels",
                    subtitle = verifiedSocialAccounts.toString() + " verified connections",
                    onClick = { onNavigate(Routes.CONNECTED_ACCOUNTS) },
                    modifier = Modifier.weight(1f)
                )
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(
                    icon = Icons.Rounded.SmartToy,
                    title = "AI Providers",
                    subtitle = if (mobileAiReady) "Provider configured" else "Connect to get AI replies",
                    onClick = { onNavigate(Routes.AI_PROVIDERS) },
                    modifier = Modifier.weight(1f)
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            // Automation Stats
            StatusCard {
                Text("Your workspace · live records", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(10.dp))
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween
                ) {
                    StatColumn("Tasks", tasks.size.toString())
                    StatColumn("Drafts", drafts.size.toString())
                    StatColumn("Approvals", pendingApprovals.toString())
                    StatColumn("Connected", verifiedSocialAccounts.toString())
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
                QuickActionTile(Icons.Rounded.Settings, "Preferences", "Voice, AI & privacy", { onNavigate(Routes.SETTINGS) }, Modifier.weight(1f))
                Spacer(modifier = Modifier.width(10.dp))
                QuickActionTile(Icons.Rounded.Security, "Privacy & Safety", "Permissions & controls", { onNavigate(Routes.SECURITY) }, Modifier.weight(1f))
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
