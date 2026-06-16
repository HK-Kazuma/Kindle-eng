import csv
import os


def format_back(info: dict) -> str:
    japanese = info.get("japanese", "")
    example = info.get("example", "")
    image = info.get("image", "")
    return (
        f"【意味】{japanese}\n\n"
        f"【例文】\n{example}\n\n"
        f"【イメージ】\n{image}"
    )


def export_to_csv(records: list[dict], output_path: str) -> None:
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["表面", "裏面"])
        for rec in records:
            writer.writerow([rec["word"], rec["back"]])
