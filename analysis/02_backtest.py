"""백테스트: 전년도 xwOBA 격차가 다음 시즌 wOBA 변화를 예측하는가?

결과 해석
- r > 0.3, 분위별 평균이 계단처럼 증가 → 격차를 핵심 지표로 사용
- 0.1 < r < 0.3 → 효과는 있지만 약함. 타석·나이 보정 추가
- r < 0.1 → xwOBA 자체를 예측값으로 사용하는 방식으로 변경
"""
import numpy as np
import pandas as pd
from scipy import stats
from pybaseball import statcast_batter_expected_stats

MIN_PA = 200


def load(year):
    d = statcast_batter_expected_stats(year, minPA=1)  # 기본값 'q'는 규정타석만 반환
    d = d[d["pa"] >= MIN_PA][["player_id", "last_name, first_name", "pa", "woba", "est_woba"]]
    return d.rename(columns={"last_name, first_name": "player"})


def backtest(year_from, year_to):
    a, b = load(year_from), load(year_to)
    m = a.merge(b, on=["player_id", "player"], suffixes=("_from", "_to"))
    m["gap_from"] = m["est_woba_from"] - m["woba_from"]   # 전년도 불운 정도
    m["change_to"] = m["woba_to"] - m["woba_from"]        # 다음 시즌 실제 변화

    r = np.corrcoef(m["gap_from"], m["change_to"])[0, 1]
    print(f"\n[{year_from} → {year_to}] 두 시즌 모두 {MIN_PA}타석 이상: {len(m)}명, r = {r:.3f}")

    m["group"] = pd.qcut(m["gap_from"], 5, labels=["very_lucky", "lucky", "neutral", "unlucky", "very_unlucky"])
    print(m.groupby("group", observed=True)["change_to"].agg(["count", "mean"]).round(3).to_string())

    # 평균 회귀 검증: 격차가 올해 wOBA의 평균 회귀를 넘어서는 정보를 주는가?
    r_woba = np.corrcoef(m["woba_from"], m["woba_to"])[0, 1]
    r_xwoba = np.corrcoef(m["est_woba_from"], m["woba_to"])[0, 1]
    print(f"r(올해 wOBA, 내년 wOBA) = {r_woba:.3f}, r(올해 xwOBA, 내년 wOBA) = {r_xwoba:.3f}")
    coef, se, p = ols(m["woba_to"], m[["woba_from", "gap_from"]])
    print("회귀: 내년 wOBA ~ 올해 wOBA + 격차")
    for name, c, s, pv in zip(["절편", "올해 wOBA", "격차"], coef, se, p):
        print(f"  {name:<8} 계수 = {c:.3f}, 표준오차 = {s:.3f}, p = {pv:.4f}")
    return r


def ols(y, X):
    """절편 포함 최소제곱. 계수, 표준오차, 양측 p값을 반환."""
    X = np.column_stack([np.ones(len(X)), X])
    y = np.asarray(y)
    coef, *_ = np.linalg.lstsq(X, y, rcond=None)
    dof = len(y) - X.shape[1]
    sigma2 = ((y - X @ coef) ** 2).sum() / dof
    se = np.sqrt(np.diag(sigma2 * np.linalg.inv(X.T @ X)))
    p = 2 * stats.t.sf(np.abs(coef / se), dof)
    return coef, se, p


if __name__ == "__main__":
    backtest(2025, 2026)
    backtest(2024, 2025)
