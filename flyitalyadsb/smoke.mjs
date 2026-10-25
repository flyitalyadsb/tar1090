// flyitalyadsb: browser smoke test of tar1090 before an image is built.
//
//   cd flyitalyadsb && npm ci && npx playwright install --with-deps chromium
//   node smoke.mjs [SOURCE_DIR]   (default: the repository root)
//
// Serves html/ with a fake readsb (/data/receiver.json, /data/aircraft.json
// with one aircraft), loads the page in headless Chromium and fails if the
// page throws a JavaScript error, the aircraft never shows up in the table, or
// the lookup tables of add-db.sh don't load (db-*.js go out gzipped, as
// nginx.conf sends them).
// Nobody looks at cell B's map, so without this a broken UI would pass the
// canary soak and reach the public map. Map tiles may fail to load: that's
// the network, not tar1090.
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { chromium } from 'playwright';

const root = path.resolve(process.argv[2] || path.join(import.meta.dirname, '..'));
const html = path.join(root, 'html');
const now = () => Date.now() / 1000;
const data = {
  '/data/receiver.json': () => ({ version: 'smoke', refresh: 1000, history: 0, lat: 45.4642, lon: 9.19 }),
  '/data/aircraft.json': () => ({
    now: now(), messages: 1000,
    aircraft: [{ hex: '4b1805', flight: 'SMOKE1  ', lat: 45.5, lon: 9.2, alt_baro: 12000, gs: 300, track: 90,
                 seen: 0.1, seen_pos: 0.1, messages: 100, rssi: -10 }],
  }),
};
const types = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.png': 'image/png',
                '.svg': 'image/svg+xml', '.json': 'application/json', '.woff2': 'font/woff2' };

const server = http.createServer((req, res) => {
  const url = new URL(req.url, 'http://x');
  if (data[url.pathname]) {
    res.writeHead(200, { 'content-type': 'application/json' });
    return res.end(JSON.stringify(data[url.pathname]()));
  }
  let p = path.join(html, decodeURIComponent(url.pathname));
  if (!p.startsWith(html)) { res.writeHead(403); return res.end(); }
  if (fs.existsSync(p) && fs.statSync(p).isDirectory()) p = path.join(p, 'index.html');
  if (!fs.existsSync(p)) { res.writeHead(404); return res.end(); }
  const headers = { 'content-type': types[path.extname(p)] || 'application/octet-stream' };
  if (/^\/db-.*\.js$/.test(url.pathname)) headers['content-encoding'] = 'gzip';
  res.writeHead(200, headers);
  fs.createReadStream(p).pipe(res);
});
await new Promise((r) => server.listen(0, '127.0.0.1', r));
const base = `http://127.0.0.1:${server.address().port}/`;

const browser = await chromium.launch();
const page = await browser.newPage();
const errors = [];
page.on('pageerror', (e) => errors.push(e.message));
page.on('response', (r) => {
  if (/\/db-[^/]*\//.test(r.url()) && r.status() >= 400) errors.push(`${r.status()} on ${r.url()}`);
});
let ok = false;
try {
  await page.goto(base, { waitUntil: 'load', timeout: 30000 });
  await page.waitForFunction(() => document.body.innerText.includes('SMOKE1'), null, { timeout: 30000 });
  ok = true;
} catch (e) {
  errors.push(`aircraft SMOKE1 never appeared: ${e.message.split('\n')[0]}`);
}
try {
  if (ok) {
    await page.waitForFunction(() => g.type_cache && operatorsCache && Object.keys(operatorsCache).length, null, { timeout: 15000 });
    const db = await page.evaluate(() => ({
      type: g.type_cache.A320,
      airline: lookupAirlineForCallsign('ITY123', ''),
      milRanges: milRanges.length,
    }));
    if (!db.type || !db.airline || !db.milRanges) errors.push(`lookup tables incomplete: ${JSON.stringify(db)}`);
  }
} catch (e) {
  errors.push(`aircraft types and airlines never loaded: ${e.message.split('\n')[0]}`);
} finally {
  await browser.close();
  server.close();
}
for (const e of errors) console.error('ERROR:', e);
console.log(ok && !errors.length ? 'smoke ok' : `smoke FAILED (${errors.length} error(s))`);
process.exit(ok && !errors.length ? 0 : 1);
