package com.javo.agents.data.repository

import com.javo.agents.data.local.AccountDao
import com.javo.agents.data.local.AccountEntity
import com.javo.agents.data.local.ApprovalDao
import com.javo.agents.data.local.ApprovalEntity
import com.javo.agents.data.local.DraftDao
import com.javo.agents.data.local.DraftEntity
import com.javo.agents.data.local.GoalDao
import com.javo.agents.data.local.GoalEntity
import com.javo.agents.data.local.JavoDatabase
import com.javo.agents.data.local.KeystoreManager
import com.javo.agents.data.local.NotificationDao
import com.javo.agents.data.local.NotificationEntity
import com.javo.agents.data.local.TaskDao
import com.javo.agents.data.local.TaskEntity
import com.javo.agents.data.remote.DraftSyncRequest
import com.javo.agents.data.remote.WindowsBridgeClient
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import java.util.UUID

interface DraftStore {
    fun observeDrafts(): Flow<List<DraftEntity>>
    suspend fun saveDraft(draft: DraftEntity)
    suspend fun getPendingSync(): List<DraftEntity>
    suspend fun markSynced(id: String)
    suspend fun deleteDraft(id: String)
}

class RoomDraftStore(private val draftDao: DraftDao) : DraftStore {
    override fun observeDrafts(): Flow<List<DraftEntity>> = draftDao.observeAll()
    override suspend fun saveDraft(draft: DraftEntity) = draftDao.upsert(draft)
    override suspend fun getPendingSync(): List<DraftEntity> = draftDao.getPendingSync()
    override suspend fun markSynced(id: String) = draftDao.markSynced(id)
    override suspend fun deleteDraft(id: String) = draftDao.deleteById(id)
}

interface RemoteDraftUploader {
    suspend fun uploadPending(drafts: List<DraftEntity>): Boolean
}

class BridgeDraftUploader(private val bridgeClient: WindowsBridgeClient) : RemoteDraftUploader {
    override suspend fun uploadPending(drafts: List<DraftEntity>): Boolean {
        if (drafts.isEmpty()) return true
        val payload = drafts.map {
            DraftSyncRequest(
                id = it.id,
                title = it.title,
                body = it.body,
                platform = it.platform,
                status = it.status
            )
        }
        return bridgeClient.syncDrafts(payload)
    }
}

class OfflineDraftRepository(
    private val draftStore: DraftStore,
    private val remoteUploader: RemoteDraftUploader
) {
    fun observeDrafts(): Flow<List<DraftEntity>> = draftStore.observeDrafts()

    suspend fun createOfflineDraft(
        title: String,
        body: String,
        platform: String,
        scheduledDateLabel: String? = null
    ): DraftEntity {
        val draft = DraftEntity(
            id = "draft-" + UUID.randomUUID().toString().take(8),
            title = title.trim(),
            body = body.trim(),
            platform = platform,
            status = "offline_draft",
            scheduledDateLabel = scheduledDateLabel,
            pendingSync = true
        )
        draftStore.saveDraft(draft)
        return draft
    }

    suspend fun queueAndTrySync(): Int {
        val pending = draftStore.getPendingSync()
        if (pending.isEmpty()) return 0
        val synced = remoteUploader.uploadPending(pending)
        if (synced) {
            pending.forEach { draftStore.markSynced(it.id) }
            return pending.size
        }
        return 0
    }

    suspend fun deleteDraft(id: String) {
        draftStore.deleteDraft(id)
    }
}

class JavoAppRepository(
    private val database: JavoDatabase,
    private val keystoreManager: KeystoreManager,
    private val bridgeClient: WindowsBridgeClient
) {
    private val taskDao: TaskDao = database.taskDao()
    private val goalDao: GoalDao = database.goalDao()
    private val approvalDao: ApprovalDao = database.approvalDao()
    private val accountDao: AccountDao = database.accountDao()
    private val notificationDao: NotificationDao = database.notificationDao()

    val draftRepository = OfflineDraftRepository(
        draftStore = RoomDraftStore(database.draftDao()),
        remoteUploader = BridgeDraftUploader(bridgeClient)
    )

    fun observeTasks(): Flow<List<TaskEntity>> = taskDao.observeAll()
    fun observeGoals(): Flow<List<GoalEntity>> = goalDao.observeAll()
    fun observeApprovals(): Flow<List<ApprovalEntity>> = approvalDao.observeAll()
    fun observeAccounts(): Flow<List<AccountEntity>> = accountDao.observeAll()
    fun observeNotifications(): Flow<List<NotificationEntity>> = notificationDao.observeAll()

    suspend fun seedInitialLocalDataIfEmpty() {
        if (database.draftDao().observeAll().first().isEmpty()) {
            database.draftDao().upsertAll(
                listOf(
                    DraftEntity("draft-101", "Morning Hinglish Reel Hook", "Aaj hum dekhenge ki local AI aapke daily content workflow ko 5x fast kaise karta hai — bina kisi cloud lock-in ke!", "Instagram", "scheduled", "Tomorrow • 09:00 AM", pendingSync = false),
                    DraftEntity("draft-102", "8GB RAM Ollama Guide Carousel", "5 practical tips to run Qwen 2.5 3B smoothly on an 8GB Windows laptop.", "Facebook", "offline_draft", "Fri • 06:30 PM", pendingSync = true),
                    DraftEntity("draft-103", "YouTube Shorts Script: Privacy Firewall", "Why your social tokens stay inside Windows DPAPI & Android Keystore.", "YouTube", "synced", "Sat • 11:00 AM", pendingSync = false)
                )
            )
        }
        if (approvalDao.observeAll().first().isEmpty()) {
            approvalDao.upsertAll(
                listOf(
                    ApprovalEntity("apr-201", "Publish Instagram Reel Caption", "Content Publisher", "Instagram", "AI team ne aapke kal ke folder video ke liye 3 Hinglish hooks ready kiye hain. Publish karein?", "medium", "Today • 07:00 PM", "pending"),
                    ApprovalEntity("apr-202", "Reply to 4 YouTube Comments", "Community Manager", "YouTube", "Drafted polite answers to viewer questions on local Whisper setup.", "low", "Today • 08:15 PM", "pending"),
                    ApprovalEntity("apr-203", "Schedule Weekly Founder Thread", "Growth Scientist", "Facebook", "Summary of this week's reach and upcoming A/B test schedule.", "low", "Mon • 10:00 AM", "approved")
                )
            )
        }
        if (goalDao.observeAll().first().isEmpty()) {
            goalDao.upsertAll(
                listOf(
                    GoalEntity("goal-1", "Consistent 5x/Week Hinglish Reels", "Build steady organic reach without paid ads using Supervised Autopilot.", 0.68f, "active", "30 Nov", "14 / 20 drafts inspected & queued"),
                    GoalEntity("goal-2", "Zero-Cost Local AI Pipeline", "Keep 100% of routine drafting on local Ollama Q4 models.", 0.92f, "active", "Ongoing", "Budget Guardian cap verified at $0.00")
                )
            )
        }
        if (taskDao.observeAll().first().isEmpty()) {
            taskDao.upsertAll(
                listOf(
                    TaskEntity("tsk-1", "Scan D:\\JavoContent\\Reels folder", "content_factory", "completed", "normal", "goal-1", true),
                    TaskEntity("tsk-2", "Verify Brand Tone on Reel #14", "brand_manager", "running", "high", "goal-1", true),
                    TaskEntity("tsk-3", "Sync Pending Approvals to Android", "device_sync_agent", "pending", "normal", null, false)
                )
            )
        }
        if (accountDao.observeAll().first().isEmpty()) {
            accountDao.upsertAll(
                listOf(
                    AccountEntity("acc-ig", "Instagram Professional", "@javo.studio", "Javo Studio", "Beta", "Not synced", "Requires Windows OAuth"),
                    AccountEntity("acc-fb", "Facebook Pages", "Javo Creators Page", "Javo Studio", "Beta", "Not synced", "Requires Windows OAuth"),
                    AccountEntity("acc-yt", "YouTube Data API", "Javo Tech Hindi", "Javo Studio", "Disconnected", "—", "Connect on Windows"),
                    AccountEntity("acc-tg", "Telegram Bot", "@JavoAutopilotBot", "Javo Studio", "Connected", "Bot Ready", "Via Windows Runtime")
                )
            )
        }
        if (notificationDao.observeAll().first().isEmpty()) {
            notificationDao.upsertAll(
                listOf(
                    NotificationEntity("not-1", "Approval Required", "Content Publisher prepared 'Morning Hinglish Reel Hook' for your review.", "approval", false, "10m ago"),
                    NotificationEntity("not-2", "Keystore Initialized", "Hardware-backed AES-256-GCM encryption is active on this device.", "security", false, "1h ago"),
                    NotificationEntity("not-3", "Offline Queue Ready", "Any drafts you write on mobile will automatically sync when paired with Windows.", "sync", true, "Today")
                )
            )
        }
    }

    suspend fun addGoal(title: String, description: String, deadline: String) {
        goalDao.upsert(
            GoalEntity(
                id = "goal-" + UUID.randomUUID().toString().take(8),
                title = title.trim(),
                description = description.trim(),
                progress = 0.1f,
                status = "active",
                deadlineLabel = deadline.ifBlank { "Flexible" },
                milestoneSummary = "Created on Android • Queued for Goal Persistence agent"
            )
        )
    }

    suspend fun updateApprovalDecision(id: String, status: String, content: String, scheduledFor: String) {
        approvalDao.updateDecision(id, status, content, scheduledFor, pendingSync = true)
    }

    suspend fun markNotificationRead(id: String) = notificationDao.markRead(id)
    suspend fun markAllNotificationsRead() = notificationDao.markAllRead()

    suspend fun addAccountPlaceholder(platform: String, handle: String, brand: String) {
        accountDao.upsert(
            AccountEntity(
                id = "acc-" + UUID.randomUUID().toString().take(6),
                platform = platform,
                handle = handle,
                brandName = brand,
                status = "Beta",
                followersLabel = "Pending Windows OAuth",
                lastSyncLabel = "Queued"
            )
        )
    }

    suspend fun triggerEmergencyStop() {
        taskDao.pauseAllActive()
        bridgeClient.triggerEmergencyStop()
        notificationDao.upsert(
            NotificationEntity(
                id = "not-" + UUID.randomUUID().toString().take(8),
                title = "Emergency Stop Activated",
                message = "Active local tasks paused and stop signal sent to Windows Runtime.",
                category = "security",
                isRead = false,
                timestampLabel = "Just now"
            )
        )
    }

    suspend fun exportLocalSnapshotJson(): String {
        val drafts = draftRepository.observeDrafts().first()
        val goals = goalDao.observeAll().first()
        val approvals = approvalDao.observeAll().first()
        return buildString {
            appendLine("{")
            appendLine("  \"app\": \"Javo Agents Android\",")
            appendLine("  \"deviceId\": \"${keystoreManager.getOrCreateDeviceId()}\",")
            appendLine("  \"draftCount\": ${drafts.size},")
            appendLine("  \"goalCount\": ${goals.size},")
            appendLine("  \"approvalCount\": ${approvals.size},")
            appendLine("  \"paired\": ${keystoreManager.isPaired()}")
            appendLine("}")
        }
    }

    suspend fun deleteAllLocalData() {
        taskDao.clearAll()
        goalDao.clearAll()
        database.draftDao().clearAll()
        approvalDao.clearAll()
        accountDao.clearAll()
        notificationDao.clearAll()
        keystoreManager.wipeAllSecrets()
    }
}
