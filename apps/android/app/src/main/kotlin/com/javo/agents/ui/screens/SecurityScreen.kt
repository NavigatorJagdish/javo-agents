package com.javo.agents.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.ui.components.EmergencyStopDialog
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.PureWhite
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun SecurityScreen(
    viewModel: MainViewModel,
    onBack: () -> Unit,
    onOpenPairing: () -> Unit
) {
    val connectionState by viewModel.connectionState.collectAsState()
    val keystoreStatus = viewModel.getKeystoreHealth()
    val pairedHost = viewModel.getPairedHostUrl()
    var showStopDialog by remember { mutableStateOf(false) }

    if (showStopDialog) {
        EmergencyStopDialog(
            onConfirmStop = {
                showStopDialog = false
                viewModel.triggerEmergencyStop()
            },
            onDismiss = { showStopDialog = false }
        )
    }

    JavoSubScreenScaffold(title = "Security Center", onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatusCard(highlightGradient = true) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Android Keystore Vault", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    StatusPill(
                        text = if (keystoreStatus.keystoreActive) "Active" else "Error",
                        color = if (keystoreStatus.keystoreActive) EmeraldSuccess else CoralDanger
                    )
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(keystoreStatus.encryptionScheme, style = MaterialTheme.typography.bodyMedium)
                Spacer(modifier = Modifier.height(4.dp))
                Text("Device ID: ${keystoreStatus.deviceId}", style = MaterialTheme.typography.labelMedium, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }

            StatusCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Windows Pairing", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    StatusPill(text = connectionState.label, color = ElectricCyan)
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = pairedHost ?: "No Windows desktop paired yet.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(10.dp))
                GradientButton(text = "Pair / Update Windows Host", onClick = onOpenPairing)
                if (keystoreStatus.hasPairingToken) {
                    Spacer(modifier = Modifier.height(8.dp))
                    JavoOutlinedButton(
                        text = "Revoke Pairing & Wipe Token",
                        onClick = { viewModel.revokePairing() },
                        borderColor = CoralDanger
                    )
                }
            }

            StatusCard {
                Text("Emergency Kill Switch", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(4.dp))
                Text(
                    "Immediately halts active Android queues and sends /security/emergency-stop to your paired Windows Local Runtime.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
                Spacer(modifier = Modifier.height(10.dp))
                Button(
                    onClick = { showStopDialog = true },
                    modifier = Modifier.fillMaxWidth(),
                    colors = ButtonDefaults.buttonColors(
                        containerColor = CoralDanger,
                        contentColor = PureWhite
                    )
                ) {
                    Text("Trigger Emergency Stop")
                }
            }
        }
    }
}
