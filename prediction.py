# ============================================================
#  競馬レース結果予測 - ステージ5: 機械学習モデル
#  目標: 過去のデータから「3着以内に入るか」を予測
#
#  設置: pip install scikit-learn pandas matplotlib
# ============================================================
 
import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
 
matplotlib.rcParams['font.family'] = ['Yu Gothic', 'Meiryo', 'MS Gothic']
matplotlib.rcParams['axes.unicode_minus'] = False
 
# ============================================================
#  [파트 A] 데이터 불러오기 + 특성(Feature) 만들기
# ============================================================
#
#  머신러닝에서 가장 중요한 개념: "특성(Feature)"
#
#  사람이 예측할 때:
#    "이 말은 인기 2번이고, 잔디 2000m인데, 이전에 비슷한 조건에서
#     잘 뛰었으니까 3착 안에 들겠다"
#
#  이 판단에 사용된 정보들:
#    - 인기 순위 → 특성 1
#    - 코스 종류 → 특성 2
#    - 거리      → 특성 3
#    - 과거 성적 → 특성 4, 5, 6...
#
#  이 "특성"들을 숫자로 바꿔서 컴퓨터에게 주면,
#  컴퓨터가 패턴을 찾아서 예측합니다.
# ============================================================
 
DB_NAME = "keiba.db"
conn = sqlite3.connect(DB_NAME)
races_df = pd.read_sql("SELECT * FROM races", conn)
horses_df = pd.read_sql("SELECT * FROM horses", conn)
conn.close()
 
print("=" * 60)
print("  競馬レース結果予測モデル")
print("=" * 60)
print(f"\n  元データ: {len(races_df)}件のレース記録")
 
# --- 거리에서 숫자 추출 ---
def extract_distance(dist_str):
    nums = "".join(c for c in str(dist_str) if c.isdigit())
    return int(nums) if nums else None
 
# --- 코스 종류 추출 (잔디=1, 더트=0) ---
def extract_surface(dist_str):
    s = str(dist_str)
    if "芝" in s:
        return 1  # 잔디
    elif "ダ" in s:
        return 0  # 더트
    return None
 
# --- 특성(Feature) 만들기 ---
races_df["finish_num"] = pd.to_numeric(races_df["finish_pos"], errors="coerce")
races_df["pop_num"] = pd.to_numeric(races_df["popularity"], errors="coerce")
races_df["heads_num"] = pd.to_numeric(races_df["num_horses"], errors="coerce")
races_df["distance_num"] = races_df["distance"].apply(extract_distance)
races_df["surface_num"] = races_df["distance"].apply(extract_surface)
 
# ★ 타겟(정답): 3착 이내면 1, 아니면 0
# 이걸 맞추는 게 모델의 목표!
races_df["top3"] = (races_df["finish_num"] <= 3).astype(int)
 
# --- 말별 과거 성적 통계 계산 ---
# "이 말이 지금까지 얼마나 잘 뛰었나"를 숫자로 표현
horse_stats = {}
for name in races_df["horse_name"].unique():
    h_data = races_df[races_df["horse_name"] == name]
    finishes = h_data["finish_num"].dropna()
 
    if len(finishes) > 0:
        horse_stats[name] = {
            "avg_finish": finishes.mean(),         # 평균 착순
            "win_rate": (finishes == 1).mean(),    # 승률
            "top3_rate": (finishes <= 3).mean(),   # 복승률
            "total_races": len(finishes),           # 총 출주 수
        }
    else:
        horse_stats[name] = {
            "avg_finish": 10,
            "win_rate": 0,
            "top3_rate": 0,
            "total_races": 0,
        }
 
# 말별 통계를 각 레이스 행에 추가
races_df["horse_avg_finish"] = races_df["horse_name"].map(
    lambda n: horse_stats.get(n, {}).get("avg_finish", 10))
races_df["horse_win_rate"] = races_df["horse_name"].map(
    lambda n: horse_stats.get(n, {}).get("win_rate", 0))
races_df["horse_top3_rate"] = races_df["horse_name"].map(
    lambda n: horse_stats.get(n, {}).get("top3_rate", 0))
races_df["horse_total_races"] = races_df["horse_name"].map(
    lambda n: horse_stats.get(n, {}).get("total_races", 0))
 
# ============================================================
#  [파트 B] 학습용 데이터 준비
# ============================================================
 
# ★ 사용할 특성(Feature) 목록
feature_columns = [
    "pop_num",            # 인기 순위
    "heads_num",          # 출주 두수
    "distance_num",       # 거리 (미터)
    "surface_num",        # 코스 (잔디=1, 더트=0)
    "horse_avg_finish",   # 그 말의 평균 착순
    "horse_win_rate",     # 그 말의 승률
    "horse_top3_rate",    # 그 말의 복승률
    "horse_total_races",  # 그 말의 총 출주 수
]
 
# 결측값이 있는 행 제거
model_df = races_df.dropna(subset=feature_columns + ["top3"])
print(f"  学習可能データ: {len(model_df)}件")
 
if len(model_df) < 10:
    print("\n  ⚠ データが少なすぎます。もっと馬を追加してください。")
    exit()
 
# ★ X = 특성(입력), y = 타겟(정답)
# 비유: 시험에서 X = 문제, y = 정답지
X = model_df[feature_columns]
y = model_df["top3"]
 
print(f"\n  特徴量 (Features): {len(feature_columns)}個")
for col in feature_columns:
    print(f"    - {col}: 平均 {X[col].mean():.2f}")
 
print(f"\n  3着以内の割合: {y.mean()*100:.1f}%")
 
# ★ 데이터를 "학습용"과 "테스트용"으로 분리
# 비유: 시험 전에 연습문제로 공부하고, 본 시험은 처음 보는 문제로 치는 것
# test_size=0.3 = 30%를 테스트용으로 남겨둠
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42
)
 
print(f"\n  学習データ: {len(X_train)}件")
print(f"  テストデータ: {len(X_test)}件")
 
 
# ============================================================
#  [파트 C] 모델 학습 (Random Forest)
# ============================================================
#
#  Random Forest (랜덤 포레스트) = "나무 여러 그루의 숲"
#
#  비유:
#    경마 예측가 100명에게 물어봄
#    - 어떤 사람은 "인기"를 중요하게 봄
#    - 어떤 사람은 "거리 적성"을 중요하게 봄
#    - 어떤 사람은 "과거 성적"을 중요하게 봄
#    100명의 다수결로 최종 결정 → 이게 랜덤 포레스트!
#
#  각 "나무"가 다른 기준으로 판단하고,
#  전체의 투표 결과가 최종 예측이 됩니다.
# ============================================================
 
print("\n" + "=" * 60)
print("  🌲 モデル学習中 (Random Forest)...")
print("=" * 60)
 
# ★ 모델 만들고 학습시키기 (이 2줄이 핵심!)
model = RandomForestClassifier(
    n_estimators=100,     # 나무 100그루
    max_depth=5,          # 나무 깊이 제한 (과적합 방지)
    random_state=42       # 재현성을 위한 시드값
)
model.fit(X_train, y_train)  # ★ 학습! (패턴을 찾는 과정)
 
print("  ✅ 学習完了!")
 
 
# ============================================================
#  [파트 D] 모델 평가
# ============================================================
 
# ★ 테스트 데이터로 예측해보기
y_pred = model.predict(X_test)
 
# 정확도 계산
accuracy = accuracy_score(y_test, y_pred)
print(f"\n  正解率 (Accuracy): {accuracy*100:.1f}%")
 
# 상세 리포트
print(f"\n  [분류 리포트]")
print(classification_report(y_test, y_pred,
                            target_names=["4着以下", "3着以内"],
                            zero_division=0))
 
 
# ============================================================
#  [파트 E] 어떤 특성이 중요한가? (Feature Importance)
# ============================================================
#
#  모델이 "어떤 정보를 가장 많이 참고했는가"를 알 수 있음
#  이게 경마에서도 유용: "인기가 중요한가, 거리가 중요한가?"
# ============================================================
 
print("=" * 60)
print("  📊 特徴量の重要度 (何が予測に効くか)")
print("=" * 60)
 
importances = model.feature_importances_
importance_df = pd.DataFrame({
    "特徴量": feature_columns,
    "重要度": importances
}).sort_values("重要度", ascending=False)
 
for _, row in importance_df.iterrows():
    bar = "█" * int(row["重要度"] * 50)
    print(f"  {row['特徴量']:25s} {row['重要度']:.3f} {bar}")
 
 
# ============================================================
#  [파트 F] 각 말의 예측 결과
# ============================================================
 
print("\n" + "=" * 60)
print("  🏇 馬別の予測結果")
print("=" * 60)
 
for name in races_df["horse_name"].unique():
    h_data = model_df[model_df["horse_name"] == name]
    if len(h_data) == 0:
        continue
 
    h_X = h_data[feature_columns]
    h_y = h_data["top3"]
 
    h_pred = model.predict(h_X)
    h_proba = model.predict_proba(h_X)  # 확률도 계산
 
    actual_top3 = h_y.sum()
    predicted_top3 = h_pred.sum()
    avg_proba = h_proba[:, 1].mean() * 100  # 3착 이내 평균 확률
 
    short_name = name.split("(")[0].strip() if "(" in name else name
    print(f"\n  {short_name}")
    print(f"    実際の3着内: {int(actual_top3)}回 / {len(h_data)}回")
    print(f"    予測の3着内: {int(predicted_top3)}回 / {len(h_data)}回")
    print(f"    平均3着内確率: {avg_proba:.1f}%")
 
 
# ============================================================
#  [파트 G] 그래프 생성
# ============================================================
 
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("競馬レース予測モデル分析", fontsize=16, fontweight="bold")
 
colors = ["#E8593C", "#3B8BD4", "#1D9E75", "#7F77DD",
          "#D85A30", "#534AB7", "#0F6E56", "#993C1D"]
 
# --- 1: 특성 중요도 막대그래프 ---
ax1 = axes[0][0]
imp_sorted = importance_df.sort_values("重要度", ascending=True)
ax1.barh(imp_sorted["特徴量"], imp_sorted["重要度"], color="#2d6a4f")
ax1.set_title("特徴量の重要度")
ax1.set_xlabel("重要度")
 
# --- 2: 혼동 행렬 (Confusion Matrix) ---
ax2 = axes[0][1]
cm = confusion_matrix(y_test, y_pred)
disp = ConfusionMatrixDisplay(cm, display_labels=["4着以下", "3着以内"])
disp.plot(ax=ax2, cmap="Greens", colorbar=False)
ax2.set_title("混同行列 (予測 vs 実際)")
 
# --- 3: 말별 예측 확률 ---
ax3 = axes[1][0]
horse_names_short = []
horse_probas = []
for name in races_df["horse_name"].unique():
    h_data = model_df[model_df["horse_name"] == name]
    if len(h_data) == 0:
        continue
    h_X = h_data[feature_columns]
    h_proba = model.predict_proba(h_X)[:, 1].mean() * 100
    short_name = name.split("(")[0].strip() if "(" in name else name
    horse_names_short.append(short_name)
    horse_probas.append(h_proba)
 
ax3.barh(horse_names_short, horse_probas, color=colors[:len(horse_names_short)])
ax3.set_title("馬別 3着以内予測確率 (%)")
ax3.set_xlabel("平均確率 (%)")
ax3.set_xlim(0, 100)
 
# --- 4: 인기 vs 예측 확률 산점도 ---
ax4 = axes[1][1]
proba_all = model.predict_proba(X)[:, 1] * 100
ax4.scatter(model_df["pop_num"], proba_all, alpha=0.5,
            c=model_df["top3"], cmap="RdYlGn", s=30)
ax4.set_title("人気順位 vs 予測確率")
ax4.set_xlabel("人気順位")
ax4.set_ylabel("3着以内予測確率 (%)")
ax4.axhline(y=50, color="gray", linestyle="--", alpha=0.5, label="50%ライン")
ax4.legend()
 
plt.tight_layout()
plt.savefig("keiba_prediction.png", dpi=150, bbox_inches="tight")
print("\n  ✅ 'keiba_prediction.png' 保存完了!")
 
plt.show()
 
print("\n" + "=" * 60)
print("  予測モデル構築完了!")
print("  このモデルをダッシュボードに組み込むことも可能です。")
print("=" * 60)