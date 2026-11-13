package com.javo.agents

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.work.Configuration
import com.javo.agents.data.local.JavoDatabase
import com.javo.agents.data.local.KeystoreManager
import com.javo.agents.data.remote.GeminiApiClient
import com.javo.agents.data.remote.WindowsBridgeClient
import com.javo.agents.data.repository.JavoAppRepository
import com.javo.agents.service.MobileAgentOrchestrator
import com.javo.agents.workers.SyncWorker

class AppContainer(application: Application) {
    val database: JavoDatabase by lazy { JavoDatabase.getInstance(application) }
    val keystoreManager: KeystoreManager by lazy { KeystoreManager(application) }
    val bridgeClient: WindowsBridgeClient by lazy { WindowsBridgeClient(keystoreManager) }
    val geminiClient: GeminiApiClient by lazy { GeminiApiClient() }
    val orchestrator: MobileAgentOrchestrator by lazy {
        MobileAgentOrchestrator(
            context = application,
            taskDao = database.taskDao(),
            draftDao = database.draftDao(),
            keystoreManager = keystoreManager,
            geminiApiClient = geminiClient
        )
    }
    val repository: JavoAppRepository by lazy {
        JavoAppRepository(
            database = database,
            keystoreManager = keystoreManager,
            bridgeClient = bridgeClient
        )
    }
}

class JavoApplication : Application(), Configuration.Provider {

    lateinit var container: AppContainer
        private set

    override fun onCreate() {
        super.onCreate()
        container = AppContainer(this)
        createNotificationChannels()
        SyncWorker.schedulePeriodicSync(this)
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setMinimumLoggingLevel(android.util.Log.INFO)
            .build()

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val manager = getSystemService(NotificationManager::class.java) ?: return
            val channels = listOf(
                NotificationChannel(
                    CHANNEL_SYNC,
                    getString(R.string.channel_sync_name),
                    NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = getString(R.string.channel_sync_desc)
                },
                NotificationChannel(
                    CHANNEL_APPROVALS,
                    getString(R.string.channel_approvals_name),
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = getString(R.string.channel_approvals_desc)
                },
                NotificationChannel(
                    CHANNEL_VOICE,
                    getString(R.string.channel_voice_name),
                    NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = getString(R.string.channel_voice_desc)
                },
                NotificationChannel(
                    CHANNEL_TASKS,
                    getString(R.string.channel_tasks_name),
                    NotificationManager.IMPORTANCE_DEFAULT
                ).apply {
                    description = getString(R.string.channel_tasks_desc)
                }
            )
            manager.createNotificationChannels(channels)
        }
    }

    companion object {
        const val CHANNEL_SYNC = "javo_sync"
        const val CHANNEL_APPROVALS = "javo_approvals"
        const val CHANNEL_VOICE = "javo_voice"
        const val CHANNEL_TASKS = "javo_tasks_and_reminders"
    }
}
