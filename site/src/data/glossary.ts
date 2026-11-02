// Column explanations: table header popovers and the "What do these columns mean?" list use the same text.
import { bare } from "../lib/explain";
import { meta } from "./players";

const lg = bare(meta.league_woba);
const next = meta.data_season + 1;

export const about = {
  pa: ["PA", `Plate appearances in ${meta.data_season}.`],
  woba: ["wOBA", `Weighted on-base average: one number for overall hitting results. League average in ${meta.data_season} was ${lg}.`],
  xwoba: ["xwOBA", "Expected wOBA from exit velocity, launch angle and, on some batted balls, sprint speed. It grades the contact, not where the ball landed."],
  luck: ["Luck", "The part of the projected change that comes from the gap between xwOBA and wOBA. Plus means contact beat results (unlucky). Minus means results beat contact (lucky)."],
  regression: ["Regression", `The pull toward the league average (${lg}). It is bigger when PA is low or wOBA is far from average.`],
  change: ["Proj. change", `Projected change in wOBA for ${next}: Luck plus Regression.`],
  proj: [`Proj. ${next} wOBA`, `${meta.data_season} wOBA plus Proj. change.`],
} as const;

export type AboutKey = keyof typeof about;
