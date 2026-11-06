"""Render the latest posts from chrismccarthydev.uk into the profile README.

Replaces everything between the LATEST-POSTS markers. If the feed has no posts,
the section is left empty so no heading shows on the profile.
"""

from __future__ import annotations

import sys
import urllib.request
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

FEED_URL = "https://chrismccarthydev.uk/feed.xml"
README = Path(__file__).resolve().parent.parent / "README.md"
START, END = "<!-- LATEST-POSTS:START -->", "<!-- LATEST-POSTS:END -->"
MAX_POSTS = 5
ATOM = {"a": "http://www.w3.org/2005/Atom"}


def fetch_posts() -> list[tuple[str, str, datetime]]:
    req = urllib.request.Request(FEED_URL, headers={"User-Agent": "profile-readme-updater"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    posts = []
    for entry in root.findall("a:entry", ATOM):
        title = (entry.findtext("a:title", default="", namespaces=ATOM) or "").strip()
        link = entry.find("a:link[@rel='alternate']", ATOM)
        if link is None:
            link = entry.find("a:link", ATOM)
        published = entry.findtext("a:published", namespaces=ATOM) or entry.findtext(
            "a:updated", default="", namespaces=ATOM
        )
        if title and link is not None and published:
            posts.append((title, urljoin(FEED_URL, link.get("href", "")), datetime.fromisoformat(published)))
    posts.sort(key=lambda p: p[2], reverse=True)
    return posts[:MAX_POSTS]


def render(posts: list[tuple[str, str, datetime]]) -> str:
    if not posts:
        return ""
    lines = ["", "## ✍️ Latest Writing", ""]
    lines += [f"- [{t.replace(']', '\\]')}]({u}) · {d:%d %b %Y}" for t, u, d in posts]
    lines += ["", f"More at [chrismccarthydev.uk](https://chrismccarthydev.uk).", ""]
    return "\n".join(lines)


def main() -> int:
    text = README.read_text(encoding="utf-8")
    if START not in text or END not in text:
        print("Markers not found in README", file=sys.stderr)
        return 1
    head, rest = text.split(START, 1)
    _, tail = rest.split(END, 1)
    new = f"{head}{START}{render(fetch_posts())}{END}{tail}"
    if new != text:
        README.write_text(new, encoding="utf-8")
        print("README updated")
    else:
        print("No change")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
