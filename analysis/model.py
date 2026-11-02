"""Rebound Score 모델: 공식, 타석 기준, 데이터 로드를 한 곳에 모은다.

proj          = (PA*(w*xwOBA + (1-w)*wOBA) + k*리그평균wOBA) / (PA + k)
Rebound Score = proj - wOBA = luck + regression
  luck        = PA*w*(xwOBA - wOBA)/(PA+k)   (운: 기대 성적과 실제 성적의 차이)
  regression  = k*(리그평균 - wOBA)/(PA+k)     (평균 회귀: 리그 평균 쪽으로 당기는 몫)
w, k는 04_projection.py가 골라 results/model_params.json에 저장한다.
"""
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
from pybaseball import statcast_batter_expected_stats

MIN_PA_FROM, MIN_PA_TO, MIN_PA_SHOW = 50, 100, 200
PARAMS = Path(__file__).resolve().parent / "results" / "model_params.json"
# 출전 위험: PA < RISK_MAX_PA 그리고 regression(3자리) >= RISK_MIN_REG. 근거는 06 (c), 결정기록 2026-11-01
RISK_MAX_PA, RISK_MIN_REG = 350, 0.010
COLS = ["player_id", "last_name, first_name", "pa", "woba", "est_woba", "ba", "est_ba", "slg", "est_slg"]


@lru_cache(maxsize=None)
def _fetch(year):
    d = statcast_batter_expected_stats(year, minPA=1)  # 기본값 'q'는 규정타석만 반환
    d = d[COLS].dropna(subset=["pa", "woba", "est_woba"])  # 2026 1타석 투수 등 값 없는 행
    return d.rename(columns={"last_name, first_name": "player"})


def load(year):
    return _fetch(year).copy()  # 호출자가 캐시된 원본을 바꾸지 못하게


def league_woba(d):
    return np.average(d["woba"], weights=d["pa"])


def project(d, w, k, lg):
    return (d["pa"] * (w * d["est_woba"] + (1 - w) * d["woba"]) + k * lg) / (d["pa"] + k)


def luck(d, w, k):
    return d["pa"] * w * (d["est_woba"] - d["woba"]) / (d["pa"] + k)


def regression(d, k, lg):
    return k * (lg - d["woba"]) / (d["pa"] + k)


def save_params(**p):
    PARAMS.parent.mkdir(parents=True, exist_ok=True)
    PARAMS.write_text(json.dumps(p, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")


def load_params():
    if not PARAMS.exists():
        raise SystemExit(f"{PARAMS} 없음: 04_projection.py를 먼저 실행하세요")
    return json.loads(PARAMS.read_text(encoding="utf-8"))
