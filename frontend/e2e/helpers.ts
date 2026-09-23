import { expect, type Page } from '@playwright/test';

export const DEMO = { email: 'demo@mimir.hu', password: 'mimir-demo-2026' };

/** Starts every test in English with a known theme, before the app boots. */
export async function prepare(page: Page, theme: { palette?: string; mode?: 'light' | 'dark' } = {}) {
  await page.addInitScript((th) => {
    if (!sessionStorage.getItem('e2e-init')) {
      sessionStorage.setItem('e2e-init', '1');
      localStorage.setItem('mimir-lang', 'en');
      localStorage.setItem('mimir-theme', JSON.stringify({ palette: th.palette ?? 'original', mode: th.mode ?? 'dark' }));
    }
  }, theme);
}

export async function login(page: Page, email = DEMO.email, password = DEMO.password) {
  await page.goto('/login');
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page).toHaveURL(/\/topics$/);
  // Signing in applies the account's language (the demo account is Hungarian); tests run in English.
  if ((await page.locator('html').getAttribute('lang')) !== 'en') {
    const viewport = page.viewportSize();
    if (viewport && viewport.width < 768) {
      await page.getByRole('button', { name: 'Menü megnyitása' }).click();
      await page.getByRole('radio', { name: 'English' }).click();
      await page.getByRole('button', { name: 'Close menu' }).click();
    } else {
      await page.getByRole('button', { name: 'English' }).click();
    }
    await expect(page.locator('html')).toHaveAttribute('lang', 'en');
  }
}
