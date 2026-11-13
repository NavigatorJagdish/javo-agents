package com.javo.agents

import com.javo.agents.data.local.DraftEntity
import com.javo.agents.data.local.TaskEntity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertTrue
import org.junit.Test

class TaskEngineTest {

    @Test
    fun testTaskEntityFieldsAndDefaults() {
        val now = System.currentTimeMillis()
        val task = TaskEntity(
            id = "tsk-101",
            title = "Create 3 Hinglish Hooks",
            assignedAgent = "content_factory",
            state = "pending",
            priority = "high",
            description = "Target tech enthusiasts and developers",
            scheduledEpochMs = now + 3600000L,
            isReminderEnabled = true
        )

        assertEquals("tsk-101", task.id)
        assertEquals("Create 3 Hinglish Hooks", task.title)
        assertEquals("content_factory", task.assignedAgent)
        assertEquals("pending", task.state)
        assertEquals("high", task.priority)
        assertEquals("Target tech enthusiasts and developers", task.description)
        assertTrue(task.isReminderEnabled)
        assertEquals(now + 3600000L, task.scheduledEpochMs)
    }

    @Test
    fun testDraftEntityWithMediaAndTags() {
        val draft = DraftEntity(
            id = "draft-101",
            title = "AI Coding Assistants Guide",
            body = "5 ways local AI saves 10 hours a week.",
            platform = "Instagram",
            status = "offline_draft",
            mediaUri = "content://media/external/images/media/42",
            mediaMimeType = "image/jpeg",
            tags = "#ai #coding #developer",
            pendingSync = true
        )

        assertEquals("draft-101", draft.id)
        assertEquals("Instagram", draft.platform)
        assertEquals("content://media/external/images/media/42", draft.mediaUri)
        assertEquals("image/jpeg", draft.mediaMimeType)
        assertEquals("#ai #coding #developer", draft.tags)
        assertTrue(draft.pendingSync)
    }
}
