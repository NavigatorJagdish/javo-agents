package com.javo.agents.data.local

import android.content.Context
import android.content.SharedPreferences
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.javo.agents.data.model.CustomAiEndpointConfig
import com.javo.agents.data.model.OperatingMode
import com.javo.agents.data.model.ProviderType
import com.javo.agents.data.model.RecognizerMode
import com.javo.agents.data.model.VoiceConversationMode
import com.javo.agents.data.model.VoiceMessage
import kotlinx.serialization.encodeToString
import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import java.nio.charset.StandardCharsets
import java.security.KeyStore
import java.security.SecureRandom
import java.util.Base64
import java.util.UUID
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

interface SecretKeyProvider {
    fun getOrCreateAesKey(): SecretKey
    fun isHardwareBacked(): Boolean
}

class AndroidKeystoreKeyProvider(
    private val keyAlias: String = DEFAULT_KEY_ALIAS
) : SecretKeyProvider {

    override fun getOrCreateAesKey(): SecretKey {
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        val existing = keyStore.getKey(keyAlias, null) as? SecretKey
        if (existing != null) return existing

        val keyGenerator = KeyGenerator.getInstance(
            KeyProperties.KEY_ALGORITHM_AES,
            ANDROID_KEYSTORE
        )
        val spec = KeyGenParameterSpec.Builder(
            keyAlias,
            KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        )
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setKeySize(256)
            .setRandomizedEncryptionRequired(true)
            .build()

        keyGenerator.init(spec)
        return keyGenerator.generateKey()
    }

    override fun isHardwareBacked(): Boolean {
        return try {
            val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
            keyStore.containsAlias(keyAlias)
        } catch (_: Exception) {
            false
        }
    }

    companion object {
        private const val ANDROID_KEYSTORE = "AndroidKeyStore"
        private const val DEFAULT_KEY_ALIAS = "javo_agents_aes256_gcm"
    }
}

class AesGcmCipher(
    private val keyProvider: SecretKeyProvider
) {
    fun encryptToBase64(plaintext: String): String {
        val secretKey = keyProvider.getOrCreateAesKey()
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.ENCRYPT_MODE, secretKey)
        val iv = cipher.iv
        val ciphertext = cipher.doFinal(plaintext.toByteArray(StandardCharsets.UTF_8))
        val combined = ByteArray(1 + iv.size + ciphertext.size)
        combined[0] = iv.size.toByte()
        System.arraycopy(iv, 0, combined, 1, iv.size)
        System.arraycopy(ciphertext, 0, combined, 1 + iv.size, ciphertext.size)
        return Base64.getEncoder().encodeToString(combined)
    }

    fun decryptFromBase64(encoded: String): String {
        val combined = Base64.getDecoder().decode(encoded)
        require(combined.size > 13) { "Corrupted ciphertext payload" }
        val ivLength = combined[0].toInt() and 0xFF
        require(ivLength in 12..16 && combined.size > 1 + ivLength) { "Invalid GCM IV length" }
        val iv = combined.copyOfRange(1, 1 + ivLength)
        val ciphertext = combined.copyOfRange(1 + ivLength, combined.size)

        val secretKey = keyProvider.getOrCreateAesKey()
        val cipher = Cipher.getInstance(TRANSFORMATION)
        cipher.init(Cipher.DECRYPT_MODE, secretKey, GCMParameterSpec(GCM_TAG_BITS, iv))
        val plainBytes = cipher.doFinal(ciphertext)
        return String(plainBytes, StandardCharsets.UTF_8)
    }

    companion object {
        private const val TRANSFORMATION = "AES/GCM/NoPadding"
        private const val GCM_TAG_BITS = 128

        fun generateRandomToken(byteCount: Int = 32): String {
            val bytes = ByteArray(byteCount)
            SecureRandom().nextBytes(bytes)
            return Base64.getUrlEncoder().withoutPadding().encodeToString(bytes)
        }
    }
}

interface SecureSecretStore {
    fun putSecret(key: String, value: String)
    fun getSecret(key: String): String?
    fun removeSecret(key: String)
    fun clearAll()
}

class EncryptedPrefsSecretStore(context: Context) : SecureSecretStore {
    private val prefs: SharedPreferences by lazy {
        val masterKey = MasterKey.Builder(context.applicationContext)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        EncryptedSharedPreferences.create(
            context.applicationContext,
            PREFS_FILE,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }

    override fun putSecret(key: String, value: String) {
        prefs.edit().putString(key, value).apply()
    }

    override fun getSecret(key: String): String? = prefs.getString(key, null)

    override fun removeSecret(key: String) {
        prefs.edit().remove(key).apply()
    }

    override fun clearAll() {
        prefs.edit().clear().apply()
    }

    companion object {
        private const val PREFS_FILE = "javo_secure_prefs"
    }
}

data class KeystoreHealthStatus(
    val keystoreActive: Boolean,
    val encryptionScheme: String,
    val hasPairingToken: Boolean,
    val hasGeminiKey: Boolean,
    val deviceId: String
)

class KeystoreManager(
    private val secretStore: SecureSecretStore,
    private val keyProvider: SecretKeyProvider
) {
    private val aesCipher = AesGcmCipher(keyProvider)

    constructor(context: Context) : this(
        secretStore = EncryptedPrefsSecretStore(context),
        keyProvider = AndroidKeystoreKeyProvider()
    )

    fun getOrCreateDeviceId(): String {
        val existing = secretStore.getSecret(KEY_DEVICE_ID)
        if (!existing.isNullOrBlank()) return existing
        val created = "android-" + UUID.randomUUID().toString()
        secretStore.putSecret(KEY_DEVICE_ID, created)
        return created
    }

    fun savePairingSession(hostUrl: String, pairingToken: String, fingerprintSha256: String = "") {
        val encryptedToken = aesCipher.encryptToBase64(pairingToken)
        secretStore.putSecret(KEY_PAIRED_HOST, hostUrl.trim().trimEnd('/'))
        secretStore.putSecret(KEY_PAIRING_TOKEN_ENC, encryptedToken)
        secretStore.putSecret(KEY_HOST_FINGERPRINT, fingerprintSha256)
        secretStore.putSecret(KEY_PAIRED_AT_MS, System.currentTimeMillis().toString())
    }

    fun getPairedHostUrl(): String? = secretStore.getSecret(KEY_PAIRED_HOST)

    fun getPairingToken(): String? {
        val encrypted = secretStore.getSecret(KEY_PAIRING_TOKEN_ENC) ?: return null
        return try {
            aesCipher.decryptFromBase64(encrypted)
        } catch (_: Exception) {
            null
        }
    }

    fun getHostFingerprint(): String = secretStore.getSecret(KEY_HOST_FINGERPRINT).orEmpty()

    fun isPaired(): Boolean = !getPairedHostUrl().isNullOrBlank() && !getPairingToken().isNullOrBlank()

    fun revokePairing() {
        secretStore.removeSecret(KEY_PAIRED_HOST)
        secretStore.removeSecret(KEY_PAIRING_TOKEN_ENC)
        secretStore.removeSecret(KEY_HOST_FINGERPRINT)
        secretStore.removeSecret(KEY_PAIRED_AT_MS)
    }

    fun saveGeminiApiKey(apiKey: String) {
        val trimmed = apiKey.trim()
        if (trimmed.isBlank()) {
            secretStore.removeSecret(KEY_GEMINI_API_ENC)
            return
        }
        secretStore.putSecret(KEY_GEMINI_API_ENC, aesCipher.encryptToBase64(trimmed))
    }

    fun getGeminiApiKey(): String? {
        val encrypted = secretStore.getSecret(KEY_GEMINI_API_ENC) ?: return null
        return try {
            aesCipher.decryptFromBase64(encrypted)
        } catch (_: Exception) {
            null
        }
    }

    fun hasGeminiApiKey(): Boolean = !getGeminiApiKey().isNullOrBlank()

    fun saveGeminiModel(model: String) {
        val trimmed = model.trim()
        if (trimmed.isNotBlank()) {
            secretStore.putSecret(KEY_GEMINI_MODEL, trimmed)
        }
    }

    fun getGeminiModel(): String {
        return secretStore.getSecret(KEY_GEMINI_MODEL) ?: "gemini-2.5-flash"
    }

    /**
     * The provider choice is an explicit user preference and must survive app restart.
     * Presence of a Gemini key is not permission to ignore a selected custom provider.
     */
    /**
     * Personal speech transcripts are stored only after explicit opt-in.
     * No audio recordings are stored. This history remains on-device in the
     * existing Keystore-backed encrypted secret store and can be deleted.
     */
    fun isVoiceHistoryEnabled(): Boolean =
        secretStore.getSecret(KEY_VOICE_HISTORY_ENABLED)?.toBooleanStrictOrNull() ?: false

    fun setVoiceHistoryEnabled(enabled: Boolean) {
        secretStore.putSecret(KEY_VOICE_HISTORY_ENABLED, enabled.toString())
        if (!enabled) clearVoiceConversation()
    }

    fun saveVoiceConversation(messages: List<VoiceMessage>) {
        if (!isVoiceHistoryEnabled()) return
        val bounded = messages.takeLast(36).map {
            it.copy(text = it.text.take(2400), actionHint = it.actionHint?.take(120))
        }
        val serialized = Json.encodeToString(bounded)
        secretStore.putSecret(KEY_VOICE_CONVERSATION_ENC, aesCipher.encryptToBase64(serialized))
    }

    fun getVoiceConversation(): List<VoiceMessage> {
        if (!isVoiceHistoryEnabled()) return emptyList()
        val encrypted = secretStore.getSecret(KEY_VOICE_CONVERSATION_ENC) ?: return emptyList()
        return try {
            Json.decodeFromString<List<VoiceMessage>>(aesCipher.decryptFromBase64(encrypted))
                .takeLast(36)
        } catch (_: Exception) {
            emptyList()
        }
    }

    fun clearVoiceConversation() {
        secretStore.removeSecret(KEY_VOICE_CONVERSATION_ENC)
    }

    fun saveSelectedAiProvider(provider: ProviderType) {
        secretStore.putSecret(KEY_SELECTED_AI_PROVIDER, provider.name)
    }

    fun getSelectedAiProvider(): ProviderType {
        val stored = secretStore.getSecret(KEY_SELECTED_AI_PROVIDER)
        val saved = ProviderType.entries.firstOrNull { it.name == stored }
        if (saved != null) return saved

        // Migration for installations created before provider preference persistence.
        // Standalone users should never default to a Windows-only backend.
        return if (getOperatingMode() == OperatingMode.WINDOWS_ENHANCED && isPaired()) {
            ProviderType.LOCAL_PC_OLLAMA
        } else if (hasGeminiApiKey()) {
            ProviderType.GEMINI_DIRECT
        } else if (getCustomAiEndpoint().isEnabled && getCustomAiEndpoint().endpointUrl.isNotBlank()) {
            ProviderType.CUSTOM_ENDPOINT
        } else {
            ProviderType.GEMINI_DIRECT
        }
    }

    fun saveDarkThemeEnabled(enabled: Boolean) {
        secretStore.putSecret(KEY_DARK_THEME, enabled.toString())
    }

    fun isDarkThemeEnabled(): Boolean = secretStore.getSecret(KEY_DARK_THEME)?.toBooleanStrictOrNull() ?: true

    fun saveOnboardingComplete(complete: Boolean) {
        secretStore.putSecret(KEY_ONBOARDING_COMPLETE, complete.toString())
    }

    fun isOnboardingComplete(): Boolean = secretStore.getSecret(KEY_ONBOARDING_COMPLETE)?.toBooleanStrictOrNull() ?: false

    fun saveAutoRunEnabled(enabled: Boolean) {
        secretStore.putSecret(KEY_AUTO_RUN, enabled.toString())
    }

    fun isAutoRunEnabled(): Boolean = secretStore.getSecret(KEY_AUTO_RUN)?.toBooleanStrictOrNull() ?: false

    fun saveVoiceModeEnabled(enabled: Boolean) {
        secretStore.putSecret(KEY_VOICE_MODE, enabled.toString())
    }

    fun isVoiceModeEnabled(): Boolean = secretStore.getSecret(KEY_VOICE_MODE)?.toBooleanStrictOrNull() ?: true

    fun saveRecognizerMode(mode: RecognizerMode) {
        secretStore.putSecret(KEY_RECOGNIZER_MODE, mode.name)
    }

    fun getRecognizerMode(): RecognizerMode {
        val stored = secretStore.getSecret(KEY_RECOGNIZER_MODE) ?: return RecognizerMode.AUTOMATIC
        return try {
            RecognizerMode.valueOf(stored)
        } catch (_: Exception) {
            RecognizerMode.AUTOMATIC
        }
    }

    fun saveOperatingMode(mode: OperatingMode) {
        secretStore.putSecret(KEY_OPERATING_MODE, mode.name)
    }

    fun getOperatingMode(): OperatingMode {
        val stored = secretStore.getSecret(KEY_OPERATING_MODE)
        if (stored != null) {
            return try {
                OperatingMode.valueOf(stored)
            } catch (_: Exception) {
                if (isPaired()) OperatingMode.WINDOWS_ENHANCED else OperatingMode.ANDROID_STANDALONE
            }
        }
        return if (isPaired()) OperatingMode.WINDOWS_ENHANCED else OperatingMode.ANDROID_STANDALONE
    }

    fun saveTtsEnabled(enabled: Boolean) {
        secretStore.putSecret(KEY_TTS_ENABLED, enabled.toString())
    }

    fun isTtsEnabled(): Boolean = secretStore.getSecret(KEY_TTS_ENABLED)?.toBooleanStrictOrNull() ?: true

    fun saveVoiceConversationMode(mode: VoiceConversationMode) {
        secretStore.putSecret(KEY_VOICE_CONVERSATION_MODE, mode.name)
    }

    fun getVoiceConversationMode(): VoiceConversationMode {
        val raw = secretStore.getSecret(KEY_VOICE_CONVERSATION_MODE) ?: return VoiceConversationMode.TAP_TO_TALK
        return try {
            VoiceConversationMode.valueOf(raw)
        } catch (_: Exception) {
            VoiceConversationMode.TAP_TO_TALK
        }
    }

    fun saveTtsSpeechRate(rate: Float) {
        secretStore.putSecret(KEY_TTS_SPEECH_RATE, rate.toString())
    }

    fun getTtsSpeechRate(): Float {
        return secretStore.getSecret(KEY_TTS_SPEECH_RATE)?.toFloatOrNull() ?: 1.0f
    }

    fun saveCustomAiEndpoint(url: String, apiKey: String, model: String, enabled: Boolean) {
        secretStore.putSecret(KEY_CUSTOM_AI_URL, url.trim())
        if (apiKey.isNotBlank()) {
            secretStore.putSecret(KEY_CUSTOM_AI_KEY_ENC, aesCipher.encryptToBase64(apiKey.trim()))
        } else {
            secretStore.removeSecret(KEY_CUSTOM_AI_KEY_ENC)
        }
        secretStore.putSecret(KEY_CUSTOM_AI_MODEL, model.trim())
        secretStore.putSecret(KEY_CUSTOM_AI_ENABLED, enabled.toString())
    }

    fun getCustomAiEndpoint(): CustomAiEndpointConfig {
        val url = secretStore.getSecret(KEY_CUSTOM_AI_URL).orEmpty()
        val encKey = secretStore.getSecret(KEY_CUSTOM_AI_KEY_ENC)
        val apiKey = if (encKey != null) {
            try { aesCipher.decryptFromBase64(encKey) } catch (_: Exception) { "" }
        } else ""
        val model = secretStore.getSecret(KEY_CUSTOM_AI_MODEL) ?: "gpt-4o-mini"
        val enabled = secretStore.getSecret(KEY_CUSTOM_AI_ENABLED)?.toBooleanStrictOrNull() ?: false
        return CustomAiEndpointConfig(url, apiKey, model, enabled)
    }

    fun saveSocialToken(platformId: String, accessToken: String, refreshToken: String?, expiresAtEpochSec: Long) {
        val encAccess = aesCipher.encryptToBase64(accessToken)
        secretStore.putSecret("social_${platformId}_token", encAccess)
        if (refreshToken != null) {
            secretStore.putSecret("social_${platformId}_refresh", aesCipher.encryptToBase64(refreshToken))
        }
        secretStore.putSecret("social_${platformId}_expires", expiresAtEpochSec.toString())
    }

    fun getSocialToken(platformId: String): String? {
        val enc = secretStore.getSecret("social_${platformId}_token") ?: return null
        return try {
            aesCipher.decryptFromBase64(enc)
        } catch (_: Exception) {
            null
        }
    }

    fun removeSocialToken(platformId: String) {
        secretStore.removeSecret("social_${platformId}_token")
        secretStore.removeSecret("social_${platformId}_refresh")
        secretStore.removeSecret("social_${platformId}_expires")
    }

    fun isSampleDataMigrated(): Boolean = secretStore.getSecret(KEY_SAMPLE_DATA_MIGRATED)?.toBooleanStrictOrNull() ?: false

    fun markSampleDataMigrated() {
        secretStore.putSecret(KEY_SAMPLE_DATA_MIGRATED, "true")
    }

    fun isDemoModeEnabled(): Boolean = secretStore.getSecret(KEY_DEMO_MODE)?.toBooleanStrictOrNull() ?: false

    fun setDemoModeEnabled(enabled: Boolean) {
        secretStore.putSecret(KEY_DEMO_MODE, enabled.toString())
    }

    fun getHealthStatus(): KeystoreHealthStatus {
        val active = try {
            keyProvider.getOrCreateAesKey()
            true
        } catch (_: Exception) {
            false
        }
        return KeystoreHealthStatus(
            keystoreActive = active,
            encryptionScheme = "AES-256-GCM (Android Keystore + EncryptedSharedPreferences)",
            hasPairingToken = isPaired(),
            hasGeminiKey = hasGeminiApiKey(),
            deviceId = getOrCreateDeviceId()
        )
    }

    fun wipeAllSecrets() {
        secretStore.clearAll()
    }

    companion object {
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_PAIRED_HOST = "paired_host_url"
        private const val KEY_PAIRING_TOKEN_ENC = "pairing_token_enc"
        private const val KEY_HOST_FINGERPRINT = "host_fingerprint"
        private const val KEY_PAIRED_AT_MS = "paired_at_ms"
        private const val KEY_GEMINI_API_ENC = "gemini_api_key_enc"
        private const val KEY_GEMINI_MODEL = "gemini_model_name"
        private const val KEY_SELECTED_AI_PROVIDER = "pref_selected_ai_provider"
        private const val KEY_VOICE_HISTORY_ENABLED = "pref_voice_history_opt_in"
        private const val KEY_VOICE_CONVERSATION_ENC = "voice_history_encrypted_v1"
        private const val KEY_DARK_THEME = "pref_dark_theme"
        private const val KEY_ONBOARDING_COMPLETE = "pref_onboarding_complete"
        private const val KEY_AUTO_RUN = "pref_auto_run"
        private const val KEY_VOICE_MODE = "pref_voice_mode"
        private const val KEY_RECOGNIZER_MODE = "pref_recognizer_mode"
        private const val KEY_SAMPLE_DATA_MIGRATED = "sample_migration_v1_done"
        private const val KEY_DEMO_MODE = "pref_demo_mode_enabled"
        private const val KEY_OPERATING_MODE = "pref_operating_mode"
        private const val KEY_TTS_ENABLED = "pref_tts_enabled"
        private const val KEY_VOICE_CONVERSATION_MODE = "pref_voice_conv_mode"
        private const val KEY_TTS_SPEECH_RATE = "pref_tts_speech_rate"
        private const val KEY_CUSTOM_AI_URL = "custom_ai_url"
        private const val KEY_CUSTOM_AI_KEY_ENC = "custom_ai_key_enc"
        private const val KEY_CUSTOM_AI_MODEL = "custom_ai_model"
        private const val KEY_CUSTOM_AI_ENABLED = "custom_ai_enabled"
    }
}
