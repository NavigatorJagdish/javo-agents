package com.javo.agents

import com.javo.agents.data.local.DraftEntity
import com.javo.agents.data.repository.DraftStore
import com.javo.agents.data.repository.OfflineDraftRepository
import com.javo.agents.data.repository.RemoteDraftUploader
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class OfflineDraftRepositoryTest {

    private class FakeDraftStore : DraftStore {
        private val items = linkedMapOf<String, DraftEntity>()
        private val flow = MutableStateFlow<List<DraftEntity>>(emptyList())

        override fun observeDrafts(): Flow<List<DraftEntity>> = flow

        override suspend fun saveDraft(draft: DraftEntity) {
            items[draft.id] = draft
            flow.value = items.values.toList()
        }

        override suspend fun getPendingSync(): List<DraftEntity> =
            items.values.filter { it.pendingSync }

        override suspend fun markSynced(id: String) {
            items[id]?.let {
                items[id] = it.copy(pendingSync = false, status = "synced")
                flow.value = items.values.toList()
            }
        }

        override suspend fun deleteDraft(id: String) {
            items.remove(id)
            flow.value = items.values.toList()
        }
    }

    @Test
    fun createOfflineDraft_staysQueuedWhenDesktopOffline_thenSyncsWhenOnline() = runTest {
        val store = FakeDraftStore()
        var desktopOnline = false
        val uploader = object : RemoteDraftUploader {
            override suspend fun uploadPending(drafts: List<DraftEntity>): Boolean {
                return desktopOnline && drafts.isNotEmpty()
            }
        }
        val repo = OfflineDraftRepository(store, uploader)

        val created = repo.createOfflineDraft(
            title = "Hinglish Reel Hook",
            body = "Local AI se content workflow automate karein!",
            platform = "Instagram",
            scheduledDateLabel = "Tomorrow 9 AM"
        )

        assertTrue(created.pendingSync)
        assertEquals(0, repo.queueAndTrySync())
        assertEquals(1, store.getPendingSync().size)

        desktopOnline = true
        val syncedCount = repo.queueAndTrySync()
        assertEquals(1, syncedCount)
        assertTrue(store.getPendingSync().isEmpty())

        val all = repo.observeDrafts().first()
        assertEquals(1, all.size)
        assertFalse(all.first().pendingSync)
        assertEquals("synced", all.first().status)
    }
}
