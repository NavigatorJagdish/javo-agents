package com.javo.agents

import com.javo.agents.data.model.PairingTokenPayload
import com.javo.agents.data.model.PairingTokenValidator
import com.javo.agents.data.model.PairingValidationResult
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class PairingTokenValidatorTest {

    @Test
    fun validate_acceptsValidLocalHttpsAndLanHttpPayloads() {
        val now = 1_700_000_000L
        val validLan = PairingTokenPayload(
            hostUrl = "http://192.168.1.25:8000/",
            pairingCode = "JAVO42",
            deviceToken = "tok_0123456789abcdef",
            expiresAtEpochSec = now + 300
        )

        val result = PairingTokenValidator.validate(validLan, now)
        assertTrue(result is PairingValidationResult.Valid)
        val payload = (result as PairingValidationResult.Valid).payload
        assertEquals("http://192.168.1.25:8000", payload.hostUrl)
    }

    @Test
    fun validate_rejectsExpiredOrRemoteCleartextPayloads() {
        val now = 1_700_000_000L

        val expired = PairingTokenPayload(
            hostUrl = "https://my-pc.tailnet.ts.net:8000",
            pairingCode = "PAIR99",
            deviceToken = "tok_0123456789abcdef",
            expiresAtEpochSec = now - 10
        )
        assertTrue(PairingTokenValidator.validate(expired, now) is PairingValidationResult.Invalid)

        val remoteHttp = PairingTokenPayload(
            hostUrl = "http://example.com:8000",
            pairingCode = "PAIR99",
            deviceToken = "tok_0123456789abcdef",
            expiresAtEpochSec = now + 300
        )
        assertTrue(PairingTokenValidator.validate(remoteHttp, now) is PairingValidationResult.Invalid)
    }

    @Test
    fun parseManualOrQr_parsesJsonAndPipeFormats() {
        val now = 1_700_000_000L
        val pipe = "https://192.168.1.10:8000|CODE123|tok_abcdef0123456789|${now + 600}|sha256:xyz"
        val resPipe = PairingTokenValidator.parseManualOrQr(pipe, now)
        assertTrue(resPipe is PairingValidationResult.Valid)

        val json = """
            {
              "hostUrl": "http://10.0.2.2:8000",
              "pairingCode": "DEV-01",
              "deviceToken": "tok_abcdef0123456789",
              "expiresAtEpochSec": ${now + 600}
            }
        """.trimIndent()
        val resJson = PairingTokenValidator.parseManualOrQr(json, now)
        assertTrue(resJson is PairingValidationResult.Valid)
    }
}
