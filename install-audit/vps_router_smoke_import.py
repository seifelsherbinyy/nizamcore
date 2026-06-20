#!/usr/bin/env python3
import importlib.util
import os
import sys
from pathlib import Path

os.environ["HOME"] = "/home/nizam"
sys.path.insert(0, "/home/nizam/nizamcore/NIZAM__system/config")
import nizam_router

rc = Path("/home/nizam/.hermes/nizam/router.config.yaml")
ex = Path("/home/nizam/.hermes/nizam/intent_exemplars.yaml")
cfg = nizam_router.load_config(rc)
exm = nizam_router.load_exemplars(ex)
tests = [
    ("my sister's graduation is next month — I want to plan something special", "Khalid", False),
    ("/pulse recovery 60 hrv 45 strain 12", "Hayat", True),
    ("what do you think about reducing coffee", "Salman", False),
]
for msg, want, hot in tests:
    o = nizam_router.resolve(msg, cfg, exm, sukoon_hot=hot)
    assert o["target"] == want, (msg, o)
    print("OK", want, o["resolver_steps"], "ir6", o.get("sukoon_overlay"))
spec = importlib.util.spec_from_file_location(
    "nizam_governor", "/home/nizam/.hermes/plugins/nizam-governor/__init__.py",
)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
print("governor_ok", hasattr(mod, "_mirror_schedule_trailing"))
