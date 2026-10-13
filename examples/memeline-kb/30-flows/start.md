# Flow: início da partida diária (SSR + POST /api/play/start + resume)

Trigger: duas entradas em produção. (a) No SSR, `Page()` chama `startSession("us")` —
`apps/web/src/app/page.tsx:19`. (b) No cliente, o `useEffect` de montagem chama
`fetch("/api/play/start", {edition, day})` — `apps/web/src/components/Memeline.tsx:159`,
mas só quando o dia local difere do dia do puzzle que veio do SSR. Há uma terceira chamada
em `restart()` (`apps/web/src/components/Memeline.tsx:416`), disparada pelo `onAgain` do
Scorecard (`apps/web/src/components/Memeline.tsx:822-825`).

Confiança: alta.

1. SSR monta a partida do dia UTC: `Page` chama `startSession("us")` sem `clientDay` — `apps/web/src/app/page.tsx:19` → `apps/web/src/server/play.ts:147`. Se lançar, a página renderiza com `initialError` (`apps/web/src/app/page.tsx:20-25`). Créditos vêm de `listCredits("us")` (`apps/web/src/app/page.tsx:31` → `apps/web/src/server/pool.ts:94`).
2. O cliente recebe `initial: StartResponse`; `stripTimeline` separa `core` de `timeline` — `apps/web/src/components/Memeline.tsx:69` → `apps/web/src/components/Memeline.tsx:933`.
3. O cliente decide entre start e resume, uma vez só na montagem (efeito em `apps/web/src/components/Memeline.tsx:146-241`):
   - 3a. `localDay()` (`apps/web/src/components/Memeline.tsx:156` → `apps/web/src/lib/progress.ts:68`) dá `YYYY-MM-DD` no fuso do aparelho. Se `firstCore.puzzleId` não termina com esse dia (`apps/web/src/components/Memeline.tsx:157`), faz `POST /api/play/start` com `{edition, day: today}` (`apps/web/src/components/Memeline.tsx:159-163`). Com `res.ok`, troca `timeline` e `core` (`apps/web/src/components/Memeline.tsx:164-170`). `!res.ok` é ignorado em silêncio; erro de rede cai no `catch` vazio (`apps/web/src/components/Memeline.tsx:171-173`).
   - 3b. `findFinished(ed, active.puzzleId)` (`apps/web/src/components/Memeline.tsx:177` → `apps/web/src/lib/progress.ts:151`). Dia já concluído → monta a tela de resultado a partir do histórico local (`apps/web/src/components/Memeline.tsx:178-201`) e retorna sem rede.
   - 3c. `loadInProgress(ed, active.puzzleId)` (`apps/web/src/components/Memeline.tsx:205` → `apps/web/src/lib/progress.ts:120`). Com token salvo, `POST /api/play/resume` com `{token}` (`apps/web/src/components/Memeline.tsx:208-212`) → `apps/web/src/app/api/play/resume/route.ts:24` → `resumeSession` em `apps/web/src/server/play.ts:174`. `!res.ok` → `clearInProgress(ed)` (`apps/web/src/components/Memeline.tsx:215` → `apps/web/src/lib/progress.ts:134`). Ok → reaplica `saved.marks` sobre `correct` (`apps/web/src/components/Memeline.tsx:221-224`).
4. Rota `/api/play/start`: `POST` em `apps/web/src/app/api/play/start/route.ts:17`, com `runtime = "nodejs"` e `dynamic = "force-dynamic"` (`apps/web/src/app/api/play/start/route.ts:14-15`).
   - 4a. Rate limit — `apps/web/src/app/api/play/start/route.ts:18` → `apps/web/src/server/rate-limit.ts:37`. Chave de `callerKey` (`apps/web/src/server/rate-limit.ts:27`): `x-forwarded-for`, depois `x-real-ip`, depois `"local"`. 90 hits por 60 s (`apps/web/src/server/rate-limit.ts:10-11`). Acima disso, 429 via `fail` (`apps/web/src/server/http.ts:34`).
   - 4b. `readBody` — `apps/web/src/app/api/play/start/route.ts:20` → `apps/web/src/server/http.ts:14`; corpo inválido vira `{}`.
   - 4c. `parseEdition(body.edition)` — `apps/web/src/app/api/play/start/route.ts:22` → `apps/web/src/server/http.ts:27`; ausente vira `"us"`, desconhecido lança `PlayError` 400.
   - 4d. `startSession(edition, body.day)` — `apps/web/src/app/api/play/start/route.ts:22` → `apps/web/src/server/play.ts:147`.
5. `getPool(edition)` — `apps/web/src/server/play.ts:148` → `apps/web/src/server/pool.ts:57`. O pool vem de `import seedUs from "@/data/seed.us.json"` (`apps/web/src/server/pool.ts:16`) e só existe para `us` (`RAW_POOLS`, `apps/web/src/server/pool.ts:18-20`). `br` e `global` lançam em `apps/web/src/server/pool.ts:63` (vira 500). Primeira chamada valida com `assertPool` (`apps/web/src/server/pool.ts:28-51`) e guarda no cache de módulo `pools` (`apps/web/src/server/pool.ts:53`, `apps/web/src/server/pool.ts:68`).
6. `resolveDay(clientDay, new Date())` — `apps/web/src/server/play.ts:149` → `apps/web/src/server/play.ts:65`. Valor que não é `YYYY-MM-DD` cai no dia UTC; fora da janela ±1 dia em torno do UTC lança `PlayError` (400).
7. `puzzleOf(edition, day)` — `apps/web/src/server/play.ts:149` → `apps/web/src/server/play.ts:78`. `puzzleId = "${edition}-${day}"`, `puzzleNumber = floor((day - 2026-01-01)/1d) + 1` (`PUZZLE_EPOCH_UTC`, `apps/web/src/server/play.ts:35`).
8. `buildDeck(pool, { edition, seed: puzzleId, size: DECK_SIZE })` — `apps/web/src/server/play.ts:152` → `packages/core/src/index.ts:404`. `DECK_SIZE = 12` (`packages/core/src/types.ts:136`). Determinístico: `mulberry32(hashSeed(seed))` (`packages/core/src/index.ts:414`, `packages/core/src/index.ts:314`, `packages/core/src/index.ts:337`); pool ordenado por id antes do sorteio (`packages/core/src/index.ts:419`); âncora via `pickAnchor` entre os 3 mais notórios do terço central (`packages/core/src/index.ts:384`); cartas seguintes por custo gap/notoriedade (`packages/core/src/index.ts:431-455`). Retorna `puzzleId: "${edition}:${seed}"` (`packages/core/src/index.ts:460`), ou seja `"us:us-2026-10-12"` (ver questões). Pool vazio lança `[core]` (`packages/core/src/index.ts:409`) → 501.
9. `createGame(deck)` — `apps/web/src/server/play.ts:153` → `packages/core/src/index.ts:133`: `placedIds = [anchorId]`, `queueIds = cardIds`, `lives = MAX_LIVES` (`packages/core/src/types.ts:135`), `score = 0`, `results = []`.
10. `sessionCore(state, puzzleId, puzzleNumber)` — `apps/web/src/server/play.ts:156` → `apps/web/src/server/play.ts:127`.
    - 10a. `signSession({ state, puzzleNumber, issuedAt: Date.now() })` — `apps/web/src/server/play.ts:130` → `apps/web/src/server/session.ts:60`. Token = `base64url(JSON) + "." + base64url(HMAC-SHA256)`. Segredo de `secret()` (`apps/web/src/server/session.ts:27`): `process.env.MEMELINE_SESSION_SECRET` com fallback `DEV_SECRET` (`apps/web/src/server/session.ts:23`); em produção sem a env, `console.warn` uma vez. O token é legível (base64), mas só carrega ids.
    - 10b. `currentCard` (`apps/web/src/server/play.ts:134` → `apps/web/src/server/play.ts:111`) = `toClientCard(requireCard(edition, queueIds[0]))`; `requireCard` em `apps/web/src/server/pool.ts:84` usa `getCardIndex` (`apps/web/src/server/pool.ts:73`). `toClientCard` (`packages/core/src/index.ts:268`) é whitelist: id, name, image, attribution.
    - 10c. `totalOf` (`apps/web/src/server/play.ts:107`) dá 11; `finished = false`, `share = null`.
11. Timeline inicial: `[anchorEntry(requireCard(edition, deck.anchorId))]` — `apps/web/src/server/play.ts:157` → `apps/web/src/server/play.ts:101`. Só a âncora vem revelada: `revealOf` (`apps/web/src/server/play.ts:91`) formata com `formatMonth(..., "pt")` (`packages/core/src/index.ts:68`), `correct: null`.
12. Resposta: `StartResponse` = `SessionCore` + `timeline` (`apps/web/src/lib/protocol.ts:15-39`).
13. Persistência no cliente: o start NÃO grava nada no localStorage. A primeira gravação é `saveInProgress` (`apps/web/src/lib/progress.ts:127`), chamada em `apps/web/src/components/Memeline.tsx:361` só depois da primeira jogada. `restart()` chama `clearInProgress` (`apps/web/src/components/Memeline.tsx:429`). Ponto terminal: `setCore`/`setTimeline` em `apps/web/src/components/Memeline.tsx:168-169` (montagem) e `apps/web/src/components/Memeline.tsx:431-432` (restart).

## Shared hops (used by other flows too)

- `sessionCore` / `signSession` (`apps/web/src/server/play.ts:127`, `apps/web/src/server/session.ts:60`): também em `resumeSession` (`apps/web/src/server/play.ts:203`) e `applyPlayerMove` (`apps/web/src/server/play.ts:238`).
- `requireCard` / `getCardIndex` / `getPool` (`apps/web/src/server/pool.ts:84`, `apps/web/src/server/pool.ts:73`, `apps/web/src/server/pool.ts:57`): resume (`apps/web/src/server/play.ts:198`), move (`apps/web/src/server/play.ts:228`, `apps/web/src/server/play.ts:230`), `listCredits` (`apps/web/src/server/pool.ts:95`).
- `toClientCard`: 4 chamadas em `apps/web/src/server/play.ts:103`, `apps/web/src/server/play.ts:113`, `apps/web/src/server/play.ts:199`, `apps/web/src/server/play.ts:240`.
- `puzzleOf`: start, resume e move (`apps/web/src/server/play.ts:149`, `apps/web/src/server/play.ts:195`, `apps/web/src/server/play.ts:234`).
- `startSession` tem exatamente 2 chamadores: `apps/web/src/app/page.tsx:19` e `apps/web/src/app/api/play/start/route.ts:22`.

## State touched

- Cache de módulo `pools` e `indexes` (`apps/web/src/server/pool.ts:53-54`), nunca invalidado.
- `hits` e `lastSweep` do rate limit (`apps/web/src/server/rate-limit.ts:13-14`), por instância.
- Flag `avisou` (`apps/web/src/server/session.ts:25`).
- Env: `MEMELINE_SESSION_SECRET`, `NODE_ENV` (`apps/web/src/server/session.ts:28-30`).
- Relógio: `new Date()`/`Date.now()` em `apps/web/src/server/play.ts:149`, `apps/web/src/server/play.ts:130`.
- Cliente: localStorage `memeline:progress:v1`, só leitura no start (`findFinished`, `loadInProgress`, `getStreak` em `apps/web/src/components/Memeline.tsx:149` → `apps/web/src/lib/progress.ts:177`); escrita só via `clearInProgress`.
- Nenhuma persistência no servidor: sessão stateless.

## Failure handling

- Rota start (`apps/web/src/app/api/play/start/route.ts:23-25` → `failure`, `apps/web/src/server/http.ts:44`): `PlayError` → status próprio; `SessionError` → 401; mensagem `[core]` → 501 com `console.error`; resto → 500 genérico com `console.error` (inclui `[pool]` para `br`/`global`).
- Rate limit → 429 antes do try.
- SSR: `try/catch` em `apps/web/src/app/page.tsx:18-25` vira `initialError`.
- Cliente: start `!res.ok` ignorado; erro de rede engolido (`apps/web/src/components/Memeline.tsx:171`, `apps/web/src/components/Memeline.tsx:232`); resume `!res.ok` limpa o progresso. `restart()` usa `reportError` e libera `busy` no `finally`.
- `progress.ts` engole exceções de `localStorage` (`apps/web/src/lib/progress.ts:96`, `apps/web/src/lib/progress.ts:106`).

## Tests covering this flow

- `packages/core/src/deck.test.ts:48-71` (determinismo de `buildDeck`), `packages/core/src/game.test.ts:44-68` (`createGame`), `packages/core/src/game.test.ts:236-244` (`toClientCard`, regra de ouro 3).
- `apps/web/src/lib/progress.test.ts` cobre `localDay`, in-progress, `findFinished` e streak.
- Sem testes para `startSession`, `resolveDay`, `puzzleOf`, `signSession`, rotas, `pool.ts` e a decisão start/resume em `Memeline.tsx`.

## Open questions

1. Dois formatos de `puzzleId`: dentro do token, `"us:us-2026-10-12"` (`packages/core/src/index.ts:460`); na resposta, `"us-2026-10-12"` (`apps/web/src/server/play.ts:81`). Funciona porque `resumeSession` extrai a data por regex no fim (`apps/web/src/server/play.ts:186`). Intencional?
2. `restart()` não manda `day` (`apps/web/src/components/Memeline.tsx:419`): perto da meia-noite local, "Jogar de novo" pode trazer o puzzle de outro dia.
3. `restart()` não checa `findFinished`; `recordFinish` substitui a entrada do mesmo `puzzleId` (`apps/web/src/lib/progress.ts:160-163`), o que contradiz `apps/web/src/components/Memeline.tsx:142-143`.
4. Se o SSR falhou (`initial = null`), o efeito retorna cedo (`apps/web/src/components/Memeline.tsx:147`) e o cliente nunca tenta `/start` sozinho.
5. O SSR sempre gera token e deck mesmo quando o cliente vai descartá-los (custo, não bug).
