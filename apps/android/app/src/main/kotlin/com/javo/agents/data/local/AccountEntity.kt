package com.javo.agents.data.local

import androidx.room.Dao
import androidx.room.Entity
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.PrimaryKey
import androidx.room.Query
import kotlinx.coroutines.flow.Flow

@Entity(tableName = "accounts")
data class AccountEntity(
    @PrimaryKey val id: String,
    val platform: String, // Facebook Pages, Instagram Professional, YouTube, Telegram
    val handle: String,
    val brandName: String,
    val status: String, // Connected, Beta, Token Expiring, Disconnected
    val followersLabel: String,
    val lastSyncLabel: String
)

@Dao
interface AccountDao {
    @Query("SELECT * FROM accounts ORDER BY platform ASC")
    fun observeAll(): Flow<List<AccountEntity>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(account: AccountEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsertAll(accounts: List<AccountEntity>)

    @Query("DELETE FROM accounts WHERE id = :id")
    suspend fun deleteById(id: String)

    @Query("DELETE FROM accounts")
    suspend fun clearAll()
}
