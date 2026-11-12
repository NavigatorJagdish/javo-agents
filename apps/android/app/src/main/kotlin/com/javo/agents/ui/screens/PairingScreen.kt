package com.javo.agents.ui.screens

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
import androidx.compose.material.icons.rounded.QrCodeScanner
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
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
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun PairingScreen(
    viewModel: MainViewModel,
    hasCameraPermission: Boolean,
    onRequestCameraPermission: () -> Unit,
    onBack: () -> Unit,
    onDoneNavigateHome: () -> Unit
) {
    val connectionState by viewModel.connectionState.collectAsState()
    val feedback by viewModel.pairingFeedback.collectAsState()

    var hostUrl by remember { mutableStateOf(viewModel.getPairedHostUrl() ?: "https://192.168.1.10:8000") }
    var pairingCode by remember { mutableStateOf("") }
    var pairingToken by remember { mutableStateOf("") }
    var rawQrPayload by remember { mutableStateOf("") }

    JavoSubScreenScaffold(title = "Windows Pairing", onBack = onBack) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .verticalScroll(rememberScrollState())
                .padding(16.dp)
        ) {
            StatusCard(highlightGradient = true) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Bridge Status", style = MaterialTheme.typography.titleMedium, modifier = Modifier.weight(1f))
                    StatusPill(text = connectionState.label, color = ElectricCyan)
                }
                Spacer(modifier = Modifier.height(6.dp))
                Text(
                    text = "Scan the QR code from your Windows Javo Dashboard (Security -> Devices) or enter the short-lived pairing token manually.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            }

            Spacer(modifier = Modifier.height(14.dp))

            StatusCard {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Rounded.QrCodeScanner, contentDescription = "QR Pairing", tint = VioletAccent)
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("QR / Compact Payload", style = MaterialTheme.typography.titleMedium)
                }
                Spacer(modifier = Modifier.height(10.dp))
                OutlinedTextField(
                    value = rawQrPayload,
                    onValueChange = { rawQrPayload = it },
                    label = { Text("Paste QR JSON or pipe payload") },
                    placeholder = { Text("https://192.168.1.10:8000|CODE123|token...|expiry") },
                    modifier = Modifier.fillMaxWidth(),
                    minLines = 2
                )
                Spacer(modifier = Modifier.height(10.dp))
                Row {
                    JavoOutlinedButton(
                        text = if (hasCameraPermission) "Camera Ready" else "Enable Camera",
                        onClick = onRequestCameraPermission,
                        modifier = Modifier.weight(1f)
                    )
                    Spacer(modifier = Modifier.width(10.dp))
                    JavoOutlinedButton(
                        text = "Pair Payload",
                        onClick = { viewModel.pairWithWindows(rawQrPayload) },
                        modifier = Modifier.weight(1f),
                        borderColor = VioletAccent
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))

            StatusCard {
                Text("Manual LAN / HTTPS Pairing", style = MaterialTheme.typography.titleMedium)
                Spacer(modifier = Modifier.height(10.dp))
                OutlinedTextField(
                    value = hostUrl,
                    onValueChange = { hostUrl = it },
                    label = { Text("Windows Runtime URL") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = pairingCode,
                    onValueChange = { pairingCode = it },
                    label = { Text("6-Digit / Short Pairing Code") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(8.dp))
                OutlinedTextField(
                    value = pairingToken,
                    onValueChange = { pairingToken = it },
                    label = { Text("Short-Lived Pairing Token (16+ chars)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth()
                )
                Spacer(modifier = Modifier.height(12.dp))
                GradientButton(
                    text = "Verify & Encrypt Token",
                    onClick = { viewModel.pairWithWindows(hostUrl, pairingCode, pairingToken) }
                )
            }

            if (!feedback.isNullOrBlank()) {
                Spacer(modifier = Modifier.height(12.dp))
                StatusCard {
                    Text(
                        text = feedback!!,
                        style = MaterialTheme.typography.bodyMedium,
                        color = EmeraldSuccess
                    )
                }
            }

            Spacer(modifier = Modifier.height(14.dp))
            JavoOutlinedButton(
                text = "Go to Home Dashboard",
                onClick = onDoneNavigateHome
            )
        }
    }
}
