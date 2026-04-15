# 🏇 競馬データ分析ダッシュボード

netkeiba.comから競走馬データを自動収集し、SQLiteに保存、分析・可視化を行い、Flaskで分析ダッシュボードを構築したプロジェクトです。

## デモ

### トップページ（全馬一覧）
- 登録馬の一覧表示、勝率バー、血統情報
- 馬名・種牡馬・調教師による検索機能

### 馬詳細ページ
- 基本情報・血統テーブル
- 着順分布グラフ（Chart.js）
- 人気順位 vs 実際着順の散布図
- 距離適性・コース適性分析
- 全レース記録一覧

### データ分析レポート
- 馬別勝率比較
- 着順分布（ボックスプロット）
- 距離別平均着順
- 人気 vs 着順相関分析

## 技術スタック

| カテゴリ | 技術 |
|---------|------|
| データ収集 | Python, Selenium, BeautifulSoup |
| データベース | SQLite3 |
| データ分析 | pandas, matplotlib |
| Webアプリ | Flask, Jinja2 |
| フロントエンド | HTML/CSS, Chart.js |

## プロジェクト構成

```
keiba-dashboard/
├── README.md              # このファイル
├── requirements.txt       # 依存パッケージ
├── scraper.py             # データ収集スクリプト
├── analysis.py            # データ分析・グラフ生成
├── app.py                 # Flask Webアプリ
├── templates/
│   ├── index.html         # トップページ
│   └── horse.html         # 馬詳細ページ
└── keiba_analysis.png     # 分析レポート画像
```

## セットアップ

### 1. リポジトリをクローン
```bash
git clone https://github.com/あなたのユーザー名/keiba-dashboard.git
cd keiba-dashboard
```

### 2. 依存パッケージをインストール
```bash
pip install -r requirements.txt
```

### 3. データ収集
```bash
python scraper.py
```
netkeiba.comから競走馬データを収集し、`keiba.db`に保存します。

### 4. データ分析（任意）
```bash
python analysis.py
```
分析グラフ（`keiba_analysis.png`）を生成します。

### 5. ダッシュボード起動
```bash
python app.py
```
ブラウザで http://localhost:5000 を開いてください。

## 機能詳細

### データ収集（scraper.py）
- Seleniumによる動的ページのスクレイピング
- 基本情報（馬名、性別、毛色、生年月日、調教師）
- 血統情報（父・母・祖父母の4代血統）
- 全競走成績（日付、開催、レース名、着順、騎手、距離、人気、頭数）
- 複数馬の一括収集対応
- サーバー負荷軽減のためのインターバル設定

### データベース（SQLite3）
- `horses`テーブル: 馬の基本情報・血統
- `races`テーブル: 全競走記録
- URL重複チェックによる安全な再実行

### データ分析（analysis.py）
- 馬別勝率・複勝率の算出
- 距離カテゴリ別（短距離/マイル/中距離/長距離）成績分析
- コース適性（芝/ダート）分析
- matplotlib による4種のグラフ生成

### Webダッシュボード（app.py）
- 全馬一覧（勝率バー付きカード表示）
- 馬詳細ページ（統計・血統・グラフ・全戦績）
- 検索機能（馬名・種牡馬・調教師対応）
- Chart.jsによるインタラクティブなグラフ
- レスポンシブデザイン

## 今後の展望
- [ ] 機械学習によるレース結果予測モデルの構築
- [ ] より多くの馬データの収集（100頭以上）
- [ ] 騎手・調教師別の分析機能追加
- [ ] 血統分析の深化（系統別の距離適性など）

## 作者
個人プロジェクトとして開発

## ライセンス
MIT License
