package com.javo.agents.service

import android.Manifest
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.content.pm.ServiceInfo
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.core.app.ServiceCompat
import androidx.core.content.ContextCompat
import com.javo.agents.JavoApplication
import com.javo.agents.MainActivity
import com.javo.agents.R

class VoiceCaptureService : Service() {

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACTION_STOP) {
            stopForeground(STOP_FOREGROUND_REMOVE)
            stopSelf()
            return START_NOT_STICKY
        }

        val hasMicPermission = ContextCompat.checkSelfPermission(
            this,
            Manifest.permission.RECORD_AUDIO
        ) == PackageManager.PERMISSION_GRANTED

        if (!hasMicPermission) {
            stopSelf()
            return START_NOT_STICKY
        }

        val openAppIntent = PendingIntent.getActivity(
            this,
            0,
            Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val stopIntent = PendingIntent.getService(
            this,
            1,
            Intent(this, VoiceCaptureService::class.java).apply { action = ACTION_STOP },
            PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT
        )

        val notification = NotificationCompat.Builder(this, JavoApplication.CHANNEL_VOICE)
            .setSmallIcon(android.R.drawable.ic_btn_speak_now)
            .setContentTitle(getString(R.string.voice_notification_title))
            .setContentText(getString(R.string.voice_notification_body))
            .setContentIntent(openAppIntent)
            .addAction(android.R.drawable.ic_media_pause, "Stop", stopIntent)
            .setOngoing(true)
            .build()

        val serviceType = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            ServiceInfo.FOREGROUND_SERVICE_TYPE_MICROPHONE
        } else {
            0
        }

        ServiceCompat.startForeground(this, NOTIFICATION_ID, notification, serviceType)
        return START_NOT_STICKY
    }

    companion object {
        const val ACTION_START = "com.javo.agents.voice.START"
        const val ACTION_STOP = "com.javo.agents.voice.STOP"
        private const val NOTIFICATION_ID = 7001

        fun start(context: Context) {
            val intent = Intent(context, VoiceCaptureService::class.java).apply {
                action = ACTION_START
            }
            ContextCompat.startForegroundService(context, intent)
        }

        fun stop(context: Context) {
            val intent = Intent(context, VoiceCaptureService::class.java).apply {
                action = ACTION_STOP
            }
            context.startService(intent)
        }
    }
}
