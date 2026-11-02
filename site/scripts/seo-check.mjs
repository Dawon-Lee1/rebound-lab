// Checks the built site (dist/) for search basics. Run after `npm run build`: npm run check:seo
// Every indexable page: unique <title>, unique description of 1–155 chars, one canonical that is in the sitemap,
// absolute og:image. Sitemap: no 404, no Search Console verification file. Verification file unchanged.
import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const dist = new URL("../dist/", import.meta.url).pathname.replace(/^\/([A-Z]:)/, "$1");
const VERIFY = "google9f13221fa911af61.html";
const errors = [];
const err = (m) => errors.push(m);

const pages = [];
const walk = (dir) => {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) walk(p);
    else if (name === "index.html") pages.push(p);
  }
};
walk(dist);

const sitemap = readFileSync(join(dist, "sitemap-0.xml"), "utf8");
const locs = new Set([...sitemap.matchAll(/<loc>([^<]+)<\/loc>/g)].map((m) => m[1]));
for (const u of locs) if (/\/404\/?$/.test(u) || u.includes("google")) err(`sitemap has ${u}`);

const one = (html, re) => [...html.matchAll(re)].map((m) => m[1]);
const decode = (s) => s.replace(/&amp;/g, "&").replace(/&#39;/g, "'").replace(/&quot;/g, '"');
const seenTitle = new Map();
const seenDesc = new Map();
for (const file of pages) {
  const html = readFileSync(file, "utf8");
  const rel = file.slice(dist.length);
  const titles = one(html, /<title>([^<]*)<\/title>/g);
  const descs = one(html, /<meta name="description" content="([^"]*)"/g).map(decode);
  const canon = one(html, /<link rel="canonical" href="([^"]*)"/g);
  const ogImg = one(html, /<meta property="og:image" content="([^"]*)"/g);
  if (titles.length !== 1) err(`${rel}: ${titles.length} <title>`);
  if (descs.length !== 1) err(`${rel}: ${descs.length} descriptions`);
  else if (descs[0].length > 155) err(`${rel}: description ${descs[0].length} chars`);
  if (canon.length !== 1) err(`${rel}: ${canon.length} canonical`);
  else if (!locs.has(canon[0])) err(`${rel}: canonical ${canon[0]} not in sitemap`);
  if (ogImg.length !== 1 || !/^https:\/\//.test(ogImg[0])) err(`${rel}: og:image missing or relative`);
  for (const [seen, v] of [[seenTitle, titles[0]], [seenDesc, descs[0]]]) {
    if (v && seen.has(v)) err(`${rel}: duplicate of ${seen.get(v)}: ${v}`);
    else if (v) seen.set(v, rel);
  }
}
if (pages.length !== locs.size) err(`${pages.length} pages but ${locs.size} sitemap URLs`);

const src = readFileSync(new URL(`../public/${VERIFY}`, import.meta.url));
if (!src.equals(readFileSync(join(dist, VERIFY)))) err(`${VERIFY} in dist differs from public/`);

if (errors.length) {
  console.error(errors.slice(0, 30).join("\n"));
  console.error(`FAIL: ${errors.length} problem(s)`);
  process.exit(1);
}
console.log(`OK: ${pages.length} pages`);
