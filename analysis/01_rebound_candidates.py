"""2026 시즌 반등 후보와 거품 주의 선수 목록.

Colab: 첫 셀에서 !pip install pybaseball -q 실행 후 이 파일 내용을 붙여넣기
로컬:  pip install -r requirements.txt 후 python 01_rebound_candidates.py
"""
from pybaseball import statcast_batter_expected_stats

MIN_PA = 200

raw = statcast_batter_expected_stats(2026)

# minPA 옵션이 적용되지 않으므로 직접 필터링
df = raw[raw["pa"] >= MIN_PA].copy()

# 원본 열(est_woba_minus_woba_diff)은 실제 - 기대라서 방향이 반대 → 직접 계산
df["rebound"] = df["est_woba"] - df["woba"]

df = df.rename(columns={"last_name, first_name": "player"})
cols = ["player", "pa", "woba", "est_woba", "rebound"]

print(f"대상 선수: {len(df)}명\n")
print("반등 후보 (운이 나빴던 선수)")
print(df[cols].sort_values("rebound", ascending=False).head(10).to_string(index=False))
print("\n거품 주의 (운이 좋았던 선수)")
print(df[cols].sort_values("rebound").head(10).to_string(index=False))
