import data from "./players.json";

export type Player = (typeof data.players)[number];
export const meta = data;
export const players = data.players;
// API 실패(unknown)는 빈 문자열: 화면에 표시하지 않음
export const teamLabel = (p: Player) => (p.team_status === "fa" ? "FA" : (p.team ?? ""));
export const f3 = (x: number) => x.toFixed(3);
