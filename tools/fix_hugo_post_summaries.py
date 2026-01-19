from __future__ import annotations

import re
from pathlib import Path

POSTS_DIR = Path(
    "/Users/chleynx/Desktop/code/chleynx-blog/chensonghi.github.io/site/content/posts"
)

FM_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.S)

IMG_RE = re.compile(r"(^|\n)(!\[[^\]]*\]\([^\)]+\)|<img\s)", re.I)


def split_front_matter(text: str):
    text = text.replace("\r\n", "\n")
    m = FM_RE.search(text)
    if not m:
        return "", text
    return text[: m.end()], text[m.end() :]


def ensure_more_before_first_image(body: str) -> tuple[str, bool]:
    if "<!--more-->" in body:
        return body, False

    m = IMG_RE.search(body)
    if not m:
        return body, False

    insert_at = m.start(2)
    # Insert marker on its own line before first image.
    new_body = body[:insert_at]
    if not new_body.endswith("\n"):
        new_body += "\n"
    new_body += "\n<!--more-->\n\n"
    new_body += body[insert_at:]
    return new_body, True


def normalize_bundle_relative_links(body: str, slug: str) -> tuple[str, bool]:
    changed = False

    # Convert '../<slug>/img.png' -> './img.png'
    pat = re.compile(rf"\]\(\.\./{re.escape(slug)}/")
    body2, n = pat.subn("](./", body)
    if n:
        changed = True
    return body2, changed


def main() -> None:
    if not POSTS_DIR.exists():
        raise SystemExit(f"posts dir not found: {POSTS_DIR}")

    changed_files = 0
    for post_dir in sorted([p for p in POSTS_DIR.iterdir() if p.is_dir()]):
        index_md = post_dir / "index.md"
        if not index_md.exists():
            continue

        slug = post_dir.name
        raw = index_md.read_text(encoding="utf-8", errors="replace")
        fm, body = split_front_matter(raw)

        body, ch1 = normalize_bundle_relative_links(body, slug)
        body, ch2 = ensure_more_before_first_image(body)

        if ch1 or ch2:
            index_md.write_text(fm + body.lstrip("\n"), encoding="utf-8")
            changed_files += 1

    print(f"updated_posts={changed_files}")


if __name__ == "__main__":
    main()
