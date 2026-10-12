#!/usr/bin/env python3
"""kb_lint.py: check that every `path:line` citation in the knowledge base exists.

A knowledge base with wrong line numbers is worse than none (Mozannar et al. 2024:
verification is the hidden cost of AI output). This script is read-only.

Usage:
  python kb_lint.py [REPO_ROOT] [--kb docs/codebase-knowledge] [--strict]

Exit code 0 when clean, 1 when broken citations were found.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CITE = re.compile(r"`?(?P<path>(?:[\w.@-]+/)*[\w.@-]+\.[A-Za-z0-9]{1,10}):(?P<start>\d+)(?:-(?P<end>\d+))?`?")
COMMIT = re.compile(r"\bcommit\s+(?P<sha>[0-9a-f]{7,40})\b")
URL_LIKE = re.compile(r"https?://")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--kb", default="docs/codebase-knowledge")
    ap.add_argument("--strict", action="store_true", help="also fail on sentences with no citation at all")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    kb = root / args.kb
    if not kb.is_dir():
        print(f"no knowledge base at {kb}")
        return 1

    problems: list[str] = []
    checked = 0
    uncited = 0
    line_cache: dict[Path, int] = {}
    for md in sorted(kb.rglob("*.md")):
        text = md.read_text(encoding="utf-8", errors="replace")
        for ln, line in enumerate(text.splitlines(), 1):
            if URL_LIKE.search(line):
                continue
            cites = list(CITE.finditer(line))
            if args.strict and not cites and not COMMIT.search(line) and re.search(r"[a-z]\.\s|[a-z]\.$", line) \
                    and not line.lstrip().startswith(("#", "|", "-", "*", ">", "```")):
                uncited += 1
            for m in cites:
                checked += 1
                target = root / m.group("path")
                where = f"{md.relative_to(root).as_posix()}:{ln}"
                if not target.is_file():
                    problems.append(f"{where}: file not found: {m.group('path')}")
                    continue
                if target not in line_cache:
                    try:
                        line_cache[target] = sum(1 for _ in target.open("rb"))
                    except OSError:
                        line_cache[target] = 0
                start, end = int(m.group("start")), int(m.group("end") or m.group("start"))
                n = line_cache[target]
                if start < 1 or end > n or start > end:
                    problems.append(f"{where}: {m.group('path')} has {n} lines, cited {start}-{end}")
            for m in COMMIT.finditer(line):
                checked += 1
                r = subprocess.run(["git", "-C", str(root), "cat-file", "-e", m.group("sha") + "^{commit}"],
                                   capture_output=True)
                if r.returncode != 0:
                    problems.append(f"{md.relative_to(root).as_posix()}:{ln}: unknown commit {m.group('sha')}")

    print(f"checked {checked} citations in {kb.relative_to(root).as_posix()}")
    for p in problems:
        print("  BROKEN " + p)
    if args.strict:
        print(f"  {uncited} prose lines without any citation")
    if problems or (args.strict and uncited):
        return 1
    print("  all citations resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
