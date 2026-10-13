# Memeline knowledge base

Memeline é um daily game de linha do tempo de memes: o jogador recebe uma carta por vez e
a encaixa pela data de viralização (mês/ano), com três vidas e um placar compartilhável
estilo Wordle (`CLAUDE.md:3-4`; o formato de placar vem do commit 54ce7c5). Monorepo TypeScript com npm workspaces
(`package.json:6-9`): regras puras em `packages/core`, pipeline de ingestão (Wikipedia,
Pageviews, Commons) em `packages/ingest`, e Next.js 15 App Router em `apps/web`.

**Architectural hypothesis (verified):** `packages/core` guarda as regras puras e o contrato
de tipos; `packages/ingest` é um conjunto de CLIs Node sem build que gera o acervo em JSON;
`apps/web` consome o core no servidor e valida cada jogada em `/api/play/*` com um token
HMAC stateless que carrega o `GameState` inteiro (`apps/web/src/server/session.ts:43`).

## Read next
- [Overview](00-overview.md) · [Glossary](10-glossary.md) · [Architecture](20-architecture.md)
- Flows: [start (SSR + /api/play/start + resume)](30-flows/start.md), [move (jogada)](30-flows/move.md), [ingest build-pool](30-flows/ingest-build-pool.md)
- [History and ownership](40-history.md) · [Conventions](50-conventions.md) · [Open questions](90-questions.md)

## Five things you would not guess from the code
1. O web ainda não lê o acervo gerado pelo ingest: `apps/web/src/server/pool.ts:16` importa
   `seed.us.json`; `out/pool.us.json` é a "troca de uma linha" futura (`apps/web/src/server/pool.ts:8`).
   Só a edição `us` existe; `br`/`global` dão 500 (`apps/web/src/server/pool.ts:62-65`).
2. Existem dois `puzzleId` para o mesmo puzzle: `"us:us-2026-10-12"` dentro do token
   (`packages/core/src/index.ts:460`) e `"us-2026-10-12"` na resposta (`apps/web/src/server/play.ts:81`).
   E o `/move` recalcula o id pelo dia UTC (`apps/web/src/server/play.ts:234`) enquanto o
   `/start` usa o dia local: perto da meia-noite no Brasil os ids divergem e o progresso se perde.
3. Os marcadores de acerto por carta existem só no cliente (`apps/web/src/lib/progress.ts:38`),
   porque `GameState.results` e `placedIds` têm ordens diferentes sem ligação
   (`packages/core/src/types.ts:117-123`; commit 3069964).
4. O core é TypeScript cru sem build (`packages/core/package.json:6-10`); por isso os imports
   internos usam `.ts` e todo workspace precisa de `allowImportingTsExtensions` (commit 72e51eb),
   e o Next precisa de `transpilePackages` + `extensionAlias` (`apps/web/next.config.ts:20-30`).
5. A Pageviews API só cobre jul/2015 em diante (`packages/ingest/src/config.ts:23-25`); 288 de
   531 candidatos caíam nisso e viraram a fila de curadoria (commit 67d9114), mas `CURÁVEL`
   omite `flag:series-edge` (`packages/ingest/src/cli/curation-queue.ts:77-86`). O impacto é parcial: `pool.ts` pega a primeira flag na ordem de push (`packages/ingest/src/pool.ts:213`) e `article-predates-data` entra antes de `series-edge` (`packages/ingest/src/peak.ts:350`, `packages/ingest/src/peak.ts:363`), então só os pré-2015 sinalizados apenas por `series-edge` (sem data de criação do artigo) somem da fila.

## Top open questions
1. O `puzzleId` do `/move` calculado por `utcDay` é bug? (`90-questions.md` #9)
2. "Jogar de novo" é modo treino ou furo do daily? (#10)
3. Um token antigo pode ser reenviado para desfazer um erro (sem nonce, 12 h)? (#12)
