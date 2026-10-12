# Mascots

Drop one image per colour palette here, named after the palette id. The app picks them up at build time
(see `src/theme/mascots.ts`); no code changes are needed.

| Palette id | Palette name     | File (any of .svg .png .webp .avif .gif .jpg) |
| ---------- | ---------------- | --------------------------------------------- |
| `original` | Mimir Original   | `original.png`                                |
| `midnight` | Midnight Blossom | `midnight.png`                                |
| `ocean`    | Deep Ocean       | `ocean.png`                                   |
| `sunset`   | Sunset Glow      | `sunset.png`                                  |
| `lavender` | Lavender Dream   | `lavender.png`                                |
| `forest`   | Forest Whisper   | `forest.png`                                  |

Optional extra poses use a `-<mood>` suffix and fall back to the default image when missing:

- `ocean-happy.png` – success screens (test ready, upload done)
- `ocean-thinking.png` – loading and generation in progress
- `ocean-wave.png` – greetings and empty states

Tips: square images with a transparent background work best; they are shown from about 40 px up to 220 px.
Palettes without artwork keep the built-in placeholder.
