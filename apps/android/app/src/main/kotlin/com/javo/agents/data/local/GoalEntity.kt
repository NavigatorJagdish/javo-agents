package com.javo.agents.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "goals")
data class GoalEntity(
    @PrimaryKey val id: String,
    val title: String,
    val description: String,
    val progress: Float, // 0.0f .. 1.0f
    val status: String, // active, paused, completed
    val deadlineLabel: String,
    val milestoneSummary: String,
    val syncedWithDesktop: Boolean = false,
    val updatedAtEpochMs: Long = System.currentTimeMillis()
)

@Dao
interface GoalDao {
    @Query("SELECT * FROM goals ORDER BY updatedAtEpochMs DESC")
    fun observeAll(): Flow<List<GoalEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(goal: GoalEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(goals: List<GoalEntity>)

    @Query("DELETE FROM goals")
    suspend fun clearAll()
}
