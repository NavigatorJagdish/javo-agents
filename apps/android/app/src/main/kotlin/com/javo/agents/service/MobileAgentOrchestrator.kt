package com.javo.agents.service

import android.content.Context
import com.javo.agents.data.local.DraftDao
import com.javo.agents.data.local.DraftEntity
import com.javo.agents.data.local.KeystoreManager
import com.javo.agents.data.local.TaskDao
import com.javo.agents.data.local.TaskEntity
import com.javo.agents.data.model.AgentInfo
import com.javo.agents.data.model.AgentRoster
import com.javo.agents.data.model.CustomAiEndpointConfig
import com.javo.agents.data.model.ProviderType
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.data.remote.GeminiApiClient
import com.javo.agents.data.remote.GeminiTurn
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.util.UUID
import java.util.concurrent.TimeUnit

class MobileAgentOrchestrator(
    private val context: Context,
    private val taskDao: TaskDao,
    private val draftDao: DraftDao,
    private val keystoreManager: KeystoreManager,
    private val geminiApiClient: GeminiApiClient = GeminiApiClient(),
    private val okHttpClient: OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .build()
) {

    fun findAgent(slugOrName: String): AgentInfo? {
        val clean = slugOrName.trim().lowercase()
        return AgentRoster.allAgents.find {
            it.slug.lowercase() == clean ||
            it.displayName.lowercase() == clean ||
            it.slug.replace("_", " ").lowercase() == clean
        }
    }

    suspend fun executeTask(task: TaskEntity): Result<String> = withContext(Dispatchers.IO) {
        taskDao.updateState(task.id, "running")

        val agent = findAgent(task.assignedAgent)
        if (agent == null) {
            val err = "Unknown or unassigned agent: '${task.assignedAgent}'"
            taskDao.updateExecutionResult(task.id, "failed", null, err)
            return@withContext Result.failure(IllegalArgumentException(err))
        }

        // Capability check
        if (agent.capability.requiresWindows) {
            val err = "Agent '${agent.displayName}' requires the Windows Desktop Runtime (OS/system-level tools). Please pair with Windows Desktop in Settings → Device Pairing to run this agent."
            taskDao.updateExecutionResult(task.id, "failed", null, err)
            return@withContext Result.failure(IllegalStateException(err))
        }

        val geminiKey = keystoreManager.getGeminiApiKey().orEmpty().trim()
        val customEndpoint = keystoreManager.getCustomAiEndpoint()

        val selectedProvider = keystoreManager.getSelectedAiProvider()
        val providerReady = when (selectedProvider) {
            ProviderType.GEMINI_DIRECT -> geminiKey.isNotBlank()
            ProviderType.CUSTOM_ENDPOINT -> customEndpoint.isEnabled && customEndpoint.endpointUrl.isNotBlank()
            ProviderType.LOCAL_PC_OLLAMA -> false // Desktop tools belong to the Windows runtime.
        }
        if (!providerReady) {
            val err = "Selected AI provider '${selectedProvider.label}' is unavailable for Android task execution. Select a configured phone provider in Settings → AI Providers."
            taskDao.updateExecutionResult(task.id, "failed", null, err)
            return@withContext Result.failure(IllegalStateException(err))
        }

        val systemInstruction = buildAgentSystemPrompt(agent)
        val userPrompt = if (task.description.isNotBlank()) {
            "Task: ${task.title}\nDetails: ${task.description}"
        } else {
            "Task: ${task.title}"
        }

        val executionResult: Result<String> = when (selectedProvider) {
            ProviderType.GEMINI_DIRECT -> geminiApiClient.generateResponse(
                prompt = userPrompt,
                apiKey = geminiKey,
                model = keystoreManager.getGeminiModel(),
                systemInstruction = systemInstruction
            )
            ProviderType.CUSTOM_ENDPOINT -> callCustomEndpoint(customEndpoint, userPrompt, systemInstruction)
            ProviderType.LOCAL_PC_OLLAMA -> Result.failure(
                IllegalStateException("Windows-only provider is unavailable on Android.")
            )
        }

        if (executionResult.isSuccess) {
            val output = executionResult.getOrThrow()
            taskDao.updateExecutionResult(task.id, "completed", output, null)

            // If Content Factory or Quality Inspector produced drafted content, offer or store as draft if relevant
            if (agent.slug == "content_factory" && (task.title.contains("draft", ignoreCase = true) || task.title.contains("post", ignoreCase = true))) {
                try {
                    val draft = DraftEntity(
                        id = UUID.randomUUID().toString(),
                        title = task.title,
                        body = output,
                        platform = "Instagram",
                        status = "offline_draft",
                        pendingSync = true
                    )
                    draftDao.upsert(draft)
                } catch (_: Exception) {}
            }

            Result.success(output)
        } else {
            val err = executionResult.exceptionOrNull()?.message ?: "Unknown agent execution error"
            taskDao.updateExecutionResult(task.id, "failed", null, err)
            Result.failure(executionResult.exceptionOrNull() ?: Exception(err))
        }
    }

    suspend fun generateContentDraft(
        topic: String,
        platform: String,
        language: VoiceLanguage = VoiceLanguage.English
    ): Result<DraftEntity> = withContext(Dispatchers.IO) {
        val geminiKey = keystoreManager.getGeminiApiKey().orEmpty().trim()
        val customEndpoint = keystoreManager.getCustomAiEndpoint()

        val selectedProvider = keystoreManager.getSelectedAiProvider()
        val providerReady = when (selectedProvider) {
            ProviderType.GEMINI_DIRECT -> geminiKey.isNotBlank()
            ProviderType.CUSTOM_ENDPOINT -> customEndpoint.isEnabled && customEndpoint.endpointUrl.isNotBlank()
            ProviderType.LOCAL_PC_OLLAMA -> false
        }
        if (!providerReady) {
            return@withContext Result.failure(
                IllegalStateException("Selected provider '${selectedProvider.label}' is not configured for mobile draft creation. Choose an available phone provider in Settings → AI Providers.")
            )
        }

        val langPrompt = when (language) {
            VoiceLanguage.Hindi -> "in natural Hindi (Devanagari script)"
            VoiceLanguage.Hinglish -> "in conversational Hinglish (Hindi written in Latin script with catchy English hooks)"
            VoiceLanguage.English -> "in punchy, engaging English"
        }

        val systemPrompt = "You are Content Factory, an expert social media copywriter for $platform. Write high-converting hooks, informative captions, and relevant hashtags $langPrompt. Be authentic, engaging, and clear."
        val userPrompt = "Create a ready-to-publish $platform post about: $topic\nInclude: 1) Strong opening hook, 2) Core body, 3) Call to Action (CTA), 4) 5 relevant hashtags."

        val resultText = when (selectedProvider) {
            ProviderType.GEMINI_DIRECT -> geminiApiClient.generateResponse(
                prompt = userPrompt,
                apiKey = geminiKey,
                model = keystoreManager.getGeminiModel(),
                systemInstruction = systemPrompt
            )
            ProviderType.CUSTOM_ENDPOINT -> callCustomEndpoint(customEndpoint, userPrompt, systemPrompt)
            ProviderType.LOCAL_PC_OLLAMA -> Result.failure(
                IllegalStateException("Windows-only provider is unavailable on Android.")
            )
        }

        if (resultText.isSuccess) {
            val content = resultText.getOrThrow()
            val title = if (topic.length > 40) topic.take(37) + "..." else topic
            val draft = DraftEntity(
                id = UUID.randomUUID().toString(),
                title = title,
                body = content,
                platform = platform,
                status = "offline_draft",
                tags = extractHashtags(content),
                pendingSync = true
            )
            draftDao.upsert(draft)
            Result.success(draft)
        } else {
            Result.failure(resultText.exceptionOrNull() ?: Exception("Draft generation failed"))
        }
    }

    private fun extractHashtags(text: String): String {
        val tags = Regex("#[A-Za-z0-9_]+").findAll(text).map { it.value }.toList()
        return tags.joinToString(" ")
    }

    private fun buildAgentSystemPrompt(agent: AgentInfo): String {
        val base = "You are ${agent.displayName}, an autonomous AI specialist in Javo Agents. ${agent.description}. You operate locally on the creator's device."
        return when (agent.slug) {
            "content_factory" -> "$base Create high-converting multi-platform drafts, hooks, and captions tailored for engagement."
            "growth_scientist" -> "$base Analyze growth data, suggest organic distribution strategies, and design clear A/B tests."
            "brand_manager" -> "$base Enforce brand tone, vocabulary guardrails, and message consistency."
            "quality_inspector" -> "$base Audit drafts for formatting errors, weak hooks, compliance risks, and readability."
            "weekly_analyst" -> "$base Provide honest, factual summaries of key metrics, distinguishing between measured data and unavailable tracking."
            "approval_manager" -> "$base Review proposed automated actions against risk policies and recommend approval or revision."
            else -> "$base Provide actionable, professional, and concise assistance for the assigned goal."
        }
    }

    private fun redactCustomError(raw: String?, apiKey: String): String {
        val text = raw.orEmpty()
        return if (apiKey.isBlank()) text else text.replace(apiKey.trim(), "[REDACTED_API_KEY]")
    }

    suspend fun callCustomEndpoint(
        config: CustomAiEndpointConfig,
        userPrompt: String,
        systemInstruction: String,
        history: List<GeminiTurn> = emptyList()
    ): Result<String> = withContext(Dispatchers.IO) {
        try {
            val url = config.endpointUrl.trim()
            val jsonPayload = JSONObject().apply {
                if (config.modelName.isNotBlank()) {
                    put("model", config.modelName.trim())
                }
                val messages = JSONArray().apply {
                    put(JSONObject().apply {
                        put("role", "system")
                        put("content", systemInstruction)
                    })
                    GeminiApiClient.boundedHistory(history).forEach { turn ->
                        put(JSONObject().apply {
                            put("role", if (turn.role == "model") "assistant" else "user")
                            put("content", turn.text)
                        })
                    }
                    put(JSONObject().apply {
                        put("role", "user")
                        put("content", userPrompt)
                    })
                }
                put("messages", messages)
                put("temperature", 0.7)
            }

            val requestBuilder = Request.Builder()
                .url(url)
                .post(jsonPayload.toString().toRequestBody("application/json".toMediaType()))

            if (config.apiKey.isNotBlank()) {
                requestBuilder.header("Authorization", "Bearer ${config.apiKey.trim()}")
            }

            val response = okHttpClient.newCall(requestBuilder.build()).execute()
            response.use { res ->
                if (!res.isSuccessful) {
                    val err = res.body?.string().orEmpty()
                    return@withContext Result.failure(Exception("Custom AI Endpoint error HTTP ${res.code}: ${redactCustomError(err, config.apiKey).take(120)}"))
                }
                val resBody = res.body?.string().orEmpty()
                val json = JSONObject(resBody)
                val choices = json.optJSONArray("choices")
                if (choices != null && choices.length() > 0) {
                    val msg = choices.getJSONObject(0).optJSONObject("message")
                    val content = msg?.optString("content")
                    if (!content.isNullOrBlank()) {
                        return@withContext Result.success(content.trim())
                    }
                }
                // Fallback for simple {"response": "..."} or {"text": "..."}
                val directText = json.optString("response").ifBlank { json.optString("text") }
                if (directText.isNotBlank()) {
                    return@withContext Result.success(directText.trim())
                }
                Result.failure(Exception("Could not parse AI response from custom endpoint."))
            }
        } catch (e: Exception) {
            Result.failure(Exception("Custom AI Endpoint network error: ${redactCustomError(e.message, config.apiKey).ifBlank { "Connection failed" }}"))
        }
    }
}
