package com.javo.agents.service

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.speech.RecognitionListener
import android.speech.RecognitionSupport
import android.speech.RecognitionSupportCallback
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import androidx.core.content.ContextCompat
import com.javo.agents.data.model.RecognizerMode
import com.javo.agents.data.model.VoiceDiagnosticsData
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.model.WaveformState
import java.util.concurrent.atomic.AtomicLong

interface VoiceRecognitionListener {
    fun onConnecting() {}
    fun onReadyForSpeech() {}
    fun onBeginningOfSpeech() {}
    fun onRmsChanged(amplitude: Float) {}
    fun onPartialResults(partialText: String) {}
    fun onFinalizing() {}
    fun onResults(finalText: String) {}
    fun onError(errorCode: Int, errorMessage: String, isActionable: Boolean = false) {}
    fun onLanguageUnavailable(language: VoiceLanguage, messageHindi: String, messageEnglish: String) {}
    fun onEndOfSpeech() {}
    fun onFinalizationTimeout(capturedPartial: String = "") {}
    fun onCancelled() {}
}

@SuppressLint("NewApi")
class VoiceRecognitionManager(
    private val context: Context,
    private val listener: VoiceRecognitionListener
) {
    private var speechRecognizer: SpeechRecognizer? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    private val activeSessionToken = AtomicLong(0L)

    @Volatile var isCurrentlyListening = false
        private set

    @Volatile var isCurrentlyFinalizing = false
        private set

    private var connectionWatchdog: Runnable? = null
    private var silenceWatchdog: Runnable? = null
    private var finalizationWatchdog: Runnable? = null

    private var lastErrorCode: Int? = null
    private var lastErrorMessage: String? = null
    private var reconnectAttemptCount = 0
    private var activeRecognizerType: String = "None"
    private val cachedLanguageSupport = mutableMapOf<String, Boolean>() // langCode -> isInstalledOnDevice

    fun isRecognitionAvailable(): Boolean {
        return SpeechRecognizer.isRecognitionAvailable(context)
    }

    fun isOnDeviceAvailable(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            SpeechRecognizer.isOnDeviceRecognitionAvailable(context)
        } else {
            false
        }
    }

    private fun clearWatchdogs() {
        connectionWatchdog?.let { mainHandler.removeCallbacks(it) }
        connectionWatchdog = null
        silenceWatchdog?.let { mainHandler.removeCallbacks(it) }
        silenceWatchdog = null
        finalizationWatchdog?.let { mainHandler.removeCallbacks(it) }
        finalizationWatchdog = null
    }

    @SuppressLint("NewApi")
    private fun createOnDeviceSpeechRecognizerSafely(): SpeechRecognizer? {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S && SpeechRecognizer.isOnDeviceRecognitionAvailable(context)) {
            try {
                SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
            } catch (_: Exception) {
                null
            }
        } else {
            null
        }
    }

    fun checkAndCacheRecognitionSupport(langCode: String) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU && isOnDeviceAvailable()) {
            mainHandler.post {
                try {
                    val recognizer = createOnDeviceSpeechRecognizerSafely() ?: return@post
                    val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE, langCode)
                    }
                    recognizer.checkRecognitionSupport(
                        intent,
                        ContextCompat.getMainExecutor(context),
                        object : RecognitionSupportCallback {
                            override fun onSupportResult(recognitionSupport: RecognitionSupport) {
                                val installed = recognitionSupport.installedOnDeviceLanguages.any {
                                    it.equals(langCode, ignoreCase = true) || it.startsWith("hi", ignoreCase = true)
                                }
                                cachedLanguageSupport[langCode] = installed
                                try { recognizer.destroy() } catch (_: Exception) {}
                            }

                            override fun onError(errorCode: Int) {
                                cachedLanguageSupport[langCode] = false
                                try { recognizer.destroy() } catch (_: Exception) {}
                            }
                        }
                    )
                } catch (_: Exception) {
                    cachedLanguageSupport[langCode] = false
                }
            }
        }
    }

    fun startListening(
        language: VoiceLanguage,
        mode: RecognizerMode = RecognizerMode.AUTOMATIC
    ) {
        val sessionToken = activeSessionToken.incrementAndGet()
        clearWatchdogs()
        isCurrentlyListening = false
        isCurrentlyFinalizing = false
        listener.onConnecting()

        // Connection watchdog: if recognizer does not become ready within 5 seconds, fail gracefully
        val connWatchdog = Runnable {
            if (activeSessionToken.get() == sessionToken && !isCurrentlyListening && !isCurrentlyFinalizing) {
                destroyRecognizerInternal()
                lastErrorCode = -4
                lastErrorMessage = "Speech recognition connection timed out. Tap mic to retry."
                listener.onError(-4, lastErrorMessage!!, isActionable = true)
            }
        }
        connectionWatchdog = connWatchdog
        mainHandler.postDelayed(connWatchdog, 5000L)

        mainHandler.post {
            try {
                destroyRecognizerInternal()

                if (!SpeechRecognizer.isRecognitionAvailable(context)) {
                    clearWatchdogs()
                    lastErrorCode = -1
                    lastErrorMessage = "Speech recognition is not available on this device."
                    listener.onError(-1, lastErrorMessage!!, isActionable = true)
                    return@post
                }

                val langCode = when (language) {
                    VoiceLanguage.Hindi, VoiceLanguage.Hinglish -> "hi-IN"
                    VoiceLanguage.English -> "en-IN"
                }

                // Language-aware recognizer selection strategy
                speechRecognizer = when (mode) {
                    RecognizerMode.ONLINE_ONLY -> {
                        activeRecognizerType = "System Speech Recognizer (Online)"
                        SpeechRecognizer.createSpeechRecognizer(context)
                    }
                    RecognizerMode.ON_DEVICE_ONLY -> {
                        val onDeviceRecognizer = createOnDeviceSpeechRecognizerSafely()
                        if (onDeviceRecognizer != null) {
                            activeRecognizerType = "On-Device Speech Recognizer (Offline)"
                            onDeviceRecognizer
                        } else {
                            clearWatchdogs()
                            lastErrorCode = -3
                            lastErrorMessage = "On-device speech recognition is not supported on this phone. Please switch to Online or Automatic mode."
                            listener.onError(-3, lastErrorMessage!!, isActionable = true)
                            return@post
                        }
                    }
                    RecognizerMode.AUTOMATIC -> {
                        val isInstalled = cachedLanguageSupport[langCode] == true
                        val onDeviceRecognizer = if (isInstalled || language == VoiceLanguage.English) {
                            createOnDeviceSpeechRecognizerSafely()
                        } else {
                            null
                        }

                        if (onDeviceRecognizer != null && isInstalled) {
                            activeRecognizerType = "On-Device Speech Recognizer (Model Verified)"
                            onDeviceRecognizer
                        } else if (onDeviceRecognizer != null && language == VoiceLanguage.English) {
                            activeRecognizerType = "On-Device Speech Recognizer (English)"
                            onDeviceRecognizer
                        } else {
                            activeRecognizerType = "System Speech Recognizer (Automatic Online)"
                            checkAndCacheRecognitionSupport(langCode)
                            SpeechRecognizer.createSpeechRecognizer(context)
                        }
                    }
                }

                speechRecognizer?.setRecognitionListener(createListener(sessionToken, language, mode))

                val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE, langCode)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, langCode)

                    if (language == VoiceLanguage.Hinglish) {
                        putExtra(
                            "android.speech.extra.EXTRA_ADDITIONAL_LANGUAGES",
                            arrayOf("en-IN", "hi-IN", "en-US")
                        )
                    }

                    putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 2000L)
                    putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1500L)
                }

                speechRecognizer?.startListening(intent)
            } catch (e: Exception) {
                clearWatchdogs()
                isCurrentlyListening = false
                isCurrentlyFinalizing = false
                lastErrorCode = -2
                lastErrorMessage = "Could not initialize speech recognizer: ${e.message}"
                listener.onError(-2, lastErrorMessage!!, isActionable = true)
            }
        }
    }

    fun stopListening() {
        mainHandler.post {
            if (isCurrentlyListening) {
                isCurrentlyListening = false
                isCurrentlyFinalizing = true
                clearWatchdogs()
                listener.onFinalizing()
                try {
                    speechRecognizer?.stopListening()
                } catch (_: Exception) {}

                // Bounded fallback in case native recognizer never calls onResults or onError after stopListening
                val token = activeSessionToken.get()
                val fallbackRunnable = Runnable {
                    if (activeSessionToken.get() == token && isCurrentlyFinalizing) {
                        isCurrentlyFinalizing = false
                        destroyRecognizerInternal()
                        listener.onFinalizationTimeout("")
                    }
                }
                finalizationWatchdog = fallbackRunnable
                mainHandler.postDelayed(fallbackRunnable, 2500L)
            }
        }
    }

    fun cancel() {
        mainHandler.post {
            isCurrentlyListening = false
            isCurrentlyFinalizing = false
            activeSessionToken.incrementAndGet()
            clearWatchdogs()
            try {
                speechRecognizer?.cancel()
            } catch (_: Exception) {}
            destroyRecognizerInternal()
            listener.onCancelled()
        }
    }

    fun destroy() {
        mainHandler.post {
            activeSessionToken.incrementAndGet()
            clearWatchdogs()
            destroyRecognizerInternal()
        }
    }

    private fun destroyRecognizerInternal() {
        isCurrentlyListening = false
        isCurrentlyFinalizing = false
        try {
            speechRecognizer?.destroy()
        } catch (_: Exception) {}
        speechRecognizer = null
    }

    fun triggerModelDownload(language: VoiceLanguage) {
        val langCode = when (language) {
            VoiceLanguage.Hindi, VoiceLanguage.Hinglish -> "hi-IN"
            VoiceLanguage.English -> "en-IN"
        }
        mainHandler.post {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE) {
                try {
                    val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                        putExtra(RecognizerIntent.EXTRA_LANGUAGE, langCode)
                    }
                    speechRecognizer?.triggerModelDownload(intent)
                } catch (_: Exception) {}
            }
        }
    }

    fun createOpenVoiceSettingsIntent(): Intent {
        val voiceSettingsIntent = Intent("android.settings.VOICE_INPUT_SETTINGS")
        return if (voiceSettingsIntent.resolveActivity(context.packageManager) != null) {
            voiceSettingsIntent
        } else {
            Intent(Settings.ACTION_SETTINGS)
        }
    }

    private fun createListener(
        sessionToken: Long,
        language: VoiceLanguage,
        mode: RecognizerMode
    ): RecognitionListener {
        return object : RecognitionListener {
            private var isSessionFinalized = false
            private var latestPartialText = ""

            override fun onReadyForSpeech(params: Bundle?) {
                if (activeSessionToken.get() != sessionToken) return
                connectionWatchdog?.let { mainHandler.removeCallbacks(it) }
                connectionWatchdog = null

                isCurrentlyListening = true
                isCurrentlyFinalizing = false
                reconnectAttemptCount = 0
                listener.onReadyForSpeech()

                // Silence watchdog: if no speech within 12 seconds, trigger stop
                val silenceRunnable = Runnable {
                    if (activeSessionToken.get() == sessionToken && isCurrentlyListening && !isSessionFinalized) {
                        stopListening()
                    }
                }
                silenceWatchdog = silenceRunnable
                mainHandler.postDelayed(silenceRunnable, 12000L)
            }

            override fun onBeginningOfSpeech() {
                if (activeSessionToken.get() != sessionToken) return
                silenceWatchdog?.let { mainHandler.removeCallbacks(it) }
                silenceWatchdog = null
                listener.onBeginningOfSpeech()
            }

            override fun onRmsChanged(rmsdB: Float) {
                if (activeSessionToken.get() != sessionToken) return
                val normalized = ((rmsdB + 2f) / 12f).coerceIn(0.0f, 1.0f)
                listener.onRmsChanged(normalized)
            }

            override fun onBufferReceived(buffer: ByteArray?) {}

            override fun onEndOfSpeech() {
                if (activeSessionToken.get() != sessionToken || isSessionFinalized) return
                silenceWatchdog?.let { mainHandler.removeCallbacks(it) }
                silenceWatchdog = null

                isCurrentlyListening = false
                isCurrentlyFinalizing = true
                listener.onEndOfSpeech()
                listener.onFinalizing()

                // BUG 1 FIX: Bounded finalization timeout (3.5 seconds)
                // If the recognition service fails to deliver onResults or onError after speech end,
                // this watchdog prevents remaining stuck in Listening/Finalizing.
                finalizationWatchdog?.let { mainHandler.removeCallbacks(it) }
                val fWatchdog = Runnable {
                    if (activeSessionToken.get() == sessionToken && !isSessionFinalized) {
                        isSessionFinalized = true
                        isCurrentlyFinalizing = false
                        destroyRecognizerInternal()
                        if (latestPartialText.isNotBlank()) {
                            listener.onResults(latestPartialText)
                        } else {
                            listener.onFinalizationTimeout("")
                        }
                    }
                }
                finalizationWatchdog = fWatchdog
                mainHandler.postDelayed(fWatchdog, 3500L)
            }

            override fun onError(error: Int) {
                if (activeSessionToken.get() != sessionToken || isSessionFinalized) return
                isSessionFinalized = true
                isCurrentlyListening = false
                isCurrentlyFinalizing = false
                clearWatchdogs()
                lastErrorCode = error

                // If error is timeout or no match, but we have partial captured text, deliver it!
                if ((error == SpeechRecognizer.ERROR_NO_MATCH || error == SpeechRecognizer.ERROR_SPEECH_TIMEOUT) &&
                    latestPartialText.isNotBlank()
                ) {
                    destroyRecognizerInternal()
                    listener.onResults(latestPartialText)
                    return
                }

                // Error 13 (ERROR_LANGUAGE_UNAVAILABLE) & Error 12 (ERROR_LANGUAGE_NOT_SUPPORTED) Handling
                if (error == 13 || error == 12 || error == SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE) {
                    val msgHindi = "हिंदी वॉइस मॉडल उपलब्ध नहीं है। इसे डाउनलोड करें या ऑनलाइन वॉइस रिकग्निशन चुनें।"
                    val msgEng = "Hindi voice model is not installed on this device. Please download it or switch to Online speech recognition."
                    lastErrorMessage = "$msgHindi\n($msgEng)"
                    val langCode = when (language) {
                        VoiceLanguage.Hindi, VoiceLanguage.Hinglish -> "hi-IN"
                        VoiceLanguage.English -> "en-IN"
                    }
                    cachedLanguageSupport[langCode] = false
                    destroyRecognizerInternal()
                    listener.onLanguageUnavailable(language, msgHindi, msgEng)
                    return
                }

                // Error 11 (ERROR_SERVER_DISCONNECTED) Handling with bounded backoff retry
                if (error == 11 || error == SpeechRecognizer.ERROR_SERVER_DISCONNECTED) {
                    destroyRecognizerInternal()
                    if (reconnectAttemptCount < 1) {
                        reconnectAttemptCount++
                        lastErrorMessage = "Speech service disconnected. Reconnecting with standard recognizer..."
                        listener.onConnecting()
                        mainHandler.postDelayed({
                            if (activeSessionToken.get() == sessionToken) {
                                startListening(language, RecognizerMode.ONLINE_ONLY)
                            }
                        }, 350L)
                        return
                    } else {
                        val msgHindi = "वॉइस सर्विस डिस्कनेक्ट हो गई। (Speech service disconnected. Tap to retry.)"
                        lastErrorMessage = msgHindi
                        listener.onError(error, msgHindi, isActionable = true)
                        return
                    }
                }

                // Standard SpeechRecognizer error codes
                val message = when (error) {
                    SpeechRecognizer.ERROR_NO_MATCH -> "No speech recognized. Please speak clearly into the microphone."
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Listening timed out due to silence."
                    SpeechRecognizer.ERROR_AUDIO -> "Audio recording error. Check that microphone is available."
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission required for Voice Mode."
                    SpeechRecognizer.ERROR_NETWORK -> "Network connection required for online speech recognition."
                    SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Speech recognition network timeout."
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Speech recognizer is busy. Please tap mic again."
                    SpeechRecognizer.ERROR_CLIENT -> "Speech recognizer client error."
                    else -> "Speech recognition error ($error)."
                }
                lastErrorMessage = message
                destroyRecognizerInternal()
                listener.onError(error, message, isActionable = (error == SpeechRecognizer.ERROR_NETWORK || error == SpeechRecognizer.ERROR_RECOGNIZER_BUSY))
            }

            override fun onResults(results: Bundle?) {
                if (activeSessionToken.get() != sessionToken || isSessionFinalized) return
                isSessionFinalized = true
                isCurrentlyListening = false
                isCurrentlyFinalizing = false
                clearWatchdogs()

                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                var text = matches?.firstOrNull()?.trim().orEmpty()
                if (text.isBlank() && latestPartialText.isNotBlank()) {
                    text = latestPartialText
                }

                destroyRecognizerInternal()
                listener.onResults(text)
            }

            override fun onPartialResults(partialResults: Bundle?) {
                if (activeSessionToken.get() != sessionToken || isSessionFinalized) return
                silenceWatchdog?.let { mainHandler.removeCallbacks(it) }
                silenceWatchdog = null

                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull()?.trim().orEmpty()
                if (text.isNotBlank()) {
                    latestPartialText = text
                    listener.onPartialResults(text)
                }
            }

            override fun onEvent(eventType: Int, params: Bundle?) {}
        }
    }

    fun getDiagnostics(
        selectedLanguage: VoiceLanguage,
        recognizerMode: RecognizerMode,
        waveformState: WaveformState,
        hasRecordAudioPermission: Boolean
    ): VoiceDiagnosticsData {
        val langCode = when (selectedLanguage) {
            VoiceLanguage.Hindi, VoiceLanguage.Hinglish -> "hi-IN"
            VoiceLanguage.English -> "en-IN"
        }
        return VoiceDiagnosticsData(
            androidVersion = "Android ${Build.VERSION.RELEASE} (API ${Build.VERSION.SDK_INT})",
            apiLevel = Build.VERSION.SDK_INT,
            deviceModel = "${Build.MANUFACTURER} ${Build.MODEL}",
            isSystemRecognitionAvailable = isRecognitionAvailable(),
            isOnDeviceRecognitionAvailable = isOnDeviceAvailable(),
            selectedRecognizerMode = recognizerMode,
            activeRecognizerType = activeRecognizerType,
            selectedLanguage = selectedLanguage,
            languageCode = langCode,
            isInstalledOnDevice = cachedLanguageSupport[langCode],
            isSupportedOnDevice = if (isOnDeviceAvailable()) true else false,
            isSupportedOnline = true,
            hasRecordAudioPermission = hasRecordAudioPermission,
            waveformState = waveformState,
            lastErrorCode = lastErrorCode,
            lastErrorMessage = lastErrorMessage,
            reconnectAttemptCount = reconnectAttemptCount
        )
    }
}
