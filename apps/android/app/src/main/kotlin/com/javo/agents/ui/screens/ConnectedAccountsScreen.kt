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
        var platform by remember { mutableStateOf("Instagram Professional") }
        var handle by remember { mutableStateOf("") }
        var brand by remember { mutableStateOf("Javo Studio") }

        AlertDialog(
            onDismissRequest = { showAddDialog = false },
            title = { Text("Add Social Channel") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(value = platform, onValueChange = { platform = it }, label = { Text("Platform") }, singleLine = true)
                    OutlinedTextField(value = handle, onValueChange = { handle = it }, label = { Text("Handle / Page Name") }, singleLine = true)
                    OutlinedTextField(value = brand, onValueChange = { brand = it }, label = { Text("Brand Profile") }, singleLine = true)
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.addAccount(platform, handle, brand)
                        showAddDialog = false
                    }
                ) { Text("Queue Channel") }
            },
            dismissButton = {
                TextButton(onClick = { showAddDialog = false }) { Text("Cancel") }
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
                Icon(Icons.Rounded.Add, contentDescription = "Add account")
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
                        "In Android Standalone mode, drafts and media are prepared locally. Direct publishing requires official OAuth Client IDs or pairing with your Windows PC DPAPI tokens.",
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
                    Text("Configured Profiles", style = MaterialTheme.typography.titleMedium)
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
