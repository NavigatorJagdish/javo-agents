package com.javo.agents.data.local

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase

@Database(
    entities = [
        TaskEntity::class,
        GoalEntity::class,
        DraftEntity::class,
        ApprovalEntity::class,
        AccountEntity::class,
        NotificationEntity::class
    ],
    version = 2,
    exportSchema = false
)
abstract class JavoDatabase : RoomDatabase() {
    abstract fun taskDao(): TaskDao
    abstract fun goalDao(): GoalDao
    abstract fun draftDao(): DraftDao
    abstract fun approvalDao(): ApprovalDao
    abstract fun accountDao(): AccountDao
    abstract fun notificationDao(): NotificationDao

    companion object {
        @Volatile
        private var INSTANCE: JavoDatabase? = null

        fun getInstance(context: Context): JavoDatabase {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: Room.databaseBuilder(
                    context.applicationContext,
                    JavoDatabase::class.java,
                    "javo_agents.db"
                ).fallbackToDestructiveMigration()
                    .build()
                    .also { INSTANCE = it }
            }
        }
    }
}
