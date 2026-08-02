# memory

Репозиторий для хранения любимых фильмов, книг, сериалов и других категорий.
Данные — это обычные markdown-файлы с YAML-frontmatter, поэтому они читаются
человеком, удобно диффятся в git и открываются в Obsidian.

## Структура

```
entities/<category>/<slug>.md   # записи (одна запись = один файл)
templates/movies.md             # шаблоны новых записей (для Templater в Obsidian)
templates/books.md
templates/series.md
templates/games.md
templates/anime.md
templates/manga.md
schemas/<category>.schema.json  # JSON Schema: какие поля допустимы в категории
scripts/validate.py             # проверка всех записей
```

## Как добавить запись

1. Скопируй шаблон из `templates/<category>.md` в `entities/<category>/`.
2. Заполни `title` и по желанию `tags` и другие поля.
3. Коммит будет отклонён, если запись не пройдёт проверку.

Пример записи (`entities/movies/brat.md`):

```markdown
---
title: "Брат"
tags: [драма, криминал, россия]
---
```

## Категории и их поля

| Категория | Обязательные поля | Опциональные поля |
|-----------|-------------------|-------------------|
| movies    | `title`           | `tags`            |
| books     | `title`           | `author`, `tags`  |
| series    | `title`           | `status` (`watching` / `finished` / `dropped`), `tags` |
| games     | `title`           | `platform`, `tags` |
| anime     | `title`           | `status` (`watching` / `finished` / `dropped`), `tags` |
| manga     | `title`           | `status` (`reading` / `finished` / `dropped`), `tags` |

- `title` — непустая строка.
- `tags` — опциональный массив уникальных строк вида `[a-zа-яё0-9-]+`
  (например `драма`, `криминал`, `90-е`).
- Запрещены любые поля, не указанные в схеме категории (приводит к ошибке).
- Внутри категории названия не должны повторяться.

## Новая категория

Чтобы завести категорию `recipes`, нужно создать три вещи:

1. `entities/recipes/` — директория с записями.
2. `schemas/recipes.schema.json` — JSON Schema для frontmatter (примеры в `schemas/`).
3. `templates/recipes.md` — шаблон записи.

Категории без своей схемы валидируются по дефолтной (обязателен только `title`).

## Проверки

Локально перед коммитом (нужно установить зависимости):

```sh
pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files   # или просто git commit — хук сработает сам
```

В CI (GitHub Actions) та же проверка запускается на каждый push и pull request.
