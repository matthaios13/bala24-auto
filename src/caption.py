"""Ελληνικός τίτλος & περιγραφή από το κείμενο του tweet (Groq, δωρεάν). Χωρίς επινοήσεις:
χρησιμοποιεί ΜΟΝΟ ό,τι γράφει το tweet."""
import json
import os
import re

import requests

PROMPT = """Είσαι Έλληνας αθλητικός συντάκτης του site Bala24. Θα σου δώσω το κείμενο ενός tweet με ρετρό ποδοσφαιρικό βίντεο
(μπορεί να είναι στα αγγλικά, ισπανικά, πορτογαλικά, ιταλικά). Γράψε ΣΩΣΤΑ, φυσικά ελληνικά, όπως ένα ελληνικό αθλητικό site.

ΚΑΝΟΝΕΣ:
- ΜΟΝΟ στοιχεία που υπάρχουν στο tweet. Μην επινοείς σκορ, ημερομηνίες, διοργανώσεις, ομάδες ή αντιπάλους.
- ΟΛΑ τα ονόματα παικτών/ομάδων με ΕΛΛΗΝΙΚΟΥΣ χαρακτήρες, όπως τα γράφει ο ελληνικός αθλητικός τύπος
  (Asprilla → Ασπρίγια, Crespo → Κρέσπο, Ajax → Άγιαξ, Rivaldo → Ριβάλντο, Juventus → Γιουβέντους, Manchester United → Μάντσεστερ Γιουνάιτεντ,
   Cantona → Καντονά, Baggio → Μπάτζιο, Zidane → Ζιντάν, Real Madrid → Ρεάλ Μαδρίτης, Barcelona → Μπαρτσελόνα).
- «το γκολ» (ουδέτερο), «η γκολάρα», «η μπάλα» (ποτέ «μπαλόνι»). Σωστά άρθρα και πτώσεις: «κόντρα στον Άγιαξ», «απέναντι στη Γιουβέντους».
- ΟΙ ΟΜΑΔΕΣ ΕΙΝΑΙ ΘΗΛΥΚΕΣ όταν το όνομα είναι πόλη/ξένο όνομα: η Λίβερπουλ (της Λίβερπουλ, τη Λίβερπουλ), η Γιουβέντους, η Μπαρτσελόνα,
  η Ρεάλ, η Μίλαν, η Ίντερ, η Μάντσεστερ Γιουνάιτεντ, η Τσέλσι, η Άρσεναλ, η Τότεναμ, η Λούτον, η Μπάγερν, η Ντόρτμουντ, η Μαρσέιγ.
  Αρσενικά μόνο όσα στα ελληνικά λέγονται αρσενικά: ο Άγιαξ, ο Ολυμπιακός, ο Παναθηναϊκός, ο ΠΑΟΚ. ΣΩΣΤΟ: «αποχαιρετά τη Λίβερπουλ», ΛΑΘΟΣ: «αποχαιρετά τον Λίβερπουλ».
- Ελληνική απόδοση ονομάτων όπως στον αθλητικό τύπο: Luton → Λούτον, Molby → Μόλμπι, Anfield → Άνφιλντ.
- ΟΧΙ αγγλικοί ποδοσφαιρικοί όροι: chip → λόμπα, volley → βολέ, header → κεφαλιά, free kick → φάουλ/εκτέλεση φάουλ,
  replay → επαναληπτικός, winner/winning goal → νικητήριο γκολ, final → τελικός, World Cup → Μουντιάλ, FA Cup → Κύπελλο Αγγλίας.
- Αν δεν ξέρεις με βεβαιότητα την ελληνική απόδοση ενός ονόματος, γράψ' το φωνητικά με ελληνικά γράμματα.
- Ύφος: ζωντανό, λιτό. Όχι υπερβολές που δεν στηρίζονται στο tweet.

ΠΑΡΑΔΕΙΓΜΑΤΑ:
Tweet: "When Hernan Crespo scored THIS vs Ajax in 2002. How about that!"
→ {"overlay": "Η γκολάρα του Κρέσπο κόντρα στον Άγιαξ το 2002",
   "youtube": "🔥 Τι γκολ ήταν αυτό του Κρέσπο κόντρα στον Άγιαξ το 2002;",
   "description": "Ο Ερνάν Κρέσπο και ένα γκολ που θυμόμαστε ακόμα, κόντρα στον Άγιαξ το 2002 ⚽ Τι λέτε, από τα καλύτερά του;"}
Tweet: "Happy Birthday Tino Asprilla!"
→ {"overlay": "Χρόνια πολλά στον Τίνο Ασπρίγια!",
   "youtube": "🎂 Χρόνια πολλά στον Τίνο Ασπρίγια!",
   "description": "Σήμερα έχει γενέθλια ο Τίνο Ασπρίγια 🎉 Θυμόμαστε μερικές από τις στιγμές που τον έκαναν θρύλο ⚽"}

ΜΟΡΦΗ: απάντησε ΜΟΝΟ με JSON:
{"overlay": "έως 55 χαρακτήρες, χωρίς emoji/hashtags", "youtube": "έως 70 χαρακτήρες, 1 emoji στην αρχή, χωρίς hashtags", "description": "2-3 σύντομες προτάσεις, 1-2 emoji"}"""


def _clean(t):
    t = re.sub(r"https?://\S+", "", t or "")
    return re.sub(r"\s+", " ", t).strip()


def generate(info, account, cfg, title_override=""):
    text = _clean(info.get("description") or info.get("title"))
    key = os.environ.get("GROQ_API_KEY", "").strip()
    out = None
    models = [os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b"), "openai/gpt-oss-120b"]
    for model in (models if key and text else []):
        try:
            r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                              headers={"Authorization": f"Bearer {key}"},
                              json={"model": model, "temperature": 0.3,
                                    "response_format": {"type": "json_object"},
                                    "messages": [{"role": "system", "content": PROMPT},
                                                 {"role": "user", "content": f"Λογαριασμός: @{account}\nTweet: {text}"}]},
                              timeout=60)
            r.raise_for_status()
            out = json.loads(r.json()["choices"][0]["message"]["content"])
            if all(out.get(k) for k in ("overlay", "youtube", "description")):
                break
            out = None
        except Exception as e:
            print(f"(Groq {model}: {e})")
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
