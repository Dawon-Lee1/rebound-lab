"""2027 예상 wOBA 모델의 w, k를 고른다. 기준은 내년 wOBA RMSE(내년 타석 가중). 공식은 model.py.

학습: 2024→2025, 검증: 2025→2026.
표본 일치 검증: 사이트는 200타석 이상만 보여주므로, 올해 200타석 이상 선수로 (w, k)를 다시 골라
200타석+ 검증 RMSE가 2% 이상 줄면 새 값을 채택한다. 채택값은 results/model_params.json에 저장.
"""
import sys

import numpy as np
import pandas as pd

import model

sys.stdout.reconfigure(encoding="utf-8")

WS = np.round(np.arange(0, 1.01, 0.1), 1)
KS = (0, 50, 100, 200, 300, 500, 800)
MIN_GAIN = 0.02


def pair(year_from, year_to, min_pa_from=model.MIN_PA_FROM):
    a, b = model.load(year_from), model.load(year_to)
    m = a[a["pa"] >= min_pa_from].merge(
        b[b["pa"] >= model.MIN_PA_TO][["player_id", "pa", "woba"]], on="player_id", suffixes=("", "_to"))
    return m, model.league_woba(a)  # 리그평균은 필터 전 전체 타석 기준


def rmse(pred, m):
    return np.sqrt(np.average((pred - m["woba_to"]) ** 2, weights=m["pa_to"]))


def grid(m, lg):
    return pd.DataFrame({k: [rmse(model.project(m, w, k, lg), m) for w in WS] for k in KS}, index=WS).rename_axis("w")


def best(g):
    w, k = g.stack().idxmin()
    return float(w), int(k)


def baselines(m, lg):
    return {"올해 wOBA 그대로": rmse(m["woba"], m),
            "올해 xwOBA 그대로": rmse(m["est_woba"], m),
            "리그 평균": rmse(pd.Series(lg, index=m.index), m)}


def ranked_show(d, w, k, lg):
    """MIN_PA_SHOW(200)타석 이상 전체를 rebound_score 내림차순으로. TOP 20은 호출자가 head(20)."""
    d = d.copy()
    d["proj_2027"] = model.project(d, w, k, lg)
    d["luck"] = model.luck(d, w, k)
    d["regression"] = model.regression(d, k, lg)
    d["rebound_score"] = d["luck"] + d["regression"]
    return d[d["pa"] >= model.MIN_PA_SHOW].sort_values("rebound_score", ascending=False)


if __name__ == "__main__":
    train, lg_train = pair(2024, 2025)
    valid, lg_valid = pair(2025, 2026)
    # 자체 점검: w=1, k=0이면 xwOBA, w=0, k=0이면 wOBA 그대로. 분해 합 = proj - wOBA
    assert np.allclose(model.project(train, 1, 0, lg_train), train["est_woba"])
    assert np.allclose(model.project(train, 0, 0, lg_train), train["woba"])
    assert np.allclose(model.luck(train, 0.8, 300) + model.regression(train, 300, lg_train),
                       model.project(train, 0.8, 300, lg_train) - train["woba"])

    g = grid(train, lg_train)
    w0, k0 = best(g)
    print(f"학습 2024→2025: {len(train)}명 (올해 {model.MIN_PA_FROM}타석+, 내년 {model.MIN_PA_TO}타석+), 리그평균 wOBA {lg_train:.3f}")
    print("학습 RMSE 격자 (행 w, 열 k)")
    print(g.round(4).to_string())
    print(f"\n최적 w = {w0}, k = {k0}, 학습 RMSE = {g.loc[w0, k0]:.4f}")

    gv = grid(valid, lg_valid)
    print(f"\n검증 2025→2026: {len(valid)}명, 리그평균 wOBA {lg_valid:.3f}")
    rows = {f"Projection (w={w0}, k={k0})": gv.loc[w0, k0], **baselines(valid, lg_valid)}
    print(pd.Series(rows, name="검증 RMSE").round(4).to_string())

    # 표본 일치 검증: 올해 200타석 이상만으로 다시 학습·검증
    train200, _ = pair(2024, 2025, model.MIN_PA_SHOW)
    valid200 = valid[valid["pa"] >= model.MIN_PA_SHOW]
    g200 = grid(train200, lg_train)
    w1, k1 = best(g200)
    print(f"\n=== 표본 일치 검증: 올해 {model.MIN_PA_SHOW}타석 이상 (학습 {len(train200)}명, 검증 {len(valid200)}명) ===")
    print("학습 RMSE 격자 (행 w, 열 k)")
    print(g200.round(4).to_string())
    old = rmse(model.project(valid200, w0, k0, lg_valid), valid200)
    new = rmse(model.project(valid200, w1, k1, lg_valid), valid200)
    rows = {f"기존 (w={w0}, k={k0}, 50타석+ 학습)": old,
            f"재조정 (w={w1}, k={k1}, 200타석+ 학습)": new,
            **baselines(valid200, lg_valid)}
    print(pd.Series(rows, name="200타석+ 검증 RMSE").round(4).to_string())
    gain = 1 - new / old
    w, k = (w1, k1) if gain >= MIN_GAIN else (w0, k0)
    print(f"RMSE 개선 {gain:.1%} → {'새 값 채택' if gain >= MIN_GAIN else '기존 값 유지'}: w = {w}, k = {k}")
    chosen = new if gain >= MIN_GAIN else old
    base = baselines(valid200, lg_valid)
    model.save_params(w=w, k=k, train="2024→2025", valid="2025→2026",
                      valid_rmse_200=round(chosen, 4),
                      candidates={"50+": [w0, k0], "200+": [w1, k1]}, gain_200=round(gain, 4),
                      # 방법론 페이지 백테스트 표: 사이트 표시 기준과 같은 200타석+ 표본
                      backtest={"train": "2024→2025", "valid": "2025→2026",
                                # 학습 표본은 채택된 후보를 고른 표본, 검증은 사이트 표시 기준(200타석+)
                                "train_min_pa": model.MIN_PA_SHOW if gain >= MIN_GAIN else model.MIN_PA_FROM,
                                "n_train": len(train200) if gain >= MIN_GAIN else len(train),
                                "valid_min_pa": model.MIN_PA_SHOW, "n_valid": len(valid200),
                                "min_pa_next": model.MIN_PA_TO,
                                "rmse": {"projection": round(chosen, 4),
                                         "woba": round(base["올해 wOBA 그대로"], 4),
                                         "xwoba": round(base["올해 xwOBA 그대로"], 4),
                                         "league": round(base["리그 평균"], 4)}})

    d = model.load(2026)
    lg = model.league_woba(d)
    print(f"\n2026 리그평균 wOBA {lg:.3f}. 반등 TOP 20 구성 비교")
    t0, t1 = ranked_show(d, w0, k0, lg).head(20), ranked_show(d, w1, k1, lg).head(20)

    def reg_share(t):
        total = t["rebound_score"].sum()
        return t["regression"].sum() / total if total else float("nan")  # 합이 0이면 비중 정의 안 됨

    comp = pd.DataFrame({
        label: {"평균 rebound": t["rebound_score"].mean(),
                "평균 luck": t["luck"].mean(),
                "평균 regression": t["regression"].mean(),
                "regression 비중": reg_share(t)}
        for label, t in ((f"w={w0}, k={k0}", t0), (f"w={w1}, k={k1}", t1))})
    print(comp.round(3).to_string())
    print(f"두 TOP 20에 함께 든 선수: {len(set(t0['player_id']) & set(t1['player_id']))}명")

    show = ranked_show(d, w, k, lg).round(3)
    cols = ["player", "pa", "woba", "est_woba", "proj_2027", "rebound_score", "luck", "regression"]
    print(f"\n채택값 (w={w}, k={k}), {model.MIN_PA_SHOW}타석 이상 {len(show)}명")
    print("\n[반등 TOP 20]")
    print(show[cols].head(20).to_string(index=False))
    print("\n[거품 BOTTOM 20]")
    print(show[cols].tail(20).iloc[::-1].to_string(index=False))
