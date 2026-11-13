package com.javo.agents

import com.javo.agents.data.local.AesGcmCipher
import com.javo.agents.data.local.KeystoreManager
import com.javo.agents.data.model.ProviderType
import com.javo.agents.data.model.OperatingMode
import com.javo.agents.data.local.SecretKeyProvider
import com.javo.agents.data.local.SecureSecretStore
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey

class KeystoreManagerTest {

    private class InMemoryKeyProvider : SecretKeyProvider {
        private val key: SecretKey by lazy {
            KeyGenerator.getInstance("AES").apply { init(256) }.generateKey()
        }

        override fun getOrCreateAesKey(): SecretKey = key
        override fun isHardwareBacked(): Boolean = true
    }

    private class InMemorySecretStore : SecureSecretStore {
        private val map = mutableMapOf<String, String>()
        override fun putSecret(key: String, value: String) { map[key] = value }
        override fun getSecret(key: String): String? = map[key]
        override fun removeSecret(key: String) { map.remove(key) }
        override fun clearAll() { map.clear() }
    }

    @Test
    fun aesGcmCipher_roundTripEncryptsWithUniqueIv() {
        val cipher = AesGcmCipher(InMemoryKeyProvider())
        val secret = "javo_pairing_secret_token_2026"

        val encrypted1 = cipher.encryptToBase64(secret)
        val encrypted2 = cipher.encryptToBase64(secret)

        assertNotEquals(secret, encrypted1)
        assertNotEquals("Randomized IV must produce distinct ciphertexts", encrypted1, encrypted2)
        assertEquals(secret, cipher.decryptFromBase64(encrypted1))
        assertEquals(secret, cipher.decryptFromBase64(encrypted2))
    }

    @Test
    fun keystoreManager_savesAndRevokesPairingAndGeminiKey() {
        val store = InMemorySecretStore()
        val manager = KeystoreManager(store, InMemoryKeyProvider())

        assertFalse(manager.isPaired())
        assertFalse(manager.hasGeminiApiKey())

        manager.savePairingSession("https://192.168.1.42:8000/", "tok_super_secret_123456", "sha256:abcd")
        manager.saveGeminiApiKey("AIzaSyTestKey12345")

        assertTrue(manager.isPaired())
        assertEquals("https://192.168.1.42:8000", manager.getPairedHostUrl())
        assertEquals("tok_super_secret_123456", manager.getPairingToken())
        assertTrue(manager.hasGeminiApiKey())
        assertEquals("AIzaSyTestKey12345", manager.getGeminiApiKey())

        manager.revokePairing()
        assertFalse(manager.isPaired())
        assertNull(manager.getPairingToken())
        assertTrue("Gemini key should remain until wiped", manager.hasGeminiApiKey())

        manager.wipeAllSecrets()
        assertFalse(manager.hasGeminiApiKey())
    }

    @Test
    fun keystoreManager_sampleMigrationAndDemoModeFlags() {
        val store = InMemorySecretStore()
        val manager = KeystoreManager(store, InMemoryKeyProvider())

        assertFalse(manager.isSampleDataMigrated())
        manager.markSampleDataMigrated()
        assertTrue(manager.isSampleDataMigrated())

        assertFalse(manager.isDemoModeEnabled())
        manager.setDemoModeEnabled(true)
        assertTrue(manager.isDemoModeEnabled())
        manager.setDemoModeEnabled(false)
        assertFalse(manager.isDemoModeEnabled())
    }

    @Test
    fun keystoreManager_selectedProviderDefaultsToPhoneSafeAndPersistsAcrossInstances() {
        val store = InMemorySecretStore()
        val keys = InMemoryKeyProvider()
        val manager = KeystoreManager(store, keys)

        // Clean Android installation must not silently prefer a paired Windows backend.
        assertEquals(OperatingMode.ANDROID_STANDALONE, manager.getOperatingMode())
        assertEquals(ProviderType.GEMINI_DIRECT, manager.getSelectedAiProvider())

        manager.saveCustomAiEndpoint(
            url = "https://example.org/v1/chat/completions",
            apiKey = "test-key-local-only",
            model = "test-model",
            enabled = true
        )
        manager.saveSelectedAiProvider(ProviderType.CUSTOM_ENDPOINT)

        // Simulates ViewModel/App recreation without dropping the selected preference.
        val reopened = KeystoreManager(store, keys)
        assertEquals(ProviderType.CUSTOM_ENDPOINT, reopened.getSelectedAiProvider())

        // Availability of an unrelated provider must NOT change the explicit selection.
        reopened.saveGeminiApiKey("AIzaSyTEST_LOCAL_ONLY")
        assertEquals(ProviderType.CUSTOM_ENDPOINT, reopened.getSelectedAiProvider())
    }

    @Test
    fun keystoreManager_selectedProviderSurvivesOperatingModeSwitch() {
        val manager = KeystoreManager(InMemorySecretStore(), InMemoryKeyProvider())
        manager.saveGeminiApiKey("AIzaSyTEST_LOCAL_ONLY")
        manager.saveSelectedAiProvider(ProviderType.GEMINI_DIRECT)
        manager.saveOperatingMode(OperatingMode.WINDOWS_ENHANCED)

        assertEquals(ProviderType.GEMINI_DIRECT, manager.getSelectedAiProvider())
        manager.saveOperatingMode(OperatingMode.ANDROID_STANDALONE)
        assertEquals(ProviderType.GEMINI_DIRECT, manager.getSelectedAiProvider())
    }

    @Test
    fun keystoreManager_voiceHistoryRequiresOptInAndCanBeRevoked() {
        val store = InMemorySecretStore()
        val keys = InMemoryKeyProvider()
        val manager = KeystoreManager(store, keys)
        val history = listOf(
            com.javo.agents.data.model.VoiceMessage(
                id = "u-1",
                isUser = true,
                text = "नमस्ते Javo",
                language = com.javo.agents.data.model.VoiceLanguage.Hindi,
                timestampLabel = "Now"
            ),
            com.javo.agents.data.model.VoiceMessage(
                id = "a-1",
                isUser = false,
                text = "नमस्ते, क्या मदद करूँ?",
                language = com.javo.agents.data.model.VoiceLanguage.Hindi,
                timestampLabel = "Now",
                actionHint = "Google Gemini (gemini-2.5-flash)"
            )
        )

        assertFalse(manager.isVoiceHistoryEnabled())
        manager.saveVoiceConversation(history)
        assertTrue(manager.getVoiceConversation().isEmpty())

        manager.setVoiceHistoryEnabled(true)
        manager.saveVoiceConversation(history)
        val reopened = KeystoreManager(store, keys)
        assertTrue(reopened.isVoiceHistoryEnabled())
        assertEquals(history, reopened.getVoiceConversation())

        reopened.setVoiceHistoryEnabled(false)
        assertFalse(reopened.isVoiceHistoryEnabled())
        assertTrue(reopened.getVoiceConversation().isEmpty())
        reopened.setVoiceHistoryEnabled(true)
        assertTrue("Revoking consent must delete saved chat text", reopened.getVoiceConversation().isEmpty())
    }

    @Test
    fun keystoreManager_clearVoiceHistoryDeletesDataWithoutRemovingProviderKey() {
        val manager = KeystoreManager(InMemorySecretStore(), InMemoryKeyProvider())
        manager.saveGeminiApiKey("sample-testing-only-key")
        manager.setVoiceHistoryEnabled(true)
        manager.saveVoiceConversation(listOf(
            com.javo.agents.data.model.VoiceMessage(
                id = "u-1", isUser = true, text = "Hello",
                language = com.javo.agents.data.model.VoiceLanguage.English,
                timestampLabel = "Now"
            )
        ))
        manager.clearVoiceConversation()
        assertTrue(manager.getVoiceConversation().isEmpty())
        assertTrue(manager.hasGeminiApiKey())
    }
}
