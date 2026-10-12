# Reading strategies, condensed from the literature

Use the strategy that matches the situation. Record which one you used in the
question log when an area was hard; the next session benefits.

## Top-down, hypothesis-driven (Brooks 1983)

When: unfamiliar repo, you have an idea of the framework or domain.
How: state a hypothesis, list the beacons it predicts, grep for them, revise.
Beacons are surface features that strongly signal a structure: a `urls.py`, a
`Startup.cs`, a `main.go` with `http.ListenAndServe`, a `celery.py`, a `reducers/`
directory, a migration folder. One grep per beacon.
Failure mode: confirmation bias. Also grep for one beacon that would *refute* the hypothesis.

## Bottom-up chunking (Pennington 1987)

When: no recognisable framework, generated or legacy code, a single confusing file.
How: read control flow first (what calls what, loops, branches), name each chunk with a
one-line intent, then assemble chunks into a situation-level story (what domain goal
this serves). Write the chunk names into the flow file as you go.

## Systematic tracing (Littman et al. 1986; Robillard et al. 2004)

When: you need to understand a behaviour end to end, or a change may have non-local
effects.
How: start at the trigger, follow every call out until you reach persistence, I/O or a
return; at each hop grep for other callers of the function you are leaving. Keep a
numbered list. Do not skip a hop because it "looks like plumbing"; plumbing is where
cross-cutting behaviour hides (auth, retries, transactions).
Failure mode: inattention blindness, scrolling past the relevant code. Use symbol
search instead of scrolling.

## Opportunistic inquiry (Letovsky 1987)

When: everything else. The expert's default.
How: question -> conjecture -> verification. Write the question, guess the answer,
then do the one search that would settle it. Log it in `90-questions.md` whether or
not it closes.

## Concept location (Rajlich & Wilde 2002; Dit et al. 2013)

When: "where is X implemented?"
How: combine techniques, because each alone misses: textual search for the concept
and its synonyms; static dependencies from the first hit outward; test names; git log
with `-S<term>` or `--grep=<term>` to find the commits that introduced the concept.
Expect the first cue to fail (Ko et al. 2006); iterate on vocabulary.

## History mining for rationale (LaToza & Myers 2010; Nygard 2011)

When: "why is it like this?"
How, in order of reliability:
1. ADRs or design docs in the repo.
2. `git log --follow -- <path>` and read the messages of the commits that shaped the file.
3. `git log -S'<symbol>'` to find when a symbol appeared or vanished.
4. `git blame -L <range> -- <path>` for the author and commit of a specific odd line.
5. Infer from surrounding tests and comments. Label as inferred.

## When to stop reading and delegate

If a question needs more than ~10 tool calls or touches more than ~8 files, spawn a
sub-agent with a precise question and a budget. Your context is the scarce resource;
a sub-agent returns 1-2k tokens of distilled findings instead of 30k tokens of raw code.
