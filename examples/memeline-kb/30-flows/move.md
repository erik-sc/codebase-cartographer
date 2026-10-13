# Flow: colocar uma carta (jogada / POST /api/play/move)

Trigger: o jogador solta a carta arrastada sobre um slot armado; `onEnd` chama
`void commitRef.current(target)` — `apps/web/src/components/Memeline.tsx:558`. Outros
gatilhos: Enter/Espaço (`apps/web/src/components/Memeline.tsx:623`) e clique no botão
`.slot` (`apps/web/src/components/Memeline.tsx:670`).

Confiança: alta.

1. Arraste: `onPointerDown` (`apps/web/src/components/Memeline.tsx:502`); `onMove` (`apps/web/src/components/Memeline.tsx:522`) arma o slot mais próximo com `nearestSlot` (`apps/web/src/components/Memeline.tsx:463`); `onEnd` (`apps/web/src/components/Memeline.tsx:534`) lê `armedRef.current`, chama `setPlaying(true)` e `commitRef.current(target)` (`apps/web/src/components/Memeline.tsx:558`). O ref aponta para o `commit` mais recente (`apps/web/src/components/Memeline.tsx:407-410`).
2. `commit(index)` — `apps/web/src/components/Memeline.tsx:325`. Não faz nada se `busyRef`, `busy`, `!core` ou `!current` (`apps/web/src/components/Memeline.tsx:326`); liga `setBusyBoth(true)` (`apps/web/src/components/Memeline.tsx:327`; definição em `apps/web/src/components/Memeline.tsx:320`).
3. `fetch("/api/play/move", POST, {token: core.token, index})` — `apps/web/src/components/Memeline.tsx:331-335` → `POST` em `apps/web/src/app/api/play/move/route.ts:17` (`runtime = "nodejs"`, `dynamic = "force-dynamic"`, `apps/web/src/app/api/play/move/route.ts:14-15`).
4. Rate limit — `apps/web/src/app/api/play/move/route.ts:18` → `apps/web/src/server/rate-limit.ts:37`: janela deslizante em memória, 90 hits / 60 s por chave (`callerKey`, `apps/web/src/server/rate-limit.ts:27`); `sweep` limpa no máximo uma vez por janela (`apps/web/src/server/rate-limit.ts:16`). Estouro → `fail(..., 429)` (`apps/web/src/server/http.ts:34`).
5. `readBody` — `apps/web/src/app/api/play/move/route.ts:20` → `apps/web/src/server/http.ts:14`; JSON inválido vira `{}`.
6. `applyPlayerMove(body.token, body.index)` — `apps/web/src/app/api/play/move/route.ts:21` → `apps/web/src/server/play.ts:211`.
7. `verifySession(token)` — `apps/web/src/server/play.ts:212` → `apps/web/src/server/session.ts:65`: HMAC-SHA256 com `timingSafeEqual` (`apps/web/src/server/session.ts:78`), parse do payload base64url, expiração em 12 h (`MAX_AGE_MS`, `apps/web/src/server/session.ts:41`, `apps/web/src/server/session.ts:92`), checagem de formato de `placedIds`, `queueIds`, `results`, `lives`, `score` (`apps/web/src/server/session.ts:96-105`). Falha → `SessionError`. Segredo: `MEMELINE_SESSION_SECRET` ou `DEV_SECRET` com `console.warn` em produção (`apps/web/src/server/session.ts:27-38`).
8. Validações do servidor (`apps/web/src/server/play.ts:216-227`, todas `PlayError`): partida acabada → 409; `index` não inteiro → 400; `index` fora de `0..placedIds.length` → 400; fila vazia → 409. A carta jogada é sempre `queueIds[0]` (o cliente não escolhe a carta), buscada com `requireCard` (`apps/web/src/server/play.ts:228` → `apps/web/src/server/pool.ts:84`).
9. Regra do jogo: `applyMove(before, getCardIndex(edition), index)` — `apps/web/src/server/play.ts:230` → `packages/core/src/index.ts:196`. `getCardIndex` (`apps/web/src/server/pool.ts:73`) é um `Map` id→`MemeCard` em cache por edição. `applyMove` repete as guardas com `[core]` (`packages/core/src/index.ts:202-218`) e monta `timeline` com os `peak` das cartas colocadas (`packages/core/src/index.ts:210`).
10. Acerto: `isCorrectPlacement(timeline, index, card)` — `packages/core/src/index.ts:220` → `packages/core/src/index.ts:98`. Comparações inclusivas, por isso empate conta como acerto (`packages/core/src/index.ts:122-123`). Tolerância via `safeTolerance` (`packages/core/src/index.ts:108` → `packages/core/src/index.ts:85`): não finito vira 0, resto `floor` com mínimo 0.
11. Posição real: `resolvePlacementIndex(timeline, card.peak, index)` — `packages/core/src/index.ts:221` → `packages/core/src/index.ts:167`. Se o slot mantém a linha ordenada, é respeitado (caso do empate); senão a carta vai para a primeira posição com `peak >=` ao dela. Acerto só por tolerância é reposicionado na ordem cronológica.
12. Novo `GameState` sem mutar o anterior (`packages/core/src/index.ts:226-237`): carta entra em `placedIds` em `placedIndex`, `queueIds` perde o primeiro, `lives` cai 1 se errou (mín. 0), `score` sobe 1 se acertou, resultado entra em `results`. Revelação via `toReveal(card)` (`packages/core/src/index.ts:241` → `packages/core/src/index.ts:253`), que usa `formatMonth` (`packages/core/src/index.ts:68`) sem `lang` (pt por padrão). `revealOf` de `apps/web/src/server/play.ts:91` NÃO participa: é usado só pela âncora (`apps/web/src/server/play.ts:103`) e pelo resume (`apps/web/src/server/play.ts:199`).
13. Resposta: `puzzleOf(edition, utcDay(new Date()))` em `apps/web/src/server/play.ts:234`; `puzzleNumber` vem do envelope (`apps/web/src/server/play.ts:235`); `sessionCore(outcome.state, ...)` (`apps/web/src/server/play.ts:238` → `apps/web/src/server/play.ts:127`) assina o novo token com `signSession` (`apps/web/src/server/session.ts:60`) e calcula `finished`, `current` (`toClientCard`, `packages/core/src/index.ts:268`), `lives`, `dealt`, `total`, `share`. Soma `placed` = {`toClientCard(playedCard)`, `outcome.reveal`, `outcome.correct`} e `placedIndex` (`apps/web/src/server/play.ts:239-244`).
14. Share, só no fim: `shareOf` (`apps/web/src/server/play.ts:116`) chama `shareText` (`packages/core/src/index.ts:482`) com `puzzleNumber`, edição, `results`, `score`, `total`, SEM `streak`.
15. `Response.json(...)` — `apps/web/src/app/api/play/move/route.ts:21`; tipo de fio `MoveResponse` (`apps/web/src/lib/protocol.ts:41`, estende `SessionCore`, `apps/web/src/lib/protocol.ts:15`).
16. Cliente: `!res.ok` → `reportError(data.error)` (`apps/web/src/components/Memeline.tsx:338-341`, definido em `apps/web/src/components/Memeline.tsx:308`). Ok → desestrutura `placed`, `placedIndex`, `next` (`apps/web/src/components/Memeline.tsx:344`) e grava `marksRef.current[placed.card.id]` (`apps/web/src/components/Memeline.tsx:348`).
17. Persistência local, antes da animação: se `next.finished`, `recordFinish` (`apps/web/src/components/Memeline.tsx:350` → `apps/web/src/lib/progress.ts:160`), `clearInProgress` (`apps/web/src/components/Memeline.tsx:358` → `apps/web/src/lib/progress.ts:134`) e `getStreak` (`apps/web/src/lib/progress.ts:177`); senão `saveInProgress` com `{puzzleId, token, marks}` (`apps/web/src/components/Memeline.tsx:361` → `apps/web/src/lib/progress.ts:127`). Tudo em `localStorage["memeline:progress:v1"]` (`apps/web/src/lib/progress.ts:24`).
18. UI (`apps/web/src/components/Memeline.tsx:368-386`): FLIP via `captureCards`, `splice` em `placedIndex`, `setCore(next)`, `setReveal`, flash "settle"/"shake", sons, status. Depois de `REVEAL_PAUSE` (`apps/web/src/components/Memeline.tsx:388-398`) desliga `busy`; se `finished`, abre overlay e toca `tada`/`over`.
19. Fim de partida: `<Scorecard share={core?.share ?? null} .../>` (`apps/web/src/components/Memeline.tsx:805-817`); `copy()` (`apps/web/src/components/Scorecard.tsx:49`) faz `navigator.clipboard.writeText(share)` (`apps/web/src/components/Scorecard.tsx:55`). Ponto terminal.

## Shared hops (used by other flows too)

- `isRateLimited`, `readBody`, `failure`/`fail`: também em start (`apps/web/src/app/api/play/start/route.ts:18`, `apps/web/src/app/api/play/start/route.ts:20`, `apps/web/src/app/api/play/start/route.ts:24`) e resume (`apps/web/src/app/api/play/resume/route.ts:21`, `apps/web/src/app/api/play/resume/route.ts:23`, `apps/web/src/app/api/play/resume/route.ts:26`). O mapa de rate limit é um só para as três rotas.
- `verifySession`: 2 chamadores, `apps/web/src/server/play.ts:175` (resume) e `apps/web/src/server/play.ts:212` (move).
- `revealOf`: só start (âncora) e resume. O comentário em `apps/web/src/server/play.ts:86-90` diz "só é chamado para a âncora", o que está desatualizado (`apps/web/src/server/play.ts:199`).
- `shareText`: servidor (`apps/web/src/server/play.ts:118`) e cliente (`apps/web/src/components/Memeline.tsx:35` import, `apps/web/src/components/Memeline.tsx:189` uso no caminho "dia já concluído").
- `reportError` e `setBusyBoth`: também em `restart` (`apps/web/src/components/Memeline.tsx:412`).

## State touched

- Servidor: nenhum estado de partida; só `hits` do rate limit (`apps/web/src/server/rate-limit.ts:13`) e cache `indexes` (`apps/web/src/server/pool.ts:74-79`).
- Cliente: estado React (`timeline`, `core`, `reveal`, `flash`, `busy`, `playing`, `overlay`, `streak`); refs `marksRef`, `busyRef`, `flipRef`, `kbIndexRef`; `localStorage` `memeline:progress:v1` com `inProgress` {puzzleId, token, marks} ou `history[]` de `Finished`, limite 400 (`apps/web/src/lib/progress.ts:26`).

## Failure handling

- 429 rate limit (`apps/web/src/app/api/play/move/route.ts:18`); `SessionError` → 401 (`apps/web/src/server/http.ts:46`); `PlayError` → 400/409 (`apps/web/src/server/http.ts:45`); mensagem `[core]` → 501 com `console.error` (`apps/web/src/server/http.ts:49-51`; na prática as guardas de `applyMove` não disparam porque `applyPlayerMove` valida antes); `[pool] carta ... não existe` de `requireCard` (`apps/web/src/server/pool.ts:86`) → 500 genérico (`apps/web/src/server/http.ts:53-54`). Nenhuma stack vai ao cliente.
- Cliente: `!res.ok` ou exceção caem em `reportError`, que seta erro/status e `setPlaying(false)` (`apps/web/src/components/Memeline.tsx:308-318`); quem desliga `busy` é o chamador, com `setBusyBoth(false)` (`apps/web/src/components/Memeline.tsx:340`, `apps/web/src/components/Memeline.tsx:399-401`). Sem retry.
- `progress.ts` engole exceções de `localStorage` (`apps/web/src/lib/progress.ts:96-99`, `apps/web/src/lib/progress.ts:106-108`).
- Clipboard engole permissão negada e mostra "copiado" (`apps/web/src/components/Scorecard.tsx:56-60`).

## Tests covering this flow

- `packages/core/src/placement.test.ts` (`isCorrectPlacement`: linha vazia, empate, tolerância, extremos, slot inválido); `packages/core/src/game.test.ts` (`applyMove`, `toClientCard`); `packages/core/src/share.test.ts` (`shareText`); `apps/web/src/lib/progress.test.ts`.
- NENHUM teste para a rota, `applyPlayerMove`, `verifySession`/`signSession`, `rate-limit`, `http.failure` ou `commit`.

## Open questions

1. **Provável bug: `puzzleId` divergente.** `applyPlayerMove` devolve `puzzleId` de `utcDay(new Date())` (`apps/web/src/server/play.ts:234`), não de `before.puzzleId`; o start usa o dia LOCAL (`apps/web/src/server/play.ts:149`, `apps/web/src/components/Memeline.tsx:157-162`). O cliente salva `next.puzzleId` (`apps/web/src/components/Memeline.tsx:352`, `apps/web/src/components/Memeline.tsx:362`) e depois compara com o id do dia local (`apps/web/src/components/Memeline.tsx:177`, `apps/web/src/components/Memeline.tsx:205`; `apps/web/src/lib/progress.ts:122`, `apps/web/src/lib/progress.ts:152`). No Brasil depois das 21h os ids não batem: partida em andamento se perde ao recarregar e o dia concluído não é reconhecido. O comentário em `apps/web/src/server/play.ts:232-233` trata só do `puzzleNumber`.
2. Share inconsistente: o do servidor não inclui `streak` (`apps/web/src/server/play.ts:118-124`); o remontado no cliente para "dia já concluído" inclui (`apps/web/src/components/Memeline.tsx:189-196`). O comentário em `apps/web/src/components/Scorecard.tsx:51-52` ("o cliente não remonta a string") é falso nesse caminho.
3. `apps/web/src/lib/protocol.ts:4-6` diz que nenhum runtime do core chega ao bundle, mas `apps/web/src/components/Memeline.tsx:35` importa `shareText` em runtime.
4. Sem nonce, um token já usado continua válido por 12 h: o cliente pode reenviar um token antigo e "desfazer" um erro. Rate limit por `x-forwarded-for` é falsificável sem proxy confiável.
5. `toReveal` não recebe idioma (pt fixo, `packages/core/src/index.ts:248-251`): a edição `us` recebe rótulos em português.
