# Question catalog

Adapted from Sillito, Murphy & De Volder (2006/2008), "Asking and answering questions
during a programming change task" (44 question types in four groups), and from
LaToza & Myers (2010), "Hard-to-answer questions about code" (the ones developers rate
hardest: rationale, history, behaviour under conditions, reachability/impact).

Use this as a seed for `90-questions.md`. Do not try to answer all of them; pick the
ones that matter for the scope, record a conjecture for each, and close them with
`path:line` or commit evidence.

## Group 1: Finding initial focus points

1. Which types/modules represent the domain concept X?
2. Where in the code is the text in this UI element, error message or log line?
3. Where is the entry point for this behaviour (route, command, handler, job)?
4. Where are instances of this class/type created?
5. Where is this data stored or persisted (table, file, cache, queue)?
6. Which tests exercise concept X?

## Group 2: Building on initial points

7. What does this function do, in one sentence, and what are its inputs/outputs?
8. Who calls this function / who depends on this module? (in-edges)
9. What does this function call / what does this module depend on? (out-edges)
10. Where is this value/field read, and where is it written?
11. What are the subtypes/implementations of this interface, and which one runs in production?
12. What configuration or environment affects this code path?
13. Which external services or libraries does this path touch?

## Group 3: Understanding a subgraph

14. What is the sequence of calls for request/job/command X, end to end?
15. What invariants or preconditions does this code assume? Where are they checked?
16. Under what conditions does this branch/exception/early-return happen?
17. What is the lifecycle of this object (creation, mutation, disposal)?
18. How does data flow from input to persistence to output for feature X?
19. What is the concurrency model here (threads, async, workers, locks)?
20. What happens when this fails? Who catches, retries, logs or ignores the error?
21. Which parts of this subgraph are covered by tests, and which are not?

## Group 4: Questions over groups of subgraphs

22. How are these two features/modules related? Do they share state?
23. What would be affected if I changed this type/signature/table? (impact)
24. Is this behaviour duplicated elsewhere? Which copy is canonical?
25. What is the dependency direction between layers, and where is it violated?
26. Which modules are tightly coupled and should be understood together?
27. Where does the implemented architecture disagree with the documented one?

## Hard questions (LaToza & Myers 2010), answered mostly from history

28. Why was it done this way? (rationale)
29. Why is this code here at all? Is it still used? (dead or legacy code)
30. When and why did this change last? Who knows about it?
31. Was there a previous approach that was abandoned? Why?
32. Which areas have a single knowledgeable person (truck factor 1)?
33. What are the known workarounds, hacks or "do not touch" zones, and why?
34. What is the intended extension point for adding a new X?
35. What performance or scale assumptions are baked in?

## Newcomer questions (Begel & Simon 2008; Dagenais et al. 2010)

36. How do I build, run and test this locally, step by step? Which step is fragile?
37. What is a safe first change to make, and how would I verify it?
38. What are the conventions I must follow for a PR to be accepted?
39. Which terms do people on this project use that mean something specific here?
