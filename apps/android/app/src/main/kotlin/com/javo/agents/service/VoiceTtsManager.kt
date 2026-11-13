package com.javo.agents.service

import android.content.Context
import android.os.Bundle
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
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

    private var tts: TextToSpeech? = null
    private var isInitialized = false

    private val _isSpeaking = MutableStateFlow(false)
    val isSpeaking: StateFlow<Boolean> = _isSpeaking.asStateFlow()

    private val callbacks = ConcurrentHashMap<String, () -> Unit>()

    init {
        tts = TextToSpeech(context.applicationContext, this)
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
                    utteranceId?.let { id ->
                        callbacks.remove(id)?.invoke()
                    }
                }

                @Deprecated("Deprecated in Java")
                override fun onError(utteranceId: String?) {
                    _isSpeaking.value = false
                    utteranceId?.let { id ->
                        callbacks.remove(id)?.invoke()
                    }
                }

                override fun onError(utteranceId: String?, errorCode: Int) {
                    _isSpeaking.value = false
                    utteranceId?.let { id ->
                        callbacks.remove(id)?.invoke()
                    }
                }
            })
        } else {
            isInitialized = false
        }
    }

    fun isReady(): Boolean = isInitialized && tts != null

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

    fun speak(
        text: String,
        language: VoiceLanguage = VoiceLanguage.English,
        onComplete: (() -> Unit)? = null
    ) {
        if (text.isBlank()) {
            onComplete?.invoke()
            return
        }

        if (!isInitialized || tts == null) {
            onComplete?.invoke()
            return
        }

        val targetLocale = getLocaleForLanguage(language)
        val langResult = tts?.setLanguage(targetLocale)
        if (langResult == TextToSpeech.LANG_MISSING_DATA || langResult == TextToSpeech.LANG_NOT_SUPPORTED) {
            // Fallback to default or English
            tts?.setLanguage(Locale.US)
        }

        val utteranceId = UUID.randomUUID().toString()
        if (onComplete != null) {
            callbacks[utteranceId] = onComplete
        }

        val params = Bundle().apply {
            putString(TextToSpeech.Engine.KEY_PARAM_UTTERANCE_ID, utteranceId)
        }

        _isSpeaking.value = true
        tts?.speak(text, TextToSpeech.QUEUE_FLUSH, params, utteranceId)
    }

    fun stop() {
        try {
            tts?.stop()
        } catch (_: Exception) {}
        _isSpeaking.value = false
        callbacks.clear()
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
