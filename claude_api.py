import json
import logging
import anthropic

logger = logging.getLogger(__name__)

CLIENT = None


def get_client() -> anthropic.Anthropic:
    global CLIENT
    if CLIENT is None:
        CLIENT = anthropic.Anthropic()
    return CLIENT


def build_prompt(word: str, context: str) -> str:
    context_line = f"\n文脈: {context}" if context else ""
    return f"""以下の英単語について、JSON形式で返してください。

単語: {word}{context_line}

{{
  "japanese": "日本語訳（文脈に合った意味、10字以内）",
  "example": "自然な英語例文（単語の典型的な使われ方）",
  "image": "この単語のコアイメージを1〜2行で。語源の分解ではなく、ネイティブが感じる空気感・具体的なシーン・日本語で頭に焼き付けやすいイメージで書くこと。"
}}

JSONのみを返してください。説明文は不要です。"""


def fetch_word_info(word: str, context: str = "") -> dict | None:
    prompt = build_prompt(word, context)
    try:
        client = get_client()
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = message.content[0].text.strip()
        # コードブロックがある場合は除去
        raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(raw)
    except json.JSONDecodeError as e:
        logger.error(f"JSONパースエラー [{word}]: {e}")
    except anthropic.APIError as e:
        logger.error(f"APIエラー [{word}]: {e}")
    except Exception as e:
        logger.error(f"予期しないエラー [{word}]: {e}")
    return None
