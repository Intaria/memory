#!/usr/bin/env python3
"""Validate frontmatter of entity markdown files against per-category schemas."""

import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "entities"
SCHEMAS = ROOT / "schemas"

TAG_PATTERN = r"^[a-zа-яё0-9-]+$"

DEFAULT_SCHEMA = {
    "type": "object",
    "required": ["title"],
    "properties": {
        "title": {"type": "string", "minLength": 1},
        "tags": {
            "type": "array",
            "items": {"type": "string", "pattern": TAG_PATTERN},
            "uniqueItems": True,
        },
    },
    "additionalProperties": True,
}


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None, "frontmatter не найден: файл должен начинаться со строки '---'"
    end = text.find("\n---", 4)
    if end == -1:
        return None, "frontmatter не закрыт: нет второй строки '---'"
    block = text[4:end]
    try:
        data = yaml.safe_load(block)
    except yaml.YAMLError as exc:
        return None, f"frontmatter не является валидным YAML: {exc}"
    if data is None:
        data = {}
    if not isinstance(data, dict):
        return None, "frontmatter должен быть объектом (пары 'ключ: значение')"
    return data, None


def load_schema(category):
    schema_path = SCHEMAS / f"{category}.schema.json"
    if not schema_path.exists():
        return DEFAULT_SCHEMA, None
    try:
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"схема {schema_path.name} повреждена: {exc}"
    return schema, None


def main():
    errors = []
    if not ENTITIES.is_dir():
        print("OK: директория entities/ не найдена, нечего проверять")
        return 0

    for category_dir in sorted(ENTITIES.iterdir()):
        if not category_dir.is_dir():
            continue
        category = category_dir.name
        schema, err = load_schema(category)
        if err:
            errors.append(f"[{category}] {err}")
            continue

        seen = {}
        for path in sorted(category_dir.glob("*.md")):
            rel = path.relative_to(ROOT)
            data, err = parse_frontmatter(path)
            if err:
                errors.append(f"{rel}: {err}")
                continue
            try:
                jsonschema.validate(data, schema)
            except jsonschema.ValidationError as exc:
                errors.append(f"{rel}: {exc.message}")
            title = data.get("title")
            if isinstance(title, str):
                key = title.strip().lower()
                if key and key in seen:
                    errors.append(
                        f"{rel}: дубликат названия '{title}' (также в {seen[key]})"
                    )
                seen[key] = rel

    if errors:
        print("Ошибки:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("OK: все записи валидны")
    return 0


if __name__ == "__main__":
    sys.exit(main())
