#!/usr/bin/env python3
"""Pick random entity records, optionally limited to a category."""

import argparse
import random
import sys
from pathlib import Path

from validate import parse_frontmatter

ROOT = Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "entities"


def collect_entries():
    entries = []
    if not ENTITIES.is_dir():
        sys.exit("Ошибка: директория entities/ не найдена")
    for category_dir in sorted(ENTITIES.iterdir()):
        if not category_dir.is_dir():
            continue
        for path in sorted(category_dir.glob("*.md")):
            data, err = parse_frontmatter(path)
            if err:
                sys.exit(f"Ошибка: {path.relative_to(ROOT)}: {err}")
            entries.append(
                {
                    "category": category_dir.name,
                    "title": data.get("title", path.stem),
                }
            )
    return entries


def main():
    parser = argparse.ArgumentParser(description="Случайная запись из memory")
    parser.add_argument("category", help="категория (обязательна)")
    parser.add_argument(
        "-n", "--count", type=int, default=1, help="сколько записей выдать (без повторов)"
    )
    args = parser.parse_args()

    if args.count < 1:
        sys.exit("Ошибка: -n должно быть >= 1")

    entries = collect_entries()
    categories = {e["category"] for e in entries}
    if args.category not in categories:
        available = ", ".join(sorted(categories))
        sys.exit(
            f"Ошибка: категория '{args.category}' не найдена (доступно: {available})"
        )
    pool = [e for e in entries if e["category"] == args.category]

    if not pool:
        sys.exit("Ошибка: в категории нет записей")
    if args.count > len(pool):
        sys.exit(
            f"Ошибка: запрошено {args.count} записей, но доступно {len(pool)}"
        )

    picked = random.sample(pool, args.count)
    for entry in picked:
        print(entry["title"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
