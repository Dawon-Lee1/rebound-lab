"""방법론 점검 3개 (2026-10-31 리뷰 항목, (c)는 2026-11-01 추가). 기존 파일은 그대로 두고 model.py만 쓴다.

(a) 생존 편향: 백테스트는 다음 해 100타석+ 선수만 쓴다. 빠진 선수의 rebound_score가 남은 선수와 다른지 본다.
(b) 회귀 목표: 리그평균(올해 1타석+ 전체) 대신 다른 목표 평균을 쓰면 검증 RMSE가 좋아지는지 본다.
    - 올해 100타석+ 평균: 2027 예측에도 쓸 수 있음 → 채택 판단은 이것으로만
    - 다음 해 100타석+ 평균: 예측 시점에 모르는 미래 정보 → 상한 확인용
(w, k)는 목표마다 학습셋(2024→2025)에서 04와 같은 격자로 다시 고르고, 검증(2025→2026) 200타석+ RMSE로 비교.
결과는 제안만 출력하고 model_params.json은 바꾸지 않는다.
(c) 출전 위험: 올해 200타석+ 선수의 다음 해 탈락 비율을 타석·regression 구간별로 보고, 05의 playing_time_risk 기준 근거로 쓴다.
"""
import sys

import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

import model

sys.stdout.reconfigure(encoding="utf-8")

WS = np.round(np.arange(0, 1.01, 0.1), 1)  # 04와 같은 격자
KS = (0, 50, 100, 200, 300, 500, 800)
MIN_GAIN = 0.02


def pair_all(year_from, year_to):
    """올해 50타석+ 전원 + 다음 해 기록(left merge, 없으면 NaN). kept = 다음 해 100타석+ (04 백테스트 표본)."""
    a, b = model.load(year_from), model.load(year_to)
    m = a[a["pa"] >= model.MIN_PA_FROM].merge(
        b[["player_id", "pa", "woba"]], on="player_id", how="left", suffixes=("", "_to"))
    m["kept"] = m["pa_to"] >= model.MIN_PA_TO  # NaN(다음 해 기록 없음)은 False
    return m, a, b


def rmse(pred, m):
    return np.sqrt(np.average((pred - m["woba_to"]) ** 2, weights=m["pa_to"]))


def best(m, lg):
    g = {(w, k): rmse(model.project(m, w, k, lg), m) for w in WS for k in KS}
    w, k = min(g, key=g.get)
    return float(w), int(k)


def survival_table(m, w, k, lg):
    m = m.assign(rebound=model.project(m, w, k, lg) - m["woba"])
    rows = {}
    for sample, s in ((f"{model.MIN_PA_FROM}+", m), (f"{model.MIN_PA_SHOW}+", m[m["pa"] >= model.MIN_PA_SHOW])):
        for label, g in (("남음", s[s["kept"]]), ("탈락", s[~s["kept"]])):
            r = g["rebound"]
            rows[(sample, label)] = {"인원": len(g), "평균": r.mean(), "표준편차": r.std(), "25%": r.quantile(.25),
                                     "중앙값": r.median(), "75%": r.quantile(.75), "rebound>0 비율": (r > 0).mean(),
                                     "평균 PA": g["pa"].mean()}
        kept, drop = s.loc[s["kept"], "rebound"], s.loc[~s["kept"], "rebound"]
        rows[(sample, "탈락")]["Mann-Whitney p"] = mannwhitneyu(kept, drop).pvalue if len(drop) else np.nan
    return pd.DataFrame(rows).T


if __name__ == "__main__":
    p = model.load_params()
    w0, k0 = p["w"], p["k"]

    print("=== (a) 생존 편향: 다음 해 100타석 미만이라 백테스트에서 빠진 선수 ===")
    print(f"rebound_score는 채택값 (w={w0}, k={k0}), 올해 전체 리그평균으로 계산\n")
    pairs = {}
    for y0, y1 in ((2024, 2025), (2025, 2026)):
        m, a, b = pair_all(y0, y1)
        pairs[(y0, y1)] = m, a, b
        t = survival_table(m, w0, k0, model.league_woba(a))
        assert t["인원"].groupby(level=0).sum()[f"{model.MIN_PA_FROM}+"] == len(m)  # 남음 + 탈락 = 전체
        print(f"[{y0}→{y1}] 올해 {model.MIN_PA_FROM}타석+ {len(m)}명 중 탈락 {int((~m['kept']).sum())}명"
              f" (다음 해 기록 없음 {int(m['pa_to'].isna().sum())}명)")
        print(t.round(3).to_string(), "\n")

    print("=== (b) 회귀 목표 평균 비교 ===")
    print("(w, k)는 학습 2024→2025(다음 해 100타석+)에서 목표마다 다시 선택, 검증 2025→2026 RMSE(내년 타석 가중)\n")
    targets = {
        "현재: 올해 1타석+ 전체": lambda a, b: model.league_woba(a),
        "올해 100타석+": lambda a, b: model.league_woba(a[a["pa"] >= model.MIN_PA_TO]),
        "다음 해 100타석+ (미래 정보)": lambda a, b: model.league_woba(b[b["pa"] >= model.MIN_PA_TO]),
    }
    mt, at, bt = pairs[(2024, 2025)]
    mv, av, bv = pairs[(2025, 2026)]
    train, valid = mt[mt["kept"]], mv[mv["kept"]]
    valid200 = valid[valid["pa"] >= model.MIN_PA_SHOW]
    rows = {}
    for name, f in targets.items():
        lg_t, lg_v = f(at, bt), f(av, bv)
        w, k = best(train, lg_t)
        rows[name] = {"목표(학습)": lg_t, "목표(검증)": lg_v, "w": w, "k": k,
                      f"검증 RMSE {model.MIN_PA_FROM}+": rmse(model.project(valid, w, k, lg_v), valid),
                      f"검증 RMSE {model.MIN_PA_SHOW}+": rmse(model.project(valid200, w, k, lg_v), valid200)}
    t = pd.DataFrame(rows).T
    base = t.iloc[0]
    for n in (model.MIN_PA_FROM, model.MIN_PA_SHOW):
        t[f"개선 {n}+"] = 1 - t[f"검증 RMSE {n}+"] / base[f"검증 RMSE {n}+"]
    # 현재 목표의 재현값이 04의 50+ 학습 후보와 같아야 함(04가 200+ 후보를 채택했으면 RMSE 비교는 생략)
    assert [base["w"], base["k"]] == p["candidates"]["50+"]
    if [w0, k0] == p["candidates"]["50+"]:
        assert round(base[f"검증 RMSE {model.MIN_PA_SHOW}+"], 4) == p["valid_rmse_200"]
    print(f"검증 {model.MIN_PA_FROM}+ {len(valid)}명, {model.MIN_PA_SHOW}+ {len(valid200)}명")
    print(t.astype(float).round(4).to_string())

    gain = t.loc["올해 100타석+", f"개선 {model.MIN_PA_SHOW}+"]
    print(f"\n판단(올해 100타석+, {model.MIN_PA_SHOW}타석+ 검증 RMSE 개선 {gain:.1%}, 기준 {MIN_GAIN:.0%}): "
          + ("채택 제안 (model_params.json은 바꾸지 않음, 결정 후 04에 반영)" if gain >= MIN_GAIN else "현재 리그평균 유지"))
    print("주의: 이 검증셋은 선택에 쓰였으므로 여기 RMSE를 사이트 성능 수치로 쓰지 않는다")

    print("\n=== (c) 출전 위험: 올해 200타석+ 선수의 다음 해 탈락(100타석 미만) 비율 ===")
    print(f"제안 기준: PA < {model.RISK_MAX_PA} 그리고 regression >= {model.RISK_MIN_REG} (regression은 3자리 반올림값)")
    print("주의: 기준값을 이 두 기간에서 골랐으므로 표본 내 결과. 화면에 비율 숫자를 쓰지 않는다\n")
    for (y0, y1), (m, a, b) in pairs.items():
        s = m[m["pa"] >= model.MIN_PA_SHOW].assign(drop=lambda x: ~x["kept"])
        s["reg"] = np.round(model.regression(s, k0, model.league_woba(a)), 3)
        flag = (s["pa"] < model.RISK_MAX_PA) & (s["reg"] >= model.RISK_MIN_REG)
        print(f"[{y0}→{y1}] {len(s)}명, 전체 탈락률 {s['drop'].mean():.3f}")
        for name, col, bins in (("PA", "pa", [200, 300, 400, 500, 10_000]), ("regression", "reg", [-1, 0, 0.01, 0.02, 1])):
            g = s.groupby(pd.cut(s[col], bins, right=False), observed=True)["drop"].agg(["size", "mean"])
            assert g["size"].sum() == len(s)  # 구간이 표본 전체를 덮음
            print(f"{name} 구간\n{g.round(3).to_string()}")
        print(f"기준 해당 {int(flag.sum())}명 탈락률 {s.loc[flag, 'drop'].mean():.3f} | 나머지 {int((~flag).sum())}명 "
              f"{s.loc[~flag, 'drop'].mean():.3f} | 탈락자 중 해당 비율 {s.loc[flag, 'drop'].sum() / s['drop'].sum():.2f}\n")
