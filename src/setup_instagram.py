"""ΜΙΑ φορά: σύνδεση Instagram @bala24gr.
Επικολλάς το (long-lived) user token από το Graph API Explorer· το script παίρνει το ΜΟΝΙΜΟ token
της Σελίδας Bala24, ελέγχει ότι βλέπει το Instagram και το αποθηκεύει στα GitHub secrets.

  python src/setup_instagram.py
"""
import getpass
import shutil
import subprocess
from pathlib import Path

import requests

PAGE_ID = "378107935397022"
IG_ID = "17841474985772141"
REPO = "matthaios13/bala24-auto"
G = "https://graph.facebook.com/v21.0"

user_tok = getpass.getpass("Επικόλλησε το token (δεν φαίνεται) και πάτα Enter: ").strip()
r = requests.get(f"{G}/{PAGE_ID}", params={"fields": "name,access_token", "access_token": user_tok}, timeout=30).json()
if "access_token" not in r:
    raise SystemExit(f"✗ Δεν δόθηκε token Σελίδας: {r.get('error', {}).get('message', r)}")
page_tok = r["access_token"]
print(f"✓ Σελίδα: {r.get('name')}")

ig = requests.get(f"{G}/{IG_ID}", params={"fields": "username", "access_token": page_tok}, timeout=30).json()
if "username" not in ig:
    raise SystemExit(f"✗ Δεν υπάρχει πρόσβαση στο Instagram: {ig.get('error', {}).get('message', ig)}")
print(f"✓ Instagram: @{ig['username']}")

dbg = requests.get(f"{G}/debug_token", params={"input_token": page_tok, "access_token": page_tok}, timeout=30).json().get("data", {})
exp = dbg.get("expires_at", 0)
print("✓ Το token δεν λήγει" if not exp else "⚠️ Το token ΛΗΓΕΙ (δεν ήταν long-lived) — κάνε «Extend Access Token» και ξανατρέξ' το.")

gh = shutil.which("gh") or str(Path.home() / ".local/bin/gh")
for k, v in {"IG_ACCESS_TOKEN": page_tok, "IG_USER_ID": IG_ID}.items():
    subprocess.run([gh, "secret", "set", k, "--repo", REPO], input=v, text=True, check=True, capture_output=True)
    print(f"✓ {k} αποθηκεύτηκε στο GitHub")
