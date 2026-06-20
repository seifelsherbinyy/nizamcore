#!/usr/bin/env bash
PLUG="$HOME/.hermes/plugins/nizam-governor/__init__.py"
STATE="$HOME/.hermes/nizam"
CFG="$HOME/nizamcore/NIZAM__system/config"

echo "########## 1. BACKUP ##########"
BAK="$PLUG.bak.$(date -u +%Y%m%dT%H%M%SZ)"
cp "$PLUG" "$BAK"
O=$(wc -c < "$PLUG"); B=$(wc -c < "$BAK")
echo "BAK=$BAK orig=$O bak=$B"
[ "$O" = "$B" ] && echo "SIZE_MATCH=YES" || echo "SIZE_MATCH=NO -- ABORT"
sha256sum "$PLUG" "$BAK"

echo "########## 2a. PERSONA ROUTING GROUND TRUTH ##########"
echo "--- nizam_router.py location + size ---"
ls -l "$CFG/nizam_router.py" 2>&1; wc -l "$CFG/nizam_router.py" 2>&1
echo "--- nizam_router.py: resolve() + helpers (defs + key logic) ---"
grep -nE "^def |^class |def resolve|embed|semantic|similarity|cosine|keyword|exemplar|score|confidence|return" "$CFG/nizam_router.py" 2>&1 | head -40
echo "--- FULL nizam_router.py (it is the crux) ---"
cat "$CFG/nizam_router.py" 2>&1

echo "########## router.config.yaml (top-level keys) ##########"
for f in "$STATE/router.config.yaml" "$CFG/router.config.yaml"; do
  if [ -f "$f" ]; then echo "FOUND: $f"; grep -nE "^[a-zA-Z_]" "$f" | head -40; break; fi
done
echo "########## intent_exemplars.yaml (structure + 2 examples) ##########"
for f in "$STATE/intent_exemplars.yaml" "$CFG/intent_exemplars.yaml"; do
  if [ -f "$f" ]; then echo "FOUND: $f"; head -40 "$f"; echo "..."; wc -l "$f"; break; fi
done
echo "########## DONE_RECON_A ##########"
