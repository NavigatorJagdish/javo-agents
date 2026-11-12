package com.javo.agents.ui.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.PureWhite

@Composable
fun EmergencyStopDialog(
    onConfirmStop: () -> Unit,
    onDismiss: () -> Unit
) {
    AlertDialog(
        onDismissRequest = onDismiss,
        icon = {
            Icon(
                imageVector = Icons.Rounded.Warning,
                contentDescription = "Emergency Stop",
                tint = CoralDanger
            )
        },
        title = {
            Text(
                text = "Activate Emergency Stop?",
                style = MaterialTheme.typography.headlineSmall
            )
        },
        text = {
            Text(
                text = "This immediately pauses all active local tasks on Android and sends /security/emergency-stop to your paired Windows Local Runtime so scheduled posts and agents halt safely.",
                style = MaterialTheme.typography.bodyMedium
            )
        },
        confirmButton = {
            Button(
                onClick = onConfirmStop,
                colors = ButtonDefaults.buttonColors(
                    containerColor = CoralDanger,
                    contentColor = PureWhite
                )
            ) {
                Text("Stop Everything")
            }
        },
        dismissButton = {
            TextButton(onClick = onDismiss) {
                Text("Cancel")
            }
        }
    )
}
