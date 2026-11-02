import { test } from "node:test";
import assert from "node:assert/strict";
import { bare, barPct, explain, metaLine, ownShare, signed, tipChange, tipLuck, tipReg } from "./explain.ts";

test("signed", () => {
  assert.equal(signed(0.034), "+.034");
  assert.equal(signed(-0.012), "−.012");
  assert.equal(signed(0), ".000");
  assert.equal(signed(-0.0004), ".000"); // rounds to zero: no sign
});

test("bare", () => {
  assert.equal(bare(0.287), ".287");
  assert.equal(bare(1.05), "1.050");
});

test("barPct", () => {
  assert.equal(barPct(0.069, 0.069), 100);
  assert.equal(barPct(-0.2, 0.1), 100);
  assert.equal(barPct(0.01, 0), 0);
  assert.equal(barPct(-0.025, 0.1), 25);
});

test("metaLine", () => {
  assert.equal(metaLine({ team: "CIN", team_status: "active", age: 30 }), "CIN, age 30");
  assert.equal(metaLine({ team: null, team_status: "fa", age: 30 }), "FA, age 30");
  assert.equal(metaLine({ team: null, team_status: "unknown", age: 30 }), "age 30");
  assert.equal(metaLine({ team: null, team_status: "unknown", age: null }), "");
});

const lg = 0.316;

test("explain: Hayes, same signs, regression dominates", () => {
  const p = { woba: 0.191, xwoba: 0.287, luck: 0.034, regression: 0.069, rebound_score: 0.103, proj_woba_2027: 0.294 };
  assert.equal(
    explain(p, lg),
    "Hit the ball like a .287 wOBA hitter but produced .191. Projected change +.103, mostly from regression toward the league average.",
  );
});

test("explain: opposite signs", () => {
  const p = { woba: 0.36, xwoba: 0.375, luck: 0.01, regression: -0.02, rebound_score: -0.01, proj_woba_2027: 0.35 };
  const s = explain(p, lg);
  assert.match(s, /Luck adds \+\.010/);
  assert.match(s, /takes −\.020/);
  assert.match(s, /\.316/);
});

test("explain: negative luck, positive regression", () => {
  const p = { woba: 0.3, xwoba: 0.28, luck: -0.012, regression: 0.008, rebound_score: -0.004, proj_woba_2027: 0.296 };
  const s = explain(p, lg);
  assert.match(s, /^Produced a \.300 wOBA on contact that earned \.280\./);
  assert.match(s, /Luck takes −\.012, but regression toward the league average \(\.316\) adds \+\.008/);
});

test("explain: luck 0", () => {
  const p = { woba: 0.33, xwoba: 0.33, luck: 0, regression: -0.006, rebound_score: -0.006, proj_woba_2027: 0.324 };
  const s = explain(p, lg);
  assert.match(s, /Results matched contact quality/);
  assert.match(s, /regression toward the league average/);
  assert.doesNotMatch(s, /NaN|undefined|Luck adds/);
});

test("explain: both zero", () => {
  const p = { woba: 0.316, xwoba: 0.316, luck: 0, regression: 0, rebound_score: 0, proj_woba_2027: 0.316 };
  assert.match(explain(p, lg), /No projected change\.$/);
});

test("tips", () => {
  const p = { pa: 242, woba: 0.191, xwoba: 0.287, luck: 0.034, regression: 0.069, rebound_score: 0.103, proj_woba_2027: 0.294 };
  assert.match(tipLuck(p), /contact quality beat results, so \+\.034/);
  assert.match(tipLuck({ ...p, luck: 0 }), /luck adds nothing/);
  assert.match(tipLuck({ ...p, luck: -0.01 }), /results beat contact quality, so −\.010/);
  assert.equal(tipReg(p, 0.316), "242 PA at a .191 wOBA pulls the projection +.069 toward the league average (.316). Fewer PA means a bigger pull.");
  assert.equal(tipChange(p, 2027), "Luck +.034 plus regression +.069 = +.103, for a projected 2027 wOBA of .294.");
});

test("ownShare", () => {
  assert.equal(ownShare(300, 300), 0.5);
  assert.equal(ownShare(0, 300), 0);
});
