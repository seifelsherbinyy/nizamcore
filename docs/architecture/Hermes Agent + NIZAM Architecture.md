# Hermes Agent + NIZAM Architecture — Decision-Grade Research Report

> **Version:** 1.0 · **Date:** May 23, 2026 · **Author:** NIZAM Architect (Seif ElSherbiny)
> **Status:** CONDITIONAL-GO — MVP ready, scale conditioned on evidence
> **Cost Ceiling:** $300/month Year 1 baseline · $500/month hard warning
> **Assumptions Used:** See Section 0.2

***

## 0. Executive Decision Snapshot

| Decision | Verdict | Confidence |
|---|---|---|
| Hermes Identity | NousResearch/hermes-agent framework (NOT Hermes-3 LLM) | CONFIRMED |
| Deploy MVP as | Local install → Telegram gateway → managed API backend | CONFIRMED |
| Multi-agent | Hermes Profiles (native) + Workspace Swarm (Beta) | LIKELY |
| Learning loop | Hermes built-in skill/memory system + NIZAM JSONL ledger | CONFIRMED |
| Storage backend | Local SQLite + GitHub immutable log + Drive hot cache | LIKELY |
| Telegram | Hermes gateway (native, first-class) | CONFIRMED |
| Cost Year 1 | $30–$150/month (API-backed), $0–$25/month (local Ollama) | ESTIMATED |
| Go/No-Go | **GO** — MVP phase with kill-switch at $300/month | — |

### 0.1 The One-Sentence Decision

**Deploy Hermes Agent v0.10+ on a Hetzner CAX21 VPS (≈€6.49/month) backed by OpenRouter (Qwen 3.5/3.6 free tier for routine tasks, Claude Sonnet for complex reasoning), with Telegram gateway, three NIZAM-specific profiles (Coordinator, Ingestion Specialist, Retrieval Specialist), and GitHub as the immutable ledger — targeting <$100/month total operational cost in Year 1.**

### 0.2 Assumptions Used

| ID | Assumption | Impact | Changeable |
|---|---|---|---|
| A1 | HERMES_TARGET = NousResearch/hermes-agent framework | HIGH | If wrong, full Section 1 revision needed |
| A2 | NIZAM repo exists or will be created at private GitHub URL | MEDIUM | Adjust storage path only |
| A3 | Usage: 10–30 messages/day, 3–5 brain dumps/week, 2–3 feedback loops/week | HIGH | Change cost model Section 8 |
| A4 | Deployment: no existing GPU, Cairo-based internet (latency to EU ~80ms) | MEDIUM | Switch deployment if GPU acquired |
| A5 | $300/month Year 1 baseline, $500/month hard stop | HIGH | Adjustable by Seif |
| A6 | Telegram single-bot, multi-profile architecture | MEDIUM | Expand later |
| A7 | No model fine-tuning; learning via skill/memory system only | LOW | By design |

***

## 1. Hermes Identity Resolution and Source Map

### 1.1 Candidate Analysis

Before any architecture work, the most critical step is resolving what "Hermes agent" actually means. Two distinct Nous Research products carry the Hermes name:

| Candidate | Type | Owner | Repo | Relevance to NIZAM |
|---|---|---|---|---|
| **NousResearch/hermes-agent** | Agent *framework* (Python CLI + runtime) | Nous Research | `github.com/NousResearch/hermes-agent` | **PRIMARY — this is the target** [^1][^2] |
| **Hermes-3 / DeepHermes-3** | LLM *model family* (weights on HuggingFace) | Nous Research | HuggingFace NousResearch | Secondary — usable as *backend model* inside hermes-agent [^3][^4] |
| **Hermes-Function-Calling repo** | Function-calling demo scripts | Nous Research | `github.com/NousResearch/Hermes-Function-Calling` | Deprecated reference implementation only [^5] |

**Decision:** `NousResearch/hermes-agent` is the unambiguous target. It is the only Nous Research product that operates as an agent runtime (Telegram gateway, multi-agent profiles, learning loop). The LLM model family is a *component* that can be used inside this framework, not a competing interpretation. All architecture below proceeds on this basis. [CONFIRMED]

### 1.2 Identity Evidence Ledger

| Claim | Source | Evidence Type | Confidence |
|---|---|---|---|
| hermes-agent released February 25, 2026 | dev.to/tokenmixai, hermesatlas.com | Tier 2/3 corroborated | CONFIRMED [^2][^6] |
| 95,600+ GitHub stars in 7 weeks | dev.to, hermesatlas.com, tencentcloud | Multiple independent sources | CONFIRMED [^7][^2] |
| MIT license | marktechpost.com | Tier 3, single source | LIKELY [^8] |
| #1 on OpenRouter daily app chart (May 10, 2026) | marktechpost.com | Tier 3 | ANECDOTAL [^8] |
| 2,674+ GitHub Actions workflow runs (active dev) | GitHub Actions page (primary) | Tier 1 | CONFIRMED [^9] |
| v0.10 ships 118 default skills | digitalapplied.com | Tier 3, detailed | LIKELY [^10] |
| Telegram gateway is first-class feature | Official Hermes docs, NousResearch | Tier 1 | CONFIRMED [^11][^12] |

***

## 2. Hermes Capability Research

### 2.1 Core Architecture

Hermes Agent follows a five-step execution cycle on every turn:[^13][^10]

1. **Receive** — message arrives via Telegram, CLI, Discord, or any of 15+ gateway integrations
2. **Retrieve** — FTS5 full-text search across 10,000+ memory/skill documents in ~10ms
3. **Reason & Act** — LLM plans and executes tool calls (up to 8 parallel via `ThreadPoolExecutor`)
4. **Document** — if 5+ tool calls fired, agent auto-writes a skill markdown file
5. **Persist** — outcome + user model update written to memory layers

### 2.2 Capability Matrix

| Feature | Official Evidence | Social Cross-Check | Contradictions | Confidence | NIZAM Implication |
|---|---|---|---|---|---|
| Telegram gateway (native) | Official docs + tutorial | Widespread setup guides | None | CONFIRMED [^11] | Primary communication layer — no wrapper needed |
| Multi-agent Profiles | Official docs, tutorial | Video demos confirm | None | CONFIRMED [^14] | Enables NIZAM coordinator + specialists natively |
| Swarm (Workspace) | LinkedIn article, YouTube demo | Multiple tutorials | Beta maturity | LIKELY [^15][^16] | Use for parallel tasks; not production-critical at MVP |
| Built-in learning loop (skill files) | Official docs, multiple Tier 1 | Most-cited feature; some critique self-eval | Self-eval unreliable [^17] | CONFIRMED (mechanism) / MIXED (accuracy) | Core NIZAM value — with manual verification gate |
| Three-tier memory (L1 MEMORY.md, L2 transcript, L3 FTS) | X post with architecture detail | Confirmed by vectorize.io | Memory forget bug in short sessions | CONFIRMED [^18][^19] | Align NIZAM ledger with L2/L3 layer |
| 40+ built-in tools (web search, browser, image gen, TTS) | binance/Tier 3 | Corroborated widely | — | LIKELY [^20] | Reduces custom tooling needed |
| 118 bundled skills (v0.10) | digitalapplied.com | Referenced across sources | — | LIKELY [^10] | Skip reinventing MLOps, GitHub, research skills |
| OpenAI-compatible endpoint (any provider) | Official docs | Ollama, LM Studio, Unsloth integrations | — | CONFIRMED [^21] | Swap models without code changes |
| Qdrant vector DB integration (optional skill) | Official Hermes docs | Tutorial coverage | Adds operational complexity | CONFIRMED [^22] | Optional for NIZAM Phase 2 RAG upgrade |
| JSONL + SQLite audit log (PR in review) | GitHub Actions PR #1819 | Active PR by core contributor | Not yet merged | MIXED / FUTURE [^9] | Monitor merge; aligns perfectly with NIZAM ledger design |
| ACP (Agent Communication Protocol) editor integration | Official Hermes ACP docs | Used for Claude Code/Cursor | — | CONFIRMED [^23][^24] | Enables Seif's dev workflow integration |
| A2A (Agent-to-Agent protocol) | GitHub Issue #514 | Feature request open | Roadmap only | FUTURE [^25] | Not available for MVP; design around it |
| Checkpoint/rollback (`/rollback` command) | kilo.ai community analysis | Explicitly praised | — | CONFIRMED [^17] | Critical for NIZAM write-safety — use before all file ops |

### 2.3 Known Pain Points (Social Cross-Check Summary)

The following issues are **confirmed via 2+ independent community sources** and must be designed around — not ignored:[^17][^26]

- **Self-evaluation always passes**: the agent's self-assessment of task quality is unreliable; it rates its own output highly even when incorrect. *Mitigation: NIZAM must implement a human-review gate on all skill generation. Add an explicit `/verify [task_id]` command to NIZAM Telegram routing.*
- **Skill overwriting manual edits**: the learning loop can overwrite hand-tuned skill files. *Mitigation: use the `lock: true` frontmatter flag in all NIZAM custom skills; store locked skills in a separate `~/.hermes/skills-nizam/` directory outside the auto-learning write path*.[^27]
- **Memory forget in short sessions**: L1 memory (MEMORY.md) has a ~2,200-character cap and the periodic nudge (every ~300s) may not fire in sessions under 5 minutes. *Mitigation: end brain-dump sessions with explicit "remember this" prompt; set `memory.nudge_interval: 120` in config*.[^18][^28]
- **Token cost compounding**: each message sends full conversation history. Users report $131/day in uncontrolled setups. *Mitigation: session resets after each NIZAM pillar task; context pruning to 90-day window*.[^17]
- **Astroturfing concern**: approximately 15% of the r/hermesagent community distrusts the project due to suspected coordinated promotion. *Assessment: the technical merits are independently verified by experienced developers. The framework is open-source and auditable. Proceed with standard OSS caution.*[^17]

***

## 3. Deployment Model Comparison

### 3.1 Options Matrix

| Model | Setup | Baseline Cost/Month | Latency | Privacy | Failure Mode | Scaling Path | Confidence |
|---|---|---|---|---|---|---|---|
| **Local PC (Ollama/LM Studio)** | Easy (5 min install) | ~$0 (electricity only) | 2–8s/response | Maximum | PC off = down | Buy better GPU | CONFIRMED [^29][^30] |
| **Hetzner CAX21 VPS (ARM)** | Medium (systemd setup) | €6.49/month (~$7) | 80–120ms (Cairo↔EU) | High | Reboot/outage | Scale VPS tier | CONFIRMED [^31] |
| **Hetzner CPX21 VPS (x86)** | Medium | €8.49/month (~$9.50) | Same | High | Same | Same | CONFIRMED [^31] |
| **DigitalOcean Droplet 2GB** | Easy (managed) | $18/month | 80–150ms | Medium | Same | Resize | ESTIMATED |
| **RunPod GPU (A100 80GB)** | Complex | ~$1.39/hr = $1,000+/month if 24/7 | 100–400ms | Low-Medium | Spot termination | Add GPUs | CONFIRMED [^32] |
| **Managed API only (OpenRouter)** | Minimal | $0 (free tier) – $50/month | 200–800ms (varies) | Low | Provider outage | Swap provider | CONFIRMED [^33] |

**Recommendation: Hetzner CAX21 VPS + OpenRouter API backend**

The recommended MVP architecture separates concerns cleanly: Hermes Agent runtime (the orchestration layer) runs persistently on a Hetzner CAX21 VPS (€6.49/month, ARM, 2 vCPU / 4 GB RAM), while inference is offloaded to managed APIs via OpenRouter. This hybrid approach costs under $30/month at low usage, keeps the agent available 24/7 via Telegram, and avoids GPU complexity entirely. Local PC is a valid development/testing environment but not suitable for 24/7 Telegram availability.[^11][^34]

**GPU rental rejection rationale:** A RunPod A100 at $1.39/hr = $1,000/month at 24/7 operation — a 30x overshoot of the cost ceiling. GPU rental is only viable for fine-tuning runs (batch, not continuous) or for users already running 7B+ models locally with a GPU. Not applicable to NIZAM MVP. [CONFIRMED — cost calculation][^35][^32]

***

## 4. Multi-Agent / Swarm Feasibility

### 4.1 Native Multi-Agent Support: CONFIRMED

Hermes Agent provides **native multi-agent support via two mechanisms**, both without requiring LangChain/AutoGen wrappers:[^36][^14]

**Mechanism 1 — Profiles (Stable, v0.10)**
Each profile is a fully isolated Hermes instance with its own configuration, memory, skills, API keys, and persona. Profiles run from the same installation. A NIZAM setup with three profiles (Coordinator + Ingestion Specialist + Retrieval Specialist) is achievable today.

```
Profile: NIZAM-COORD (Coordinator)
  - Model: Claude Sonnet (complex reasoning)
  - Skills: routing, pillar classification, digest generation
  - Memory: shared NIZAM context

Profile: NIZAM-INGEST (Ingestion Specialist)
  - Model: Qwen 3.5 free (classification, tagging)
  - Skills: brain-dump parsing, folder routing, JSONL writing
  - Memory: ingestion history only

Profile: NIZAM-RECALL (Retrieval Specialist)
  - Model: Qwen 3.5 free (retrieval, summarization)
  - Skills: FTS5 search, GitHub log query, Drive cache lookup
  - Memory: retrieval patterns
```

**Mechanism 2 — Workspace Swarm (Beta, v0.10)**
Hermes Workspace allows multiple agents to run in parallel on a single mission with assigned roles (planner, builder, reviewer). The orchestrator receives the mission and routes tasks to specialists. All outputs land locally.[^16][^37]

**Feasibility verdict for NIZAM MVP:** Use Profiles for deterministic role separation. Use Swarm for experimental parallel tasks in Phase 2. Do not architect NIZAM MVP around Swarm — it is Beta and lacks OpenClaw's deterministic cron reliability.

### 4.2 Multi-Agent Feasibility Matrix

| Requirement | Hermes Native | Wrapper Needed | Confidence |
|---|---|---|---|
| Multiple agent roles (coordinator + specialists) | ✅ Profiles | No | CONFIRMED [^14] |
| Isolated memory per role | ✅ Profiles | No | CONFIRMED |
| Parallel task execution | ✅ Swarm (Beta) | Optional LangGraph for prod | LIKELY [^15] |
| Inter-agent communication | ⚠️ ACP (local) | A2A = FUTURE | MIXED [^23][^25] |
| Shared durable ledger | ❌ Not native | Custom JSONL via GitHub | ASSUMPTION |
| Deterministic cron/scheduling | ⚠️ Limited | Consider OpenClaw as orchestrator | MIXED [^17] |
| Task budget / timeout policy | ❌ Not confirmed native | Custom retry wrapper | MISSING |

### 4.3 The OpenClaw+Hermes Hybrid Option

A meaningful minority of experienced users (~20%) run **OpenClaw as orchestrator + Hermes as execution specialist**. This is worth tracking for NIZAM Phase 2 if deterministic scheduling proves critical. For MVP, Hermes standalone is sufficient.[^17]

***

## 5. Learning Loop Architecture

### 5.1 Hermes Native Learning Loop

Hermes implements a closed learning loop that is structurally aligned with NIZAM's principles:[^10][^13]

```
[User Input / Brain Dump]
         │
         ▼
[Receive → FTS5 Retrieve (10ms)]
         │
         ▼
[LLM Reasons + Executes Tools (up to 8 parallel)]
         │
         ├──→ [5+ tool calls?] → Auto-generate SKILL.md
         │
         ▼
[Persist to MEMORY.md + USER.md + Transcript DB]
         │
         ▼
[Periodic Nudge (~300s)] → "Has anything worth saving happened?"
         │                    → Yes: write / No: silent return
         ▼
[Session Close: L3 extracts semantics]
```

**Alignment with NIZAM principles:**
- Learning loop = feedback + retrieval (NOT model fine-tuning) ✅
- Immutable log: Hermes L2 transcript + NIZAM GitHub JSONL ✅
- NIZAM as single source of truth: enforced via JSONL ledger that Hermes writes to but never modifies directly ✅
- Recovery-first: `/rollback` command before all file operations ✅

### 5.2 NIZAM-Specific Learning Loop Design

The standard Hermes loop must be augmented with NIZAM-specific components to ensure SESHAT/ARES-style auditability:

```
[Telegram Brain Dump]
         │
         ▼
[NIZAM-INGEST Profile]
  - Classify pillar (Health/Finance/Work/Spiritual/Creative)
  - Extract entities, tags, date
  - Write to NIZAM-INGEST-QUEUE.jsonl (append-only)
         │
         ▼
[NIZAM-COORD Profile]
  - Read from queue
  - Route to relevant folder/ledger
  - Trigger retrieval if decision needed
  - Write NIZAM-DECISIONS-LOG.jsonl
         │
         ▼
[NIZAM-RECALL Profile]
  - User asks for digest / decision support
  - FTS5 + GitHub log query
  - Returns cited, confidence-labeled response
         │
         ▼
[User Feedback via /feedback command]
  - Explicit: "wrong pillar" → update classification skill
  - Implicit: no correction → skill confidence +1
  - Feedback written to NIZAM-FEEDBACK.jsonl
         │
         ▼
[Feedback propagation target: < 1 hour]
  - Next session of NIZAM-INGEST loads updated classification skill
```

### 5.3 Learning Loop Modes Comparison

| Mode | Latency | Cost | NIZAM Fit | Confidence |
|---|---|---|---|---|
| Hermes FTS5 skill retrieval | ~10ms | $0 | ✅ Primary | CONFIRMED [^18] |
| Qdrant vector RAG (optional) | 50–200ms | ~$20-50/month managed | ✅ Phase 2 | CONFIRMED [^22] |
| Model fine-tuning | N/A for MVP | $500–$5,000 per run | ❌ Rejected | — |
| External memory (Mem0) | 100–500ms | $0–$25/month | Optional Phase 2 | LIKELY [^38] |

**Decision: Feedback propagation target of <1 hour is achievable** with Hermes's periodic nudge (configurable to 120s) and session-close semantics. Real-time (<1 minute) is not needed for NIZAM's use case and would add cost without value.

***

## 6. NIZAM Context Injection and Storage Backend

### 6.1 Storage Backend Comparison

| Backend | Cost | Latency | Reliability | Quota | NIZAM Role | Verdict |
|---|---|---|---|---|---|---|
| **GitHub (immutable JSONL log)** | Free (private repo) | 100–500ms | High | 5,000 req/hr authenticated [^39][^40] | Durable ledger, audit trail | ✅ PRIMARY LEDGER |
| **Google Drive (hot cache)** | Free (15GB) / $2/100GB | 50–200ms | High | ~1B queries/day per project [^41] | Context cache, fast retrieval | ✅ HOT CACHE |
| **Local SQLite (on VPS)** | Free | <5ms | Medium (single server) | Unlimited | Session state, queue buffer | ✅ SESSION STORE |
| **Qdrant (local/cloud)** | Free (local) / $20+/month | 50–100ms | High | N/A | Semantic search Phase 2 | 🔷 PHASE 2 |
| **Notion** | $5-10/month | 1–2s | Low (documented failures) | Strict (3 req/s) | — | ❌ REJECTED |
| **PostgreSQL (VPS)** | Included in VPS | <10ms | High | Unlimited | Full-text search upgrade | 🔷 PHASE 2 option |

**Notion rejection rationale:** Seif's own prior experience confirms reliability issues, Notion API rate limits are the strictest of any option (3 requests/second), and average latency of 1–2s makes it unsuitable for any real-time agent context retrieval. This aligns with the prompt's explicit bias.

### 6.2 NIZAM Storage Schema

```
NIZAM Root (GitHub Private Repo: seif/nizam-ledger)
│
├── /ledger/
│   ├── NIZAM-INGEST.jsonl          # Append-only brain dump log
│   ├── NIZAM-DECISIONS.jsonl       # Routing decisions with provenance
│   ├── NIZAM-FEEDBACK.jsonl        # User corrections and confidence updates
│   └── NIZAM-COSTS.jsonl           # Token spend, API calls, daily totals
│
├── /pillars/
│   ├── health/
│   ├── finance/
│   ├── work/
│   ├── spiritual/
│   └── creative/
│
├── /skills-nizam/                  # Locked NIZAM skills (not auto-modified)
│   ├── pillar-classification.md
│   ├── brain-dump-parser.md
│   ├── digest-generator.md
│   └── cost-monitor.md
│
├── /snapshots/                     # Rollback checkpoints (weekly auto)
│
└── /config/
    ├── AGENTS.md                   # Global agent context (always injected)
    └── SOUL.md                     # NIZAM identity / SESHAT alignment

VPS Hot Cache (Google Drive sync or local SQLite)
├── recent-context.json             # Last 90 days of relevant entries
├── active-queue.jsonl              # Pending ingest items
└── retrieval-index.sqlite          # FTS5 index for fast recall
```

Each JSONL entry must include: `timestamp`, `session_id`, `pillar`, `confidence_score`, `source_agent`, `provenance`, `rollback_ref`, and `content_hash`. No agent writes directly to the ledger — all writes route through NIZAM-COORD's controlled logger with validation.

### 6.3 Context Injection Pipeline

```
Agent Receives Query
        │
        ▼
[L1: AGENTS.md + SOUL.md] ← Always in prompt (static, low token cost)
        │
        ▼
[L2: FTS5 Search on local SQLite hot cache] ← Fast path (<5ms)
        │
        ├──→ Cache hit (>80% relevance): inject + respond
        │
        └──→ Cache miss: query GitHub JSONL log (100–500ms)
                │
                └──→ Update local cache with result
                        │
                        └──→ Respond with source provenance cited
```

**Context multiplier estimate:** Standard Hermes inference at ~1,000 tokens/message. With NIZAM context injection (AGENTS.md + retrieved context): ~2,500–4,000 tokens/message. RAG multiplier: **2.5–4x** [ESTIMATED]. This is within acceptable bounds at free/cheap model tiers.

***

## 7. Telegram Integration

### 7.1 Architecture

Hermes Agent provides **first-class Telegram integration** via its gateway system. No custom bot framework is needed. The official setup is:[^12][^11]

```bash
# One-time setup
hermes gateway setup  # Select Telegram, paste BotFather token + user ID
hermes gateway start  # Persistent process (systemd service on VPS)
```

The gateway supports a `home channel` for proactive messages and cron outputs. Each Profile can have its own Telegram connection, enabling per-agent channel routing.[^11]

### 7.2 NIZAM Telegram Routing Design

```
User → Telegram → Hermes Gateway → NIZAM Router

Commands and routing:
/dump [text]        → NIZAM-INGEST: parse brain dump, classify, queue
/learn [fact]       → NIZAM-INGEST: explicit memory write
/recall [query]     → NIZAM-RECALL: FTS5 + ledger search, return cited response
/feedback [text]    → NIZAM-COORD: log correction, update skill confidence
/digest [pillar?]   → NIZAM-RECALL: generate daily/weekly digest
/cost               → NIZAM-COORD: query NIZAM-COSTS.jsonl, return spend summary
/status             → NIZAM-COORD: health check, queue depth, last sync
/pause              → Gateway: suspend all proactive messages
/resume             → Gateway: resume normal operation
/rollback [task_id] → NIZAM-COORD: restore pre-task snapshot
```

A single Telegram bot token is sufficient for MVP. Per-profile channel routing is achieved via Hermes Profiles — each profile can have a separate `TELEGRAM_HOME_CHANNEL` configured. For NIZAM MVP, route all input through one channel and use command prefixes.[^11]

### 7.3 Telegram Rate Limits and Backoff

Telegram Bot API rate limits are well-documented:[^42][^43]

- **Global bot limit:** 30 messages/second to different chats
- **Per-chat limit:** 1 message/second to a single chat (the primary constraint for NIZAM)
- **Paid broadcast:** Up to 1,000 messages/second at 0.1 Telegram Stars per message (not needed for NIZAM)
- **429 Too Many Requests:** Returns a `retry_after` value (seconds to wait)

At NIZAM's projected usage (10–30 messages/day), the rate limit will never be approached. However, implement exponential backoff regardless as a production hygiene requirement:

```python
# Required in all NIZAM Telegram dispatch code
def send_with_backoff(bot, chat_id, text, max_retries=5):
    for attempt in range(max_retries):
        try:
            bot.send_message(chat_id, text)
            return
        except TelegramError as e:
            if "retry_after" in str(e).lower():
                wait = 2 ** attempt
                time.sleep(wait)
            else:
                raise
    raise RuntimeError("Telegram send failed after max retries")
```

### 7.4 Security Checklist

- [ ] Telegram bot token stored in `~/.hermes/.env` only — never committed to GitHub
- [ ] Hermes user ID whitelist enabled (only Seif's Telegram user ID can send commands)
- [ ] VPS firewall: Hermes gateway port not publicly exposed (Telegram uses outbound webhook only)
- [ ] All API keys (OpenRouter, Anthropic, GitHub token) in `.env`, excluded from ledger JSONL
- [ ] Secrets rotation procedure: `hermes setup` → update keys → restart gateway
- [ ] Audit log: every command logged to NIZAM-DECISIONS.jsonl with timestamp + user ID hash
- [ ] Prompt injection defense: NIZAM-INGEST validates structured fields; free-text only goes to sandboxed processing profile

***

## 8. Cost Model

### 8.1 Usage Scenarios

| Scenario | Messages/Day | Brain Dumps/Week | Feedback/Week | Tokens/Message (with context) |
|---|---|---|---|---|
| **Low** | 10 | 2 | 1 | 2,500 |
| **Baseline** | 25 | 5 | 3 | 3,500 |
| **High** | 60 | 10 | 7 | 5,000 |
| **Stress (3 agents, rich context)** | 100 | 15 | 14 | 8,000 |

### 8.2 Monthly Cost Breakdown

**Configuration A: Free Tier (Qwen 3.5/3.6 via OpenRouter free)**
OpenRouter offers free models (Qwen 3.5, Qwen 3.6 Plus, GLM-5.1) at 20 requests/minute, 200 requests/day limit. At 25 messages/day, this is viable for routine classification and retrieval tasks.[^33][^44]

| Component | Cost/Month | Notes |
|---|---|---|
| Hetzner CAX21 VPS | €6.49 (~$7) | ARM 2vCPU/4GB [^31] |
| OpenRouter free tier | $0 | Qwen 3.5/3.6 for INGEST + RECALL |
| Claude Sonnet (complex tasks only) | $5–$20 | ~50 complex messages/month at $3/M out |
| GitHub private repo | $0 | Free for individuals |
| Google Drive | $0 | 15GB free tier |
| Monitoring (UptimeRobot free) | $0 | Ping VPS + gateway |
| **Total Baseline** | **~$15–$30/month** | Well under $300 ceiling |

**Configuration B: Mid-Tier (mix of free + Claude Sonnet)**

| Scenario | Year 1 Monthly | Year 2 Monthly (2x usage) | Notes |
|---|---|---|---|
| Low | $12/month | $18/month | Mostly free models |
| Baseline | $30/month | $55/month | 20% Claude, 80% free |
| High | $80/month | $140/month | 40% Claude for complex |
| Stress (7 agents) | $220/month | $380/month | Approaching ceiling |

**Configuration C: All-Claude (worst case)**

At Claude Sonnet 4.x pricing of ~$3/M input + $15/M output (estimated at May 2026 rates), with 25 messages/day × 3,500 tokens × 30 days = 2.625M tokens/month:
- Input cost: ~$7.90
- Output cost (assuming 1,500 token avg output): ~$16.90
- **Monthly total: ~$25–$35/month** at baseline usage [ESTIMATED]

Even all-Claude at baseline is well within the $300/month ceiling. The cost risk is in context compounding during multi-agent sessions, not in per-message cost.

### 8.3 Cost Sensitivity Analysis

| Variable | Change | Cost Impact | Mitigation |
|---|---|---|---|
| Token cost +50% | Provider price hike | +$15–$50/month | Swap to cheaper model tier |
| Context size 3x (deep RAG) | More history injected | +$30–$100/month | Context pruning, 90-day window |
| Agents 7x (full swarm) | Tokens multiply | +$100–$200/month | Free model routing for simple agents |
| Retries +20% | Bad model responses | +$5–$15/month | Retry cap (3 max), task budget |
| GPU idle (if rented) | N/A for recommended setup | N/A | Not using GPU rental |

### 8.4 24-Month Cost Projection

| Month | Low ($) | Baseline ($) | High ($) | Stress ($) |
|---|---|---|---|---|
| 1–6 | 15 | 30 | 80 | 220 |
| 7–12 | 18 | 45 | 100 | 280 |
| 13–18 | 20 | 55 | 130 | 340 |
| 19–24 | 22 | 65 | 160 | 400 |
| **Total Year 1** | **$198** | **$450** | **$1,080** | **$3,000** |
| **Total Year 2** | **$252** | **$720** | **$1,740** | **$4,320** |

**Kill-switch triggers:**
- Monthly cost >$150: review model routing, increase free tier allocation
- Monthly cost >$300: pause non-essential agents, switch all to free/cheap models
- Monthly cost >$500: immediate architecture review, possible Hermes instance pause

### 8.5 Hidden Cost Variables

The following costs are typically underestimated and must be tracked in NIZAM-COSTS.jsonl:[^17]

| Variable | Impact | Tracking Method |
|---|---|---|
| Context history compounding | HIGH — full history sent each turn | Session reset after each pillar task |
| Agent-to-agent messages (swarm) | MEDIUM — each inter-agent message = API call | Log coordinator→specialist calls separately |
| Failed run waste (retried tasks) | LOW-MEDIUM — retries cost tokens | Max 3 retries; log retried tasks with cost |
| RAG retrieval overhead | MEDIUM — 2.5–4x context multiplier | Track tokens_with_context vs base_tokens |
| Monitoring/logging infra | LOW ($0 with free tier tools) | UptimeRobot free, Hermes local logs |

***

## 9. Confidence Ledger

### 9.1 Claim-by-Claim Evidence Grading

Using the formula: `+35 official docs, +20 repo evidence, +15 reproducible benchmark, +10 repeated GitHub issues, +10 repeated social (2+ platforms), -20 contradictory reports, -15 stale source >18 months, -25 missing primary evidence`

| Claim | Score | Label | Key Sources |
|---|---|---|---|
| hermes-agent is correct Hermes identity | 35+20+10+10 = 75 | LIKELY → CONFIRMED | GitHub, official docs, multiple Tier 3 [^1][^2][^9] |
| Telegram gateway is first-class native | 35+20+10 = 65 | CONFIRMED | Official docs + tutorial [^11][^12] |
| Multi-agent via Profiles works today | 35+20+10 = 65 | CONFIRMED | Official docs, video demo [^14][^36] |
| Swarm feature is stable | 35-20 = 15 | ANECDOTAL | Only beta/limited evidence [^15][^16] |
| MIT license | 35-25(not Tier 1) = 10 | LIKELY | Single Tier 3 cite [^8] — check GitHub README to verify |
| FTS5 memory retrieval ~10ms | 35+10 = 45 | ESTIMATED | Social architecture post [^18] |
| Self-evaluation unreliable | -25+10+10+20 = 15 | CONFIRMED RISK | Multiple independent reports [^17][^26] |
| Skill overwrite of manual edits | -25+10+10+10 = 5 | CONFIRMED RISK | Community + workaround documented [^27][^17] |
| Hetzner CAX21 €6.49/month | 35+20 = 55 | CONFIRMED | Official Hetzner pricing [^31] |
| OpenRouter free models (200 req/day) | 35+20 = 55 | CONFIRMED | Official OpenRouter [^33] |
| GitHub API 5,000 req/hr authenticated | 35+20 = 55 | CONFIRMED | GitHub official docs [^39][^40] |
| Telegram per-chat 1 msg/sec limit | 35+20+10 = 65 | CONFIRMED | Official API docs + community [^43] |
| Token cost compounding is main cost risk | +10+10 = 20 | CONFIRMED RISK | Multiple community reports [^17] |
| A2A protocol support (inter-agent) | -25+0 = -25 | FUTURE / MISSING | GitHub issue only [^25] |
| JSONL SQLite audit log (in PR) | 20-20 = 0 | MIXED / FUTURE | GitHub PR not merged [^9] |

***

## 10. Failure Modes, Risk Controls, and Kill-Switches

### 10.1 Risk Register

| Risk ID | Failure Mode | Probability | Impact | Control | Kill-Switch |
|---|---|---|---|---|---|
| R1 | Self-evaluation passes on bad skill | HIGH | MEDIUM | Human review gate on all skill writes | `/skill-lock [name]` — freeze skill |
| R2 | Skill overwrite destroys tuned NIZAM workflow | MEDIUM | HIGH | Locked skills dir + lock:true frontmatter [^27] | Git rollback to last commit |
| R3 | Memory forget in short sessions | HIGH | MEDIUM | Explicit "remember this" at session end + nudge=120s | Manual `cat MEMORY.md` inspection |
| R4 | Token cost spike from context compounding | MEDIUM | HIGH | Session resets + 90-day context window | `/pause` + model downgrade |
| R5 | Hermes update breaks working setup | MEDIUM | HIGH | Pin version in install script; test updates on dev profile | `pip install hermes-agent==ast_good>` |
| R6 | Telegram gateway drops (network/process crash) | LOW-MEDIUM | MEDIUM | systemd service + health ping | `systemctl restart hermes-gateway` |
| R7 | GitHub API rate limit hit | LOW | LOW | 5,000 req/hr >> NIZAM usage; add local SQLite cache | Fallback to local cache only |
| R8 | Agent writes directly to ledger (bypasses COORD) | MEDIUM | HIGH | NIZAM-COORD is sole ledger writer; others are read-only | Audit NIZAM-DECISIONS.jsonl for unauthorized writes |
| R9 | VPS disk full (JSONL logs unbounded) | LOW | MEDIUM | 90-day archive rotation + Hetzner 20GB default | `find /nizam/ledger -mtime +90 -exec gzip {} \;` |
| R10 | Prompt injection via Telegram message | LOW-MEDIUM | HIGH | Input sanitization in NIZAM-INGEST; structured field parsing only | Block unrecognized command prefixes |

### 10.2 Emergency Runbook

```bash
# Cost spike > $300/month
hermes gateway stop                    # Stop all proactive agent activity
hermes model                           # Switch all profiles to free Qwen tier
cat ~/.hermes/costs/NIZAM-COSTS.jsonl  # Identify which agent is burning

# Memory corruption / wrong routing
git -C ~/nizam-ledger log --oneline -20  # Find last good commit
git -C ~/nizam-ledger revert HEAD        # Rollback ledger

# Hermes gateway crash
systemctl restart hermes-gateway
hermes status                          # Verify recovery
journalctl -u hermes-gateway -n 50    # Check error log

# Skill self-overwrote a locked skill (should not happen with lock:true)
git -C ~/.hermes/skills-nizam log --oneline [skill-name].md
git -C ~/.hermes/skills-nizam checkout [commit-hash] -- [skill-name].md
```

***

## 11. Recommended Architecture and Roadmap

### 11.1 NIZAM Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     NIZAM SYSTEM BOUNDARY                        │
│                                                                  │
│  [Seif via Telegram] ──────────────────────────────────────────┐│
│         │                                                        ││
│         ▼                                                        ││
│  ┌──────────────────┐    ┌─────────────────────────────┐        ││
│  │  Hermes Gateway  │───▶│    NIZAM-COORD (Profile 1)  │        ││
│  │  (Telegram Bot)  │    │  Model: Claude Sonnet/free  │        ││
│  │  Systemd Service │    │  Role: Route, plan, decide  │        ││
│  └──────────────────┘    └─────────┬───────────────────┘        ││
│                                    │                             ││
│              ┌─────────────────────┼────────────────────┐       ││
│              │                     │                    │        ││
│              ▼                     ▼                    ▼        ││
│  ┌───────────────────┐  ┌──────────────────┐  ┌─────────────┐  ││
│  │ NIZAM-INGEST      │  │ NIZAM-RECALL     │  │ NIZAM-COST  │  ││
│  │ (Profile 2)       │  │ (Profile 3)      │  │ (future P4) │  ││
│  │ Model: Qwen free  │  │ Model: Qwen free │  │             │  ││
│  │ Role: Parse,      │  │ Role: Search,    │  │             │  ││
│  │ classify, queue   │  │ retrieve, digest │  │             │  ││
│  └─────────┬─────────┘  └────────┬─────────┘  └─────────────┘  ││
│            │                     │                               ││
│            └──────────┬──────────┘                              ││
│                       ▼                                          ││
│  ┌────────────────────────────────────────────────────────┐     ││
│  │                  STORAGE LAYER                          │     ││
│  │                                                         │     ││
│  │  [SQLite Hot Cache]  ←──→  [Google Drive Sync]         │     ││
│  │        ↓                                               │     ││
│  │  [GitHub Private Repo: seif/nizam-ledger]              │     ││
│  │   ├── ledger/*.jsonl   (immutable append-only)         │     ││
│  │   ├── pillars/*        (categorized notes)             │     ││
│  │   ├── skills-nizam/*   (locked custom skills)          │     ││
│  │   └── snapshots/*      (weekly rollback points)        │     ││
│  └────────────────────────────────────────────────────────┘     ││
│                                                                  ││
│  ┌────────────────────────────────────────────────────────┐     ││
│  │  INFERENCE LAYER (OpenRouter / Anthropic API)           │     ││
│  │  - Free: Qwen 3.5/3.6 for INGEST, RECALL (routine)    │     ││
│  │  - Paid: Claude Sonnet for COORD (complex reasoning)   │     ││
│  └────────────────────────────────────────────────────────┘     ││
└─────────────────────────────────────────────────────────────────┘│
                                                                    │
[Hetzner CAX21 VPS: €6.49/month, 24/7 uptime, Cairo→EU ~80ms]─────┘
```

### 11.2 Implementation Roadmap

**Phase 0 — Environment Prep (Week 1)**
- [ ] Provision Hetzner CAX21 VPS (Ubuntu 24.04 LTS)
- [ ] Install Hermes Agent via official install script
- [ ] Create Telegram bot via @BotFather; store token in `.env` only
- [ ] Configure OpenRouter API key; set default model to `qwen/qwen3.6-plus:free`
- [ ] Create `seif/nizam-ledger` private GitHub repo; generate Personal Access Token (PAT) with repo scope
- [ ] Run `hermes gateway start` + verify Telegram message delivery
- [ ] Create systemd service for Hermes gateway (auto-restart on crash)

**Phase 1 — MVP Single-Agent NIZAM (Weeks 2–4)**
- [ ] Write `AGENTS.md` (NIZAM identity, pillar taxonomy, routing rules)
- [ ] Write `SOUL.md` (SESHAT/ARES principles alignment statement)
- [ ] Create `~/.hermes/skills-nizam/brain-dump-parser.md` (with `lock: true`)
- [ ] Create `~/.hermes/skills-nizam/pillar-classifier.md` (with `lock: true`)
- [ ] Implement `/dump` → ingestion → GitHub JSONL flow (single agent first)
- [ ] Implement `/recall` → FTS5 search → cited response
- [ ] Set up NIZAM-COSTS.jsonl auto-writer (daily token summary)
- [ ] Test feedback loop: `/feedback wrong pillar` → manual skill confidence update
- [ ] Validate memory persistence: `cat ~/.hermes/memories/MEMORY.md` after 5 days

**Phase 2 — Multi-Agent NIZAM (Month 2)**
- [ ] Create Profile 2: NIZAM-INGEST (separate config, memory, skills)
- [ ] Create Profile 3: NIZAM-RECALL (separate config, memory, skills)
- [ ] Route `/dump` commands to NIZAM-INGEST profile
- [ ] Route `/recall` and `/digest` commands to NIZAM-RECALL profile
- [ ] Implement NIZAM-COORD as supervisor (Profile 1 orchestrates 2+3)
- [ ] Test inter-profile message flow via ACP
- [ ] Set up 90-day context pruning cron job

**Phase 3 — Enhanced Retrieval (Month 3–4)**
- [ ] Evaluate Qdrant local (Docker) vs Qdrant cloud for semantic search
- [ ] Add Mem0 or Hindsight as L3 external memory provider
- [ ] Implement Hermes Workspace Swarm for parallel digest generation
- [ ] Add structured JSONL + SQLite audit log (monitor PR #1819 merge)[^9]
- [ ] Set up weekly automated rollback snapshots
- [ ] Performance review: token costs, latency, recall accuracy

**Phase 4 — Scale and Optimize (Month 5–6)**
- [ ] Evaluate OpenClaw as orchestrator if deterministic cron scheduling needed[^17]
- [ ] Add A2A protocol support when released[^25]
- [ ] Expand to 5–7 pillars-specific profiles if value is demonstrated
- [ ] Implement MiniMax or GLM-5.1 as cheapest reliable model for high-frequency tasks

### 11.3 What NOT to Build Yet

- ❌ GPU rental infrastructure — cost 10–30x ceiling; no GPU needed
- ❌ Model fine-tuning pipeline — cost, complexity, and marginal gain unjustified
- ❌ Notion integration — reliability-rejected, do not revisit until API v3 proven stable
- ❌ Hermes Workspace Swarm for critical workflows — Beta; use Profiles instead
- ❌ A2A inter-agent network — GitHub Issue status, not yet available[^25]
- ❌ Distributed learning (agents update independent models) — violates NIZAM single-source-of-truth principle
- ❌ Full-text Discord/Slack deployment — Telegram is sufficient; complexity without gain

### 11.4 Decision Matrix

| Criterion | Weight | Local PC | Hetzner+API | GPU Rental | Managed SaaS |
|---|---|---|---|---|---|
| Cost (Year 1) | 25% | 9 | 10 | 2 | 6 |
| Reliability (24/7) | 20% | 3 | 9 | 7 | 9 |
| Privacy | 15% | 10 | 8 | 5 | 4 |
| Implementation Speed | 15% | 9 | 8 | 5 | 9 |
| Maintainability | 15% | 6 | 8 | 4 | 7 |
| Scalability | 10% | 4 | 8 | 10 | 7 |
| **Weighted Score** | — | **6.8** | **8.7** | **5.1** | **7.1** |

**Winner: Hetzner CAX21 + OpenRouter API hybrid**

***

## 12. Appendix

### 12.1 Search Queries Executed

- `NousResearch hermes-agent GitHub features skills learning loop 2026`
- `Nous Research Hermes model family 2025 2026 GitHub`
- `NousResearch Hermes-3 capabilities tool calling function calling`
- `hermes agent multi-agent swarm orchestration support`
- `hermes agent Telegram integration deployment`
- `hermes agent deployment local CPU GPU requirements specs 2026`
- `hermes agent cost API pricing OpenRouter together.ai 2026`
- `hermes agent Reddit community complaints issues pain points`
- `hermes agent v0.10 release notes changelog features May 2026`
- `hermes agent storage backend SQLite vector database RAG integration`
- `Telegram Bot API rate limits 2025 2026 webhook polling limits`
- `hermes agent GitHub stars issues open 2026 community feedback`
- `hermes agent GitHub issues problems failures 2026`
- `hermes agent ACP protocol agent communication inter-agent`
- `hermes agent Qdrant vector DB RAG integration`
- `VPS hosting cost small server Hetzner 2026`
- `OpenRouter pricing free models Qwen Llama 2026`
- `GitHub API rate limits authenticated 2026 per hour`
- `Google Drive API quota limits 2026`

### 12.2 Source Evidence Summary

| Tier | Sources Used | Notes |
|---|---|---|
| Tier 1 (Official) | hermes-agent.nousresearch.com docs, GitHub NousResearch/hermes-agent, Hetzner.com, gramio.dev (Telegram API), github.com/orgs/community | Primary source for all capability, pricing, and API limit claims |
| Tier 2 (Repo/Benchmark) | GitHub Actions workflow log (2,674 runs), GitHub Issue #514, GitHub PR #1819, mem0.ai integration docs | Active development confirmed; specific feature status tracked |
| Tier 3 (Community) | kilo.ai (1,300 Reddit comments analyzed), r/hermesagent threads, dev.to, digitalapplied.com, vectorize.io, lumadock.com | Social cross-check; pain points confirmed across multiple sources |
| Tier 4 (Blogs/SEO) | nxcode.io, juliangoldie.com, utilo.io, mindstudio.ai | Used as leads only; cross-checked against Tier 1 before inclusion |

### 12.3 Unresolved Questions

| Question | Impact | Resolution Path |
|---|---|---|
| hermes-agent exact license (MIT confirmation) | LOW | Check `LICENSE` file in GitHub repo before production use |
| PR #1819 (JSONL+SQLite audit log) merge status | MEDIUM | Monitor GitHub; ping maintainer if >60 days unmerged |
| A2A protocol release timeline | LOW | Subscribe to GitHub Issue #514; design NIZAM without it for now |
| Cairo→Hetzner latency actual measurement | LOW | Run `ping hel1.hetzner.com` from VPS after provisioning |
| Swarm Beta graduation to stable | MEDIUM | Wait for v0.12+ release notes; community stability reports |
| OpenRouter free tier rate limits change | MEDIUM | Re-verify at model selection time; always have paid fallback |
| Hermes Workspace availability (closed Beta?) | MEDIUM | Check `hermes workspace` command after install |

### 12.4 Dated Pricing References

All prices accessed or estimated at May 23, 2026:

- Hetzner CAX21: €6.49/month[^31]
- Hetzner CPX21: €8.49/month[^31]
- RunPod A100 80GB: $1.39/hr on-demand[^32]
- Vast.ai/RunPod H100: $1.49–$2.49/hr[^45][^35]
- Together AI Qwen 3.5 free tier: included in OpenRouter free[^46]
- OpenRouter free models: 20 req/min, 200 req/day, $0[^33]
- Together AI DeepSeek V3.1: $0.60/$1.70 per 1M tokens[^47]
- Together AI Llama 3.1 8B: $0.18/$0.18 per 1M tokens[^46]
- MiniMax/GLM: $10–$36/year flat rate subscription (community-reported)[^17]
- Google Drive: Free (15GB), $2/100GB thereafter[^41]
- GitHub private repo: $0 for individual accounts[^39]

---

## References

1. [Open-Source AI Agent by Nous Research - Hermes Agent](https://hermes-agent.org/about/) - Hermes Agent is an open-source autonomous AI agent built by Nous Research and released in February 2...

2. [95.6K Stars, Self-Improving AI Agent (April 2026) - DEV Community](https://dev.to/tokenmixai/hermes-agent-review-956k-stars-self-improving-ai-agent-april-2026-11le) - Hermes Agent is Nous Research's open-source AI agent framework, released February 25, 2026. Seven we...

3. [NousResearch/Hermes-3-Llama-3.1-8B - Hugging Face](https://huggingface.co/NousResearch/Hermes-3-Llama-3.1-8B) - The Hermes 3 series builds and expands on the Hermes 2 set of capabilities, including more powerful ...

4. [Nous Research API and Models - OpenRouter](https://openrouter.ai/nousresearch) - The Hermes 3 series builds and expands on the Hermes 2 set of capabilities, including more powerful ...

5. [NousResearch/Hermes-Function-Calling - GitHub](https://github.com/NousResearch/Hermes-Function-Calling) - This repository contains code for the Hermes Pro Large Language Model to perform function calling ba...

6. [The State of Hermes Agent — April 2026](https://hermesatlas.com/reports/state-of-hermes-april-2026) - A community report on the first six weeks of Nous Research's self-improving AI agent. 57200 stars, 8...

7. [The Best Open Source AI Agents in 2026: A Developer's Honest ...](https://www.tencentcloud.com/techpedia/144032) - Hermes Agent. GitHub stars: 60,000+ in under 2 months | First release: 2025. Hermes Agent is the new...

8. [OpenClaw vs Hermes Agent: Why Nous Research's Self ...](https://www.marktechpost.com/2026/05/10/openclaw-vs-hermes-agent-why-nous-researchs-self-improving-agent-now-leads-openrouters-global-rankings/) - As of May 10, 2026, Hermes Agent — built by Nous Research — has overtaken OpenClaw to hold the #1 po...

9. [NousResearch/hermes-agent: The agent that grows with you](https://github.com/nousresearch/hermes-agent) - The self-improving AI agent built by Nous Research. It's the only agent with a built-in learning loo...

10. [Hermes Agent v0.10: Self-Improving Open-Source AI Agent](https://www.digitalapplied.com/blog/hermes-agent-v0-10-self-improving-open-source-guide) - Nous Research's Hermes Agent v0.10 (April 16, 2026) ships 118 skills, three-layer memory, six messag...

11. [Tutorial: Team Telegram Assistant - Hermes Agent](https://hermes-agent.nousresearch.com/docs/guides/team-telegram-assistant) - Set Up a Team Telegram Assistant. This tutorial walks you through setting up a Telegram bot powered ...

12. [Hermes Agent Telegram Bot Setup | Gateway, BotFather, User ID](https://www.remoteopenclaw.com/blog/hermes-agent-telegram-setup) - Step 1: Create a Telegram Bot · Step 2: Get Your Telegram User ID · Step 3: Configure the Hermes Gat...

13. [What Is Hermes Agent? Complete Guide to the Self-Improving AI ...](https://www.nxcode.io/resources/news/hermes-agent-complete-guide-self-improving-ai-2026) - Hermes Agent is the only open-source framework with a closed learning loop: it solves tasks, writes ...

14. [Hermes Agent Multi Agent Profiles Let You Run A Company Of AI ...](https://juliangoldie.com/hermes-agent-multi-agent-profiles/) - Hermes Agent multi agent profiles make it possible to run a company of agents directly from one loca...

15. [Run Multiple AI Agents At Once With Hermes Agent Swarm - LinkedIn](https://www.linkedin.com/pulse/run-multiple-ai-agents-once-hermes-agent-swarm-julian-goldie-v4vuc) - Hermes Agent Swarm gives AI agents a better way to work together on real tasks instead of forcing on...

16. [Hermes + Agent Swarms Just Changed AI Agents Forever - YouTube](https://www.youtube.com/watch?v=pSzeCN4NoBU) - ... multiple Hermes AI agents simultaneously with coordinated roles ... help, then promotes training...

17. [OpenClaw vs Hermes 2026: 1,300 Reddit Comments Analyzed | Kilo](https://kilo.ai/openclaw/vs-hermes) - We analyzed 25 threads and 1,300+ comments from r/openclaw to find out what users really think about...

18. [the three-tier memory of Hermes agent. AI agents forgets everything ...](https://x.com/akshay_pachaar/status/2054861039804772827) - it has three memory layers, each at a different speed. tier 1: two tiny markdown files. MEMORY.md (2...

19. [How Hermes Agent Memory Actually Works (And How to Make It ...](https://vectorize.io/articles/hermes-agent-memory-explained) - OpenViking uses a tiered loading system (L0/L1/L2) that prioritizes recently accessed or frequently ...

20. [Hermes Agent Guide: Beyond OpenClaw, Boosting Productivity by ...](https://www.binance.com/en/square/post/312090900924370) - Hermes Agent is a self-evolving AI entity built by Nous Research, and it is currently the only Agent...

21. [AI Providers | Hermes Agent - nous research](https://hermes-agent.nousresearch.com/docs/integrations/providers) - This page covers setting up inference providers for Hermes Agent — from cloud APIs like OpenRouter a...

22. [Qdrant Vector Search - Hermes Agent](https://hermes-agent.nousresearch.com/docs/user-guide/skills/optional/mlops/mlops-qdrant) - Use when building production RAG systems requiring fast nearest neighbor search, hybrid search with ...

23. [ACP Editor Integration | Hermes Agent - nous research](https://hermes-agent.nousresearch.com/docs/user-guide/features/acp) - Hermes Agent can run as an ACP server, letting ACP-compatible editors talk to Hermes over stdio and ...

24. [Agent Communication Protocol: Welcome](https://agentcommunicationprotocol.dev/introduction/welcome) - What is ACP? The Agent Communication Protocol (ACP) is an open protocol for agent interoperability t...

25. [Feature: A2A (Agent-to-Agent) Protocol Support — Remote ... - GitHub](https://github.com/NousResearch/hermes-agent/issues/514) - A2A would give Hermes the ability to participate in multi-agent networks — calling remote agents (an...

26. [My frustrating experience with Hermes : r/hermesagent - Reddit](https://www.reddit.com/r/hermesagent/comments/1tbj6cx/my_frustrating_experience_with_hermes/) - For an agent that should have a better memory system, it's frustrating to see that it “forgets” inst...

27. [Edit Hermes Agent skills without breaking the loop - LumaDock](https://lumadock.com/tutorials/hermes-skills-without-breaking-loop) - Customise Hermes Agent skills without the learning loop overwriting your edits, with locks and confl...

28. [Hermes Agent Memory Not Working? Here's Why - Vectorize](https://vectorize.io/articles/hermes-agent-memory-not-working) - Empty memory files, Hermes forgetting things it knew, session search returning nothing — the most co...

29. [Run Hermes Agent Locally on AMD Ryzen™ AI Max+ Processors ...](https://www.amd.com/en/blogs/2026/run-hermes-agent-locally-on-amd-ryzen-ai-max-processors-and-radeon-gpus.html) - This guide demonstrates how to run Hermes Agent on Windows using WSL2 and LM Studio on AMD Ryzen™ AI...

30. [Hermes Agent + Gemma 4 & Qwen 3.5: Local AI Agent Guide](https://lushbinary.com/blog/hermes-agent-gemma-4-qwen-3-5-local-ai-guide/) - This guide walks you through setting up Hermes Agent with both model families via Ollama, compares t...

31. [Hetzner Server Comparison 2025: Best Value Cloud & Dedicated ...](https://www.achromatic.dev/blog/hetzner-server-comparison) - Complete Hetzner server comparison with real benchmarks. Compare all cloud VPS (CAX, CCX, CPX, CX) a...

32. [RunPod GPU Pricing: Compare 10+ GPUs](https://computeprices.com/providers/runpod) - Available GPUs ; A100 SXM, 80GB. 1×2×4×. $1.39/hr. 5/14/2026 ; B200, 192GB. 1×. $5.98/hr. 5/14/2026.

33. [OpenRouter Free Models: All 28 Listed (May 2026) - CostGoat](https://costgoat.com/pricing/openrouter-free-models) - OpenRouter offers select models at zero cost — no API key charges, no hidden fees. Free models are s...

34. [Your Complete Hermes Agent Deployment Roadmap - Tencent Cloud](https://www.tencentcloud.com/techpedia/144037?lang=en) - Meta Description: The definitive roadmap for deploying Hermes Agent on the cloud — from choosing a s...

35. [A100 Price Per Hour: $1.29 - SynpixCloud](https://www.synpixcloud.com/blog/cloud-gpu-pricing-comparison-2026) - RunPod H100 pricing: $2.49/hr on-demand, $1.49/hr spot. Significantly cheaper than AWS or GCP for th...

36. [Nous Research Hermes Agent: Setup and Tutorial Guide - DataCamp](https://www.datacamp.com/tutorial/hermes-agent) - When you choose Full Setup , you will be able to configure everything, including API keys and the Te...

37. [Hermes Agent Swarms + Autonomy is INSANE (FREE Setup)](https://www.youtube.com/watch?v=nzOp1GqVIZY) - ... multiple agents in parallel using Hermes Workspace (swarm feature), outlines using profiles for ...

38. [How to Add Memory to Your Hermes Agent - Mem0](https://mem0.ai/blog/how-to-add-memory-to-your-hermes-agent) - Hermes Agent just added 6 memory providers. Mem0 is one of them. Setup takes one command. Circuit br...

39. [Understanding GitHub API Rate Limits: REST, GraphQL, and Beyond](https://github.com/orgs/community/discussions/163553) - Authenticated requests: 5,000 requests per hour per user or OAuth app; Unauthenticated requests: 60 ...

40. [A Developer's Guide: Managing Rate Limits for the GitHub API](https://www.lunar.dev/post/a-developers-guide-managing-rate-limits-for-the-github-api) - 1. Primary and Secondary Rate Limits · Unauthenticated Requests: Limited to 60 requests per hour. · ...

41. [What is the limit on Google Drive API usage? - Stack Overflow](https://stackoverflow.com/questions/10311969/what-is-the-limit-on-google-drive-api-usage) - Currently for the Drive API it reads "Courtesy limit: 1,000,000,000 queries/day". It's a per app quo...

42. [How to solve rate limit errors from Telegram Bot API with ...](https://gramio.dev/rate-limits) - Telegram Bot API enforces strict rate limits to protect its infrastructure and other bots from abuse...

43. [API call limits for Telegram bot endpoints besides messaging](https://community.latenode.com/t/api-call-limits-for-telegram-bot-endpoints-besides-messaging/22786) - From what I understand, bots are allowed to send up to 30 messages per second when messaging differe...

44. [Qwen3.6 Plus (free) via OpenRouter using API Key | TypingMind](https://www.typingmind.com/guide/openrouter/qwen3.6-plus-free) - Complete guide to Qwen: Qwen3.6 Plus (free) via OpenRouter: pricing, capabilities, setup with Typing...

45. [H100 Rental Prices Compared: $1.49-$6.98/hr Across 15+ ...](https://intuitionlabs.ai/articles/h100-rental-prices-cloud-comparison) - NVIDIA H100 GPU rental rates from $1.49/hr (Vast.ai) to $6.98/hr (Azure). Compare AWS, GCP, Lambda, ...

46. [Together AI Pricing 2026: Plans, Costs & Rates](https://checkthat.ai/brands/together-ai/pricing) - Together AI pricing breakdown: token rates, image & video costs, comparison to OpenAI & Vertex AI. 2...

47. [Llama 70B $0.88, DeepSeek V3 $1.25, GPT-OSS $0.05 / 1M](https://www.aipricing.guru/together-pricing/) - Together AI API pricing spans $0.88 to $9.00 per million tokens across its open-model catalog. DeepS...

