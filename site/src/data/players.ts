import data from "./players.json";

export type Player = (typeof data.players)[number];
export const meta = data;
export const players = data.players;
// API 실패(unknown)는 빈 문자열: 화면에 표시하지 않음
export const teamLabel = (p: Player) => (p.team_status === "fa" ? "FA" : (p.team ?? ""));

// 막대 공통 축척: 전 선수 최대 절댓값이라 어떤 막대도 칸을 넘지 않고, 같은 종류끼리 길이를 비교할 수 있다
const maxAbs = (f: (p: Player) => number) => Math.max(...players.map((p) => Math.abs(f(p))));
export const scale = {
  luck: maxAbs((p) => p.luck),
  change: Math.max(maxAbs((p) => p.luck), maxAbs((p) => p.regression), maxAbs((p) => p.rebound_score)),
  woba: Math.max(maxAbs((p) => p.woba), maxAbs((p) => p.xwoba)),
};
