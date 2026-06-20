#!/usr/bin/env python3
"""Interactive Google OAuth token bootstrap for Calendar/Tasks/Gmail."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SECRETS = REPO / "NIZAM__system" / "connectors" / "oauth-client.json"
DEFAULT_TOKEN = REPO / "NIZAM__system" / "connectors" / "oauth-token.json"


def run(secrets: Path, token: Path, *, launch_browser: bool = True) -> int:
    from google_auth_oauthlib.flow import InstalledAppFlow

    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from NIZAM__system.connectors.google_oauth import ALL_SCOPES

    scopes = list(ALL_SCOPES)
    if not secrets.exists():
        print(f"Missing OAuth client secrets file: {secrets}", file=sys.stderr)
        print("Download Desktop OAuth JSON from Google Cloud Console.", file=sys.stderr)
        return 2
    flow = InstalledAppFlow.from_client_secrets_file(str(secrets), scopes)
    if launch_browser:
        creds = flow.run_local_server(port=0)
    else:
        auth_url, _ = flow.authorization_url(prompt="consent")
        print("Open this URL in a browser, approve access, then paste the redirect URL:")
        print(auth_url)
        redirect = input("Redirect URL: ").strip()
        flow.fetch_token(authorization_response=redirect)
        creds = flow.credentials
    token.parent.mkdir(parents=True, exist_ok=True)
    token.write_text(creds.to_json(), encoding="utf-8")
    relay_env = REPO / "NIZAM__system" / "relay" / ".env"
    lines = []
    if relay_env.exists():
        lines = relay_env.read_text(encoding="utf-8").splitlines()
    mapping = {
        "GOOGLE_OAUTH_CLIENT_SECRETS": str(secrets),
        "GOOGLE_OAUTH_TOKEN": str(token),
    }
    existing = {line.split("=", 1)[0]: line for line in lines if "=" in line}
    for key, value in mapping.items():
        existing[key] = f"{key}={value}"
    relay_env.write_text("\n".join(existing.values()) + "\n", encoding="utf-8")
    print(f"OAuth token saved to {token}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap Google OAuth for NIZAM connectors")
    parser.add_argument("--secrets", type=Path, default=DEFAULT_SECRETS)
    parser.add_argument("--token", type=Path, default=DEFAULT_TOKEN)
    parser.add_argument("--console", action="store_true", help="Use console flow instead of browser")
    return run(parser.parse_args().secrets, parser.parse_args().token, launch_browser=not parser.parse_args().console)


if __name__ == "__main__":
    raise SystemExit(main())
