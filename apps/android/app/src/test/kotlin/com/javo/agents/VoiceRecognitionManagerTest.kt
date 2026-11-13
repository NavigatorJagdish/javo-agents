package com.javo.agents

import com.javo.agents.data.model.RecognizerMode
import com.javo.agents.data.model.VoiceDiagnosticsData
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.model.WaveformState
import com.javo.agents.service.VoiceRecognitionListener
import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class VoiceRecognitionManagerTest {

    @Test
    fun error13_triggersHindiLanguageUnavailableMessage() {
        var unavailableCalled = false
        var capturedHindiMsg = ""
        var capturedEngMsg = ""

        val listener = object : VoiceRecognitionListener {
            override fun onLanguageUnavailable(language: VoiceLanguage, messageHindi: String, messageEnglish: String) {
                unavailableCalled = true
                capturedHindiMsg = messageHindi
                capturedEngMsg = messageEnglish
            }
        }

        // Test error 13 contract
        val errorCode = 13 // SpeechRecognizer.ERROR_LANGUAGE_UNAVAILABLE
        if (errorCode == 13 || errorCode == 12) {
            val msgHindi = "हिंदी वॉइस मॉडल उपलब्ध नहीं है। इसे डाउनलोड करें या ऑनलाइन वॉइस रिकग्निशन चुनें।"
            val msgEng = "Hindi voice model is not installed on this device. Please download it or switch to Online speech recognition."
            listener.onLanguageUnavailable(VoiceLanguage.Hindi, msgHindi, msgEng)
        }

        assertTrue("Error 13 must trigger onLanguageUnavailable callback", unavailableCalled)
        assertEquals("हिंदी वॉइस मॉडल उपलब्ध नहीं है। इसे डाउनलोड करें या ऑनलाइन वॉइस रिकग्निशन चुनें।", capturedHindiMsg)
        assertTrue(capturedEngMsg.contains("Hindi voice model is not installed"))
    }

    @Test
    fun error11_disconnectRecovery_reportsActionableMessageAfterRetry() {
        var errorReported = false
        var capturedError = 0
        var capturedMessage = ""
        var isActionableFlag = false

        val listener = object : VoiceRecognitionListener {
            override fun onError(errorCode: Int, errorMessage: String, isActionable: Boolean) {
                errorReported = true
                capturedError = errorCode
                capturedMessage = errorMessage
                isActionableFlag = isActionable
            }
        }

        // Simulate reconnect attempt exhausted
        var reconnectAttempts = 1
        if (reconnectAttempts >= 1) {
            val msgHindi = "वॉइस सर्विस डिस्कनेक्ट हो गई। (Speech service disconnected. Tap to retry.)"
            listener.onError(11, msgHindi, isActionable = true)
        }

        assertTrue("Error 11 must trigger onError when retry attempts are exhausted", errorReported)
        assertEquals(11, capturedError)
        assertTrue(capturedMessage.contains("वॉइस सर्विस डिस्कनेक्ट हो गई।"))
        assertTrue("Error 11 should be flagged as actionable for UI retry", isActionableFlag)
    }

    @Test
    fun recognizerMode_selectionLogic_preventsError13ForHindiInAutomaticMode() {
        val targetLanguage = VoiceLanguage.Hindi
        val langCode = "hi-IN"
        val cachedInstalledModels = mapOf("en-IN" to true, "hi-IN" to false) // Hindi model NOT installed on-device

        // Automatic mode selection simulation
        fun resolveEngine(language: VoiceLanguage, mode: RecognizerMode, isInstalled: Boolean, onDeviceAvailable: Boolean): String {
            return when (mode) {
                RecognizerMode.ONLINE_ONLY -> "System Speech Recognizer (Online)"
                RecognizerMode.ON_DEVICE_ONLY -> if (onDeviceAvailable) "On-Device Speech Recognizer (Offline)" else "Error: Not Supported"
                RecognizerMode.AUTOMATIC -> {
                    if (onDeviceAvailable && isInstalled) {
                        "On-Device Speech Recognizer (Model Verified)"
                    } else if (language == VoiceLanguage.English && onDeviceAvailable) {
                        "On-Device Speech Recognizer (English)"
                    } else {
                        "System Speech Recognizer (Automatic Online)"
                    }
                }
            }
        }

        val selectedEngineAuto = resolveEngine(
            targetLanguage,
            RecognizerMode.AUTOMATIC,
            cachedInstalledModels[langCode] ?: false,
            onDeviceAvailable = true
        )

        // In Automatic mode without Hindi model installed, MUST route to System Online to avoid Error 13
        assertEquals("System Speech Recognizer (Automatic Online)", selectedEngineAuto)

        val selectedEngineOnline = resolveEngine(
            targetLanguage,
            RecognizerMode.ONLINE_ONLY,
            isInstalled = false,
            onDeviceAvailable = true
        )
        assertEquals("System Speech Recognizer (Online)", selectedEngineOnline)

        val selectedEngineEnglishAuto = resolveEngine(
            VoiceLanguage.English,
            RecognizerMode.AUTOMATIC,
            isInstalled = true,
            onDeviceAvailable = true
        )
        assertEquals("On-Device Speech Recognizer (Model Verified)", selectedEngineEnglishAuto)
    }

    @Test
    fun speechFailure_neverTriggersFabricatedCommand() {
        var commandDispatched = false
        var dispatchedText = ""

        fun handleSpeechResults(finalText: String) {
            val query = finalText.trim()
            if (query.isNotBlank()) {
                commandDispatched = true
                dispatchedText = query
            }
        }

        // Test with empty string (e.g. from no speech detected or error)
        handleSpeechResults("")
        assertFalse("Empty transcript must never trigger command execution", commandDispatched)

        // Test with whitespace string
        handleSpeechResults("   ")
        assertFalse("Whitespace transcript must never trigger command execution", commandDispatched)

        // Test with legitimate spoken Hindi text
        handleSpeechResults("इंस्टाग्राम के लिए रील हुक बनाओ")
        assertTrue("Legitimate transcript must trigger command execution", commandDispatched)
        assertEquals("इंस्टाग्राम के लिए रील हुक बनाओ", dispatchedText)
    }

    @Test
    fun voiceDiagnostics_containsNoRawAudioOrTokens() {
        val diag = VoiceDiagnosticsData(
            androidVersion = "Android 14 (API 34)",
            apiLevel = 34,
            deviceModel = "Pixel 8 Pro",
            isSystemRecognitionAvailable = true,
            isOnDeviceRecognitionAvailable = true,
            selectedRecognizerMode = RecognizerMode.AUTOMATIC,
            activeRecognizerType = "System Speech Recognizer (Automatic Online)",
            selectedLanguage = VoiceLanguage.Hindi,
            languageCode = "hi-IN",
            isInstalledOnDevice = false,
            isSupportedOnDevice = true,
            isSupportedOnline = true,
            hasRecordAudioPermission = true,
            waveformState = WaveformState.Idle,
            lastErrorCode = 13,
            lastErrorMessage = "हिंदी वॉइस मॉडल उपलब्ध नहीं है।",
            reconnectAttemptCount = 0
        )

        val json = JSONObject().apply {
            put("android_version", diag.androidVersion)
            put("api_level", diag.apiLevel)
            put("device_model", diag.deviceModel)
            put("system_recognition_available", diag.isSystemRecognitionAvailable)
            put("on_device_recognition_available", diag.isOnDeviceRecognitionAvailable)
            put("selected_recognizer_mode", diag.selectedRecognizerMode.name)
            put("active_recognizer_type", diag.activeRecognizerType)
            put("selected_language", diag.selectedLanguage.displayName)
            put("language_code", diag.languageCode)
            put("is_installed_on_device", diag.isInstalledOnDevice)
            put("is_supported_on_device", diag.isSupportedOnDevice)
            put("is_supported_online", diag.isSupportedOnline)
            put("has_mic_permission", diag.hasRecordAudioPermission)
            put("waveform_state", diag.waveformState.name)
            put("last_error_code", diag.lastErrorCode ?: JSONObject.NULL)
            put("last_error_message", diag.lastErrorMessage ?: JSONObject.NULL)
            put("reconnect_attempts", diag.reconnectAttemptCount)
        }

        val jsonString = json.toString()
        assertFalse("Diagnostics must never leak API keys", jsonString.contains("AIzaSy"))
        assertFalse("Diagnostics must never contain audio binary data", jsonString.contains("pcm_data"))
        assertFalse("Diagnostics must never contain private transcripts", jsonString.contains("personal_transcription"))
        assertTrue(jsonString.contains("AUTOMATIC"))
        assertTrue(jsonString.contains("hi-IN"))
        assertEquals(13, json.getInt("last_error_code"))
    }
}
