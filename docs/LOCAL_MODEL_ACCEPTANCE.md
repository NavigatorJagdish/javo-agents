# Real local model smoke — updated 18 November 2026

On18November the extended `--workflow` check also passed against the installed
real model. It saved/reviewed a three-node graph through the authenticated API,
ran it through the durable worker/router/resource manager, inspected actual
nonempty model output and verified2 successful requests /218 reported tokens
after runtime restart. Markers: REAL_LOCAL_MODEL_COMPANION_LEDGER_RESTART_OK
and REAL_SAVED_LOCAL_WORKFLOW_OUTPUT_LEDGER_OK. Observed companion time5.391s;
workflow time1.922s. Initial attempts under low memory were refused. The retry
used improved available host RAM and unchanged production safeguards, with no
fixture, cloud call or owner-profile mutation. This remains one short English
brief, not sustained hardware or multilingual-quality acceptance.

The following records the earlier16November companion-only observation.

An actual Qwen2.5:0.5b model generated a reply through the authenticated Javo
companion, production resource manager, AI router and durable usage ledger.
The test used a fresh temporary profile and real host capacity, with no model
fixture or capacity override. It saved the provider configuration through the
real API, checked the model inventory, resumed only that isolated runtime,
generated text and restarted the runtime to verify persisted usage.

Observed result: REAL_LOCAL_MODEL_COMPANION_LEDGER_RESTART_OK;3.000seconds
for the synthetic one-sentence request,142 reported tokens. The reply was:
“Hello! Welcome to Javo. I'm glad you're here to meet some local artists.”
The ledger retained one successful request and the same token count after
restart. A separate direct Ollama smoke returned nonempty text in1.719seconds
with32 prompt/11 completion tokens. These are individual observations, not
repeatable latency guarantees or evidence of broad task quality.

The host had about8007MiB usable RAM and an Intel UHD620 adapter. No GPU
acceleration claim is made. Production CPU/RAM admission was left enabled.
This does not certify the full8GB baseline, sustained load, concurrency,
multilingual quality, safety, every specialist or larger RAM/GPU profiles.
The small model is an initial local smoke option, not a fixed upper capability
limit or a general recommendation for complex creator/engineering work.

The official standalone Ollama v0.40.16 Windows archive matched its published
SHA25650fcf5ad54277f2fa5d173ebfc93bcb017adbc0c9ef2314daabc96ca9e6aa64e.
Extraction paths/expanded size were checked; `ollama.exe` had a valid Windows
Authenticode signature for Ollama Inc. The model's reported digest was
a8b0c51577010a279d933d14c2a8ab4b268079d44c5c8830c0a93900f1827c67
and size397821319bytes. Binaries/model weights remain outside Git and source
checkpoints; no binary distribution was published.

The manually started service binds127.0.0.1:11434, with `OLLAMA_NO_CLOUD=1`,
one parallel request, one loaded model,2048 default context and30second idle
keep-alive. The log confirmed cloud features disabled. No Windows service,
autorun entry, global PATH change or paid provider was installed/activated.
The owner's existing Javo profile/settings were not used or overwritten for
acceptance. This does not attest to arbitrary user-hosted proxies or other
Ollama installations; verify their execution/privacy/cost policy separately.

To repeat against an existing local-only Ollama service and installed model:

```powershell
.\services\local-runtime\.venv\Scripts\python.exe scripts/verify-local-model.py --model qwen2.5:0.5b
# Include the actual saved/reviewed workflow path:
.\services\local-runtime\.venv\Scripts\python.exe scripts/verify-local-model.py --model qwen2.5:0.5b --workflow
```

The script does not download models. Insufficient real headroom fails the
check; do not weaken production safeguards to obtain a passing result.

Primary references: [Windows runtime](https://docs.ollama.com/windows),
[local-only mode/context/storage](https://docs.ollama.com/faq),
[model details and Apache2.0 license](https://ollama.com/library/qwen2.5:0.5b).
