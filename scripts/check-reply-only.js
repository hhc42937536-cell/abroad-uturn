import { readFile, readdir } from 'node:fs/promises';
import { join } from 'node:path';

const banned = [
  '/message/multicast',
  '/message/broadcast',
  '/message/narrowcast',
  'multicast',
  'broadcast',
  'narrowcast'
];

const roots = ['src', 'scripts'];
const offenders = [];

for (const root of roots) {
  for await (const file of walk(root)) {
    if (!file.endsWith('.js')) continue;
    if (file.replaceAll('\\', '/').endsWith('scripts/check-reply-only.js')) continue;
    const content = await readFile(file, 'utf8');
    for (const term of banned) {
      if (content.includes(term)) offenders.push(`${file}: ${term}`);
    }
  }
}

if (offenders.length) {
  console.error('Limited price-push policy violation:');
  console.error(offenders.join('\n'));
  process.exit(1);
}

console.log('limited price-push policy ok');

async function* walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  for (const entry of entries) {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) yield* walk(path);
    else yield path;
  }
}
