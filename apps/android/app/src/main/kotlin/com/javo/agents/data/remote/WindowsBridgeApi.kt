package com.javo.agents.data.remote

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable
import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.DELETE
import retrofit2.http.GET
import retrofit2.http.POST
import retrofit2.http.Path

@Serializable
data class HealthDto(
    val status: String = "ok",
    val version: String = "0.1.1-alpha",
    @SerialName("uptime_seconds") val uptimeSeconds: Double = 0.0
)

@Serializable
data class PairConfirmRequest(
    @SerialName("device_id") val deviceId: String,
    @SerialName("device_name") val deviceName: String,
    val platform: String = "android",
    @SerialName("device_token") val deviceToken: String = ""
)

@Serializable
data class PairConfirmResponse(
    val paired: Boolean = true,
    @SerialName("device_id") val deviceId: String = "",
    @SerialName("device_token") val deviceToken: String = "",
    val message: String = "Paired"
)

@Serializable
data class DraftSyncRequest(
    val id: String,
    val title: String,
    val body: String,
    val platform: String,
    val status: String
)

@Serializable
data class ApprovalDecisionRequest(
    val status: String,
    @SerialName("updated_content") val updatedContent: String,
    @SerialName("scheduled_for") val scheduledFor: String
)

@Serializable
data class VoiceCommandRequest(
    val text: String,
    val language: String = "en"
)

@Serializable
data class VoiceCommandResponse(
    val reply: String,
    @SerialName("routed_agent") val routedAgent: String = "voice_agent",
    val status: String = "executed"
)

@Serializable
data class EmergencyStopResponse(
    val stopped: Boolean = true,
    @SerialName("cancelled_tasks") val cancelledTasks: Int = 0
)

@Serializable
data class SyncPayloadDto(
    @SerialName("device_id") val deviceId: String = "",
    val status: String = "synced",
    @SerialName("active_agents") val activeAgents: Int = 0,
    @SerialName("pending_approvals") val pendingApprovals: Int = 0,
    @SerialName("acknowledged_ids") val acknowledgedIds: List<String> = emptyList(),
    @SerialName("synced_drafts_count") val syncedDraftsCount: Int = 0,
    val message: String = "Synced"
)

interface WindowsBridgeApi {
    @GET("/health")
    suspend fun getHealth(): Response<HealthDto>

    @POST("/devices/pair/{code}/confirm")
    suspend fun confirmPairing(
        @Path("code") code: String,
        @Body request: PairConfirmRequest
    ): Response<PairConfirmResponse>

    @POST("/devices/{id}/sync")
    suspend fun syncDevice(
        @Path("id") deviceId: String,
        @Body drafts: List<DraftSyncRequest>
    ): Response<SyncPayloadDto>

    @DELETE("/devices/{id}")
    suspend fun revokeDevice(@Path("id") deviceId: String): Response<Unit>

    @POST("/agents/{agentName}/enable")
    suspend fun enableAgent(@Path("agentName") agentName: String): Response<Unit>

    @POST("/agents/{agentName}/disable")
    suspend fun disableAgent(@Path("agentName") agentName: String): Response<Unit>

    @POST("/content")
    suspend fun uploadDraft(@Body draft: DraftSyncRequest): Response<Unit>

    @POST("/tasks/{id}/execute")
    suspend fun submitApprovalDecision(
        @Path("id") approvalId: String,
        @Body decision: ApprovalDecisionRequest
    ): Response<Unit>

    @POST("/voice/command")
    suspend fun sendVoiceCommand(@Body request: VoiceCommandRequest): Response<VoiceCommandResponse>

    @POST("/security/emergency-stop")
    suspend fun triggerEmergencyStop(): Response<EmergencyStopResponse>
}
