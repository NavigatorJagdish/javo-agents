package com.javo.agents.ui.components

import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.CheckCircle
import androidx.compose.material.icons.rounded.Dashboard
import androidx.compose.material.icons.rounded.GraphicEq
import androidx.compose.material.icons.rounded.GridView
import androidx.compose.material3.Badge
import androidx.compose.material3.BadgedBox
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.NavigationBarItemDefaults
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.vector.ImageVector
import com.javo.agents.ui.navigation.Routes
import com.javo.agents.ui.theme.ElectricCyan

data class BottomNavItem(
    val route: String,
    val label: String,
    val icon: ImageVector
)

val primaryNavItems = listOf(
    BottomNavItem(Routes.HOME, "Home", Icons.Rounded.Dashboard),
    BottomNavItem(Routes.AGENT_TEAM, "Agents", Icons.Rounded.AutoAwesome),
    BottomNavItem(Routes.VOICE_MODE, "Voice", Icons.Rounded.GraphicEq),
    BottomNavItem(Routes.APPROVAL_INBOX, "Inbox", Icons.Rounded.CheckCircle),
    BottomNavItem(Routes.CONTENT_LIBRARY, "Studio", Icons.Rounded.GridView)
)

@Composable
fun BottomNavBar(
    currentRoute: String?,
    pendingApprovalsCount: Int,
    onNavigate: (String) -> Unit
) {
    NavigationBar(
        containerColor = MaterialTheme.colorScheme.surface
    ) {
        primaryNavItems.forEach { item ->
            val selected = currentRoute == item.route
            NavigationBarItem(
                selected = selected,
                onClick = { onNavigate(item.route) },
                icon = {
                    if (item.route == Routes.APPROVAL_INBOX && pendingApprovalsCount > 0) {
                        BadgedBox(
                            badge = { Badge { Text(pendingApprovalsCount.toString()) } }
                        ) {
                            Icon(item.icon, contentDescription = item.label)
                        }
                    } else {
                        Icon(item.icon, contentDescription = item.label)
                    }
                },
                label = { Text(item.label) },
                colors = NavigationBarItemDefaults.colors(
                    selectedIconColor = ElectricCyan,
                    selectedTextColor = ElectricCyan,
                    indicatorColor = ElectricCyan.copy(alpha = 0.14f)
                )
            )
        }
    }
}
