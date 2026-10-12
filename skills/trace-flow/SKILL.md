---
name: trace-flow
description: Trace one behaviour end to end through the code (an HTTP request, a CLI command, a background job, startup, an event handler, a button click) and write it as a numbered path with file:line for every hop into docs/codebase-knowledge/30-flows/. Use whenever the user asks "what happens when...", "walk me through...", "how does a request to X get handled", or before changing code whose effects may be non-local. Read-only; never prompts.
argument-hint: <flow name or trigger, e.g. "POST /api/play/move" or "startup">
allowed-tools: Read, Grep, Glob, Agent, Write(./docs/codebase-knowledge/**), Edit(./docs/codebase-knowledge/**)
---

# Trace a flow

Flow to trace: **$ARGUMENTS**

Systematic tracing is what separates developers who succeed at change tasks from those
who miss non-local effects (Littman et al. 1986; Robillard et al. 2004). The product of
this skill is one file, `docs/codebase-knowledge/30-flows/<slug>.md`, in the format
described in `${CLAUDE_SKILL_DIR}/../learn-codebase/references/kb-template.md`.

## Procedure

1. If `docs/codebase-knowledge/30-flows/<slug>.md` already exists, read it: you are
   updating, not rewriting. Re-verify every cited line (code moves) and keep the
   numbering stable where the steps are unchanged.
2. Locate the trigger yourself with a few Greps (route table, command registry,
   event subscription, scheduler, `main`). Name it with `path:line`.
3. Spawn the `tracer` agent with the trigger location, the flow name, and a budget
   of ~30 tool calls. If the flow has an obvious fork (two implementations, a client
   and a server half), spawn two tracers in the same message, one per branch.
4. Merge the tracer output into the flow file. Add:
   - a 3-5 line plain-language summary at the top for a newcomer,
   - the "shared hops" section (functions on this path used by other flows), because
     those are the places where a change here breaks something else,
   - tests covering the flow, or "no tests found (grep for X, Y returned nothing)".
5. Add any new concept you met to `10-glossary.md`, and any unresolved dynamic
   dispatch to `90-questions.md` with the exact runtime check the user could do.
6. Report to the user: the numbered path in the chat (short form), the file written,
   and the top risk you noticed (a swallowed exception, a missing test, a hop that
   many flows share).

## Rules

- Every step has `path:line` seen this session. Dynamic hops you could not resolve
  statically are marked as such, never guessed.
- Do not stop at the first plausible function; follow the call to persistence, the
  response, or the repository boundary.
- Plumbing hops (middleware, decorators, base classes, DI) are steps, not noise.
- No edits outside `docs/codebase-knowledge/`. No running code.
- Answer in the user's language; keep identifiers verbatim.
