package com.javo.agents.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "notifications")
data class NotificationEntity(
    @PrimaryKey val id: String,
    val title: String,
    val message: String,
    val category: String, // approval, sync, security, agent
    val isRead: Boolean = false,
    val timestampLabel: String,
    val createdAtEpochMs: Long = System.currentTimeMillis()
)

@Dao
interface NotificationDao {
    @Query("SELECT * FROM notifications ORDER BY createdAtEpochMs DESC")
    fun observeAll(): Flow<List<NotificationEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(items: List<NotificationEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(item: NotificationEntity)

    @Query("UPDATE notifications SET isRead = 1 WHERE id = :id")
    suspend fun markRead(id: String)

    @Query("UPDATE notifications SET isRead = 1")
    suspend fun markAllRead()

    @Query("DELETE FROM notifications WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM notifications")
    suspend fun clearAll()
}
