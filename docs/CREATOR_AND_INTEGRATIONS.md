# Voice, creation and reviewed integrations — 20 November 2026

This is a development increment. It does not certify every external agent,
model, production workflow or final product requirement.

## Local voice

Voice now contains eight Kokoro presets, speed and original natural/radio/echo/
deep/bright effects, explicit WAV playback/download, a pronunciation dictionary,
microphone capture up to30 seconds, WAV upload, Whisper transcription and manual
transcript transfer. A transcript never runs a command by itself. Deep/bright
change pitch and duration together. The original Hindi pronunciation frontend
is approximate; this is neither a trained custom voice nor a promised imitation
of another service. Wake word, streamed conversation and voice training remain
unimplemented. Mindhub assets/code/service were not copied or connected.

Install the optional models outside the checkout/app bundle:

```powershell
python scripts/install-speech-models.py --model-root D:/openaiprojects/local-models/speech
```

Use the runtime virtual environment's Python. The installer verifies pinned
archive sizes/hashes and extracts only needed model, lexicon and notice files.
It preserves differing existing files and excludes the old GPL phonemizer data.
Kokoro's archive digest matches its official release; Whisper's pinned digest
is an observed local integrity pin because the release supplied no vendor digest.
No model download happens from saving settings. Review each model's own license
before any commercial use or redistribution; models are not Javo-owned assets.

In Voice → Local model setup, select `kokoro-int8-multi-lang-v1_0` and
`sherpa-onnx-whisper-tiny` beneath that directory. Save, explicitly resume the
runtime if desired, then generate a short sample. Settings are in a separate
encrypted voice configuration. Keep the app's resource checks enabled; use one
heavy model/tool at a time on8GB machines.

Real source-runtime HTTP acceptance using sherpa/core2.0.1 and normal admission
generated English, Hindi and radio WAVs in13.813s,11.328s and11.297s respectively.
The clips lasted3.527s,4.652s and3.331s. Actual Whisper round trips took1.765s
and1.485s. English misrecognized “Javo”; Hindi was imperfect/romanized. These are
measured samples, not conversational latency, physical-microphone or naturalness
certification. Repeat explicitly using:

```powershell
python scripts/verify-local-speech.py --model-root D:/openaiprojects/local-models/speech --output-dir D:/openaiprojects/voice-acceptance
```

## Images, videos and trends

Creation studio saves encrypted local ComfyUI settings. Its fixed native graphs
support checkpoint images at512×512 and Wan2.1 short video at832×480,49frames,
16fps. Node/model inventory checks do not prove rendering. No ComfyUI runtime,
weights or GPL code is bundled with Javo. No image/video render or quality was
verified on this CPU/8GB host. A suitably provisioned, separately operated service
and independently licensed models are required for actual generation acceptance.

Every submission reviews the exact brief and saved configuration, creates a
durable idempotent receipt, and avoids automatic replay after uncertain network
outcomes. Refresh observes the specific provider ID. Downloads require a bounded
actual artifact and a matching hash. Queued removal addresses only this job;
stopping tracking does not certify stopping the external generator.

Trend refresh requests Google's official public RSS with country only, retains
source/time and fails without replacing a previous snapshot on invalid responses.
Actual India refresh on20November returned10 topics. It is search interest,
not social-platform analytics or guaranteed demand. UI checks use clearly
synthetic audio; real model and official-feed evidence are separate checks.

## External agent/tool connections

Integrations lists11 pinned references, actual license classifications, archived
status and supported adapter paths. A catalog entry is never a running runtime.
Create a separate expiring client grant; never give a client the owner token.
Grant only the necessary scopes: status, goal-title reads, workflow summaries,
proposal submission and optionally that same grant's reviewed results. Revocation
also prevents pending proposals from being approved. Prompts/output can be private;
own-result access deliberately discloses the requested result to that client.

External clients can propose a saved executable workflow. Review inbox loads the
actual saved definition/prompts and input. Approval checks revision, fingerprint,
expiry and source authorization again, then atomically queues the run. It does
not resume execution or authorize publishing, paid actions, email or shell access.

| Tool | Available Javo path | External acceptance remaining |
| --- | --- | --- |
| Hermes, OpenHands, CrewAI, Browser Use | Scoped HTTP MCP bridge or stdio proxy | Install/configure each external runtime in isolation; verify tool schema and model permissions |
| LangGraph | Optional compiled read-only SDK example | Broader model/review orchestration |
| Aider | Original read-only context export | Reviewed edits in a separate checkout/CLI |
| Claude Task Master | Original task JSON export | External-only license review and actual CLI/MCP use |
| n8n | Read-only and17-node reviewed drafting templates | Separate instance, credentials, import/run acceptance |
| Cloudflare Agentic Inbox | Catalog/reference | Domain/email/account deployment and explicit send authorization |
| LangChain Agent Inbox | Review-format export, archived warning | Upstream is archived; no hosted UI activated |
| Awesome MCP Servers | Discovery reference only | Audit each selected server; directory listing is not vetting |

`integrations/clients/mcp_stdio_proxy.py` is dependency-free and loopback-only.
The optional LangGraph client pins LangGraph1.2.22/MCP2.3.0 in its separate
requirements file. Actual official SDK and stdio checks passed against a real
isolated Javo server; no cloud tracing/model/account was used. Run them with
`scripts/verify-integration-sdk.py` from the separate SDK environment.

## Best use now

Supply verified facts to a saved caption/Hindi-script/trend-ideas workflow, inspect
its exact definition and review the generated draft. Generate a short voice sample,
listen, correct pronunciation and export WAV. Research trends explicitly and verify
context before drafting. Add a separate media generator only after checking its
models, hardware and license. Keep publication manual until official connections
and independently checked remote receipts are implemented.

See [n8n setup](N8N_WORKFLOWS.md), [license boundary](THIRD_PARTY_BOUNDARY.md)
and [security review](security/SECURITY_REVIEW_20261120.md).
