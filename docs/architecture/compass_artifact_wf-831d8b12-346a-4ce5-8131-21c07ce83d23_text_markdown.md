# Hermes → NIZAM Integration: Decision-Grade Research Report
*Research date: May 23, 2026. NIZAM repo: github.com/seifelsherbinyy/nizamcore. Local rig: RTX 3050 4GB / i5-12400 / 16GB DDR4-3200 single-channel.*

## 0. Executive Decision Snapshot

**Verdict: CONDITIONAL-GO — adopt the Nous Research stack as a managed-API inference layer, NOT as a local-inference layer. Build MVP against a hosted endpoint (OpenRouter or Nous Portal Plus). Reject local self-hosting of Hermes-class models on the current desktop. Defer multi-agent swarming until single-coordinator MVP is stable.**

- **BUILD NOW**: (1) thin Hermes adapter to NIZAM's LLM runtime that talks to Hermes 4 70B via OpenRouter (or Nous Portal Plus at $20/mo); (2) Telegram intake adapter with hard rate-limit guard; (3) Notion+Drive+GitHub dual-write governor wired to the existing confidence-threshold ledger.
- **DEFER**: native multi-agent swarm, fine-tuning, local inference for orchestration, agent-to-agent messaging fabric. Revisit after 60 days of MVP traffic data.
- **REJECT**: running Hermes 3/4 8B+ locally on the RTX 3050 4GB. Mathematically untenable — see §3.
- **Go/No-go criteria for promoting Phase 1 → Phase 2**: (a) MVP cost ≤ $50/month observed over 14 days; (b) Telegram intake p95 latency ≤ 5s; (c) auto-write rate (confidence ≥ 0.78) ≥ 60% on real intake; (d) dead-letter rate < 5%; (e) no prompt-injection incident.
- **Kill-switches**: (a) monthly spend hits $300 → pause non-essential agents, route to free-tier model; (b) monthly spend hits $500 → full pause + human review; (c) Notion 429 rate > 1%/hour for 30 min → fall back to local JSONL only; (d) Telegram 429 burst → drop to polling, queue with idempotency keys; (e) any strict_local data egress detected → halt all writers, raise alarm.

---

## 1. Hermes Identity Resolution & Source Map

"Hermes" overloads across at least four distinct artifacts. Decision rule applied: pick the candidate with strongest match to "agentic orchestration/inference for a personal optimization system." Winner: **Nous Research Hermes model family + the companion Hermes Agent framework** (both from the same org, MIT/Llama-licensed, with first-class function calling and a Telegram gateway).

### Candidate Identity Table

| # | Name | Owner | Repo / Docs | License | Type | Last update (as of May 2026) | Maturity | Relevance to NIZAM |
|---|---|---|---|---|---|---|---|---|
| A | **Nous Hermes 4 family** (14B Qwen3-base, 70B & 405B Llama-3.1-base, plus Hermes 4.3 36B on ByteDance Seed) | Nous Research | huggingface.co/NousResearch; arXiv 2508.18255 | Per-base-model: Llama 3.1 Community License for 70B/405B; Qwen license for 14B; weights on HF | Open-weight LLM with hybrid `<think>` reasoning + XML tool-call format | 70B & 405B FP8 released Sep 2025; 14B Jan 2025; 4.3 36B trained on Psyche decentralized network | Production-grade; supported by vLLM, SGLang, llama.cpp, LM Studio GGUF | **HIGH** — function calling, JSON mode, 128K context, hosted via OpenRouter/Together/Lambda |
| B | **Nous Hermes 3** (8B / 70B / 405B, Llama 3.1 base) | Nous Research | huggingface.co/NousResearch/Hermes-3-Llama-3.1-*; arXiv 2408.11857 | Llama 3.1 Community License | Open-weight LLM, full-parameter fine-tune, native XML `<tool_call>` | Aug 2024 (still served; OpenRouter shows $1/$1 paid + $0/$0 free tier on 405B) | Mature, widely deployed | **HIGH** — 8B is the smallest Hermes-class size; still doesn't fit 4GB at usable quality |
| C | **OpenHermes / Hermes 2 Pro** (older Mistral/Llama-3-8B fine-tunes) | Nous Research (community-mirrored) | huggingface.co/NousResearch/Hermes-2-Pro-Llama-3-8B | Llama 3 Community License | Open-weight LLM | 2024 (superseded) | Stable but legacy | **MEDIUM** — reference for function-calling prompt format |
| D | **Hermes Agent framework** | Nous Research | github.com/NousResearch/hermes-agent; hermes-agent.nousresearch.com/docs | MIT (per README) | Self-improving CLI agent with Telegram/Discord/Slack/WhatsApp/Signal/Email gateway, 40+ tools, learning loop, runs on a $5 VPS | Mar 2026 launch; OpenRouter Apps board ranks it #1 in Personal Agents | New but active; Native Windows beta only, WSL2 recommended | **HIGH but partly redundant** — overlaps with NIZAM's planned orchestration; borrow patterns, don't adopt wholesale |
| E | "Hermes" message bus / RPC frameworks (e.g., Hermes RPC, IBM/telecom Hermes) | Various | Multiple | Various | Generic name collision | n/a | n/a | **LOW** |
| F | **NIZAM HERMES agent** (Seif's own ARES v2.0 codename) | Seif Elsherbiny | Private; conceptual hat | n/a | Internal codename, NOT a public product | Internal | Concept-only | **CRITICAL DISAMBIGUATION** — rename/namespace to avoid collision |

**Chosen interpretation** for this report: "Hermes" = Nous Hermes model family (primarily **Hermes 4 70B** as cost-quality sweet spot; **Hermes 3 8B** as the only realistic local fallback) plus evaluation of whether NIZAM should borrow patterns from the Hermes Agent framework. The user's internal HERMES codename is referred to as "ARES-HERMES" here to avoid ambiguity.

**ASSUMPTION**: ARES-HERMES is the *role*, not the substrate. External Hermes provides the inference substrate that ARES-HERMES and the other seven NIZAM agents ride on.

---

## 2. Hermes Capability Research

### 2.1 Tool / function calling
- **Native XML tool-call schema** (`<tool_call>{"arguments":..., "name":...}</tool_call>` paired with `<tool_response>`), trained as added special tokens for stream-time parsing. Source: NousResearch/Hermes-3-Llama-3.1-405B HF model card.
- vLLM and SGLang ship Hermes-specific tool parsers (`--tool-call-parser hermes` in vLLM; `qwen25` parser in SGLang for Hermes 4 14B). Source: Hermes 4 model cards.
- Reference repo: github.com/NousResearch/Hermes-Function-Calling — 1.2k stars, 148 forks. Ships `functioncall.py` with recursion loop, max_depth, validation, and tool_response error feedback.
- Hermes 4 adds hybrid `<think>...</think>` segments toggled via system prompt or `thinking=True` chat-template flag.

### 2.2 Context length
- All Hermes 3 sizes inherit Llama 3.1's 131,072-token context. Confirmed on OpenRouter model cards.
- Hermes 4 70B and 405B: same 131K. Hermes 4 14B: 131K (Qwen 3 14B base).
- Hermes 4.3 36B model card does not explicitly state extended context; must be verified per use case (STALE risk, flagged).

### 2.3 Quantization & memory
- Hermes 3 405B FP16 > 800 GB VRAM; FP8 (NeuralMagic) ≈ 430 GB (cluster-only).
- Hermes 3 70B at Q4_K_M ≈ 40 GB VRAM (dual 24 GB or A100/H100).
- Hermes 3 8B at Q4_K_M ≈ 4.9 GB on disk; needs ~6–7 GB usable VRAM at 4K context with KV cache. **Does NOT fit a 4 GB card with reasonable context.**
- Hermes 3 Llama-3.2-3B at Q4_K_M ≈ 2.0 GB — the only realistic local option, but weaker on tool calling. Source: bartowski/Hermes-3-Llama-3.2-3B-GGUF model card.

### 2.4 Benchmark claims (primary sources)
- **Hermes 4 Technical Report (arXiv 2508.18255, Teknium et al., 25 Aug 2025)**: "We comprehensively evaluate across mathematical reasoning, coding, knowledge, comprehension, and alignment benchmarks." Evaluation suite includes MATH-500, AIME'24/25, GPQA Diamond, LiveCodeBench, BBH, MMLU, MMLU-Pro, SimpleQA, IFEval, Arena-Hard, RefusalBench, RewardBench, DROP, MuSR, OBQA, EQBench3, CreativeWriting3.
- **Independent Artificial Analysis** (artificialanalysis.ai): Hermes 4 405B (non-reasoning) scores **18 on the Artificial Analysis Intelligence Index v4.0**, below the open-weight median of 23; 34 tok/s output (median 52); TTFT 2.46s. The page concludes Hermes 4 405B is "below average in intelligence and particularly expensive when comparing to other open weight non-reasoning models of similar size." **MIXED signal** — Nous's own report numbers are stronger, but independent re-eval pushes back.
- **Hermes 4.3 36B model card (NousResearch HF)**: MATH-500 93.8%, MMLU 87.7%, BBH 86.4%, AIME 24 71.9%, GPQA Diamond 65.5%, RefusalBench 74.6% (vs 59.5% Hermes 4 70B). Note: vendor-reported, no independent reproduction yet.
- **MISSING**: a primary-source BFCL (Berkeley Function Calling Leaderboard) number for any Hermes model. The Hermes 4 report does not list BFCL. **Flag as ASSUMPTION** that function-calling quality is at parity with Llama 3.1 Instruct until a published BFCL score is found.

### 2.5 Extensibility, licensing, maintenance
- **Licensing**: Hermes 3 weights are downstream of the **Llama 3 Community License** per the HF model cards' legal block. Hermes 4 14B inherits the **Qwen 3 license**. The `Hermes-Function-Calling` repo carries the repo-default license (not verified against the LICENSE file in this round — listed in §12.3 unresolved). **Hermes Agent framework is MIT** per README.
- **Maintenance activity**: Hermes 4 series shipped Sep 2025; Hermes 4.3 36B added late 2025 / early 2026 (first Hermes trained on the Psyche decentralized network per Nous blog). Hermes Agent OpenRouter listing reports "Active since Mar 2026", "Models used 350", "Total tokens 8.56T" — high traffic but very young.
- **Community / social cross-check**:
  - Reddit r/LocalLLaMA, HN, and X: Hermes 3 has had broad positive uptake for function calling and steerability; Teknium (@Teknium1) posted Nous Portal tier pricing on X (Plus $20 / Super $100 / Ultra $200) at x.com/Teknium/status/2047442402303226174.
  - GitHub Hermes-Function-Calling: 1.2k stars, 148 forks.
  - Critical caveat: Nous Portal itself states "The Hermes 4 series of models are not recommended for use in Hermes Agent. For Hermes Agent, configure an agentic model" — implying Hermes 4 is tuned for reasoning, not for tightly-controlled agent loops. **Material for NIZAM.**

### 2.6 Capability Confidence Matrix

| Capability | Hermes 3 8B | Hermes 3 70B | Hermes 4 70B | Hermes 4 405B | Hermes 4.3 36B | Hermes Agent fw |
|---|---|---|---|---|---|---|
| Native function calling | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED |
| OpenAI-compatible API serving | CONFIRMED (vLLM/SGLang) | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED (any provider) |
| 128K context | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED | LIKELY (model card silent on extended ctx) | n/a |
| Local on 4GB VRAM | REJECTED (≈4.9 GB Q4 + KV) | REJECTED | REJECTED | REJECTED | REJECTED | n/a |
| Multi-agent native | MISSING | MISSING | MISSING | MISSING | MISSING | LIKELY (subagents + scheduled automations + 40+ tools) |
| Telegram integration | n/a (model layer) | n/a | n/a | n/a | n/a | CONFIRMED (built-in gateway) |
| Active maintenance | LIKELY | LIKELY | CONFIRMED | CONFIRMED | CONFIRMED | CONFIRMED (rapid Mar–May 2026) |
| Function-calling BFCL score | MISSING | MISSING | MISSING | MISSING | MISSING | n/a |
| Cost on OpenRouter | $0/$0 free-tier & $1/$1 paid 405B | n/a (no separate H3-70B listing surfaced) | **$0.13/$0.40** | **$1.00/$3.00** | n/a | n/a |
| Independent Intel Index | n/a | n/a | n/a | 18 (MIXED — below avg) | n/a | n/a |
| Refusal/steerability | CONFIRMED neutral | CONFIRMED neutral | CONFIRMED neutral | CONFIRMED neutral | SOTA RefusalBench 74.6% | n/a |

---

## 3. Deployment Model Comparison

### 3.1 Local on the actual hardware — HARD-FLAGGED

Desktop: RTX 3050 4GB GDDR6 / i5-12400 / 16GB DDR4-3200 single-channel. The 4GB VRAM ceiling is binding.

What can actually run locally (per llama.cpp / Ollama community benchmarks):
- **Hermes 3 Llama-3.2-3B Q4_K_M ≈ 2.0 GB on disk**: fits with ~1 GB headroom for a 2–4K context KV cache. **Estimated 15–30 tok/s output (memory-bandwidth-scaling estimate; no published RTX 3050 desktop 3B benchmark found as of May 2026, ESTIMATED).** Quality: a 3B will not match Hermes 4 70B on multi-step tool calling — community guides note 3B-class for the 4GB tier is for "simple Q&A, light coding, summarization" only.
- **Hermes 3 8B Q4_K_M (~4.9 GB)**: does NOT fully fit. CPU offload through DDR4-3200 single-channel (~25.6 GB/s) caps the 8B at **≈5 tok/s ceiling** (consistent with localscore.ai's RTX 3050 Laptop 4GB Llama 3.1 8B Q4_K_M reading of 4.8 tok/s even with full GPU offload on the laptop variant).
- **Anything ≥14B**: not feasible.

**Local verdict**: REJECT local hosting of Hermes for NIZAM's orchestration role. A 3B can be useful for narrow ARES-HERMES classification triage (e.g., Warden intake tagging) but the coordinator and any agent that emits structured plans/tool calls must run against a hosted endpoint. Keep a local 3B GGUF as a **strict-local privacy fallback** for offline/sensitive intake only.

### 3.2 Deployment table (pricing dated late May 2026)

| Option | Setup complexity | Baseline monthly cost | Latency (TTFT / tok/s) | Privacy | Failure modes | Scaling path | Confidence |
|---|---|---|---|---|---|---|---|
| **Local on RTX 3050 4GB (3B model)** | Med (Ollama + llama.cpp) | $0 (electricity ~$3–6) | <1s / 15–30 tok/s (ESTIMATED) | Strongest (no egress) | Quality cliff, no >3B, KV exhaust at long context | Hardware swap only | CONFIRMED tradeoffs |
| **Cloud CPU VM (Hetzner CX22, DigitalOcean droplet)** | Low | $5–10 (Hermes-Agent README cites $5 VPS as viable host for the framework, NOT for model inference) | n/a | Med | Single point of failure | Vertical | CONFIRMED ($5 VPS) |
| **Cloud GPU VM (RunPod Community Cloud A100 80GB)** | Med | A100 ≈ $1.04–$1.99/hr per Mar–Apr 2026 sources → $750–1,400/mo at 24/7. At 4 hr/day on-demand: ~$125–240/mo | <0.5s / 80–120 tok/s on Hermes 3 70B Q4 | Med | Pod can vanish (Community Cloud), checkpoint required | Switch to Secure Cloud | LIKELY |
| **GPU rental — Vast.ai marketplace** | High (Docker, persistence) | A100 80GB ≈ $0.67/hr; 4 hr/day → ~$80/mo | <0.5s / 80–120 tok/s | Lower (community hosts) | Host disappearance | Re-rental | LIKELY |
| **GPU rental — Lambda Labs on-demand** | Low | A100 80GB $1.29/hr; H100 $2.99/hr. 4 hr/day ≈ $155–360/mo | <0.5s | Med | Availability spikes, no spot | Reserved 15–30% discount | CONFIRMED |
| **Managed API — OpenRouter (Hermes 4 70B)** | Lowest | **$0.13/M input + $0.40/M output**. NIZAM target volumes (§8): $5–60/mo | TTFT ~1–3s, 30–60 tok/s across providers | Med (per-provider policy) | Provider down → fallback model | Switch with one config | CONFIRMED |
| **Managed API — OpenRouter (Hermes 4 405B)** | Lowest | **$1.00/M input + $3.00/M output** | TTFT 2.46s, 34 tok/s median (Artificial Analysis) | Med | Same | Same | CONFIRMED |
| **Managed API — Nous Portal Free** | Lowest | $0/mo, $0.10 monthly credits | Same as OpenRouter underlying | Med | Rate-limit-bound; Stripe required even for free | Upgrade | CONFIRMED |
| **Managed API — Nous Portal Plus** | Lowest | **$20/mo + $22 credits + 10% bonus + $10 rollover; access to 300+ models + Tool Gateway (web search / image / TTS / browser)** | Same | Med | n/a | Upgrade to Super/Ultra | CONFIRMED |
| **Managed API — Nous Portal Super / Ultra** | Lowest | **$100 / $200 monthly** ($110 / $220 credits, $50 / $100 rollover) | Same | Med | n/a | n/a | CONFIRMED |
| **Managed API — Together.ai (Llama family; Hermes not first-party)** | Low | Llama 3.3 70B ~$0.88/$0.88 per M; H100 dedicated $3.99/hr; ZDR mode available | TTFT <0.5s, 100–150 tok/s commodity | Med | Rate limits at peak | Dedicated endpoints | CONFIRMED |
| **Managed API — DeepInfra (Hermes 3 / Llama)** | Low | Llama 3.3 70B $0.23/$0.40 per Apr 2026 AI Pricing Guru | Variable | Med | Smaller community | n/a | LIKELY |
| **Hybrid: managed API primary + local 3B for strict-local + cloud GPU for fine-tune jobs** | High | $20–60/mo steady + occasional $5–20 GPU bursts | Best for hot path | Best for sensitive items | Multiple failure surfaces — needs router | Mature | RECOMMENDED |

**Recommendation**: **Hybrid with managed API primary (Hermes 4 70B via OpenRouter or Nous Portal Plus) and a local 3B fallback for strict_local data**. Lambda/RunPod only for batch fine-tune or one-off scale tests.

---

## 4. Multi-Agent / Swarm Feasibility

### 4.1 Does Hermes have native multi-agent support?
- **Hermes model family**: NO native multi-agent layer. They are LLMs with strong function calling.
- **Hermes Agent framework**: YES — built-in subagents, scheduled automations, 40+ tools, learning loop, multi-channel gateway. But: it is **young** (Mar 2026 launch), Windows native is "early beta" (WSL2 recommended), and it overlaps with NIZAM's existing 8-hat architecture. Wholesale adoption would replace NIZAM's dual-write governor and ledger semantics — high migration cost, loss of strict_local invariants.

### 4.2 Wrapper evaluation (weighted decision matrix)

Criteria weights from prompt: cost 25 / reliability 20 / privacy 15 / impl speed 15 / maintainability 15 / scalability 10. Scores 1–5.

| Framework | Cost | Reliability | Privacy | Impl speed | Maintainability | Scalability | Weighted |
|---|---|---|---|---|---|---|---|
| Hand-rolled Python coordinator (asyncio + Redis-lite or SQLite queue) | 5 | 4 | 5 | 4 | 4 | 3 | **4.20** |
| **LangGraph** (state machine, checkpointing, LangSmith trace) | 4 | 5 | 4 | 3 | 4 | 5 | **4.20** |
| CrewAI | 4 | 3 | 4 | 5 | 3 | 3 | 3.65 |
| AutoGen / Microsoft Agent Framework | 3 | 4 | 3 | 3 | 4 | 4 | 3.50 |
| Hermes Agent (adopt wholesale) | 4 | 3 | 2 | 5 | 3 | 4 | 3.45 |
| Temporal / Prefect / Celery (workflow engines) | 3 | 5 | 4 | 2 | 5 | 5 | 3.95 |
| Ray Serve | 2 | 5 | 4 | 2 | 4 | 5 | 3.45 |

Note: AutoGen itself is now in maintenance mode — per github.com/microsoft/autogen README (May 2026): "AutoGen is now in maintenance mode. It will not receive new features or enhancements and is community managed going forward. New users should start with Microsoft Agent Framework." (VentureBeat, Emilia David, Oct 1, 2025: "Microsoft retires AutoGen and debuts Agent Framework to unify and govern enterprise AI agents.")

**Recommendation**: **Tie between hand-rolled and LangGraph at 4.20.** Decision rule:
- **MVP (Phase 1, weeks 1–4)**: hand-rolled coordinator with a single Hermes coordinator + 1–2 specialists (Warden + Scribe), SQLite ledger, idempotent retries. Reason: NIZAM already has the conceptual hats and confidence thresholds — minimum framework risk.
- **Phase 2 (weeks 5–10)**: migrate the coordinator to LangGraph **only if** observed needs include conditional branching, time-travel replay, or persistent multi-step state.
- **Phase 3 (later)**: revisit Hermes Agent framework as a *reference codebase* — borrow patterns (gateway, learning loop, skills) rather than adopt whole.

MVP topology: **Coordinator + max 2 specialists + task budget per request (default 3 tool calls, hard cap 7) + append-only message ledger + 30s timeout + 3-retry exponential backoff [1, 4, 16] s** (matches NIZAM's existing retry_policy).

---

## 5. Learning Loop Architecture

**Pattern: HYBRID — centralized ledger + per-agent local cache + retrieval-based learning. No model fine-tuning in Phase 1 or 2.**

```
Telegram /dump
      │
      ▼
+--------------------+      +----------------------+
| Warden (intake)    |─────▶| Local JSONL buffer   |
| - Bot API webhook  |      | strict_local/intake  |
| - HMAC verify      |      | (gitignored)         |
+--------------------+      +----------+-----------+
                                       │
                                       ▼ async
                              +--------+--------+
                              | Scribe (classify| ◀── Hermes 4 70B (managed)
                              | + structure)   |
                              +--------+--------+
                                       │
                       confidence ≥ 0.78 ──┐
                                       │   │ 0.55–0.77      < 0.55
                                       ▼   ▼                 ▼
                              ┌──────────────────┐   ┌──────────────┐
                              | Steward dual-    |   | Dead-letter  |
                              | write governor   |   | queue        |
                              | Notion+Drive+GH  |   +──────────────┘
                              +────────┬─────────┘
                                       │
                                       ▼
                              ┌────────────────────┐
                              | Embedding + RAG    |
                              | index (sqlite-vss /|
                              | FAISS, local)      |
                              +────────┬───────────┘
                                       │
                                       ▼
                              ┌────────────────────┐
                              | /learn /feedback   |
                              | logs → re-tag and  |
                              | re-embed nightly   |
                              +────────────────────┘
```

- **Centralized vs distributed**: durable state strictly centralized in the NIZAM ledger (per repo spec: "NIZAM is the single source of truth"). Agents may cache **read-only** locally.
- **Feedback target**: < 1 hour from `/feedback` to retrieval re-rank. Implementation: emit feedback row → nightly batch re-embed (NOT real-time fine-tune); reflect tag changes in vector metadata immediately.
- **RAG failure modes**: (a) embedding drift after model swap → version every embedding row, rebuild on model change; (b) stale context bleed → TTL on cache entries; (c) hallucination from low-confidence retrievals → top-k similarity floor (e.g., cosine ≥ 0.32) and route to dead-letter on no hit; (d) prompt-injection via retrieved docs → wrap retrieved text in `<retrieved>…</retrieved>` fenced delimiters and instruct the model to ignore embedded directives (still imperfect — see §10).
- **No fine-tuning** until Phase 3 and only if (a) retrieval cost > $50/mo, (b) labelled dataset ≥ 5k clean rows, (c) privacy review passed.

---

## 6. NIZAM Context Injection & Storage Backend Design

NIZAM's existing dual-write governor is fundamentally sound. Relevant external constraints:

| Backend | Limit / pricing (current) | Use in NIZAM |
|---|---|---|
| **Notion API** | **3 requests/sec average per integration, HTTP 429 with Retry-After**, 1000-block ceiling per page, 100 blocks per write. Same limit on all plans. Source: developers.notion.com/reference/request-limits. | Structured rows only; never bulk imports. Hard token-bucket pacing in Steward. |
| **Google Drive API** | 1,000 queries/100s/user default; folder ID `1N_Cx5i4UPxp7qkCb6WxA3TYPgion4RUi` is the canonical narrative store | Narrative blobs. Exponential backoff and resumable uploads. |
| **GitHub** | 5000 REST req/hr authenticated; commit-and-push for audit | Append-only commit ledger. |
| **Local JSONL ledgers** | filesystem only | strict_local (gitignored). Never commits, never egresses. |
| **Vector DB (recommended addition)** | sqlite-vss or DuckDB-VSS local, $0; or pgvector on a $5 VPS | Local-first retrieval; no third-party DB until volume warrants. |
| **Hot cache** | in-process LRU + on-disk SQLite | Per-agent ephemeral state |

**Design rules**:
- Every durable write goes through Steward and produces: provenance (source agent, confidence, model name, model version hash), immutable hash, rollback pointer (previous-hash chain).
- Notion is the rate-limit-binding system. Build Steward as a **token-bucket writer at 2 req/s** (below the 3/s ceiling; Notion practitioners note edit requests take time to settle and recommend throttling further).
- Don't put structured logs into Notion — that goes to local JSONL + GitHub commit. Notion is for human-readable rows the user actually opens.
- **Schema versioning**: every JSONL line carries `schema_version` and `nizam_commit_sha`. Rollback = revert to a prior commit + replay ledger from a snapshot.

---

## 7. Telegram Integration

### 7.1 Verified official limits (correcting the prompt)

| Limit | Value | Source |
|---|---|---|
| Per-bot global broadcast | **30 messages/second** | core.telegram.org/bots/faq: "The API will not allow bulk notifications to more than ~30 users per second" |
| Per-chat | "Avoid sending more than 1 message per second" in a given chat | core.telegram.org/bots/faq |
| Per-group | "Bots cannot send more than 20 messages per minute to the same group" | core.telegram.org/bots/faq |
| Paid broadcast (opt-in via @BotFather) | Up to **1000 messages/second**, 0.1 Stars per excess message; minimum balance required | core.telegram.org/bots/api |

**The prompt's "100 msgs/sec" claim is INCORRECT.** Official ceiling is 30/sec free or 1000/sec via paid broadcast — there is no 100/sec tier in official Telegram docs. Update NIZAM docs.

### 7.2 Webhook vs polling
- **Webhook in production** (push, single SSL endpoint, no idle polling cost). HTTPS cert required; webhook secret token (`X-Telegram-Bot-Api-Secret-Token`) MUST be validated server-side.
- **Long-polling fallback** for local dev or when webhook endpoint is down (offset-based confirmation via `getUpdates`).

### 7.3 Security
- Store TELEGRAM_BOT_TOKEN in OS keyring or an `.env` outside the repo tree.
- Validate webhook origin via secret token + optional Telegram IP allowlist.
- Every inbound message is **untrusted user input**. Wrap in `<user_message>` fenced delimiters; instruct the model to ignore instructions inside; never execute tool calls derived from quoted user text without `/confirm`.
- No scraping private Discord/Facebook content. Only respond to user-initiated messages on the user's own bot.

### 7.4 Command routing (proposed)

| Command | Behavior |
|---|---|
| `/dump <text>` | Append to Warden intake JSONL; ack immediately, classify async |
| `/learn <fact>` | Add to learning index with manual confidence = 0.95 |
| `/feedback <id> <up|down> [note]` | Mark prior auto-write correct/incorrect; trigger re-rank |
| `/status` | Last 24h: intake count, auto-write rate, dead-letter count, spend YTD |
| `/cost` | Spend today / month-to-date / projection vs $300 baseline & $500 hard warning |
| `/route <agent>` | Force next message to a specific hat (debug only) |
| `/digest` | Trigger Almanac weekly review |
| `/pause [agent|all]` | Kill-switch — sets Guardrail flag, halts writers |
| `/resume [agent|all]` | Clears Guardrail flag after manual confirm |

### 7.5 Queue / backoff / idempotency
- Use Telegram's `update_id` as **idempotency key** on intake. Dedup before any side effect.
- Outbound token-bucket at 25/sec global (safety margin below 30) and 1/sec per chat. On HTTP 429: honor `retry_after` + 10% jitter (per the GramIO recipe). Never retry without bucket pause.

---

## 8. Cost Model (24-Month Scenarios)

### 8.1 Assumptions

- **Hermes 4 70B via OpenRouter** = $0.13/M input + $0.40/M output.
- **Hermes 4 405B via OpenRouter** = $1.00/M input + $3.00/M output.
- **Nous Portal Plus** = $20/mo flat + $22 credits + Tool Gateway included.
- **Claude Sonnet 4.6** = $3/$15 per M (comparison only; current Anthropic-listed pricing for Sonnet 4.6, released Feb 17, 2026).
- **DeepSeek V4 Flash** = $0.14/M input + $0.28/M output per api-docs.deepseek.com (May 2026); cache-hit input drops 10× to $0.014/M. Note: V3.2 is deprecated on the official API and only surfaces on aggregators like OpenRouter ($0.252/$0.378).
- **Notion / Drive / GitHub**: $0 at NIZAM volumes.
- **Context multiplier (RAG)**: 2.5× baseline input tokens.
- **Sub-agent multiplier**: MVP 2 agents = 2×; Phase 2 with 4 agents = 4×; Phase 3 full swarm = up to 7×.
- **Retry overhead**: +15% (3 attempts, 85% one-shot success).
- **Failed-run waste**: 8% of tokens on dead-letter / discarded output.
- **GPU idle (RunPod stress case)**: 50% idle.

### 8.2 Scenarios (monthly $; Hermes 4 70B managed unless noted)

| Scenario | Messages/day | Avg tokens/msg (in/out) | Agent mult | Eff. monthly input M | Eff. monthly output M | Hermes 4 70B (OR) | Hermes 4 405B (OR) | Nous Portal Plus | Claude Sonnet 4.6 |
|---|---|---|---|---|---|---|---|---|---|
| **Low** | 10 | 600 / 400 | 2 | 0.90 | 0.24 | $0.21 | $1.62 | $20 (covered) | $6.30 |
| **Baseline** | 50 | 800 / 600 | 2 | 6.0 | 1.8 | $1.50 | $11.4 | $20 (covered) | $45 |
| **High** | 200 | 1200 / 900 | 4 | 72 | 21.6 | $18.0 | $136.8 | $20 + small overage | $540 (over $300 ceiling) |
| **Stress** | 500 | 1500 / 1200 | 7 | 393 | 126 | **$101.4** | $769.2 | Plus insufficient → Super $100 + overage | $2,069 |

### 8.3 Sensitivity (applied to Baseline on Hermes 4 70B)

| Factor flipped | New monthly cost |
|---|---|
| Tokens +50% | $2.25 |
| Context ×3 | $5.40 |
| Agents ×7 | $5.25 |
| Retries +20% | $1.80 |
| GPU idle 50% (only applies if self-host) | n/a — managed |
| All four sim. | ~$33 |

### 8.4 Breakeven analysis (managed API vs self-hosted)
- 24/7 cloud H100 at $2.39/hr ≈ **$1,720/mo**. Breakeven against Hermes 4 70B Baseline ($1.50/mo) requires >1100× current load — i.e., never at personal scale.
- Even at Stress ($101/mo), managed wins by ~17× vs 24/7 H100.
- Spot RunPod A100 80GB at ~$1.04/hr × 4 hr/day = ~$125/mo — only attractive for fine-tuning, not steady inference.
- **Conclusion**: managed API dominates at any NIZAM-realistic load. Self-host only for periodic fine-tune jobs (Phase 3).

### 8.5 Recommended cost guardrails
- Soft alert: **$50/mo** (3× baseline).
- Stage-1 throttle: **$150/mo** — disable non-essential agents (Pulse, Witness drift to local 3B).
- Stage-2 throttle: **$300/mo** (baseline ceiling) — pause auto-write, manual review only.
- Hard stop: **$500/mo** — Guardrail kill-switch + human confirm before any further spend.

---

## 9. Confidence Ledger

Rubric: start 0; +35 official docs; +20 repo/release; +15 reproducible benchmark; +10 repeated GitHub issues; +10 social corroboration across 2+ platforms; −20 contradictory reports; −15 stale source >18 months; −25 missing primary evidence. Map: 80–100 CONFIRMED, 60–79 LIKELY, 40–59 MIXED/ESTIMATED, 20–39 ANECDOTAL, 0–19 MISSING.

| # | Claim | Sources | Score | Label |
|---|---|---|---|---|
| C1 | Hermes 4 70B & 405B are Llama-3.1 fine-tunes from Nous Research, hybrid reasoning with `<think>` tags | HF model cards, arXiv 2508.18255, hermes4.nousresearch.com | 90 | CONFIRMED |
| C2 | Hermes 4 70B priced $0.13/M input, $0.40/M output on OpenRouter | openrouter.ai/nousresearch/hermes-4-70b | 85 | CONFIRMED |
| C3 | Hermes 4 405B Artificial Analysis Intel Index = 18 (below median) | artificialanalysis.ai/models/hermes-4-llama-3-1-405b | 80 | CONFIRMED |
| C4 | Hermes 3 8B Q4_K_M ≈ 4.9 GB on disk; needs ~6–7 GB VRAM with KV cache | bartowski HF GGUF model card; sitepoint.com; localllm.in | 85 | CONFIRMED |
| C5 | RTX 3050 4GB cannot host any 8B+ Hermes at usable speed (8B Q4_K_M ≈5 tok/s ceiling per localscore.ai laptop variant + CPU-spill math) | techreviewer.com (RTX 3050 LLM); localllm.in; apxml.com calculator; localscore.ai | 80 | CONFIRMED |
| C6 | Telegram free Bot API: 30 msgs/sec global; 1/sec per chat; 20/min per group | core.telegram.org/bots/faq, core.telegram.org/bots/api | 95 | CONFIRMED |
| C7 | Telegram paid broadcast: up to 1000 msgs/sec, 0.1 Stars per excess message | core.telegram.org/bots/api | 90 | CONFIRMED |
| C8 | Prompt's "100 msgs/sec" claim is NOT in official Telegram docs | absence + multiple official pages | 80 | CONFIRMED (corrected) |
| C9 | Notion API rate limit = 3 req/sec avg per integration; 429 + Retry-After | developers.notion.com/reference/request-limits | 95 | CONFIRMED |
| C10 | Nous Portal tiers: Plus $20, Super $100, Ultra $200 with 10% bonus credits and Tool Gateway | portal.nousresearch.com/manage-subscription; x.com/Teknium/status/2047442402303226174 | 85 | CONFIRMED |
| C11 | Hermes Agent framework is MIT-licensed, Mar 2026 launch, native Telegram gateway | github.com/NousResearch/hermes-agent README | 80 | CONFIRMED |
| C12 | Hermes 4 is "not recommended for use in Hermes Agent — configure an agentic model" | portal.nousresearch.com/info | 75 | LIKELY (vendor-stated) |
| C13 | Hermes-Function-Calling repo: 1.2k stars, 148 forks | github.com/NousResearch/Hermes-Function-Calling | 80 | CONFIRMED |
| C14 | RunPod A100 80GB ≈ $1.04–$1.99/hr Apr 2026; Vast.ai cheaper at $0.67/hr | runpod.io/pricing; computeprices.com; Medium price tracker Feb 14 2026 | 75 | LIKELY |
| C15 | Lambda Labs H100 on-demand $2.99/hr; A100 80GB $1.29–$2.49/hr | lambda.ai/pricing; gpuperhour.com; checkthat.ai | 80 | CONFIRMED |
| C16 | DeepSeek V4 Flash $0.14/$0.28 per M (current official API); V3.2 deprecated on official API but $0.252/$0.378 still on OpenRouter | api-docs.deepseek.com/quick_start/pricing; openrouter.ai/deepseek/deepseek-v3.2 | 85 | CONFIRMED (corrected) |
| C17 | Claude Sonnet 4.6 $3/$15 per M (released Feb 17, 2026) | platform.claude.com/docs/en/about-claude/pricing; anthropic.com/claude/sonnet | 90 | CONFIRMED |
| C18 | NIZAM spec (8 hats, dual-write governor, thresholds 0.78/0.55, retry [1,4,16] s) | user-supplied repo description | 100 | CONFIRMED (by user) |
| C19 | AutoGen in maintenance mode; Microsoft Agent Framework is successor | github.com/microsoft/autogen README (May 2026): "AutoGen is now in maintenance mode … New users should start with Microsoft Agent Framework"; VentureBeat (Emilia David, Oct 1, 2025): "Microsoft retires AutoGen and debuts Agent Framework to unify and govern enterprise AI agents" | 85 | CONFIRMED |
| C20 | BFCL function-calling score for any Hermes model | none found in primary sources searched | 5 | **MISSING** — required before any claim Hermes outperforms peers on tool calling |
| C21 | Hermes 4.3 36B benchmark scores (MATH-500 93.8, MMLU 87.7, etc.) | NousResearch/Hermes-4.3-36B HF model card | 65 | LIKELY (vendor-reported, no independent reproduction) |
| C22 | Hermes 4 405B independent Intel Index = 18 contradicts vendor "frontier" framing | artificialanalysis.ai vs hermes4.nousresearch.com | 60 | MIXED — surfaced for user judgment |
| C23 | Hermes weights distributed under Llama 3 / Qwen 3 Community License downstream | HF model cards; fast.io guide | 70 | LIKELY (not verified against LICENSE file in this round) |

**Items to verify before BUILD trigger**: C20 (BFCL), C23 (exact LICENSE file text).

---

## 10. Failure Modes, Risk Controls, Kill-Switches

| Failure | Likelihood | Impact | Control | Kill-switch |
|---|---|---|---|---|
| Hermes 4 endpoint outage | Med | High | Multi-provider OpenRouter fallback: Hermes 4 70B → Llama 4 70B → DeepSeek V4 Flash → local 3B | `/pause` if all upstream fail >5 min |
| Cost runaway (agent loop) | Med | High ($) | Hard per-request token budget (8K in / 4K out); tool-call depth ≤7; circuit breaker on 3 consecutive failures | Auto-pause at $300/mo; manual at $500/mo |
| Prompt injection via Telegram or retrieved doc | High | High | Fence user + retrieved text; system prompt to ignore embedded directives; never act on tool calls derived from untrusted text without `/confirm` | `/pause all` + log |
| Notion 429 storm | Med | Med | Token-bucket writer at 2 req/s; queue with exponential backoff; failure → local JSONL only | Auto-fall-back to strict_local mode |
| Telegram 429 | Low | Low | 25/sec global cap; 1/sec per chat; honor `retry_after` + 10% jitter | n/a |
| strict_local data egress | Low | Catastrophic | gitignore enforcement; pre-commit hook scanning strict_local paths; Steward refuses remote writes of `tier:strict_local` rows | Auto-halt all writers, alarm |
| Model swap drift (embedding mismatch) | Med | Med | Every embedding row stores model_id + version; nightly re-embed on model change | Disable retrieval until re-embed complete |
| Hermes Agent framework fork-divergence (if adopted) | Med | High | Don't adopt wholesale; borrow patterns only | n/a |
| Nous Research org pivot / model deprecation | Low | Med | OpenRouter abstracts provider; can swap to Llama 4 70B with one config | n/a |
| Loss of GitHub access token | Low | Low | Refresh quarterly; second factor; local JSONL is always-on backup | Steward writes JSONL even if GitHub unavailable |
| RAG hallucination | High | Med | Top-k similarity floor (≥0.32 cosine); require ≥2 supporting chunks for any auto-write at confidence ≥0.78 | Dead-letter on no support |

---

## 11. Recommended Architecture & Roadmap

### 11.1 Decision (weighted matrix; same weights as §4.2)

| Option | Cost | Reliability | Privacy | Impl speed | Maintainability | Scalability | Weighted |
|---|---|---|---|---|---|---|---|
| Local-only (3B) | 5 | 2 | 5 | 3 | 3 | 1 | 3.20 |
| Self-host on rented GPU | 2 | 4 | 4 | 2 | 3 | 4 | 3.10 |
| Pure managed API (OpenRouter Hermes 4 70B) | 5 | 4 | 3 | 5 | 4 | 5 | **4.30** |
| Pure managed API (Nous Portal Plus, $20 flat) | 4 | 4 | 3 | 5 | 4 | 4 | 4.00 |
| **Hybrid: managed primary + local 3B for strict_local + cloud GPU for fine-tunes** | 4 | 5 | 5 | 4 | 4 | 5 | **4.45** ← WINNER |

### 11.2 Architecture (Phase 1 MVP)

```
                       ┌──────────────────────────────┐
                       │  Telegram (primary channel)  │
                       │  webhook + secret token      │
                       └────────────┬─────────────────┘
                                    │ HTTPS
                                    ▼
                       ┌──────────────────────────────┐
                       │  Warden adapter (FastAPI)    │
                       │  - secret-token verify       │
                       │  - dedup on update_id        │
                       │  - append → intake.jsonl     │
                       └────────────┬─────────────────┘
                                    │ async task
                                    ▼
                       ┌──────────────────────────────┐
       ┌──────────────▶│  Hermes Coordinator (1 LLM   │
       │               │  call to Hermes 4 70B via    │
       │               │  OpenRouter)                 │
       │               │  - assigns hat = Scribe      │
       │               │  - emits structured plan     │
       │               └────────────┬─────────────────┘
       │                            ▼
       │               ┌──────────────────────────────┐
       │               │  Scribe specialist           │
       │               │  - classify, extract,        │
       │               │    confidence score          │
       │               └────────────┬─────────────────┘
       │                            ▼
       │               ┌──────────────────────────────┐
       │               │  Steward dual-write governor │
       │               │  - confidence ≥ 0.78 → write │
       │               │  - 0.55–0.77 → review queue  │
       │               │  - <0.55 → dead-letter       │
       │               └─┬─────┬──────┬─────┬─────────┘
       │                 │     │      │     │
       │                 ▼     ▼      ▼     ▼
       │              Notion Drive  GitHub local
       │              (rows) (narr.)(audit) JSONL
       │                                     │
       │                                     ▼
       │                          ┌──────────────────┐
       │                          │ Almanac (weekly  │
       │                          │ digest, /digest) │
       │                          └────────┬─────────┘
       │                                   │
       └──────────────── /feedback ────────┘
                                   │
                                   ▼
                          Guardrail kill-switch (env flag + Telegram /pause)
```

### 11.3 Roadmap

**Phase 1 — MVP (weeks 1–4, target spend ≤ $10/mo)**
1. `Warden` Telegram webhook adapter (FastAPI on local dev, then $5 Hetzner VPS).
2. `Steward` dual-write governor (Notion + Drive + GitHub + local JSONL) with token-bucket pacing at 2 req/s for Notion.
3. `Scribe` classifier calling Hermes 4 70B via OpenRouter.
4. `Guardrail` kill-switch (env flag + `/pause`).
5. `/status` and `/cost` commands.
6. End-to-end test: `/dump "ate eggs 8am"` → Notion row + Drive narrative + GitHub commit; `/feedback up` round-trip.

**Phase 2 — depth (weeks 5–10, target ≤ $50/mo)**
1. Add `Pulse` (biometrics ingestion) and `Witness` (subjective journal) as additional specialists.
2. RAG: local sqlite-vss embedding index; retrieval injection capped at 4K context.
3. Migrate coordinator to LangGraph **only if** observed need.
4. `Almanac` weekly digest job (`/digest`).
5. Multi-provider fallback chain (Hermes 4 70B → Llama 4 70B → DeepSeek V4 → local 3B).
6. Decision review at week 10: promote to swarm?

**Phase 3 — selective swarm + automation (later)**
1. `Dispatcher` planner agent (only if multi-step planning need is real).
2. Borrow `Hermes Agent` patterns: scheduled automations, skill library.
3. Consider LoRA fine-tune on Hermes 3 8B (RunPod A100 4-hr job ≈ $5) only if labelled corpus ≥ 5k and retrieval cost > $50/mo.
4. Strict_local local-3B path for sensitive intake (Hermes 3 Llama-3.2-3B via Ollama).

### 11.4 What NOT to build yet
- Multi-agent swarming above 2 specialists.
- Fine-tuning.
- Self-hosted GPU inference 24/7.
- Slack / Discord / WhatsApp gateways (Telegram-primary per spec).
- Vector DB on a paid service (use local sqlite-vss first).
- Real-time learning / online RL (nightly re-embed only).
- Hermes Agent framework wholesale adoption.

### 11.5 Implementation Checklist
- [ ] Create `nizam/adapters/telegram_webhook.py` with HMAC-style secret token verification and `update_id` deduplication.
- [ ] Create `nizam/runtime/hermes_client.py` wrapping the OpenAI-compatible OpenRouter endpoint; model = `nousresearch/hermes-4-70b`.
- [ ] Add fallback chain config to `.env.example`: `HERMES_FALLBACK_CHAIN=hermes-4-70b,llama-4-70b,deepseek-v4-flash,local-3b`.
- [ ] Implement `nizam/governor/steward.py` with token-bucket (2 req/s Notion), exponential backoff [1,4,16] s, dead-letter, hash-chain provenance.
- [ ] Add `/status`, `/cost`, `/pause`, `/resume`, `/feedback`, `/dump` Telegram command handlers.
- [ ] Add Guardrail env flag `NIZAM_KILL_ALL=1` checked before every Steward write.
- [ ] Pre-commit hook scanning for `strict_local` paths in staged files.
- [ ] Cost meter: per-call token logging → daily aggregate → soft alert at $50, throttle at $150, halt at $300, hard stop at $500.
- [ ] Telegram outbound rate-limiter: 25/sec global, 1/sec per chat, jittered `retry_after` honor.
- [ ] sqlite-vss local index with `model_id` + `model_version` columns on every embedding row.
- [ ] Document and verify (a) BFCL score for chosen model, (b) exact LICENSE file text for Hermes-Function-Calling repo, before any production deployment.

---

## 12. Appendix

### 12.1 Search queries used (selected)
- "Nous Research Hermes 4 release model card"
- "Nous Hermes 3 405B benchmarks tool calling"
- "Hermes model OpenRouter pricing 2026"
- "Telegram Bot API rate limits 30 messages per second official"
- "RTX 3050 4GB VRAM LLM inference Q4 quantization tokens per second"
- "RunPod pricing A100 H100 hourly 2026"
- "Together.ai Hermes Llama pricing inference 2026"
- "Notion API rate limit 3 requests per second 2026"
- "LangGraph vs CrewAI vs AutoGen 2026 multi-agent orchestration"
- "Hermes-Function-Calling github license"
- "Lambda Labs cloud GPU pricing per hour 2026"
- "OpenRouter Hermes 4 70B price per token 2026"
- "Hermes 2 Pro Llama 3 8B Q4 GGUF VRAM local"
- "Nous Portal Plus Super Ultra subscription price"
- "DeepSeek V3 pricing input output tokens 2026"
- "Hermes 4 technical report arxiv 2508.18255 benchmark MATH MMLU IFEval"
- "Claude Sonnet 4.6 API price 2026 per million tokens"
- "Hermes 3 BFCL function calling benchmark score"

### 12.2 Key source links (dated as of May 23, 2026)
- huggingface.co/NousResearch/Hermes-4-70B, /Hermes-4-405B, /Hermes-4-14B, /Hermes-4.3-36B, /Hermes-3-Llama-3.1-405B
- arxiv.org/abs/2508.18255 (Hermes 4 Technical Report)
- arxiv.org/pdf/2408.11857 (Hermes 3 Technical Report)
- openrouter.ai/nousresearch and per-model pages
- portal.nousresearch.com/manage-subscription (Nous Portal tiers)
- portal.nousresearch.com/info ("Hermes 4 not recommended in Hermes Agent" caveat)
- github.com/NousResearch/Hermes-Function-Calling
- github.com/NousResearch/hermes-agent
- hermes-agent.nousresearch.com/docs
- core.telegram.org/bots/faq and core.telegram.org/bots/api
- developers.notion.com/reference/request-limits
- artificialanalysis.ai/models/hermes-4-llama-3-1-405b
- runpod.io/pricing, lambda.ai/pricing, together.ai/pricing
- api-docs.deepseek.com/quick_start/pricing
- platform.claude.com/docs/en/about-claude/pricing
- github.com/microsoft/autogen (maintenance mode notice)
- localscore.ai (RTX 3050 benchmarks)

### 12.3 Unresolved questions (require evidence before full BUILD trigger)
1. **BFCL score for any Hermes model** — currently MISSING. Until found, do not claim Hermes is competitive with tool-calling SOTA; treat as parity with base Llama 3.1 70B.
2. **Exact LICENSE text** for Hermes 3 and Hermes 4 weight repos and for Hermes-Function-Calling (not verified against the LICENSE file in this round).
3. **Hermes Agent framework production track record** — Mar 2026 launch is very young; look for >90-day uptime data before borrowing patterns.
4. Whether NIZAM's strict_local privacy guarantee survives any third-party provider's data-retention policy. Confirm Together.ai ZDR mode and OpenRouter's "do not train" defaults before sending strict_local data anywhere.
5. The "AGENTIC_MODEL_LIST" Nous Portal references — what model is recommended for Hermes Agent if not Hermes 4? Resolve before Phase 3.

---

**Final disposition: CONDITIONAL-GO. Build Phase 1 MVP against Hermes 4 70B (OpenRouter) or Nous Portal Plus. Reject local Hermes-class self-host. Defer multi-agent swarm. Re-evaluate at week 10 with real cost and quality data.**