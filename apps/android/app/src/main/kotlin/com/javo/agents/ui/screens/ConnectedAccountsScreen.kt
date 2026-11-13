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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Link
import androidx.compose.material.icons.rounded.LinkOff
import androidx.compose.material.icons.rounded.Lock
import androidx.compose.material3.AlertDialog
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
import com.javo.agents.data.model.SocialPlatform
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

@Composable
fun ConnectedAccountsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val accounts by viewModel.accounts.collectAsState()
    val socialConnections by viewModel.socialConnections.collectAsState()
    val operatingMode by viewModel.operatingMode.collectAsState()
    var showAddDialog by remember { mutableStateOf(false) }

    if (showAddDialog) {
        AlertDialog(
            onDismissRequest = { showAddDialog = false },
            title = { Text("Connect an official account") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        "Facebook Pages, Instagram Professional and YouTube require official authorization. Typing a handle cannot connect an account.",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        "Required: a platform developer app/OAuth client, user login and consent, approved scopes, and a secure callback/token exchange where needed.",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Text(
                        "Android Standalone does NOT require Windows. Until the mobile OAuth broker is configured, use local Content Studio drafts and manual sharing. Account linking is not yet available.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = AmberWarning
                    )
                }
            },
            confirmButton = {
                TextButton(onClick = { showAddDialog = false }) { Text("Understood") }
            }
        )
    }

    JavoSubScreenScaffold(
        title = "Connected Accounts",
        onBack = onBack,
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showAddDialog = true },
                containerColor = ElectricCyan,
                contentColor = MidnightNavy
            ) {
                Icon(Icons.Rounded.Add, contentDescription = "Account connection requirements")
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
            item {
                StatusCard(highlightGradient = true) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Rounded.Lock, contentDescription = "Security", tint = ElectricCyan)
                        Spacer(modifier = Modifier.width(8.dp))
                        Text("Honest Platform Integration", style = MaterialTheme.typography.titleMedium)
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "In Android Standalone mode, drafts and media are prepared locally. Direct publishing requires official OAuth authorization, eligible permissions and sometimes a secure server broker. Windows is optional, not mandatory.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
            }

            item {
                Text("Direct Social Integrations", style = MaterialTheme.typography.titleMedium)
            }

            items(socialConnections, key = { it.platform.id }) { item ->
                StatusCard {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Column(modifier = Modifier.weight(1f)) {
                            Text(item.platform.displayName, style = MaterialTheme.typography.titleMedium)
                            Text(
                                if (item.isConnected) item.accountName.orEmpty() else "OAuth 2.0 PKCE / API",
                                style = MaterialTheme.typography.bodyMedium,
                                color = if (item.isConnected) ElectricCyan else MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        }
                        StatusPill(
                            text = item.statusLabel,
                            color = if (item.isConnected) EmeraldSuccess else AmberWarning
                        )
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(
                        item.statusDescription,
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                    if (item.isConnected) {
                        Spacer(modifier = Modifier.height(8.dp))
                        JavoOutlinedButton(
                            text = "Disconnect",
                            onClick = { viewModel.disconnectSocialPlatform(item.platform) },
                            borderColor = CoralDanger
                        )
                    }
                }
            }

            if (accounts.isNotEmpty()) {
                item {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text("Locally listed profiles (not verified connections)", style = MaterialTheme.typography.titleMedium)
                }
                items(accounts, key = { it.id }) { account ->
                    val pillColor = when (account.status) {
                        "Connected" -> EmeraldSuccess
                        "Beta" -> ElectricCyan
                        else -> AmberWarning
                    }
                    StatusCard {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(account.platform, style = MaterialTheme.typography.titleMedium)
                                Text("${account.handle} • ${account.brandName}", style = MaterialTheme.typography.bodyMedium, color = ElectricCyan)
                            }
                            StatusPill(text = account.status, color = pillColor)
                        }
                        Spacer(modifier = Modifier.height(6.dp))
                        Text(
                            "${account.followersLabel} • ${account.lastSyncLabel}",
                            style = MaterialTheme.typography.labelMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant
                        )
                    }
                }
            }
        }
    }
}
