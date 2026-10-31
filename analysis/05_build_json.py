"""사이트용 players.json 생성. w, k는 04가 저장한 results/model_params.json에서 읽는다. 공식은 model.py.

표시값 일관성: luck, regression을 먼저 3자리로 반올림하고 그 합을 rebound_score로,
woba + rebound_score를 proj_woba_2027로 쓴다. 순위는 반올림 전 값 기준(표시값이 같아도 순위는 다를 수 있음).
"""
import json
import sys
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np

import model

sys.stdout.reconfigure(encoding="utf-8")

YEAR = 2026
OUT = Path(__file__).resolve().parent.parent / "site" / "src" / "data" / "players.json"
# 화면 근거로 보여줄 시즌 합계값만 공개 (CLAUDE.md 제약)
RAW = {"pa": "pa", "woba": "woba", "xwoba": "est_woba", "ba": "ba", "xba": "est_ba", "slg": "slg", "xslg": "est_slg"}
TABS = {"luck": "luck_raw", "sell": "luck_raw", "rebound": "rebound_raw"}  # 탭 이름 → 정렬 열(반올림 전 값). rank_<탭>으로 저장
REBOUND_TAB_MIN_PA = 300  # 백업 포수 쏠림 방지. 결정기록 2026-10-31
AGE_DATE = date(2027, 4, 1)  # 2027 개막 무렵 기준 나이
MLB_API = "https://statsapi.mlb.com/api/v1"
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"  # API 원본, .gitignore 대상


def r3(x):
    return np.round(x, 3) + 0.0  # + 0.0은 -0.0을 0.0으로 바꿈


def age_on(birth):
    if not birth:
        return None
    b = date.fromisoformat(birth)
    return AGE_DATE.year - b.year - ((AGE_DATE.month, AGE_DATE.day) < (b.month, b.day))


def _get(path, raw_name):
    with urllib.request.urlopen(f"{MLB_API}/{path}", timeout=30) as r:
        body = r.read()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    (RAW_DIR / raw_name).write_bytes(body)
    return json.loads(body)


def fetch_mlb(ids):
    """MLB Stats API에서 (선수 id → 선수, 팀 id → 약자, 마이너 팀 id → 모 구단 id). 실패하면 빈 dict 3개."""
    try:
        people = {}
        for i in range(0, len(ids), 100):
            chunk = ids[i:i + 100]
            r = _get(f"people?personIds={','.join(map(str, chunk))}&hydrate=currentTeam", f"mlb_people_{YEAR}_{i // 100}.json")
            people |= {p["id"]: p for p in r["people"]}
        teams = _get("teams?sportIds=1,11,12,13,14,16", "mlb_teams.json")["teams"]  # MLB + 마이너 + 루키
    except Exception as e:  # 네트워크·형식 오류: 빌드는 계속, team·age는 null
        print(f"경고: MLB Stats API 실패 → team·age 전원 null ({e!r})")
        return {}, {}, {}
    return (people, {t["id"]: t["abbreviation"] for t in teams if t.get("sport", {}).get("id") == 1},
            {t["id"]: t["parentOrgId"] for t in teams if "parentOrgId" in t})


def team_info(person, abbr, parent):
    """(팀 약자, team_status). 마이너 소속은 모 구단 약자. currentTeam 없으면 FA, 응답 없음·모르는 팀은 unknown."""
    if person is None:
        return None, "unknown"
    if "currentTeam" not in person:
        return (None, "fa") if person.get("active") else (None, "unknown")  # 은퇴 선수는 active=False
    ct = person["currentTeam"]
    tid = ct.get("parentOrgId") or parent.get(ct["id"], ct["id"])  # 겨울리그 팀은 응답에 소속 구단 id가 붙어 옴
    team = abbr.get(tid)
    return (team, "active") if team else (None, "unknown")


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
    assert age_on("1990-04-01") == 37 and age_on("1990-04-02") == 36 and age_on(None) is None
    t = {999: "AAA", 119: "LAD"}, {999: 119}  # (팀 id → 약자, 마이너 id → 모 구단 id)
    assert team_info({"currentTeam": {"id": 999}}, *t) == ("LAD", "active")  # 마이너 → 모 구단
    assert team_info({"currentTeam": {"id": 119}}, *t) == ("LAD", "active")
    assert team_info({"currentTeam": {"id": 670, "parentOrgId": 119}}, *t) == ("LAD", "active")  # 겨울리그
    assert team_info({"active": True}, *t) == (None, "fa")  # currentTeam 없음
    assert team_info({"active": False}, *t) == (None, "unknown")  # 은퇴 등 비활성: FA로 표시하지 않음
    assert team_info(None, *t) == (None, "unknown")  # API 실패 또는 응답에 없음
    p = model.load_params()
    w, k = p["w"], p["k"]
    d = model.load(YEAR)
    lg = model.league_woba(d)
    d = build(d, w, k, lg)
    # 탭: Buy-Low(luck > 0, 큰 순), Sell-High(luck < 0, 작은 순), Rebound(rebound_score 순). 탭 밖 순위는 NaN. 결정기록 2026-10-31
    d = d[d["pa"] >= model.MIN_PA_SHOW].sort_values("luck_raw", ascending=False)
    d["in_buylow_tab"], d["in_sell_tab"] = d["luck"] > 0, d["luck"] < 0  # 탭은 화면 표시값 부호, 순위는 반올림 전 값
    d["in_rebound_tab"] = d["pa"] >= REBOUND_TAB_MIN_PA
    d["rank_luck"] = d["luck_raw"].where(d["in_buylow_tab"]).rank(method="min", ascending=False)
    d["rank_sell"] = d["luck_raw"].where(d["in_sell_tab"]).rank(method="min", ascending=True)
    d["rank_rebound"] = d["rebound_raw"].where(d["in_rebound_tab"]).rank(method="min", ascending=False)
    assert not (d["in_buylow_tab"] & d["in_sell_tab"]).any()
    assert (d.loc[d["in_buylow_tab"] | d["in_sell_tab"], "luck"] != 0).all()  # 화면에 0.000인 선수는 탭 밖
    assert d.loc[d["rank_luck"] == 1, "luck_raw"].iloc[0] == d["luck_raw"].max() > 0
    assert d.loc[d["rank_sell"] == 1, "luck_raw"].iloc[0] == d["luck_raw"].min() < 0
    assert d["rank_luck"].notna().sum() == d["in_buylow_tab"].sum() and d["rank_sell"].notna().sum() == d["in_sell_tab"].sum()
    people, abbr, parent = fetch_mlb([int(i) for i in d["player_id"]])

    players = [{
        "player_id": int(r["player_id"]),
        "name": " ".join(reversed(r["player"].split(", ", 1))),  # "Last, First" → "First Last"
        **dict(zip(("team", "team_status"), team_info(people.get(int(r["player_id"])) if people else None, abbr, parent))),
        "age": age_on((people.get(int(r["player_id"])) or {}).get("birthDate")),
        **{key: int(r["pa"]) if key == "pa" else float(r3(r[col])) for key, col in RAW.items()},
        **{key: float(r[key]) for key in ("proj_woba_2027", "rebound_score", "luck", "regression")},
        **{f"rank_{tab}": None if np.isnan(r[f"rank_{tab}"]) else int(r[f"rank_{tab}"]) for tab in TABS},
        **{f"in_{tab}_tab": bool(r[f"in_{tab}_tab"]) for tab in ("buylow", "sell", "rebound")},
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
    print("team_status:", {s: sum(x["team_status"] == s for x in players) for s in ("active", "fa", "unknown")},
          "/ age null:", sum(x["age"] is None for x in players),
          "/ 탭 인원:", {t: sum(x[f"in_{t}_tab"] for x in players) for t in ("buylow", "sell", "rebound")})
