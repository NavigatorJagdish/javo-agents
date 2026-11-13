package com.javo.agents.workers

import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.work.CoroutineWorker
import androidx.work.Data
import androidx.work.ExistingWorkPolicy
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import com.javo.agents.JavoApplication
import com.javo.agents.MainActivity
import com.javo.agents.R
import java.util.concurrent.TimeUnit

class TaskReminderWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        val app = applicationContext as? JavoApplication ?: return Result.failure()
        val container = app.container

        val taskId = inputData.getString(KEY_TASK_ID) ?: return Result.failure()
        val taskTitle = inputData.getString(KEY_TASK_TITLE) ?: "Task Reminder"
        val taskAgent = inputData.getString(KEY_TASK_AGENT) ?: "Javo Assistant"
        val isScheduledExecution = inputData.getBoolean(KEY_EXECUTE, false)

        if (isScheduledExecution) {
            val task = container.database.taskDao().getById(taskId)
            if (task != null && (task.state == "pending" || task.state == "running")) {
                val execResult = container.orchestrator.executeTask(task)
                if (execResult.isSuccess) {
                    showNotification(
                        title = "Task Completed: $taskTitle",
                        message = "Successfully executed by $taskAgent. Tap to view results.",
                        notificationId = taskId.hashCode()
                    )
                    return Result.success()
                } else {
                    val err = execResult.exceptionOrNull()?.message ?: "Execution failed"
                    showNotification(
                        title = "Task Failed: $taskTitle",
                        message = "Execution issue: ${err.take(80)}",
                        notificationId = taskId.hashCode()
                    )
                    return Result.failure()
                }
            }
        }

        // Standard reminder notification
        showNotification(
            title = "Task Reminder: $taskTitle",
            message = "Assigned to $taskAgent. Tap to open and review in Javo Agents.",
            notificationId = taskId.hashCode()
        )

        return Result.success()
    }

    private fun showNotification(title: String, message: String, notificationId: Int) {
        val intent = Intent(applicationContext, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP
        }
        val pendingIntent = PendingIntent.getActivity(
            applicationContext,
            notificationId,
            intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(applicationContext, JavoApplication.CHANNEL_TASKS)
            .setSmallIcon(R.mipmap.ic_launcher)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        try {
            NotificationManagerCompat.from(applicationContext).notify(notificationId, notification)
        } catch (_: SecurityException) {
            // Permission POST_NOTIFICATIONS may not be granted by user
        }
    }

    companion object {
        const val KEY_TASK_ID = "task_id"
        const val KEY_TASK_TITLE = "task_title"
        const val KEY_TASK_AGENT = "task_agent"
        const val KEY_EXECUTE = "is_scheduled_execution"

        fun scheduleTaskReminder(
            context: Context,
            taskId: String,
            taskTitle: String,
            taskAgent: String,
            delayMs: Long,
            executeAtEnd: Boolean = false
        ) {
            val data = Data.Builder()
                .putString(KEY_TASK_ID, taskId)
                .putString(KEY_TASK_TITLE, taskTitle)
                .putString(KEY_TASK_AGENT, taskAgent)
                .putBoolean(KEY_EXECUTE, executeAtEnd)
                .build()

            val request = OneTimeWorkRequestBuilder<TaskReminderWorker>()
                .setInitialDelay(delayMs.coerceAtLeast(0L), TimeUnit.MILLISECONDS)
                .setInputData(data)
                .build()

            WorkManager.getInstance(context).enqueueUniqueWork(
                "task_reminder_$taskId",
                ExistingWorkPolicy.REPLACE,
                request
            )
        }

        fun cancelTaskReminder(context: Context, taskId: String) {
            WorkManager.getInstance(context).cancelUniqueWork("task_reminder_$taskId")
        }
    }
}
