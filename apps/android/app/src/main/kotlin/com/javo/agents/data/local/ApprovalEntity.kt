package com.javo.agents.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "approvals")
data class ApprovalEntity(
    @PrimaryKey val id: String,
    val title: String,
    val agentName: String,
    val platform: String,
    val previewContent: String,
    val riskLevel: String, // low, medium, high
    val scheduledFor: String,
    val status: String, // pending, approved, rejected, rescheduled
    val pendingSync: Boolean = false,
    val createdAtEpochMs: Long = System.currentTimeMillis()
)

@Dao
interface ApprovalDao {
    @Query("SELECT * FROM approvals ORDER BY createdAtEpochMs DESC")
    fun observeAll(): Flow<List<ApprovalEntity>>

    @Query("SELECT * FROM approvals WHERE status = 'pending' ORDER BY createdAtEpochMs DESC")
    fun observePending(): Flow<List<ApprovalEntity>>

    @Query("SELECT * FROM approvals WHERE pendingSync = 1")
    suspend fun getPendingSync(): List<ApprovalEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(approval: ApprovalEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(approvals: List<ApprovalEntity>)

    @Query("UPDATE approvals SET status = :status, previewContent = :updatedContent, scheduledFor = :scheduledFor, pendingSync = :pendingSync WHERE id = :id")
    suspend fun updateDecision(
        id: String,
        status: String,
        updatedContent: String,
        scheduledFor: String,
        pendingSync: Boolean = true
    )

    @Query("UPDATE approvals SET pendingSync = 0 WHERE id = :id")
    suspend fun markSynced(id: String)

    @Query("DELETE FROM approvals WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM approvals")
    suspend fun clearAll()
}
