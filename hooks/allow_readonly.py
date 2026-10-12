#!/usr/bin/env python3
"""PreToolUse hook: auto-approve a strict safelist of read-only shell commands.

Why: Claude Code already runs many read-only commands without prompting, but
exploration sessions still hit prompts for things like `git log --follow`, `rg`,
`tree`, `tokei`, or the bundled skeleton script. Each prompt is an "approval limbo"
that breaks the learning flow. This hook says "allow" only for commands that cannot
modify the filesystem, the repo, or the network, and stays silent otherwise (so the
normal permission flow, including any deny rules, still applies).

Input (stdin): JSON with "tool_name" and "tool_input": {"command": "..."}.
Output (stdout): JSON permission decision, or nothing to express no opinion.

Design rules:
  * No compound operators, pipes, redirects, or substitutions are allowed through.
  * Only the first token (program) and, for git, the subcommand are matched.
  * Flags that make a read-only program write are rejected (find -delete/-exec,
    sed -i, sort -o, git log --output, python -c, etc.).
"""
from __future__ import annotations

import json
import re
import shlex
import sys

READONLY_PROGRAMS = {
    "ls", "cat", "head", "tail", "wc", "stat", "file", "du", "pwd", "echo", "tree",
    "grep", "egrep", "fgrep", "rg", "ag", "ack", "find", "fd", "which", "where", "type",
    "tokei", "cloc", "scc", "jq", "yq", "diff", "cmp", "md5sum", "sha256sum", "nl", "cut",
    "sort", "uniq", "tr", "awk", "basename", "dirname", "realpath", "readlink", "env",
    "printenv", "date", "uname", "hostname", "nproc", "column", "less", "more", "strings",
}
GIT_READONLY_SUBCOMMANDS = {
    "log", "show", "blame", "diff", "status", "ls-files", "ls-tree", "shortlog", "rev-parse",
    "rev-list", "branch", "tag", "describe", "cat-file", "grep", "remote", "reflog", "config",
    "worktree", "stash", "name-rev", "count-objects", "check-ignore", "merge-base", "for-each-ref",
}
# subcommands above that have mutating forms: require these to be absent
GIT_FORBIDDEN_ARGS = {
    "branch": {"-d", "-D", "-m", "-M", "-c", "-C", "--delete", "--move", "--copy", "-u", "--set-upstream-to", "--unset-upstream", "--edit-description"},
    "tag": {"-d", "-D", "--delete", "-a", "-s", "-f", "-m", "-F", "-e"},
    "remote": {"add", "remove", "rm", "rename", "set-url", "prune", "update", "set-head", "set-branches"},
    "config": {"--add", "--unset", "--unset-all", "--replace-all", "--edit", "-e", "--rename-section", "--remove-section"},
    "worktree": {"add", "remove", "prune", "move", "lock", "unlock", "repair"},
    "stash": {"push", "pop", "apply", "drop", "clear", "save", "branch", "create", "store"},
    "reflog": {"expire", "delete"},
    "diff": {"--output"}, "log": {"--output"}, "show": {"--output"},
}
FORBIDDEN_FLAGS = {
    "find": {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint", "-fprintf", "-fls"},
    "fd": {"-x", "--exec", "-X", "--exec-batch"},
    "sort": {"-o", "--output"},
    "sed": {"-i", "--in-place"},
    "awk": {"-f"},
    "rg": {"--pre"},
    "tree": {"-o"},
    "jq": {"--rawfile", "--slurpfile", "-f", "--from-file"},
    "less": {"-o", "-O", "--log-file"},
}
SHELL_META = re.compile(r"[|&;<>`$(){}\n]")  # also rejects $(..), `..`, {a,b}
SKILL_SCRIPT = re.compile(r"(?:^|[\\/])(repo_skeleton|kb_lint)\.py$")


def decision(allow: bool, reason: str) -> None:
    if not allow:
        return  # silence = no opinion; normal permission flow continues
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": reason,
        }
    }))


def is_readonly(command: str) -> tuple[bool, str]:
    cmd = command.strip()
    if not cmd or len(cmd) > 2000:
        return False, "empty or too long"
    if SHELL_META.search(cmd):
        return False, "shell metacharacter"
    try:
        argv = shlex.split(cmd, posix=True)
    except ValueError:
        return False, "unparseable"
    if not argv:
        return False, "empty"
    # strip harmless wrappers
    while argv and argv[0] in {"command", "builtin", "time", "nice", "nohup"}:
        argv = argv[1:]
    if not argv:
        return False, "empty"
    prog = argv[0].rsplit("/", 1)[-1].rsplit("\\", 1)[-1].lower()
    if prog.endswith(".exe"):
        prog = prog[:-4]
    args = argv[1:]
    if any(a.startswith("--") and "=" in a and a.split("=", 1)[0] in {"--output", "--out", "-o"} for a in args):
        return False, "output flag"

    if prog == "git":
        # skip global options like -C <path> and -c key=val
        i = 0
        while i < len(args) and args[i].startswith("-"):
            if args[i] in {"-C", "-c", "--git-dir", "--work-tree"}:
                i += 2
            else:
                i += 1
        if i >= len(args):
            return False, "no git subcommand"
        sub = args[i]
        rest = args[i + 1:]
        if sub not in GIT_READONLY_SUBCOMMANDS:
            return False, f"git {sub} is not read-only"
        if sub == "stash" and (not rest or rest[0] not in {"list", "show"}):
            return False, "git stash mutating form"
        if sub == "worktree" and (not rest or rest[0] != "list"):
            return False, "git worktree mutating form"
        if sub == "remote" and rest and rest[0] not in {"-v", "--verbose", "show", "get-url"}:
            return False, "git remote mutating form"
        if sub == "config" and rest and not any(r in {"--get", "--list", "-l", "--get-all", "--get-regexp"} for r in rest):
            return False, "git config may write"
        bad = GIT_FORBIDDEN_ARGS.get(sub, set())
        if any(r in bad or r.split("=", 1)[0] in bad for r in rest):
            return False, f"git {sub} with mutating flag"
        return True, f"read-only git {sub}"

    if prog in {"python", "python3", "py"}:
        # only the bundled read-only skill scripts, by file name, and no -c/-m
        script = next((a for a in args if not a.startswith("-")), None)
        if any(a in {"-c", "-m"} for a in args) or not script or not SKILL_SCRIPT.search(script):
            return False, "python only allowed for bundled skeleton/lint scripts"
        return True, "bundled read-only script"

    if prog in READONLY_PROGRAMS:
        bad = FORBIDDEN_FLAGS.get(prog, set())
        if any(a in bad or a.split("=", 1)[0] in bad for a in args):
            return False, f"{prog} with writing flag"
        return True, f"read-only {prog}"

    return False, "not on safelist"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        return 0
    if payload.get("tool_name") not in {"Bash", "PowerShell"}:
        return 0
    command = (payload.get("tool_input") or {}).get("command", "")
    ok, why = is_readonly(command)
    decision(ok, why)
    return 0


if __name__ == "__main__":
    sys.exit(main())
