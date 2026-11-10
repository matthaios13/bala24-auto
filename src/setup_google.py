"""ΜΙΑ φορά στο Mac: σύνδεση του λογαριασμού Google του Bala24 (YouTube + Google Sheets).

  python src/setup_google.py ~/Downloads/client_secret_XXXX.json

Ανοίγει τον browser: διαλέγεις τον λογαριασμό Google που έχει το κανάλι YouTube του Bala24 και πατάς «Allow».
- Το κλειδί για το YouTube μπαίνει κατευθείαν στα GitHub secrets (για τις αναρτήσεις).
- Το ίδιο κλειδί μένει τοπικά στο Mac (για να διαβάζει/ενημερώνει το Google Sheet).
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import yaml
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

ROOT = Path(__file__).resolve().parent.parent
REPO = "matthaios13/bala24-auto"
DATA = Path(os.environ.get("BALA24_DATA", Path.home() / "Library/Application Support/Bala24Auto"))
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/spreadsheets"]

SHEET_ONLY = "--sheet" in sys.argv
paths = [p for p in sys.argv[1:] if p != "--sheet" and "installed" in json.load(open(p))]
if not paths:
    sys.exit("Δώσε το αρχείο client_secret (τύπου Desktop app).")
secret = paths[-1]
gh = shutil.which("gh") or str(Path.home() / ".local/bin/gh")

if SHEET_ONLY:   # μόνο σύνδεση του λογαριασμού που έχει το Google Sheet
    print("Άνοιξε ο browser: διάλεξε τον λογαριασμό Google που ΕΧΕΙ το Sheet «Bala24 – Βίντεο για Reels» και πάτα «Allow»…")
    c = InstalledAppFlow.from_client_secrets_file(secret, scopes=["https://www.googleapis.com/auth/spreadsheets"]).run_local_server(
        port=0, access_type="offline", prompt="consent")
    DATA.mkdir(parents=True, exist_ok=True)
    t = DATA / "sheets_token.json"; t.write_text(c.to_json()); t.chmod(0o600)
    sid = yaml.safe_load((ROOT / "config.yaml").read_text())["source"]["sheet_id"]
    m = build("sheets", "v4", credentials=c, cache_discovery=False).spreadsheets().get(spreadsheetId=sid).execute()
    sys.exit(f"✓ Πρόσβαση στο Sheet: «{m['properties']['title']}»")

print("Άνοιξε ο browser: διάλεξε τον λογαριασμό Google του Bala24 (αυτόν με το κανάλι @Bala24_gr) και πάτα «Allow»…")
creds = InstalledAppFlow.from_client_secrets_file(secret, scopes=SCOPES).run_local_server(
    port=0, access_type="offline", prompt="consent")
DATA.mkdir(parents=True, exist_ok=True)
tok = DATA / "google_token.json"
tok.write_text(creds.to_json()); tok.chmod(0o600)

ch = build("youtube", "v3", credentials=creds, cache_discovery=False).channels().list(part="snippet", mine=True).execute()
name = ch["items"][0]["snippet"]["title"] if ch.get("items") else None
print(f"✓ Κανάλι YouTube: {name}")
if name and "bala" not in name.lower():
    print("  ⚠️ Αυτό δεν μοιάζει με το κανάλι του Bala24 — αν είναι λάθος λογαριασμός, τρέξε το ξανά.")

client = json.load(open(secret))["installed"]
for k, v in {"YT_CLIENT_ID": client["client_id"], "YT_CLIENT_SECRET": client["client_secret"],
             "YT_REFRESH_TOKEN": creds.refresh_token}.items():
    subprocess.run([gh, "secret", "set", k, "--repo", REPO], input=v, text=True, check=True, capture_output=True)
    print(f"✓ {k} αποθηκεύτηκε στο GitHub")

sheet = yaml.safe_load((ROOT / "config.yaml").read_text())["source"]["sheet_id"]
try:
    meta = build("sheets", "v4", credentials=creds, cache_discovery=False).spreadsheets().get(spreadsheetId=sheet).execute()
    print(f"✓ Πρόσβαση στο Sheet: «{meta['properties']['title']}»")
except Exception as e:
    print(f"✗ Δεν υπάρχει πρόσβαση στο Sheet ({str(e)[:120]}).\n"
          f"  Άνοιξε το Sheet → Κοινή χρήση → πρόσθεσε τον λογαριασμό που διάλεξες τώρα ως «Επεξεργαστής».")
