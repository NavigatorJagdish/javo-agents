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
    val priority: String = "normal", // low, normal, high, critical
    val description: String = "",
    val scheduledEpochMs: Long? = null,
    val isReminderEnabled: Boolean = false,
    val resultOutput: String? = null,
    val errorMessage: String? = null,
    val goalId: String? = null,
    val syncedWithDesktop: Boolean = false,
    val createdAtEpochMs: Long = System.currentTimeMillis(),
    val updatedAtEpochMs: Long = System.currentTimeMillis()
)

@Dao
interface TaskDao {
    @Query("SELECT * FROM tasks ORDER BY updatedAtEpochMs DESC")
    fun observeAll(): Flow<List<TaskEntity>>

    @Query("SELECT * FROM tasks WHERE id = :id LIMIT 1")
    suspend fun getById(id: String): TaskEntity?

    @Query("SELECT * FROM tasks WHERE state = 'pending' ORDER BY createdAtEpochMs ASC")
    suspend fun getPendingTasks(): List<TaskEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(tasks: List<TaskEntity>)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(task: TaskEntity)

    @Query("UPDATE tasks SET state = :newState, updatedAtEpochMs = :now WHERE state IN ('pending', 'running')")
    suspend fun pauseAllActive(newState: String = "paused", now: Long = System.currentTimeMillis())

    @Query("UPDATE tasks SET state = :newState, updatedAtEpochMs = :now WHERE id = :id")
    suspend fun updateState(id: String, newState: String, now: Long = System.currentTimeMillis())

    @Query("UPDATE tasks SET state = :newState, resultOutput = :result, errorMessage = :error, updatedAtEpochMs = :now WHERE id = :id")
    suspend fun updateExecutionResult(id: String, newState: String, result: String?, error: String?, now: Long = System.currentTimeMillis())

    @Query("DELETE FROM tasks WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM tasks")
    suspend fun clearAll()
}
