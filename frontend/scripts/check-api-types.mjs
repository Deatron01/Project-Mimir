// Fails if src/api/schema.d.ts is out of date with openapi/mimir-public.yaml (run `npm run api:types` to fix).
import { execFileSync } from 'node:child_process';
import { mkdtempSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const out = join(mkdtempSync(join(tmpdir(), 'mimir-api-')), 'schema.d.ts');
execFileSync(process.execPath, ['node_modules/openapi-typescript/bin/cli.js', 'openapi/mimir-public.yaml', '-o', out, '--default-non-nullable', 'false'], { stdio: 'ignore' });
const norm = (s) => s.replace(/\r\n/g, '\n').trim();
if (norm(readFileSync(out, 'utf8')) !== norm(readFileSync('src/api/schema.d.ts', 'utf8'))) {
  console.error('src/api/schema.d.ts is out of date. Run `npm run api:types` and commit the result.');
  process.exit(1);
}
console.log('api types ok: src/api/schema.d.ts matches openapi/mimir-public.yaml');
