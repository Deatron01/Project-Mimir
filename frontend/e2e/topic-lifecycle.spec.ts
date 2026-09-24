import { expect, test } from '@playwright/test';
import { login, prepare } from './helpers';

// TOP-16: register → verify → create topic with a document → generate → review/edit → save → export → delete.
test('topic lifecycle', async ({ page, isMobile }) => {
  await prepare(page);
  const email = `teacher-${Date.now()}@school.hu`;
  const password = 'correct horse battery';

  // Register and confirm the e-mail through the mock mailbox.
  await page.goto('/register');
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill(password);
  await page.getByLabel('Confirm password').fill(password);
  await page.getByLabel('I am at least 16 years old.').check();
  await page.getByRole('checkbox', { name: /I accept the Terms of use/ }).check();
  await page.getByRole('button', { name: 'Sign up' }).click();
  await expect(page.getByRole('heading', { name: 'Check your inbox' })).toBeVisible();
  await page.getByRole('button', { name: 'Mock mailbox' }).click();
  await page.getByRole('link', { name: 'Open link' }).first().click();
  await expect(page.getByText('Your e-mail address is confirmed')).toBeVisible();

  await login(page, email, password);
  await expect(page.getByRole('heading', { name: 'Create your first topic' })).toBeVisible();

  // Create a topic with one document (consent required).
  await page.getByRole('button', { name: 'New topic' }).first().click();
  const dialog = page.getByRole('dialog', { name: 'New topic' });
  await dialog.getByLabel(/^Name/).fill('Cell biology');
  await dialog.locator('input[type=file]').setInputFiles({
    name: 'cells.txt',
    mimeType: 'text/plain',
    buffer: Buffer.from(
      'The cell is the basic unit of life in every living organism. The nucleus stores the genetic information of the cell. ' +
        'Mitochondria produce most of the chemical energy needed by the cell. The cell membrane controls what enters and leaves the cell. ' +
        'Ribosomes build proteins from amino acids according to the genetic code. Plant cells also have a rigid cell wall made of cellulose.',
    ),
  });
  await dialog.getByRole('button', { name: 'Create and upload' }).click();
  await expect(dialog.getByText('Please tick the box to upload.')).toBeVisible();
  await dialog.getByRole('checkbox', { name: /I confirm that I may use these documents/ }).check();
  await dialog.getByRole('button', { name: 'Create and upload' }).click();

  await expect(page).toHaveURL(/\/topics\/top_[^/]+\/files$/);
  await expect(page.getByRole('heading', { name: 'Cell biology', level: 1 })).toBeVisible();
  await expect(page.getByText('Ready', { exact: true })).toBeVisible({ timeout: 20_000 });

  // Generate a test from the chat.
  await page.getByRole('link', { name: 'Chat' }).click();
  await page.getByRole('button', { name: /questions ·/ }).click();
  await page.getByLabel('Number of questions').fill('3');
  await page.getByLabel('Describe the test (optional), e.g. “focus on the light reactions”…').fill('Focus on organelles');
  await page.getByRole('button', { name: 'Generate test' }).click();
  await page.getByRole('link', { name: 'Review and edit the test' }).click({ timeout: 30_000 });

  // Review: reorder, then save to "My tests".
  await expect(page.getByText('3 questions')).toBeVisible();
  const firstText = await page.getByPlaceholder('Question text').first().inputValue();
  await page.getByRole('button', { name: 'Move question down' }).first().click();
  await expect(page.getByPlaceholder('Question text').nth(1)).toHaveValue(firstText);
  await page.getByRole('checkbox', { name: /Save to "My tests"/ }).check();
  await page.getByRole('button', { name: 'Save changes' }).click();
  await expect(page.getByText('Saved to “My tests”.').first()).toBeVisible();

  // Export as JSON.
  await page.getByRole('button', { name: 'Export' }).click();
  await page.getByLabel('JSON').check();
  const [download] = await Promise.all([page.waitForEvent('download'), page.getByRole('button', { name: 'Download' }).click()]);
  expect(download.suggestedFilename()).toMatch(/\.json$/);

  // The saved test appears under "My tests", grouped by topic.
  if (isMobile) await page.getByRole('button', { name: 'Open menu' }).click();
  await page.getByRole('link', { name: 'My tests' }).first().click();
  await expect(page.getByRole('heading', { name: /Cell biology/ })).toBeVisible();

  // Delete the topic (type the name to confirm); everything goes with it.
  await page.getByRole('link', { name: 'Cell biology', exact: true }).click();
  await page.getByRole('button', { name: 'Delete topic' }).click();
  const confirm = page.getByRole('alertdialog', { name: 'Delete this topic?' });
  await expect(confirm.getByRole('button', { name: 'Delete permanently' })).toBeDisabled();
  await confirm.getByLabel(/Type "Cell biology" to confirm/).fill('Cell biology');
  await confirm.getByRole('button', { name: 'Delete permanently' }).click();
  await expect(page).toHaveURL(/\/topics$/);
  await expect(page.getByRole('heading', { name: 'Create your first topic' })).toBeVisible({ timeout: 20_000 });
});

test('topics are private to their owner', async ({ page, isMobile }) => {
  await prepare(page);
  await login(page);
  await page.goto('/topics/top_demo/chat');
  await expect(page.getByRole('heading', { name: 'Fotoszintézis (demo)', level: 1 })).toBeVisible();
  if (isMobile) await page.getByRole('button', { name: 'Open menu' }).click();
  await page.getByRole('button', { name: 'Sign out' }).click();

  // A different (fresh) user gets "not found" for the same URL.
  await page.goto('/register');
  const email = `other-${Date.now()}@x.hu`;
  await page.getByLabel('Email address').fill(email);
  await page.getByLabel('Password', { exact: true }).fill('another long password');
  await page.getByLabel('Confirm password').fill('another long password');
  await page.getByLabel('I am at least 16 years old.').check();
  await page.getByRole('checkbox', { name: /I accept the Terms of use/ }).check();
  await page.getByRole('button', { name: 'Sign up' }).click();
  await page.getByRole('button', { name: 'Mock mailbox' }).click();
  await page.getByRole('link', { name: 'Open link' }).first().click();
  await expect(page.getByText('Your e-mail address is confirmed')).toBeVisible();
  await login(page, email, 'another long password');
  await page.goto('/topics/top_demo/chat');
  await expect(page.getByRole('heading', { name: 'Topic not found' })).toBeVisible();
});
