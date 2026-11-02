import type { APIRoute } from "astro";
import { meta, players } from "../data/players";

// llmstxt.org format: what the site is, where the key pages are, where the data comes from and its limits.
export const GET: APIRoute = ({ site }) => {
  const url = (path: string) => new URL(path, site).href;
  const season = meta.data_season;
  const body = `# Rebound Lab

> Rebound Lab is a free tool for ${season + 1} season-long fantasy baseball drafts. It compares ${players.length} MLB hitters' ${season} results (wOBA) with the quality of their contact (xwOBA) to find buy-low and sell-high candidates. Each hitter's projected ${season + 1} wOBA change splits into Luck (the xwOBA–wOBA gap) and Regression (the pull toward the league average).

## Key pages

- [Board](${url("/")}): all hitters ranked in Buy-Low, Sell-High and Rebound tabs
- [Methodology](${url("/methodology/")}): the projection formula, backtest results and limitations
- [FAQ](${url("/methodology/#m-faq")}): short answers about xwOBA, Luck, Proj. change and the playing-time flag
- Player pages: ${url("/player/")}{MLBAM player ID}/

## Data and limits

Season totals from Baseball Savant (MLB Advanced Media). The backtest only covers hitters with ${meta.backtest.min_pa_next}+ PA the next season; the projection does not adjust for age and is not translated into fantasy categories (AVG, HR, R, RBI, SB). Not betting advice.
`;
  return new Response(body, { headers: { "Content-Type": "text/plain; charset=utf-8" } });
};
