"""
get_upstox_token.py
===================
Morning helper to generate Upstox v2 access token.

Steps:
1. Run this script.
2. It will print an authorization URL.
3. Open that URL in your browser and log in.
4. You will be redirected to your redirect_uri with a ?code=XXXX in the URL.
5. Paste that code back into this script.
6. The script will exchange it for an access_token and update config/config.yml.
"""

import sys
import yaml
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent
CONFIG_PATH = ROOT / "config" / "config.yml"

def get_upstox_token():
    # Load existing config
    with open(CONFIG_PATH, 'r') as f:
        cfg = yaml.safe_load(f)

    broker_cfg = cfg.get('broker', {})
    if broker_cfg.get('name') != 'upstox':
        print("Broker name is not 'upstox' in config.yml. Please update it first.")
        return

    api_key = broker_cfg.get('api_key')
    api_secret = broker_cfg.get('api_secret')
    redirect_uri = broker_cfg.get('redirect_uri')

    if not all([api_key, api_secret, redirect_uri]):
        print("Missing api_key, api_secret or redirect_uri in config.yml")
        return

    # 1. Generate Auth URL
    auth_url = (
        f"https://api.upstox.com/v2/login/authorization/dialog"
        f"?response_type=code&client_id={api_key}&redirect_uri={redirect_uri}"
    )

    print("\n" + "="*60)
    print("UPSTOX AUTHENTICATION")
    print("="*60)
    print(f"1. Open this URL in your browser:\n{auth_url}")
    print("\n2. Log in and authorize the app.")
    print("3. You will be redirected to a URL. Copy the 'code' parameter.")

    code = input("\n4. Enter the authorization code: ").strip()

    # 2. Exchange code for token
    resp = requests.post(
        "https://api.upstox.com/v2/login/authorization/token",
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        data={
            "code": code,
            "client_id": api_key,
            "client_secret": api_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
    )

    if resp.status_code == 200:
        token_data = resp.json()
        access_token = token_data.get("access_token")
        print(f"\n✓ Login successful! User: {token_data.get('user_name')}")

        # 3. Update config.yml
        broker_cfg['access_token'] = access_token

        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(cfg, f, default_flow_style=False)

        print(f"✓ access_token saved to {CONFIG_PATH}")
    else:
        print(f"\n× Failed to get token: {resp.text}")

if __name__ == "__main__":
    get_upstox_token()
