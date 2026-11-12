package com.javo.agents

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.SnackbarHost
import androidx.compose.material3.SnackbarHostState
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.currentBackStackEntryAsState
import androidx.navigation.compose.rememberNavController
import com.javo.agents.ui.navigation.Routes
import com.javo.agents.ui.screens.AIProvidersScreen
import com.javo.agents.ui.screens.AgentTeamScreen
import com.javo.agents.ui.screens.AnalyticsScreen
import com.javo.agents.ui.screens.ApprovalInboxScreen
import com.javo.agents.ui.screens.CalendarScreen
import com.javo.agents.ui.screens.ConnectedAccountsScreen
import com.javo.agents.ui.screens.ContentLibraryScreen
import com.javo.agents.ui.screens.GoalsScreen
import com.javo.agents.ui.screens.HelpReportingScreen
import com.javo.agents.ui.screens.HomeScreen
import com.javo.agents.ui.screens.LocalSetupScreen
import com.javo.agents.ui.screens.NotificationsScreen
import com.javo.agents.ui.screens.PairingScreen
import com.javo.agents.ui.screens.PrivacyDataScreen
import com.javo.agents.ui.screens.SecurityScreen
import com.javo.agents.ui.screens.SettingsScreen
import com.javo.agents.ui.screens.SplashScreen
import com.javo.agents.ui.screens.VoiceModeScreen
import com.javo.agents.ui.screens.WelcomeScreen
import com.javo.agents.ui.screens.WorkflowsScreen
import com.javo.agents.ui.theme.JavoAgentsTheme
import com.javo.agents.ui.viewmodel.MainViewModel

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent {
            JavoAgentsAppRoot()
        }
    }
}

@Composable
private fun JavoAgentsAppRoot(
    viewModel: MainViewModel = viewModel()
) {
    val darkTheme by viewModel.darkTheme.collectAsState()
    val toastMessage by viewModel.statusToast.collectAsState()
    val snackbarHostState = remember { SnackbarHostState() }
    val context = LocalContext.current

    var hasAudioPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.RECORD_AUDIO) ==
                PackageManager.PERMISSION_GRANTED
        )
    }
    var hasCameraPermission by remember {
        mutableStateOf(
            ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) ==
                PackageManager.PERMISSION_GRANTED
        )
    }

    val audioPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasAudioPermission = granted
    }

    val cameraPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { granted ->
        hasCameraPermission = granted
    }

    val notificationPermissionLauncher = rememberLauncherForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { _ -> }

    LaunchedEffect(Unit) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val granted = ContextCompat.checkSelfPermission(
                context,
                Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED
            if (!granted) {
                notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }

    LaunchedEffect(toastMessage) {
        if (!toastMessage.isNullOrBlank()) {
            snackbarHostState.showSnackbar(toastMessage!!)
            viewModel.clearToast()
        }
    }

    JavoAgentsTheme(darkTheme = darkTheme) {
        val navController = rememberNavController()
        val navBackStackEntry by navController.currentBackStackEntryAsState()
        val currentRoute = navBackStackEntry?.destination?.route

        val navigateTopLevel: (String) -> Unit = { target ->
            navController.navigate(target) {
                popUpTo(Routes.HOME) { saveState = true }
                launchSingleTop = true
                restoreState = true
            }
        }

        Box(modifier = Modifier.fillMaxSize()) {
            NavHost(
                navController = navController,
                startDestination = Routes.SPLASH
            ) {
                composable(Routes.SPLASH) {
                    SplashScreen(
                        isOnboardingComplete = viewModel.isOnboardingComplete(),
                        onNavigateNext = { onboarded ->
                            val next = if (onboarded) Routes.HOME else Routes.WELCOME
                            navController.navigate(next) {
                                popUpTo(Routes.SPLASH) { inclusive = true }
                            }
                        }
                    )
                }

                composable(Routes.WELCOME) {
                    WelcomeScreen(
                        onGetStarted = { navController.navigate(Routes.LOCAL_SETUP) },
                        onPairWindows = { navController.navigate(Routes.PAIRING) },
                        onSkipToHome = {
                            viewModel.completeOnboarding()
                            navController.navigate(Routes.HOME) {
                                popUpTo(Routes.WELCOME) { inclusive = true }
                            }
                        }
                    )
                }

                composable(Routes.LOCAL_SETUP) {
                    LocalSetupScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() },
                        onContinueToPairing = { navController.navigate(Routes.PAIRING) },
                        onFinishOffline = {
                            navController.navigate(Routes.HOME) {
                                popUpTo(Routes.WELCOME) { inclusive = true }
                            }
                        }
                    )
                }

                composable(Routes.PAIRING) {
                    PairingScreen(
                        viewModel = viewModel,
                        hasCameraPermission = hasCameraPermission,
                        onRequestCameraPermission = {
                            cameraPermissionLauncher.launch(Manifest.permission.CAMERA)
                        },
                        onBack = { navController.popBackStack() },
                        onDoneNavigateHome = {
                            navController.navigate(Routes.HOME) {
                                popUpTo(Routes.HOME) { inclusive = true }
                            }
                        }
                    )
                }

                composable(Routes.HOME) {
                    HomeScreen(
                        viewModel = viewModel,
                        currentRoute = currentRoute,
                        onNavigate = { route ->
                            if (route in setOf(
                                    Routes.HOME,
                                    Routes.AGENT_TEAM,
                                    Routes.VOICE_MODE,
                                    Routes.APPROVAL_INBOX,
                                    Routes.CONTENT_LIBRARY
                                )
                            ) {
                                navigateTopLevel(route)
                            } else {
                                navController.navigate(route)
                            }
                        }
                    )
                }

                composable(Routes.AGENT_TEAM) {
                    AgentTeamScreen(
                        viewModel = viewModel,
                        currentRoute = currentRoute,
                        onNavigate = navigateTopLevel
                    )
                }

                composable(Routes.VOICE_MODE) {
                    VoiceModeScreen(
                        viewModel = viewModel,
                        currentRoute = currentRoute,
                        hasAudioPermission = hasAudioPermission,
                        onRequestAudioPermission = {
                            audioPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
                        },
                        onNavigate = navigateTopLevel
                    )
                }

                composable(Routes.WORKFLOWS) {
                    WorkflowsScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.CONTENT_LIBRARY) {
                    ContentLibraryScreen(
                        viewModel = viewModel,
                        currentRoute = currentRoute,
                        onNavigate = navigateTopLevel
                    )
                }

                composable(Routes.CALENDAR) {
                    CalendarScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.CONNECTED_ACCOUNTS) {
                    ConnectedAccountsScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.ANALYTICS) {
                    AnalyticsScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.GOALS) {
                    GoalsScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.APPROVAL_INBOX) {
                    ApprovalInboxScreen(
                        viewModel = viewModel,
                        currentRoute = currentRoute,
                        onNavigate = navigateTopLevel
                    )
                }

                composable(Routes.AI_PROVIDERS) {
                    AIProvidersScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.NOTIFICATIONS) {
                    NotificationsScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.SETTINGS) {
                    SettingsScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() },
                        onNavigate = { navController.navigate(it) }
                    )
                }

                composable(Routes.SECURITY) {
                    SecurityScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() },
                        onOpenPairing = { navController.navigate(Routes.PAIRING) }
                    )
                }

                composable(Routes.PRIVACY_DATA) {
                    PrivacyDataScreen(
                        viewModel = viewModel,
                        onBack = { navController.popBackStack() }
                    )
                }

                composable(Routes.HELP_REPORTING) {
                    HelpReportingScreen(
                        onBack = { navController.popBackStack() }
                    )
                }
            }

            SnackbarHost(
                hostState = snackbarHostState,
                modifier = Modifier
                    .align(Alignment.BottomCenter)
                    .padding(bottom = 84.dp, start = 16.dp, end = 16.dp)
            )
        }
    }
}
