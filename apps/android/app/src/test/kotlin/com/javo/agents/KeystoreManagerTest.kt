package com.javo.agents

import com.javo.agents.data.local.AesGcmCipher
import com.javo.agents.data.local.KeystoreManager
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
}
