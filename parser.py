import re
import unicodedata

import pandas as pd

HIGHLIGHT_LINE = re.compile(r'.+のハイライト \| 位置: \d+オプション')
STRIP_PUNCT = re.compile(r'^[.,;:!?"\']+|[.,;:!?"\']+$')


def is_word(text: str) -> bool:
    return text.count(" ") <= 1


def normalize(text: str) -> str:
    text = unicodedata.normalize('NFKC', text)
    return STRIP_PUNCT.sub("", text).strip().lower()


# --- CSV形式（既存） ---

def load_highlights(csv_path: str) -> pd.DataFrame:
    df = pd.read_csv(csv_path, encoding="utf-8")
    required_cols = {"highlighted_text"}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSVに必要な列がありません: {required_cols - set(df.columns)}")
    return df


def extract_words(df: pd.DataFrame) -> list[dict]:
    seen: set[str] = set()
    results: list[dict] = []

    for _, row in df.iterrows():
        raw = str(row.get("highlighted_text", "")).strip()
        if not raw:
            continue
        if not is_word(raw):
            continue
        key = normalize(raw)
        if not key or key in seen:
            continue
        seen.add(key)

        context_parts = []
        for col in ("title", "author", "location"):
            val = row.get(col)
            if val and str(val).strip():
                context_parts.append(str(val).strip())

        results.append({
            "word": key,
            "context": ", ".join(context_parts) if context_parts else "",
        })

    return results


# --- テキスト形式（Kindleノートブックのコピペ） ---

def extract_words_from_text(text: str) -> list[dict]:
    """
    Kindleノートブックからコピペしたテキストを解析する。

    フォーマット:
        [ハイライトしたテキスト]
        [色]のハイライト | 位置: [N]オプション

    「のハイライト」行の直前にある行だけを実際のハイライトとして確定する。
    これにより、ページ上の本タイトル・章タイトル・UI文字を除外できる。
    """
    seen: set[str] = set()
    results: list[dict] = []

    current_candidate: str | None = None
    in_memo = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        # のハイライト行 → 直前の候補を正式なハイライトとして確定
        if HIGHLIGHT_LINE.match(stripped):
            if current_candidate:
                key = normalize(current_candidate)
                if key and key not in seen and is_word(key):
                    seen.add(key)
                    results.append({"word": key, "context": ""})
            current_candidate = None
            in_memo = False
            continue

        # メモ開始行
        if stripped.startswith("メモ"):
            in_memo = True
            continue

        # メモ内容はスキップ（current_candidateは保持したまま）
        if in_memo:
            continue

        # ハイライト候補として保持（次の行が来れば上書きされる）
        current_candidate = stripped

    return results


def load_words_from_file(file_path: str) -> list[dict]:
    """ファイル拡張子に応じてCSVまたはテキスト形式を自動判定して読み込む。"""
    if file_path.lower().endswith(".csv"):
        df = load_highlights(file_path)
        return extract_words(df)
    else:
        with open(file_path, encoding="utf-8") as f:
            text = f.read()
        return extract_words_from_text(text)
