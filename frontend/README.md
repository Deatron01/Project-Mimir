# Mimir frontend

React 18 + TypeScript (strict) + Vite 5 + Tailwind 3. Hungarian (default) and English UI, 6 colour palettes, each with a light and dark mode. Data fetching with TanStack Query over a client generated from the OpenAPI spec.

## Run locally

```bash
npm ci
npm run dev               # http://localhost:5173 – topic workspace on the in-browser mock API
npm run dev:legacy        # the old single-document chat, /api proxied to the gateway on :80
```

In mock mode no backend is needed. Sign in with **demo@mimir.hu / mimir-demo-2026**, or register: the verification and password-reset e-mails appear in the **Mock mailbox** button (bottom left). The mock keeps its data in `localStorage` (`mimir-mock-db`); "Reset demo data" in the mailbox starts over. Demo switches: a file whose name contains `fail` fails processing; a chat message containing `#fail` makes generation fail.

## Scripts

| Script | What it does |
| --- | --- |
| `npm run build` | Production build into `dist/` |
| `npm run check` | Everything CI checks before building: theme CSS and WCAG AA contrast (12 palette/mode pairs), HU/EN key parity and usage, API types in sync, `tsc`, ESLint |
| `npm test` / `npm run test:coverage` | Vitest unit + component tests (MSW mock API in Node) |
| `npm run e2e` | Playwright: topic lifecycle (desktop + mobile) and axe accessibility scan in every palette × mode |
| `npm run storybook` | Component catalogue with palette / mode / language toolbar and the a11y panel |
| `npm run api:types` | Regenerate `src/api/schema.d.ts` after editing `openapi/mimir-public.yaml` |
| `npm run theme:build` | Regenerate `src/theme/themes.css` after editing `src/theme/palettes.json` |

## Configuration (FE-03)

| Setting | Build time | Runtime (Docker) | Default |
| --- | --- | --- | --- |
| API base URL | `VITE_API_BASE_URL` | `MIMIR_API_BASE_URL` | `/api/v1` in dev, `https://api.mimir-ai.hu/api/v1` in prod |
| API mode | `VITE_API_MODE` (`v1` / `legacy`) | `MIMIR_API_MODE` | `v1` in dev, `legacy` in prod |
| Mock API | `VITE_USE_MOCKS` | `MIMIR_USE_MOCKS` | on in dev (v1), off in prod |
| Privacy e-mail | `VITE_PRIVACY_EMAIL` | `MIMIR_PRIVACY_EMAIL` | empty |

At start-up the app reads `/config.json`; the container writes it from the `MIMIR_*` variables (`docker/40-mimir-config.sh`), so the same image runs against any backend. Without the file the build-time values apply. **Switching production to the new UI** = deploy the v1 backend, then set `MIMIR_API_MODE=v1` (or `VITE_API_MODE=v1` on Netlify). `/chat` then redirects to `/topics`.

## Architecture

```
openapi/mimir-public.yaml   public API contract (source of truth for types and mocks)
src/api/                    typed client (openapi-fetch), auth refresh, SSE, upload, TanStack Query hooks
src/mocks/                  MSW handlers + in-memory DB + simulated job runner (dev, tests, Storybook, E2E)
src/pages/topics/           Topic explorer, workspace, My tests
src/components/workspace/   Workspace header and the Chat / Files / Tests panes
src/components/tests/       Test editor (drag reorder, regenerate, citations) and export dialog
src/pages/legacy/           Old chat + test list, used only when apiMode = legacy
```

- **Auth:** the access token lives only in memory; the refresh token is an HttpOnly cookie. On `401 TOKEN_EXPIRED` the client refreshes once (shared between parallel requests) and replays the request; a failed refresh signs the user out with a "session expired" notice.
- **Live updates:** `GET /topics/{id}/events` (SSE over `fetch`, so the bearer token can be sent), with reconnect/back-off and `Last-Event-ID`. Events are folded into the query cache; polling takes over while the stream is down.
- **Errors:** every API error is an `ApiError` with a `code`; the UI shows `t('errors.<CODE>')`. `npm run check:i18n` fails if a code in the spec has no translation.
- **Uploads:** XHR for byte progress; client-side limit checks mirror the server's; the consent box is required.

## Theming

- Colours are semantic tokens (`background`, `surface`, `border`, `textMain`, `muted`, `primary`, `onPrimary`, `accent`, `danger`, `success`, `warning`, plus `brandPrimary` / `brandAccent` for the background glow).
- Tokens are CSS variables with RGB channels, so Tailwind opacity modifiers (`bg-primary/20`) work.
- Source of truth: `src/theme/palettes.json`. Dark values keep the original palette colours (only `accent` was lightened where it failed contrast as text); light values are derived from the same hues.
- `<html data-palette="ocean" data-mode="light">` selects the theme. An inline script in `index.html` applies the saved choice before first paint.
- Never use raw hex or `text-white` / `bg-white` in components; use a token.

## Translations

- Files: `src/locales/hu/translation.json`, `src/locales/en/translation.json` (same keys in both; `npm run check:i18n` enforces it).
- Use `const { t } = useTranslation()` and `t('section.key')`; for inline markup use `<Trans i18nKey="…" components={{ 1: <span /> }} />`.
- API errors arrive as codes and are translated under `errors.<CODE>`; never show raw backend text.
- ESLint (`i18next/no-literal-string`) rejects hard-coded text in JSX.
- Page titles: `useDocumentTitle('meta.<page>')`.
