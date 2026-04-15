# ============================================================
#  競馬データダッシュボード - ステージ4: Webアプリ
#  実行: python app.py → ブラウザで http://localhost:5000
# ============================================================

import sqlite3
from flask import Flask, render_template, request

# ★ Flask = ウェブサーバーを作る道具
# この1行で「Webサイトを作る準備OK」になる
app = Flask(__name__)

DB_NAME = "keiba.db"


def get_db():
    """データベースに接続して返す関数"""
    conn = sqlite3.connect(DB_NAME)
    # ★ row_factory = 結果を辞書(dict)形式で返す設定
    # これがないと row[0], row[1] みたいに番号でアクセスするしかない
    # これがあると row["name"], row["color"] みたいに名前でアクセスできる
    conn.row_factory = sqlite3.Row
    return conn


# ============================================================
#  ページ1: トップページ (全馬一覧)
# ============================================================

# ★ @app.route("/") = 「アドレスが / の時、この関数を実行しろ」
# ブラウザで http://localhost:5000/ にアクセスすると実行される
@app.route("/")
def index():
    conn = get_db()

    # 全馬の基本情報を取得
    horses = conn.execute("""
        SELECT url, name, gender, color, birth_date, trainer,
               total_record, sire, dam, total_races
        FROM horses ORDER BY name
    """).fetchall()

    # 各馬の勝率を計算
    horse_stats = []
    for horse in horses:
        races = conn.execute("""
            SELECT finish_pos FROM races WHERE horse_url = ?
        """, (horse["url"],)).fetchall()

        total = len(races)
        wins = sum(1 for r in races
                   if r["finish_pos"].isdigit() and int(r["finish_pos"]) == 1)
        top3 = sum(1 for r in races
                   if r["finish_pos"].isdigit() and int(r["finish_pos"]) <= 3)

        win_rate = round(wins / total * 100, 1) if total > 0 else 0
        top3_rate = round(top3 / total * 100, 1) if total > 0 else 0

        horse_stats.append({
            "url": horse["url"],
            "name": horse["name"],
            "gender": horse["gender"],
            "color": horse["color"],
            "birth_date": horse["birth_date"],
            "trainer": horse["trainer"],
            "total_record": horse["total_record"],
            "sire": horse["sire"],
            "dam": horse["dam"],
            "total_races": total,
            "wins": wins,
            "top3": top3,
            "win_rate": win_rate,
            "top3_rate": top3_rate,
        })

    conn.close()

    # ★ render_template = HTMLファイルにデータを埋め込んで返す
    return render_template("index.html", horses=horse_stats)


# ============================================================
#  ページ2: 馬の詳細ページ
# ============================================================

# ★ <path:url> = URLの一部をパラメータとして受け取る
# 例: /horse/https://db.netkeiba.com/horse/1994100530/
@app.route("/horse/<path:url>")
def horse_detail(url):
    conn = get_db()

    # 馬の基本情報
    horse = conn.execute("""
        SELECT * FROM horses WHERE url = ?
    """, (url,)).fetchone()

    if not horse:
        return "馬が見つかりません", 404

    # 全レース記録
    races = conn.execute("""
        SELECT * FROM races WHERE horse_url = ? ORDER BY race_date DESC
    """, (url,)).fetchall()

    # --- 統計計算 ---
    total = len(races)
    finish_nums = []
    for r in races:
        if r["finish_pos"].isdigit():
            finish_nums.append(int(r["finish_pos"]))

    wins = sum(1 for f in finish_nums if f == 1)
    top3 = sum(1 for f in finish_nums if f <= 3)
    win_rate = round(wins / total * 100, 1) if total > 0 else 0
    top3_rate = round(top3 / total * 100, 1) if total > 0 else 0
    avg_finish = round(sum(finish_nums) / len(finish_nums), 1) if finish_nums else 0

    # --- 距離別成績 ---
    dist_stats = {}
    for r in races:
        dist_str = r["distance"] or ""
        nums = "".join(c for c in dist_str if c.isdigit())
        if not nums:
            continue
        d = int(nums)
        if d <= 1400:
            cat = "短距離"
        elif d <= 1800:
            cat = "マイル"
        elif d <= 2200:
            cat = "中距離"
        else:
            cat = "長距離"

        if cat not in dist_stats:
            dist_stats[cat] = {"total": 0, "wins": 0, "finishes": []}

        dist_stats[cat]["total"] += 1
        if r["finish_pos"].isdigit():
            f = int(r["finish_pos"])
            dist_stats[cat]["finishes"].append(f)
            if f == 1:
                dist_stats[cat]["wins"] += 1

    for cat in dist_stats:
        fs = dist_stats[cat]["finishes"]
        dist_stats[cat]["avg"] = round(sum(fs) / len(fs), 1) if fs else 0

    # --- コース適性 ---
    surface_stats = {}
    for r in races:
        dist_str = r["distance"] or ""
        if "芝" in dist_str:
            surface = "芝"
        elif "ダ" in dist_str:
            surface = "ダート"
        else:
            continue

        if surface not in surface_stats:
            surface_stats[surface] = {"total": 0, "wins": 0, "finishes": []}

        surface_stats[surface]["total"] += 1
        if r["finish_pos"].isdigit():
            f = int(r["finish_pos"])
            surface_stats[surface]["finishes"].append(f)
            if f == 1:
                surface_stats[surface]["wins"] += 1

    for s in surface_stats:
        fs = surface_stats[s]["finishes"]
        surface_stats[s]["avg"] = round(sum(fs) / len(fs), 1) if fs else 0

    # --- 着順分布 (グラフ用) ---
    finish_distribution = [0] * 18  # 1着~18着
    for f in finish_nums:
        if 1 <= f <= 18:
            finish_distribution[f - 1] += 1

    # --- 人気 vs 着順 (散布図用) ---
    pop_vs_finish = []
    for r in races:
        if r["finish_pos"].isdigit() and r["popularity"] and r["popularity"].isdigit():
            pop_vs_finish.append({
                "pop": int(r["popularity"]),
                "finish": int(r["finish_pos"]),
                "race": r["race_name"],
            })

    conn.close()

    return render_template("horse.html",
                           horse=horse,
                           races=races,
                           total=total,
                           wins=wins,
                           top3=top3,
                           win_rate=win_rate,
                           top3_rate=top3_rate,
                           avg_finish=avg_finish,
                           dist_stats=dist_stats,
                           surface_stats=surface_stats,
                           finish_distribution=finish_distribution,
                           pop_vs_finish=pop_vs_finish)


# ============================================================
#  検索機能
# ============================================================

@app.route("/search")
def search():
    # ★ request.args.get("q") = URLの?q=の値を取得
    # 例: /search?q=サイレンス → query = "サイレンス"
    query = request.args.get("q", "")
    conn = get_db()

    horses = conn.execute("""
        SELECT url, name, gender, color, sire, total_record
        FROM horses
        WHERE name LIKE ? OR sire LIKE ? OR dam LIKE ? OR trainer LIKE ?
    """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()

    conn.close()
    return render_template("index.html", horses=horses, search_query=query)


# ============================================================
#  サーバー起動
# ============================================================

if __name__ == "__main__":
    # ★ debug=True = コードを変えると自動で再起動
    # ★ ブラウザで http://localhost:5000 を開く
    print("\n" + "=" * 50)
    print("  競馬データダッシュボード起動!")
    print("  ブラウザで http://localhost:5000 を開いてください")
    print("  終了: Ctrl + C")
    print("=" * 50 + "\n")
    app.run(debug=True)
