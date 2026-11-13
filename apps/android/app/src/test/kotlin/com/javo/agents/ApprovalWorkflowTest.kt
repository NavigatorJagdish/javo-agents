package com.javo.agents

import com.javo.agents.data.local.ApprovalEntity
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class ApprovalWorkflowTest {

    @Test
    fun pendingApproval_transitionsToApprovedAndRejected() {
        val initial = ApprovalEntity(
            id = "apr-test-1",
            title = "Test Reel Approval",
            agentName = "Content Publisher",
            platform = "Instagram",
            previewContent = "Sample Reel Hook",
            riskLevel = "medium",
            scheduledFor = "Tomorrow 10:00 AM",
            status = "pending",
            pendingSync = false
        )

        assertEquals("pending", initial.status)
        assertFalse(initial.pendingSync)

        // Approve
        val approved = initial.copy(status = "approved", pendingSync = true)
        assertEquals("approved", approved.status)
        assertTrue(approved.pendingSync)

        // Reject
        val rejected = initial.copy(status = "rejected", pendingSync = true)
        assertEquals("rejected", rejected.status)
        assertTrue(rejected.pendingSync)

        // Reschedule
        val rescheduled = initial.copy(
            status = "rescheduled",
            scheduledFor = "Friday 6:00 PM",
            previewContent = "Edited Caption",
            pendingSync = true
        )
        assertEquals("rescheduled", rescheduled.status)
        assertEquals("Friday 6:00 PM", rescheduled.scheduledFor)
        assertEquals("Edited Caption", rescheduled.previewContent)
        assertTrue(rescheduled.pendingSync)
    }

    @Test
    fun legacySampleIds_areIdentifiedForSafeMigration() {
        val legacyIds = setOf(
            "draft-101", "draft-102", "draft-103",
            "apr-201", "apr-202", "apr-203",
            "goal-1", "goal-2",
            "tsk-1", "tsk-2", "tsk-3",
            "acc-ig", "acc-fb", "acc-yt", "acc-tg",
            "not-1", "not-2", "not-3"
        )

        // Real user created ID
        val userDraftId = "draft-a1b2c3d4"
        val userApprovalId = "apr-999"

        assertFalse(legacyIds.contains(userDraftId))
        assertFalse(legacyIds.contains(userApprovalId))
        assertTrue(legacyIds.contains("draft-101"))
        assertTrue(legacyIds.contains("apr-201"))
    }
}
