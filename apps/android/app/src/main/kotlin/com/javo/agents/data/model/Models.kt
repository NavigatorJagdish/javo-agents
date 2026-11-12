package com.javo.agents.data.model

import kotlinx.serialization.Serializable
import java.net.URI

enum class WaveformState(val label: String) {
    Idle("Idle"),
    Listening("Listening"),
    Thinking("Thinking"),
    Executing("Executing"),
    Finished("Finished")
}

enum class VoiceLanguage(val displayName: String, val code: String) {
    English("English", "en"),
    Hindi("Hindi", "hi"),
    Hinglish("Hinglish", "hi-en")
}

enum class AgentCategory(val label: String) {
    Growth("Growth"),
    Content("Content"),
    Operations("Operations"),
    Security("Security"),
    System("System")
}

data class AgentInfo(
    val number: Int,
    val slug: String,
    val displayName: String,
    val category: AgentCategory,
    val description: String,
    val capabilities: List<String>,
    val requiredPermissions: List<String>,
    val isEnabled: Boolean = true,
    val status: String = "Standby",
    val isTemplate: Boolean = false
)

object AgentRoster {
    val allAgents: List<AgentInfo> = listOf(
        AgentInfo(1, "growth_scientist", "Growth Scientist", AgentCategory.Growth, "Analyzes growth metrics, suggests content strategies, and designs A/B experiments.", listOf("Metric analysis", "A/B design", "Growth forecasts"), listOf("analytics:read", "goals:read"), true, "Active"),
        AgentInfo(2, "content_factory", "Content Factory", AgentCategory.Content, "Generates multi-platform drafts, hooks, and captions using your brand voice.", listOf("Caption drafting", "Hook writing", "Asset prep"), listOf("content:write", "ai:invoke"), true, "Active"),
        AgentInfo(3, "smart_memory", "Smart Memory", AgentCategory.System, "Stores and retrieves contextual preferences and past campaign learnings locally.", listOf("Context recall", "Preference memory"), listOf("memory:read", "memory:write"), true, "Active"),
        AgentInfo(4, "self_upgrading_engineer", "Self-Upgrading Engineer", AgentCategory.System, "Monitors runtime health and suggests local configuration optimizations.", listOf("Health checks", "Config tuning"), listOf("system:read"), false, "Standby"),
        AgentInfo(5, "telegram_agent", "Telegram Agent", AgentCategory.Operations, "Handles Telegram bot commands, approval alerts, and status digests.", listOf("Bot commands", "Approval alerts"), listOf("telegram:send"), true, "Active"),
        AgentInfo(6, "brand_manager", "Brand Manager", AgentCategory.Content, "Enforces brand tone, vocabulary guardrails, and visual identity rules.", listOf("Tone audit", "Brand compliance"), listOf("brand:read", "content:read"), true, "Standby"),
        AgentInfo(7, "voice_agent", "Voice Agent", AgentCategory.Operations, "Processes English, Hindi, and Hinglish voice commands into structured actions.", listOf("Speech intent", "Multilingual reply"), listOf("voice:process", "tasks:create"), true, "Active"),
        AgentInfo(8, "api_integration", "API Integration", AgentCategory.System, "Manages external social API sync, rate limits, and token refresh hooks.", listOf("API sync", "Rate limiting"), listOf("accounts:read"), true, "Standby"),
        AgentInfo(9, "content_publisher", "Content Publisher", AgentCategory.Content, "Publishes approved posts to connected Facebook, Instagram, and YouTube channels.", listOf("Scheduled publish", "Post verification"), listOf("content:publish", "approval:required"), true, "Standby"),
        AgentInfo(10, "community_manager", "Community Manager", AgentCategory.Growth, "Monitors audience comments, summarizes sentiment, and drafts replies.", listOf("Sentiment scan", "Reply drafting"), listOf("comments:read", "approval:required"), true, "Standby"),
        AgentInfo(11, "account_guardian", "Account Guardian", AgentCategory.Security, "Monitors connected social accounts for unusual auth changes or policy flags.", listOf("Anomaly detection", "Token expiry alert"), listOf("accounts:read", "security:alert"), true, "Active"),
        AgentInfo(12, "resource_optimizer", "Resource Optimizer", AgentCategory.System, "Balances CPU/RAM limits on 8GB+ Windows hosts when running local AI models.", listOf("RAM guard", "Queue scheduling"), listOf("system:read"), true, "Active"),
        AgentInfo(13, "quality_inspector", "Quality Inspector", AgentCategory.Content, "Checks drafts for formatting issues, broken links, and compliance rules.", listOf("Pre-publish QA", "Link checks"), listOf("content:read"), true, "Standby"),
        AgentInfo(14, "niche_radar", "Niche Radar", AgentCategory.Growth, "Tracks niche topics and seasonal publishing opportunities.", listOf("Topic radar", "Trend digest"), listOf("analytics:read"), false, "Standby"),
        AgentInfo(15, "approval_manager", "Approval Manager", AgentCategory.Operations, "Routes sensitive actions into Supervised Autopilot approval queues.", listOf("Risk scoring", "Approval routing"), listOf("approvals:manage"), true, "Active"),
        AgentInfo(16, "budget_guardian", "Budget Guardian", AgentCategory.Operations, "Enforces strict zero-cost guardrails and API token ceilings.", listOf("Zero-cost cap", "Usage alerts"), listOf("billing:guard"), true, "Active"),
        AgentInfo(17, "content_recycler", "Content Recycler", AgentCategory.Content, "Identifies evergreen posts and adapts them into fresh formats.", listOf("Evergreen remix", "Format adapt"), listOf("content:read", "content:write"), false, "Standby"),
        AgentInfo(18, "brand_studio", "Brand Studio", AgentCategory.Content, "Prepares consistent thumbnail overlays, color palettes, and layout templates.", listOf("Template specs", "Palette checks"), listOf("brand:read"), false, "Standby"),
        AgentInfo(19, "weekly_analyst", "Weekly Analyst", AgentCategory.Growth, "Compiles weekly performance summaries distinguishing real vs unavailable data.", listOf("Weekly digest", "KPI delta"), listOf("analytics:read"), true, "Standby"),
        AgentInfo(20, "recovery_agent", "Recovery Agent", AgentCategory.System, "Reconciles missed jobs and recovers interrupted tasks after device sleep.", listOf("Job recovery", "Retry backoff"), listOf("tasks:write"), true, "Active"),
        AgentInfo(21, "plugin_trust", "Plugin Trust", AgentCategory.Security, "Audits local skill manifests and enforces sandbox permission boundaries.", listOf("Manifest audit", "Trust scoring"), listOf("security:read"), true, "Standby"),
        AgentInfo(22, "security_guardian", "Security Guardian", AgentCategory.Security, "Watches audit logs, device pairing sessions, and triggers emergency stops.", listOf("Audit watch", "Emergency stop"), listOf("security:write"), true, "Active"),
        AgentInfo(23, "goal_persistence", "Goal Persistence", AgentCategory.Growth, "Tracks long-term milestones and updates goal completion percentages.", listOf("Milestone sync", "Goal reminders"), listOf("goals:write"), true, "Standby"),
        AgentInfo(24, "workflow_automation", "Workflow Automation", AgentCategory.Operations, "Executes deterministic node graphs with condition and approval gates.", listOf("DAG runner", "Condition eval"), listOf("workflows:run"), true, "Active"),
        AgentInfo(25, "reporting_agent", "Reporting Agent", AgentCategory.Growth, "Generates structured CSV/Markdown reports for local export.", listOf("Export reports", "Audit summary"), listOf("reports:export"), true, "Standby"),
        AgentInfo(26, "release_agent", "Release Agent", AgentCategory.System, "Tracks local runtime versions and verifies SHA-256 release checksums.", listOf("Version check", "Checksum verify"), listOf("system:read"), false, "Standby"),
        AgentInfo(27, "device_sync_agent", "Device Sync Agent", AgentCategory.Operations, "Coordinates encrypted LAN/HTTPS state synchronization with Android clients.", listOf("Delta sync", "Offline queue"), listOf("devices:sync"), true, "Active"),
        AgentInfo(28, "ux_assistant", "UX Assistant", AgentCategory.System, "Provides accessibility checks and onboarding guidance across surfaces.", listOf("Onboarding help", "Accessibility check"), listOf("ui:assist"), false, "Standby"),
        AgentInfo(29, "compliance_agent", "Compliance Agent", AgentCategory.Security, "Validates platform disclosure, privacy, and supervised autopilot boundaries.", listOf("Policy check", "Disclosure audit"), listOf("compliance:read"), true, "Active")
    )

    val templates: List<AgentInfo> = listOf(
        AgentInfo(101, "tpl_hinglish_reels", "Hinglish Reels Growth Pack", AgentCategory.Content, "Pre-configured Content Factory + Voice + Quality Inspector template for short-form reels.", listOf("Hinglish hooks", "Approval gate"), listOf("content:write", "approval:required"), isEnabled = false, status = "Template", isTemplate = true),
        AgentInfo(102, "tpl_daily_digest", "Founder Morning Digest", AgentCategory.Operations, "Combines Weekly Analyst + Telegram + Device Sync for 8 AM briefings.", listOf("Daily summary", "Mobile push"), listOf("analytics:read", "devices:sync"), isEnabled = false, status = "Template", isTemplate = true),
        AgentInfo(103, "tpl_safe_autopilot", "Supervised Autopilot Guard", AgentCategory.Security, "Pairs Approval Manager + Budget Guardian + Compliance Agent with strict zero-cost caps.", listOf("Human sign-off", "Zero-cost lock"), listOf("approvals:manage", "billing:guard"), isEnabled = false, status = "Template", isTemplate = true)
    )
}

data class VoiceMessage(
    val id: String,
    val isUser: Boolean,
    val text: String,
    val language: VoiceLanguage,
    val timestampLabel: String,
    val actionHint: String? = null
)

data class WorkflowInfo(
    val id: String,
    val name: String,
    val triggerType: String,
    val nodeCount: Int,
    val requiresApproval: Boolean,
    val isActive: Boolean,
    val lastRunSummary: String,
    val nodes: List<String>
)

enum class DataProvenance(val badge: String) {
    REAL_RUNTIME("Live Runtime"),
    LOCAL_DEVICE("Local Device"),
    DEMO_UNAVAILABLE("Sample / Unavailable")
}

data class AnalyticsMetric(
    val id: String,
    val label: String,
    val value: String,
    val delta: String,
    val provenance: DataProvenance,
    val note: String
)

enum class ProviderType(val label: String) {
    LOCAL_PC_OLLAMA("Local AI via Paired Windows PC (Ollama)"),
    GEMINI_DIRECT("Google Gemini Developer API (Keystore)")
}

data class AIProviderConfig(
    val activeProvider: ProviderType = ProviderType.LOCAL_PC_OLLAMA,
    val localModelName: String = "qwen2.5:3b-instruct-q4_K_M",
    val geminiModelName: String = "gemini-2.5-flash",
    val hasGeminiKeyStored: Boolean = false,
    val zeroCostGuardEnabled: Boolean = true,
    val privacyFirewallStrict: Boolean = true
)

data class DiagnosticCheck(
    val name: String,
    val status: String,
    val detail: String,
    val passed: Boolean
)

@Serializable
data class PairingTokenPayload(
    val hostUrl: String,
    val pairingCode: String,
    val deviceToken: String,
    val expiresAtEpochSec: Long,
    val fingerprintSha256: String = ""
)

sealed class PairingValidationResult {
    data class Valid(val payload: PairingTokenPayload) : PairingValidationResult()
    data class Invalid(val reason: String) : PairingValidationResult()
}

object PairingTokenValidator {
    private val codeRegex = Regex("^[A-Za-z0-9\\-_]{6,64}$")

    fun validate(
        rawPayload: PairingTokenPayload,
        nowEpochSec: Long = System.currentTimeMillis() / 1000L
    ): PairingValidationResult {
        val trimmedUrl = rawPayload.hostUrl.trim().trimEnd('/')
        if (trimmedUrl.isBlank()) {
            return PairingValidationResult.Invalid("Host URL is required.")
        }

        val uri = try {
            URI(trimmedUrl)
        } catch (_: Exception) {
            return PairingValidationResult.Invalid("Malformed host URL.")
        }

        val scheme = uri.scheme?.lowercase()
        val host = uri.host?.lowercase() ?: ""
        if (scheme != "https" && scheme != "http") {
            return PairingValidationResult.Invalid("URL scheme must be https or local http.")
        }

        val isLoopbackOrLan = host == "localhost" ||
            host == "127.0.0.1" ||
            host == "10.0.2.2" ||
            host.startsWith("192.168.") ||
            host.startsWith("10.") ||
            host.endsWith(".local")

        if (scheme == "http" && !isLoopbackOrLan) {
            return PairingValidationResult.Invalid("Plain HTTP is only allowed for local LAN or loopback hosts; use HTTPS remotely.")
        }

        if (!codeRegex.matches(rawPayload.pairingCode.trim())) {
            return PairingValidationResult.Invalid("Pairing code must be 6-64 alphanumeric characters.")
        }

        if (rawPayload.deviceToken.trim().length < 16) {
            return PairingValidationResult.Invalid("Short-lived pairing token must be at least 16 characters.")
        }

        if (rawPayload.expiresAtEpochSec <= nowEpochSec) {
            return PairingValidationResult.Invalid("Pairing token has expired. Generate a fresh QR or code on Windows.")
        }

        return PairingValidationResult.Valid(
            rawPayload.copy(
                hostUrl = trimmedUrl,
                pairingCode = rawPayload.pairingCode.trim(),
                deviceToken = rawPayload.deviceToken.trim()
            )
        )
    }

    fun parseManualOrQr(rawText: String, nowEpochSec: Long = System.currentTimeMillis() / 1000L): PairingValidationResult {
        val cleaned = rawText.trim()
        if (cleaned.startsWith("{")) {
            return try {
                val decoded = kotlinx.serialization.json.Json {
                    ignoreUnknownKeys = true
                }.decodeFromString<PairingTokenPayload>(cleaned)
                validate(decoded, nowEpochSec)
            } catch (e: Exception) {
                PairingValidationResult.Invalid("Invalid pairing JSON: ${e.message ?: "parse error"}")
            }
        }
        // Support pipe-separated compact code: https://192.168.1.50:8000|PAIR1234|tok_abc123...|1799999999
        val parts = cleaned.split("|")
        if (parts.size >= 4) {
            val exp = parts[3].toLongOrNull()
                ?: return PairingValidationResult.Invalid("Invalid expiry timestamp in pairing token.")
            return validate(
                PairingTokenPayload(
                    hostUrl = parts[0],
                    pairingCode = parts[1],
                    deviceToken = parts[2],
                    expiresAtEpochSec = exp,
                    fingerprintSha256 = parts.getOrNull(4).orEmpty()
                ),
                nowEpochSec
            )
        }
        return PairingValidationResult.Invalid("Unsupported pairing format. Scan QR or enter host URL & code.")
    }
}
