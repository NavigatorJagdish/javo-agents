package com.javo.agents

import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.model.VoiceMessage
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.Json
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class VoiceReplyTrustTest {
    @Test
    fun legacyChatMessagesNeverInheritVerifiedProviderStatus() {
        val legacy = """{"id":"m-1","isUser":false,"text":"Old message","language":"Hindi","timestampLabel":"Now","actionHint":"Google Gemini (legacy)"}"""
        val restored = Json.decodeFromString<VoiceMessage>(legacy)
        assertFalse(restored.isVerifiedAiReply)
    }

    @Test
    fun verifiedStatusSurvivesExplicitOptInSerialization() {
        val verified = VoiceMessage(
            id = "a-1",
            isUser = false,
            text = "Generated content text",
            language = VoiceLanguage.Hinglish,
            timestampLabel = "Now",
            actionHint = "Google Gemini (gemini-3.5-flash-lite)",
            isVerifiedAiReply = true
        )
        val restored = Json.decodeFromString<VoiceMessage>(Json.encodeToString(verified))
        assertTrue(restored.isVerifiedAiReply)
        assertTrue(restored.text == "Generated content text")
    }
}