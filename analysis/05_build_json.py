"""사이트용 players.json 생성. w, k는 04가 저장한 results/model_params.json에서 읽는다. 공식은 model.py.

표시값 일관성: luck, regression을 먼저 3자리로 반올림하고 그 합을 rebound_score로,
woba + rebound_score를 proj_woba_2027로 쓴다. 순위는 반올림 전 값 기준(표시값이 같아도 순위는 다를 수 있음).
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

import model

sys.stdout.reconfigure(encoding="utf-8")

YEAR = 2026
OUT = Path(__file__).resolve().parent.parent / "site" / "src" / "data" / "players.json"
# 화면 근거로 보여줄 시즌 합계값만 공개 (CLAUDE.md 제약)
RAW = {"pa": "pa", "woba": "woba", "xwoba": "est_woba", "ba": "ba", "xba": "est_ba", "slg": "slg", "xslg": "est_slg"}
TABS = {"luck": "luck_raw", "rebound": "rebound_raw"}  # 탭 이름 → 정렬 열(반올림 전 값). rank_<탭>으로 저장
REBOUND_TAB_MIN_PA = 300  # 백업 포수 쏠림 방지. 결정기록 2026-10-31


def r3(x):
    return np.round(x, 3) + 0.0  # + 0.0은 -0.0을 0.0으로 바꿈


def build(d, w, k, lg):
    d = d.copy()
    luck, reg = model.luck(d, w, k), model.regression(d, k, lg)
    assert np.allclose(luck + reg, model.project(d, w, k, lg) - d["woba"]), "분해 합이 proj - wOBA와 다름"
    d["luck_raw"], d["rebound_raw"] = luck, luck + reg  # 순위용
    d["luck"], d["regression"] = r3(luck), r3(reg)
    d["rebound_score"] = r3(d["luck"] + d["regression"])
    d["proj_woba_2027"] = r3(r3(d["woba"]) + d["rebound_score"])  # 화면의 woba 표시값 기준
    return d


if __name__ == "__main__":
    p = model.load_params()
    w, k = p["w"], p["k"]
    d = model.load(YEAR)
    lg = model.league_woba(d)
    d = build(d, w, k, lg)
    # 기본 탭 Buy-Low(luck 순), 보조 탭 Rebound(rebound_score 순). 결정기록 2026-10-31
    d = d[d["pa"] >= model.MIN_PA_SHOW].sort_values("luck_raw", ascending=False)
    d["in_rebound_tab"] = d["pa"] >= REBOUND_TAB_MIN_PA
    d["rank_luck"] = d["luck_raw"].rank(method="min", ascending=False)
    d["rank_rebound"] = d["rebound_raw"].where(d["in_rebound_tab"]).rank(method="min", ascending=False)  # 탭 밖은 NaN

    players = [{
        "player_id": int(r["player_id"]),
        "name": " ".join(reversed(r["player"].split(", ", 1))),  # "Last, First" → "First Last"
        "team": None,  # shortcut: 원본에 팀 열이 없음, 2주차 파이프라인에서 채우기
        **{key: int(r["pa"]) if key == "pa" else float(r3(r[col])) for key, col in RAW.items()},
        **{key: float(r[key]) for key in ("proj_woba_2027", "rebound_score", "luck", "regression")},
        **{f"rank_{tab}": None if np.isnan(r[f"rank_{tab}"]) else int(r[f"rank_{tab}"]) for tab in TABS},
        "in_rebound_tab": bool(r["in_rebound_tab"]),
    } for _, r in d.iterrows()]

    out = {
        "data_season": YEAR,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "method_version": f"v1 (w={w}, k={k})",
        "source": "Baseball Savant",
        "league_woba": float(r3(lg)),
        "default_sort": "luck",
        "tabs": list(TABS),
        "min_pa_show": model.MIN_PA_SHOW,
        "rebound_tab_min_pa": REBOUND_TAB_MIN_PA,
        "players": players,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print(f"{OUT} 저장: {len(players)}명, w = {w}, k = {k}, 리그평균 wOBA {lg:.3f}")
