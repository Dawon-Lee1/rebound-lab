// Display helpers and the auto-generated player sentence. Pure functions, no data import, so `node --test` runs them directly.

/** ".287" — baseball style, no leading zero. */
export const bare = (x: number) => x.toFixed(3).replace(/^(-?)0\./, "$1.");

/** "+.034" / "−.012" (U+2212) / ".000" — sign always shown so meaning never relies on color. */
export const signed = (x: number) => {
  const s = bare(Math.abs(x));
  if (s === ".000") return s;
  return (x > 0 ? "+" : "−") + s;
};

/** Bar length as % of the shared scale, capped at 100. */
export const barPct = (x: number, max: number) => (max > 0 ? Math.min(100, (Math.abs(x) / max) * 100) : 0);

type Team = { team: string | null; team_status: string };
/** "CIN" / "FA" / "" — unknown team (API miss) is an empty string so it is not shown. */
export const teamLabel = (p: Team) => (p.team_status === "fa" ? "FA" : (p.team ?? ""));

/** "CIN, age 30". */
export const metaLine = (p: Team & { age: number | null }) =>
  [teamLabel(p), p.age != null ? `age ${p.age}` : null].filter(Boolean).join(", ");

type Line = { woba: number; xwoba: number; luck: number; regression: number; rebound_score: number; proj_woba_2027: number };
const REG = "regression toward the league average";

export function explain(p: Line, lg: number): string {
  const L = p.luck; // already rounded to 3 decimals by 05_build_json.py, so this matches the screen
  const R = p.regression;
  const C = signed(p.rebound_score);

  const first =
    L > 0
      ? `Hit the ball like a ${bare(p.xwoba)} wOBA hitter but produced ${bare(p.woba)}.`
      : L < 0
        ? `Produced a ${bare(p.woba)} wOBA on contact that earned ${bare(p.xwoba)}.`
        : `Results matched contact quality (${bare(p.woba)} wOBA, ${bare(p.xwoba)} xwOBA).`;

  let second: string;
  if (L === 0 && R === 0) second = "No projected change.";
  else if (L === 0) second = `Projected change ${C}, all from ${REG}.`;
  else if (R === 0) second = `Projected change ${C}, all from luck.`;
  else if (Math.sign(L) === Math.sign(R))
    second = `Projected change ${C}, mostly from ${Math.abs(L) >= Math.abs(R) ? "luck" : REG}.`;
  else
    second = `Luck ${L > 0 ? "adds" : "takes"} ${signed(p.luck)}, but ${REG} (${bare(lg)}) ${R > 0 ? "adds" : "takes"} ${signed(p.regression)}, for a projected change of ${C}.`;

  return `${first} ${second}`;
}

type Tip = { pa: number; woba: number; xwoba: number; luck: number; regression: number; rebound_score: number; proj_woba_2027: number };
/** Per-player popover text for the Luck, Regression and Proj. change numbers. */
export const tipLuck = (p: Tip) =>
  signed(p.luck) === ".000"
    ? `xwOBA ${bare(p.xwoba)} and wOBA ${bare(p.woba)} were close, so luck adds nothing.`
    : `xwOBA ${bare(p.xwoba)} vs wOBA ${bare(p.woba)}: ${p.luck > 0 ? "contact quality beat results" : "results beat contact quality"}, so ${signed(p.luck)} of the projected change is luck.`;
export const tipReg = (p: Tip, lg: number) =>
  `${p.pa} PA at a ${bare(p.woba)} wOBA pulls the projection ${signed(p.regression)} toward the league average (${bare(lg)}). Fewer PA means a bigger pull.`;
export const tipChange = (p: Tip, season: number) =>
  `Luck ${signed(p.luck)} plus regression ${signed(p.regression)} = ${signed(p.rebound_score)}, for a projected ${season} wOBA of ${bare(p.proj_woba_2027)}.`;
