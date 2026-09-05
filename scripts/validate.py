#!/usr/bin/env python3
"""校验 leetcode-to-github 生成的仓库结构。

检查项：
- 目录命名（{四位题号}-{kebab-case 标题}）
- 单题目录是否包含 README 与 solution 代码文件
- README 是否包含模板要求的核心段落
- 是否存在重复题号
- 是否存在明显敏感信息（API Key / Token / 密码等）
- Markdown 代码块围栏是否基本配对
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
DEFAULT_CONFIG = SCRIPT_DIR.parent / "config.yaml"

DIR_PATTERN = re.compile(r"^(\d{4})-([a-z0-9]+(?:-[a-z0-9]+)*)$")
SOLUTION_PATTERN = re.compile(r"^solution\.[a-z0-9]+$", re.IGNORECASE)

REQUIRED_SECTIONS = ["题目", "我的思路", "代码", "代码分析", "复杂度", "总结"]

SENSITIVE_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "私钥"),
    (re.compile(r"(?i)api[_-]?key\s*[:=]\s*\S+"), "API Key"),
    (re.compile(r"(?i)secret\s*[:=]\s*\S+"), "Secret"),
    (re.compile(r"(?i)password\s*[:=]\s*\S+"), "密码"),
    (re.compile(r"(?i)passwd\s*[:=]\s*\S+"), "密码"),
    (re.compile(r"(?i)access[_-]?token\s*[:=]\s*\S+"), "Access Token"),
    (re.compile(r"(?i)authorization\s*:\s*bearer\s+\S+"), "Authorization"),
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"), "GitHub Token"),
    (re.compile(r"(?i)github[_-]?token\s*[:=]\s*\S+"), "GitHub Token"),
]


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
    """读取本 skill 使用的简单 YAML 子集（仅嵌套映射 + 标量）。"""
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


def _extract_heading(text: str):
    m = re.search(r"^#\s+(\d{1,4})\.\s*(.+?)\s*$", text, re.M)
    if not m:
        return None, None
    return int(m.group(1)), m.group(2).strip()


def _has_section(text: str, section: str) -> bool:
    return bool(re.search(rf"^#{{2,3}}\s+{re.escape(section)}\s*$", text, re.M))


def _fences_balanced(text: str) -> bool:
    fence_char = None
    fence_len = 0
    for line in text.splitlines():
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if not m:
            continue
        marker = m.group(1)
        if fence_char is None:
            fence_char = marker[0]
            fence_len = len(marker)
        elif marker[0] == fence_char and len(marker) >= fence_len:
            fence_char = None
            fence_len = 0
    return fence_char is None


def validate(repo: Path, config: dict):
    errors: list[str] = []
    warnings: list[str] = []
    root = _get(config, "repository.root", "")
    readme_file = _get(config, "structure.readme_file", "README.md")
    solutions_root = repo / root if root else repo

    if not solutions_root.is_dir():
        return [f"题解目录不存在: {solutions_root}"], []

    seen_numbers: dict[int, Path] = {}
    dirs = sorted(d for d in solutions_root.iterdir() if d.is_dir() and DIR_PATTERN.match(d.name))

    for d in dirs:
        number = int(DIR_PATTERN.match(d.name).group(1))
        if number in seen_numbers:
            errors.append(f"重复题号 {number:04d}: {seen_numbers[number].name} 与 {d.name}")
        else:
            seen_numbers[number] = d

        readme = d / readme_file
        if not readme.is_file():
            errors.append(f"{d.name}: 缺少 {readme_file}")
            continue

        text = readme.read_text(encoding="utf-8", errors="replace")
        head_num, _ = _extract_heading(text)
        if head_num is None:
            errors.append(f"{d.name}: README 缺少形如 '# 0001. Two Sum' 的标题")
        elif head_num != number:
            warnings.append(f"{d.name}: 目录题号 {number:04d} 与 README 标题题号 {head_num:04d} 不一致")

        for sec in REQUIRED_SECTIONS:
            if not _has_section(text, sec):
                errors.append(f"{d.name}: README 缺少 '## {sec}' 段落")

        if not _fences_balanced(text):
            errors.append(f"{d.name}: README 代码块围栏不配对")

        solutions = [
            p for p in d.iterdir()
            if p.is_file() and SOLUTION_PATTERN.match(p.name) and p.suffix.lower() != ".md"
        ]
        if not solutions:
            errors.append(f"{d.name}: 缺少 solution 代码文件")

        for f in sorted(d.iterdir()):
            if not f.is_file():
                continue
            try:
                ftext = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            for pat, label in SENSITIVE_PATTERNS:
                if pat.search(ftext):
                    errors.append(f"{d.name}/{f.name}: 检测到疑似敏感信息 ({label})")

    # 扫描仓库根目录的文档类文件，防止把密钥写进 README/配置
    for f in sorted(repo.iterdir()):
        if not f.is_file():
            continue
        if f.suffix.lower() not in (".md", ".yaml", ".yml", ".json", ".toml", ".txt"):
            continue
        try:
            ftext = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for pat, label in SENSITIVE_PATTERNS:
            if pat.search(ftext):
                errors.append(f"{f.name}: 检测到疑似敏感信息 ({label})")

    return errors, warnings


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="校验 leetcode-to-github 仓库结构")
    parser.add_argument("--repo", help="目标仓库路径（默认取 config 的 repository.local_path，再默认当前目录）")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="config.yaml 路径")
    args = parser.parse_args(argv)

    config = _load_config(Path(args.config))
    if args.repo:
        repo = Path(args.repo)
    else:
        local = _get(config, "repository.local_path", "")
        repo = Path(local) if local else Path.cwd()

    errors, warnings = validate(repo, config)
    for w in warnings:
        print(f"[警告] {w}")
    for e in errors:
        print(f"[错误] {e}")
    print()
    print(f"目录: {repo}")
    print(f"结果: {'通过' if not errors else '未通过'}（{len(errors)} 个错误，{len(warnings)} 个警告）")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
