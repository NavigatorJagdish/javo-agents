package com.javo.agents.data.remote

import com.javo.agents.data.local.KeystoreManager
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.Json
import okhttp3.Interceptor
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.kotlinx.serialization.asConverterFactory
import java.util.concurrent.TimeUnit

enum class BridgeConnectionState(val label: String) {
    Unpaired("Not Paired"),
    Connected("Connected to Windows"),
    OfflineQueue("Offline (Queued Locally)")
}

class WindowsBridgeClient(
    private val keystoreManager: KeystoreManager
) {
    private val json = Json {
        ignoreUnknownKeys = true
        encodeDefaults = true
    }

    private val _connectionState = MutableStateFlow(
        if (keystoreManager.isPaired()) BridgeConnectionState.OfflineQueue else BridgeConnectionState.Unpaired
    )
    val connectionState: StateFlow<BridgeConnectionState> = _connectionState.asStateFlow()

    @Volatile
    private var cachedBaseUrl: String? = null

    @Volatile
    private var cachedApi: WindowsBridgeApi? = null

    private val authInterceptor = Interceptor { chain ->
        val original = chain.request()
        val builder = original.newBuilder()
            .header("X-Javo-Device-Id", keystoreManager.getOrCreateDeviceId())
            .header("Accept", "application/json")

        keystoreManager.getPairingToken()?.let { token ->
            builder.header("X-Javo-Device-Token", token)
            builder.header("Authorization", "Bearer $token")
        }

        chain.proceed(builder.build())
    }

    private val okHttpClient: OkHttpClient by lazy {
        val logging = HttpLoggingInterceptor().apply {
            level = HttpLoggingInterceptor.Level.BASIC
        }
        OkHttpClient.Builder()
            .addInterceptor(authInterceptor)
            .addInterceptor(logging)
            .connectTimeout(8, TimeUnit.SECONDS)
            .readTimeout(15, TimeUnit.SECONDS)
            .writeTimeout(15, TimeUnit.SECONDS)
            .build()
    }

    private fun apiFor(baseUrl: String): WindowsBridgeApi {
        val normalized = baseUrl.trim().trimEnd('/') + "/"
        if (cachedBaseUrl == normalized && cachedApi != null) {
            return cachedApi!!
        }
        val retrofit = Retrofit.Builder()
            .baseUrl(normalized)
            .client(okHttpClient)
            .addConverterFactory(json.asConverterFactory("application/json".toMediaType()))
            .build()
        return retrofit.create(WindowsBridgeApi::class.java).also {
            cachedBaseUrl = normalized
            cachedApi = it
        }
    }

    suspend fun pingPairedHost(): Boolean {
        val host = keystoreManager.getPairedHostUrl()
        if (host.isNullOrBlank()) {
            _connectionState.value = BridgeConnectionState.Unpaired
            return false
        }
        return try {
            val response = apiFor(host).getHealth()
            val ok = response.isSuccessful
            _connectionState.value = if (ok) BridgeConnectionState.Connected else BridgeConnectionState.OfflineQueue
            ok
        } catch (_: Exception) {
            _connectionState.value = BridgeConnectionState.OfflineQueue
            false
        }
    }

    suspend fun confirmPairing(
        hostUrl: String,
        pairingCode: String,
        deviceToken: String,
        deviceName: String
    ): Result<String> {
        return try {
            val response = apiFor(hostUrl).confirmPairing(
                code = pairingCode,
                request = PairConfirmRequest(
                    deviceId = keystoreManager.getOrCreateDeviceId(),
                    deviceName = deviceName,
                    deviceToken = deviceToken
                )
            )
            if (response.isSuccessful) {
                val body = response.body()
                val serverToken = body?.deviceToken?.ifBlank { deviceToken } ?: deviceToken
                keystoreManager.savePairingSession(hostUrl, serverToken)
                _connectionState.value = BridgeConnectionState.Connected
                Result.success(body?.message ?: "Paired with Windows Runtime")
            } else {
                // Allow local offline-first pairing record when runtime is temporarily unreachable
                _connectionState.value = BridgeConnectionState.OfflineQueue
                Result.failure(IllegalStateException("Runtime returned HTTP ${response.code()}"))
            }
        } catch (e: Exception) {
            _connectionState.value = BridgeConnectionState.OfflineQueue
            Result.failure(e)
        }
    }

    suspend fun syncDrafts(drafts: List<DraftSyncRequest>): Boolean {
        val host = keystoreManager.getPairedHostUrl() ?: return false
        return try {
            val response = apiFor(host).syncDevice(keystoreManager.getOrCreateDeviceId(), drafts)
            val ok = response.isSuccessful
            _connectionState.value = if (ok) BridgeConnectionState.Connected else BridgeConnectionState.OfflineQueue
            ok
        } catch (_: Exception) {
            _connectionState.value = BridgeConnectionState.OfflineQueue
            false
        }
    }

    suspend fun sendVoiceCommand(text: String, languageCode: String): VoiceCommandResponse? {
        val host = keystoreManager.getPairedHostUrl() ?: return null
        return try {
            val response = apiFor(host).sendVoiceCommand(VoiceCommandRequest(text, languageCode))
            if (response.isSuccessful) {
                _connectionState.value = BridgeConnectionState.Connected
                response.body()
            } else {
                _connectionState.value = BridgeConnectionState.OfflineQueue
                null
            }
        } catch (_: Exception) {
            _connectionState.value = BridgeConnectionState.OfflineQueue
            null
        }
    }

    suspend fun triggerEmergencyStop(): Boolean {
        val host = keystoreManager.getPairedHostUrl() ?: return false
        return try {
            val response = apiFor(host).triggerEmergencyStop()
            response.isSuccessful
        } catch (_: Exception) {
            false
        }
    }

    suspend fun revokeOnDesktop() {
        val host = keystoreManager.getPairedHostUrl()
        if (!host.isNullOrBlank()) {
            try {
                apiFor(host).revokeDevice(keystoreManager.getOrCreateDeviceId())
            } catch (_: Exception) {
                // Always clear local credentials even if desktop is unreachable
            }
        }
        keystoreManager.revokePairing()
        cachedApi = null
        cachedBaseUrl = null
        _connectionState.value = BridgeConnectionState.Unpaired
    }
}
