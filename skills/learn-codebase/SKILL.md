---
name: learn-codebase
description: Build a verified, persistent knowledge base of an unfamiliar repository using only read-only tools (no permission prompts). Use this whenever the user wants to learn, understand, onboard to, map, explore, or "get up to speed" on a codebase, asks "how does this project work", "where do I start", "explain this repo", or opens a project they have never worked on. Also use it before large refactors, when a CLAUDE.md is missing or stale, or when the user complains about Claude re-exploring the same code every session.
argument-hint: [area or goal, e.g. "payments module" or "everything"]
allowed-tools: Read, Grep, Glob, Agent, Bash(python ${CLAUDE_SKILL_DIR}/scripts/*), Bash(git log *), Bash(git ls-files *), Bash(git shortlog *), Bash(git blame *), Bash(git show *), Bash(git rev-parse *), Bash(git branch *), Bash(git tag *), Bash(git describe *), Bash(git diff *), Bash(git status *), Write(./docs/codebase-knowledge/**), Edit(./docs/codebase-knowledge/**)
---

# Learn a codebase (read-only, no approval limbo)

You are building a **knowledge base** (KB) for this repository, the way a senior
engineer who has worked here for years would hold it in their head. The KB lives in
`docs/codebase-knowledge/` and must survive this session: next time, Claude or a human
starts from it instead of re-deriving everything.

Scope for this run: **$ARGUMENTS** (empty means the whole repository).

Answer the user in the language they are writing in. Write the KB files in that same
language, but keep identifiers, paths and quoted code verbatim.

## Why this workflow is shaped the way it is

Four decades of program-comprehension research (see [references/research-brief.md](references/research-brief.md))
converge on a few facts that this skill is built around:

- Comprehension is **~58% of developer time** (Xia et al. 2018) and seniors spend far less
  because they already hold the map. A persisted, verified KB emulates seniority.
- Experts read **top-down, hypothesis-first**, looking for *beacons* that confirm or refute
  a guess (Brooks 1983), and they chunk code into known *plans* and conventions
  (Soloway & Ehrlich 1984). Linear file-by-file reading is what novices do.
- The hardest, most-deferred questions are about **rationale ("why?") and behaviour
  under conditions**, and the only source is usually history or a missing colleague
  (Ko et al. 2007; LaToza & Myers 2010). Code alone does not answer them; git does.
- Readers who **trace interactions systematically** succeed at change tasks; as-needed
  skimmers miss non-local effects (Littman et al. 1986; Robillard et al. 2004).
- For LLM agents, the winning pattern is **skeleton first, then hierarchical
  localization** (repo -> dir -> file -> symbol), sub-agents with fresh context that return
  distilled summaries, and notes persisted outside the context window
  (Agentless 2024; RepoUnderstander 2024; Anthropic context-engineering guidance).
  Over-reading is the dominant token cost, and long contexts rot.
- Every claim needs **file:line evidence**, because fluent but unverified prose costs
  the reader more verification time than it saves (Mozannar et al. 2024).

## Zero-prompt contract

Everything here is read-only except writing into `docs/codebase-knowledge/`.
Read, Grep, Glob and the `Agent` tool never prompt. The sub-agents you spawn
(`cartographer`, `historian`, `tracer`, `verifier`) are restricted to read-only tools and
run with `permissionMode: dontAsk`, so a stray write attempt is denied instead of
hanging on an approval. Git read commands are in Claude Code's built-in read-only set.

If a `Write` to `docs/codebase-knowledge/` is denied (the project has not been trusted
yet), do not fight it: print the KB content in the chat under a heading per file and tell
the user to copy the project settings from the cartographer templates. Never fall back to
Bash to write files.

## Phases

Work through these in order. Each phase ends with something written to the KB, so a
session that is interrupted still leaves value behind. Keep your own context small: do
not paste whole files into your reasoning. Delegate breadth to sub-agents and keep only
their summaries.

### Phase 0: Reuse what exists (2 minutes)

1. If `docs/codebase-knowledge/INDEX.md` exists, read it and `90-questions.md`. Treat
   recorded facts as hypotheses to spot-check, not truths: the code may have moved.
   Then skip to the phase that the open questions point at.
2. Read `README*`, `CLAUDE.md`, `AGENTS.md`, `CONTRIBUTING*`, `docs/adr*/**`,
   `docs/architecture*` if present. These are *intended* architecture; the code is the
   *implemented* one. Note disagreements as questions.

### Phase 1: Skeleton and hypothesis (5 minutes)

Run the bundled inventory script. It is pure Python, read-only, and prints a budgeted
repo map (file tree, languages, size, entry-point beacons, top-referenced symbols via a
simple PageRank over the import graph, churn and ownership from git):

```
python ${CLAUDE_SKILL_DIR}/scripts/repo_skeleton.py . --budget 6000
```

Use `--area <path>` to restrict it when the scope is a sub-tree. If Python is not
available, ask the `cartographer` agent to produce the same sections by hand.

From the skeleton, write down **one architectural hypothesis** in a sentence
("Django monolith with Celery workers and a React SPA in /web") and the 3-5 **beacons**
you expect to find if it is true (settings module, URL router, task queue config, SPA
build entry). Confirm or refute each beacon with one Grep/Glob each. Revise the
hypothesis until the beacons agree with it.

Write `00-overview.md` now: hypothesis, beacons with evidence, how to build/run/test
(only what you verified in config files; mark anything untested as "unverified").

### Phase 2: Fan out to sub-agents (parallel)

Spawn these in **one message** so they run concurrently. Give each a hard budget
("at most 25 tool calls") and demand a summary under 1,500 words with `path:line`
evidence for every claim. Scale the number of cartographers to the repo: one per major
subsystem the skeleton revealed, at most six.

- `cartographer` x N: one per subsystem. Task: module responsibilities, public
  surface, key types, dependencies in/out, conventions observed, violations of those
  conventions, anything that looks like dead or legacy code.
- `historian` x 1: Task: why the code is shaped this way. Mine `git log`, `git shortlog`,
  ADRs, changelogs: founding commits, big rewrites, hotspots (high churn), ownership
  concentration (files with a single author), recent activity, and rationale found in
  commit messages or PR-style messages. Label inferred rationale as inferred.
- `cartographer` x 1 for cross-cutting concerns: config and env loading, logging,
  error handling, auth, feature flags, i18n, testing strategy and fixtures.

While they run, draft the glossary (Phase 3) from the skeleton's identifiers.

### Phase 3: Glossary of domain concepts (concept location)

Comprehension is concept location (Rajlich & Wilde 2002): the mapping from domain
vocabulary to code is the index everything else hangs on. Build `10-glossary.md`:

| Concept | Meaning in this project | Where it lives (path:line) | Synonyms / aliases in code |

Seed it from: README nouns, model/entity/table names, route names, UI strings, test
names, event/queue names. Expect your first search cue to fail (Ko et al. 2006): when
a domain word has no hits, grep for synonyms, abbreviations, and the plural/singular.
Flag concepts with **two names for one thing** or **one name for two things**; those
are the places newcomers get lost.

### Phase 4: Structural and behavioural maps

Merge the sub-agent summaries into two separate artefacts (Pennington 1987: readers
hold a *program model* and a *situation model*; both are needed):

- `20-architecture.md`: the structural map. Layers, modules, dependency direction,
  data stores, external services, boundaries. Keep the layout stable across runs so it
  can be diffed (Kuhn et al. 2010: a consistent map beats a pretty one).
- `30-flows/<name>.md`: one file per important end-to-end behaviour (a request, a job,
  a CLI command, startup). Write them as numbered steps, each with `path:line`. Trace
  callers and callees systematically rather than stopping at the first plausible
  function (Littman et al. 1986). Use the `tracer` agent for each flow, in parallel.
  Pick 2-4 flows for a first pass: the main entry point, the most-churned feature, and
  whatever `$ARGUMENTS` asks for.

### Phase 5: History, conventions, ownership

From the historian's report write:

- `40-history.md`: timeline of structural decisions, hotspots, candidate ADRs for
  rationale you reconstructed (clearly marked "inferred, not documented"), and the
  **truck-factor map**: which areas are known by one person. These are where the only
  knowledge is the code and the history, so they deserve the most careful notes.
- `50-conventions.md`: the project's local "plans": naming, layering rules, error
  handling idiom, test structure, commit style, how feature flags or migrations are
  done. Include observed violations; each one is either a bug or hidden intent.

### Phase 6: Question log and self-test

Open questions are the engine of comprehension (Letovsky 1987: question -> conjecture
-> verification). Maintain `90-questions.md` as a table:

| # | Question | Conjecture | Status (open / verified / refuted) | Evidence |

Seed it from [references/question-catalog.md](references/question-catalog.md), which
adapts Sillito et al.'s 44 question types and LaToza & Myers's hard questions. Close
what you can now; leave the rest open with your best conjecture so the next session
starts there.

Then self-test: pick five entries from the glossary and five steps from a flow, and
check, from the KB alone, whether you could locate each symbol. Spawn the `verifier`
agent on the KB directory: it checks that every `path:line` reference exists and that
the referenced line plausibly supports the claim. Fix or delete anything it flags.
A KB with a wrong line number is worse than no KB.

### Phase 7: Index and hand-off

Write `INDEX.md` (under 60 lines): one paragraph on what the system is, the
hypothesis, links to the other files, the five most important things a newcomer
would not guess from the code, and the top three open questions.

Finish with a short report to the user in the chat:
- what you now know with confidence (3-6 bullets),
- what is still uncertain and why,
- the list of KB files written,
- a suggestion to add `@docs/codebase-knowledge/INDEX.md` to `CLAUDE.md` so future
  sessions load the summary, and to run `/quiz-me` if they want to internalise it.

## Guard rails

- **Evidence or silence.** Never assert a symbol, path, API or call edge you have not
  seen in a tool result this session. If you are summarising a sub-agent, keep its
  evidence citations.
- **Budget the reading.** If you find yourself opening the 30th file by hand, stop and
  delegate to a sub-agent with a precise question. Read-ops are where agents burn
  their context.
- **Prefer symbol search over file reading.** Grep for `def name|class Name|function name`
  and read the window around the hit, not the whole file.
- **Verify intended vs implemented.** Docs lie by omission; say so in the KB when
  they do, with the evidence.
- **Keep it stable.** When updating an existing KB, edit in place and keep the file
  layout and section order so diffs show what actually changed in understanding.
- **Do not touch anything else.** No edits outside `docs/codebase-knowledge/`, no
  builds, no test runs, no network. If running something would answer a question,
  write the question down with the exact command the user could run.

See [references/kb-template.md](references/kb-template.md) for the exact file layout and
section headings, and [references/reading-strategies.md](references/reading-strategies.md)
when you are stuck on how to approach a confusing area.
