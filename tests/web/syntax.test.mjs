// Every module /play loads parses (a slip in one, such as a name declared twice, stops the whole
// page at its loading screen, and most modules aren't imported by the other tests).
//   node --test tests/web/
import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../../src/web_isometric');
const files = ['world3d', 'world3d/hud', 'shared'].flatMap(d => fs.readdirSync(path.join(ROOT, d))
  .filter(f => f.endsWith('.js')).map(f => path.join(d, f)));

test('every /play module parses', () => {
  const bad = [];
  for (const f of files) {
    const src = fs.readFileSync(path.join(ROOT, f), 'utf8');
    const esm = /^\s*(import|export)\s/m.test(src);
    const r = spawnSync(process.execPath, ['--check', ...(esm ? ['--input-type=module'] : [])], { input: src, encoding: 'utf8' });
    if (r.status !== 0) bad.push(`${f}: ${(r.stderr.match(/SyntaxError[^\n]*/) || [r.stderr.slice(0, 200)])[0]}`);
  }
  assert.deepEqual(bad, [], bad.join('\n'));
  assert.ok(files.length > 40, `found the modules (${files.length})`);
});
