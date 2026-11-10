# Bala24 auto-poster

3 Reels/Shorts την ημέρα (11:00, 15:00, 20:00) σε Instagram (@bala24gr) και YouTube (@Bala24_gr),
από ρετρό ποδοσφαιρικά βίντεο του X που βρίσκονται στο Google Sheet «Bala24 – Βίντεο για Reels».

**Το Mac** (08:30 και 21:30 κάθε μέρα): παίρνει τα επόμενα links από το Sheet, κατεβάζει το tweet,
γράφει ελληνικό τίτλο/περιγραφή (Groq), βάζει template + outro Bala24 και τα στέλνει στην ουρά (branch `queue`).
Κρατά 7 μέρες έτοιμα βίντεο. Στο Sheet η στήλη Status γίνεται `queued` / `error`.

**Το GitHub** κάνει τις αναρτήσεις στις ώρες του config, ακόμα κι αν το Mac είναι κλειστό.
YouTube: πρώτα ιδιωτικό → έλεγχος copyright μετά από 30' → δημόσιο (ή μένει ιδιωτικό + email).

- Για να προσθέσεις βίντεο: βάλε link tweet στη στήλη Link του Sheet (προαιρετικά δικό σου τίτλο στη στήλη Title).
- Για να μην ανέβει κάποιο: γράψε `skip` στη στήλη Status.
- Ρυθμίσεις: `config.yaml`. Ημερολόγιο Mac: `~/Library/Application Support/Bala24Auto/prepare.log`
