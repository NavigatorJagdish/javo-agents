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
    suspend fun uploadPending(drafts: List<DraftEntity>): List<String>
}

class BridgeDraftUploader(private val bridgeClient: WindowsBridgeClient) : RemoteDraftUploader {
    override suspend fun uploadPending(drafts: List<DraftEntity>): List<String> {
        if (drafts.isEmpty()) return emptyList()
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
        val ackedIds = remoteUploader.uploadPending(pending)
        ackedIds.forEach { draftStore.markSynced(it) }
        return ackedIds.size
    }

    suspend fun updateDraft(draft: DraftEntity) {
        draftStore.saveDraft(draft)
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

    suspend fun migrateLegacySampleDataIfPresent() {
        if (!keystoreManager.isSampleDataMigrated()) {
            val sampleDrafts = listOf("draft-101", "draft-102", "draft-103")
            sampleDrafts.forEach { database.draftDao().deleteById(it) }

            val sampleApprovals = listOf("apr-201", "apr-202", "apr-203")
            sampleApprovals.forEach { approvalDao.deleteById(it) }

            val sampleGoals = listOf("goal-1", "goal-2")
            sampleGoals.forEach { goalDao.deleteById(it) }

            val sampleTasks = listOf("tsk-1", "tsk-2", "tsk-3")
            sampleTasks.forEach { taskDao.deleteById(it) }

            val sampleAccounts = listOf("acc-ig", "acc-fb", "acc-yt", "acc-tg")
            sampleAccounts.forEach { accountDao.deleteById(it) }

            val sampleNotifications = listOf("not-1", "not-2", "not-3")
            sampleNotifications.forEach { notificationDao.deleteById(it) }

            keystoreManager.markSampleDataMigrated()
        }
    }

    suspend fun loadDemoData() {
        keystoreManager.setDemoModeEnabled(true)
        database.draftDao().upsertAll(
            listOf(
                DraftEntity("demo-draft-1", "Morning Hinglish Reel Hook", "Aaj hum dekhenge ki local AI aapke daily content workflow ko 5x fast kaise karta hai — bina kisi cloud lock-in ke!", "Instagram", "scheduled", "Tomorrow • 09:00 AM", pendingSync = false),
                DraftEntity("demo-draft-2", "8GB RAM Ollama Guide Carousel", "5 practical tips to run Qwen 2.5 3B smoothly on an 8GB Windows laptop.", "Facebook", "offline_draft", "Fri • 06:30 PM", pendingSync = true),
                DraftEntity("demo-draft-3", "YouTube Shorts Script: Privacy Firewall", "Why your social tokens stay inside Windows DPAPI & Android Keystore.", "YouTube", "synced", "Sat • 11:00 AM", pendingSync = false)
            )
        )
        approvalDao.upsertAll(
            listOf(
                ApprovalEntity("demo-apr-1", "Publish Instagram Reel Caption", "Content Publisher", "Instagram", "AI team ne aapke kal ke folder video ke liye 3 Hinglish hooks ready kiye hain. Publish karein?", "medium", "Today • 07:00 PM", "pending"),
                ApprovalEntity("demo-apr-2", "Reply to 4 YouTube Comments", "Community Manager", "YouTube", "Drafted polite answers to viewer questions on local Whisper setup.", "low", "Today • 08:15 PM", "pending")
            )
        )
        goalDao.upsertAll(
            listOf(
                GoalEntity("demo-goal-1", "Consistent 5x/Week Hinglish Reels", "Build steady organic reach without paid ads using Supervised Autopilot.", 0.68f, "active", "30 Nov", "14 / 20 drafts inspected & queued")
            )
        )
        taskDao.upsertAll(
            listOf(
                TaskEntity("demo-tsk-1", "Scan D:\\JavoContent\\Reels folder", "content_factory", "completed", "normal", "demo-goal-1", true),
                TaskEntity("demo-tsk-2", "Verify Brand Tone on Reel #14", "brand_manager", "running", "high", "demo-goal-1", true)
            )
        )
        accountDao.upsertAll(
            listOf(
                AccountEntity("demo-acc-1", "Instagram Professional", "@javo.studio.demo", "Javo Studio", "Demo", "12.4K Followers", "Demo Mode"),
                AccountEntity("demo-acc-2", "YouTube Data API", "Javo Tech Hindi (Demo)", "Javo Studio", "Demo", "48.2K Subscribers", "Demo Mode")
            )
        )
    }

    suspend fun clearDemoData() {
        keystoreManager.setDemoModeEnabled(false)
        listOf("demo-draft-1", "demo-draft-2", "demo-draft-3").forEach { database.draftDao().deleteById(it) }
        listOf("demo-apr-1", "demo-apr-2").forEach { approvalDao.deleteById(it) }
        listOf("demo-goal-1").forEach { goalDao.deleteById(it) }
        listOf("demo-tsk-1", "demo-tsk-2").forEach { taskDao.deleteById(it) }
        listOf("demo-acc-1", "demo-acc-2").forEach { accountDao.deleteById(it) }
    }

    suspend fun addTask(
        title: String,
        assignedAgent: String = "general_assistant",
        priority: String = "normal",
        goalId: String? = null
    ): TaskEntity {
        val task = TaskEntity(
            id = "tsk-" + UUID.randomUUID().toString().take(8),
            title = title.trim(),
            assignedAgent = assignedAgent,
            state = "pending",
            priority = priority,
            goalId = goalId,
            syncedWithDesktop = false
        )
        taskDao.upsert(task)
        return task
    }

    suspend fun updateTaskState(taskId: String, newState: String) {
        taskDao.updateState(taskId, newState)
    }

    suspend fun deleteTask(taskId: String) {
        taskDao.deleteById(taskId)
    }

    suspend fun updateDraft(draft: DraftEntity) = draftRepository.updateDraft(draft)
    suspend fun deleteDraft(id: String) = draftRepository.deleteDraft(id)
    suspend fun deleteApproval(id: String) = approvalDao.deleteById(id)

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
