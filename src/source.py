"""Βίντεο από το Google Sheet «Bala24 – Βίντεο για Reels» (links tweets) → κατέβασμα του tweet."""
import os
import re
import shutil
import sys
from pathlib import Path

import yt_dlp

DATA = Path(os.environ.get("BALA24_DATA", Path.home() / "Library/Application Support/Bala24Auto"))
TOKEN = DATA / "google_token.json"
SCOPES = ["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/spreadsheets"]


def tweet_id(url):
    m = re.search(r"/status/(\d+)", url or "")
    return m.group(1) if m else None


SHEETS_TOKEN = DATA / "sheets_token.json"     # λογαριασμός που έχει το Sheet (αν είναι άλλος από του YouTube)


def _sheets():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    if SHEETS_TOKEN.exists():
        creds = Credentials.from_authorized_user_file(str(SHEETS_TOKEN), ["https://www.googleapis.com/auth/spreadsheets"])
    else:
        creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    return build("sheets", "v4", credentials=creds, cache_discovery=False).spreadsheets()


def read_rows(sheet_id):
    """[{row, url, id, account, title, status}] με τη σειρά του Sheet."""
    vals = _sheets().values().get(spreadsheetId=sheet_id, range="A2:E").execute().get("values", [])
    rows = []
    for i, v in enumerate(vals, start=2):
        v = v + [""] * (5 - len(v))
        tid = tweet_id(v[0])
        if tid:
            rows.append({"row": i, "url": v[0].strip(), "id": tid, "account": v[1].strip(),
                         "status": v[3].strip().lower(), "title": v[4].strip()})
    return rows


def mark(sheet_id, row, status):
    try:
        _sheets().values().update(spreadsheetId=sheet_id, range=f"D{row}", valueInputOption="RAW",
                                  body={"values": [[status]]}).execute()
    except Exception as e:  # η σήμανση δεν πρέπει να σταματά τη ροή
        print(f"(δεν γράφτηκε η κατάσταση στο Sheet: {e})")


def _opts():
    opts = {"quiet": True, "no_warnings": True, "noprogress": True, "sleep_interval_requests": 1}
    deno = shutil.which("deno") or str(Path(sys.executable).with_name("deno"))
    if Path(deno).exists():
        opts["js_runtimes"] = {"deno": {"path": deno}}
    return opts


def download(url, workdir):
    """Κατεβάζει ένα tweet (βίντεο + εικόνα). Επιστρέφει (video, thumb, info)."""
    from imageio_ffmpeg import get_ffmpeg_exe
    workdir = Path(workdir)
    opts = {**_opts(), "format": "bv*+ba/b", "merge_output_format": "mp4", "ffmpeg_location": get_ffmpeg_exe(),
            "outtmpl": str(workdir / "tw.%(ext)s"), "writethumbnail": True, "playlist_items": "1",
            "postprocessors": [{"key": "FFmpegThumbnailsConvertor", "format": "jpg"}]}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
    if info.get("_type") == "playlist":
        info = (info.get("entries") or [{}])[0]
    video = next(workdir.glob("tw*.mp4"), None)
    thumb = next(workdir.glob("tw*.jpg"), None)
    if not video:
        raise RuntimeError("δεν βρέθηκε βίντεο στο tweet")
    if not thumb:   # εικόνα από το ίδιο το βίντεο
        import subprocess
        thumb = workdir / "thumb.jpg"
        subprocess.run([get_ffmpeg_exe(), "-v", "error", "-y", "-ss", "1", "-i", str(video), "-frames:v", "1", str(thumb)], check=True)
    return video, thumb, info
