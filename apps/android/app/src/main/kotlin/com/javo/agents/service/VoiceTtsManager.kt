package com.javo.agents.service

import android.content.Context
import android.media.AudioAttributes
import android.media.AudioFocusRequest
import android.media.AudioManager
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import android.speech.tts.Voice
import com.javo.agents.data.model.VoiceLanguage
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.Locale
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap

class VoiceTtsManager(
    private val context: Context
) : TextToSpeech.OnInitListener {

    private val audioManager = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager
    private val mainHandler = Handler(Looper.getMainLooper())

    private var tts: TextToSpeech? = null
    private var isInitialized = false

    private val _isSpeaking = MutableStateFlow(false)
    val isSpeaking: StateFlow<Boolean> = _isSpeaking.asStateFlow()

    private val callbacks = ConcurrentHashMap<String, () -> Unit>()
    private var speechRate: Float = 1.0f

    private var audioFocusRequest: AudioFocusRequest? = null
    private val focusChangeListener = AudioManager.OnAudioFocusChangeListener { focusChange ->
        if (focusChange == AudioManager.AUDIOFOCUS_LOSS ||
            focusChange == AudioManager.AUDIOFOCUS_LOSS_TRANSIENT
        ) {
            stop()
        }
    }

    private var pendingSpeakRequest: Triple<String, VoiceLanguage, (() -> Unit)?>? = null

    init {
        mainHandler.post {
            try {
                tts = TextToSpeech(context.applicationContext, this)
            } catch (_: Exception) {
                isInitialized = false
            }
        }
    }

    override fun onInit(status: Int) {
        if (status == TextToSpeech.SUCCESS) {
            isInitialized = true
            tts?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
                override fun onStart(utteranceId: String?) {
                    _isSpeaking.value = true
                }

                override fun onDone(utteranceId: String?) {
                    _isSpeaking.value = false
                    abandonAudioFocus()
                    utteranceId?.let { id ->
                        callbacks.remove(id)?.invoke()
                    }
                }

                @Deprecated("Deprecated in Java")
                override fun onError(utteranceId: String?) {
                    _isSpeaking.value = false
                    abandonAudioFocus()
                    utteranceId?.let { id ->
                        callbacks.remove(id)?.invoke()
                    }
                }

                override fun onError(utteranceId: String?, errorCode: Int) {
                    _isSpeaking.value = false
                    abandonAudioFocus()
                    utteranceId?.let { id ->
                        callbacks.remove(id)?.invoke()
                    }
                }
            })

            // Execute any pending speak queued before onInit
            pendingSpeakRequest?.let { (text, lang, onComplete) ->
                pendingSpeakRequest = null
                speak(text, lang, onComplete)
            }
        } else {
            isInitialized = false
            _isSpeaking.value = false
            pendingSpeakRequest?.let { (_, _, onComplete) ->
                pendingSpeakRequest = null
                onComplete?.invoke()
            }
        }
    }

    fun isReady(): Boolean = isInitialized && tts != null

    fun setSpeechRate(rate: Float) {
        speechRate = rate.coerceIn(0.6f, 1.8f)
        try {
            tts?.setSpeechRate(speechRate)
        } catch (_: Exception) {}
    }

    fun getSpeechRate(): Float = speechRate

    fun isLanguageAvailable(language: VoiceLanguage): Boolean {
        if (!isInitialized || tts == null) return false
        val locale = getLocaleForLanguage(language)
        val availability = tts?.isLanguageAvailable(locale) ?: TextToSpeech.LANG_NOT_SUPPORTED
        return availability >= TextToSpeech.LANG_AVAILABLE
    }

    private fun getLocaleForLanguage(language: VoiceLanguage): Locale {
        return when (language) {
            VoiceLanguage.Hindi -> Locale("hi", "IN")
            VoiceLanguage.Hinglish -> Locale("hi", "IN")
            VoiceLanguage.English -> Locale("en", "IN")
        }
    }

    private fun selectOptimalVoice(language: VoiceLanguage) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
            try {
                val voices = tts?.voices ?: return
                val targetLang = when (language) {
                    VoiceLanguage.Hindi, VoiceLanguage.Hinglish -> "hi"
                    VoiceLanguage.English -> "en"
                }

                val bestVoice = voices.firstOrNull { voice ->
                    voice.locale.language.equals(targetLang, ignoreCase = true) &&
                        !voice.isNetworkConnectionRequired &&
                        voice.quality >= Voice.QUALITY_NORMAL
                } ?: voices.firstOrNull { voice ->
                    voice.locale.language.equals(targetLang, ignoreCase = true)
                }

                if (bestVoice != null) {
                    tts?.voice = bestVoice
                }
            } catch (_: Exception) {}
        }
    }

    private fun requestAudioFocus(): Boolean {
        return try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                val playbackAttributes = AudioAttributes.Builder()
                    .setUsage(AudioAttributes.USAGE_ASSISTANT)
                    .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                    .build()
                audioFocusRequest = AudioFocusRequest.Builder(AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK)
                    .setAudioAttributes(playbackAttributes)
                    .setAcceptsDelayedFocusGain(false)
                    .setOnAudioFocusChangeListener(focusChangeListener)
                    .build()
                audioManager?.requestAudioFocus(audioFocusRequest!!) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
            } else {
                @Suppress("DEPRECATION")
                audioManager?.requestAudioFocus(
                    focusChangeListener,
                    AudioManager.STREAM_MUSIC,
                    AudioManager.AUDIOFOCUS_GAIN_TRANSIENT_MAY_DUCK
                ) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
            }
        } catch (_: Exception) {
            false
        }
    }

    private fun abandonAudioFocus() {
        try {
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                audioFocusRequest?.let { audioManager?.abandonAudioFocusRequest(it) }
                audioFocusRequest = null
            } else {
                @Suppress("DEPRECATION")
                audioManager?.abandonAudioFocus(focusChangeListener)
            }
        } catch (_: Exception) {}
    }

    fun speak(
        text: String,
        language: VoiceLanguage = VoiceLanguage.English,
        onComplete: (() -> Unit)? = null
    ): Boolean {
        val sanitized = text.replace(Regex("[#*_`\\[\\]()]"), "").trim()
        if (sanitized.isBlank()) {
            onComplete?.invoke()
            return false
        }

        if (!isInitialized || tts == null) {
            // Never queue audio behind a cancelled session: the caller must wait
            // for isReady() and explicitly start playback when the engine is ready.
            onComplete?.invoke()
            return false
        }

        // Request audio focus before starting speech
        requestAudioFocus()

        val targetLocale = getLocaleForLanguage(language)
        val langResult = tts?.setLanguage(targetLocale)
        if (langResult == TextToSpeech.LANG_MISSING_DATA || langResult == TextToSpeech.LANG_NOT_SUPPORTED) {
            // Fallback to US English if regional dialect pack missing
            tts?.setLanguage(Locale.US)
        }

        tts?.setSpeechRate(speechRate)
        selectOptimalVoice(language)

        val utteranceId = UUID.randomUUID().toString()
        if (onComplete != null) {
            callbacks[utteranceId] = onComplete
        }

        val params = Bundle().apply {
            putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, utteranceId)
        }

        val speakResult = tts?.speak(sanitized, TextToSpeech.QUEUE_FLUSH, params, utteranceId)
        if (speakResult != TextToSpeech.SUCCESS) {
            // Synthesis call failed; NEVER claim speaking state if engine rejected
            _isSpeaking.value = false
            abandonAudioFocus()
            callbacks.remove(utteranceId)?.invoke()
            return false
        }

        _isSpeaking.value = true
        return true
    }

    fun stop() {
        // Cancelling voice output must also discard requests that were waiting
        // for the Android engine: never start stale speech after user cancellation.
        val pending = pendingSpeakRequest
        pendingSpeakRequest = null
        pending?.third?.invoke()
        try {
            tts?.stop()
        } catch (_: Exception) {}
        _isSpeaking.value = false
        abandonAudioFocus()
        val pendingCallbacks = callbacks.values.toList()
        callbacks.clear()
        pendingCallbacks.forEach { it.invoke() }
    }

    fun shutdown() {
        stop()
        try {
            tts?.shutdown()
        } catch (_: Exception) {}
        tts = null
        isInitialized = false
    }
}
