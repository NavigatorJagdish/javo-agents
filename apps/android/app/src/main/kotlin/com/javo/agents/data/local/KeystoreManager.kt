package com.javo.agents.data.local

import android.content.Context
import android.content.SharedPreferences
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
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
        private const val KEY_DARK_THEME = "pref_dark_theme"
        private const val KEY_ONBOARDING_COMPLETE = "pref_onboarding_complete"
        private const val KEY_AUTO_RUN = "pref_auto_run"
        private const val KEY_VOICE_MODE = "pref_voice_mode"
        private const val KEY_SAMPLE_DATA_MIGRATED = "sample_migration_v1_done"
        private const val KEY_DEMO_MODE = "pref_demo_mode_enabled"
    }
}
