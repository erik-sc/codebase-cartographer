# Question log

| # | Question | Conjecture | Status | Evidence |
|---|---|---|---|---|
| 1 | Onde está o ponto de entrada de uma partida? | SSR em `page.tsx` + rota `/api/play/start` | verified | `apps/web/src/app/page.tsx:19`, `apps/web/src/app/api/play/start/route.ts:17` |
| 2 | Onde a data de pico é escondida do cliente? | Whitelist `toClientCard` | verified | `packages/core/src/index.ts:268`, `packages/core/src/game.test.ts:236-244` |
| 3 | Como o servidor mantém o estado sem banco? | Token HMAC stateless com `GameState` dentro | verified | `apps/web/src/server/session.ts:43`, `apps/web/src/server/session.ts:60-65` |
| 4 | Qual é a sequência de chamadas de uma jogada? | ver `30-flows/move.md` | verified | `apps/web/src/server/play.ts:211-244`, `packages/core/src/index.ts:196-244` |
| 5 | Como o empate no mesmo mês conta como acerto? | Comparação inclusiva, não caso especial | verified | `packages/core/src/index.ts:122-123`, commit a6260ca |
| 6 | O web consome o `pool.<locale>.json` do ingest? | Não; ainda lê `seed.us.json` | verified | `apps/web/src/server/pool.ts:16`, `apps/web/src/server/pool.ts:8-10` |
| 7 | As edições `br`/`global` funcionam? | Não; lançam `[pool]` → 500 | verified | `apps/web/src/server/pool.ts:18-20`, `apps/web/src/server/pool.ts:62-65` |
| 8 | Por que `puzzleId` tem dois formatos (`us:us-2026-10-12` no token, `us-2026-10-12` na resposta)? | `buildDeck` prefixa `${edition}:` e o web passa `puzzleId` como seed; ninguém percebeu porque `resumeSession` extrai a data por regex | open | `packages/core/src/index.ts:460`, `apps/web/src/server/play.ts:81`, `apps/web/src/server/play.ts:186` |
| 9 | O `puzzleId` devolvido pelo `/move` (dia UTC) diverge do `/start` (dia local) perto da meia-noite local? Isso perde a partida em andamento e deixa rejogar o dia? | Sim, provável bug: deveria usar `before.puzzleId` | open | `apps/web/src/server/play.ts:234`, `apps/web/src/server/play.ts:149`, `apps/web/src/components/Memeline.tsx:177`, `apps/web/src/components/Memeline.tsx:205` |
| 10 | "Jogar de novo" (`restart`) é modo treino intencional ou furo do daily? | Furo: não manda `day`, não checa `findFinished`, e `recordFinish` sobrescreve o placar | open | `apps/web/src/components/Memeline.tsx:412-425`, `apps/web/src/lib/progress.ts:160-163`, `apps/web/src/components/Memeline.tsx:142-143` |
| 11 | Por que `shareText` roda no cliente se `protocol.ts` promete zero runtime do core no bundle? | Para incluir `streak` no share do "dia já concluído", que o servidor não conhece; o comentário ficou desatualizado | open | `apps/web/src/components/Memeline.tsx:35`, `apps/web/src/components/Memeline.tsx:189-196`, `apps/web/src/lib/protocol.ts:4-6` |
| 12 | Um token antigo pode ser reenviado para "desfazer" um erro? | Sim: não há nonce e a validade é 12 h | open | `apps/web/src/server/session.ts:41`, `apps/web/src/server/session.ts:92` |
| 13 | Como uma edição `global` montaria o pool se `MemeCard.locale` é só `us`/`br`? | Provavelmente união dos dois pools; não implementado | open | `packages/core/src/types.ts:12-13`, `packages/core/src/types.ts:55` |
| 14 | `curation-queue.ts` roda em Linux/CI? | Não: `pathname.slice(1)` só funciona no Windows | open | `packages/ingest/src/cli/curation-queue.ts:111`, `packages/ingest/src/config.ts:53` |
| 15 | Por que `CURÁVEL` não inclui `flag:series-edge`, se o objetivo da fila é resgatar os pré-2015? | Esquecimento; `series-edge` é justamente o sintoma de pré-2015 | open | `packages/ingest/src/cli/curation-queue.ts:77-86`, `packages/ingest/src/peak.ts:358-367` |
| 16 | O cache de 404 (`null`) do ingest expira? | Não; só `--refresh` invalida | verified (comportamento), open (intenção) | `packages/ingest/src/wikipedia.ts:233-245`, `packages/ingest/src/util/cache.ts:44-65` |
| 17 | `fetch-error` e `image:*` deveriam voltar para a fila de curadoria? | Provavelmente sim para `fetch-error` (transitório) | open | `packages/ingest/src/cli/curation-queue.ts:78-87` |
| 18 | Por que o core é TS cru sem build? | Para o ingest rodar com `--experimental-strip-types` | verified (documentado) | commit 72e51eb, `packages/core/package.json:6-10`, `CLAUDE.md:57-58` |
| 19 | Por que `.next-prod/` separado de `.next/`? | Build com dev no ar corrompia o cache | verified (documentado) | commit 54ce7c5, `apps/web/next.config.ts:11-18` |
| 20 | Por que os marcadores de acerto ficam no cliente? | `results` e `placedIds` têm ordens diferentes sem ligação | verified (documentado) | commit 3069964, `packages/core/src/types.ts:117-123` |
| 21 | Por que a Pageviews API e não Google Trends? | `pytrends` arquivado; Pageviews é pública e por idioma | verified (documentado) | `CLAUDE.md:25-28` |
| 22 | `DeckOptions.recentIds` (anti-repetição) é usado? | Não; o web nunca passa | verified | `packages/core/src/index.ts:301`, `apps/web/src/server/play.ts:152` |
| 23 | `MemeCard.difficulty` e `peakPrecision` são lidos em algum lugar? | Não (ingest só grava `"month"`) | verified | `packages/core/src/types.ts:76`, `packages/ingest/src/pool.ts:245` |
| 24 | Os testes passam? Quantos? | Commits dizem 89 (core) + 23 (ingest) + 19 (progress) | open (unverified) | commits a6260ca, 7a35429, 3069964; comando: `npm test` |
| 25 | O `[core]` → 501 em `failure()` deveria ser 500? | Sim; o core já não lança "não implementado" | open | `apps/web/src/server/http.ts:40-51`, `packages/core/src/index.ts:149` |
| 26 | Qual é a "metade" do MVP 3 que falta (commit 72e51eb)? | Ler `docs/MVPS.md` | open | commit 72e51eb, `docs/MVPS.md` |
| 27 | `toReveal` (pt fixo) deveria receber idioma para a edição `us`? | Sim quando a UI em inglês existir | open | `packages/core/src/index.ts:248-251`, `apps/web/src/server/play.ts:91` |
| 28 | Qual é uma primeira mudança segura? | Exportar `toReveal` do core e trocar `revealOf` por ele; verificar com `npm test` e `npm run typecheck` | open | `packages/core/src/index.ts:253`, `apps/web/src/server/play.ts:91-99` |
