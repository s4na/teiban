import console from 'node:console';
import { mkdir, copyFile, rm } from 'node:fs/promises';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const dist = join(root, 'dist');
const staging = join(dist, 'extension');
await rm(staging, { recursive: true, force: true });
await mkdir(staging, { recursive: true });
// An explicit allowlist keeps dependencies, tests and local files out of the ZIP.
for (const file of ['manifest.json', 'content.js', 'content.css']) {
  await copyFile(join(root, 'extension', file), join(staging, file));
}
const archive = join(dist, 'extension.zip');
await rm(archive, { force: true });
execFileSync('zip', ['-q', archive, 'manifest.json', 'content.js', 'content.css'], { cwd: staging });
console.log(`Packaged ${archive}`);
