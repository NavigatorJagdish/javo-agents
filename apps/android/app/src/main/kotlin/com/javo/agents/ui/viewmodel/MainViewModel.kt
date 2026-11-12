package com.javo.agents.ui.viewmodel

import android.app.Application
import android.os.Build
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.javo.agents.JavoApplication
import com.javo.agents.data.local.AccountEntity
import com.javo.agents.data.local.ApprovalEntity
import com.javo.agents.data.local.DraftEntity
import com.javo.agents.data.local.GoalEntity
import com.javo.agents.data.local.KeystoreHealthStatus
import com.javo.agents.data.local.NotificationEntity
import com.javo.agents.data.local.TaskEntity
import com.javo.agents.data.model.AIProviderConfig
import com.javo.agents.data.model.AgentInfo
import com.javo.agents.data.model.AgentRoster
import com.javo.agents.data.model.AnalyticsMetric
import com.javo.agents.data.model.DataProvenance
import com.javo.agents.data.model.DiagnosticCheck
import com.javo.agents.data.model.PairingTokenPayload
import com.javo.agents.data.model.PairingTokenValidator
import com.javo.agents.data.model.PairingValidationResult
import com.javo.agents.data.model.ProviderType
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.model.VoiceMessage
import com.javo.agents.data.model.WaveformState
import com.javo.agents.data.model.WorkflowInfo
import com.javo.agents.data.remote.BridgeConnectionState
import com.javo.agents.service.VoiceCaptureService
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val app = application as JavoApplication
    private val container = app.container
    private val keystore = container.keystoreManager
    private val bridge = container.bridgeClient
    private val repo = container.repository

    val tasks: StateFlow<List<TaskEntity>> = repo.observeTasks()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val goals: StateFlow<List<GoalEntity>> = repo.observeGoals()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val drafts: StateFlow<List<DraftEntity>> = repo.draftRepository.observeDrafts()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val approvals: StateFlow<List<ApprovalEntity>> = repo.observeApprovals()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val accounts: StateFlow<List<AccountEntity>> = repo.observeAccounts()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val notifications: StateFlow<List<NotificationEntity>> = repo.observeNotifications()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())

    val connectionState: StateFlow<BridgeConnectionState> = bridge.connectionState

    private val _darkTheme = MutableStateFlow(keystore.isDarkThemeEnabled())
    val darkTheme: StateFlow<Boolean> = _darkTheme.asStateFlow()

    private val _autoRunEnabled = MutableStateFlow(keystore.isAutoRunEnabled())
    val autoRunEnabled: StateFlow<Boolean> = _autoRunEnabled.asStateFlow()

    private val _voiceModeEnabled = MutableStateFlow(keystore.isVoiceModeEnabled())
    val voiceModeEnabled: StateFlow<Boolean> = _voiceModeEnabled.asStateFlow()

    private val _agents = MutableStateFlow(AgentRoster.allAgents)
    val agents: StateFlow<List<AgentInfo>> = _agents.asStateFlow()

    private val _templates = MutableStateFlow(AgentRoster.templates)
    val templates: StateFlow<List<AgentInfo>> = _templates.asStateFlow()

    private val _waveformState = MutableStateFlow(WaveformState.Idle)
    val waveformState: StateFlow<WaveformState> = _waveformState.asStateFlow()

    private val _selectedVoiceLanguage = MutableStateFlow(VoiceLanguage.Hinglish)
    val selectedVoiceLanguage: StateFlow<VoiceLanguage> = _selectedVoiceLanguage.asStateFlow()

    private val _voiceMessages = MutableStateFlow(
        listOf(
            VoiceMessage("v-1", false, "Namaste! Main Javo hoon. Aap English, Hindi ya Hinglish mein bol kar drafts, approvals aur agents manage kar sakte hain.", VoiceLanguage.Hinglish, "Ready"),
            VoiceMessage("v-2", true, "Aaj ke pending Instagram approvals dikhao aur ek Hinglish hook draft banao.", VoiceLanguage.Hinglish, "Sample"),
            VoiceMessage("v-3", false, "2 pending approvals queue mein hain. Content Factory ko Hinglish hook ke liye assign kar diya hai.", VoiceLanguage.Hinglish, "Sample", "Routed to: approval_manager, content_factory")
        )
    )
    val voiceMessages: StateFlow<List<VoiceMessage>> = _voiceMessages.asStateFlow()

    private val _workflows = MutableStateFlow(
        listOf(
            WorkflowInfo("wf-1", "Folder-to-Reel Autopilot", "Folder Watcher", 6, true, true, "Ready • Waiting for new video in D:\\JavoContent", listOf("Folder Watcher", "Content Analyzer", "AI Prompt", "Quality Inspector", "Approval Gate", "Publish")),
            WorkflowInfo("wf-2", "Morning Growth Digest", "Schedule (08:30 IST)", 4, false, true, "Last ran today • 0 errors", listOf("Schedule", "Analytics", "Weekly Analyst", "Notification")),
            WorkflowInfo("wf-3", "Comment Sentiment Guard", "Account Event", 5, true, false, "Paused • Supervised mode", listOf("Account Event", "Condition", "AI Prompt", "Approval Gate", "Comment Reply"))
        )
    )
    val workflows: StateFlow<List<WorkflowInfo>> = _workflows.asStateFlow()

    private val _aiConfig = MutableStateFlow(
        AIProviderConfig(
            activeProvider = ProviderType.LOCAL_PC_OLLAMA,
            hasGeminiKeyStored = keystore.hasGeminiApiKey()
        )
    )
    val aiConfig: StateFlow<AIProviderConfig> = _aiConfig.asStateFlow()

    private val _pairingFeedback = MutableStateFlow<String?>(null)
    val pairingFeedback: StateFlow<String?> = _pairingFeedback.asStateFlow()

    private val _statusToast = MutableStateFlow<String?>(null)
    val statusToast: StateFlow<String?> = _statusToast.asStateFlow()

    private val _exportedSnapshot = MutableStateFlow<String?>(null)
    val exportedSnapshot: StateFlow<String?> = _exportedSnapshot.asStateFlow()

    init {
        viewModelScope.launch {
            repo.seedInitialLocalDataIfEmpty()
            if (keystore.isPaired()) {
                bridge.pingPairedHost()
            }
        }
    }

    fun isOnboardingComplete(): Boolean = keystore.isOnboardingComplete()

    fun completeOnboarding() {
        keystore.saveOnboardingComplete(true)
    }

    fun toggleDarkTheme(enabled: Boolean) {
        _darkTheme.value = enabled
        keystore.saveDarkThemeEnabled(enabled)
    }

    fun toggleAutoRun(enabled: Boolean) {
        _autoRunEnabled.value = enabled
        keystore.saveAutoRunEnabled(enabled)
    }

    fun toggleVoiceMode(enabled: Boolean) {
        _voiceModeEnabled.value = enabled
        keystore.saveVoiceModeEnabled(enabled)
    }

    fun toggleAgentEnabled(slug: String) {
        _agents.update { list ->
            list.map { agent ->
                if (agent.slug == slug) {
                    val next = !agent.isEnabled
                    agent.copy(
                        isEnabled = next,
                        status = if (next) "Active" else "Paused"
                    )
                } else agent
            }
        }
    }

    fun activateTemplate(slug: String) {
        _templates.update { list ->
            list.map { tpl ->
                if (tpl.slug == slug) tpl.copy(isEnabled = true, status = "Applied") else tpl
            }
        }
        _statusToast.value = "Template queued for agent pipeline."
    }

    fun toggleWorkflow(id: String) {
        _workflows.update { list ->
            list.map { wf ->
                if (wf.id == id) wf.copy(isActive = !wf.isActive) else wf
            }
        }
    }

    fun setVoiceLanguage(language: VoiceLanguage) {
        _selectedVoiceLanguage.value = language
    }

    fun startVoiceCapture(hasAudioPermission: Boolean) {
        if (!hasAudioPermission) {
            _statusToast.value = "Microphone permission is required for Push-to-Talk."
            return
        }
        _waveformState.value = WaveformState.Listening
        try {
            VoiceCaptureService.start(app)
        } catch (_: Exception) {
            // Foreground service may be restricted if backgrounded; UI visualizer still operates cleanly
        }
    }

    fun stopAndProcessVoiceCommand(spokenOrTypedText: String) {
        try {
            VoiceCaptureService.stop(app)
        } catch (_: Exception) {
        }
        val query = spokenOrTypedText.trim()
        if (query.isBlank()) {
            _waveformState.value = WaveformState.Idle
            return
        }

        val lang = _selectedVoiceLanguage.value
        val userMsg = VoiceMessage(
            id = "u-${System.currentTimeMillis()}",
            isUser = true,
            text = query,
            language = lang,
            timestampLabel = "Now"
        )
        _voiceMessages.update { it + userMsg }

        viewModelScope.launch {
            _waveformState.value = WaveformState.Thinking
            delay(500)
            _waveformState.value = WaveformState.Executing

            val remoteReply = bridge.sendVoiceCommand(query, lang.code)
            val replyText = remoteReply?.reply ?: when (lang) {
                VoiceLanguage.Hindi -> "Aapka command '${query}' offline queue mein save ho gaya hai. Windows runtime connect hote hi Voice Agent execute karega."
                VoiceLanguage.Hinglish -> "Got it! '${query}' ko local queue mein add kar diya hai. Supervised Autopilot approval ke bina kuch publish nahi hoga."
                VoiceLanguage.English -> "Queued '${query}' locally. Once connected to your paired Windows runtime, Voice Agent will execute it under Supervised Autopilot."
            }

            val assistantMsg = VoiceMessage(
                id = "a-${System.currentTimeMillis()}",
                isUser = false,
                text = replyText,
                language = lang,
                timestampLabel = "Now",
                actionHint = if (remoteReply != null) "Executed via ${remoteReply.routedAgent}" else "Queued offline • Device Sync ready"
            )
            _voiceMessages.update { it + assistantMsg }
            _waveformState.value = WaveformState.Finished
            delay(1200)
            _waveformState.value = WaveformState.Idle
        }
    }

    fun pairWithWindows(rawOrHostUrl: String, manualCode: String = "", manualToken: String = "") {
        val validation = if (manualCode.isBlank() && manualToken.isBlank()) {
            PairingTokenValidator.parseManualOrQr(rawOrHostUrl)
        } else {
            PairingTokenValidator.validate(
                PairingTokenPayload(
                    hostUrl = rawOrHostUrl,
                    pairingCode = manualCode,
                    deviceToken = manualToken,
                    expiresAtEpochSec = (System.currentTimeMillis() / 1000L) + 600L
                )
            )
        }

        when (validation) {
            is PairingValidationResult.Invalid -> {
                _pairingFeedback.value = validation.reason
            }
            is PairingValidationResult.Valid -> {
                val payload = validation.payload
                keystore.savePairingSession(
                    hostUrl = payload.hostUrl,
                    pairingToken = payload.deviceToken,
                    fingerprintSha256 = payload.fingerprintSha256
                )
                keystore.saveOnboardingComplete(true)
                viewModelScope.launch {
                    val result = bridge.confirmPairing(
                        hostUrl = payload.hostUrl,
                        pairingCode = payload.pairingCode,
                        deviceToken = payload.deviceToken,
                        deviceName = "${Build.MANUFACTURER} ${Build.MODEL}"
                    )
                    _pairingFeedback.value = if (result.isSuccess) {
                        "Paired & verified with Windows Local Runtime!"
                    } else {
                        "Credentials encrypted in Android Keystore. Runtime unreachable right now — offline queue active."
                    }
                }
            }
        }
    }

    fun revokePairing() {
        viewModelScope.launch {
            bridge.revokeOnDesktop()
            _pairingFeedback.value = "Pairing revoked and Keystore token wiped."
        }
    }

    fun createOfflineDraft(title: String, body: String, platform: String, scheduledDate: String?) {
        if (title.isBlank() || body.isBlank()) return
        viewModelScope.launch {
            repo.draftRepository.createOfflineDraft(title, body, platform, scheduledDate)
            val synced = repo.draftRepository.queueAndTrySync()
            _statusToast.value = if (synced > 0) "Draft saved & synced ($synced)." else "Draft saved offline; queued for desktop sync."
        }
    }

    fun syncNow() {
        viewModelScope.launch {
            val online = bridge.pingPairedHost()
            val synced = if (online) repo.draftRepository.queueAndTrySync() else 0
            _statusToast.value = if (online) {
                "Windows Runtime reachable. Synced $synced pending items."
            } else {
                "Windows Runtime offline. Changes remain safely queued in Room."
            }
        }
    }

    fun decideApproval(id: String, status: String, content: String, scheduledFor: String) {
        viewModelScope.launch {
            repo.updateApprovalDecision(id, status, content, scheduledFor)
            _statusToast.value = "Approval marked as $status."
        }
    }

    fun addGoal(title: String, description: String, deadline: String) {
        if (title.isBlank()) return
        viewModelScope.launch {
            repo.addGoal(title, description, deadline)
            _statusToast.value = "Goal saved locally."
        }
    }

    fun addAccount(platform: String, handle: String, brand: String) {
        if (handle.isBlank()) return
        viewModelScope.launch {
            repo.addAccountPlaceholder(platform, handle, brand.ifBlank { "Javo Studio" })
            _statusToast.value = "$platform added. Complete OAuth on Windows desktop."
        }
    }

    fun markNotificationRead(id: String) {
        viewModelScope.launch { repo.markNotificationRead(id) }
    }

    fun markAllNotificationsRead() {
        viewModelScope.launch { repo.markAllNotificationsRead() }
    }

    fun selectAIProvider(provider: ProviderType) {
        _aiConfig.update { it.copy(activeProvider = provider) }
    }

    fun saveGeminiKey(apiKey: String) {
        keystore.saveGeminiApiKey(apiKey)
        _aiConfig.update { it.copy(hasGeminiKeyStored = keystore.hasGeminiApiKey()) }
        _statusToast.value = if (keystore.hasGeminiApiKey()) {
            "Gemini API key encrypted in Android Keystore."
        } else {
            "Gemini API key removed."
        }
    }

    fun toggleZeroCostGuard(enabled: Boolean) {
        _aiConfig.update { it.copy(zeroCostGuardEnabled = enabled) }
    }

    fun triggerEmergencyStop() {
        viewModelScope.launch {
            _waveformState.value = WaveformState.Idle
            repo.triggerEmergencyStop()
            _statusToast.value = "Emergency Stop executed: local tasks paused & desktop notified."
        }
    }

    fun exportLocalData() {
        viewModelScope.launch {
            _exportedSnapshot.value = repo.exportLocalSnapshotJson()
        }
    }

    fun deleteAllLocalData() {
        viewModelScope.launch {
            repo.deleteAllLocalData()
            _aiConfig.update { it.copy(hasGeminiKeyStored = false) }
            _exportedSnapshot.value = null
            _statusToast.value = "All local Room data and Keystore secrets deleted."
        }
    }

    fun clearToast() {
        _statusToast.value = null
    }

    fun getKeystoreHealth(): KeystoreHealthStatus = keystore.getHealthStatus()

    fun getPairedHostUrl(): String? = keystore.getPairedHostUrl()

    fun getAnalyticsMetrics(): List<AnalyticsMetric> {
        val draftCount = drafts.value.size
        val pendingCount = approvals.value.count { it.status == "pending" }
        val activeAgents = agents.value.count { it.isEnabled }
        val isConnected = connectionState.value == BridgeConnectionState.Connected

        return listOf(
            AnalyticsMetric("m1", "Active Agents Configured", "$activeAgents / 29", "Local Roster", DataProvenance.LOCAL_DEVICE, "Synced from your Android agent configuration."),
            AnalyticsMetric("m2", "Drafts in Content Studio", "$draftCount", "${drafts.value.count { it.pendingSync }} queued", DataProvenance.LOCAL_DEVICE, "Stored locally in encrypted-ready Room database."),
            AnalyticsMetric("m3", "Approvals Awaiting Review", "$pendingCount", "Supervised Autopilot", DataProvenance.LOCAL_DEVICE, "Human-in-the-loop gate before publishing."),
            AnalyticsMetric("m4", "7-Day Social Reach", if (isConnected) "Syncing..." else "Unavailable", if (isConnected) "Live" else "Pair Windows", DataProvenance.DEMO_UNAVAILABLE, "Real platform reach metrics require Windows OAuth connectors (Instagram/Facebook/YouTube).")
        )
    }

    fun runDiagnostics(): List<DiagnosticCheck> {
        val ks = keystore.getHealthStatus()
        val paired = keystore.isPaired()
        val connected = connectionState.value == BridgeConnectionState.Connected
        return listOf(
            DiagnosticCheck("Android Keystore AES-256-GCM", if (ks.keystoreActive) "Healthy" else "Warning", ks.encryptionScheme, ks.keystoreActive),
            DiagnosticCheck("Local Room Database", "Healthy", "${drafts.value.size} drafts • ${approvals.value.size} approvals • ${goals.value.size} goals", true),
            DiagnosticCheck("Windows Pairing Record", if (paired) "Paired" else "Unpaired", keystore.getPairedHostUrl() ?: "No Windows host paired yet", paired),
            DiagnosticCheck("Windows Runtime Bridge", connectionState.value.label, if (connected) "LAN/HTTPS bridge responding" else "Operating in offline queue mode", connected)
        )
    }
}
