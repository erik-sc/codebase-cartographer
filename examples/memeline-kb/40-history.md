# History and ownership

Fonte: `git log` / `git shortlog` (10 commits, 1 autor, todos datados de 2026-09-20).
Como o histórico é curto e cada commit tem mensagem longa em prosa, quase toda a
razão de ser do código está *documentada* nos commits; pouca coisa precisou ser inferida.

## Timeline of structural decisions

| When | What | Why (documented / inferred) | Evidence (commit) |
|---|---|---|---|
| 2026-09-20 | Scaffold do monorepo: `packages/core/src/types.ts` como contrato, npm workspaces, `CLAUDE.md` com regras de ouro, protótipos HTML em `docs/` | documentado: "contrato de tipos, workspaces e regras do projeto" | commit 9a5011a |
| 2026-09-20 | Roadmap de MVPs em `docs/MVPS.md` | documentado | commit eea14fc |
| 2026-09-20 | Regras do jogo no core com 89 testes: empate e tolerância por comparação inclusiva, partida imutável, deck determinístico via mulberry32, share-card | documentado: "A regra de empate sai de usar comparacao inclusiva, nao de um caso especial" | commit a6260ca |
| 2026-09-20 | MVP 1 jogável: Next 15 App Router, rotas `/api/play/start` e `/move`, acervo com datas só no servidor, estado assinado com HMAC (token adulterado devolve 401); ingest com cliente Pageviews, cache, detecção de primeiro pico proeminente e CLI do pool (23 testes) | documentado | commit 7a35429 |
| 2026-09-20 | `curation-queue`: rejeições pré-2015 viram fila de trabalho priorizada | documentado: Pageviews API só cobre jul/2015 em diante; 288 de 531 candidatos caíam nesse caso e "sao justamente a parte nostalgica do acervo" | commit 67d9114 |
| 2026-09-20 | Rota `/api/play/resume` e `apps/web/src/lib/progress.ts` (localStorage): partida retomada ao recarregar; sequência por dia LOCAL | documentado: recarregar dava segunda chance no mesmo puzzle; cliente guarda só o token (690 bytes) porque as cartas com imagem em data URI encheriam o localStorage | commit 3069964 |
| 2026-09-20 | Daily fecha pelo dia LOCAL do jogador com janela ±1 dia em torno do UTC; UI enxuta (sem botão de nova partida); `next build` passa a escrever em `.next-prod/` via `tools/build-web.mjs` | documentado: puzzle virava às 21h no Brasil; build com dev no ar corrompia o cache | commit 54ce7c5 |
| 2026-09-20 | Animação de volta da carta via Web Animations API; `reportError` limpa estado | documentado: dependência da ordem de render fazia a carta saltar | commit 74981ee |
| 2026-09-20 | Imports internos do core passam a usar extensão `.ts`; `allowImportingTsExtensions` sobe para `tsconfig.base.json` | documentado: core é publicado como TS cru para `--experimental-strip-types`; imports `.js` davam `ERR_MODULE_NOT_FOUND`; o ingest só não quebrava porque seus oito imports do core são `import type` | commit 72e51eb |
| 2026-09-20 | Correção de texto corrompido em `docs/MVPS.md` | documentado | commit 5a95356 |

## Hotspots (churn)

Do `repo_skeleton.py` (commits que tocam o arquivo):

| path | commits | o que continua mudando |
|---|---|---|
| `docs/MVPS.md` | 4 | registro de revisão dos MVPs (commits eea14fc, 3069964, 72e51eb, 5a95356) |
| `apps/web/src/components/Memeline.tsx` | 4 | drag & drop, animação de volta, retomada, daily fechado (commits 7a35429, 3069964, 54ce7c5, 74981ee) |
| `apps/web/src/server/play.ts` | 3 | resolução do dia, resume (commits 7a35429, 3069964, 54ce7c5) |
| `apps/web/src/components/Scorecard.tsx` | 3 | commits 7a35429, 3069964, 54ce7c5 |
| `apps/web/src/app/globals.css` | 3 | commits 7a35429, 54ce7c5, 74981ee |
| `apps/web/package.json` | 3 | commits 9a5011a, 3069964, 54ce7c5 |

Leitura: a parte que mais muda é a experiência de jogo no cliente (`Memeline.tsx`) e a
lógica de dia/sessão (`play.ts`). O core mudou uma vez depois de nascer (commit 72e51eb,
só extensões de import). O ingest nunca foi alterado depois do commit 7a35429, exceto pela
adição de `curation-queue.ts` (commit 67d9114).

## Ownership concentration (truck factor)

| Area | Main author(s) | Risk |
|---|---|---|
| Todo o repositório | Érik S. (10 de 10 commits, `git shortlog -sn`) | Truck factor 1 em tudo. O que mitiga é a densidade das mensagens de commit e dos comentários em prosa (`CLAUDE.md:61`). |
| `apps/web/src/components/Memeline.tsx` | Érik S. | 936 linhas, 4 commits, muitos detalhes de timing de render documentados só em commits 54ce7c5 e 74981ee |
| `packages/ingest/src/peak.ts` | Érik S. | heurísticas de pico (ressurgimento, artigo tardio, pré-2015) com 1 commit; a razão está em comentários e em `docs/PLANO.md` §5.4 (`packages/ingest/src/peak.ts:214`) |

## Candidate ADRs (inferred, not documented)

Quase tudo abaixo está documentado em commit ou no `CLAUDE.md`; marco como inferido só
o que precisou de reconstrução.

1. **Validação server-side com token HMAC stateless em vez de banco de sessões.**
   Contexto: regra de ouro 3 (`CLAUDE.md:17-20`), "o cliente nunca recebe a data".
   Decisão: estado inteiro da partida assinado e devolvido ao cliente (commit 7a35429).
   Consequências: sem persistência no servidor; o cliente carrega o token no localStorage
   (commit 3069964). *Inferido:* a escolha de stateless parece motivada por não ter
   banco no MVP 1; nenhum commit diz isso explicitamente.
2. **Core publicado como TypeScript cru, sem build.** Documentado em commit 72e51eb e
   `CLAUDE.md:59-60`. Consequência: todos os workspaces precisam de
   `allowImportingTsExtensions` (`tsconfig.base.json`, commit 72e51eb).
3. **Dia do puzzle = dia local do cliente com janela ±1 em torno do UTC.** Documentado
   em commit 54ce7c5 ("como no Wordle"). *Inferido:* a janela de ±1 é um compromisso
   entre fusos reais e não deixar puxar puzzles futuros; o valor exato não tem teste
   citado no commit (ver `90-questions.md`).
4. **Marcadores de acerto ficam no cliente.** Documentado em commit 3069964: o servidor
   não consegue reconstruí-los porque `results` e `placedIds` têm ordens diferentes
   (`packages/core/src/types.ts:117-123`). *Inferido:* é dívida consciente; um campo de
   ligação no `GameState` resolveria.
5. **Fila de curadoria em vez de descarte.** Documentado em commit 67d9114.
6. **Build separado de dev (`.next-prod/`).** Documentado em commit 54ce7c5 e
   `CLAUDE.md:63-65`.

## Abandoned or reverted approaches

- Nenhum revert no histórico (`git log` sem commits "revert"; 10 commits lineares).
- Animação da volta da carta por classe CSS + `setReturning(true)` foi substituída pela
  Web Animations API (commit 74981ee).
- Botão de "nova partida" removido porque furava o daily (commit 54ce7c5).
- Imports internos `.js` no core abandonados em favor de `.ts` (commit 72e51eb).

## Open questions only a human can answer

- Há um repositório anterior ou protótipo fora do git? O commit 9a5011a já chega com
  `docs/partida.html` (997 linhas) e `docs/theme.html` (882 linhas) prontos.
- O MVP 3 "pela metade" mencionado em commit 72e51eb: qual metade falta?
