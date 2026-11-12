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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun NotificationsScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit
) {
    val notifications by viewModel.notifications.collectAsState()

    JavoSubScreenScaffold(
        title = "Notifications",
        onBack = onBack,
        actions = {
            TextButton(onClick = { viewModel.markAllNotificationsRead() }) {
                Text("Mark all read")
            }
        }
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp)
        ) {
            items(notifications, key = { it.id }) { item ->
                StatusCard(
                    highlightGradient = !item.isRead,
                    onClick = { viewModel.markNotificationRead(item.id) }
                ) {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text(item.title, style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                        StatusPill(
                            text = if (item.isRead) "Read" else "New",
                            color = if (item.isRead) EmeraldSuccess else ElectricCyan
                        )
                    }
                    Spacer(modifier = Modifier.height(6.dp))
                    Text(item.message, style = MaterialTheme.typography.bodyMedium)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text("${item.category.uppercase()} • ${item.timestampLabel}", style = MaterialTheme.typography.labelSmall, color = VioletAccent)
                }
            }
        }
    }
}
