from __future__ import annotations

import re
import shutil
from pathlib import Path
from urllib.parse import quote

# Hexo sources
HEXO_POSTS_DIR = Path("/Users/chleynx/Desktop/code/chleynx-blog/Blog/source/_posts")

# Hugo site
HUGO_POSTS_DIR = Path(
    "/Users/chleynx/Desktop/code/chleynx-blog/chensonghi.github.io/site/content/posts"
)

FRONT_MATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)

REMOVE_FM_KEYS = {"typora-root-url"}


def parse_front_matter(markdown_text: str):
    text = markdown_text.replace("\r\n", "\n")
    m = FRONT_MATTER_RE.search(text)
    if not m:
        return None, text

    fm_raw = m.group(1)
    body = text[m.end() :]

    fm: dict[str, str] = {}
    for line in fm_raw.split("\n"):
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip()

    return fm, body


def normalize_to_list_literal(value: str) -> str:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return value

    # handle comma-separated
    if "," in value:
        parts = [p.strip().strip('"') for p in value.split(",") if p.strip()]
        return "[" + ", ".join(f'"{p}"' for p in parts) + "]"

    # single value -> list
    v = value.strip('"')
    return f'["{v}"]'


def build_front_matter(fm: dict[str, str]) -> str:
    out: list[str] = []

    if "title" in fm:
        out.append(f"title: {fm['title']}")
    if "date" in fm:
        out.append(f"date: {fm['date']}")

    if "tags" in fm:
        out.append(f"tags: {normalize_to_list_literal(fm['tags'])}")
    if "categories" in fm:
        out.append(f"categories: {normalize_to_list_literal(fm['categories'])}")

    for key, value in fm.items():
        if key in {"title", "date", "tags", "categories"}:
            continue
        if key in REMOVE_FM_KEYS:
            continue
        out.append(f"{key}: {value}")

    return "---\n" + "\n".join(out) + "\n---\n\n"


def rewrite_body_links(body: str, post_basename: str) -> str:
    # Hexo often emits links like:
    #   /YYYY/MM/DD/<urlencoded title>/image.png
    # We'll rewrite those to page-bundle relative paths: ./image.png
    enc = quote(post_basename)

    b = body
    # markdown link or image: ](/yyyy/mm/dd/<name>/...
    b = re.sub(rf"\]\(/\d{{4}}/\d{{2}}/\d{{2}}/{re.escape(enc)}/", "](./", b)
    b = re.sub(rf"\]\(/\d{{4}}/\d{{2}}/\d{{2}}/{re.escape(post_basename)}/", "](./", b)

    # also handle absolute URLs to the same path (if any)
    b = re.sub(
        rf"\]\(https?://[^)]+/\d{{4}}/\d{{2}}/\d{{2}}/{re.escape(enc)}/",
        "](./",
        b,
    )
    b = re.sub(
        rf"\]\(https?://[^)]+/\d{{4}}/\d{{2}}/\d{{2}}/{re.escape(post_basename)}/",
        "](./",
        b,
    )

    return b


def copy_assets(post_basename: str, dest_dir: Path) -> int:
    asset_dir = HEXO_POSTS_DIR / post_basename
    if not asset_dir.exists() or not asset_dir.is_dir():
        return 0

    copied = 0
    for child in asset_dir.iterdir():
        if child.is_file():
            shutil.copy2(child, dest_dir / child.name)
            copied += 1

    return copied


def migrate_one(md_path: Path) -> tuple[int, int]:
    post_basename = md_path.stem
    dest_dir = HUGO_POSTS_DIR / post_basename
    dest_dir.mkdir(parents=True, exist_ok=True)

    raw = md_path.read_text(encoding="utf-8", errors="replace")
    fm, body = parse_front_matter(raw)
    if fm is None:
        return (0, 0)

    body = rewrite_body_links(body, post_basename)
    new_text = build_front_matter(fm) + body.lstrip("\n")

    (dest_dir / "index.md").write_text(new_text, encoding="utf-8")

    copied = copy_assets(post_basename, dest_dir)
    return (1, copied)


def main() -> None:
    if not HEXO_POSTS_DIR.exists():
        raise SystemExit(f"Hexo posts dir not found: {HEXO_POSTS_DIR}")

    HUGO_POSTS_DIR.mkdir(parents=True, exist_ok=True)

    md_files = sorted([p for p in HEXO_POSTS_DIR.iterdir() if p.is_file() and p.suffix == ".md"])

    migrated = 0
    assets = 0
    skipped = 0

    for md in md_files:
        ok, copied = migrate_one(md)
        if ok:
            migrated += 1
            assets += copied
        else:
            skipped += 1

    print(f"migrated_posts={migrated} skipped_posts={skipped} copied_assets={assets}")


if __name__ == "__main__":
    main()
