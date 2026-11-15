# Text companion and audio status

The Voice navigation opens **Javo companion**. It contains a real, authenticated
text interface, bounded model requests and audited runtime controls. Old sample
conversations, fake Whisper readiness, empty WAV output and fabricated command
success responses have been removed.

To use text inference, install and run a compatible Ollama model, save its model
name and loopback endpoint in Settings, then explicitly resume the runtime.
Select a language and send text. Conversation context is bounded to recent
completed exchanges. Provider, model and “no action performed” identify AI advice.
The model has no tools. Captions and explanations do not publish or approve posts.

Controls accept exact commands: `status` / `runtime status`, `pause autopilot`,
`resume autopilot`, `emergency stop` and the documented API Hindi/Hinglish variants.
Resume needs a separate confirmation and clears emergency stop; it can release
eligible queued work. Pausing holds queued automation. Emergency stop requests
cooperative cancellation. Cancel closes a pending text request; the backend
cancels its bounded worker operation on disconnect. A completed control cannot be
undone by cancelling its response. Check status afterwards if interrupted.

Chat uses Ollama by default. Selecting a cloud provider explicitly warns about
sending conversation context; provider selection clears current conversation and
context to prevent a local conversation being forwarded on a later selection.
Cloud generation obeys the existing zero-cost budget; positive budget edits remain
blocked pending durable spending controls. There is no silent provider fallback.
Saving credentials alone does not make network requests.

History is held in tab memory only, bounded to 40 displayed messages and four
context turns; it is not persisted to localStorage, IndexedDB or a server history
store. Clear resets both displayed and sent context. Reload or leaving this screen
also clears it. The selected provider processes the text it receives. No claim is
made about a provider's retention policy. Request bodies are not written to logs.

Speech recognition, speech synthesis, microphone capture and wake word are not
yet integrated. `/voice/capabilities` reports this explicitly; `/voice/tts` and
`/voice/transcribe` return 501. No dummy audio or transcript is returned.

Tests use synthetic responses through a temporary loopback provider fixture,
plus authenticated API, real worker cancellation and Windows packaged runtime
checks. These do not prove inference quality or performance of a real model.
