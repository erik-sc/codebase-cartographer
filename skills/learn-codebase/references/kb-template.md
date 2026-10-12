# Knowledge base layout

All files live in `docs/codebase-knowledge/`. Keep the numbering and section headings
stable across runs so that `git diff` on the KB shows how understanding changed.

```
docs/codebase-knowledge/
├── INDEX.md            <= 60 lines; the only file meant to be @imported into CLAUDE.md
├── 00-overview.md      hypothesis, beacons, build/run/test facts
├── 10-glossary.md      concept -> code mapping
├── 20-architecture.md  structural map (program model)
├── 30-flows/           one file per end-to-end behaviour (situation model)
│   └── <flow-name>.md
├── 40-history.md       timeline, hotspots, ownership, inferred rationale
├── 50-conventions.md   local plans and idioms, with observed violations
└── 90-questions.md     question log (open / verified / refuted)
```

## Evidence format

Every factual sentence carries at least one citation in this exact form so that the
`verifier` agent and `scripts/kb_lint.py` can check it:

- `path/to/file.ext:123` for a line
- `path/to/file.ext:120-140` for a range
- `commit abc1234` for history
- `(unverified)` when you could not find evidence and are stating an expectation

Relative paths from the repository root. No `./` prefix.

## INDEX.md

```markdown
# <Project> knowledge base

<One paragraph: what the system does, for whom, main technologies.>

**Architectural hypothesis (verified):** <one sentence>

## Read next
- [Overview](00-overview.md) · [Glossary](10-glossary.md) · [Architecture](20-architecture.md)
- Flows: [startup](30-flows/startup.md), [<main flow>](30-flows/<name>.md)
- [History and ownership](40-history.md) · [Conventions](50-conventions.md) · [Open questions](90-questions.md)

## Five things you would not guess from the code
1. ... (path:line or commit)
...

## Top open questions
1. ...
```

## 00-overview.md

```markdown
# Overview
## Hypothesis and beacons
| Beacon expected | Found? | Evidence |
## Repository shape
<the skeleton script's summary: languages, size, top directories>
## Build, run, test
<only what config files say; mark each "verified in <path>" or "unverified">
## Entry points
| Kind (http/cli/job/ui) | Name | path:line |
```

## 10-glossary.md

```markdown
# Glossary
| Concept | Meaning here | Where (path:line) | Aliases in code | Notes |
## Naming hazards
- <two names, one thing> / <one name, two things>
```

## 20-architecture.md

```markdown
# Architecture (implemented)
## Layers and dependency direction
## Modules
| Module | Responsibility | Public surface | Depends on | Depended on by | Evidence |
## Data stores and external services
## Boundaries and seams
## Where implemented differs from documented
```

## 30-flows/<name>.md

```markdown
# Flow: <name>
Trigger: <what starts it> (path:line)
1. <step> — path:line
2. ...
## State touched
## Failure handling
## Tests covering this flow
## Open questions
```

## 40-history.md

```markdown
# History and ownership
## Timeline of structural decisions
| When | What | Why (documented / inferred) | Evidence (commit) |
## Hotspots (churn)
## Ownership concentration (truck factor)
| Area | Main author(s) | Risk |
## Candidate ADRs (inferred, not documented)
```

## 50-conventions.md

```markdown
# Conventions ("plans" this project uses)
## Naming
## Layering rules
## Error handling
## Testing
## Configuration and feature flags
## Observed violations
| Where | Convention broken | Bug or intent? |
```

## 90-questions.md

```markdown
# Question log
| # | Question | Conjecture | Status | Evidence |
```
