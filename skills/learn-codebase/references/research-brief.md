# Research brief: what this workflow is built on

Short version for the agent. The full annotated survey with citations is in the
repository's `RESEARCH.md`.

## Human program comprehension

- Brooks 1983: comprehension is hypothesis-driven; experts look for *beacons* that
  confirm a guess. Start with a hypothesis, not with file one.
- Soloway & Ehrlich 1984: experts chunk code into known *plans* and conventions;
  when conventions are violated their advantage disappears. Extract the local plans.
- Letovsky 1987: the cognitive unit is the inquiry: question -> conjecture -> verify.
- Pennington 1987: two models, *program* (control flow, structure) and *situation*
  (domain, data flow). Produce both.
- Littman et al. 1986; Robillard et al. 2004: systematic tracing succeeds at change
  tasks; as-needed skimming misses non-local effects and suffers inattention blindness.
- von Mayrhauser & Vans 1995: readers switch among domain, program and situation
  models; a persisted knowledge base makes switching cheap.
- Ko et al. 2006/2007; LaToza et al. 2006; LaToza & Myers 2010: the hardest and most
  deferred questions are rationale ("why") and behaviour under conditions; first
  search cues fail often; ~35% of time is navigation.
- Sillito et al. 2006/2008: 44 question types in four groups; tools help with finding
  focus points, not with composing answers across subgraphs.
- Xia et al. 2018: ~58% of developer time is comprehension; seniors spend much less.
- Rajlich & Wilde 2002; Dit et al. 2013: comprehension is concept location; hybrid
  techniques (text + static + dynamic + history) beat any single one.
- Begel & Simon 2008; Dagenais et al. 2010; Steinmacher et al. 2015: newcomers hide
  ignorance, need early experimentation and validation, and are blocked by setup and
  "where do I start".
- Avelino et al. 2016; Rigby et al. 2016; Fritz et al. 2010/2014: knowledge is
  concentrated (truck factor <= 2 in 65% of projects) and is lost on turnover;
  knowledge = authorship + interaction.
- Lethbridge et al. 2003; Aghajani et al. 2019/2020: coarse docs stay useful when
  stale, fine-grained docs rot fastest; outdatedness is the top documentation issue.
- Nygard 2011: ADRs capture rationale cheaply.

## LLM agents on repositories

- Agentless 2024; RepoUnderstander 2024: skeleton first, then hierarchical
  localization (repo -> dir -> file -> symbol).
- CodePlan 2023; RepoGraph 2025; CodexGraph 2024: a dependency graph decides what to
  read next and answers "who uses X" without reading.
- RepoCoder 2023: iterate retrieval using what you just learned; cap the loop.
- SWE-agent 2024; AutoCodeRover 2024: bounded, symbol-level tool views beat raw file
  dumps; over-reading dominates token spend (SWE-Pruner: 76% of tokens are reads).
- DocAgent 2025: summarise in dependency order (leaves first).
- Anthropic context engineering 2025; multi-agent research system 2025: just-in-time
  retrieval, progressive disclosure, structured notes outside the window, sub-agents
  that return 1-2k-token distilled summaries, fan out for breadth only.
- Lost in the Middle 2023; Context Rot 2025: long contexts degrade; keep each context
  short and put the important material first.
- Spracklen et al. 2025: models hallucinate packages/APIs; verify before asserting.
- SWE-QA 2025; CoReQA 2025; RepoQA 2024: cross-file, multi-hop questions are where
  models fail; record call chains explicitly.

## Humans learning with AI

- Nam et al. 2024: on-demand LLM explanations raise throughput but not measured
  understanding.
- METR 2025: experienced devs on their own repos were 19% slower with AI while
  believing they were faster; the agent's missing tacit context is the bottleneck.
- Anthropic 2026 skill-formation RCT; Bergh et al. 2026: delegation lowers
  comprehension (esp. debugging) and ownership; conceptual questions and explain-back
  preserve it.
- Barke et al. 2023; Prather et al. 2023: keep the human in "acceleration" mode by
  having them state the plan or prediction first; otherwise they drift.
- Mozannar et al. 2024: verification is the hidden cost; attach evidence to every claim.
- Roediger & Karpicke 2006; Schulte 2008; Lehtinen et al. 2023: retrieval practice,
  the block-model question grid, and questions about code the learner just touched
  expose fragile knowledge.

## How the principles map to this plugin

| Principle | Where it lives |
|---|---|
| Skeleton first, hypothesis + beacons | `scripts/repo_skeleton.py`, Phase 1 |
| Hierarchical localization, symbol search | cartographer/tracer agent prompts |
| Fan out with budgets, distilled summaries | Phase 2, `maxTurns` on agents |
| Two models: structural and situational | `20-architecture.md`, `30-flows/` |
| Concept location / glossary | Phase 3, `10-glossary.md` |
| Why via history | historian agent, `40-history.md` |
| Question -> conjecture -> verify | `90-questions.md`, `/ask-codebase` |
| Evidence on every claim | `path:line` rule, verifier agent, `kb_lint.py` |
| Persist coarse knowledge, regenerate fine | KB layout, INDEX.md @import |
| Keep the human active | `/quiz-me`, `95-learning-log.md` |
| No approval limbo | read-only tool sets, `dontAsk`, allow rules, hook |
