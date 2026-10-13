# Overview

## Hypothesis and beacons

**Hipótese (verificada):** monorepo TypeScript com npm workspaces em que `packages/core`
guarda as regras puras do jogo, `packages/ingest` é um pipeline CLI que gera o acervo
(JSON) e `apps/web` é um Next.js 15 (App Router) cuja UI React consome `@memeline/core`
e cujas rotas `/api/play/*` validam as jogadas no servidor com um token HMAC.

| Beacon expected | Found? | Evidence |
|---|---|---|
| `workspaces` apontando para `packages/*` e `apps/*` | sim | `package.json:6-9` |
| Regras puras exportadas de um único módulo (`createGame`, `applyMove`, `buildDeck`) | sim | `packages/core/src/index.ts:133`, `packages/core/src/index.ts:196`, `packages/core/src/index.ts:404` |
| Rotas de API Next.js `start`/`move`/`resume` com handler `POST` | sim | `apps/web/src/app/api/play/start/route.ts:17`, `apps/web/src/app/api/play/move/route.ts:17`, `apps/web/src/app/api/play/resume/route.ts:20` |
| Sessão assinada com HMAC no servidor | sim | `apps/web/src/server/session.ts:57`, `apps/web/src/server/session.ts:60`, `apps/web/src/server/session.ts:65` |
| Ingest como CLIs Node sem build step (`--experimental-strip-types`) | sim | `packages/ingest/package.json:9-12` |
| Direção de dependência `web → core`, `ingest → core`, nunca o contrário | sim | `apps/web/src/components/Memeline.tsx:35`, `packages/ingest/src/pool.ts:18`; nenhum import de `apps/web` em `packages/ingest/src` (só menções em comentários, `packages/ingest/src/cli/build-pool.ts:6`) |

## Repository shape

Resumo do `repo_skeleton.py` (67 arquivos, ~2 MB):

- Linguagens: TypeScript 45 arquivos (237 KB), JSON 11 (571 KB, principalmente
  `package-lock.json` e `apps/web/src/data/seed.us.json`), JavaScript 4 (672 KB, quase
  tudo `docs/memes-img.js`), Markdown 3, HTML 2 (protótipos em `docs/`), CSS 1.
- Diretórios de topo por número de arquivos: `packages` 28, `apps` 25, raiz 5, `docs` 5,
  `tools` 3.
- Arquivos mais centrais (in-degree no grafo de imports): `packages/core/src/index.ts`
  (5), `apps/web/src/server/play.ts` (5), `apps/web/src/server/http.ts` (3),
  `apps/web/src/server/rate-limit.ts` (3).
- Histórico: 10 commits, um único autor, todos em 2026-09-20 (ver `40-history.md`).

## Build, run, test

Só o que os manifests declaram; nada foi executado nesta sessão.

| Comando | O que faz | Status |
|---|---|---|
| `npm install` | instala os workspaces (`packages/*`, `apps/*`) na raiz | verificado em `package.json:6-9`; "pnpm NÃO está instalado" em `CLAUDE.md:48` |
| `npm test` | `vitest run` em cada workspace com script `test` | verificado em `package.json:15`, `packages/core/package.json:12`, `packages/ingest/package.json:7`, `apps/web/package.json:10` (unverified: se todos passam) |
| `npm run typecheck` | `tsc --noEmit` em todos | verificado em `package.json:16` |
| `npm run dev` | `next dev` em `apps/web`, escreve em `.next/` | verificado em `package.json:17`, `apps/web/package.json:6`; nota sobre `.next/` em `CLAUDE.md:63-65` |
| `npm run build` (web) | roda `tools/build-web.mjs`, que faz `next build` em `.next-prod/` | verificado em `apps/web/package.json:7`, `tools/build-web.mjs:1-20` (unverified: conteúdo exato do script não lido) |
| `npm run docs` | `node tools/serve.mjs`, serve `docs/` em `http://localhost:5173` | verificado em `package.json:18`, `CLAUDE.md:51` |
| `npm run candidates` / `peaks` / `build-pool` / `curation-queue` (em `packages/ingest`) | CLIs do pipeline via `node --experimental-strip-types` | verificado em `packages/ingest/package.json:9-12` |

Requisitos: Node `>=20` (`package.json:10-12`); `CLAUDE.md:57-58` diz que Node 23 roda
TypeScript direto. Vitest está em versões diferentes: `^2.1.8` em core/ingest
(`packages/core/package.json:15`) e `^3.2.7` em web (`apps/web/package.json:21`).

## Entry points

| Kind (http/cli/job/ui) | Name | path:line |
|---|---|---|
| http | `POST /api/play/start` | `apps/web/src/app/api/play/start/route.ts:17` |
| http | `POST /api/play/move` | `apps/web/src/app/api/play/move/route.ts:17` |
| http | `POST /api/play/resume` | `apps/web/src/app/api/play/resume/route.ts:20` |
| ui | página raiz (`Page`) e layout (`RootLayout`) | `apps/web/src/app/page.tsx:14`, `apps/web/src/app/layout.tsx:22` |
| ui | componente principal `Memeline` | `apps/web/src/components/Memeline.tsx:60` |
| cli | `candidates` | `packages/ingest/src/cli/candidates.ts:1` |
| cli | `peaks` | `packages/ingest/src/cli/peaks.ts:1` |
| cli | `build-pool` | `packages/ingest/src/cli/build-pool.ts:1` |
| cli | `curation-queue` (`main`) | `packages/ingest/src/cli/curation-queue.ts:109` |
| cli | servidor de preview dos protótipos | `tools/serve.mjs:1` |
| cli | build do web em `.next-prod/` | `tools/build-web.mjs:1` |
