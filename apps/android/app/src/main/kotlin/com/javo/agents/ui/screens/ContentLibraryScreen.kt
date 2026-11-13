package com.javo.agents.ui.screens

import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.PickVisualMediaRequest
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.horizontalScroll
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.rounded.Add
import androidx.compose.material.icons.rounded.AutoAwesome
import androidx.compose.material.icons.rounded.AttachFile
import androidx.compose.material.icons.rounded.Clear
import androidx.compose.material.icons.rounded.ContentPaste
import androidx.compose.material.icons.rounded.DeleteOutline
import androidx.compose.material.icons.rounded.Edit
import androidx.compose.material.icons.rounded.Image
import androidx.compose.material.icons.rounded.Search
import androidx.compose.material.icons.rounded.Sync
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.FilterChip
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.javo.agents.data.local.DraftEntity
import com.javo.agents.data.model.VoiceLanguage
import com.javo.agents.ui.components.BottomNavBar
import com.javo.agents.ui.components.GradientButton
import com.javo.agents.ui.components.JavoOutlinedButton
import com.javo.agents.ui.components.JavoSubScreenScaffold
import com.javo.agents.ui.components.StatusCard
import com.javo.agents.ui.components.StatusPill
import com.javo.agents.ui.theme.AmberWarning
import com.javo.agents.ui.theme.CoralDanger
import com.javo.agents.ui.theme.ElectricCyan
import com.javo.agents.ui.theme.EmeraldSuccess
import com.javo.agents.ui.theme.MidnightNavy
import com.javo.agents.ui.theme.VioletAccent
import com.javo.agents.ui.viewmodel.MainViewModel

@Composable
fun ContentLibraryScreen(
    viewModel: MainViewModel,
    currentRoute: String?,
    onNavigate: (String) -> Unit
) {
    val drafts by viewModel.drafts.collectAsState()
    val approvals by viewModel.approvals.collectAsState()

    var searchQuery by remember { mutableStateOf("") }
    var selectedPlatform by remember { mutableStateOf("All") }
    var showCreateDialog by remember { mutableStateOf(false) }
    var editingDraft by remember { mutableStateOf<DraftEntity?>(null) }
    var deletingDraftId by remember { mutableStateOf<String?>(null) }

    val platforms = listOf("All", "Instagram", "YouTube", "Facebook", "X", "Telegram", "LinkedIn")

    val filteredDrafts = remember(drafts, searchQuery, selectedPlatform) {
        drafts.filter { draft ->
            val matchesSearch = searchQuery.isBlank() ||
                draft.title.contains(searchQuery, ignoreCase = true) ||
                draft.body.contains(searchQuery, ignoreCase = true)
            val matchesPlatform = selectedPlatform == "All" ||
                draft.platform.equals(selectedPlatform, ignoreCase = true)
            matchesSearch && matchesPlatform
        }
    }

    val isGeneratingDraft by viewModel.isGeneratingDraft.collectAsState()

    // Create Draft Dialog
    if (showCreateDialog) {
        var title by remember { mutableStateOf("") }
        var body by remember { mutableStateOf("") }
        var platform by remember { mutableStateOf("Instagram") }
        var schedule by remember { mutableStateOf("") }
        var tags by remember { mutableStateOf("") }
        var attachedMediaUri by remember { mutableStateOf<String?>(null) }
        var aiTopic by remember { mutableStateOf("") }
        var showAiSection by remember { mutableStateOf(false) }

        val mediaPicker = rememberLauncherForActivityResult(
            contract = ActivityResultContracts.PickVisualMedia()
        ) { uri ->
            if (uri != null) {
                attachedMediaUri = uri.toString()
            }
        }

        AlertDialog(
            onDismissRequest = { showCreateDialog = false },
            title = { Text("New Content Draft") },
            text = {
                Column(
                    modifier = Modifier.verticalScroll(rememberScrollState()),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    // AI Generator toggle
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Text("AI Content Assist", style = MaterialTheme.typography.titleSmall)
                        JavoOutlinedButton(
                            text = if (showAiSection) "Hide AI" else "AI Assist ✨",
                            onClick = { showAiSection = !showAiSection },
                            borderColor = ElectricCyan
                        )
                    }

                    if (showAiSection) {
                        OutlinedTextField(
                            value = aiTopic,
                            onValueChange = { aiTopic = it },
                            label = { Text("Topic / Idea for Content Factory") },
                            singleLine = true,
                            modifier = Modifier.fillMaxWidth()
                        )
                        GradientButton(
                            text = if (isGeneratingDraft) "Generating..." else "Generate Hook & Caption",
                            onClick = {
                                viewModel.generateContentDraftWithAi(aiTopic, platform)
                                showCreateDialog = false
                            },
                            enabled = aiTopic.isNotBlank() && !isGeneratingDraft
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                    }

                    OutlinedTextField(
                        value = title,
                        onValueChange = { title = it },
                        label = { Text("Title / Hook") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = body,
                        onValueChange = { body = it },
                        label = { Text("Caption / Script") },
                        minLines = 3,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = tags,
                        onValueChange = { tags = it },
                        label = { Text("Hashtags / Tags (e.g. #tech #reels)") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = platform,
                        onValueChange = { platform = it },
                        label = { Text("Platform (Instagram, YouTube, X...)") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = schedule,
                        onValueChange = { schedule = it },
                        label = { Text("Target Schedule (Optional)") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )

                    // Media Picker Row
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        JavoOutlinedButton(
                            text = if (attachedMediaUri != null) "Change Media" else "Attach Photo/Video",
                            onClick = {
                                mediaPicker.launch(
                                    PickVisualMediaRequest(ActivityResultContracts.PickVisualMedia.ImageAndVideo)
                                )
                            },
                            borderColor = if (attachedMediaUri != null) EmeraldSuccess else ElectricCyan
                        )
                        if (attachedMediaUri != null) {
                            StatusPill(text = "📸 Media Attached", color = EmeraldSuccess)
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        if (title.isNotBlank() && body.isNotBlank()) {
                            viewModel.createDraftWithMedia(
                                title = title,
                                body = body,
                                platform = platform,
                                scheduledDate = schedule.ifBlank { null },
                                mediaUri = attachedMediaUri,
                                tags = tags
                            )
                            showCreateDialog = false
                        }
                    }
                ) { Text("Save Offline") }
            },
            dismissButton = {
                TextButton(onClick = { showCreateDialog = false }) { Text("Cancel") }
            }
        )
    }

    // Edit Draft Dialog
    if (editingDraft != null) {
        val draft = editingDraft!!
        var editTitle by remember(draft.id) { mutableStateOf(draft.title) }
        var editBody by remember(draft.id) { mutableStateOf(draft.body) }
        var editPlatform by remember(draft.id) { mutableStateOf(draft.platform) }
        var editSchedule by remember(draft.id) { mutableStateOf(draft.scheduledDateLabel.orEmpty()) }

        AlertDialog(
            onDismissRequest = { editingDraft = null },
            title = { Text("Edit Draft") },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(
                        value = editTitle,
                        onValueChange = { editTitle = it },
                        label = { Text("Title / Hook") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = editBody,
                        onValueChange = { editBody = it },
                        label = { Text("Caption / Script") },
                        minLines = 3,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = editPlatform,
                        onValueChange = { editPlatform = it },
                        label = { Text("Platform") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                    OutlinedTextField(
                        value = editSchedule,
                        onValueChange = { editSchedule = it },
                        label = { Text("Schedule Slot") },
                        singleLine = true,
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.updateDraft(
                            draft.copy(
                                title = editTitle.trim(),
                                body = editBody.trim(),
                                platform = editPlatform.trim(),
                                scheduledDateLabel = editSchedule.ifBlank { null },
                                pendingSync = true
                            )
                        )
                        editingDraft = null
                    }
                ) { Text("Save Changes") }
            },
            dismissButton = {
                TextButton(onClick = { editingDraft = null }) { Text("Cancel") }
            }
        )
    }

    // Delete Confirmation Dialog
    if (deletingDraftId != null) {
        AlertDialog(
            onDismissRequest = { deletingDraftId = null },
            title = { Text("Delete Draft?") },
            text = { Text("This offline draft will be permanently deleted from local storage.") },
            confirmButton = {
                TextButton(
                    onClick = {
                        viewModel.deleteDraft(deletingDraftId!!)
                        deletingDraftId = null
                    }
                ) { Text("Delete", color = CoralDanger) }
            },
            dismissButton = {
                TextButton(onClick = { deletingDraftId = null }) { Text("Cancel") }
            }
        )
    }

    JavoSubScreenScaffold(
        title = "Content Studio",
        actions = {
            IconButton(onClick = { viewModel.syncNow() }) {
                Icon(Icons.Rounded.Sync, contentDescription = "Sync drafts", tint = ElectricCyan)
            }
        },
        floatingActionButton = {
            FloatingActionButton(
                onClick = { showCreateDialog = true },
                containerColor = ElectricCyan,
                contentColor = MidnightNavy
            ) {
                Icon(Icons.Rounded.Add, contentDescription = "Create draft")
            }
        },
        bottomBar = {
            BottomNavBar(
                currentRoute = currentRoute,
                pendingApprovalsCount = approvals.count { it.status == "pending" },
                onNavigate = onNavigate
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp)
        ) {
            // Search Bar
            OutlinedTextField(
                value = searchQuery,
                onValueChange = { searchQuery = it },
                placeholder = { Text("Search drafts by title or caption...") },
                leadingIcon = { Icon(Icons.Rounded.Search, contentDescription = "Search") },
                trailingIcon = {
                    if (searchQuery.isNotBlank()) {
                        IconButton(onClick = { searchQuery = "" }) {
                            Icon(Icons.Rounded.Clear, contentDescription = "Clear")
                        }
                    }
                },
                modifier = Modifier
                    .fillMaxWidth()
                    .padding(vertical = 4.dp),
                singleLine = true
            )

            // Platform Filter Chips
            Row(
                modifier = Modifier
                    .fillMaxWidth()
                    .horizontalScroll(rememberScrollState())
                    .padding(vertical = 6.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                platforms.forEach { platform ->
                    FilterChip(
                        selected = selectedPlatform == platform,
                        onClick = { selectedPlatform = platform },
                        label = { Text(platform) }
                    )
                }
            }

            Spacer(modifier = Modifier.height(4.dp))

            if (filteredDrafts.isEmpty()) {
                Box(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth(),
                    contentAlignment = Alignment.Center
                ) {
                    Column(
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center,
                        modifier = Modifier.padding(24.dp)
                    ) {
                        Icon(
                            imageVector = Icons.Rounded.ContentPaste,
                            contentDescription = "No Drafts",
                            modifier = Modifier.size(52.dp),
                            tint = ElectricCyan.copy(alpha = 0.6f)
                        )
                        Spacer(modifier = Modifier.height(12.dp))
                        Text(
                            text = if (searchQuery.isNotBlank() || selectedPlatform != "All") "No Matching Drafts" else "No Drafts in Studio",
                            style = MaterialTheme.typography.titleMedium
                        )
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(
                            text = if (searchQuery.isNotBlank() || selectedPlatform != "All") {
                                "Try adjusting your search query or platform filter."
                            } else {
                                "Tap '+' to write a local draft, or use Voice Mode to compose content with AI."
                            },
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onSurfaceVariant,
                            textAlign = androidx.compose.ui.text.style.TextAlign.Center
                        )
                    }
                }
            } else {
                LazyColumn(
                    modifier = Modifier
                        .weight(1f)
                        .fillMaxWidth(),
                    verticalArrangement = Arrangement.spacedBy(10.dp)
                ) {
                    items(filteredDrafts, key = { it.id }) { draft ->
                        val statusLabel = when {
                            draft.status == "scheduled" -> "Scheduled"
                            draft.pendingSync -> "Queued Sync"
                            else -> "Synced"
                        }
                        val statusColor = when {
                            draft.status == "scheduled" -> VioletAccent
                            draft.pendingSync -> AmberWarning
                            else -> EmeraldSuccess
                        }

                        StatusCard {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Text(
                                    text = draft.title,
                                    style = MaterialTheme.typography.titleMedium,
                                    modifier = Modifier.weight(1f)
                                )
                                StatusPill(text = statusLabel, color = statusColor)
                                IconButton(onClick = { editingDraft = draft }) {
                                    Icon(
                                        Icons.Rounded.Edit,
                                        contentDescription = "Edit draft",
                                        tint = ElectricCyan
                                    )
                                }
                                IconButton(onClick = { deletingDraftId = draft.id }) {
                                    Icon(
                                        Icons.Rounded.DeleteOutline,
                                        contentDescription = "Delete draft",
                                        tint = MaterialTheme.colorScheme.onSurfaceVariant
                                    )
                                }
                            }
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(draft.body, style = MaterialTheme.typography.bodyMedium)
                            if (draft.tags.isNotBlank()) {
                                Spacer(modifier = Modifier.height(4.dp))
                                Text(draft.tags, style = MaterialTheme.typography.labelMedium, color = ElectricCyan)
                            }
                            Spacer(modifier = Modifier.height(8.dp))
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween,
                                verticalAlignment = Alignment.CenterVertically
                            ) {
                                Row(horizontalArrangement = Arrangement.spacedBy(8.dp), verticalAlignment = Alignment.CenterVertically) {
                                    Text(
                                        text = draft.platform,
                                        style = MaterialTheme.typography.labelMedium,
                                        color = ElectricCyan
                                    )
                                    if (!draft.mediaUri.isNullOrBlank()) {
                                        StatusPill(text = "📸 Media", color = EmeraldSuccess)
                                    }
                                }
                                Text(
                                    text = draft.scheduledDateLabel ?: "Unscheduled",
                                    style = MaterialTheme.typography.labelMedium,
                                    color = MaterialTheme.colorScheme.onSurfaceVariant
                                )
                            }
                        }
                    }
                    item { Spacer(modifier = Modifier.height(80.dp)) }
                }
            }
        }
    }
}
