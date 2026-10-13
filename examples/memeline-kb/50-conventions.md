# Conventions ("plans" this project uses)

## Naming

- Prefixo `[modulo]` em mensagens de erro e log: `[core] função:` (`packages/core/src/index.ts:42`,
  `packages/core/src/index.ts:149`, `packages/core/src/index.ts:409`), `[pool]`
  (`apps/web/src/server/pool.ts:63-65`), `[api]` (`apps/web/src/server/http.ts:50`),
  `[page]` (`apps/web/src/app/page.tsx:24`), `[session]` (`apps/web/src/server/session.ts:32-35`).
- Comentários longos em pt-BR explicando o porquê, citando `PLANO §x.y` e "regra de ouro nº N"
  (`CLAUDE.md:59`; ex. `packages/ingest/src/pool.ts:107`, `packages/ingest/src/peak.ts:214`).
- Variáveis locais misturam português e inglês (`cabeDepoisDoAnterior`,
  `packages/core/src/index.ts:122`); helpers de teste em português (`carta`, `acervo`,
  `deckDe`, `congelar`, `packages/core/src/game.test.ts:7-42`; `alvo`,
  `packages/core/src/placement.test.ts:5`).
- Imports internos com extensão `.ts` (`packages/core/src/index.ts:18`,
  `packages/core/tsconfig.json:4`; motivo em commit 72e51eb).
- Arquivos de saída do ingest: `out/candidates.<locale>.json`, `out/pool.<locale>.json`,
  `out/pool.<locale>.audit.json`, `out/curation-queue.<locale>.json`
  (`packages/ingest/src/cli/build-pool.ts:41`, `packages/ingest/src/cli/build-pool.ts:72-73`,
  `packages/ingest/src/cli/curation-queue.ts:142-157`).

## Layering rules

- `web → core`, `ingest → core`, nunca o contrário (`CLAUDE.md:44`); respeitado (ver
  `20-architecture.md`).
- `packages/core`: zero I/O, zero `Date.now()`, `Math.random()` proibido para o deck ser
  reproduzível (`packages/core/src/index.ts:9-10`, `packages/core/src/index.ts:328-332`).
- `apps/web/src/server/*` é a autoridade: o cliente só manda `{token, index}` e o servidor
  escolhe a carta (`queueIds[0]`, `apps/web/src/server/play.ts:226`).
- `lib/protocol.ts` só com tipos (`apps/web/src/lib/protocol.ts:4-6`).
- Predicado não lança, fronteira lança: `isCorrectPlacement` devolve `false` para slot
  inválido (`packages/core/src/index.ts:103-106`) e `applyMove` lança
  (`packages/core/src/index.ts:212-218`).
- Imutabilidade no core: arrays copiados antes de escrever (`packages/core/src/index.ts:223-227`);
  testes congelam o estado com `Object.freeze` (`packages/core/src/game.test.ts:37-42`).
- Determinismo: ordenação canônica por id antes de qualquer sorteio
  (`packages/core/src/index.ts:416-419`).

## Error handling

- Classes próprias: `PlayError` com `status` (default 400; usada também com 409,
  `apps/web/src/server/play.ts:26-32`), `SessionError` (`apps/web/src/server/session.ts:50`),
  `NotFoundError`/`HttpError` no ingest (`packages/ingest/src/util/http.ts:21-41`).
- Mapeamento central erro → HTTP em `failure()` (`apps/web/src/server/http.ts:44-55`):
  `PlayError` → status próprio; `SessionError` → 401; mensagem iniciando com `[core]` → 501;
  resto → 500 genérico sem stack. Corpo sempre `{ error }` (`apps/web/src/server/http.ts:35`).
- As três rotas têm o mesmo esqueleto: `isRateLimited` → 429, depois `try { … } catch
  { return failure(error) }` (`apps/web/src/app/api/play/move/route.ts:17-25`).
- `readBody` engole JSON inválido e devolve `{}` (`apps/web/src/server/http.ts:14-25`).
- Core: `RangeError` para argumento fora da faixa, `Error` para bug de dados
  (`packages/core/src/index.ts:42`, `packages/core/src/index.ts:149`).
- Ingest: 404 vira valor (`null`/`missing`), não exceção (`packages/ingest/src/wikipedia.ts:239-241`,
  `packages/ingest/src/pageviews.ts:87-89`); rejeições de domínio são valores
  (`CommonsLookup`, `RejectionReason`, `packages/ingest/src/pool.ts:183-215`); `buildCard`
  captura tudo como `fetch-error` (`packages/ingest/src/pool.ts:147-171`). Retry com backoff
  exponencial para 5xx/429/rede (`packages/ingest/src/util/http.ts:88`,
  `packages/ingest/src/util/http.ts:118`).
- Cliente: `progress.ts` engole exceções de `localStorage` (`apps/web/src/lib/progress.ts:96-99`).
- Página degrada: erro no SSR vira `initialError` (`apps/web/src/app/page.tsx:18-25`).

## Testing

- Vitest, `vitest run` nos 3 workspaces (`packages/core/package.json:12`,
  `packages/ingest/package.json:7`, `apps/web/package.json:10`); sem `vitest.config.*`;
  testes colocalizados `*.test.ts`.
- `describe` nomeado "função — cenário" (`packages/core/src/placement.test.ts:44`); um arquivo
  por área no core (dates, placement, game, deck, share).
- Helpers locais por arquivo, não compartilhados: `carta()` com assinaturas diferentes em
  `packages/core/src/game.test.ts:7` e `packages/core/src/deck.test.ts:4`; `poolGrande()`
  (`packages/core/src/deck.test.ts:27`); `series`/`calm` (`packages/ingest/src/peak.test.ts:19`,
  `packages/ingest/src/peak.test.ts:25`).
- `fakeStorage()` via `vi.stubGlobal("window", …)` para evitar jsdom
  (`apps/web/src/lib/progress.test.ts:14-29`).
- Cobertura: core bem coberto (89 testes, commit a6260ca); ingest só `peak.ts`; web só
  `progress.ts`. Sem testes de rotas, sessão, rate limit, `pool.ts`, HTTP/cache do ingest ou CLIs.

## Configuration and feature flags

- Sem feature flags no código (`docs/PLANO.md:222` cita PostHog como plano).
- Só quatro `process.env`: `MEMELINE_SESSION_SECRET` e `NODE_ENV`
  (`apps/web/src/server/session.ts:28-30`), `NEXT_DIST_DIR` (`apps/web/next.config.ts:19`),
  `PORT` (`tools/serve.mjs:9`). Sem `.env.example`.
- `packages/ingest/src/config.ts` só tem constantes (`:19` `USER_AGENT`, `:23-25` janela de
  dados, `:28-31` `PROJECT_BY_LOCALE`, `:42-48` intervalos, `:51` `THUMB_WIDTH`, `:56-58` paths).
- `tsconfig.base.json:4-19`: ES2022, `moduleResolution: "Bundler"`, `strict`,
  `noUncheckedIndexedAccess`, `allowImportingTsExtensions`, `noEmit`.
- Build e dev em diretórios separados: `tools/build-web.mjs:14-20` roda `next build` com
  `NEXT_DIST_DIR=".next-prod"` (motivo em `apps/web/next.config.ts:11-18`, `CLAUDE.md:63-65`).
- Sem parameter properties em classes por causa do `--experimental-strip-types`
  (`packages/ingest/src/util/http.ts:12-18`).
- `.gitignore:1-18` ignora `.env*`, `.next/`, `.next-prod/`, `out/`, `coverage/`,
  `packages/ingest/.cache/`, `packages/ingest/out/`. `.claude/launch.json:4-9` só define o
  servidor estático de docs.
- Commits: assunto `<área>: <resumo>` em pt sem acentos, corpo em prosa com a motivação
  (commits 54ce7c5, 3069964, 72e51eb).

## Observed violations

| Where | Convention broken | Bug or intent? |
|---|---|---|
| `apps/web/src/server/play.ts:234` | `puzzleId` da resposta do move vem de `utcDay(new Date())`, não de `before.puzzleId`; o start usa dia local (`apps/web/src/server/play.ts:149`) | Provável bug: ids divergem perto da meia-noite local (ver `30-flows/move.md`) |
| `apps/web/src/components/Memeline.tsx:35`, `:189-196` | Runtime do core no bundle do cliente e share remontado, contra `apps/web/src/lib/protocol.ts:4-6` e `apps/web/src/components/Scorecard.tsx:51-52` | Intenção não documentada; dois formatos de share |
| `apps/web/src/components/Memeline.tsx:412-425`, `apps/web/src/components/Scorecard.tsx:129-130` | "Jogar de novo" sem `day` e sem checar `findFinished`; `recordFinish` sobrescreve (`apps/web/src/lib/progress.ts:163`) | Fura o daily; intenção desconhecida (modo treino?) |
| `apps/web/src/server/http.ts:40-51` | `[core]` → 501 assume core "não implementado"; hoje `[core]` é violação de invariante | Resquício de andaime; expõe mensagem interna |
| `apps/web/src/server/http.ts:12` + `apps/web/src/server/pool.ts:62-65` | `br`/`global` aceitos mas sem acervo → 500 em vez de 4xx | Dívida conhecida do MVP 1 |
| `apps/web/src/server/session.ts:23`, `:30-37` | Segredo de dev hardcoded; produção sem env só avisa | Risco assumido no comentário |
| `apps/web/src/server/rate-limit.ts:27-33` | Confia em `x-forwarded-for` sem validar proxy | Documentado como intencional (`apps/web/src/server/rate-limit.ts:4-6`) |
| `apps/web/src/server/play.ts:91-99` vs `packages/core/src/index.ts:249-255` | `revealOf` duplica `toReveal` privado do core | Intenção: `toReveal` não exportado; candidato a refatorar |
| `apps/web/src/server/play.ts:128`, `:216-224`, `:135` | Web recalcula `finished`, revalida índice e `Math.max(0, lives)` que `applyMove` já faz | Redundante; contradiz `apps/web/src/server/play.ts:4-6` |
| `apps/web/src/components/Memeline.tsx:121` | `maxLives` com fallback `3` duplica `MAX_LIVES` | Redundante |
| `packages/ingest/src/cli/curation-queue.ts:110-111` | Lê locale de `process.argv[2]` sem `parseArgs`; raiz via `pathname.slice(1)` só funciona no Windows (resto usa `fileURLToPath`, `packages/ingest/src/config.ts:53`) | Provável bug em POSIX/CI |
| `packages/ingest/src/cli/curation-queue.ts:23-53` | Redefine `Audit`/`AuditItem` em vez de importar `PoolAudit` (`packages/ingest/src/pool.ts:69`) | Tipos podem divergir |
| `packages/ingest/src/cli/curation-queue.ts:77-86` | `CURÁVEL` omite `flag:series-edge` (pré-2015, `packages/ingest/src/peak.ts:358-367`) | Provável bug: contradiz o cabeçalho do arquivo |
| `packages/ingest/src/cli/peaks.ts:43-64`, `candidates.ts`, `build-pool.ts` | Top-level await sem catch; só `packages/ingest/src/cli/curation-queue.ts:177-180` define `exitCode` | Inconsistente |
| `packages/ingest/src/peak.ts:422-435` | `flat-series` é sobrescrito por métodos seguintes porque o `if` da `:426` inicia nova cadeia | Pode ser intencional; não documentado |
| `packages/ingest/src/peak.ts:127-131` | JSDoc de `baseConfidence` órfão, colado em `trailingMedian` | Resto de edição |
| `packages/ingest/src/pool.ts:151-159` vs `:191` | Audit de `fetch-error` usa slug do título pedido; caminho normal usa slug canônico | Mesmo meme com slugs diferentes entre rodadas |
| `packages/ingest/src/util/month.ts:4-9`, `:21` | Duplica `monthStamp`; `stamp % 12` diverge do core para negativos | Legado; comentário obsoleto |
| `tools/fetch-images.mjs:2`, `:17`, `:20`, `:30-32` | `User-Agent` `MemelineMock`/`example.org` fora da política de `packages/ingest/src/config.ts:19-20`; comentário diz 360px, código 260; `console.log("FALHA")` em vez de `console.error` | Script de protótipo |
| `apps/web/package.json:21` vs `packages/core/package.json:15` | Vitest `^3.2.7` no web e `^2.1.8` nos pacotes | Inconsistência de versão |
| `packages/core/src/index.ts:4-7`, `apps/web/src/app/page.tsx:21-22` | Comentários dizem que o core está "pendente" | Obsoletos |
| `apps/web/src/server/session.ts:111`, `apps/web/src/components/Flag.tsx:24`, `packages/ingest/src/util/http.ts:126`, `packages/core/src/types.ts:76` (`difficulty`), `packages/core/src/index.ts:301` (`recentIds`) | Exportados/definidos sem nenhum uso | Possível código morto |
