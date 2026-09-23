// Fails if the hu and en translation files have different keys, or if the source uses a key that doesn't exist.
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const root = new URL('../src/', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
const load = (lng) => JSON.parse(readFileSync(join(root, 'locales', lng, 'translation.json'), 'utf8'));

const flatten = (obj, prefix = '') =>
  Object.entries(obj).flatMap(([k, v]) => {
    const key = prefix ? `${prefix}.${k}` : k;
    if (Array.isArray(v)) return [`${key}[${v.length}]`, ...v.flatMap((x, i) => (typeof x === 'object' ? flatten(x, `${key}.${i}`) : []))];
    return v && typeof v === 'object' ? flatten(v, key) : [key];
  });

const hu = new Set(flatten(load('hu')));
const en = new Set(flatten(load('en')));
const problems = [];
for (const k of hu) if (!en.has(k)) problems.push(`missing in en: ${k}`);
for (const k of en) if (!hu.has(k)) problems.push(`missing in hu: ${k}`);

// Keys used in code: t('a.b'), i18nKey="a.b". Plural keys resolve to key_one / key_other.
const files = [];
const walk = (dir) =>
  readdirSync(dir).forEach((f) => {
    const p = join(dir, f);
    if (statSync(p).isDirectory()) walk(p);
    else if (/\.(jsx?|tsx?)$/.test(f)) files.push(p);
  });
walk(root);
const base = new Set([...hu].map((k) => k.replace(/\[\d+\]$/, '').replace(/_(one|other)$/, '')));
const prefixes = new Set([...base].flatMap((k) => k.split('.').map((_, i, a) => a.slice(0, i + 1).join('.'))));
for (const f of files) {
  const src = readFileSync(f, 'utf8');
  for (const m of src.matchAll(/(?:\bt\(\s*|i18nKey=)['"`]([\w.-]+)['"`]/g)) {
    if (!prefixes.has(m[1])) problems.push(`unknown key "${m[1]}" in ${f.slice(root.length)}`);
  }
}

// Keys built at runtime from API enums (errors.<CODE>, files.status.<status>, …) must exist for every enum value.
const specPath = new URL('../openapi/mimir-public.yaml', import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, '$1');
let spec = '';
try {
  spec = readFileSync(specPath, 'utf8');
} catch {
  /* spec not present – skip */
}
const enumOf = (name) => {
  const m = new RegExp(`\\n    ${name}:\\s*(?:\\n\\s*type: string\\n\\s*)?(?:\\{ type: string, )?enum: \\[([^\\]]+)\\]`).exec(spec);
  return m ? m[1].split(',').map((x) => x.trim()) : [];
};
const dynamic = [
  ['errors', [...enumOf('ErrorCode'), 'NETWORK', 'UNKNOWN']],
  ['files.status', enumOf('FileStatus')],
  ['jobs.type', enumOf('JobType')],
  ['jobs.status', enumOf('JobStatus')],
  ['editor.difficulty', enumOf('Difficulty')],
  ['editor.types', enumOf('QuestionType')],
];
if (spec) {
  for (const [prefix, values] of dynamic) {
    if (!values.length) problems.push(`could not read enum for ${prefix} from the OpenAPI spec`);
    for (const v of values) if (!hu.has(`${prefix}.${v}`)) problems.push(`missing dynamic key ${prefix}.${v}`);
  }
}

if (problems.length) {
  console.error(problems.join('\n'));
  process.exit(1);
}
console.log(`i18n ok: ${hu.size} keys in hu and en, all keys used in code exist.`);
