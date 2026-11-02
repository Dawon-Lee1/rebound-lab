// WCAG 2.1 contrast check for the color tokens in src/styles/global.css. Exits 1 on any failure.
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/styles/global.css", import.meta.url), "utf8");
const dark = css.indexOf("@media (prefers-color-scheme: dark)");
if (dark < 0) throw new Error("dark-mode block not found");
const tokens = (s) => Object.fromEntries([...s.matchAll(/--([a-z]+):\s*(#[0-9A-Fa-f]{6})/g)].map((m) => [m[1], m[2]]));
const modes = { light: tokens(css.slice(0, dark)), dark: tokens(css.slice(dark, css.indexOf("}", css.indexOf("}", dark) + 1))) };

const lum = (hex) => {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((v) => (v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};
export const ratio = (a, b) => {
  const [hi, lo] = [lum(a), lum(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
};
console.assert(Math.abs(ratio("#000000", "#FFFFFF") - 21) < 1e-9, "ratio self-check");

const checks = [
  ...["ink", "muted", "luck", "reg", "sell"].map((t) => [t, 4.5]), // text
  ["rule", 3], // bar zero-line and control borders (non-text, 1.4.11)
];
let failed = 0;
for (const [mode, t] of Object.entries(modes)) {
  for (const [fg, min] of checks) {
    for (const bg of ["bg", "surface"]) {
      if (!t[fg] || !t[bg]) throw new Error(`${mode}: missing --${fg} or --${bg}`);
      const r = ratio(t[fg], t[bg]);
      const ok = r >= min;
      failed += !ok;
      console.log(`${ok ? "PASS" : "FAIL"} ${mode.padEnd(5)} --${fg.padEnd(6)} on --${bg.padEnd(7)} ${r.toFixed(2)} (min ${min})`);
    }
  }
}
process.exit(failed ? 1 : 0);
