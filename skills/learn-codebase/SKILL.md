---
name: learn-codebase
description: Build a verified, persistent knowledge base of an unfamiliar repository using only read-only tools (no permission prompts). Use this whenever the user wants to learn, understand, onboard to, map, explore, or "get up to speed" on a codebase, asks "how does this project work", "where do I start", "explain this repo", or opens a project they have never worked on. Also use it before large refactors, when a CLAUDE.md is missing or stale, or when the user complains about Claude re-exploring the same code every session.
argument-hint: [area or goal, e.g. "payments module" or "everything"]
allowed-tools: Read, Grep, Glob, Agent, Bash(python ${CLAUDE_SKILL_DIR}/scripts/*), Bash(git log *), Bash(git ls-files *), Bash(git shortlog *), Bash(git blame *), Bash(git show *), Bash(git rev-parse *), Bash(git branch *), Bash(git tag *), Bash(git describe *), Bash(git diff *), Bash(git status *), Write(./docs/codebase-knowledge/**), Edit(./docs/codebase-knowledge/**)
---

# Learn a codebase (read-only, no approval limbo)

Build the **knowledge base** (KB) a senior engineer would hold in their head for this
repository, and persist it in `<repo root>/docs/codebase-knowledge/` so the next session
(Claude's or a human's) starts from it instead of re-deriving it.

Scope for this run: **$ARGUMENTS** (empty means the whole repository).

The design follows the program-comprehension literature (hypothesis-first reading,
concept location, systematic tracing, rationale from history, evidence on every claim);
read [references/research-brief.md](references/research-brief.md) only if you want
the reasons. Everything below is read-only except writes inside `docs/codebase-knowledge/`;
the sub-agents have only Read/Grep/Glob (plus read-only git for `historian`/`verifier`)
and run with `permissionMode: dontAsk`, so nothing here waits on an approval. If a Write
to the KB is denied, print the files in chat under one heading each and point the user
to `templates/settings.project.json`; never write via Bash.

Answer the user in their language and write the KB in it, keeping identifiers, paths and
quoted code verbatim.

## Non-negotiable rules

- **Evidence or silence.** Every factual sentence cites `path:line`, `path:a-b` or
  `commit sha` that you or a sub-agent saw this session. Unverified expectations are
  marked `(unverified)`. A wrong line number is worse than no KB.
- **Full paths everywhere, including inside tables.** Abbreviating
  `apps/web/src/server/http.ts:87` to `http.ts:87` is the single most common way to
  break the linter. Paths are relative to the repo root, no `./`.
- **When two sub-agents disagree, grep it yourself.** Do not average or hedge.
- **Budget your own reading.** Delegate anything wider than ~10 tool calls or ~8 files.
  Grep for the symbol and read a 40-80 line window; do not open whole files.
- **Keep the KB layout stable** (file names, section order) so `git diff` on it shows
  how understanding changed. When updating an existing KB, edit in place.
- **No edits outside `docs/codebase-knowledge/`, no builds, tests or network.** If
  running something would answer a question, log the exact command in `90-questions.md`.

## Phase 0: Reuse what exists

If `docs/codebase-knowledge/INDEX.md` exists, read it and `90-questions.md`; treat
recorded facts as hypotheses to spot-check and jump to whatever the open questions
point at. Read `README*`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING*`, `docs/adr*/**`
if present: that is the *intended* architecture; the code is the *implemented* one,
and disagreements become questions.

## Phase 1: Skeleton, hypothesis, beacons

Run the inventory script, passing the repo root explicitly (the cwd may be elsewhere):

```
python ${CLAUDE_SKILL_DIR}/scripts/repo_skeleton.py <repo root> --budget 6000
```

Add `--area <subpath>` when the scope is a sub-tree. If Python is missing, ask a
`cartographer` to produce the same sections (shape, beacons, central files, history).

From the skeleton write one architectural hypothesis in a sentence and the 3-5
beacons it predicts (router, settings module, queue config, build entry...), plus one
beacon that would *refute* it. Confirm each with one Grep/Glob; revise until they agree.

Write `00-overview.md` now (template in [references/kb-template.md](references/kb-template.md)):
hypothesis, beacon table with evidence, build/run/test facts taken only from config
files (`package.json` scripts, Makefile, CI workflow), each marked "verified in <path>"
or "(unverified)". Entry points come from the skeleton's beacons and the top-ranked files.

## Phase 2: One fan-out, in a single message

Spawn every sub-agent at once; the skeleton already gives you the subsystems and the
entry points, so there is no reason to wait for cartographers before tracing. Give each
a hard budget ("at most 25 tool calls"), the repo root as an absolute path, and the
rule "full paths, `path:line` on every claim, report under 1,500 words".

- `cartographer` x one per major subsystem (at most six) and one for cross-cutting
  concerns (config/env, logging, errors, auth, flags, test fixtures). Ask for:
  responsibility, public surface, dependencies in/out, conventions, violations,
  probable dead code.
- `tracer` x 2-4 flows: the main entry point, the most-churned feature from the
  skeleton, and whatever `$ARGUMENTS` names. Give each the trigger's `path:line`.
- `historian` x 1 **only if the skeleton shows more than ~50 commits or more than one
  author**. Otherwise do history inline with `git log --oneline`, `git shortlog -sn`
  and `git show <sha> --stat` for the handful of commits that matter. Ask for:
  timeline of structural decisions, hotspots, ownership concentration, documented vs
  inferred rationale, abandoned approaches.

While they run, draft the glossary (Phase 3) from the identifiers in the skeleton.

## Phase 3: Glossary (concept location)

`10-glossary.md`: `| Concept | Meaning here | Where (full path:line) | Aliases in code | Notes |`.
Seed from README nouns, entity/table names, route names, UI strings, test names,
event/queue names. When a domain word has no hits, grep synonyms, abbreviations,
singular/plural before concluding it is absent. Flag two-names-one-thing and
one-name-two-things under "Naming hazards": that is where newcomers get lost.

## Phase 4: Merge into the KB

From the sub-agent reports write, in this order:

- `20-architecture.md`: layers, dependency direction, module table (responsibility,
  public surface, depends on / depended on by, evidence), data stores and external
  services, boundaries, and "where implemented differs from documented".
- `30-flows/<slug>.md`, one per traced flow: numbered steps with `path:line` for the
  call site and the definition, shared hops with caller counts, state touched, failure
  handling, tests found (or the greps that found none).
- `40-history.md`: timeline, hotspots (use the skeleton's window; say "repo is N days
  old" when churn is meaningless), ownership concentration, candidate ADRs marked
  "inferred, not documented".
- `50-conventions.md`: naming, layering rules, error handling, testing, config/flags,
  and an "observed violations" table with a bug-or-intent verdict per row.
- `90-questions.md`: `| # | Question | Conjecture | Status | Evidence |`. Status is
  `open`, `verified (code)`, `verified (documented)` or `refuted`. Seed from
  [references/question-catalog.md](references/question-catalog.md); close what you
  can, leave the rest with your best conjecture.

## Phase 5: Verify

1. Run the linter and fix everything it reports, then re-run until clean:
   ```
   python ${CLAUDE_SKILL_DIR}/scripts/kb_lint.py <repo root>
   ```
2. List the 8-12 load-bearing claims (architecture statements, bug or violation
   verdicts, "there is no X", the first three hops of each flow) and hand exactly that
   list to one `verifier` agent with the KB path. It checks whether the cited lines
   actually support each claim, which the linter cannot. Fix or delete what it flags.

## Phase 6: Index and hand-off

Write `INDEX.md` (under 60 lines): one paragraph on what the system is, the verified
hypothesis, links to every KB file, the five things a newcomer would not guess from the
code (each with evidence), and the top three open questions.

Report to the user: 3-6 bullets of what you now know with confidence, what is still
uncertain and why, the KB files written, and two suggestions: add
`@docs/codebase-knowledge/INDEX.md` to `CLAUDE.md`, and run `/quiz-me` to internalise it.

See [references/reading-strategies.md](references/reading-strategies.md) when an area
resists understanding.
