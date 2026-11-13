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
import com.javo.agents.data.model.CustomAiEndpointConfig
import com.javo.agents.data.model.DataProvenance
import com.javo.agents.data.model.DiagnosticCheck
import com.javo.agents.data.model.LanguageUnavailableEvent
import com.javo.agents.data.model.OperatingMode
import com.javo.agents.data.model.PairingTokenPayload
import com.javo.agents.data.model.PairingTokenValidator
import com.javo.agents.data.model.PairingValidationResult
import com.javo.agents.data.model.ProviderType
import com.javo.agents.data.model.RecognizerMode
import com.javo.agents.data.model.SocialConnectionInfo
import com.javo.agents.data.model.SocialPlatform
import com.javo.agents.data.model.VoiceDiagnosticsData
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.model.VoiceConversationMode
import com.javo.agents.data.model.VoiceMessage
import com.javo.agents.data.model.WaveformState
import com.javo.agents.data.model.WorkflowInfo
import com.javo.agents.data.remote.BridgeConnectionState
import com.javo.agents.data.remote.GeminiAuthException
import com.javo.agents.data.remote.GeminiQuotaExceededException
import com.javo.agents.data.remote.GeminiTurn
import com.javo.agents.data.remote.GeminiUnavailableException
import com.javo.agents.service.VoiceRecognitionListener
import com.javo.agents.service.VoiceRecognitionManager
import com.javo.agents.service.VoiceTtsManager
import com.javo.agents.workers.TaskReminderWorker
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.withTimeoutOrNull
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import java.util.UUID

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val app = application as JavoApplication
    private val container = app.container
    private val keystore = container.keystoreManager
    private val bridge = container.bridgeClient
    private val gemini = container.geminiClient
    private val repo = container.repository
    private val orchestrator = container.orchestrator
    private val ttsManager by lazy { VoiceTtsManager(app) }

    private val _operatingMode = MutableStateFlow(keystore.getOperatingMode())
    val operatingMode: StateFlow<OperatingMode> = _operatingMode.asStateFlow()

    private val _ttsEnabled = MutableStateFlow(keystore.isTtsEnabled())
    val ttsEnabled: StateFlow<Boolean> = _ttsEnabled.asStateFlow()
    val isTtsSpeaking: StateFlow<Boolean> = ttsManager.isSpeaking

    private val _customAiConfig = MutableStateFlow(keystore.getCustomAiEndpoint())
    val customAiConfig: StateFlow<CustomAiEndpointConfig> = _customAiConfig.asStateFlow()

    private val _isGeneratingDraft = MutableStateFlow(false)
    val isGeneratingDraft: StateFlow<Boolean> = _isGeneratingDraft.asStateFlow()

    private val _isExecutingTask = MutableStateFlow<String?>(null)
    val isExecutingTask: StateFlow<String?> = _isExecutingTask.asStateFlow()

    private val _socialConnections = MutableStateFlow<List<SocialConnectionInfo>>(emptyList())
    val socialConnections: StateFlow<List<SocialConnectionInfo>> = _socialConnections.asStateFlow()

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

    private val _liveRmsAmplitude = MutableStateFlow(0f)
    val liveRmsAmplitude: StateFlow<Float> = _liveRmsAmplitude.asStateFlow()

    private val _liveSpeechTranscript = MutableStateFlow("")
    val liveSpeechTranscript: StateFlow<String> = _liveSpeechTranscript.asStateFlow()

    private val _selectedVoiceLanguage = MutableStateFlow(VoiceLanguage.Hinglish)
    val selectedVoiceLanguage: StateFlow<VoiceLanguage> = _selectedVoiceLanguage.asStateFlow()

    // No seeded/demo conversation. History is restored only after user opt-in.
    private val _voiceMessages = MutableStateFlow(keystore.getVoiceConversation())
    val voiceMessages: StateFlow<List<VoiceMessage>> = _voiceMessages.asStateFlow()

    private val _voiceHistoryEnabled = MutableStateFlow(keystore.isVoiceHistoryEnabled())
    val voiceHistoryEnabled: StateFlow<Boolean> = _voiceHistoryEnabled.asStateFlow()

    fun setVoiceHistoryEnabled(enabled: Boolean) {
        keystore.setVoiceHistoryEnabled(enabled)
        _voiceHistoryEnabled.value = enabled
        if (enabled) keystore.saveVoiceConversation(_voiceMessages.value)
        _statusToast.value = if (enabled) {
            "Encrypted chat history enabled on this device. Use Clear to delete it."
        } else {
            "Saved chat history deleted. Current on-screen messages remain until you clear them."
        }
    }

    private fun persistVoiceHistoryIfEnabled() {
        if (_voiceHistoryEnabled.value) keystore.saveVoiceConversation(_voiceMessages.value)
    }

    /** Only verified Gemini replies and their immediate user turns may enter Gemini context. */
    private fun verifiedGeminiHistory(): List<GeminiTurn> =
        _voiceMessages.value.zipWithNext()
            .filter { (before, after) ->
                before.isUser && !after.isUser &&
                    after.actionHint?.startsWith("Google Gemini (") == true
            }
            .takeLast(6)
            .flatMap { (before, after) ->
                listOf(GeminiTurn("user", before.text), GeminiTurn("model", after.text))
            }

    // Clean baseline: empty workflows unless configured or demo mode is on
    private val _workflows = MutableStateFlow<List<WorkflowInfo>>(emptyList())
    val workflows: StateFlow<List<WorkflowInfo>> = _workflows.asStateFlow()

    private val _demoModeActive = MutableStateFlow(keystore.isDemoModeEnabled())
    val demoModeActive: StateFlow<Boolean> = _demoModeActive.asStateFlow()

    private val _aiConfig = MutableStateFlow(
        AIProviderConfig(
            activeProvider = keystore.getSelectedAiProvider(),
            geminiModelName = keystore.getGeminiModel(),
            hasGeminiKeyStored = keystore.hasGeminiApiKey()
        )
    )
    val aiConfig: StateFlow<AIProviderConfig> = _aiConfig.asStateFlow()

    private val _geminiTestFeedback = MutableStateFlow<String?>(null)
    val geminiTestFeedback: StateFlow<String?> = _geminiTestFeedback.asStateFlow()

    private val _isTestingGemini = MutableStateFlow(false)
    val isTestingGemini: StateFlow<Boolean> = _isTestingGemini.asStateFlow()

    private val _pairingFeedback = MutableStateFlow<String?>(null)
    val pairingFeedback: StateFlow<String?> = _pairingFeedback.asStateFlow()

    private val _statusToast = MutableStateFlow<String?>(null)
    val statusToast: StateFlow<String?> = _statusToast.asStateFlow()

    private val _exportedSnapshot = MutableStateFlow<String?>(null)
    val exportedSnapshot: StateFlow<String?> = _exportedSnapshot.asStateFlow()

    private val _recognizerMode = MutableStateFlow(keystore.getRecognizerMode())
    val recognizerMode: StateFlow<RecognizerMode> = _recognizerMode.asStateFlow()

    private val _languageUnavailableEvent = MutableStateFlow<LanguageUnavailableEvent?>(null)
    val languageUnavailableEvent: StateFlow<LanguageUnavailableEvent?> = _languageUnavailableEvent.asStateFlow()

    private val _actionableVoiceError = MutableStateFlow<String?>(null)
    val actionableVoiceError: StateFlow<String?> = _actionableVoiceError.asStateFlow()

    private val _voiceConversationMode = MutableStateFlow(keystore.getVoiceConversationMode())
    val voiceConversationMode: StateFlow<VoiceConversationMode> = _voiceConversationMode.asStateFlow()

    private val _isHandsFreeSessionActive = MutableStateFlow(false)
    val isHandsFreeSessionActive: StateFlow<Boolean> = _isHandsFreeSessionActive.asStateFlow()

    private val _ttsSpeechRate = MutableStateFlow(keystore.getTtsSpeechRate())
    val ttsSpeechRate: StateFlow<Float> = _ttsSpeechRate.asStateFlow()

    private val isProcessingVoiceCommand = AtomicBoolean(false)

    private val voiceManager by lazy {
        VoiceRecognitionManager(
            context = app,
            listener = object : VoiceRecognitionListener {
                override fun onConnecting() {
                    _waveformState.value = WaveformState.Connecting
                }

                override fun onReadyForSpeech() {
                    _waveformState.value = WaveformState.Listening
                    _actionableVoiceError.value = null
                    _languageUnavailableEvent.value = null
                }

                override fun onBeginningOfSpeech() {
                    // Speech detected
                }

                override fun onRmsChanged(amplitude: Float) {
                    _liveRmsAmplitude.value = amplitude
                }

                override fun onPartialResults(partialText: String) {
                    _liveSpeechTranscript.value = partialText
                }

                override fun onEndOfSpeech() {
                    _liveRmsAmplitude.value = 0f
                    _waveformState.value = WaveformState.Finalizing
                }

                override fun onFinalizing() {
                    _liveRmsAmplitude.value = 0f
                    _waveformState.value = WaveformState.Finalizing
                }

                override fun onResults(finalText: String) {
                    val candidate = if (finalText.isNotBlank()) finalText else _liveSpeechTranscript.value
                    _liveSpeechTranscript.value = ""
                    _liveRmsAmplitude.value = 0f
                    if (candidate.isNotBlank()) {
                        stopAndProcessVoiceCommand(candidate)
                    } else {
                        _waveformState.value = WaveformState.Idle
                    }
                }

                override fun onFinalizationTimeout(capturedPartial: String) {
                    val candidate = if (capturedPartial.isNotBlank()) capturedPartial else _liveSpeechTranscript.value
                    _liveSpeechTranscript.value = ""
                    _liveRmsAmplitude.value = 0f
                    if (candidate.isNotBlank()) {
                        stopAndProcessVoiceCommand(candidate)
                    } else {
                        _waveformState.value = WaveformState.Idle
                        _actionableVoiceError.value = "Listening finished. Tap mic to retry."
                    }
                }

                override fun onCancelled() {
                    _liveSpeechTranscript.value = ""
                    _liveRmsAmplitude.value = 0f
                    _waveformState.value = WaveformState.Idle
                    _isHandsFreeSessionActive.value = false
                    isProcessingVoiceCommand.set(false)
                }

                override fun onError(errorCode: Int, errorMessage: String, isActionable: Boolean) {
                    _liveSpeechTranscript.value = ""
                    _liveRmsAmplitude.value = 0f
                    _waveformState.value = WaveformState.Idle
                    isProcessingVoiceCommand.set(false)
                    if (isActionable) {
                        _actionableVoiceError.value = errorMessage
                    }
                    if (errorCode != android.speech.SpeechRecognizer.ERROR_NO_MATCH &&
                        errorCode != android.speech.SpeechRecognizer.ERROR_SPEECH_TIMEOUT
                    ) {
                        _statusToast.value = errorMessage
                    }
                }

                override fun onLanguageUnavailable(language: VoiceLanguage, messageHindi: String, messageEnglish: String) {
                    _liveSpeechTranscript.value = ""
                    _liveRmsAmplitude.value = 0f
                    _waveformState.value = WaveformState.Idle
                    isProcessingVoiceCommand.set(false)
                    _languageUnavailableEvent.value = LanguageUnavailableEvent(language, messageHindi, messageEnglish)
                    _statusToast.value = messageHindi
                }
            }
        )
    }

    init {
        viewModelScope.launch {
            repo.migrateLegacySampleDataIfPresent()
            if (keystore.isPaired()) {
                bridge.pingPairedHost()
            }
            refreshSocialConnections()
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

    fun setOperatingMode(mode: OperatingMode) {
        keystore.saveOperatingMode(mode)
        _operatingMode.value = mode
        // Mode controls available device capabilities, not the user's chosen AI provider.
        // Never replace an explicitly selected provider just because another key exists.
        _statusToast.value = if (
            mode != OperatingMode.WINDOWS_ENHANCED &&
            _aiConfig.value.activeProvider == ProviderType.LOCAL_PC_OLLAMA
        ) {
            "Mobile mode enabled. Select Gemini or Custom AI in Settings → AI Providers to receive phone-only replies."
        } else {
            "Switched to ${mode.displayName}"
        }
    }

    fun toggleTts(enabled: Boolean) {
        keystore.saveTtsEnabled(enabled)
        _ttsEnabled.value = enabled
        if (!enabled) {
            ttsManager.stop()
        }
        _statusToast.value = if (enabled) "Voice replies enabled (TTS)" else "Voice audio replies muted"
    }

    fun stopTts() {
        ttsManager.stop()
    }

    fun toggleAgentEnabled(slug: String) {
        _agents.update { list ->
            list.map { agent ->
                if (agent.slug == slug) {
                    val next = !agent.isEnabled
                    agent.copy(
                        isEnabled = next,
                        status = if (next) "Enabled" else "Disabled"
                    )
                } else agent
            }
        }
    }

    fun activateTemplate(slug: String) {
        _templates.update { list ->
            list.map { tpl ->
                if (tpl.slug == slug) tpl.copy(isEnabled = true, status = "Selected") else tpl
            }
        }
        _statusToast.value = "Template selected for this session. Create an actual task in Workflows to run a specialist."
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
        _languageUnavailableEvent.value = null
        _actionableVoiceError.value = null
    }

    fun setRecognizerMode(mode: RecognizerMode) {
        keystore.saveRecognizerMode(mode)
        _recognizerMode.value = mode
        _languageUnavailableEvent.value = null
        _actionableVoiceError.value = null
        _statusToast.value = "Recognizer set to ${mode.displayName}"
    }

    fun switchRecognizerToOnlineAndRetry() {
        setRecognizerMode(RecognizerMode.ONLINE_ONLY)
        _languageUnavailableEvent.value = null
        _actionableVoiceError.value = null
        startVoiceCapture(hasAudioPermission = true)
    }

    fun triggerLanguageModelDownload() {
        voiceManager.triggerModelDownload(_selectedVoiceLanguage.value)
        _statusToast.value = "Triggered language model download request."
    }

    fun createOpenVoiceSettingsIntent(): android.content.Intent = voiceManager.createOpenVoiceSettingsIntent()

    fun dismissLanguageUnavailable() {
        _languageUnavailableEvent.value = null
    }

    fun clearActionableVoiceError() {
        _actionableVoiceError.value = null
    }

    fun getVoiceDiagnostics(): VoiceDiagnosticsData {
        return voiceManager.getDiagnostics(
            selectedLanguage = _selectedVoiceLanguage.value,
            recognizerMode = _recognizerMode.value,
            waveformState = _waveformState.value,
            hasRecordAudioPermission = true
        )
    }

    fun exportVoiceDiagnosticsJson(): String {
        val diag = getVoiceDiagnostics()
        val escapedError = diag.lastErrorMessage?.replace("\"", "\\\"")?.replace("\n", "\\n")
        return buildString {
            appendLine("{")
            appendLine("  \"android_version\": \"${diag.androidVersion}\",")
            appendLine("  \"api_level\": ${diag.apiLevel},")
            appendLine("  \"device_model\": \"${diag.deviceModel}\",")
            appendLine("  \"system_recognition_available\": ${diag.isSystemRecognitionAvailable},")
            appendLine("  \"on_device_recognition_available\": ${diag.isOnDeviceRecognitionAvailable},")
            appendLine("  \"selected_recognizer_mode\": \"${diag.selectedRecognizerMode.name}\",")
            appendLine("  \"active_recognizer_type\": \"${diag.activeRecognizerType}\",")
            appendLine("  \"selected_language\": \"${diag.selectedLanguage.displayName}\",")
            appendLine("  \"language_code\": \"${diag.languageCode}\",")
            appendLine("  \"is_installed_on_device\": ${diag.isInstalledOnDevice},")
            appendLine("  \"is_supported_on_device\": ${diag.isSupportedOnDevice},")
            appendLine("  \"is_supported_online\": ${diag.isSupportedOnline},")
            appendLine("  \"has_mic_permission\": ${diag.hasRecordAudioPermission},")
            appendLine("  \"waveform_state\": \"${diag.waveformState.name}\",")
            appendLine("  \"last_error_code\": ${diag.lastErrorCode},")
            appendLine("  \"last_error_message\": ${if (escapedError != null) "\"$escapedError\"" else "null"},")
            appendLine("  \"reconnect_attempts\": ${diag.reconnectAttemptCount},")
            appendLine("  \"exported_at_ms\": ${System.currentTimeMillis()}")
            appendLine("}")
        }
    }

    fun startVoiceCapture(hasAudioPermission: Boolean) {
        if (ttsManager.isSpeaking.value) {
            ttsManager.stop()
        }

        if (!hasAudioPermission) {
            _statusToast.value = "Microphone permission is required for Voice Mode."
            return
        }

        if (_waveformState.value == WaveformState.Connecting ||
            _waveformState.value == WaveformState.Listening
        ) {
            stopVoiceListening()
            return
        }

        _languageUnavailableEvent.value = null
        _actionableVoiceError.value = null
        _waveformState.value = WaveformState.Connecting
        _liveSpeechTranscript.value = ""
        _liveRmsAmplitude.value = 0f
        if (_voiceConversationMode.value == VoiceConversationMode.HANDS_FREE) {
            _isHandsFreeSessionActive.value = true
        }
        voiceManager.startListening(_selectedVoiceLanguage.value, _recognizerMode.value)
    }

    fun stopVoiceListening() {
        try {
            voiceManager.stopListening()
        } catch (_: Exception) {}
    }

    fun cancelVoiceCapture() {
        try {
            voiceManager.cancel()
        } catch (_: Exception) {}
        _liveSpeechTranscript.value = ""
        _liveRmsAmplitude.value = 0f
        _waveformState.value = WaveformState.Idle
        _isHandsFreeSessionActive.value = false
        isProcessingVoiceCommand.set(false)
    }

    fun stopSpeaking() {
        ttsManager.stop()
        _waveformState.value = WaveformState.Idle
    }

    fun setVoiceConversationMode(mode: VoiceConversationMode) {
        _voiceConversationMode.value = mode
        keystore.saveVoiceConversationMode(mode)
        if (mode == VoiceConversationMode.TAP_TO_TALK) {
            _isHandsFreeSessionActive.value = false
        }
    }

    fun setTtsSpeechRate(rate: Float) {
        _ttsSpeechRate.value = rate
        ttsManager.setSpeechRate(rate)
        keystore.saveTtsSpeechRate(rate)
    }

    fun stopAndProcessVoiceCommand(spokenOrTypedText: String) {
        if (!isProcessingVoiceCommand.compareAndSet(false, true)) {
            return
        }
        stopVoiceListening()
        val query = spokenOrTypedText.trim()
        if (query.isBlank()) {
            _waveformState.value = WaveformState.Idle
            isProcessingVoiceCommand.set(false)
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
        persistVoiceHistoryIfEnabled()

        viewModelScope.launch {
            _waveformState.value = WaveformState.Thinking

            var replyText: String
            var actionHint: String? = null
            var verifiedProviderResponse = false

            // Only the explicitly selected provider may process this utterance.
            // Never silently switch to another AI provider based on a stored key.
            when (_aiConfig.value.activeProvider) {
                ProviderType.LOCAL_PC_OLLAMA -> {
                    if (_operatingMode.value != OperatingMode.WINDOWS_ENHANCED) {
                        replyText = "Windows Ollama is selected, but Android is in standalone mode. Open Settings → AI Providers and select Gemini or your Custom AI endpoint."
                        actionHint = "Provider requires Windows mode"
                    } else if (connectionState.value != BridgeConnectionState.Connected) {
                        replyText = "Selected provider Windows Ollama is not connected. Pair with the Windows runtime, or explicitly choose a phone AI provider."
                        actionHint = "Windows unavailable"
                    } else {
                        val remoteReply = withTimeoutOrNull(25_000L) {
                            bridge.sendVoiceCommand(query, lang.code)
                        }
                        val actualReply = remoteReply?.getOrNull()?.reply
                        if (remoteReply?.isSuccess == true && !actualReply.isNullOrBlank()) {
                            replyText = actualReply
                            verifiedProviderResponse = true
                            actionHint = "Response from Windows runtime"
                        } else {
                            val err = remoteReply?.exceptionOrNull()?.message
                                ?: "Timed out, unreachable, or empty response"
                            replyText = "Windows request failed: $err. Nothing was confirmed as executed."
                            actionHint = "Provider request failed"
                        }
                    }
                }

                ProviderType.GEMINI_DIRECT -> {
                    if (!keystore.hasGeminiApiKey()) {
                        replyText = "Google Gemini is selected but no API key is configured. Open Settings → AI Providers, save your own key, and test the connection."
                        actionHint = "Set up Gemini key"
                    } else {
                        val activeModel = keystore.getGeminiModel()
                        val systemPrompt = "You are Javo, a helpful Hindi/Hinglish-first conversational assistant. Answer the user's actual question accurately, naturally and concisely. Propose authorized tool actions instead of claiming to execute them. Never fabricate actions, completed tasks or social publishing."
                        val geminiRes = withTimeoutOrNull(25_000L) {
                            gemini.generateResponse(
                                prompt = query,
                                apiKey = keystore.getGeminiApiKey().orEmpty(),
                                model = activeModel,
                                systemInstruction = systemPrompt,
                                history = verifiedGeminiHistory()
                            )
                        }
                        if (geminiRes == null) {
                            replyText = "Gemini request timed out. Check your network and try again."
                            actionHint = "Provider timeout"
                        } else if (geminiRes.isSuccess) {
                            replyText = geminiRes.getOrThrow()
                            verifiedProviderResponse = true
                            actionHint = "Google Gemini ($activeModel)"
                        } else {
                            val ex = geminiRes.exceptionOrNull()
                            replyText = when (ex) {
                                is GeminiQuotaExceededException -> "Gemini quota/rate limit reached. Check your quota and retry later."
                                is GeminiAuthException -> "Gemini key rejected. Review Settings → AI Providers."
                                is GeminiUnavailableException -> "Gemini service is temporarily unavailable. Please retry."
                                else -> "Gemini request failed: ${ex?.message ?: "Unknown error"}"
                            }
                            actionHint = "Provider error"
                        }
                    }
                }

                ProviderType.CUSTOM_ENDPOINT -> {
                    val endpoint = keystore.getCustomAiEndpoint()
                    if (!endpoint.isEnabled || endpoint.endpointUrl.isBlank()) {
                        replyText = "Custom AI is selected but its endpoint is not configured. Set a valid endpoint URL and model under Settings → AI Providers."
                        actionHint = "Configure Custom AI"
                    } else {
                        val systemPrompt = "You are Javo, a helpful, Hindi/Hinglish-first assistant. Never fabricate completed external actions."
                        val customRes = withTimeoutOrNull(25_000L) {
                            orchestrator.callCustomEndpoint(endpoint, query, systemPrompt)
                        }
                        if (customRes == null) {
                            replyText = "Custom AI endpoint request timed out."
                            actionHint = "Provider timeout"
                        } else if (customRes.isSuccess) {
                            replyText = customRes.getOrThrow()
                            verifiedProviderResponse = true
                            actionHint = "Custom AI (${endpoint.modelName})"
                        } else {
                            val err = customRes.exceptionOrNull()?.message ?: "Request failed"
                            replyText = "Custom AI endpoint failed: $err"
                            actionHint = "Provider error"
                        }
                    }
                }
            }

            val assistantMsg = VoiceMessage(
                id = "a-${System.currentTimeMillis()}",
                isUser = false,
                text = replyText,
                language = lang,
                timestampLabel = "Now",
                actionHint = actionHint
            )
            _voiceMessages.update { it + assistantMsg }
            persistVoiceHistoryIfEnabled()
            _waveformState.value = WaveformState.Responding
            isProcessingVoiceCommand.set(false)

            // Network/provider failures should be read as actionable text,
            // not voiced as though Javo completed a legitimate AI reply.
            if (verifiedProviderResponse && _ttsEnabled.value) {
                _waveformState.value = WaveformState.Speaking
                val started = ttsManager.speak(replyText, lang) {
                    viewModelScope.launch {
                        _waveformState.value = WaveformState.Idle
                        if (_voiceConversationMode.value == VoiceConversationMode.HANDS_FREE &&
                            _isHandsFreeSessionActive.value &&
                            _waveformState.value == WaveformState.Idle
                        ) {
                            delay(650)
                            if (_isHandsFreeSessionActive.value && _waveformState.value == WaveformState.Idle) {
                                startVoiceCapture(hasAudioPermission = true)
                            }
                        }
                    }
                }
                if (!started) {
                    _waveformState.value = WaveformState.Idle
                }
            } else {
                delay(600)
                _waveformState.value = WaveformState.Idle
            }
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
                viewModelScope.launch {
                    _pairingFeedback.value = "Verifying pairing with Windows Runtime at ${payload.hostUrl}..."
                    val result = bridge.confirmPairing(
                        hostUrl = payload.hostUrl,
                        pairingCode = payload.pairingCode,
                        deviceToken = payload.deviceToken,
                        deviceName = "${Build.MANUFACTURER} ${Build.MODEL}"
                    )
                    if (result.isSuccess) {
                        keystore.savePairingSession(
                            hostUrl = payload.hostUrl,
                            pairingToken = payload.deviceToken,
                            fingerprintSha256 = payload.fingerprintSha256
                        )
                        keystore.saveOnboardingComplete(true)
                        _pairingFeedback.value = "Paired & verified with Windows Local Runtime!"
                    } else {
                        val errMsg = result.exceptionOrNull()?.message ?: "Host unreachable or pairing rejected"
                        _pairingFeedback.value = "Pairing failed: $errMsg. Check that Windows Runtime is running on the same network."
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
            if (online) {
                val synced = repo.draftRepository.queueAndTrySync()
                _statusToast.value = "Windows Runtime reachable. Synced $synced pending items."
            } else {
                _statusToast.value = "Windows Runtime offline or unauthenticated. Drafts safely kept in local storage."
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
        keystore.saveSelectedAiProvider(provider)
        _aiConfig.update { it.copy(activeProvider = provider) }
        _statusToast.value = if (
            provider == ProviderType.LOCAL_PC_OLLAMA &&
            _operatingMode.value != OperatingMode.WINDOWS_ENHANCED
        ) {
            "Windows Ollama requires Windows Enhanced mode and a verified pairing."
        } else {
            "AI provider selected: ${provider.label}"
        }
    }

    fun selectGeminiModel(model: String) {
        keystore.saveGeminiModel(model)
        _aiConfig.update { it.copy(geminiModelName = model) }
        _geminiTestFeedback.value = null
    }

    fun saveGeminiKey(apiKey: String) {
        keystore.saveGeminiApiKey(apiKey)
        _aiConfig.update { it.copy(hasGeminiKeyStored = keystore.hasGeminiApiKey()) }
        _geminiTestFeedback.value = null
        _statusToast.value = if (keystore.hasGeminiApiKey()) {
            "Gemini API key encrypted in Android Keystore."
        } else {
            "Gemini API key removed."
        }
    }

    fun testGeminiConnection() {
        val apiKey = keystore.getGeminiApiKey()
        if (apiKey.isNullOrBlank()) {
            _geminiTestFeedback.value = "Save an API key first before testing connection."
            return
        }
        val model = keystore.getGeminiModel()
        viewModelScope.launch {
            _isTestingGemini.value = true
            _geminiTestFeedback.value = "Testing connection to $model..."
            val result = gemini.testConnection(apiKey, model)
            _isTestingGemini.value = false
            if (result.isSuccess) {
                _geminiTestFeedback.value = result.getOrNull() ?: "Connected successfully to $model!"
            } else {
                val ex = result.exceptionOrNull()
                _geminiTestFeedback.value = when (ex) {
                    is GeminiQuotaExceededException -> "Quota/Rate limit hit (HTTP 429). Check your Google AI Studio quota."
                    is GeminiAuthException -> "Authentication failed (HTTP 401/403). Invalid API key."
                    is GeminiUnavailableException -> "Service unavailable (HTTP 500/503). Try again later."
                    else -> "Connection failed: ${ex?.message ?: "Unknown error"}"
                }
            }
        }
    }

    fun toggleZeroCostGuard(enabled: Boolean) {
        _aiConfig.update { it.copy(zeroCostGuardEnabled = enabled) }
    }

    fun updateDraft(draft: DraftEntity) {
        viewModelScope.launch {
            repo.updateDraft(draft)
            _statusToast.value = "Draft updated."
        }
    }

    fun deleteDraft(id: String) {
        viewModelScope.launch {
            repo.deleteDraft(id)
            _statusToast.value = "Draft deleted."
        }
    }

    fun deleteApproval(id: String) {
        viewModelScope.launch {
            repo.deleteApproval(id)
            _statusToast.value = "Approval item deleted."
        }
    }

    fun createLocalTask(
        title: String,
        assignedAgent: String = "growth_scientist",
        priority: String = "normal",
        goalId: String? = null,
        description: String = "",
        scheduledEpochMs: Long? = null,
        isReminderEnabled: Boolean = false
    ) {
        if (title.isBlank()) return
        viewModelScope.launch {
            val task = repo.addTask(
                title = title,
                assignedAgent = assignedAgent,
                priority = priority,
                goalId = goalId,
                description = description,
                scheduledEpochMs = scheduledEpochMs,
                isReminderEnabled = isReminderEnabled
            )
            if (scheduledEpochMs != null && scheduledEpochMs > System.currentTimeMillis()) {
                val delayMs = scheduledEpochMs - System.currentTimeMillis()
                TaskReminderWorker.scheduleTaskReminder(
                    context = app,
                    taskId = task.id,
                    taskTitle = task.title,
                    taskAgent = task.assignedAgent,
                    delayMs = delayMs,
                    executeAtEnd = true
                )
                _statusToast.value = "Task scheduled with autonomous reminder."
            } else if (isReminderEnabled) {
                TaskReminderWorker.scheduleTaskReminder(
                    context = app,
                    taskId = task.id,
                    taskTitle = task.title,
                    taskAgent = task.assignedAgent,
                    delayMs = 3600000L, // 1 hour reminder default
                    executeAtEnd = false
                )
                _statusToast.value = "Task created with reminder enabled."
            } else {
                _statusToast.value = "Task created in local queue."
            }
        }
    }

    fun executeTaskLocally(taskId: String) {
        viewModelScope.launch {
            _isExecutingTask.value = taskId
            val task = container.database.taskDao().getById(taskId)
            if (task == null) {
                _statusToast.value = "Task not found."
                _isExecutingTask.value = null
                return@launch
            }
            val result = orchestrator.executeTask(task)
            _isExecutingTask.value = null
            if (result.isSuccess) {
                _statusToast.value = "Task completed by ${task.assignedAgent}."
            } else {
                val err = result.exceptionOrNull()?.message ?: "Execution failed"
                _statusToast.value = err
            }
        }
    }

    fun updateTaskStatus(taskId: String, newState: String) {
        viewModelScope.launch {
            repo.updateTaskState(taskId, newState)
            _statusToast.value = "Task updated to $newState."
        }
    }

    fun deleteTask(taskId: String) {
        viewModelScope.launch {
            TaskReminderWorker.cancelTaskReminder(app, taskId)
            repo.deleteTask(taskId)
            _statusToast.value = "Task removed."
        }
    }

    fun generateContentDraftWithAi(
        topic: String,
        platform: String = "Instagram",
        language: VoiceLanguage = _selectedVoiceLanguage.value
    ) {
        if (topic.isBlank()) return
        viewModelScope.launch {
            _isGeneratingDraft.value = true
            val result = orchestrator.generateContentDraft(topic, platform, language)
            _isGeneratingDraft.value = false
            if (result.isSuccess) {
                _statusToast.value = "Generated new draft for $platform!"
            } else {
                val err = result.exceptionOrNull()?.message ?: "Draft generation failed"
                _statusToast.value = err
            }
        }
    }

    fun createDraftWithMedia(
        title: String,
        body: String,
        platform: String,
        scheduledDate: String? = null,
        mediaUri: String? = null,
        mediaMimeType: String? = null,
        tags: String = ""
    ) {
        if (title.isBlank() || body.isBlank()) return
        viewModelScope.launch {
            repo.draftRepository.createOfflineDraft(
                title = title,
                body = body,
                platform = platform,
                scheduledDateLabel = scheduledDate,
                mediaUri = mediaUri,
                mediaMimeType = mediaMimeType,
                tags = tags
            )
            val synced = repo.draftRepository.queueAndTrySync()
            _statusToast.value = if (synced > 0) "Draft saved & synced ($synced)." else "Draft saved offline in local storage."
        }
    }

    fun saveCustomAiEndpoint(url: String, apiKey: String, model: String, enabled: Boolean) {
        keystore.saveCustomAiEndpoint(url, apiKey, model, enabled)
        val updated = keystore.getCustomAiEndpoint()
        _customAiConfig.value = updated
        if (enabled) {
            selectAIProvider(ProviderType.CUSTOM_ENDPOINT)
        }
        _statusToast.value = if (enabled) "Custom AI Endpoint saved & active." else "Custom AI Endpoint disabled."
    }

    fun refreshSocialConnections() {
        val list = listOf(
            createSocialInfo(SocialPlatform.YOUTUBE),
            createSocialInfo(SocialPlatform.INSTAGRAM),
            createSocialInfo(SocialPlatform.FACEBOOK),
            createSocialInfo(SocialPlatform.TELEGRAM)
        )
        _socialConnections.value = list
    }

    private fun createSocialInfo(platform: SocialPlatform): SocialConnectionInfo {
        val token = keystore.getSocialToken(platform.id)
        val isConnected = !token.isNullOrBlank()
        return if (isConnected) {
            SocialConnectionInfo(
                platform = platform,
                isConnected = true,
                accountName = "Connected Account",
                statusLabel = "Connected",
                statusDescription = "Authorized for publishing via Android Keystore token.",
                requiresSetup = false,
                lastSyncEpochMs = System.currentTimeMillis()
            )
        } else {
            val setupDesc = when (platform) {
                SocialPlatform.YOUTUBE -> "Requires Google Cloud Console OAuth 2.0 Client ID for YouTube Data API v3."
                SocialPlatform.INSTAGRAM -> "Requires Meta App ID with Instagram Content Publishing permissions."
                SocialPlatform.FACEBOOK -> "Requires Meta App ID with Pages Manage Posts permissions."
                SocialPlatform.TELEGRAM -> "Requires Telegram Bot Token configured in Settings."
            }
            SocialConnectionInfo(
                platform = platform,
                isConnected = false,
                statusLabel = "Setup Required",
                statusDescription = setupDesc,
                requiresSetup = true
            )
        }
    }

    fun disconnectSocialPlatform(platform: SocialPlatform) {
        keystore.removeSocialToken(platform.id)
        refreshSocialConnections()
        _statusToast.value = "${platform.displayName} disconnected."
    }

    fun toggleDemoMode(enabled: Boolean) {
        viewModelScope.launch {
            if (enabled) {
                repo.loadDemoData()
                _demoModeActive.value = true
                _statusToast.value = "Demo Mode loaded sample drafts & tasks."
            } else {
                repo.clearDemoData()
                _demoModeActive.value = false
                _statusToast.value = "Demo sample records cleared."
            }
        }
    }

    fun clearVoiceHistory() {
        _voiceMessages.value = emptyList()
        keystore.clearVoiceConversation()
        _statusToast.value = "Voice conversation and saved local history cleared."
    }

    override fun onCleared() {
        super.onCleared()
        voiceManager.destroy()
        ttsManager.shutdown()
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
