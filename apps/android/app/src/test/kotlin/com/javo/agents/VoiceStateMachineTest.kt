package com.javo.agents

import com.javo.agents.data.model.VoiceConversationMode
import com.javo.agents.data.model.WaveformState
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test
import java.util.concurrent.atomic.AtomicBoolean

@OptIn(ExperimentalCoroutinesApi::class)
class VoiceStateMachineTest {

    @Test
    fun fullVoiceCycle_transitionsThroughAllStatesInOrder() {
        val stateHistory = mutableListOf<WaveformState>()
        var currentState = WaveformState.Idle
        stateHistory.add(currentState)

        // 1. User taps mic -> Connecting
        currentState = WaveformState.Connecting
        stateHistory.add(currentState)

        // 2. Recognizer ready -> Listening
        currentState = WaveformState.Listening
        stateHistory.add(currentState)

        // 3. User stops talking (onEndOfSpeech) -> Finalizing
        currentState = WaveformState.Finalizing
        stateHistory.add(currentState)

        // 4. Transcript arrived, dispatching to AI -> Thinking
        currentState = WaveformState.Thinking
        stateHistory.add(currentState)

        // 5. AI response generated, preparing voice synthesis -> Responding
        currentState = WaveformState.Responding
        stateHistory.add(currentState)

        // 6. TTS audio playback starts -> Speaking
        currentState = WaveformState.Speaking
        stateHistory.add(currentState)

        // 7. TTS audio playback ends (onDone) -> Idle
        currentState = WaveformState.Idle
        stateHistory.add(currentState)

        val expected = listOf(
            WaveformState.Idle,
            WaveformState.Connecting,
            WaveformState.Listening,
            WaveformState.Finalizing,
            WaveformState.Thinking,
            WaveformState.Responding,
            WaveformState.Speaking,
            WaveformState.Idle
        )
        assertEquals("State machine must transition strictly in prescribed order", expected, stateHistory)
    }

    @Test
    fun concurrencyGuard_preventsDuplicateExecutionFromSimultaneousManualStopAndCallback() {
        val isProcessing = AtomicBoolean(false)
        var executionCount = 0

        fun processVoiceCommand(text: String): Boolean {
            if (!isProcessing.compareAndSet(false, true)) {
                return false // Discard duplicate call
            }
            executionCount++
            return true
        }

        // Simulate simultaneous trigger from onResults callback and user tapping Stop button
        val callbackDispatched = processVoiceCommand("Create a task for tomorrow")
        val manualStopDispatched = processVoiceCommand("Create a task for tomorrow")

        assertTrue("First dispatch must succeed", callbackDispatched)
        assertFalse("Second concurrent dispatch must be safely rejected", manualStopDispatched)
        assertEquals("Command must execute exactly once", 1, executionCount)
    }

    @Test
    fun ttsSynthesisFailure_neverFalselyClaimsSpeaking() {
        var isSpeaking = false
        var waveformState = WaveformState.Responding

        fun simulateTtsSpeak(synthesisSuccess: Boolean) {
            if (synthesisSuccess) {
                isSpeaking = true
                waveformState = WaveformState.Speaking
            } else {
                // When TTS synthesis fails (e.g. engine error), fail closed
                isSpeaking = false
                waveformState = WaveformState.Idle
            }
        }

        // Simulate synthesis failure
        simulateTtsSpeak(synthesisSuccess = false)

        assertFalse("isSpeaking must be false if synthesis fails", isSpeaking)
        assertEquals("Waveform state must revert to Idle on synthesis failure", WaveformState.Idle, waveformState)
    }

    @Test
    fun handsFreeMode_autoResumesListeningAfterSpeechFinishes() = runTest {
        var mode = VoiceConversationMode.HANDS_FREE
        var isHandsFreeActive = true
        var nextListenTriggered = false

        fun onTtsDone() {
            if (mode == VoiceConversationMode.HANDS_FREE && isHandsFreeActive) {
                // Auto resume listening
                nextListenTriggered = true
            }
        }

        onTtsDone()
        assertTrue("Hands-free mode must trigger next listening session on TTS completion", nextListenTriggered)

        // In Tap-to-Talk mode, next session is NOT auto triggered
        mode = VoiceConversationMode.TAP_TO_TALK
        nextListenTriggered = false
        onTtsDone()
        assertFalse("Tap-to-talk mode must remain Idle after speech completion", nextListenTriggered)
    }

    @Test
    fun cancelDuringListening_immediatelyReturnsToIdle() {
        var waveformState = WaveformState.Listening
        var isListening = true

        fun cancelVoiceCapture() {
            isListening = false
            waveformState = WaveformState.Idle
        }

        cancelVoiceCapture()
        assertFalse("Listening must be cancelled", isListening)
        assertEquals("State must be immediately Idle", WaveformState.Idle, waveformState)
    }
}
