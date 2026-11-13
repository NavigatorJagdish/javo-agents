package com.javo.agents.service

import android.content.Context
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import com.javo.agents.data.model.VoiceLanguage

interface VoiceRecognitionListener {
    fun onReadyForSpeech() {}
    fun onBeginningOfSpeech() {}
    fun onRmsChanged(amplitude: Float) {}
    fun onPartialResults(partialText: String) {}
    fun onResults(finalText: String) {}
    fun onError(errorCode: Int, errorMessage: String) {}
    fun onEndOfSpeech() {}
}

class VoiceRecognitionManager(
    private val context: Context,
    private val listener: VoiceRecognitionListener
) {
    private var speechRecognizer: SpeechRecognizer? = null
    private val mainHandler = Handler(Looper.getMainLooper())
    private var isCurrentlyListening = false

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

    fun startListening(language: VoiceLanguage) {
        mainHandler.post {
            try {
                destroyRecognizer()

                if (!SpeechRecognizer.isRecognitionAvailable(context)) {
                    listener.onError(-1, "Speech recognition is not available on this device.")
                    return@post
                }

                speechRecognizer = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S &&
                    SpeechRecognizer.isOnDeviceRecognitionAvailable(context)
                ) {
                    SpeechRecognizer.createOnDeviceSpeechRecognizer(context)
                } else {
                    SpeechRecognizer.createSpeechRecognizer(context)
                }

                speechRecognizer?.setRecognitionListener(createListener())

                val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
                    putExtra(
                        RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                        RecognizerIntent.LANGUAGE_MODEL_FREE_FORM
                    )
                    putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
                    putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 3)

                    // Target language code
                    val langCode = when (language) {
                        VoiceLanguage.Hindi -> "hi-IN"
                        VoiceLanguage.Hinglish -> "hi-IN"
                        VoiceLanguage.English -> "en-IN"
                    }
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE, langCode)
                    putExtra(RecognizerIntent.EXTRA_LANGUAGE_PREFERENCE, langCode)
                    if (language == VoiceLanguage.Hinglish) {
                        putExtra(
                            RecognizerIntent.EXTRA_ADDITIONAL_LANGUAGES,
                            arrayOf("en-IN", "hi-IN", "en-US")
                        )
                    }

                    putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_COMPLETE_SILENCE_LENGTH_MILLIS, 1800L)
                    putExtra(RecognizerIntent.EXTRA_SPEECH_INPUT_POSSIBLY_COMPLETE_SILENCE_LENGTH_MILLIS, 1200L)
                }

                isCurrentlyListening = true
                speechRecognizer?.startListening(intent)
            } catch (e: Exception) {
                isCurrentlyListening = false
                listener.onError(-2, "Could not start speech recognizer: ${e.message}")
            }
        }
    }

    fun stopListening() {
        mainHandler.post {
            if (isCurrentlyListening) {
                try {
                    speechRecognizer?.stopListening()
                } catch (_: Exception) {}
            }
        }
    }

    fun cancel() {
        mainHandler.post {
            isCurrentlyListening = false
            try {
                speechRecognizer?.cancel()
            } catch (_: Exception) {}
        }
    }

    fun destroy() {
        mainHandler.post {
            destroyRecognizer()
        }
    }

    private fun destroyRecognizer() {
        isCurrentlyListening = false
        try {
            speechRecognizer?.destroy()
        } catch (_: Exception) {}
        speechRecognizer = null
    }

    private fun createListener(): RecognitionListener {
        return object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                listener.onReadyForSpeech()
            }

            override fun onBeginningOfSpeech() {
                listener.onBeginningOfSpeech()
            }

            override fun onRmsChanged(rmsdB: Float) {
                // rmsdB ranges typically between -2 dB and 10 dB
                val normalized = ((rmsdB + 2f) / 12f).coerceIn(0.0f, 1.0f)
                listener.onRmsChanged(normalized)
            }

            override fun onBufferReceived(buffer: ByteArray?) {}

            override fun onEndOfSpeech() {
                isCurrentlyListening = false
                listener.onEndOfSpeech()
            }

            override fun onError(error: Int) {
                isCurrentlyListening = false
                val message = when (error) {
                    SpeechRecognizer.ERROR_NO_MATCH -> "No speech recognized. Speak clearly into the microphone."
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "Listening timed out due to silence."
                    SpeechRecognizer.ERROR_AUDIO -> "Audio recording error."
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Microphone permission required."
                    SpeechRecognizer.ERROR_NETWORK -> "Network required for online speech recognition."
                    SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Speech recognition network timeout."
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Speech recognizer is busy. Retrying..."
                    SpeechRecognizer.ERROR_CLIENT -> "Speech recognizer client error."
                    else -> "Speech recognizer error ($error)."
                }
                listener.onError(error, message)
            }

            override fun onResults(results: Bundle?) {
                isCurrentlyListening = false
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull()?.trim().orEmpty()
                listener.onResults(text)
            }

            override fun onPartialResults(partialResults: Bundle?) {
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                val text = matches?.firstOrNull()?.trim().orEmpty()
                if (text.isNotBlank()) {
                    listener.onPartialResults(text)
                }
            }

            override fun onEvent(eventType: Int, params: Bundle?) {}
        }
    }
}
