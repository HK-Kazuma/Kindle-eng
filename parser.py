import re

import pandas as pd

HIGHLIGHT_LINE = re.compile(r'.+のハイライト \| 位置: \d+オプション')
STRIP_PUNCT = re.compile(r'^[.,;:!?"\']+|[.,;:!?"\']+$')


def is_word(text: str) -> bool:
    return text.count(" ") <= 1


def normalize(text: str) -> str:
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
    """
    seen: set[str] = set()
    results: list[dict] = []
    in_memo = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        if HIGHLIGHT_LINE.match(stripped):
            in_memo = False
            continue

        if stripped.startswith("メモ"):
            in_memo = True
            continue

        if in_memo:
            continue

        key = normalize(stripped)
        if not key or key in seen:
            continue
        if not is_word(key):
            continue

        seen.add(key)
        results.append({"word": key, "context": ""})

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
