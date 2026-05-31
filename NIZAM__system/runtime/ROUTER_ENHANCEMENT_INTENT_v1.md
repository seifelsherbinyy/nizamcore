# Intent router enhancement — Stage 1 design (paper only)

**Status:** TABLE APPROVED — Stage 1b/1c implemented locally (governor 1.11.2 + `nizam_router.py`); **no VPS deploy** until operator `/confirm router-stage-1`.  
**Held after router approval:** emotion/engagement-aware routing, web-research tool, cost-refinement.  
**Related merge:** `nizam/config-backup-20260531` @ `12ac8c7` (runtime config snapshot; governor plugin not in that PR).

---

## A. Operator confirmations (non-blockers)

### A1 — Extended mirror debounce (30s, wired from `_capture`)

**Staging code reviewed:** `NIZAM__system/hermes-plugins/nizam-governor/__init__.py` (`MIRROR_THROTTLE_SEC = 30`).

Current behavior is **leading-edge throttle only**:

1. Each `_capture` spawns `_mirror_ledgers_async()` → daemon thread.
2. Thread reads `last_mirror` timestamp; if `now - last < 30s`, it **returns without mirroring**.
3. On success it writes `last_mirror = now` and runs `rclone copy`.

**Gap:** There is **no trailing-edge timer**. If the last inbound of a session arrives and no further `_capture` fires after the throttle window elapses, a burst of captures can all be skipped and **never** flushed until the next session message (which may never come).

**Verdict for v1.11.1 as staged locally:** Cannot honestly confirm “quiet end of session still flushes.” Recommend **MIRROR-1** in the next governor patch (before or with router deploy):

- On each `_capture`, schedule/cancel a single `threading.Timer(30, _mirror_flush)` (daemon).
- Immediate mirror still allowed when `now - last >= 30` (keep coalescing under load).
- Timer fires once after quiescence → guaranteed final flush.

Operator VPS check after merge:

```bash
grep -n 'MIRROR_THROTTLE\|Timer\|pending_mirror\|mirror_due' ~/.hermes/plugins/nizam-governor/__init__.py
```

If the VPS copy already contains `Timer` / `pending_mirror`, say so and we’ll reconcile staging with live.

### A2 — v1.11.0 `.bak` swap discipline

**Local tree:** `plugin.yaml` declares `version: 1.11.1`; **no** `__init__.py.bak` or `__init__.py.v1.11.0` in the workspace (plugin deploy is VPS-local).

**Verdict:** Rollback artifact is **not verifiable from the merged PR** (`12ac8c7` is config-only). Operator confirmation on VPS:

```bash
ls -la ~/.hermes/plugins/nizam-governor/
# Expect: __init__.py (1.11.1) + __init__.py.bak or __init__.py.v1.11.0.bak from swap
```

---

## B. Why live misroutes differ from `router_dry_run.py`

| Layer | What routes today | Effect on your three cases |
|-------|-------------------|----------------------------|
| **Hermes governor P3** | `_active_persona()` → `Amin` unless `/shura` or `/naqd` mode flag | Free text → **Amin** capture voice (matches graduation + coffee live) |
| **SUKOON overlay** | `_sukoon_hot()` injects downshift context in `_pre_llm` | Can make **any** target *sound* like SUKOON even when `/pulse` logs biometrics |
| **`router_dry_run` / relay** | Exemplar Jaccard + `router.config.yaml` intents | Used in Phase-1 boot loop; **not** wired into live Hermes dispatch yet |
| **`/pulse` command** | Governor `_cmd_pulse` (BODY_LEDGER) | Works as command, but **not** in `router.config.yaml` `commands:` and does not set persona **Hayat** for follow-on turns |

Stage 1 closes the gap by making **deterministic intent → codename → governor persona activation** the single path for non-command and command traffic, with SUKOON as **tone overlay only** (IR-6).

---

## C. Eight intent-router refinements (IR-1 … IR-8)

| ID | Name | Rule (deterministic, pre-LLM) | Primary files |
|----|------|--------------------------------|---------------|
| **IR-1** | Command registry completeness | Slash-first messages resolve `router.config.yaml` `commands:` before exemplars; add `/pulse` → Hayat, `/dump` → Amin (mirror governor registrations). | `router.config.yaml`, `router_dry_run.py`, governor command hook |
| **IR-2** | Biometric utterance detector | Regex bundle: `recovery\|hrv\|strain` numeric triplet (with or without `/pulse`) → `biometric_log` → Hayat. | `router.config.yaml` `detectors.biometric`, exemplars |
| **IR-3** | Occasion tactical planning | `graduation\|wedding\|anniversary\|birthday` + `plan\|something special\|next month` → `tactical_plan` → Khalid (beats generic brainstorm). | `intent_exemplars.yaml#tactical_plan`, negative exemplars on `#brainstorm` |
| **IR-4** | Habit co-thinking (Salman) | `what do you think about` + lifestyle lexicon (`coffee\|caffeine\|sleep\|alcohol\|screen`) → `brainstorm` → Salman (not capture). | `intent_exemplars.yaml#brainstorm`, `capture` negatives |
| **IR-5** | Plan-vs-dump disambiguation | `plan\|prepare\|organize` without `/dump\|/tafrigh` → prefer tactical or brainstorm per IR-3/4; `random thought\|dump before I forget` → capture. | exemplars + `route_confidence.fallback_command` unchanged |
| **IR-6** | SUKOON overlay isolation | SUKOON downshift may append **tone** constraints only; **must not** change resolved `target` codename (Hayat stays Hayat). | `nizam-governor/__init__.py` `_pre_llm`, `sukoon_gate.py` docs |
| **IR-7** | Kinship + planning lane | Kin terms (`sister\|brother\|mother\|father`) + planning → Khalid unless `#ahel` / strict_local markers → Ammar/Yusra lane (no cloud). | exemplars, AHEL markers unchanged |
| **IR-8** | Confidence + confirm band | Commands = 1.0; detector hits ≥ 0.85 auto-route; 0.50–0.70 → single confirm prompt; `< 0.50` → `/tafrigh-capture`. | `router.config.yaml` `route_confidence` (already present) |

**Deploy unit (after approval):** `router.config.yaml`, `intent_exemplars.yaml`, `router_dry_run.py` (+ fixture rows), governor `_resolve_target()` + `_set_active_codename()` — **not** LLM-as-router yet.

---

## D. Before / after routing table (includes three live misroutes)

Legend:

- **Live (observed):** operator-reported Hermes behavior pre-enhancement.
- **Stdlib before:** `router_dry_run._match_intent` + current exemplars (local probe 2026-05-31).
- **After (paper):** deterministic IR-1…IR-8 resolver (no LLM).

| # | Input | Live (observed) | Stdlib before | After (paper) | Δ |
|---|--------|-----------------|---------------|---------------|---|
| **T1** | `my sister's graduation is next month — I want to plan something special` | **Amin** (capture loop) | **Salman** (brainstorm, conf ~0.17) | **Khalid** (tactical_plan, IR-3+IR-7) | T1: Amin→Khalid ✓ |
| **T2** | `/pulse recovery 60 hrv 45 strain 12` | **SUKOON** (recovery voice) | **Hayat** (biometric_log; command kind) | **Hayat** (IR-1 `/pulse` + IR-2; IR-6 blocks SUKOON persona swap) | T2: SUKOON→Hayat ✓ |
| **T3** | `what do you think about reducing coffee` | **Amin** (capture) | **Salman** (brainstorm, conf ~0.15) | **Salman** (IR-4 habit co-thinking) | T3: Amin→Salman ✓ |
| 4 | `Plan the next quarter.` | Amin likely | Khalid | Khalid | — |
| 5 | `HRV today was 38, sleep 7h.` | Amin / mixed | Hayat | Hayat | — |
| 6 | `Let me dump for 10 minutes about wealth.` | Amin | Salman | Salman | — |
| 7 | `PANIC: overload red, I can't breathe.` | crisis | protocol:crisis_sukoon_red | protocol:crisis_sukoon_red | — |
| 8 | `/shura-brainstorm Q3 wealth` | Salman | Salman | Salman | — |
| 9 | `Note about Dad's appointment Tuesday.` | Amin / Yusra? | Yusra | Yusra (or Ammar if strict_local) | — |
| 10 | `Random thought I want to dump before I forget.` | Amin | Amin | Amin | — |

**Approval gate:** T1, T2, T3 must show the **After** column targets in a re-run of `router_dry_run` (extended fixture) **and** in governor integration tests — still **no VPS deploy** until you sign off on this table.

---

## E. Staging plan (no deploy until approved)

| Stage | Deliverable | Deploy? |
|-------|-------------|---------|
| **1a** | This doc + extended `router_10_inputs.jsonl` (add T1–T3) | No |
| **1b** | Patch `intent_exemplars.yaml` + `router.config.yaml` (IR-1–IR-5, IR-7–IR-8) | No — PR for review |
| **1c** | Update `router_dry_run.py` detectors + governor `_resolve_target` / persona set | No — PR for review |
| **1d** | Operator re-runs dry-run; paste table | No |
| **2** | VPS deploy plugin + config after explicit `/confirm router-stage-1` | Yes |
| **3** | LLM-as-router (deepseek-v4-flash) | Held |
| **4** | Emotion/engagement-aware, web-research tool, cost-refinement | Held |

---

## F. Exemplar snippets (preview, not applied)

```yaml
# tactical_plan additions (IR-3)
- "my sister's graduation is next month — plan something special"
- "family event next month — need a plan"
- "anniversary coming up — want to organize something memorable"

# brainstorm additions (IR-4)
- "what do you think about reducing coffee"
- "what do you think about cutting caffeine"
- "thinking about changing my sleep routine — your take?"

# capture negatives (IR-4, IR-5)
capture:
  - "_negative: what do you think about"   # handled as metadata in matcher patch
```

```yaml
# router.config.yaml commands (IR-1)
commands:
  "/pulse": { target: Hayat, kind: COMMAND }
  "/dump":  { target: Amin,  kind: COMMAND }
```

---

## G. Verification commands (local, post-1b/1c)

```powershell
python D:\NIZAM\NIZAM__system\config\fixtures\router_dry_run.py
python D:\NIZAM\tools\t1_pre_egress_integration_test.py
```

---

*Generated 2026-05-31 — enhancement phase, router stage 1 only.*
