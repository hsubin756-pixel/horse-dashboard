# ============================================================
#  競馬データ分析 - ステージ3: 分析 & 可視化
# ============================================================

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib

# ★ 폰트 수정: Yu Gothic (일본어+한글 모두 지원)
#   Yu Gothic이 없으면 Meiryo → MS Gothic 순으로 시도
matplotlib.rcParams['font.family'] = ['Yu Gothic', 'Meiryo', 'MS Gothic']
matplotlib.rcParams['axes.unicode_minus'] = False

DB_NAME = "keiba.db"
conn = sqlite3.connect(DB_NAME)

horses_df = pd.read_sql("SELECT * FROM horses", conn)
races_df = pd.read_sql("SELECT * FROM races", conn)
conn.close()

print("=" * 60)
print("  競馬データ分析開始")
print("=" * 60)
print(f"\n  登録馬: {len(horses_df)}頭")
print(f"  レース記録: {len(races_df)}件")

# ★ 디버그: 착순 데이터 확인
print(f"\n  [デバッグ] finish_pos のサンプル: {races_df['finish_pos'].unique()[:20]}")

# 착순을 숫자로 변환
races_df["finish_num"] = pd.to_numeric(races_df["finish_pos"], errors="coerce")
print(f"  [デバッグ] 数値変換成功: {races_df['finish_num'].notna().sum()}件 / {len(races_df)}件")

# ============================================================
#  分析 1: 馬別勝率
# ============================================================

print("\n" + "=" * 60)
print("  📊 分析1: 馬別勝率")
print("=" * 60)

for name in races_df["horse_name"].unique():
    horse_races = races_df[races_df["horse_name"] == name]
    total = len(horse_races)
    wins = len(horse_races[horse_races["finish_num"] == 1])
    top3 = len(horse_races[horse_races["finish_num"] <= 3])
    win_rate = (wins / total * 100) if total > 0 else 0
    top3_rate = (top3 / total * 100) if total > 0 else 0
    print(f"\n  {name}")
    print(f"    出走: {total}回 | 1着: {wins}回 (勝率{win_rate:.1f}%) | 3着内: {top3}回 (複勝率{top3_rate:.1f}%)")

# ============================================================
#  分析 2: 距離別成績
# ============================================================

print("\n" + "=" * 60)
print("  📊 分析2: 距離別成績")
print("=" * 60)

def extract_distance(dist_str):
    nums = ""
    for char in str(dist_str):
        if char.isdigit():
            nums += char
    if nums:
        return int(nums)
    return None

races_df["distance_num"] = races_df["distance"].apply(extract_distance)

def classify_distance(d):
    if d is None:
        return "不明"
    if d <= 1400:
        return "短距離 (~1400m)"
    elif d <= 1800:
        return "マイル (1401~1800m)"
    elif d <= 2200:
        return "中距離 (1801~2200m)"
    else:
        return "長距離 (2201m~)"

races_df["dist_category"] = races_df["distance_num"].apply(classify_distance)

for name in races_df["horse_name"].unique():
    horse_data = races_df[races_df["horse_name"] == name]
    print(f"\n  {name}:")
    for cat in ["短距離 (~1400m)", "マイル (1401~1800m)",
                "中距離 (1801~2200m)", "長距離 (2201m~)"]:
        cat_data = horse_data[horse_data["dist_category"] == cat]
        if len(cat_data) > 0:
            avg = cat_data["finish_num"].mean()
            count = len(cat_data)
            wins = len(cat_data[cat_data["finish_num"] == 1])
            print(f"    {cat}: {count}回出走, 平均{avg:.1f}着, {wins}勝")

# ============================================================
#  分析 3: コース適性 (芝 vs ダート)
# ============================================================

print("\n" + "=" * 60)
print("  📊 分析3: コース適性")
print("=" * 60)

def extract_surface(dist_str):
    s = str(dist_str)
    if "芝" in s:
        return "芝"
    elif "ダ" in s:
        return "ダート"
    return "不明"

races_df["surface"] = races_df["distance"].apply(extract_surface)

for name in races_df["horse_name"].unique():
    horse_data = races_df[races_df["horse_name"] == name]
    print(f"\n  {name}:")
    for surface in ["芝", "ダート"]:
        s_data = horse_data[horse_data["surface"] == surface]
        if len(s_data) > 0:
            avg = s_data["finish_num"].mean()
            wins = len(s_data[s_data["finish_num"] == 1])
            print(f"    {surface}: {len(s_data)}回, 平均{avg:.1f}着, {wins}勝")

# ============================================================
#  グラフ作成
# ============================================================

print("\n" + "=" * 60)
print("  📈 グラフ生成中...")
print("=" * 60)

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("競馬データ分析レポート", fontsize=16, fontweight="bold")

colors = ["#E8593C", "#3B8BD4", "#1D9E75", "#7F77DD",
          "#D85A30", "#534AB7", "#0F6E56", "#993C1D"]

# --- 1: 馬別勝率 ---
ax1 = axes[0][0]
names = []
win_rates = []
for name in races_df["horse_name"].unique():
    horse_data = races_df[races_df["horse_name"] == name]
    total = len(horse_data)
    wins = len(horse_data[horse_data["finish_num"] == 1])
    short_name = name.split("(")[0].strip() if "(" in name else name
    names.append(short_name)
    win_rates.append(wins / total * 100 if total > 0 else 0)

ax1.bar(names, win_rates, color=colors[:len(names)])
ax1.set_title("馬別勝率 (%)")
ax1.set_ylabel("勝率 (%)")
ax1.tick_params(axis="x", rotation=20)
for i, v in enumerate(win_rates):
    ax1.text(i, v + 1, f"{v:.1f}%", ha="center", fontsize=9)

# --- 2: 着順分布 (ボックスプロット) ---
ax2 = axes[0][1]
box_data = []
box_labels = []
for name in races_df["horse_name"].unique():
    horse_data = races_df[races_df["horse_name"] == name]["finish_num"].dropna()
    if len(horse_data) > 0:
        box_data.append(horse_data.values)
        short_name = name.split("(")[0].strip() if "(" in name else name
        box_labels.append(short_name)

if box_data:
    bp = ax2.boxplot(box_data, labels=box_labels, patch_artist=True)
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
        patch.set_alpha(0.6)
    ax2.set_title("着順分布")
    ax2.set_ylabel("着順")
    ax2.tick_params(axis="x", rotation=20)
else:
    ax2.set_title("着順分布 (データなし)")
    ax2.text(0.5, 0.5, "数値データなし", ha="center", va="center",
             transform=ax2.transAxes, fontsize=14)

# --- 3: 距離別平均着順 ---
ax3 = axes[1][0]
dist_order = ["短距離", "マイル", "中距離", "長距離"]
dist_full = ["短距離 (~1400m)", "マイル (1401~1800m)",
             "中距離 (1801~2200m)", "長距離 (2201m~)"]
has_data = False

for i, name in enumerate(races_df["horse_name"].unique()):
    horse_data = races_df[races_df["horse_name"] == name]
    avgs = []
    categories = []
    for j, cat in enumerate(dist_full):
        cat_data = horse_data[horse_data["dist_category"] == cat]
        if len(cat_data) > 0:
            avg_finish = cat_data["finish_num"].mean()
            if pd.notna(avg_finish):
                avgs.append(avg_finish)
                categories.append(dist_order[j])

    if avgs:
        has_data = True
        short_name = name.split("(")[0].strip() if "(" in name else name
        ax3.plot(categories, avgs, "o-", label=short_name,
                 color=colors[i], linewidth=2, markersize=8)

if has_data:
    ax3.set_title("距離別平均着順")
    ax3.set_ylabel("平均着順 (低いほど良い)")
    ax3.legend(fontsize=8)
    ax3.invert_yaxis()
else:
    ax3.set_title("距離別平均着順 (データなし)")

# --- 4: 人気 vs 着順 ---
ax4 = axes[1][1]
races_df["pop_num"] = pd.to_numeric(races_df["popularity"], errors="coerce")

for i, name in enumerate(races_df["horse_name"].unique()):
    horse_data = races_df[races_df["horse_name"] == name].dropna(
        subset=["pop_num", "finish_num"])
    if len(horse_data) > 0:
        short_name = name.split("(")[0].strip() if "(" in name else name
        ax4.scatter(horse_data["pop_num"], horse_data["finish_num"],
                    label=short_name, color=colors[i], alpha=0.6, s=50)

max_val = max(races_df["pop_num"].max(), races_df["finish_num"].max())
if pd.notna(max_val):
    ax4.plot([0, max_val], [0, max_val], "k--", alpha=0.3, label="人気=着順")
ax4.set_title("人気順位 vs 実際着順")
ax4.set_xlabel("人気順位")
ax4.set_ylabel("実際着順")
ax4.legend(fontsize=8)

plt.tight_layout()
plt.savefig("keiba_analysis.png", dpi=150, bbox_inches="tight")
print("\n  ✅ 'keiba_analysis.png' 保存完了!")

# ★ plt.show()는 창을 닫을 때까지 코드가 멈추므로 맨 마지막에
print("\n  グラフウィンドウを閉じると終了します...")
plt.show()

print("\n" + "=" * 60)
print("  分析完了!")
print("=" * 60)