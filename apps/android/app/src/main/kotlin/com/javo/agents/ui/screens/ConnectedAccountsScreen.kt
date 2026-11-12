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
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
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
import com.javo.agents.ui.theme.AmberWarning
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.MidnightNavy
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun ConnectedAccountsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val accounts by viewModel.accounts.collectAsState()
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
                ) { Text("Queue OAuth") }
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
                    Text("OAuth Credentials Stay on Windows", style = MaterialTheme.typography.titleMedium)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Social OAuth tokens are never exposed to mobile storage. Complete Meta / YouTube OAuth on your paired Windows desktop.",
                        style = MaterialTheme.typography.bodyMedium,
                        color = MaterialTheme.colorScheme.onSurfaceVariant
                    )
                }
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
