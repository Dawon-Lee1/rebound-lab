import data from "./players.json";

export type Player = (typeof data.players)[number];
export const meta = data;
export const players = data.players;
export const f3 = (x: number) => x.toFixed(3);
