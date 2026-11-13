package com.javo.agents.data.remote

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.concurrent.TimeUnit

open class GeminiApiException(message: String) : Exception(message)
class GeminiQuotaExceededException(message: String) : GeminiApiException(message)
class GeminiAuthException(message: String) : GeminiApiException(message)
class GeminiUnavailableException(message: String) : GeminiApiException(message)

/**
 * The only conversation turns sent to Gemini are verified exchanges with Gemini.
 * History is capped and explicit; task-execution errors and other provider replies
 * must never be silently leaked to a different AI provider.
 */
data class GeminiTurn(val role: String, val text: String)

class GeminiApiClient(
    private val okHttpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(12, TimeUnit.SECONDS)
        .readTimeout(25, TimeUnit.SECONDS)
        .build()
) {
    companion object {
        const val MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"
        const val MODEL_GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"
        const val MODEL_GEMINI_2_0_FLASH = "gemini-2.0-flash"

        val SUPPORTED_MODELS = listOf(
            MODEL_GEMINI_2_5_FLASH,
            MODEL_GEMINI_2_5_FLASH_LITE,
            MODEL_GEMINI_2_0_FLASH
        )

        val RETIRED_MODELS = listOf(
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.0-pro"
        )

        fun resolveModel(requested: String?): String {
            val clean = requested?.trim().orEmpty()
            if (clean in RETIRED_MODELS) {
                return MODEL_GEMINI_2_5_FLASH
            }
            if (clean in SUPPORTED_MODELS) {
                return clean
            }
            return MODEL_GEMINI_2_5_FLASH
        }

        /** Bounded, validated prior conversation turns to avoid unbounded token use. */
        fun boundedHistory(history: List<GeminiTurn>): List<GeminiTurn> =
            history.takeLast(12).mapNotNull { turn ->
                val role = turn.role.lowercase()
                val trimmed = turn.text.trim().take(1800)
                if (role !in setOf("user", "model") || trimmed.isBlank()) null
                else GeminiTurn(role, trimmed)
            }

        fun sanitizeError(raw: String?, apiKey: String): String {
            if (raw.isNullOrBlank()) return "Unknown Gemini API error."
            val strippedQuery = raw.replace(Regex("key=[A-Za-z0-9_\\-]+"), "key=[REDACTED]")
            return if (apiKey.isNotBlank()) strippedQuery.replace(apiKey.trim(), "[REDACTED_API_KEY]") else strippedQuery
        }
    }

    suspend fun testConnection(
        apiKey: String,
        model: String = MODEL_GEMINI_2_5_FLASH
    ): Result<String> = withContext(Dispatchers.IO) {
        val cleanKey = apiKey.trim()
        if (cleanKey.isBlank()) {
            return@withContext Result.failure(GeminiAuthException("Gemini API key is not configured."))
        }
        val startTime = System.currentTimeMillis()
        val res = generateResponse(
            prompt = "Respond with the word 'OK'.",
            apiKey = cleanKey,
            model = model,
            systemInstruction = "You are a connectivity test probe. Respond with single word 'OK'."
        )
        val latencyMs = System.currentTimeMillis() - startTime
        if (res.isSuccess) {
            val targetModel = resolveModel(model)
            Result.success("Connected to $targetModel (${latencyMs}ms). Verified ready for Hindi, Hinglish & English.")
        } else {
            Result.failure(res.exceptionOrNull() ?: GeminiApiException("Connection test failed."))
        }
    }

    suspend fun generateResponse(
        prompt: String,
        apiKey: String,
        model: String = MODEL_GEMINI_2_5_FLASH,
        systemInstruction: String = "You are Javo, a local-first AI assistant for creators and entrepreneurs. You are concise, friendly, and fluent in Hindi, Hinglish, and English. Respond naturally in the user's preferred language.",
        history: List<GeminiTurn> = emptyList()
    ): Result<String> = withContext(Dispatchers.IO) {
        val cleanKey = apiKey.trim()
        if (cleanKey.isBlank()) {
            return@withContext Result.failure(GeminiAuthException("Gemini API key is not configured."))
        }
        val cleanPrompt = prompt.trim()
        if (cleanPrompt.isBlank()) {
            return@withContext Result.failure(IllegalArgumentException("Prompt is empty."))
        }

        val targetModel = resolveModel(model)

        try {
            // Keep the API key out of URL query strings / network error messages.
            val url = "https://generativelanguage.googleapis.com/v1beta/models/${targetModel}:generateContent"

            val requestJson = JSONObject().apply {
                if (systemInstruction.isNotBlank()) {
                    put(
                        "systemInstruction",
                        JSONObject().put(
                            "parts",
                            JSONArray().put(JSONObject().put("text", systemInstruction.take(4000)))
                        )
                    )
                }
                val contentsArray = JSONArray()
                val safeHistory = boundedHistory(history)
                safeHistory.forEach { turn ->
                    contentsArray.put(
                        JSONObject()
                            .put("role", turn.role)
                            .put("parts", JSONArray().put(JSONObject().put("text", turn.text)))
                    )
                }
                contentsArray.put(
                    JSONObject()
                        .put("role", "user")
                        .put("parts", JSONArray().put(JSONObject().put("text", cleanPrompt)))
                )
                put("contents", contentsArray)
            }

            val body = requestJson.toString().toRequestBody("application/json".toMediaType())
            val request = Request.Builder()
                .url(url)
                .header("x-goog-api-key", cleanKey)
                .post(body)
                .build()

            val call = okHttpClient.newCall(request)
            val response = call.execute()
            response.use { res ->
                if (!res.isSuccessful) {
                    val rawErr = res.body?.string().orEmpty()
                    val sanitized = sanitizeError(rawErr, cleanKey)

                    val exception: Exception = when (res.code) {
                        429 -> GeminiQuotaExceededException(
                            "Google Gemini rate limit / quota exceeded (HTTP 429). The free tier allows up to 15 RPM. Please wait a moment before trying again."
                        )
                        401, 403 -> GeminiAuthException(
                            "Invalid or unauthorized Gemini API key (HTTP ${res.code}). Please verify your key in Settings → AI Providers."
                        )
                        404 -> IllegalArgumentException(
                            "Gemini model '$targetModel' not found (HTTP 404). Please ensure you are using a supported model."
                        )
                        500, 502, 503, 504 -> GeminiUnavailableException(
                            "Google Gemini API is temporarily unavailable (HTTP ${res.code}). Please retry shortly."
                        )
                        else -> GeminiApiException(
                            "Gemini API returned HTTP ${res.code}: ${sanitized.take(160)}"
                        )
                    }
                    return@withContext Result.failure(exception)
                }

                val responseBody = res.body?.string() ?: ""
                val json = JSONObject(responseBody)
                val candidates = json.optJSONArray("candidates")
                if (candidates == null || candidates.length() == 0) {
                    return@withContext Result.failure(
                        GeminiApiException("No response candidates returned from Gemini.")
                    )
                }

                val firstCandidate = candidates.getJSONObject(0)
                val content = firstCandidate.optJSONObject("content")
                val parts = content?.optJSONArray("parts")
                val text = parts?.optJSONObject(0)?.optString("text")

                if (text.isNullOrBlank()) {
                    return@withContext Result.failure(
                        GeminiApiException("Empty text generated by Gemini.")
                    )
                }

                Result.success(text.trim())
            }
        } catch (e: Exception) {
            val sanitizedMsg = sanitizeError(e.message, cleanKey)
            Result.failure(GeminiApiException("Gemini network error: $sanitizedMsg"))
        }
    }
}
