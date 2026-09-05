/**
 * Screen capture for the SlateIQ trailer.
 *
 *   node video/capture.mjs                # every scene
 *   node video/capture.mjs hero dpr       # only those scenes
 *
 * Each scene records its own 1920x1080 webm into data/video/raw/<name>.webm.
 * App scenes drive the real SlateIQ UI (local by default — identical build to
 * Cloud Run, just faster); the `live` scene deliberately drives the hosted
 * Cloud Run service so the closing beat is genuinely the deployed app.
 */
import { chromium } from 'playwright';
import http from 'node:http';
import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const ROOT = path.resolve(HERE, '..');
const RAW = path.join(ROOT, 'data', 'video', 'raw');
const CARDS = path.join(HERE, 'cards');

const APP = process.env.SLATEIQ_URL || 'http://localhost:8811';
const LIVE = process.env.SLATEIQ_LIVE_URL || 'https://slateiq-957930801789.us-central1.run.app';
const CARD_PORT = 8899;

const VIEW = { width: 1920, height: 1080 };
const MIME = { '.html': 'text/html', '.css': 'text/css', '.mp4': 'video/mp4', '.jpg': 'image/jpeg', '.js': 'text/javascript' };

/** Static server for the card pages (they reference real clips and thumbnails). */
function serveCards() {
  return http
    .createServer((req, res) => {
      const rel = decodeURIComponent(req.url.split('?')[0]).replace(/^\/+/, '') || 'index.html';
      const file = path.join(CARDS, rel);
      if (!file.startsWith(CARDS) && !fsSync.existsSync(file)) return res.writeHead(404).end();
      fsSync.readFile(file, (err, buf) => {
        if (err) return res.writeHead(404).end('nope');
        res.writeHead(200, { 'content-type': MIME[path.extname(file)] || 'application/octet-stream' });
        res.end(buf);
      });
    })
    .listen(CARD_PORT);
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

/* ------------------------------------------------------------------ helpers */

/** Type a question at human speed, send it, and wait out the agent (20–60 s). */
async function ask(page, question, { settle = 2200 } = {}) {
  const ta = page.locator('#ask-input');
  await ta.click();
  await ta.pressSequentially(question, { delay: 52 });
  await sleep(700);
  await ta.press('Enter');
  const stop = page.getByRole('button', { name: 'Stop' });
  await stop.waitFor({ state: 'visible', timeout: 30_000 }).catch(() => {});
  await stop.waitFor({ state: 'hidden', timeout: 300_000 }).catch(() => {});
  await sleep(settle);
}

/** Blow the docked trace panel up to the full frame — the Stage-1 evidence shot. */
async function traceFullFrame(page, mark, hold = 6500) {
  await page.evaluate(() => {
    const aside = document.querySelector('section[aria-label="Agent trace"]').closest('aside');
    const convo = aside.parentElement.firstElementChild;
    convo.style.display = 'none';
    Object.assign(aside.style, { width: '100vw', maxWidth: 'none', borderLeft: 'none' });
    const st = document.createElement('style');
    st.id = 'fs-trace';
    st.textContent = `
      aside pre, aside pre code { font-size: 22px !important; line-height: 1.62 !important; }
      aside pre { padding: 40px 26px 22px !important; }
      aside .font-mono { font-size: 19px !important; }
      aside h2 { font-size: 21px !important; letter-spacing: .16em !important; }
      aside p, aside li span, aside li p { font-size: 17.5px !important; }
      aside [class*="chip"] { font-size: 14px !important; padding: 5px 11px !important; }
      aside ol { max-width: 1560px; margin: 0 auto; }
      aside > div { padding: 26px 40px !important; }
      aside > header, aside > p { padding: 20px 40px !important; }`;
    document.head.appendChild(st);
  });
  await sleep(500);
  mark('traceIn');
  // put the first statement with real SQL at the top of the frame
  await page.evaluate(() => {
    const pre = document.querySelector('section[aria-label="Agent trace"] pre');
    if (pre) pre.closest('li').scrollIntoView({ block: 'start' });
  });
  await sleep(hold);
  mark('traceOut');
  await page.evaluate(() => {
    const aside = document.querySelector('section[aria-label="Agent trace"]').closest('aside');
    aside.parentElement.firstElementChild.style.display = '';
    Object.assign(aside.style, { width: '', maxWidth: '', borderLeft: '' });
    document.getElementById('fs-trace')?.remove();
  });
  await sleep(700);
}

/** Hover then click a cited take's poster frame; the player autoplays at the cited offset. */
async function playFirstTake(page, { hover = 1200, play = 5000, nth = 0 } = {}) {
  const target = page.locator('button[aria-label^="Play take"]').nth(nth);
  if (!(await target.count())) return false;
  await target.scrollIntoViewIfNeeded().catch(() => {});
  await target.hover().catch(() => {});
  await sleep(hover);
  await target.click({ timeout: 8000 }).catch(() => {});
  await sleep(1200);
  await page.evaluate(() => document.querySelector('video')?.play?.());
  await sleep(play);
  return true;
}

/** The Takes-browser drawer: flag timeline, transcript, player. */
async function openTakeDrawer(page, { dwell = 5000 } = {}) {
  const open = page.getByRole('button', { name: /Open take/ }).first();
  if (!(await open.count())) return false;
  await open.scrollIntoViewIfNeeded().catch(() => {});
  await open.click({ timeout: 8000 }).catch(() => {});
  await sleep(1500);
  await page.evaluate(() => document.querySelector('[role="dialog"] video')?.play?.());
  await sleep(dwell);
  return true;
}

async function gotoApp(page, hash) {
  await page.goto(`${APP}/#${hash}`, { waitUntil: 'networkidle', timeout: 60_000 });
  await sleep(1500);
}

/* ------------------------------------------------------------------- scenes */

const SCENES = {
  /* --- rendered cards ------------------------------------------------ */
  title: card('title.html'),
  cost: card('cost.html', 14_000),
  ingest: card('ingest.html'),
  terminal: card('terminal.html'),
  arch: card('arch.html'),
  end: card('end.html'),

  /* --- the app -------------------------------------------------------- */
  async hero(page, mark) {
    await gotoApp(page, 'ask');
    await ask(page, 'Which circled takes are measurably soft?');
    mark('answered');
    await sleep(3500);
    await traceFullFrame(page, mark, 7500);
    mark('takeIn');
    await playFirstTake(page, { play: 7000 });
    await sleep(1500);
  },

  // Scene 12 is one of the day-12 scenes with real ingested footage, so the
  // cited takes actually play — a synthetic scene would render "media not published".
  async editor(page, mark) {
    await gotoApp(page, 'ask');
    await ask(page, 'Where does Celia mention her robot hand?');
    mark('answered');
    await sleep(3000);
    await playFirstTake(page, { play: 7000 });
    await sleep(1500);
  },

  async producer(page, mark) {
    await gotoApp(page, 'ask');
    await ask(page, 'Are we on schedule after day 12?');
    mark('answered');
    await sleep(1500);
    await page.mouse.wheel(0, 500);
    await sleep(4000);
  },

  async continuity(page, mark) {
    await gotoApp(page, 'ask');
    await ask(page, 'Continuity issues in scene 41');
    mark('answered');
    await sleep(2000);
    await page.mouse.wheel(0, 420);
    await sleep(4500);
  },

  async dpr(page, mark) {
    await gotoApp(page, 'health');
    const gen = page.getByRole('button', { name: /Generate Daily Progress Report/i });
    await gen.scrollIntoViewIfNeeded();
    await sleep(1200);
    await gen.click();
    await page.getByRole('button', { name: /Generating/i }).waitFor({ state: 'hidden', timeout: 420_000 }).catch(() => {});
    await sleep(2000);
    mark('report');
    for (const dy of [280, 300, 300, 300]) { await page.mouse.wheel(0, dy); await sleep(2700); }
    await page.getByRole('button', { name: /Read it aloud/i }).click().catch(() => {});
    mark('aloud');
    await sleep(10_000);
  },

  /**
   * Driven against the hosted service on purpose: Grafana is wired up there via
   * /api/config, so the panels the voiceover promises are the ones on screen.
   */
  async health(page, mark) {
    await page.goto(`${LIVE}/#health`, { waitUntil: 'domcontentloaded', timeout: 90_000 });
    // The d-solo iframes never go network-idle, and Grafana renders them slowly
    // on a cold Cloud Run instance — wait for their load events, then let them paint.
    await page.waitForSelector('iframe', { timeout: 60_000 }).catch(() => {});
    await page
      .evaluate(
        () =>
          Promise.race([
            Promise.all(
              [...document.querySelectorAll('iframe')].map(
                (f) => new Promise((r) => f.addEventListener('load', r, { once: true })),
              ),
            ),
            new Promise((r) => setTimeout(r, 45_000)),
          ]),
        undefined,
      )
      .catch(() => {});
    await sleep(9000);
    mark('charts');
    await sleep(6000);
    await page.mouse.wheel(0, 620);
    await sleep(5000);
    await page.goto(`${LIVE}/#takes`, { waitUntil: 'domcontentloaded', timeout: 90_000 });
    await sleep(7000);
    mark('takes');
    await page.mouse.wheel(0, 520);
    await sleep(3500);
    await openTakeDrawer(page, { dwell: 7000 });
  },

  /** Deliberately the hosted Cloud Run service, not localhost. */
  async live(page, mark) {
    await page.goto(`${LIVE}/#about`, { waitUntil: 'networkidle', timeout: 90_000 });
    await sleep(4500);
    await page.getByRole('heading', { name: 'Live', exact: true }).scrollIntoViewIfNeeded().catch(() => {});
    await sleep(1200);
    mark('urls');
    await sleep(9000);
  },
};

function card(file, ms) {
  return async (page, _mark) => {
    await page.goto(`http://localhost:${CARD_PORT}/${file}`, { waitUntil: 'load' });
    const dur = ms ?? (await page.evaluate(() => window.__duration ?? 12000));
    await sleep(dur);
  };
}

/* --------------------------------------------------------------------- main */

const wanted = process.argv.slice(2).length ? process.argv.slice(2) : Object.keys(SCENES);

await fs.mkdir(RAW, { recursive: true });
const MARKS = path.join(RAW, 'markers.json');
const marks = fsSync.existsSync(MARKS) ? JSON.parse(fsSync.readFileSync(MARKS, 'utf8')) : {};
const server = serveCards();
/**
 * `npx playwright install chromium` can fail behind a flaky network; if any
 * Playwright chromium build is already in the shared cache, use that instead of
 * making the render depend on a download.
 */
function findChrome() {
  if (process.env.SLATEIQ_CHROME) return process.env.SLATEIQ_CHROME;
  const cache = path.join(process.env.HOME, '.cache', 'ms-playwright');
  if (!fsSync.existsSync(cache)) return undefined;
  for (const dir of fsSync.readdirSync(cache).filter((d) => d.startsWith('chromium-')).sort().reverse()) {
    for (const rel of ['chrome-linux64/chrome', 'chrome-linux/chrome']) {
      const exe = path.join(cache, dir, rel);
      if (fsSync.existsSync(exe)) return exe;
    }
  }
  return undefined;
}
const CHROME = findChrome();
const browser = await chromium.launch({ executablePath: CHROME, args: ['--autoplay-policy=no-user-gesture-required', '--hide-scrollbars'] });

for (const name of wanted) {
  const fn = SCENES[name];
  if (!fn) { console.error(`no scene "${name}"`); continue; }
  const t0 = Date.now();
  const ctx = await browser.newContext({
    viewport: VIEW,
    deviceScaleFactor: 1,
    recordVideo: { dir: RAW, size: VIEW },
    permissions: [],
  });
  const page = await ctx.newPage();
  const t1 = Date.now();
  marks[name] = {};
  const mark = (label) => { marks[name][label] = +((Date.now() - t1) / 1000).toFixed(2); };
  try {
    await fn(page, mark);
  } catch (e) {
    console.error(`  scene ${name} threw: ${e.message}`);
  }
  const video = page.video();
  await ctx.close();
  const src = await video.path();
  const dst = path.join(RAW, `${name}.webm`);
  await fs.rm(dst, { force: true });
  await fs.rename(src, dst);
  console.log(`${name.padEnd(11)} ${((Date.now() - t0) / 1000).toFixed(1)}s  →  ${path.relative(ROOT, dst)}`);
}

await fs.writeFile(MARKS, JSON.stringify(marks, null, 2));
await browser.close();
server.close();
