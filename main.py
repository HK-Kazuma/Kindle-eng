import argparse
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv
from tqdm import tqdm

from parser import load_words_from_file
from claude_api import fetch_word_info
from exporter import format_back, export_to_csv

load_dotenv()

logging.basicConfig(
    filename="error.log",
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    encoding="utf-8",
)

MAX_WORKERS = 5


def process_entry(entry: dict) -> tuple[str, dict | None]:
    info = fetch_word_info(entry["word"], entry["context"])
    return entry["word"], info


def main() -> None:
    parser = argparse.ArgumentParser(description="Kindleハイライト → Anki CSV変換ツール")
    parser.add_argument("input_file", help="Kindleハイライトのファイル（.csv または .txt）")
    parser.add_argument(
        "-o", "--output",
        default="anki_output.csv",
        help="出力CSVファイルパス（デフォルト: anki_output.csv）",
    )
    parser.add_argument(
        "-w", "--workers",
        type=int,
        default=MAX_WORKERS,
        help=f"並列数（デフォルト: {MAX_WORKERS}）",
    )
    args = parser.parse_args()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("エラー: ANTHROPIC_API_KEY が設定されていません。.env ファイルを確認してください。")
        sys.exit(1)

    print(f"読み込み中: {args.input_file}")
    try:
        words = load_words_from_file(args.input_file)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {args.input_file}")
        sys.exit(1)
    except Exception as e:
        print(f"エラー: ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

    if not words:
        print("処理対象の単語が見つかりませんでした。")
        sys.exit(0)

    total = len(words)
    print(f"単語数（重複除去後）: {total}　並列数: {args.workers}")

    # 元の順序を保持するためインデックスで管理
    results: dict[str, dict | None] = {}
    failed: list[str] = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(process_entry, entry): entry["word"] for entry in words}
        with tqdm(total=total, desc="処理中", unit="単語") as bar:
            for future in as_completed(futures):
                word, info = future.result()
                if info is None:
                    failed.append(word)
                else:
                    results[word] = info
                bar.update(1)
                tqdm.write(f"完了: [{word}]")

    # 元の順序でCSV出力
    records = [
        {"word": e["word"], "back": format_back(results[e["word"]])}
        for e in words
        if e["word"] in results
    ]

    export_to_csv(records, args.output)
    print(f"\n完了: {args.output} に {len(records)} 件出力しました。")

    if failed:
        print(f"失敗した単語 ({len(failed)} 件): {', '.join(failed)}")
        print("詳細は error.log を確認してください。")


if __name__ == "__main__":
    main()
