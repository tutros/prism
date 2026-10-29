// Post-build guard: fails if dist/ contains font sources that the production
// nginx CSP (frontend/nginx.conf, font-src 'self') would block. Run by
// `npm run build`, so the Docker image build fails on a regression too.
import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { extname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const dist = fileURLToPath(new URL('../dist/', import.meta.url));
const FORBIDDEN = ['data:font', 'fonts.googleapis.com', 'fonts.gstatic.com'];
const TEXT = new Set(['.css', '.js', '.html']);

function walk(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    return entry.isDirectory() ? walk(path) : [path];
  });
}

const problems = [];
let fontUrls = 0;
for (const file of walk(dist)) {
  if (!TEXT.has(extname(file))) continue;
  const text = readFileSync(file, 'utf8');
  for (const needle of FORBIDDEN) {
    const count = text.split(needle).length - 1;
    if (count) problems.push(`${file}: ${count} x ${needle}`);
  }
  if (extname(file) !== '.css') continue;
  // Every font url() must be a same-origin asset that exists in dist/.
  for (const match of text.matchAll(/url[(]["']?([^"')]+[.]woff2?)["']?[)]/g)) {
    fontUrls += 1;
    const url = match[1];
    if (!url.startsWith('/assets/') || !existsSync(join(dist, url))) {
      problems.push(`${file}: font url ${url} is not a same-origin asset in dist/`);
    }
  }
}

if (problems.length) {
  console.error('check-dist: font sources the nginx CSP would block:');
  for (const p of problems) console.error(`  ${p}`);
  process.exit(1);
}
console.log(`check-dist: ${fontUrls} font url(s), all same-origin files; no data: or Google font sources`);
