#!/usr/bin/env python3
"""Validate frontmatter of entity markdown files against per-category schemas."""

import copy
import json
import re
import sys
from pathlib import Path

import jsonschema
import yaml

ROOT = Path(__file__).resolve().parent.parent
ENTITIES = ROOT / "entities"
SCHEMAS = ROOT / "schemas"
USERS_FILE = ROOT / "users.yaml"

TAG_PATTERN = r"^[a-zа-яё0-9-]+$"

ADDED_BY_PROPERTY = {"type": "string", "minLength": 1}

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


def load_users():
    if not USERS_FILE.is_file():
        return None, "users.yaml не найден в корне репозитория"
    try:
        data = yaml.safe_load(USERS_FILE.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, f"users.yaml не является валидным YAML: {exc}"
    if not isinstance(data, dict) or not isinstance(data.get("users"), list):
        return None, "users.yaml должен содержать список 'users:'"
    users = []
    for name in data["users"]:
        if not isinstance(name, str) or not name.strip():
            return None, "users.yaml: имена должны быть непустыми строками"
        users.append(name.strip())
    if len(set(users)) != len(users):
        return None, "users.yaml: имена не должны повторяться"
    return users, None


def load_schema(category):
    schema_path = SCHEMAS / f"{category}.schema.json"
    if not schema_path.exists():
        schema = copy.deepcopy(DEFAULT_SCHEMA)
    else:
        try:
            schema = json.loads(schema_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return None, f"схема {schema_path.name} повреждена: {exc}"
    schema.setdefault("properties", {})["added_by"] = ADDED_BY_PROPERTY
    return schema, None


def main():
    errors = []
    users, users_err = load_users()
    if users_err:
        errors.append(users_err)

    if not ENTITIES.is_dir():
        for error in errors:
            print(f"Ошибки:\n  - {error}")
        return 1 if errors else 0

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
            added_by = data.get("added_by")
            if users is not None and isinstance(added_by, str) and added_by:
                if added_by not in users:
                    errors.append(
                        f"{rel}: added_by '{added_by}' не найден в users.yaml "
                        f"(доступно: {', '.join(users)})"
                    )
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
