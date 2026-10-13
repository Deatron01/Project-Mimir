# Mascots

One character per colour palette, named after the palette id. The app picks the files up at build time
(see `src/theme/mascots.ts`); no code changes are needed to add or replace one.

| Palette id | Palette name     | Character                   |
| ---------- | ---------------- | --------------------------- |
| `original` | Stargazer Silver | Stargazer Scholar Girl      |
| `midnight` | Midnight Lab     | Researcher & Teacher        |
| `library`  | Old Library      | Archival Scholar Librarian  |
| `sunset`   | Evening Lecture  | The Professor               |
| `lavender` | Varsity Lavender | Cocky Sports Star Boy       |
| `forest`   | Atelier Green    | Design-Disgust Girl Scholar |

Files per palette (any of .svg .png .webp .avif .gif .jpg), shown here for `library`:

- `library.webp` – the default pose (the sheet's front view)
- `library-wave.webp` – greetings and empty states (the 3/4 view)
- `library-thinking.webp` – loading and generation in progress (the profile view)
- `library-happy.webp` – success screens; not drawn yet, so these show the default pose
- `library-face.webp` – head crop, shown instead of the figure below 56 px (navbar, chat avatar, palette picker)

A missing mood falls back to the default pose, a missing head crop to the figure, and a palette with no artwork
at all to the built-in placeholder.

The images are cut straight out of the character sheets in `/art` by `art/extract_mascots.py` (Python with
Pillow, NumPy and SciPy): only the sheet's panel background is removed, nothing is redrawn.

    python art/extract_mascots.py art frontend/src/assets/mascots

Tips for new artwork: square images with a transparent background work best; figures are shown from 84 px up
to 120 px and head crops from 26 px to 38 px, so about 500 px and 250 px are plenty.
