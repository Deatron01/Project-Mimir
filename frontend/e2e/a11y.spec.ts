import AxeBuilder from '@axe-core/playwright';
import { expect, test } from '@playwright/test';
import { login, prepare } from './helpers';
import palettes from '../src/theme/palettes.json' with { type: 'json' };

// TOP-15 / FE-09: no WCAG 2.1 A/AA violations on the topic screens in every palette × mode.
const PAGES = ['/topics', '/topics/top_demo/chat/ses_demo', '/topics/top_demo/files', '/topics/top_demo/tests/tst_demo'];

for (const palette of palettes.palettes.map((p) => p.id)) {
  for (const mode of ['light', 'dark'] as const) {
    test(`axe: ${palette} / ${mode}`, async ({ page }) => {
      await prepare(page, { palette, mode });
      await login(page);
      for (const path of PAGES) {
        await page.goto(path);
        // The topic event stream keeps a request open, so wait for content rather than network idle.
        await expect(page.getByRole('heading', { level: 1 }).first()).toBeVisible();
        await expect(page.locator('main [role=status] .animate-spin')).toHaveCount(0);
        // Framer-motion entrance animations must finish before colours are measured.
        await page.waitForTimeout(400);
        const results = await new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa']).analyze();
        const summary = results.violations.map(
          (v) =>
            `${v.id} (${v.impact}) on ${path}: ${v.nodes
              .slice(0, 3)
              .map((n) => `${n.target.join(' ')} ${JSON.stringify((n.any[0]?.data as Record<string, unknown> | undefined) ?? {})}`)
              .join(' | ')}`,
        );
        expect(summary, summary.join('\n')).toEqual([]);
      }
    });
  }
}

test('dialog traps focus and closes on Escape', async ({ page }) => {
  await prepare(page);
  await login(page);
  const opener = page.getByRole('button', { name: 'New topic' });
  await opener.click();
  const dialog = page.getByRole('dialog', { name: 'New topic' });
  await expect(dialog.getByLabel(/^Name/)).toBeFocused();
  for (let i = 0; i < 12; i += 1) await page.keyboard.press('Tab');
  expect(await dialog.evaluate((d) => d.contains(document.activeElement))).toBe(true);
  await page.keyboard.press('Escape');
  await expect(dialog).toBeHidden();
  await expect(opener).toBeFocused();
});
