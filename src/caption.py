"""Ελληνικός τίτλος & περιγραφή από το κείμενο του tweet (Groq, δωρεάν). Χωρίς επινοήσεις:
χρησιμοποιεί ΜΟΝΟ ό,τι γράφει το tweet."""
import json
import os
import re

import requests

PROMPT = """Είσαι editor του ελληνικού αθλητικού site Bala24. Θα σου δώσω το κείμενο ενός tweet με ρετρό ποδοσφαιρικό βίντεο.
Γράψε στα ΕΛΛΗΝΙΚΑ, με ενθουσιασμό αλλά ΜΟΝΟ με στοιχεία που υπάρχουν στο tweet (μην επινοείς σκορ, ημερομηνίες, ομάδες):
- "overlay": τίτλος για πάνω στο βίντεο, έως 55 χαρακτήρες, χωρίς emoji, χωρίς hashtags.
- "youtube": τίτλος YouTube έως 70 χαρακτήρες, με 1 emoji στην αρχή, χωρίς hashtags.
- "description": 2-3 σύντομες προτάσεις για το τι βλέπουμε, με 1-2 emoji.
Ονόματα παικτών/ομάδων στα ελληνικά όπως τα γράφουν τα ελληνικά αθλητικά site (π.χ. Κρέσπο, Ίντερ, Άγιαξ).
Απάντησε ΜΟΝΟ με JSON: {"overlay": "...", "youtube": "...", "description": "..."}"""


def _clean(t):
    t = re.sub(r"https?://\S+", "", t or "")
    return re.sub(r"\s+", " ", t).strip()


def generate(info, account, cfg, title_override=""):
    text = _clean(info.get("description") or info.get("title"))
    key = os.environ.get("GROQ_API_KEY", "").strip()
    out = None
    if key and text:
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": f"Bearer {key}"},
                              json={"model": "llama-3.3-70b-versatile", "temperature": 0.4,
                                    "response_format": {"type": "json_object"},
                                    "messages": [{"role": "system", "content": PROMPT},
                                                 {"role": "user", "content": f"Λογαριασμός: @{account}\nTweet: {text}"}]},
                              timeout=60)
            r.raise_for_status()
            out = json.loads(r.json()["choices"][0]["message"]["content"])
        except Exception as e:
            print(f"(Groq: {e} — τίτλος από το αρχικό κείμενο)")
    if not out:
        out = {"overlay": text[:55] or "Ρετρό ποδόσφαιρο", "youtube": f"⚽ {text[:68]}", "description": text}
    overlay = title_override or out["overlay"]
    yt = f"⚽ {title_override}" if title_override else out["youtube"]
    tags = cfg["publish"].get("youtube_title_hashtags", "").strip()
    room = 100 - len(tags) - 1
    if len(yt) > room:
        yt = yt[:room].rsplit(" ", 1)[0].rstrip(" ,-–:") + "…"
    full = "\n\n".join(x for x in [out["description"].strip(), f"🎥 Πηγή: @{account}",
                                   "📲 Instagram: @bala24gr | YouTube: @Bala24_gr | bala24.gr", cfg["hashtags"]] if x)
    return {"overlay_title": overlay.strip(), "youtube_title": f"{yt} {tags}".strip(),
            "ig_caption": f"{overlay.strip()}\n\n{full}", "full_description": full}
