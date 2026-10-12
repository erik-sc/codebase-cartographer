---
name: ask-codebase
description: Answer a specific question about this repository ("where is X handled", "why does Y exist", "what calls Z", "what happens when...") with file:line evidence, using the knowledge base in docs/codebase-knowledge first and read-only exploration second. Use whenever the user asks a how/where/why/what-if question about existing code rather than asking for a change. Never prompts for permissions.
argument-hint: <question>
allowed-tools: Read, Grep, Glob, Agent, Bash(git log *), Bash(git blame *), Bash(git show *), Bash(git shortlog *), Edit(./docs/codebase-knowledge/**), Write(./docs/codebase-knowledge/**)
---

# Ask the codebase

Question: **$ARGUMENTS**

Answer in the user's language. Every factual statement carries a `path:line` or
`commit sha` you saw this session. If you cannot find evidence, say "I could not
verify this" rather than producing fluent guesswork: unverified prose costs the reader
more than it saves.

## Procedure: question -> conjecture -> verification (Letovsky 1987)

1. **Classify the question** using the catalog in
   `${CLAUDE_SKILL_DIR}/../learn-codebase/references/question-catalog.md`:
   focus-point (where is X), building-on (who calls / what calls), subgraph (what
   happens when), cross-subgraph (how do A and B relate / impact), or history (why).
   The class decides the tools: history questions go to `git log -S` and the
   `historian` agent; subgraph questions go to the `tracer` agent; the rest is Grep.
2. **Check the KB first.** If `docs/codebase-knowledge/INDEX.md` exists, read it and the
   one or two files the question maps to (glossary for "where", flows for "what happens",
   history for "why", questions log for everything: it may already be an open question
   with a conjecture). Treat KB facts as hypotheses; re-verify the specific lines you
   are about to cite, because code moves.
3. **State a conjecture** in one line before searching. It focuses the search and
   makes it obvious when you were wrong.
4. **Verify with the cheapest tool.** Grep for the symbol or concept and its
   synonyms; read 40-80 line windows around hits, not whole files. Expect the first
   cue to fail (Ko et al. 2006); try the UI string, the test name, the log message,
   the plural. For "who calls X", grep the name across the repo and list call sites.
   For "why", `git log -S'<symbol>' --oneline` then `git show <sha> --stat` for the
   two or three commits that matter.
5. **Delegate when it gets wide.** If the answer needs more than ~10 tool calls or
   spans more than ~8 files, spawn `tracer` (behaviour) or `historian` (rationale) or
   `cartographer` (structure) with the exact question and a budget, and synthesise
   their evidence-backed summary. They are read-only and never prompt.
6. **Answer**, in this shape:

```
**Answer:** <one or two sentences>

**Evidence**
- path:line — what this line shows
- commit sha — what the message says (quote briefly)

**How it fits** (optional, 2-4 bullets): the surrounding flow or module, pointing to KB files

**Confidence:** high | medium | low — and what would raise it (a test to run, a person to ask)
```

7. **Feed the KB.** If `docs/codebase-knowledge/` exists and you learned something
   durable (a new glossary term, a flow step, a rationale), append it to the right file
   and add a row to `90-questions.md` with status "verified" and the evidence. Keep
   section order and formatting stable. If the KB does not exist, suggest running
   `/learn-codebase` once; do not create partial KB files.

## Do not

- Do not run the code, tests or builds; write the command the user could run instead.
- Do not edit anything outside `docs/codebase-knowledge/`.
- Do not answer from general knowledge of a framework when the repo could contradict
  it; check how *this* repo does it.
