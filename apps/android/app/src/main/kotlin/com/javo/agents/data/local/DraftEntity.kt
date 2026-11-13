package com.javo.agents.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "drafts")
data class DraftEntity(
    @PrimaryKey val id: String,
    val title: String,
    val body: String,
    val platform: String, // Instagram, Facebook, YouTube
    val status: String, // offline_draft, queued_sync, synced, scheduled, published
    val scheduledDateLabel: String? = null,
    val mediaUri: String? = null,
    val mediaMimeType: String? = null,
    val tags: String = "",
    val publishedResultUrl: String? = null,
    val publishedAtEpochMs: Long? = null,
    val pendingSync: Boolean = true,
    val createdAtEpochMs: Long = System.currentTimeMillis(),
    val updatedAtEpochMs: Long = System.currentTimeMillis()
)

@Dao
interface DraftDao {
    @Query("SELECT * FROM drafts ORDER BY updatedAtEpochMs DESC")
    fun observeAll(): Flow<List<DraftEntity>>

    @Query("SELECT * FROM drafts WHERE pendingSync = 1")
    suspend fun getPendingSync(): List<DraftEntity>

    @Query("SELECT * FROM drafts WHERE id = :id")
    suspend fun getById(id: String): DraftEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(draft: DraftEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(drafts: List<DraftEntity>)

    @Query("UPDATE drafts SET pendingSync = 0, status = :status WHERE id = :id")
    suspend fun markSynced(id: String, status: String = "synced")

    @Query("DELETE FROM drafts WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM drafts")
    suspend fun clearAll()
}
