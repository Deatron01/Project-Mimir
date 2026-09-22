# Mimir frontend

React 18 + Vite 5 + Tailwind 3. Hungarian (default) and English UI, 6 colour palettes, each with a light and dark mode.

## Run locally

```bash
cp .env.example .env      # optional
npm ci
npm run dev               # http://localhost:5173, /api is proxied to the gateway on :80
```

Useful scripts:

| Script | What it does |
| --- | --- |
| `npm run build` | Production build into `dist/` |
| `npm run check` | Theme CSS is up to date, WCAG AA contrast for all 12 palette/mode pairs, HU/EN keys match |
| `npm run theme:build` | Regenerate `src/theme/themes.css` after editing `src/theme/palettes.json` |

## API configuration

All calls go through `src/config.js`. Set `VITE_API_BASE_URL` to point at another gateway; otherwise dev uses `/api/v1` (proxied) and production builds use `https://api.mimir-ai.hu/api/v1`.

## Theming

- Colours are semantic tokens (`background`, `surface`, `border`, `textMain`, `muted`, `primary`, `onPrimary`, `accent`, `danger`, `success`, `warning`, plus `brandPrimary` / `brandAccent` for the background glow).
- Tokens are CSS variables with RGB channels, so Tailwind opacity modifiers (`bg-primary/20`) work.
- Source of truth: `src/theme/palettes.json`. Dark values keep the original palette colours (only `accent` was lightened where it failed contrast as text); light values are derived from the same hues.
- `<html data-palette="ocean" data-mode="light">` selects the theme. An inline script in `index.html` applies the saved choice before first paint.
- Never use raw hex or `text-white` / `bg-white` in components; use a token.

## Translations

- Files: `src/locales/hu/translation.json`, `src/locales/en/translation.json` (same keys in both; `npm run check:i18n` enforces it).
- Use `const { t } = useTranslation()` and `t('section.key')`; for inline markup use `<Trans i18nKey="…" components={{ 1: <span /> }} />`.
- API errors should arrive as codes and be translated here, not shown as raw backend text.
- Page titles: `useDocumentTitle('meta.<page>')`.
