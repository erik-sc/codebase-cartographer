---
name: quiz-me
description: Help the human actually learn and retain a codebase instead of delegating understanding to Claude. Runs retrieval-practice quizzes, explain-back checks and predict-then-verify exercises generated from docs/codebase-knowledge and the code itself, graded against file:line evidence. Use when the user wants to internalise, study, memorise, onboard themselves, prepare to own an area, or says "test me", "quiz me", "make sure I understand this". Read-only; never prompts.
argument-hint: [area or KB file, e.g. "payments flow" or "glossary"]
allowed-tools: Read, Grep, Glob, Edit(./docs/codebase-knowledge/**), Write(./docs/codebase-knowledge/**)
---

# Quiz me on the codebase

Scope: **$ARGUMENTS** (empty: pick from the whole knowledge base, weighted toward
areas the question log marks as important or recently learned).

## Why this exists

Explaining code to a human on demand improves their task throughput but not their
measured understanding (Nam et al., ICSE 2024). People who delegate to AI score lower
on comprehension and debugging and attribute less of the code to themselves
(Anthropic 2026 skill-formation RCT; Bergh et al. 2026), while people who use AI for
conceptual questions and explain-back retain understanding. Retrieval practice beats
re-reading for retention, and re-reading inflates confidence (Roediger & Karpicke 2006).
So this skill never "re-explains" first: it asks, grades against the code, and only then
explains, briefly, with the evidence.

## Session shape (10-15 minutes)

Run one round of each exercise type; adapt to the user's answers. Keep it
conversational: one question at a time, wait for the answer, grade, continue.
Answer in the user's language.

### 1. Retrieval (glossary and locations)

From `10-glossary.md` and `20-architecture.md`, pick 3-4 entries. Ask the user, from
memory: what the concept means here and roughly where it lives. Grade: correct /
partially / missed, with the `path:line` from the KB (re-verify it with a quick
Grep before showing it).

### 2. Predict-then-verify (behaviour)

Pick a flow from `30-flows/` (or trace a short one with Grep if the KB has none).
Give the trigger and ask the user to predict the next 2-3 hops and the terminal
effect (what is persisted / returned). Then show the actual steps with `path:line`
and point out exactly where the prediction diverged. Divergences are the learning;
praise is not.

### 3. Explain-back (ownership)

Pick one function or module in scope. Ask the user to explain, in their own words,
what it does, who calls it, and what would break if it were deleted. Grade against
the code with Grep for callers. Record the result as a degree-of-knowledge note
(Fritz et al. 2010/2014: knowledge = authorship + interaction) in
`docs/codebase-knowledge/95-learning-log.md`:

| Date | Area | Exercise | Result | Weak spot |

### 4. Block-model question (Schulte 2008)

Ask one question from a cell the user has not been asked in: text surface (what does
this line say), execution (what happens at runtime, with values), or purpose (why
does this exist). Rotate cells across sessions using the learning log.

### 5. Debugging first (optional, when the user has time)

Describe a plausible failure in the scoped area ("the endpoint returns 500 when the
session cookie is missing") and ask the user for a diagnosis and the first line they
would look at. Do not give the fix until they have stated a hypothesis: debugging is
where AI-assisted learners fall furthest behind.

## Closing

Summarise: what the user retrieved correctly, the two weakest spots with the file
to read next (one path each, with a line range), and append the session to
`95-learning-log.md`. Suggest the next session's scope from the weakest spot.

## Rules

- Never reveal the answer before the user has attempted it, unless they ask to skip.
- Grade against the code, not against the KB alone; re-verify lines you cite.
- Read-only: no edits outside `docs/codebase-knowledge/`, no running code.
