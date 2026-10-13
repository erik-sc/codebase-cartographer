# Architecture (implemented)

## Layers and dependency direction

```
docs/ (protótipos HTML estáticos; servidos por tools/serve.mjs)

packages/core  ──(import type)──>  packages/ingest  ──(arquivo JSON, ainda não ligado)──>  apps/web
      ▲                                                                                      │
      └──────────────────────── import de valor (@memeline/core) ─────────────────────────────┘
```

- `packages/core` não depende de nada em runtime: nenhuma dependência além de `vitest` em dev
  (`packages/core/package.json:16-18`); internamente só `./types.ts` (`packages/core/src/index.ts:13-16`).
  É publicado como TypeScript cru: `main`, `types` e `exports` apontam para `./src/index.ts`
  (`packages/core/package.json:6-10`).
- `packages/ingest` importa do core **só tipos** (`import type`): `MonthStamp` em
  `packages/ingest/src/wikipedia.ts:10`, `packages/ingest/src/pageviews.ts:15`,
  `packages/ingest/src/peak.ts:29`, `packages/ingest/src/util/month.ts:12`; `Locale` em
  `packages/ingest/src/config.ts:12`; `MemeAttribution`/`MemeImage` em `packages/ingest/src/commons.ts:22`;
  `Locale`/`MemeCard`/`MemeSource` em `packages/ingest/src/pool.ts:18`; `MemeCard` em
  `packages/ingest/src/cli/build-pool.ts:30`. Ninguém importa `@memeline/ingest`.
- `apps/web` importa valores do core no servidor (`applyMove`, `buildDeck`, `createGame`,
  `DECK_SIZE`, `formatMonth`, `MAX_LIVES`, `shareText`, `toClientCard`,
  `apps/web/src/server/play.ts:10-19`) e um valor no cliente (`shareText`,
  `apps/web/src/components/Memeline.tsx:35`). Precisa de `transpilePackages: ["@memeline/core"]`
  (`apps/web/next.config.ts:20`) e de `extensionAlias` `.js→.ts` (`apps/web/next.config.ts:24-30`).
- A regra `web → core`, `ingest → core`, nunca o contrário (`CLAUDE.md:44`) é respeitada: nenhum
  import de `apps/web` dentro de `packages/ingest/src` (só menções em comentários,
  `packages/ingest/src/cli/build-pool.ts:6`, `packages/ingest/src/pool.ts:4`).

Dentro de `apps/web`:

- `src/server/*` roda só no servidor e é o dono do acervo, porque `peak` é a resposta
  (`apps/web/src/server/pool.ts:4-6`).
- `src/lib/protocol.ts` só tem tipos, importados com `import type` (`apps/web/src/lib/protocol.ts:4-6`).
- `src/lib/progress.ts` e `src/lib/sfx.ts` são só de cliente e protegem `window` com try/catch.
- `src/components/*` é UI `"use client"` (`apps/web/src/components/Memeline.tsx:1`,
  `apps/web/src/components/Scorecard.tsx:1`, `apps/web/src/components/CreditsWindow.tsx:1`).
- Grafo interno: `page.tsx` → `server/play`, `server/pool`, `components/Memeline`
  (`apps/web/src/app/page.tsx:1-4`); rotas → `server/http`, `server/play`, `server/rate-limit`;
  `http.ts` → `play.ts` e `session.ts` (`apps/web/src/server/http.ts:9-10`); `play.ts` → `pool`,
  `session`, `lib/protocol` (`apps/web/src/server/play.ts:22-24`); `Memeline` → `lib/progress`,
  `lib/protocol` (type), `lib/sfx`, `lib/facts` (`apps/web/src/components/Memeline.tsx:14-36`).

## Modules

| Module | Responsibility | Public surface | Depends on | Depended on by | Evidence |
|---|---|---|---|---|---|
| `packages/core/src/types.ts` | Contrato compartilhado: `MemeCard`, `ClientCard`, `GameState`, `Deck`, `MoveOutcome`, `Locale`, `Edition`, `MAX_LIVES`, `DECK_SIZE` | tudo re-exportado por `packages/core/src/index.ts:18` | nada | ingest (tipos), web (tipos e valores) | `packages/core/src/types.ts:12-136` |
| `packages/core/src/index.ts` | Regras puras: `monthStamp`/`monthFromStamp`/`formatMonth`, `isCorrectPlacement`, `createGame`, `applyMove`, `toClientCard`, `buildDeck`, `shareText` | `packages/core/src/index.ts:40`, `:57`, `:68`, `:98`, `:133`, `:196`, `:268`, `:404`, `:482` | `./types.ts` | `apps/web/src/server/play.ts:10-19`, `apps/web/src/components/Memeline.tsx:35` | privadas: `safeTolerance` `:85`, `requireCard` `:146`, `resolvePlacementIndex` `:167`, `toReveal` `:253`, `hashSeed` `:314`, `mulberry32` `:337`, `pickAnchor` `:384` |
| `packages/ingest/src/wikipedia.ts` | Candidatos por categoria/Wikidata e metadados do artigo | `listCandidates` `:98`, `listCandidatesFromWikidata` `:145`, `fetchArticleInfo` `:216` | `util/cache`, `util/http` (`packages/ingest/src/wikipedia.ts:7-8`) | `pool.ts`, CLIs | MediaWiki Action API (`packages/ingest/src/wikipedia.ts:14`), SPARQL (`packages/ingest/src/wikipedia.ts:155`) |
| `packages/ingest/src/pageviews.ts` | Série mensal de pageviews com meses vazios preenchidos | `fetchMonthlySeries` `:71`, `lastClosedMonth` `:47` | `util/cache`, `util/http` (`packages/ingest/src/pageviews.ts:11-12`) | `pool.ts`, `cli/peaks.ts` | REST em `wikimedia.org/api/rest_v1` (`packages/ingest/src/pageviews.ts:17`) |
| `packages/ingest/src/peak.ts` | Detecção do primeiro pico proeminente, flags, confiança, notoriedade | `detectPeak` `:151`, `smooth` `:104`, `estimateNotoriety` `:461`, tipos `PeakDetection` `:54`, `PeakFlag` `:41`, `PeakMethod` `:32` | `@memeline/core` (type) | `pool.ts`, `cli/peaks.ts`, `peak.test.ts` | único módulo do ingest com testes (`packages/ingest/src/peak.test.ts`) |
| `packages/ingest/src/commons.ts` | Thumbnail, autor e licença no Commons; rejeições como valores | `fetchCommonsImage` `:93`, `stripHtml` `:51`, `CommonsLookup` `:78`, `ImageRejection` `:72` | `util/cache`, `util/http` (`packages/ingest/src/commons.ts:20-21`) | `pool.ts` | Commons API (`packages/ingest/src/commons.ts:24`) |
| `packages/ingest/src/pool.ts` | Orquestra artigo → pageviews → pico → imagem → `MemeCard` + `PoolAudit` | `buildCard` `:147`, `buildCardStrict` `:174`, `toleranceFor` `:109`, `PoolAudit` `:69`, `RejectionReason` `:20` | commons, peak, pageviews, wikipedia (`packages/ingest/src/pool.ts:11-17`) | `packages/ingest/src/cli/build-pool.ts:52` | |
| `packages/ingest/src/util/{http,cache,concurrency,month,slug}.ts` | Camada HTTP com pacing/retry, cache em disco, `mapLimit`, utilitários de mês e slug | `fetchJson` `packages/ingest/src/util/http.ts:87`, `cached` `packages/ingest/src/util/cache.ts:44`, `mapLimit` `packages/ingest/src/util/concurrency.ts:11` | `config.ts` (`packages/ingest/src/util/http.ts:10`, `packages/ingest/src/util/cache.ts:17`) | clientes de API e CLIs | `fetchBuffer` (`packages/ingest/src/util/http.ts:126`) sem chamador |
| `packages/ingest/src/cli/*.ts` | `candidates` → `build-pool` → `curation-queue`; `peaks` é diagnóstico | scripts em `packages/ingest/package.json:9-12` | tudo acima | ninguém (saída em `out/*.json`) | ver `30-flows/ingest-build-pool.md` |
| `apps/web/src/server/play.ts` | Orquestração da partida: `startSession`, `resumeSession`, `applyPlayerMove`, `PlayError` | `:147`, `:174`, `:211`, `:26` | core, `pool`, `session`, `lib/protocol` (`apps/web/src/server/play.ts:22-24`) | rotas, `page.tsx`, `http.ts` | |
| `apps/web/src/server/session.ts` | Token stateless `payload.mac` HMAC-SHA256, 12 h | `signSession` `:60`, `verifySession` `:65`, `SessionError` `:50`, `editionOf` `:111` | `node:crypto` (`apps/web/src/server/session.ts:14`) | `play.ts`, `http.ts` | `editionOf` sem uso |
| `apps/web/src/server/pool.ts` | Acervo validado e em cache; créditos | `getPool` `:57`, `getCardIndex` `:73`, `requireCard` `:84`, `listCredits` `:94` | `@/data/seed.us.json` (`apps/web/src/server/pool.ts:16`) | `play.ts`, `page.tsx` | só `us` (`apps/web/src/server/pool.ts:18-20`) |
| `apps/web/src/server/http.ts` | Cola das rotas: `readBody`, `parseEdition`, `fail`, `failure` (erro → status) | `:14`, `:27`, `:34`, `:44` | `play.ts`, `session.ts` (`apps/web/src/server/http.ts:9-10`) | 3 rotas | |
| `apps/web/src/server/rate-limit.ts` | Janela deslizante em memória, 90 req/60 s por IP | `isRateLimited` `:37`, `callerKey` `:27` | nada | 3 rotas | por instância (`apps/web/src/server/rate-limit.ts:4-7`) |
| `apps/web/src/app/api/play/{start,move,resume}/route.ts` | Handlers `POST` | `apps/web/src/app/api/play/start/route.ts:17`, `apps/web/src/app/api/play/move/route.ts:17`, `apps/web/src/app/api/play/resume/route.ts:20` | `server/*` | cliente via `fetch` | mesmo esqueleto nas três |
| `apps/web/src/lib/protocol.ts` | Tipos de fio: `SessionCore`, `StartResponse`, `MoveResponse`, `ApiError`, `CreditEntry` | `:15`, `:36`, `:41`, `:48`, `:56` | core (type) | servidor e cliente | |
| `apps/web/src/lib/progress.ts` | Progresso por aparelho em `localStorage` (`memeline:progress:v1`): in-progress, histórico, streak | `localDay` `:68` … `getStreak` `:177` | core (type) | `Memeline.tsx` | testado em `apps/web/src/lib/progress.test.ts` |
| `apps/web/src/lib/{sfx,facts}.ts` | Sons sintetizados por Web Audio; textos do placar | `sfx` `apps/web/src/lib/sfx.ts:103`; `FACTS` `apps/web/src/lib/facts.ts:8`, `scoreLabel` `apps/web/src/lib/facts.ts:34`, `pickFact` `apps/web/src/lib/facts.ts:39` | nada | `Memeline.tsx`, `Scorecard.tsx` | `localStorage` `memeline-snd` (`apps/web/src/lib/sfx.ts:12`) |
| `apps/web/src/components/*` | UI Win98: `Memeline` (936 linhas), `Scorecard`, `CreditsWindow`, `Flag` | `apps/web/src/components/Memeline.tsx:60`, `apps/web/src/components/Scorecard.tsx:15`, `apps/web/src/components/CreditsWindow.tsx:9`, `apps/web/src/components/Flag.tsx:12` | `lib/*`, core (`shareText`) | `page.tsx` | `editionName` (`apps/web/src/components/Flag.tsx:24`) sem uso |
| `tools/*.mjs` | `serve.mjs` (docs estáticos, porta 5173), `build-web.mjs` (`next build` em `.next-prod`), `fetch-images.mjs` | | | scripts npm | `tools/build-web.mjs:14-20`, `tools/serve.mjs:9` |

## Data stores and external services

- **Sem banco de dados.** O estado da partida viaja inteiro no token HMAC
  (`apps/web/src/server/session.ts:43`, `apps/web/src/server/session.ts:56-63`); o servidor
  só tem caches de módulo (`apps/web/src/server/pool.ts:53-54`) e o mapa de rate limit
  (`apps/web/src/server/rate-limit.ts:13`).
- **Acervo:** `apps/web/src/data/seed.us.json`, importado estaticamente
  (`apps/web/src/server/pool.ts:16`). O pipeline gera `packages/ingest/out/pool.<locale>.json`
  (`packages/ingest/src/cli/build-pool.ts:71-83`), mas o web ainda não o lê
  (`apps/web/src/server/pool.ts:8-10` descreve a troca futura).
- **Cliente:** `localStorage` `memeline:progress:v1` (`apps/web/src/lib/progress.ts:24`) e
  `memeline-snd` (`apps/web/src/lib/sfx.ts:12`).
- **Ingest, cache em disco:** `packages/ingest/.cache/<namespace>/<key>.<sha1-10>.json`
  (`packages/ingest/src/util/cache.ts:26-30`), sem expiração.
- **Serviços externos (só o ingest):** MediaWiki Action API (`packages/ingest/src/wikipedia.ts:14`),
  Wikidata SPARQL (`packages/ingest/src/wikipedia.ts:155`), Wikimedia Pageviews REST
  (`packages/ingest/src/pageviews.ts:17`), Commons API (`packages/ingest/src/commons.ts:24`).
  Pacing por host em `packages/ingest/src/config.ts:42-48`; `User-Agent` em
  `packages/ingest/src/config.ts:19`.
- **Env vars:** só quatro leituras no repo: `MEMELINE_SESSION_SECRET`
  (`apps/web/src/server/session.ts:28`), `NODE_ENV` (`apps/web/src/server/session.ts:30`),
  `NEXT_DIST_DIR` (`apps/web/next.config.ts:19`), `PORT` (`tools/serve.mjs:9`).

## Boundaries and seams

- **Fronteira de segurança:** `toClientCard` (`packages/core/src/index.ts:268`) é a whitelist
  que impede `peak` e `fact` de chegarem ao cliente; `listCredits`
  (`apps/web/src/server/pool.ts:94`) faz o mesmo para créditos.
- **Seam core ↔ web:** `applyPlayerMove` valida índice/fim de partida antes de chamar
  `applyMove` (`apps/web/src/server/play.ts:216-227` vs `packages/core/src/index.ts:202-218`),
  e `revealOf` (`apps/web/src/server/play.ts:91`) duplica `toReveal` privado do core
  (`packages/core/src/index.ts:253`). Candidato a exportar `toReveal`.
- **Seam ingest ↔ web:** a "troca de uma linha" de `seed.us.json` por `out/pool.us.json`
  (`apps/web/src/server/pool.ts:8`). Sem teste de contrato entre o JSON gerado e `MemeCard`.
- **Seam servidor ↔ cliente:** os marcadores de acerto por carta (`marks`) existem só no
  cliente (`apps/web/src/lib/progress.ts:29`), porque `GameState` não liga `results` a
  `placedIds` (`packages/core/src/types.ts:117-123`).
- **Utilitários de mês duplicados:** `packages/ingest/src/util/month.ts:4-9` reimplementa
  `monthStamp` alegando que o core "ainda lança 'não implementado'", o que já não é verdade;
  `monthParts` usa `stamp % 12` (`packages/ingest/src/util/month.ts:21`), diferente do
  `Math.floor` do core para stamps negativos.

## Where implemented differs from documented

| Documentado | Implementado | Evidência |
|---|---|---|
| `CLAUDE.md:7` e `packages/core/src/types.ts:13`: edições USA, BR e Global | Só `us` tem acervo; `br`/`global` lançam `[pool]` e viram 500 | `apps/web/src/server/pool.ts:18-20`, `apps/web/src/server/pool.ts:62-65`, `apps/web/src/server/http.ts:12` |
| `apps/web/src/lib/protocol.ts:4-6`: nenhum runtime do core chega ao bundle | `shareText` importado em runtime no cliente | `apps/web/src/components/Memeline.tsx:35`, `apps/web/src/components/Memeline.tsx:189` |
| `apps/web/src/components/Scorecard.tsx:51-52`: "o cliente não remonta a string" de share | Remonta no caminho "dia já concluído", com `streak` | `apps/web/src/components/Memeline.tsx:189-196` |
| `apps/web/src/server/play.ts:86-90`: `revealOf` "só é chamado para a âncora" | Também no resume | `apps/web/src/server/play.ts:199` |
| `packages/core/src/index.ts:4-7`, `apps/web/src/app/page.tsx:21-22`, `packages/ingest/src/util/month.ts:7`, `apps/web/src/server/http.ts:40-51`: core "pendente"/"não implementado" | Core totalmente implementado; o mapeamento `[core]` → 501 agora captura violações de invariante | `packages/core/src/index.ts:149`, `packages/core/src/index.ts:203`, `packages/core/src/index.ts:409` |
| `packages/ingest/src/cli/curation-queue.ts:11-14`: resgatar os memes pré-2015 | `CURÁVEL` não inclui `flag:series-edge`, que é o sintoma de pré-2015 | `packages/ingest/src/cli/curation-queue.ts:77-86`, `packages/ingest/src/pool.ts:45-54`, `packages/ingest/src/peak.ts:358-367` |
| `docs/PLANO.md:222`: PostHog para feature flags | Nenhum uso no código | grep `posthog` vazio em `*.ts/tsx/mjs` |
| `packages/ingest/src/config.ts:36-42`: comentário cita 120 ms | Padrão real `REQUEST_INTERVAL_MS = 150` | `packages/ingest/src/config.ts:42-48` |
