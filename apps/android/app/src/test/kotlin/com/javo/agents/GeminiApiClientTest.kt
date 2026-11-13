package com.javo.agents

import com.javo.agents.data.remote.GeminiApiClient
import com.javo.agents.data.remote.GeminiAuthException
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class GeminiApiClientTest {

    @Test
    fun resolveModel_defaultsToGemini25Flash_whenBlankOrNull() {
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel(null))
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel(""))
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel("   "))
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel("unknown-model-xyz"))
    }

    @Test
    fun resolveModel_migratesRetiredModelsToGemini25Flash() {
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel("gemini-1.5-flash"))
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel("gemini-1.5-pro"))
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel("gemini-1.0-pro"))
    }

    @Test
    fun resolveModel_preservesCurrentSupportedModels() {
        assertEquals("gemini-2.5-flash", GeminiApiClient.resolveModel("gemini-2.5-flash"))
        assertEquals("gemini-2.5-flash-lite", GeminiApiClient.resolveModel("gemini-2.5-flash-lite"))
        assertEquals("gemini-2.0-flash", GeminiApiClient.resolveModel("gemini-2.0-flash"))
    }

    @Test
    fun sanitizeError_redactsApiKeyAndQueryParams() {
        val testApiKey = "AIzaSySecretApiKey12345"
        val rawError = "HTTP 400 at https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=$testApiKey with key $testApiKey invalid"

        val sanitized = GeminiApiClient.sanitizeError(rawError, testApiKey)

        assertFalse("Raw API key must not appear in sanitized error", sanitized.contains(testApiKey))
        assertTrue("API key should be replaced with placeholder", sanitized.contains("[REDACTED_API_KEY]"))
        assertTrue("Query string key param should be masked", sanitized.contains("key=[REDACTED]"))
    }

    @Test
    fun testConnection_failsFast_whenApiKeyIsBlank() = runTest {
        val client = GeminiApiClient()
        val result = client.testConnection("")

        assertTrue(result.isFailure)
        assertTrue(result.exceptionOrNull() is GeminiAuthException)
    }

    @Test
    fun generateResponse_failsFast_whenApiKeyOrPromptIsBlank() = runTest {
        val client = GeminiApiClient()

        val blankKeyRes = client.generateResponse(prompt = "Hello", apiKey = "")
        assertTrue(blankKeyRes.isFailure)
        assertTrue(blankKeyRes.exceptionOrNull() is GeminiAuthException)

        val blankPromptRes = client.generateResponse(prompt = "  ", apiKey = "dummy-key")
        assertTrue(blankPromptRes.isFailure)
        assertTrue(blankPromptRes.exceptionOrNull() is IllegalArgumentException)
    }
}
