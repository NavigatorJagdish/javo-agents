package com.javo.agents.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "tasks")
data class TaskEntity(
    @PrimaryKey val id: String,
    val title: String,
    val assignedAgent: String,
    val state: String, // pending, running, paused, completed, failed, cancelled
    val priority: String, // low, normal, high, critical
    val goalId: String? = null,
    val syncedWithDesktop: Boolean = false,
    val updatedAtEpochMs: Long = System.currentTimeMillis()
)

@Dao
interface TaskDao {
    @Query("SELECT * FROM tasks ORDER BY updatedAtEpochMs DESC")
    fun observeAll(): Flow<List<TaskEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(tasks: List<TaskEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(task: TaskEntity)

    @Query("UPDATE tasks SET state = :newState, updatedAtEpochMs = :now WHERE state IN ('pending', 'running')")
    suspend fun pauseAllActive(newState: String = "paused", now: Long = System.currentTimeMillis())

    @Query("DELETE FROM tasks")
    suspend fun clearAll()
}
