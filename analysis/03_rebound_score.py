"""Rebound Score: 타석 수가 적을수록 격차를 0쪽으로 당기는 보정 점수.

Rebound Score = (xwOBA - wOBA) * PA / (PA + k)
k('가상 타석 수')는 백테스트 상관계수가 가장 높은 값으로 선택한다.
"""
import numpy as np
from pybaseball import statcast_batter_expected_stats

MIN_PA = 100


def load(year):
    d = statcast_batter_expected_stats(year, minPA=1)  # 기본값 'q'는 규정타석만 반환
    d = d[d["pa"] >= MIN_PA][["player_id", "last_name, first_name", "pa", "woba", "est_woba"]]
    return d.rename(columns={"last_name, first_name": "player"})


def score(df, k):
    return (df["est_woba"] - df["woba"]) * df["pa"] / (df["pa"] + k)


def pick_k(year_from=2025, year_to=2026, ks=(0, 100, 200, 300, 500, 800)):
    a, b = load(year_from), load(year_to)
    m = a.merge(b, on=["player_id", "player"], suffixes=("", "_to"))
    change = m["woba_to"] - m["woba"]
    results = {k: np.corrcoef(score(m, k), change)[0, 1] for k in ks}
    for k, r in results.items():
        print(f"k = {k:>4}: r = {r:.3f}")
    return max(results, key=results.get)


if __name__ == "__main__":
    best_k = pick_k()
    print(f"\n선택된 k = {best_k}")
    df = load(2026)
    df["rebound_score"] = score(df, best_k)
    print(df.sort_values("rebound_score", ascending=False).head(20).to_string(index=False))
