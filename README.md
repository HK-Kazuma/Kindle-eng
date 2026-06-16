# Kindle Highlights → Anki 自動変換ツール

Kindleでハイライトした英単語をClaude APIで解析し、Ankiにインポート可能なCSVを生成するツール。

## セットアップ

```bash
cd kindle_to_anki
pip install -r requirements.txt
```

`.env.example` をコピーして `.env` を作成し、APIキーを設定する。

```bash
cp .env.example .env
# .env を編集して ANTHROPIC_API_KEY を設定
```

## 使い方

```bash
python main.py <kindle_highlights.csv>
```

出力は `anki_output.csv` に保存される（`-o` オプションで変更可）。

```bash
python main.py sample_input.csv -o my_deck.csv
```

## 入力CSVフォーマット

| 列 | 内容 |
|---|---|
| title | 書籍タイトル |
| author | 著者名 |
| location | Kindle内の位置 |
| highlighted_text | ハイライトしたテキスト |

スペースが1つ以下のハイライトを「単語」として処理し、文章は除外する。

## Ankiへのインポート手順

1. `anki_output.csv` を生成
2. Ankiを開き「ファイル → インポート」
3. フィールドの区切り文字を「カンマ」に設定
4. フィールドマッピング: フィールド1→表面、フィールド2→裏面

## ディレクトリ構成

```
kindle_to_anki/
├── main.py           # エントリーポイント
├── parser.py         # CSV読み込み・単語抽出
├── claude_api.py     # Claude API呼び出し
├── exporter.py       # Anki用CSV出力
├── requirements.txt
├── .env.example
├── sample_input.csv  # サンプル入力
└── error.log         # エラーログ（自動生成）
```
