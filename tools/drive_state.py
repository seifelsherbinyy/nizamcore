#!/usr/bin/env python3
"""Inspect current JOURNALS_REFERENCES Drive folder state + write a receipt.
Token auto-refresh reuses the same OAuth creds/logic as upload_ledger_entry.py."""
import json, os, urllib.parse, urllib.request, sys, datetime

FID = "1v1cRcpWOhy6Z7yAq9ZNhvOMeAXPVYws1"
TOKEN = os.path.expanduser("~/.nizam-drive/token.json")


def _get_token():
    with open(TOKEN) as f:
        t = json.load(f)
    try:
        exp = datetime.datetime.fromisoformat(
            t.get("expires_at", "2000-01-01T00:00:00+00:00").replace("Z", "+00:00")
        )
        if (exp - datetime.datetime.now(datetime.timezone.utc)).total_seconds() < 300:
            data = urllib.parse.urlencode({
                "client_id": t["client_id"], "client_secret": t["client_secret"],
                "refresh_token": t["refresh_token"], "grant_type": "refresh_token",
            }).encode()
            req = urllib.request.Request(t["token_uri"], data=data, method="POST")
            req.add_header("Content-Type", "application/x-www-form-urlencoded")
            with urllib.request.urlopen(req) as r:
                nr = json.loads(r.read())
            t["access_token"] = nr["access_token"]
            t["expires_at"] = (datetime.datetime.now(datetime.timezone.utc) +
                               datetime.timedelta(seconds=nr.get("expires_in", 3600))).isoformat()
            with open(TOKEN, "w") as f2:
                json.dump(t, f2, indent=2)
    except Exception:
        pass
    return t["access_token"]


at = _get_token()
q = urllib.parse.quote(f"'{FID}' in parents and trashed=false")
url = f"https://www.googleapis.com/drive/v3/files?q={q}&fields=files(id,name,mimeType,size)"
req = urllib.request.Request(url, headers={"Authorization": f"Bearer {at}"})
files = json.loads(urllib.request.urlopen(req).read()).get("files", [])

print("JOURNALS_REFERENCES on Drive now:")
for f in files:
    print(f"  - {f.get('name')} ({f.get('mimeType')}) size={f.get('size','?')}")

out = {
    "generated_at": "2026-09-04",
    "egress": "CONDITIONAL_PAUSED_await_your_policy_confirm",
    "files_on_drive": [f.get("name") for f in files],
    "next_run": "14:30 Africa/Cairo daily; on egress-confirm, reconcile re-uploads + read-back verifies",
}
outpath = "/home/nizam/nizamcore/YAWMIYAT__journaling/_retrieval/DRIVE_STATE.json"
with open(outpath, "w") as f:
    json.dump(out, f, indent=2)
print(f"DRIVE_STATE.json written ({outpath})")
sys.exit(0)