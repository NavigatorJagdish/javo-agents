# Local AI Setup (Ollama + whisper.cpp + Piper + 8GB RAM Tuning)

Javo Agents runs **100% locally at $0 API cost** using Ollama for text/reasoning, `whisper.cpp` for Speech-to-Text, and `Piper` for Text-to-Speech. Refer to `models/manifests/ollama-8gb-profiles.json` for hardware-specific profiles.

---

## 1. Ollama Setup

1. Install Ollama for Windows from [ollama.com](https://ollama.com).
2. Pull the model recommended for your RAM tier:

| RAM Tier | Recommended Model | Footprint | Command |
| :--- | :--- | :--- | :--- |
| **8 GB (CPU-only)** | `qwen2.5:3b-instruct-q4_K_M` | ~2.3 GB | `ollama pull qwen2.5:3b-instruct-q4_K_M` |
| **8 GB Ultra-Light** | `gemma2:2b-instruct-q4_K_M` | ~1.7 GB | `ollama pull gemma2:2b-instruct-q4_K_M` |
| **16 GB (CPU/Hybrid)** | `qwen2.5:7b-instruct-q4_K_M` | ~4.9 GB | `ollama pull qwen2.5:7b-instruct-q4_K_M` |
| **32 GB+ (GPU)** | `qwen2.5:14b-instruct-q4_K_M` | ~9.2 GB | `ollama pull qwen2.5:14b-instruct-q4_K_M` |

---

## 2. 8 GB RAM Tuning Checklist

If your Windows PC has 8 GB RAM:
1. Set `JAVO_MAX_CONCURRENT_AGENTS=1` (or `2` max) in `services/local-runtime/.env`.
2. Set Ollama keep-alive short so memory frees quickly between tasks:
   ```powershell
   $env:OLLAMA_KEEP_ALIVE = "2m"
   $env:OLLAMA_NUM_PARALLEL = "1"
   ```
3. Close heavy browser tabs when running long video transcription + LLM generation simultaneously.
4. Use `q4_K_M` quantized models only; avoid `7b`+ models on 8 GB CPU-only machines.

---

## 3. Local Voice: whisper.cpp & Piper TTS

- **Speech-to-Text (`whisper.cpp`)**:
  - Recommended 8 GB model: `ggml-tiny.en-q5_1` (~140 MB) or `ggml-base-q5_1` for Hindi/Hinglish recognition.
- **Text-to-Speech (`Piper`)**:
  - Recommended voices: `en_US-lessac-medium` (English) and `hi_IN-rohan-medium` / `hi_IN-pratham-medium` (Hindi).
  - Configure paths in **Dashboard → Settings → Voice**.
