# Javo ownership and third-party boundary

Owner requirement: preserve Javo's existing license and avoid integrating
components in a way that changes it. `LICENSE` remains the original MIT notice,
copyright2026 Javo Agents Contributors. No upstream code becomes Javo-owned by
being named in the catalog. Original adapter/template code follows the project's
license; existing separately licensed built-in manifests retain their notices.

The catalog records reference pins, README/license review and intended protocols,
not a complete source/security/legal audit of those repositories.

| Component | Treatment |
| --- | --- |
| n8n | Sustainable Use/Enterprise conditions; external-only, no runtime bundling |
| Claude Task Master | MIT + Commons Clause; external-only, no assumption of unrestricted commercial rights |
| ComfyUI | GPL runtime remains separately operated; no copied runtime/custom nodes or model weights bundled |
| sherpa-onnx/core | Reviewed2.0.1 speech path; legacy1.x carried GPL frontend components and is refused |
| Kokoro/Whisper | Optional externally stored model files with original notices/provenance; separate model terms require review |
| Other catalog references | Preserve their upstream license/notice requirements; no blanket approval of dependencies/models/services |

Upstream [issue3731](https://github.com/k2-fsa/sherpa-onnx/issues/3731) and
[mergedPR4055](https://github.com/k2-fsa/sherpa-onnx/pull/4055) describe removing
the old espeak/piper frontend in sherpa2. Javo uses its native lexicon frontend
and original pronunciation helper. No old espeak data is loaded or redistributed.

`scripts/check-distribution-license-boundary.py` checks the retained MIT notice,
reviewed engine version and, during runtime bundling, known restricted filenames
and model weights. It is a fail-closed technical gate for known cases, not a
complete license classifier. No commercial compatibility or immunity is promised.
Before distributing a paid build, review the exact final dependency inventory,
native-library notices, all chosen model terms and service agreements; ship their
required notices and obtain any required permissions. Do not interpret a remote
protocol connection as resolving all possible licensing obligations.
