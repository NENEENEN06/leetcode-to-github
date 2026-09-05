#!/usr/bin/env python3
"""自动生成/更新根目录 README.md 的题目索引表。"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parent / "config.yaml"

DIR_PATTERN = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
START = "<!-- leetcode-index:start -->"
END = "<!-- leetcode-index:end -->"


def _parse_scalar(text: str):
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in ('"', "'"):
        return text[1:-1]
    low = text.lower()
    if low in ("true", "yes"):
        return True
    if low in ("false", "no"):
        return False
    if low in ("null", "none", "~"):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _load_config(path: Path) -> dict:
    if not path.exists():
        return {}
    root: dict = {}
    stack: list[tuple[int, dict]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        content = line.strip()
        if ":" not in content:
            continue
        key, _, val = content.partition(":")
        key = key.strip().strip('"').strip("'")
        val = val.strip()
        while stack and stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1] if stack else root
        if val == "":
            child: dict = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(val)
    return root


def _get(config: dict, dotted: str, default=None):
    node = config
    for part in dotted.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


def _extract_meta(text: str):
    number = title = difficulty = topic = None
    m = re.search(r"^#\s+(\d{1,4})\.\s*(.+?)\s*$", text, re.M)
    if m:
        number = int(m.group(1))
        title = m.group(2).strip()
    m = re.search(r"(?im)^-\s*Difficulty\s*:\s*(.+?)\s*$", text)
    if m:
        difficulty = m.group(1).strip()
    m = re.search(r"(?im)^-\s*Topics\s*:\s*(.+?)\s*$", text)
    if m:
        topics = [t.strip() for t in m.group(1).split(",") if t.strip()]
        topic = topics[0] if topics else None
    return number, title, difficulty, topic


def _slug_to_title(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-"))


def build_rows(repo: Path, root: str, readme_file: str):
    solutions_root = repo / root if root else repo
    if not solutions_root.is_dir():
        return []
    rows = []
    for d in sorted(solutions_root.iterdir()):
        if not d.is_dir() or not DIR_PATTERN.match(d.name):
            continue
        number = int(DIR_PATTERN.match(d.name).group(1))
        readme = d / readme_file
        title = difficulty = topic = ""
        if readme.is_file():
            text = readme.read_text(encoding="utf-8", errors="replace")
            _, t, diff, top = _extract_meta(text)
            title = t or _slug_to_title(d.name.split("-", 1)[1])
            difficulty = diff or ""
            topic = top or ""
        else:
            title = _slug_to_title(d.name.split("-", 1)[1])
        rows.append((number, title, difficulty, topic))
    rows.sort(key=lambda r: r[0])
    return rows


def _esc(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ").strip()


def render_table(rows) -> str:
    lines = ["## Problems", "", "| # | Problem | Difficulty | Topic |", "|---|---|---|---|"]
    for number, title, difficulty, topic in rows:
        lines.append(f"| {number:04d} | {_esc(title)} | {_esc(difficulty)} | {_esc(topic)} |")
    lines.append("")
    lines.append(f"共 {len(rows)} 道题。")
    return "\n".join(lines)


def make_block(rows) -> str:
    return f"{START}\n\n{render_table(rows)}\n\n{END}"


def update_index(index_path: Path, block: str):
    header = "# LeetCode Solutions\n\n这里是我的 LeetCode 刷题记录，按题号整理。\n\n"
    if not index_path.exists():
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(header + block + "\n", encoding="utf-8")
        return

    text = index_path.read_text(encoding="utf-8")
    if START in text and END in text:
        start_i = text.index(START)
        end_i = text.index(END) + len(END)
        if text[end_i:].startswith("\r\n"):
            end_i += 2
        elif text[end_i:].startswith("\n"):
            end_i += 1
        new_text = text[:start_i] + block + text[end_i:]
    else:
        new_text = text.rstrip() + "\n\n" + block + "\n"

    if not new_text.endswith("\n"):
        new_text += "\n"
    index_path.write_text(new_text, encoding="utf-8")


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="生成/更新 LeetCode 题目索引")
    parser.add_argument("--repo", help="目标仓库路径（默认取 config 的 repository.local_path，再默认当前目录）")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="config.yaml 路径")
    parser.add_argument("--index", help="索引文件路径（默认仓库根目录下的 index_file）")
    args = parser.parse_args(argv)

    config = _load_config(Path(args.config))
    if args.repo:
        repo = Path(args.repo)
    else:
        local = _get(config, "repository.local_path", "")
        repo = Path(local) if local else Path.cwd()

    root = _get(config, "repository.root", "")
    readme_file = _get(config, "structure.readme_file", "README.md")
    index_file = _get(config, "structure.index_file", "README.md")
    index_path = Path(args.index) if args.index else (repo / index_file)

    rows = build_rows(repo, root, readme_file)
    block = make_block(rows)
    update_index(index_path, block)

    print(f"已更新索引: {index_path}")
    print(f"共 {len(rows)} 道题。")
    for number, title, difficulty, topic in rows:
        print(f"  {number:04d}  {title}  [{difficulty}]  {topic}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
