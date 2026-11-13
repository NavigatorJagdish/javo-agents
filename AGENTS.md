# JAVO AGENTS — REPOSITORY IMPLEMENTATION RULES
## Read before any AI-assisted coding change

**Canonical product contract:** [docs/JAVO_COMPLETE_ECOSYSTEM_MASTER_SPEC_v2.md](docs/JAVO_COMPLETE_ECOSYSTEM_MASTER_SPEC_v2.md)  
**Reality / progress ledger:** [docs/JAVO_IMPLEMENTATION_TRACEABILITY_MATRIX_v2.md](docs/JAVO_IMPLEMENTATION_TRACEABILITY_MATRIX_v2.md)
**Owner intent / explicit approvals / ordered work:** [docs/JAVO_OWNER_REQUIREMENTS_APPROVALS_EXECUTION_PLAN_v3.md](docs/JAVO_OWNER_REQUIREMENTS_APPROVALS_EXECUTION_PLAN_v3.md)  
**Prior reference (older strategic baseline):** JAVO_5_Projects_Master_Documentation.docx, 12 Nov 2026. When the old order of product releases conflicts with the newer owner-approved Android-first requirements, follow the v2 spec.

### Owner's non-negotiables
- Continue work in existing private NavigatorJagdish/javo-agents, existing Android applicationId com.javo.agents. No new Javo Agents APK identity/repo.
- Android Standalone mode must be genuinely useful without a Windows PC. Desktop/Cloud optional extensions.
- Primary UX is a natural Hindi/Hinglish conversational assistant, not a decorative multi-card statistics dashboard.
- Respect the explicitly selected AI provider. Keys/configured endpoints do not authorize silent fallback to other providers.
- The Master Agent and specialists must have actual runnable tool contracts, evidence, state, permissions and outputs. Do not confuse agent catalog entries, enabled preferences and real running jobs.
- **Never seed fake real-mode tasks, conversations, approvals, social connections, analytics or execution status.** Demo state opt-in and visibly separated.
- Social OAuth through official providers only. No password/cookie scraping; Facebook personal Profile manual share/export unless a legitimate provider API explicitly permits otherwise.
- All external writes, publishing, calls, financial, deletion and device-control actions require named destination preview and proper user authorization.
- Honor the user's free-first/local-first requirement but disclose hosted/API costs and limitations accurately.
- Preserve existing genuine Room data, encrypted credentials, migrations, signing continuity and rollback path.
- Keep repo/PR private and do not merge or publish public artifacts without explicit owner approval.

### Working cycle
1. Read the v2 master spec and locate the corresponding requirement ID.
2. Inspect the actual source, relevant tests, API contract, permissions, UI and real operating mode.
3. Implement the smallest complete end-to-end vertical slice; replace fake success states with honest errors.
4. Add positive and negative regression tests, especially voice error 11/13, false queued/posted, provider selection, sync idempotency and unauthorized approval.
5. Run Android lint/unit/build, backend tests, security and relevant front-end CI on the **exact new commit**.
6. When an actual APK is built, prove source SHA, versionCode, signing continuity, release asset ID and SHA-256.
7. Owner's physical-device testing and live Facebook/Instagram/YouTube provider results are **NOT VERIFIED** until actually run. Never infer them from CI.
8. Update the traceability matrix rows and changelog with exact evidence and outstanding blockers.

### Mobile voice
Support user-selected Hindi/Hinglish/English, real transcripts, cancel, finalization timeout and audible TTS. No fabricated utterance, silent command substitutions, or repeated mic loops. Hands-free must be explicitly started. Wake word / locked-screen background listening are advanced, OS-policy-bound features, not promises.

### Capability and connection badges
Use distinct statuses: PROPOSED, IMPLEMENTED, CONFIGURED, AVAILABLE, RUNNING, WAITING_APPROVAL, FAILED, VERIFIED, BLOCKED. The string "Connected" requires actual authenticated platform identity; "Synced" requires durable remote acknowledgement; "Published" requires verified platform receipt.

### Scope boundaries
The five planned product domains are Social AI, Agents Platform, Business, Voice/Jarvis and Studio, sharing Javo Core; Cloud is optional infrastructure. Separately discussed Javo Social Connector/Publisher and Javo ReVanced are not silently folded into the Agents APK.

**Do not claim the complete ecosystem is finished until real end-to-end user journeys pass on owner hardware and eligible external platforms.**
