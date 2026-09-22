// WCAG 2.2 AA gate for every palette x mode combination.
// Text pairs need 4.5:1, large/UI pairs need 3:1. Exits 1 on any failure.
import { readFileSync } from 'node:fs';
import { contrast } from './color-utils.mjs';

const data = JSON.parse(readFileSync(new URL('../src/theme/palettes.json', import.meta.url), 'utf8'));

const RULES = [
  ['text', 'bg', 4.5],
  ['text', 'surface', 4.5],
  ['muted', 'bg', 4.5],
  ['muted', 'surface', 4.5],
  ['accent', 'bg', 4.5],
  ['accent', 'surface', 4.5],
  ['onPrimary', 'primary', 4.5],
  ['primary', 'bg', 3],
  ['danger', 'bg', 4.5],
  ['danger', 'surface', 4.5],
  ['success', 'bg', 4.5],
  ['success', 'surface', 4.5],
  ['warning', 'bg', 4.5],
];

let failures = 0;
for (const p of data.palettes) {
  for (const mode of ['dark', 'light']) {
    const c = p[mode];
    const bad = RULES.filter(([fg, bg, min]) => contrast(c[fg], c[bg]) < min).map(
      ([fg, bg, min]) => `${fg}/${bg} ${contrast(c[fg], c[bg]).toFixed(2)} < ${min}`,
    );
    failures += bad.length;
    console.log(`${bad.length ? 'FAIL' : 'ok  '} ${p.id.padEnd(9)} ${mode.padEnd(5)} ${bad.join(', ')}`);
  }
}
if (failures) {
  console.error(`\n${failures} contrast failure(s).`);
  process.exit(1);
}
console.log('\nAll palettes pass WCAG AA.');
