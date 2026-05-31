"""
NIZAM Governor — hermes plugin (Phase 1).

Wires NIZAM governance over the single hermes agent:
  HIMAYAH  - egress GOVERNANCE (v3): AHEL/family is ordinary context (block RETIRED, v3.1) but is
             encrypted at rest (Fernet) and is written to the VPS ledger ONLY — never mirrored to
             Drive (absence in the cloud, not just encryption). Per-tool egress audit + greenlist.
             The model-call egress itself is ZDR-constrained (provider data_collection=deny).
  SUKOON   - recovery-first downshift injected when overload flags are hot (>=2 red in 7d).
  Cost+Ledger - per-turn cost estimate -> NIZAM-COSTS.jsonl; events -> EVENT_LEDGER.jsonl.
  Persona modes - /shura (Salman brainstorm), /naqd (Hazim red-team) framing injection.
  Operator commands - /dump /cost /pause /resume /kill.

Every hook is best-effort: exceptions are swallowed so a plugin fault can never break the agent.
Timestamps are UTC ISO-8601 'Z' (NIZAM ledger standard).
"""
import os
import re
import json
import sys
import time
import datetime
import hashlib
import subprocess
import threading
import difflib
from pathlib import Path

HOME = os.environ.get("HOME") or "/home/nizam"
NIZAM_ROOT = os.path.join(HOME, "nizamcore")
LEDGER_DIR = os.path.join(NIZAM_ROOT, "NIZAM__system", "ledgers")
DUMP_DIR = os.path.join(NIZAM_ROOT, "TAFRIGH__brain_dumper", "dumps")
SUKOON_FLAGS = os.path.join(NIZAM_ROOT, "SUKOON__recovery_first", "overload_flags.jsonl")
COSTS = os.path.join(LEDGER_DIR, "NIZAM-COSTS.jsonl")
EVENTS = os.path.join(LEDGER_DIR, "EVENT_LEDGER.jsonl")
REFUSALS = os.path.join(LEDGER_DIR, "HIMAYAH__egress_refusals.jsonl")

STATE_DIR = os.path.join(HOME, ".hermes", "nizam")
PAUSE_FLAG = os.path.join(STATE_DIR, "paused")
KILL_FLAG = os.path.join(STATE_DIR, "killed")
MODE_FILE = os.path.join(STATE_DIR, "mode")

# --- P1 capture-first dual-write ---
LEARNING_LEDGER = os.path.join(LEDGER_DIR, "LEARNING_LEDGER.jsonl")
DEAD_LETTER = os.path.join(LEDGER_DIR, "DEAD_LETTER.jsonl")
STRICT_LOCAL_CAPTURE = os.path.join(NIZAM_ROOT, "AHEL__family_network", "strict_local_capture.jsonl")
SEEN_INDEX = os.path.join(STATE_DIR, "seen_keys")
MIRROR_STATE = os.path.join(STATE_DIR, "last_mirror")
MIRROR_DIR = os.path.join(STATE_DIR, "mirror")  # staging dir for AHEL-filtered ledger copies mirrored to Drive
RCLONE = "/home/nizam/.local/bin/rclone"            # absolute: works under cron/systemd (no PATH/HOME reliance)
RCLONE_CONF = "/home/nizam/.config/rclone/rclone.conf"
DRIVE_REMOTE = "drive-crypt:"          # encrypt-before-upload; Drive stores ciphertext
DRIVE_LEDGER_DIR = "NIZAM_ledgers"     # path under the crypt remote
MIRROR_THROTTLE_SEC = 30               # debounce async Drive copies (MIRROR-1: trailing timer + immediate)
MIRROR_TIMER = None                    # trailing-edge flush (reset on every _capture)
MIRROR_TIMER_LOCK = threading.Lock()
SEEN_MAX = 500                         # recent dedupe window
ACTIVE_CODENAME = os.path.join(STATE_DIR, "active_codename")

# --- P2 token instrumentation (soft-warn only, NO hard caps) ---
BUDGETS_FILE = os.path.join(STATE_DIR, "budgets.json")
WARN_STATE = os.path.join(STATE_DIR, "warn_state.json")
PENDING_WARN = os.path.join(STATE_DIR, "pending_warn")
WARN_THRESHOLDS = [0.70, 0.85, 0.95]   # flag / warn / alert
DEFAULT_BUDGETS = {"providers": {"openrouter": 30.0, "anthropic": 20.0}, "models": {}}

# --- P3 persona router + self-introduction ---
AGENT_PERSONAS = os.path.join(STATE_DIR, "agent_personas.json")  # canonical persona map (= ~/.hermes/nizam/)
LAST_PERSONA = os.path.join(STATE_DIR, "last_persona")
QUIET_FLAG = os.path.join(STATE_DIR, "quiet")
MODE_TO_CODENAME = {"shura": "Salman", "naqd": "Hazim"}
DEFAULT_PERSONA = "Amin"                # no active command -> capture (near-silent)
_PERSONA_CACHE = {"mtime": 0.0, "data": None}

# --- P4 HIMAYAH egress governance (audit every external write; greenlight gate; governance, not prevention) ---
EGRESS_AUDIT = os.path.join(LEDGER_DIR, "HIMAYAH__egress_audit.jsonl")
GREENLIST_FILE = os.path.join(STATE_DIR, "egress_greenlist.json")
DEFAULT_GREENLIST = ["openrouter", "anthropic", "elevenlabs", "telegram", "google_drive", "github", "web"]
EGRESS_TOOL_MAP = {  # network-egress tools -> outbound integration
    "browser": "web", "web_search": "web", "x_search": "web", "tool_search": "web",
    "web_fetch": "web", "fetch": "web", "search": "web", "tts": "elevenlabs",
    "image_gen": "web", "terminal": "shell",
}
# Persistence-sink tools whose args must be secret-scrubbed (memory is a distinct store).
MEMORY_TOOLS = {"memory", "remember", "save_memory", "add_memory", "update_memory"}

# --- P5 AUDIT / muhasaba (soul-mutation diffs vs baseline; growth + drift legible) ---
MUHASABA_LEDGER = os.path.join(LEDGER_DIR, "MUHASABA_LEDGER.jsonl")
BASELINE_DIR = os.path.join(STATE_DIR, "baselines")
SOUL_WATCH = [("soul", os.path.join(HOME, ".hermes", "SOUL.md")),
              ("user_profile", os.path.join(HOME, ".hermes", "user.md"))]

# --- P6 Hayat capacity routing + opening_voice (manual-paste biometric path, B3) ---
BODY_LEDGER = os.path.join(LEDGER_DIR, "BODY_LEDGER.jsonl")
PULSE_STATE = os.path.join(STATE_DIR, "last_pulse.json")
# WHOOP-style recovery zones -> capacity band -> daily deep-block budget
CAPACITY_BANDS = [(67, "HIGH", "<=3 deep blocks"), (34, "MEDIUM", "1-2 deep blocks"), (0, "LOW", "TINY-MODE (one small ask)")]

# Rough per-1k-token USD (input, output) — estimates only, tune from real billing.
PRICING = {
    "deepseek/deepseek-v4-flash": (0.0001, 0.0003),
    "deepseek/deepseek-v4-pro": (0.0004, 0.0012),
    "claude-sonnet-4-6": (0.003, 0.015),
}

# AHEL markers — v3.1: family content is ORDINARY context (no block); marker drives at-rest encryption.
AHEL_MARKERS = re.compile(r"(?i)(#ahel\b|\[ahel\]|#family\b|\[family\])")

# Secret-scrubber: at-rest write-path redaction (auto-detect + explicit markers).
ATREST_KEY = os.path.join(STATE_DIR, "atrest.key")
SECRET_PATTERNS = [
    (re.compile(r"sk-or-[A-Za-z0-9_\-]{8,}"), "openrouter_key"),
    (re.compile(r"sk-ant-[A-Za-z0-9_\-]{8,}"), "anthropic_key"),
    (re.compile(r"\bgh[posur]_[A-Za-z0-9]{20,}\b"), "github_token"),
    (re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"), "github_pat"),
    (re.compile(r"\bAKIA[0-9A-Z]{16}\b"), "aws_key"),
    (re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b"), "google_key"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9\-]{10,}\b"), "slack_token"),
    (re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\b"), "jwt"),
    (re.compile(r"\bsk-[A-Za-z0-9]{24,}\b"), "api_key"),
    (re.compile(r"(?i)\b(?:password|passwd|pwd|secret|token|api[_-]?key|bearer)\b\s*[:=]?\s+\S{6,}"), "labeled_secret"),
    (re.compile(r"\b\d{4}[ \-]?\d{4}[ \-]?\d{4}[ \-]?\d{1,4}\b"), "card_number"),
    (re.compile(r"\b[A-Fa-f0-9]{40,}\b"), "hex_token"),
]


# ---------------------------------------------------------------- helpers
def _utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _ensure(d):
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass


def _append(path, obj):
    try:
        _ensure(os.path.dirname(path))
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _event(etype, **fields):
    row = {"ts": _utc(), "type": etype, "actor": "nizam-governor"}
    row.update(fields)
    _append(EVENTS, row)


def _msg_text(event, kwargs):
    """Extract user text from a gateway MessageEvent object (real gateway) or dict (tests)."""
    t = getattr(event, "text", None)   # MessageEvent.text — the real gateway path
    if isinstance(t, str) and t:
        return t
    for src in (event, kwargs):
        if isinstance(src, dict):
            for k in ("text", "message", "content", "body"):
                v = src.get(k)
                if isinstance(v, str) and v:
                    return v
                if isinstance(v, dict):
                    tt = v.get("text") or v.get("content")
                    if isinstance(tt, str) and tt:
                        return tt
    return ""


def _norm_model(m):
    return (m or "").split("/")[-1]


def _lane(model):
    m = (model or "").lower()
    if "claude" in m or "sonnet" in m:
        return "reviewer"
    if "pro" in m:
        return "generator.reasoning"
    return "generator.fast"


def _read_mode():
    try:
        with open(MODE_FILE) as f:
            return f.read().strip()
    except Exception:
        return ""


def _set_mode(m):
    try:
        _ensure(STATE_DIR)
        with open(MODE_FILE, "w") as f:
            f.write(m)
    except Exception:
        pass


def _clear_mode():
    try:
        os.remove(MODE_FILE)
    except Exception:
        pass


def _sukoon_hot():
    """True when >=2 red overload flags appear within the last 7 days."""
    try:
        if not os.path.exists(SUKOON_FLAGS):
            return False
        cutoff = time.time() - 7 * 86400
        red = 0
        with open(SUKOON_FLAGS) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                sev = str(r.get("severity") or r.get("level") or "").lower()
                ts = r.get("ts") or r.get("timestamp") or ""
                ok_time = True
                try:
                    dt = datetime.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
                    ok_time = dt.timestamp() >= cutoff
                except Exception:
                    ok_time = True
                if ok_time and (sev in ("red", "high", "critical") or r.get("red")):
                    red += 1
        return red >= 2
    except Exception:
        return False


# ---------------------------------------------------------------- capture-first (P1)
def _sha16(s):
    return hashlib.sha256((s or "").encode("utf-8", "ignore")).hexdigest()[:16]


def _seen(key):
    try:
        if not os.path.exists(SEEN_INDEX):
            return False
        with open(SEEN_INDEX) as f:
            return key in f.read().split()
    except Exception:
        return False


def _mark_seen(key):
    try:
        _ensure(STATE_DIR)
        keys = []
        if os.path.exists(SEEN_INDEX):
            with open(SEEN_INDEX) as f:
                keys = f.read().split()
        keys.append(key)
        keys = keys[-SEEN_MAX:]
        with open(SEEN_INDEX, "w") as f:
            f.write("\n".join(keys))
    except Exception:
        pass


def _filter_ahel(src_path, dst_path):
    """Copy src->dst dropping EVERY row with ahel truthy. INVARIANT: no ahel:true row is ever mirrored,
    in ANY ledger (absence on Drive, not just encryption). Defense-in-depth: the structured check drops
    valid dicts with ahel truthy; a text-level backstop drops even MALFORMED lines that carry an ahel:true
    marker (so corrupted rows can't leak). The backstop is safe — genuine ahel:true is unescaped JSON,
    whereas an ahel string inside a captured message is escaped (\\"ahel\\") and won't match.
    Returns kept-row count, or -1 if the source is missing/unreadable."""
    try:
        if not os.path.exists(src_path):
            return -1
        _ensure(os.path.dirname(dst_path))
        kept = 0
        with open(src_path, encoding="utf-8") as src, open(dst_path, "w", encoding="utf-8") as dst:
            for line in src:
                ls = line.strip()
                if not ls:
                    continue
                drop = ('"ahel": true' in ls) or ('"ahel":true' in ls)   # text backstop (catches corrupted lines)
                if not drop:
                    try:
                        r = json.loads(ls)
                        if isinstance(r, dict) and r.get("ahel"):
                            drop = True
                    except Exception:
                        pass   # unparseable & no ahel marker -> safe to keep
                if drop:
                    continue   # AHEL -> VPS-only, never mirrored
                dst.write(ls + "\n"); kept += 1
        return kept
    except Exception:
        return -1


def _build_mirror_set():
    """Stage AHEL-filtered copies of every OPERATIONAL ledger for the Drive mirror. The AHEL
    strict_local_capture file is NEVER staged — enforced by the `never` set AND the per-row ahel
    filter above. Returns {basename: kept_rows}."""
    ledgers = [LEARNING_LEDGER, EVENTS, EGRESS_AUDIT, COSTS, BODY_LEDGER]
    never = {STRICT_LOCAL_CAPTURE}            # AHEL strict_local capture: never leaves the VPS
    _ensure(MIRROR_DIR)
    counts = {}
    for src in ledgers:
        if src in never:                      # belt-and-suspenders: AHEL file can never be in the set
            continue
        base = os.path.basename(src)
        kept = _filter_ahel(src, os.path.join(MIRROR_DIR, base))
        if kept >= 0:
            counts[base] = kept
    return counts


def _mirror_execute():
    """Run one encrypted Drive mirror cycle (AHEL-filtered staging + rclone)."""
    now = time.time()
    _ensure(STATE_DIR)
    with open(MIRROR_STATE, "w") as f:
        f.write(str(now))
    counts = _build_mirror_set()
    if not (counts and os.path.exists(RCLONE) and os.path.isdir(MIRROR_DIR)):
        return
    subprocess.run(
        [RCLONE, "--config", RCLONE_CONF, "copy", MIRROR_DIR, DRIVE_REMOTE + DRIVE_LEDGER_DIR],
        timeout=180, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    _event("drive_mirror", files=sorted(counts.keys()), rows=counts, ahel_excluded=True)
    _egress_audit("google_drive", "drive_mirror", files=len(counts), ahel_excluded=True)


def _mirror_trailing_flush():
    """MIRROR-1: fire after quiescence so the last capture of a session still mirrors."""
    global MIRROR_TIMER
    with MIRROR_TIMER_LOCK:
        MIRROR_TIMER = None
    try:
        _mirror_execute()
    except Exception as e:
        _append(DEAD_LETTER, {"ts": _utc(), "stage": "drive_mirror_trailing", "error": str(e)[:200]})


def _mirror_schedule_trailing():
    global MIRROR_TIMER
    with MIRROR_TIMER_LOCK:
        if MIRROR_TIMER is not None:
            try:
                MIRROR_TIMER.cancel()
            except Exception:
                pass
        MIRROR_TIMER = threading.Timer(float(MIRROR_THROTTLE_SEC), _mirror_trailing_flush)
        MIRROR_TIMER.daemon = True
        MIRROR_TIMER.start()


def _mirror_try_immediate():
    try:
        now = time.time()
        try:
            last = float(open(MIRROR_STATE).read().strip())
        except Exception:
            last = 0.0
        if now - last >= MIRROR_THROTTLE_SEC:
            _mirror_execute()
    except Exception as e:
        _append(DEAD_LETTER, {"ts": _utc(), "stage": "drive_mirror_immediate", "error": str(e)[:200]})


def _mirror_ledgers_async():
    """MIRROR-1: immediate path when throttle window elapsed + trailing Timer(30) reset per _capture."""
    _mirror_schedule_trailing()
    try:
        threading.Thread(target=_mirror_try_immediate, daemon=True).start()
    except Exception:
        pass


def _scrub(text):
    """Redact secrets before any at-rest write. Explicit [[redact]]..[[/redact]] / #secret + auto-detect.
    Returns (scrubbed_text, [redaction_kinds]). Ordinary/family text passes through untouched."""
    if not text:
        return text, []
    found = []
    s = text

    def _span(m):
        found.append("explicit_span")
        return "[REDACTED:explicit]"
    s = re.sub(r"\[\[redact\]\].*?\[\[/redact\]\]", _span, s, flags=re.S | re.I)

    def _sec(m):
        found.append("explicit_secret")
        return "#secret [REDACTED]"
    s = re.sub(r"#secret\b.*", _sec, s, flags=re.I)

    for pat, kind in SECRET_PATTERNS:
        def _r(m, k=kind):
            found.append(k)
            return "[REDACTED:%s]" % k
        s = pat.sub(_r, s)
    return s, found


def _atrest_fernet():
    try:
        from cryptography.fernet import Fernet
        if not os.path.exists(ATREST_KEY):
            _ensure(STATE_DIR)
            with open(ATREST_KEY, "wb") as f:
                f.write(Fernet.generate_key())
            try:
                os.chmod(ATREST_KEY, 0o600)
            except Exception:
                pass
        return Fernet(open(ATREST_KEY, "rb").read())
    except Exception:
        return None


def _encrypt_atrest(text):
    f = _atrest_fernet()
    if f is None:
        return None
    try:
        return f.encrypt(text.encode("utf-8")).decode("ascii")
    except Exception:
        return None


def _capture(text, session, platform, ahel=False, msg_id=None):
    """Capture-first durability: persist every inbound BEFORE the LLM.
    Secrets scrubbed (auto + #secret/[[redact]]); AHEL text encrypted at rest on VPS.
    Dual-write: ordinary rows -> VPS LEARNING_LEDGER + async encrypted Drive mirror;
    AHEL (ahel:true / strict_local_maximum) -> LEARNING_LEDGER on the VPS ONLY, never mirrored to Drive.
    Idempotent; failures -> DEAD_LETTER."""
    if not text:
        return
    try:
        key = _sha16(str(msg_id) if msg_id else ((session or "") + "|" + text))
        if _seen(key):
            return
        scrubbed, redactions = _scrub(text)
        row = {"ts": _utc(), "source": platform or "telegram", "session": session,
               "dedupe_key": key, "ahel": bool(ahel)}
        if redactions:
            row["redacted"] = redactions
        if ahel:
            enc = _encrypt_atrest(scrubbed)
            if enc:
                row["text_enc"] = enc
                row["enc"] = "fernet"
            else:
                row["text"] = scrubbed
                row["enc"] = "unavailable"
        else:
            row["text"] = scrubbed
        _append(LEARNING_LEDGER, row)
        _mark_seen(key)
        _event("capture_first", dedupe_key=key, ahel=bool(ahel), chars=len(text), redactions=len(redactions))
        if redactions:
            _event("secret_scrubbed", count=len(redactions), kinds=redactions)
        _mirror_ledgers_async()   # mirrors ALL operational ledgers, AHEL-filtered (AHEL stays VPS-only)
    except Exception as e:
        _append(DEAD_LETTER, {"ts": _utc(), "stage": "capture_first",
                              "error": str(e)[:200], "session": session})


# ---------------------------------------------------------------- token instrumentation (P2)
def _provider(model):
    m = (model or "").lower()
    if "claude" in m or "sonnet" in m or "anthropic" in m:
        return "anthropic"
    return "openrouter"


def _budgets():
    try:
        with open(BUDGETS_FILE) as f:
            b = json.load(f)
        b.setdefault("providers", {})
        b.setdefault("models", {})
        return b
    except Exception:
        return DEFAULT_BUDGETS


def _mtd_usage():
    """Month-to-date est USD per provider and per model from NIZAM-COSTS."""
    month = _utc()[:7]
    prov, mod = {}, {}
    try:
        with open(COSTS) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if not str(r.get("ts", "")).startswith(month):
                    continue
                usd = float(r.get("est_usd") or 0)
                p = r.get("provider") or _provider(r.get("model"))
                prov[p] = prov.get(p, 0.0) + usd
                mm = r.get("model", "?")
                mod[mm] = mod.get(mm, 0.0) + usd
    except FileNotFoundError:
        pass
    return {"providers": prov, "models": mod}


def _warn_state():
    try:
        with open(WARN_STATE) as f:
            return json.load(f)
    except Exception:
        return {}


def _queue_warn(msg):
    try:
        _ensure(STATE_DIR)
        with open(PENDING_WARN, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _check_thresholds():
    """Detect newly-crossed 70/85/95% per provider/model. Soft-warn only — NEVER blocks."""
    try:
        month = _utc()[:7]
        budgets = _budgets()
        usage = _mtd_usage()
        state = _warn_state()
        if state.get("month") != month:
            state = {"month": month}
        pending = []

        def _scan(kind, used_map, bud_map, default_map):
            for name, used in used_map.items():
                bud = float((bud_map.get(name) if bud_map else 0) or default_map.get(name) or 0)
                if bud <= 0:
                    continue
                pct = used / bud
                skey = kind + ":" + name
                alerted = set(state.get(skey, []))
                for thr in WARN_THRESHOLDS:
                    if pct >= thr and thr not in alerted:
                        alerted.add(thr)
                        lvl = int(round(thr * 100))
                        pending.append("%s %s at %d%% of $%.0f ($%.2f MTD)" % (kind, name, lvl, bud, used))
                        _event("token_warn", scope=kind, name=name, level=lvl,
                               mtd_usd=round(used, 4), budget_usd=bud)
                state[skey] = sorted(alerted)

        _scan("provider", usage["providers"], budgets.get("providers"), DEFAULT_BUDGETS["providers"])
        _scan("model", usage["models"], budgets.get("models"), {})
        try:
            _ensure(STATE_DIR)
            with open(WARN_STATE, "w") as f:
                json.dump(state, f)
        except Exception:
            pass
        if pending:
            _queue_warn("; ".join(pending))
    except Exception:
        pass


# ---------------------------------------------------------------- persona router (P3)
def _load_personas():
    """Load the canonical persona map from ~/.hermes/nizam/agent_personas.json (single source of truth)."""
    try:
        mt = os.path.getmtime(AGENT_PERSONAS)
        if _PERSONA_CACHE["data"] is None or mt != _PERSONA_CACHE["mtime"]:
            raw = json.load(open(AGENT_PERSONAS, encoding="utf-8"))
            agents = {a["codename"]: a for a in raw.get("agents", [])}
            _PERSONA_CACHE["data"] = {"agents": agents, "cross_cutting": raw.get("cross_cutting", {})}
            _PERSONA_CACHE["mtime"] = mt
        return _PERSONA_CACHE["data"]
    except Exception:
        return {"agents": {}, "cross_cutting": {}}


def _router_config_paths():
    rc = os.path.join(STATE_DIR, "router.config.yaml")
    ex = os.path.join(STATE_DIR, "intent_exemplars.yaml")
    if not os.path.exists(rc):
        rc = os.path.join(NIZAM_ROOT, "NIZAM__system", "config", "router.config.yaml")
    if not os.path.exists(ex):
        ex = os.path.join(NIZAM_ROOT, "NIZAM__system", "config", "intent_exemplars.yaml")
    return rc, ex


def _resolve_route(text):
    """IR-1..IR-8 deterministic resolver; IR-6 keeps SUKOON as tone overlay only."""
    try:
        cfg_dir = os.path.join(NIZAM_ROOT, "NIZAM__system", "config")
        if cfg_dir not in sys.path:
            sys.path.insert(0, cfg_dir)
        import nizam_router
        rc, ex = _router_config_paths()
        return nizam_router.resolve(
            text,
            nizam_router.load_config(Path(rc)),
            nizam_router.load_exemplars(Path(ex)),
            sukoon_hot=_sukoon_hot(),
        )
    except Exception:
        return {"target": DEFAULT_PERSONA, "route_action": "fallback_capture", "confidence": 0.0,
                "sukoon_overlay": False, "resolver_steps": ["fallback:exception"]}


def _set_active_codename(code):
    if not code or ":" in code or code.startswith("protocol:") or code.startswith("governor:"):
        return
    try:
        _ensure(STATE_DIR)
        with open(ACTIVE_CODENAME, "w", encoding="utf-8") as f:
            f.write(code)
    except Exception:
        pass


def _active_persona():
    """Command mode (/shura,/naqd) overrides; else resolver-persisted codename; else capture."""
    mode_code = MODE_TO_CODENAME.get(_read_mode())
    if mode_code:
        return mode_code
    try:
        if os.path.exists(ACTIVE_CODENAME):
            code = open(ACTIVE_CODENAME, encoding="utf-8").read().strip()
            if code:
                return code
    except Exception:
        pass
    return DEFAULT_PERSONA


def _quiet():
    return os.path.exists(QUIET_FLAG)


def _persona_changed(code):
    try:
        prev = open(LAST_PERSONA).read().strip() if os.path.exists(LAST_PERSONA) else ""
    except Exception:
        prev = ""
    return prev != code


def _set_last_persona(code):
    try:
        _ensure(STATE_DIR)
        with open(LAST_PERSONA, "w") as f:
            f.write(code)
    except Exception:
        pass


# ---------------------------------------------------------------- HIMAYAH egress governance (P4)
def _greenlist():
    try:
        with open(GREENLIST_FILE) as f:
            return set(json.load(f).get("approved", []))
    except Exception:
        return set(DEFAULT_GREENLIST)


def _egress_audit(integration, channel, **extra):
    """Audit-log EVERY external write. Flag (warn) anything not on the greenlist — governance, not prevention."""
    try:
        greenlit = integration in _greenlist()
        row = {"ts": _utc(), "integration": integration, "channel": channel, "greenlit": greenlit}
        row.update(extra)
        _append(EGRESS_AUDIT, row)
        if not greenlit:
            _event("egress_ungreenlit", integration=integration, channel=channel)
            _queue_warn("ungreenlit egress: %s via %s — approve with /greenlight %s" % (integration, channel, integration))
    except Exception:
        pass


# ---------------------------------------------------------------- AUDIT / muhasaba (P5)
def _muhasaba_check():
    """Detect soul/identity mutations vs baseline; record a visible unified diff to the muhasaba ledger."""
    try:
        _ensure(BASELINE_DIR)
        for name, path in SOUL_WATCH:
            if not os.path.exists(path):
                continue
            cur = open(path, encoding="utf-8", errors="ignore").read()
            base_path = os.path.join(BASELINE_DIR, name + ".base")
            prev = open(base_path, encoding="utf-8", errors="ignore").read() if os.path.exists(base_path) else ""
            if prev == cur:
                continue
            if prev:  # real mutation (not first-seen baseline)
                diff = "".join(difflib.unified_diff(
                    prev.splitlines(keepends=True), cur.splitlines(keepends=True),
                    fromfile=name + "@baseline", tofile=name + "@now", n=1))[:4000]
                _append(MUHASABA_LEDGER, {"ts": _utc(), "artifact": name,
                                          "prev_sha": _sha16(prev), "new_sha": _sha16(cur), "diff": diff})
                _event("soul_mutation", artifact=name, prev_sha=_sha16(prev), new_sha=_sha16(cur))
            with open(base_path, "w", encoding="utf-8") as f:
                f.write(cur)
    except Exception:
        pass


def _cmd_muhasaba(raw_args):
    out = ["NIZAM muhasaba — baseline vs now"]
    muts = []
    try:
        for line in open(MUHASABA_LEDGER):
            try:
                muts.append(json.loads(line))
            except Exception:
                pass
    except FileNotFoundError:
        pass
    if muts:
        last = muts[-1]
        out.append("last soul change: %s (%s)  %s -> %s" % (last["ts"], last["artifact"], last["prev_sha"], last["new_sha"]))
        out.append("soul mutations logged: %d (growth + drift legible)" % len(muts))
    else:
        out.append("identity stable — no soul mutations since baseline")
    cutoff = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    turns = 0
    try:
        for line in open(EVENTS):
            try:
                r = json.loads(line)
                if r.get("type") == "turn" and str(r.get("ts", "")) >= cutoff:
                    turns += 1
            except Exception:
                pass
    except FileNotFoundError:
        pass
    out.append("flow (7d): %d turns | MTD cost $%.4f" % (turns, sum(_mtd_usage()["providers"].values())))
    return "\n".join(out)


# ---------------------------------------------------------------- Hayat capacity + opening_voice (P6)
def _latest_pulse():
    try:
        with open(PULSE_STATE) as f:
            return json.load(f)
    except Exception:
        return None


def _capacity():
    """(band, daily-ask budget, recovery) from latest pulse. No data -> MEDIUM with LOW fallback."""
    p = _latest_pulse()
    rec = None
    if p:
        try:
            rec = float(p.get("recovery"))
        except Exception:
            rec = None
    if rec is None:
        return ("MEDIUM", "1-2 deep blocks (no-data default; fall back to LOW if unsure)", None)
    for thr, band, budget in CAPACITY_BANDS:
        if rec >= thr:
            return (band, budget, rec)
    return ("LOW", "TINY-MODE (one small ask)", rec)


def _opening_voice():
    """OBJECTIVE biometrics only. Never a scored/subjective inner state. Hermes never claims to feel."""
    p = _latest_pulse()
    band, budget, rec = _capacity()
    if not p:
        return "No biometric pulse on file. Capacity defaulting to MEDIUM (LOW fallback). Send: /pulse recovery <n> hrv <n> strain <n>."
    fields = []
    for k, label, unit in (("recovery", "recovery", "%"), ("hrv", "HRV", "ms"), ("strain", "strain", "")):
        v = p.get(k)
        if v is not None:
            fields.append("%s %s%s" % (label, v, unit))
    return "%s (%s). Capacity: %s — %s." % (", ".join(fields) or "pulse logged", str(p.get("ts", ""))[:10], band, budget)


def _cmd_pulse(raw_args):
    txt = (raw_args or "").strip()
    if not txt:
        return _opening_voice()
    rec = re.search(r"recovery\D*([0-9]+(?:\.[0-9]+)?)", txt, re.I)
    hrv = re.search(r"hrv\D*([0-9]+(?:\.[0-9]+)?)", txt, re.I)
    strain = re.search(r"strain\D*([0-9]+(?:\.[0-9]+)?)", txt, re.I)
    p = {"ts": _utc(),
         "recovery": float(rec.group(1)) if rec else None,
         "hrv": float(hrv.group(1)) if hrv else None,
         "strain": float(strain.group(1)) if strain else None,
         "raw": txt[:200]}
    _append(BODY_LEDGER, p)
    try:
        _ensure(STATE_DIR)
        with open(PULSE_STATE, "w") as f:
            json.dump(p, f)
    except Exception:
        pass
    _event("pulse_logged", recovery=p["recovery"], hrv=p["hrv"], strain=p["strain"])
    return "Pulse logged. " + _opening_voice()


# ---------------------------------------------------------------- hooks
def _pre_dispatch(event=None, **kwargs):
    try:
        text = _msg_text(event, kwargs)
        msg_id = getattr(event, "message_id", None)
        session = ""
        src = getattr(event, "source", None)
        if src is not None:
            session = str(getattr(src, "session_key", "") or getattr(src, "chat_id", "")
                          or getattr(src, "key", "") or getattr(src, "user_id", "") or "")
        if not session and isinstance(event, dict):
            session = str(event.get("session_id") or event.get("chat_id") or "")
        ahel = bool(text and AHEL_MARKERS.search(text))
        # Hard kill switch — FULL halt FIRST: no capture, no LLM, nothing persists. (checked before capture)
        if os.path.exists(KILL_FLAG) or os.environ.get("NIZAM_KILL_ALL") == "1":
            _event("dispatch_skip", reason="NIZAM_KILL_ALL")
            return {"action": "skip", "reason": "NIZAM_KILL_ALL"}
        # CAPTURE-FIRST: persist every inbound (secrets scrubbed; AHEL encrypted at rest) BEFORE the LLM.
        if text:
            _capture(text, session, "telegram", ahel=ahel, msg_id=msg_id)
            route = _resolve_route(text)
            _set_active_codename(route.get("target"))
            if route.get("sukoon_overlay"):
                _event("route_sukoon_overlay", target=route.get("target"),
                       steps=route.get("resolver_steps"), ir6="tone_only")
        # Pause — buffer non-command messages; slash-commands (e.g. /resume) still run.
        # (AHEL hard-block RETIRED per v3.1: family content is ordinary, allowed context.)
        if os.path.exists(PAUSE_FLAG) and text and not text.lstrip().startswith("/"):
            return {"action": "skip", "reason": "paused"}
        # SECRET-SCRUB UPSTREAM: if the inbound carries secrets, REWRITE so NO downstream sink
        # (agent context, memory tool, reply, sessions) ever sees plaintext. Ledger already scrubbed above.
        if text:
            scrubbed, redactions = _scrub(text)
            if redactions and scrubbed != text:
                _event("dispatch_scrub_rewrite", count=len(redactions), kinds=redactions)
                return {"action": "rewrite", "text": scrubbed}
    except Exception:
        pass
    return None


def _pre_llm(user_message="", model="", platform="", session_id="", **kwargs):
    try:
        parts = []
        if _sukoon_hot():
            parts.append(
                "[SUKOON downshift active] Recovery-first: reply in a single warm, concise line. "
                "Do NOT enumerate failure modes or stack pressure. Reduce load."
            )
        # P3: load the single active persona's contract from the canonical map and enforce it.
        personas = _load_personas()
        code = _active_persona()
        p = (personas.get("agents") or {}).get(code)
        if p:
            parts.append("[Active persona: %s — %s / %s] %s" % (
                code, p.get("module", ""), p.get("function", ""), p.get("contract", "")))
            voice = (personas.get("cross_cutting") or {}).get("voice")
            if voice:
                parts.append("[Voice] " + voice)
            # Self-introduction on activation or persona change (suppressible via /quiet).
            if (not _quiet()) and _persona_changed(code):
                parts.append(
                    "[Self-introduction REQUIRED this turn] Open your reply with a two-line header in your "
                    "own register — line 1: '%s — %s / %s.'  line 2: one short sentence of what you do — "
                    "then continue normally." % (code, p.get("module", ""), p.get("function", "")))
            _set_last_persona(code)
        if _latest_pulse():
            band, budget, _rec = _capacity()
            parts.append("[Capacity: %s — daily-ask budget %s] Objective biometrics only; never infer a "
                         "subjective inner state; never claim to feel." % (band, budget))
        parts.append(
            "[HIMAYAH] strict_local and family/AHEL content never leaves the device or a non-ZDR lane. "
            "Cloud calls are ZDR-constrained (provider data_collection=deny)."
        )
        if parts:
            return {"context": "\n".join(parts)}
    except Exception:
        pass
    return None


def _post_llm(session_id="", user_message="", assistant_response="", model="", platform="", **kwargs):
    try:
        usage = kwargs.get("usage") or {}
        in_tok = usage.get("prompt_tokens") or max(1, len(user_message or "") // 4)
        out_tok = usage.get("completion_tokens") or max(1, len(assistant_response or "") // 4)
        pin, pout = PRICING.get(model) or PRICING.get(_norm_model(model)) or (0.0002, 0.0006)
        usd = round((in_tok / 1000.0) * pin + (out_tok / 1000.0) * pout, 6)
        lane = _lane(model)
        prov = _provider(model)
        _append(COSTS, {
            "ts": _utc(), "session": session_id, "model": model, "provider": prov, "lane": lane,
            "in_tok": in_tok, "out_tok": out_tok, "est_usd": usd, "platform": platform,
        })
        _event("turn", session=session_id, model=model, lane=lane, est_usd=usd)
        _egress_audit(prov, "model_call", model=model, est_usd=usd)  # P4: audit model egress
        _check_thresholds()   # P2: soft-warn at 70/85/95%, never blocks
    except Exception:
        pass


def _transform_out(response_text="", session_id="", **kwargs):
    """P2: surface any queued token soft-warn by appending it to the Telegram reply."""
    try:
        if not os.path.exists(PENDING_WARN):
            return None
        with open(PENDING_WARN, encoding="utf-8") as f:
            warns = [w.strip() for w in f if w.strip()]
        try:
            os.remove(PENDING_WARN)
        except Exception:
            pass
        if not warns:
            return None
        return (response_text or "") + "\n\n— [NIZAM usage] " + " | ".join(warns) + " (soft-warn, no cap)"
    except Exception:
        return None


def _pre_tool(tool_name="", args=None, task_id="", **kwargs):
    try:
        _event("tool_call", tool=tool_name, task=task_id)
        if os.path.exists(KILL_FLAG):
            return {"action": "block", "message": "NIZAM kill switch engaged; tool calls halted."}
        # Persistence-sink scrub (defense-in-depth): redact secrets from memory-tool args in place,
        # so redaction holds across EVERY sink, not just the ledger.
        if tool_name in MEMORY_TOOLS and isinstance(args, dict):
            for k, v in list(args.items()):
                if isinstance(v, str):
                    sv, red = _scrub(v)
                    if red:
                        args[k] = sv
                        _event("memory_scrubbed", tool=tool_name, kinds=red)
        # HIMAYAH P4: audit external-egress tool calls; flag if integration not greenlit.
        integ = EGRESS_TOOL_MAP.get(tool_name)
        if integ:
            _egress_audit(integ, "tool:" + tool_name, task=task_id)
    except Exception:
        pass
    return None


# ---------------------------------------------------------------- commands
def _cmd_dump(raw_args):
    text = (raw_args or "").strip()
    if not text:
        return "Send: /dump <your thought>. I capture it verbatim, no judgement."
    _ensure(DUMP_DIR)
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    path = os.path.join(DUMP_DIR, day + ".jsonl")
    _append(path, {"ts": _utc(), "text": text})
    _clear_mode()
    _event("capture", chars=len(text), file=os.path.basename(path))
    return "Captured to TAFRIGH (" + day + ")."


def _cmd_cost(raw_args):
    today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
    t_usd = 0.0
    try:
        with open(COSTS) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except Exception:
                    continue
                if str(r.get("ts", "")).startswith(today):
                    t_usd += float(r.get("est_usd") or 0)
    except FileNotFoundError:
        return "No cost data yet."
    usage = _mtd_usage()
    budgets = _budgets()
    m_usd = sum(usage["providers"].values())
    out = ["NIZAM cost (estimate, USD) — soft-warn only, no hard caps",
           "today:         $%.4f" % t_usd,
           "month-to-date: $%.4f" % m_usd,
           "by provider (MTD / budget):"]
    pbud = budgets.get("providers") or {}
    for p, used in sorted(usage["providers"].items()):
        bud = float(pbud.get(p) or DEFAULT_BUDGETS["providers"].get(p) or 0)
        if bud > 0:
            pct = int(used / bud * 100)
            flag = " <-- 95%" if pct >= 95 else (" <-- 85%" if pct >= 85 else (" <-- 70%" if pct >= 70 else ""))
            out.append("  %-12s $%.4f / $%.0f  (%d%%)%s" % (p, used, bud, pct, flag))
        else:
            out.append("  %-12s $%.4f  (no budget set)" % (p, used))
    return "\n".join(out)


def _cmd_pause(raw_args):
    _ensure(STATE_DIR)
    open(PAUSE_FLAG, "w").close()
    _event("pause")
    return "Paused. Non-command messages are buffered. Send /resume to continue."


def _cmd_resume(raw_args):
    try:
        os.remove(PAUSE_FLAG)
    except FileNotFoundError:
        pass
    _event("resume")
    return "Resumed."


def _cmd_kill(raw_args):
    _ensure(STATE_DIR)
    open(KILL_FLAG, "w").close()
    _event("kill_switch")
    return ("KILL SWITCH ENGAGED. All message and tool processing halted. "
            "Restore on the VPS:  rm ~/.hermes/nizam/killed")


def _cmd_shura(raw_args):
    _set_mode("shura")
    return "Brainstorm mode (Salman) on. Send your topic; /naqd to critique, /dump to capture."


def _cmd_naqd(raw_args):
    _set_mode("naqd")
    return "Red-team mode (Hazim) on. Send the plan or claim; I'll find the failure modes. /shura to switch."


def _cmd_quiet(raw_args):
    if os.path.exists(QUIET_FLAG):
        try:
            os.remove(QUIET_FLAG)
        except Exception:
            pass
        return "Self-introductions ON — personas will introduce on activation/change."
    _ensure(STATE_DIR)
    open(QUIET_FLAG, "w").close()
    return "Quiet mode ON — persona self-introductions suppressed. /quiet again to re-enable."


def _cmd_greenlight(raw_args):
    name = (raw_args or "").strip().lower()
    gl = _greenlist()
    if not name:
        return "Greenlit outbound integrations: " + ", ".join(sorted(gl)) + "\nApprove a new one: /greenlight <name>"
    gl.add(name)
    try:
        _ensure(STATE_DIR)
        with open(GREENLIST_FILE, "w") as f:
            json.dump({"approved": sorted(gl)}, f)
    except Exception:
        pass
    _event("greenlight_added", integration=name)
    return "Greenlit '" + name + "'. Outbound to it will no longer flag in the HIMAYAH egress audit."


# ---------------------------------------------------------------- register
def _on_session_start(session_id="", model="", platform="", **kwargs):
    _muhasaba_check()  # P5: detect + record soul/identity mutations vs baseline


def register(ctx):
    ctx.register_hook("pre_gateway_dispatch", _pre_dispatch)
    ctx.register_hook("pre_llm_call", _pre_llm)
    ctx.register_hook("post_llm_call", _post_llm)
    ctx.register_hook("pre_tool_call", _pre_tool)
    ctx.register_hook("transform_llm_output", _transform_out)
    ctx.register_hook("on_session_start", _on_session_start)

    ctx.register_command("dump", _cmd_dump, "Capture a raw thought to TAFRIGH")
    ctx.register_command("cost", _cmd_cost, "Show today + month-to-date NIZAM cost")
    ctx.register_command("pause", _cmd_pause, "Pause non-command processing")
    ctx.register_command("resume", _cmd_resume, "Resume after /pause")
    ctx.register_command("kill", _cmd_kill, "Hard kill switch — halt all processing")
    ctx.register_command("shura", _cmd_shura, "Brainstorm mode (Salman)")
    ctx.register_command("naqd", _cmd_naqd, "Red-team mode (Hazim)")
    ctx.register_command("quiet", _cmd_quiet, "Toggle persona self-introductions")
    ctx.register_command("greenlight", _cmd_greenlight, "List/approve outbound egress integrations")
    ctx.register_command("muhasaba", _cmd_muhasaba, "Baseline-vs-now: soul mutations + flow over time")
    ctx.register_command("pulse", _cmd_pulse, "Log biometrics (recovery/hrv/strain) / show opening_voice")
