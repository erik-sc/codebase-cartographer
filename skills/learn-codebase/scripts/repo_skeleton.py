#!/usr/bin/env python3
"""repo_skeleton.py: read-only, dependency-free repository inventory.

Prints a budgeted Markdown "skeleton" of a repository, in the spirit of Aider's
repo map and Agentless's hierarchical localization:

  1. shape: languages, file counts, size, top-level directories
  2. beacons: files that strongly signal a framework / architecture (Brooks 1983)
  3. symbols: most-referenced definitions, ranked by a PageRank over the import graph
  4. history: churn hotspots, ownership concentration (truck factor), recent activity

It never writes anything and only runs read-only git commands.

Usage:
  python repo_skeleton.py [ROOT] [--area SUBPATH] [--budget 6000] [--no-git] [--json]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------- config

LANG_BY_EXT = {
    ".py": "Python", ".pyi": "Python", ".js": "JavaScript", ".mjs": "JavaScript",
    ".cjs": "JavaScript", ".jsx": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript",
    ".go": "Go", ".rs": "Rust", ".java": "Java", ".kt": "Kotlin", ".kts": "Kotlin",
    ".cs": "C#", ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".scala": "Scala",
    ".c": "C", ".h": "C/C++ header", ".cc": "C++", ".cpp": "C++", ".hpp": "C++",
    ".m": "Objective-C", ".mm": "Objective-C++", ".dart": "Dart", ".ex": "Elixir",
    ".exs": "Elixir", ".erl": "Erlang", ".hs": "Haskell", ".lua": "Lua", ".r": "R",
    ".sql": "SQL", ".sh": "Shell", ".bash": "Shell", ".ps1": "PowerShell",
    ".html": "HTML", ".vue": "Vue", ".svelte": "Svelte", ".css": "CSS", ".scss": "SCSS",
    ".md": "Markdown", ".yml": "YAML", ".yaml": "YAML", ".json": "JSON", ".toml": "TOML",
    ".xml": "XML", ".proto": "Protobuf", ".graphql": "GraphQL", ".tf": "Terraform",
}

CODE_EXTS = {e for e, l in LANG_BY_EXT.items()
             if l not in {"Markdown", "YAML", "JSON", "TOML", "XML", "HTML", "CSS", "SCSS", "SQL"}}

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "vendor", "dist", "build", "out", "target",
    ".next", ".nuxt", ".venv", "venv", "env", "__pycache__", ".mypy_cache", ".pytest_cache",
    ".tox", ".idea", ".vscode", "coverage", ".cache", "bin", "obj", ".gradle", ".dart_tool",
    "Pods", "DerivedData", ".terraform", "site-packages",
}

# (glob-ish filename pattern, what it signals)
BEACONS = [
    ("package.json", "Node/JS project manifest (scripts = how to run)"),
    ("pnpm-workspace.yaml", "pnpm monorepo"), ("lerna.json", "Lerna monorepo"),
    ("turbo.json", "Turborepo monorepo"), ("nx.json", "Nx monorepo"),
    ("tsconfig.json", "TypeScript"), ("next.config.*", "Next.js app"),
    ("nuxt.config.*", "Nuxt app"), ("vite.config.*", "Vite build"),
    ("angular.json", "Angular app"), ("svelte.config.*", "SvelteKit app"),
    ("remix.config.*", "Remix app"), ("app.json", "Expo/React Native (maybe)"),
    ("pyproject.toml", "Python project (PEP 621/Poetry)"), ("setup.py", "Python package"),
    ("requirements*.txt", "Python deps"), ("Pipfile", "Pipenv"),
    ("manage.py", "Django project"), ("*/settings.py", "Django settings"),
    ("*/urls.py", "Django URL router"), ("*/celery.py", "Celery workers"),
    ("alembic.ini", "Alembic migrations (SQLAlchemy)"), ("*/wsgi.py", "WSGI entry"),
    ("*/asgi.py", "ASGI entry"), ("go.mod", "Go module"), ("main.go", "Go entry point"),
    ("Cargo.toml", "Rust crate"), ("pom.xml", "Maven (Java)"), ("build.gradle*", "Gradle"),
    ("settings.gradle*", "Gradle multi-project"), ("*.csproj", ".NET project"),
    ("*.sln", ".NET solution"), ("Program.cs", ".NET entry point"), ("Startup.cs", "ASP.NET startup"),
    ("Gemfile", "Ruby/Bundler"), ("config/routes.rb", "Rails router"),
    ("composer.json", "PHP/Composer"), ("artisan", "Laravel"), ("mix.exs", "Elixir/Mix"),
    ("pubspec.yaml", "Dart/Flutter"), ("Package.swift", "SwiftPM"),
    ("Dockerfile*", "Container build"), ("docker-compose*.y*ml", "Compose stack (services = architecture!)"),
    ("compose*.y*ml", "Compose stack"), ("Makefile", "Make targets (how to build/run)"),
    ("justfile", "just recipes"), ("Taskfile.y*ml", "Task runner"),
    (".github/workflows/*.y*ml", "GitHub Actions CI (how it is tested)"),
    (".gitlab-ci.yml", "GitLab CI"), ("Jenkinsfile", "Jenkins CI"),
    ("serverless.y*ml", "Serverless framework"), ("template.y*ml", "AWS SAM (maybe)"),
    ("*.tf", "Terraform infra"), ("helm/*", "Helm charts"), ("k8s/*", "Kubernetes manifests"),
    ("prisma/schema.prisma", "Prisma schema (data model)"), ("*/migrations/*", "DB migrations (data model history)"),
    ("openapi*.y*ml", "OpenAPI spec"), ("openapi*.json", "OpenAPI spec"), ("*.proto", "gRPC/protobuf contracts"),
    ("schema.graphql", "GraphQL schema"), ("CLAUDE.md", "Claude Code instructions"),
    ("AGENTS.md", "Agent instructions"), ("docs/adr/*", "Architecture Decision Records"),
    ("docs/decisions/*", "Architecture Decision Records"), ("CODEOWNERS", "Ownership map"),
    (".env.example", "Env contract"), ("README*", "README"), ("CONTRIBUTING*", "Contribution rules"),
]

# Definition regexes per language family: (compiled regex, group index of the name)
DEF_PATTERNS = {
    "Python": [re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_]\w*)"), re.compile(r"^\s*class\s+([A-Za-z_]\w*)")],
    "JavaScript": [
        re.compile(r"^\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)"),
        re.compile(r"^\s*(?:export\s+)?class\s+([A-Za-z_$][\w$]*)"),
        re.compile(r"^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>"),
    ],
    "Go": [re.compile(r"^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)"), re.compile(r"^type\s+([A-Za-z_]\w*)\s+(?:struct|interface)")],
    "Rust": [re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?fn\s+([A-Za-z_]\w*)"),
             re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait)\s+([A-Za-z_]\w*)")],
    "Java": [re.compile(r"^\s*(?:public|protected|private)?\s*(?:static\s+)?(?:final\s+)?(?:class|interface|enum|record)\s+([A-Za-z_]\w*)"),
             re.compile(r"^\s*(?:public|protected|private)\s+(?:static\s+)?(?:final\s+)?[\w<>\[\], ]+\s+([a-z]\w*)\s*\(")],
    "C#": [re.compile(r"^\s*(?:public|internal|private|protected)?\s*(?:static\s+|sealed\s+|abstract\s+|partial\s+)*(?:class|interface|record|struct|enum)\s+([A-Za-z_]\w*)"),
           re.compile(r"^\s*(?:public|internal|private|protected)\s+(?:static\s+|async\s+|virtual\s+|override\s+)*[\w<>\[\], ?]+\s+([A-Z]\w*)\s*\(")],
    "Ruby": [re.compile(r"^\s*def\s+(?:self\.)?([A-Za-z_]\w*[?!=]?)"), re.compile(r"^\s*(?:class|module)\s+([A-Z]\w*)")],
    "PHP": [re.compile(r"^\s*(?:public|private|protected)?\s*(?:static\s+)?function\s+([A-Za-z_]\w*)"), re.compile(r"^\s*(?:abstract\s+|final\s+)?(?:class|interface|trait)\s+([A-Za-z_]\w*)")],
    "Kotlin": [re.compile(r"^\s*(?:\w+\s+)*fun\s+(?:<[^>]+>\s*)?(?:[\w.]+\.)?([A-Za-z_]\w*)"), re.compile(r"^\s*(?:\w+\s+)*(?:class|interface|object)\s+([A-Za-z_]\w*)")],
    "Swift": [re.compile(r"^\s*(?:\w+\s+)*func\s+([A-Za-z_]\w*)"), re.compile(r"^\s*(?:\w+\s+)*(?:class|struct|enum|protocol)\s+([A-Za-z_]\w*)")],
    "C++": [re.compile(r"^\s*(?:class|struct)\s+([A-Za-z_]\w*)")],
    "C": [re.compile(r"^[A-Za-z_][\w\s\*]*\s\*?([A-Za-z_]\w*)\s*\([^;]*\)\s*\{?\s*$")],
    "Elixir": [re.compile(r"^\s*defmodule\s+([\w.]+)"), re.compile(r"^\s*defp?\s+([a-z_]\w*[?!]?)")],
    "Dart": [re.compile(r"^\s*(?:abstract\s+)?class\s+([A-Za-z_]\w*)")],
    "Scala": [re.compile(r"^\s*(?:\w+\s+)*(?:class|object|trait)\s+([A-Za-z_]\w*)"), re.compile(r"^\s*(?:\w+\s+)*def\s+([A-Za-z_]\w*)")],
}
DEF_PATTERNS["TypeScript"] = DEF_PATTERNS["JavaScript"] + [
    re.compile(r"^\s*(?:export\s+)?(?:interface|enum)\s+([A-Za-z_$][\w$]*)"),
    re.compile(r"^\s*(?:export\s+)?type\s+([A-Za-z_$][\w$]*)\s*(?:<[^>]*>)?\s*=")]

IMPORT_PATTERNS = [
    re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))"),                    # Python
    re.compile(r"^\s*import\s+(?:[^'\"]*?from\s+)?['\"]([^'\"]+)['\"]"),                  # JS/TS
    re.compile(r"^\s*(?:const|let|var)\s+.*?=\s*require\(\s*['\"]([^'\"]+)['\"]"),        # CJS
    re.compile(r"^\s*export\s+.*?from\s+['\"]([^'\"]+)['\"]"),                           # re-export
    re.compile(r"^\s*(?:use|mod)\s+([\w:]+)"),                                            # Rust
    re.compile(r"^\s*import\s+(?:static\s+)?([\w.]+)"),                                   # Java/Kotlin/Scala/Go-ish
    re.compile(r"^\s*using\s+([\w.]+)\s*;"),                                              # C#
    re.compile(r"^\s*require(?:_relative)?\s+['\"]([^'\"]+)['\"]"),                       # Ruby
    re.compile(r"^\s*#include\s+[\"<]([^\">]+)[\">]"),                                    # C/C++
    re.compile(r"^\s*\"([\w./-]+)\"\s*$"),                                                # Go import block lines
]

# ---------------------------------------------------------------- helpers


def run_git(root: Path, *args: str, timeout: int = 60) -> str | None:
    try:
        out = subprocess.run(["git", "-C", str(root), "-c", "core.quotepath=off", *args],
                             capture_output=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if out.returncode != 0:
        return None
    raw = out.stdout
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def list_files(root: Path, area: str | None) -> list[Path]:
    """Prefer `git ls-files` (respects .gitignore); fall back to os.walk."""
    files: list[Path] = []
    tracked = run_git(root, "ls-files", "-z", "--", area or ".")
    if tracked is not None:
        for rel in tracked.split("\0"):
            if not rel:
                continue
            p = root / rel
            parts = set(Path(rel).parts[:-1])
            if parts & SKIP_DIRS:
                continue
            if p.is_file():
                files.append(p)
        if files:
            return files
        # empty index (fresh repo with no commits/adds): fall through to os.walk
    base = root / area if area else root
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for fn in filenames:
            files.append(Path(dirpath) / fn)
    return files


def rel(root: Path, p: Path) -> str:
    return p.relative_to(root).as_posix()


def glob_match(pattern: str, relpath: str) -> bool:
    from fnmatch import fnmatch
    name = relpath.rsplit("/", 1)[-1]
    if "/" in pattern:
        return fnmatch(relpath, pattern) or fnmatch(relpath, "*/" + pattern)
    return fnmatch(name, pattern)


def read_text(p: Path, limit: int = 400_000) -> str:
    try:
        if p.stat().st_size > limit:
            return ""
        return p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def module_key(relpath: str) -> str:
    """Normalise a file path to a module-ish key used to resolve imports."""
    p = relpath
    for ext in sorted(CODE_EXTS, key=len, reverse=True):
        if p.endswith(ext):
            p = p[: -len(ext)]
            break
    for suffix in ("/index", "/__init__", "/mod"):
        if p.endswith(suffix):
            p = p[: -len(suffix)]
    return p


def package_map(root: Path, rels: list[str]) -> dict[str, str]:
    """Map workspace package names (from package.json "name") to their directory."""
    pk: dict[str, str] = {}
    for r in rels:
        if r.rsplit("/", 1)[-1] != "package.json":
            continue
        try:
            data = json.loads(read_text(root / r, 200_000) or "{}")
        except ValueError:
            continue
        name = data.get("name") if isinstance(data, dict) else None
        if isinstance(name, str) and name:
            d = r[: -len("package.json")].rstrip("/")
            pk[name] = d
    return pk


def resolve_import(spec: str, importer: str, keys: dict[str, str],
                   packages: dict[str, str] | None = None) -> str | None:
    """Best-effort mapping of an import string to a file in the repo."""
    spec = spec.strip()
    cand: list[str] = []
    packages = packages or {}
    # workspace package: "@scope/pkg" or "@scope/pkg/sub"
    for name, d in packages.items():
        if spec == name or spec.startswith(name + "/"):
            tail = spec[len(name):].lstrip("/")
            base = f"{d}/{tail}" if tail else d
            cand += [base, base + "/src", base + "/src/index", base + "/index", base + "/lib"]
    # path alias like "@/lib/x" or "~/lib/x": try every ancestor of the importer with /src
    m_alias = re.match(r"^[@~]/(.+)$", spec)
    if m_alias:
        anc = Path(importer).parent
        while True:
            cand += [(anc / "src" / m_alias.group(1)).as_posix(), (anc / m_alias.group(1)).as_posix()]
            if anc == Path("."):
                break
            anc = anc.parent
    if spec.startswith("."):
        base = Path(importer).parent
        parts = spec.split("/") if "/" in spec else [spec]
        if "/" in spec:
            cand.append((base / spec).as_posix())
        else:  # python relative: from .x.y import z
            dots = len(spec) - len(spec.lstrip("."))
            up = base
            for _ in range(dots - 1):
                up = up.parent
            tail = spec.lstrip(".").replace(".", "/")
            cand.append((up / tail).as_posix() if tail else up.as_posix())
    else:
        dotted = spec.replace("::", "/").replace(".", "/")
        cand += [spec, dotted, "src/" + dotted, "lib/" + dotted, "app/" + dotted]
        # strip alias prefixes like @/, ~/, @app/
        m = re.match(r"^[@~][\w-]*/(.+)$", spec)
        if m:
            cand += [m.group(1), "src/" + m.group(1)]
    for c in cand:
        c = os.path.normpath(c).replace("\\", "/")
        if c in keys:
            return keys[c]
        # progressively shorten dotted paths (pkg.sub.name -> pkg/sub)
        while "/" in c:
            c = c.rsplit("/", 1)[0]
            if c in keys:
                return keys[c]
    return None


def pagerank(nodes: list[str], edges: dict[str, set[str]], iters: int = 30, d: float = 0.85) -> dict[str, float]:
    n = len(nodes)
    if n == 0:
        return {}
    rank = {k: 1.0 / n for k in nodes}
    incoming: dict[str, list[str]] = collections.defaultdict(list)
    for src, dsts in edges.items():
        for dst in dsts:
            incoming[dst].append(src)
    outdeg = {k: len(edges.get(k, ())) for k in nodes}
    for _ in range(iters):
        new = {}
        dangling = sum(rank[k] for k in nodes if outdeg[k] == 0)
        for k in nodes:
            s = sum(rank[src] / outdeg[src] for src in incoming.get(k, ()) if outdeg[src])
            new[k] = (1 - d) / n + d * (s + dangling / n)
        rank = new
    return rank


# ---------------------------------------------------------------- analysis


def analyse(root: Path, area: str | None, use_git: bool) -> dict:
    files = list_files(root, area)
    rels = [rel(root, f) for f in files]

    # 1. shape
    lang_counts: collections.Counter = collections.Counter()
    lang_bytes: collections.Counter = collections.Counter()
    top_dirs: collections.Counter = collections.Counter()
    total_bytes = 0
    for f, r in zip(files, rels):
        ext = f.suffix.lower()
        lang = LANG_BY_EXT.get(ext, "other")
        try:
            size = f.stat().st_size
        except OSError:
            size = 0
        total_bytes += size
        lang_counts[lang] += 1
        lang_bytes[lang] += size
        top = r.split("/", 1)[0] if "/" in r else "(root)"
        top_dirs[top] += 1

    # 2. beacons
    beacons: list[tuple[str, str]] = []
    seen_patterns: collections.Counter = collections.Counter()
    for r in rels:
        for pat, meaning in BEACONS:
            if seen_patterns[pat] >= 3:
                continue
            if glob_match(pat, r):
                beacons.append((r, meaning))
                seen_patterns[pat] += 1
                break

    # 3. symbols + import graph
    code_files = [(f, r) for f, r in zip(files, rels) if f.suffix.lower() in CODE_EXTS]
    keys = {module_key(r): r for _, r in code_files}
    packages = package_map(root, rels)
    edges: dict[str, set[str]] = collections.defaultdict(set)
    defs: dict[str, list[tuple[str, int]]] = {}
    loc: dict[str, int] = {}
    for f, r in code_files:
        text = read_text(f)
        if not text:
            continue
        lines = text.splitlines()
        loc[r] = len(lines)
        lang = LANG_BY_EXT.get(f.suffix.lower(), "")
        pats = DEF_PATTERNS.get(lang, [])
        found: list[tuple[str, int]] = []
        for i, line in enumerate(lines, 1):
            for p in pats:
                m = p.match(line)
                if m:
                    found.append((m.group(1), i))
                    break
            for ip in IMPORT_PATTERNS:
                m = ip.match(line)
                if m:
                    spec = next((g for g in m.groups() if g), None)
                    if spec:
                        target = resolve_import(spec, r, keys, packages)
                        if target and target != r:
                            edges[r].add(target)
                    break
        defs[r] = found

    nodes = [r for _, r in code_files]
    rank = pagerank(nodes, edges)
    indeg: collections.Counter = collections.Counter()
    for src, dsts in edges.items():
        for dst in dsts:
            indeg[dst] += 1

    # 4. history
    history: dict = {}
    if use_git:
        log = run_git(root, "log", "--since=2 years ago", "--name-only", "--pretty=format:%H%x09%an%x09%as", "--", area or ".", timeout=120)
        if log is not None:
            churn: collections.Counter = collections.Counter()
            authors_by_file: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
            commits = 0
            authors: collections.Counter = collections.Counter()
            last_dates: list[str] = []
            cur_author = None
            for line in log.splitlines():
                if "\t" in line and re.match(r"^[0-9a-f]{7,40}\t", line):
                    commits += 1
                    _, cur_author, date = line.split("\t", 2)
                    authors[cur_author] += 1
                    last_dates.append(date)
                elif line.strip() and cur_author:
                    churn[line.strip()] += 1
                    authors_by_file[line.strip()][cur_author] += 1
            single_owner = []
            for fpath, cnt in authors_by_file.items():
                if sum(cnt.values()) >= 3 and len(cnt) == 1 and fpath in loc:
                    single_owner.append((fpath, next(iter(cnt))))
            history = {
                "commits_2y": commits,
                "authors": authors.most_common(8),
                "first_date": min(last_dates) if last_dates else None,
                "last_date": max(last_dates) if last_dates else None,
                "hotspots": [(f, c) for f, c in churn.most_common(15) if f in loc or f in rels],
                "single_owner_files": sorted(single_owner, key=lambda x: -churn[x[0]])[:15],
                "truck_factor_note": "files with >=3 commits and exactly one author in the last 2 years",
            }
        first = run_git(root, "log", "--reverse", "--pretty=format:%as %s", "--max-count=1")
        if first:
            history["first_commit"] = first.strip().splitlines()[0][:120]
        tags = run_git(root, "tag", "--sort=-creatordate")
        if tags:
            history["recent_tags"] = tags.split()[:5]

    return {
        "root": str(root), "area": area, "file_count": len(files), "total_bytes": total_bytes,
        "languages": [(l, c, lang_bytes[l]) for l, c in lang_counts.most_common(10)],
        "top_dirs": top_dirs.most_common(20), "beacons": beacons,
        "ranked_files": sorted(nodes, key=lambda k: -rank.get(k, 0)), "rank": rank, "indeg": indeg,
        "defs": defs, "loc": loc, "edges": {k: sorted(v) for k, v in edges.items()}, "history": history,
    }


# ---------------------------------------------------------------- rendering


def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def render(a: dict, budget_tokens: int) -> str:
    out: list[str] = []
    w = out.append
    w(f"# Repository skeleton: {a['root']}" + (f" (area: {a['area']})" if a["area"] else ""))
    w("")
    w("## 1. Shape")
    w(f"- Files: {a['file_count']}  Size: {human(a['total_bytes'])}")
    w("- Languages (files, bytes): " + ", ".join(f"{l} {c} ({human(b)})" for l, c, b in a["languages"]))
    w("- Top-level dirs (file count): " + ", ".join(f"{d} {c}" for d, c in a["top_dirs"]))
    w("")
    w("## 2. Beacons (what the repo claims to be; verify each)")
    if a["beacons"]:
        for path, meaning in a["beacons"][:40]:
            w(f"- `{path}`: {meaning}")
    else:
        w("- none recognised; fall back to bottom-up reading of the top-level dirs")
    w("")
    w("## 3. Most central files (PageRank over resolved imports) and their definitions")
    w("Read these first: they are the ones everything else depends on.")
    w("")
    w("| file | in-degree | LOC | top definitions (name:line) |")
    w("|---|---|---|---|")
    approx_tokens = sum(len(s) for s in out) // 4
    for path in a["ranked_files"]:
        if approx_tokens > budget_tokens * 0.75:
            w(f"| ... | | | truncated at budget; rerun with --area or --budget |")
            break
        d = a["defs"].get(path, [])
        names = ", ".join(f"{n}:{ln}" for n, ln in d[:8]) + (f" (+{len(d) - 8})" if len(d) > 8 else "")
        row = f"| `{path}` | {a['indeg'].get(path, 0)} | {a['loc'].get(path, 0)} | {names} |"
        w(row)
        approx_tokens += len(row) // 4
    w("")
    h = a["history"]
    w("## 4. History (git)")
    if not h:
        w("- git history unavailable (not a repo, git missing, or --no-git)")
    else:
        if h.get("first_commit"):
            w(f"- First commit: {h['first_commit']}")
        w(f"- Commits in last 2 years: {h.get('commits_2y', 0)}  span {h.get('first_date')} .. {h.get('last_date')}")
        if h.get("recent_tags"):
            w("- Recent tags: " + ", ".join(h["recent_tags"]))
        if h.get("authors"):
            w("- Top authors (commits): " + ", ".join(f"{n} {c}" for n, c in h["authors"]))
        if h.get("hotspots"):
            w("- Churn hotspots (commits touching file): " + ", ".join(f"`{f}` {c}" for f, c in h["hotspots"]))
        if h.get("single_owner_files"):
            w(f"- Single-owner files ({h['truck_factor_note']}): "
              + ", ".join(f"`{f}` ({au})" for f, au in h["single_owner_files"]))
    w("")
    w("## 5. Suggested next moves")
    w("- State one architectural hypothesis from sections 1-2 and name 3-5 beacons it predicts.")
    w("- Open the top 5 files of section 3 only around their definitions (grep the name, read a 40-line window).")
    w("- For every hotspot or single-owner file in section 4, plan a `git log --follow` pass; that is where the rationale lives.")
    return "\n".join(out)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=".")
    ap.add_argument("--area", help="sub-path to restrict the inventory to")
    ap.add_argument("--budget", type=int, default=6000, help="approximate token budget for the output")
    ap.add_argument("--no-git", action="store_true")
    ap.add_argument("--json", action="store_true", help="emit raw analysis as JSON instead of Markdown")
    args = ap.parse_args(argv)
    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"not a directory: {root}", file=sys.stderr)
        return 2
    a = analyse(root, args.area, not args.no_git)
    if args.json:
        a = dict(a)
        a["rank"] = {k: round(v, 6) for k, v in a["rank"].items()}
        a["indeg"] = dict(a["indeg"])
        print(json.dumps(a, indent=1, default=str))
    else:
        print(render(a, args.budget))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
