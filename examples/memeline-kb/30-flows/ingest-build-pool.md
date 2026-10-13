# Flow: ingest build-pool (candidatos → pool.<locale>.json + auditoria)

Trigger: `npm run build-pool` em `packages/ingest`, que roda
`node --experimental-strip-types src/cli/build-pool.ts` (`packages/ingest/package.json:12`).
O script é ESM com top-level await, sem `main()`; a execução começa em
`packages/ingest/src/cli/build-pool.ts:32`.

Confiança: alta (todos os hops lidos; nada executado).

1. Parse de argv: `parseArgs(process.argv.slice(2))` — `packages/ingest/src/cli/build-pool.ts:32` → `packages/ingest/src/cli/args.ts:17`. Aceita `--k v`, `--k=v` e flag nua; `args.number` cai no fallback se o valor não é finito (`packages/ingest/src/cli/args.ts:47-51`).
2. Locale: `readLocale(args)` — `packages/ingest/src/cli/build-pool.ts:33` → `packages/ingest/src/cli/args.ts:56`; lança `Error` para valor fora de `us`/`br`. Lê ainda `refresh`, `limit` (default Infinity), `min-confidence` (50) e `concurrency` (5) — `packages/ingest/src/cli/build-pool.ts:34-37`.
3. Entrada: sem títulos posicionais, lê `OUT_DIR/candidates.<locale>.json` (campo `titles`) — `packages/ingest/src/cli/build-pool.ts:40-45`; `OUT_DIR` = `packages/ingest/out` — `packages/ingest/src/config.ts:56-58`. Aplica `slice(0, limit)` — `packages/ingest/src/cli/build-pool.ts:46`.
4. Fan-out: `mapLimit(titles, concurrency, …)` — `packages/ingest/src/cli/build-pool.ts:51` → `packages/ingest/src/util/concurrency.ts:11` (N runners sobre um cursor compartilhado, ordem preservada).
5. Por título: `buildCard(title, {locale, refresh, minConfidence})` — `packages/ingest/src/cli/build-pool.ts:52` → `packages/ingest/src/pool.ts:147`, wrapper tolerante a falha que chama `buildCardStrict` (`packages/ingest/src/pool.ts:149` → `packages/ingest/src/pool.ts:174`).
6. Metadados do artigo: `fetchArticleInfo(project, title, {refresh})` — `packages/ingest/src/pool.ts:180` → `packages/ingest/src/wikipedia.ts:216` (Action API com `redirects=1`, `pageimages`, `pageprops=disambiguation`, primeira revisão). Projeto vem de `PROJECT_BY_LOCALE` — `packages/ingest/src/config.ts:28-31`. Artigo `missing` → rejeição `article-missing` (`packages/ingest/src/pool.ts:183`); desambiguação → `disambiguation` (`packages/ingest/src/pool.ts:186`).
7. Cache em disco (plumbing): `cached("article/<project>", title, …)` — `packages/ingest/src/wikipedia.ts:233` → `packages/ingest/src/util/cache.ts:44`. Arquivo `CACHE_DIR/<namespace>/<key>.<sha1[0:10]>.json` (`packages/ingest/src/util/cache.ts:26-30`); só vai à rede sem cache ou com `refresh` (`packages/ingest/src/util/cache.ts:52-65`).
8. HTTP (plumbing): `fetchJson` — `packages/ingest/src/wikipedia.ts:238` → `packages/ingest/src/util/http.ts:87`. Antes de cada tentativa chama `pace(url)` (`packages/ingest/src/util/http.ts:92` → `packages/ingest/src/util/http.ts:54`), que serializa por host: 400 ms para wikipedia/commons, 150 ms por default (`packages/ingest/src/config.ts:42-48`), e respeita `cooldownUntil` após 429. `User-Agent` em `packages/ingest/src/config.ts:19`. O fluxo sai do repositório no `fetch` — `packages/ingest/src/util/http.ts:94`.
9. Série de pageviews: `fetchMonthlySeries(project, article.title, {refresh})` — `packages/ingest/src/pool.ts:189` → `packages/ingest/src/pageviews.ts:71`. Janela de `DATA_WINDOW_START` (jul/2015, `packages/ingest/src/config.ts:23-25`) até `lastClosedMonth()` (`packages/ingest/src/pageviews.ts:47`); `/` no título vira `%252F` (`packages/ingest/src/pageviews.ts:56-58`). Usa `cached("pageviews/<project>", …)` (`packages/ingest/src/pageviews.ts:81`) e `fetchJson` (`packages/ingest/src/pageviews.ts:86`). Meses sem dado viram 0 (`packages/ingest/src/pageviews.ts:109-115`). A série é arquivada na auditoria via `archive()` (`packages/ingest/src/pool.ts:115`, chamada em `packages/ingest/src/pool.ts:190`). Série ausente/vazia → `no-pageviews` (`packages/ingest/src/pool.ts:193-195`).
10. Detecção de pico: `detectPeak({points, articleCreated})` — `packages/ingest/src/pool.ts:197` → `packages/ingest/src/peak.ts:151`. Suavização [1,2,1] (`packages/ingest/src/peak.ts:104`), proeminência 0.6 e mínimo de 3000 views (`packages/ingest/src/peak.ts:87-90`), confiança base (`packages/ingest/src/peak.ts:141`), flags (`packages/ingest/src/peak.ts:291-403`), cada flag impõe teto de confiança (`packages/ingest/src/peak.ts:411-418`), `needsManualReview = confidence < 70 || flags.length > 0` (`packages/ingest/src/peak.ts:441`). `estimateNotoriety` (`packages/ingest/src/pool.ts:199` → `packages/ingest/src/peak.ts:461`) = `20*log10(mediana)` limitado a 0..100. `stamp === null` → `no-peak` (`packages/ingest/src/pool.ts:201`).
11. Imagem: sem `article.pageImage` → `no-page-image` (`packages/ingest/src/pool.ts:204`). Com imagem, `fetchCommonsImage(article.pageImage, {refresh})` — `packages/ingest/src/pool.ts:206` → `packages/ingest/src/commons.ts:93`: `cached("commons", …)` (`packages/ingest/src/commons.ts:111`) e `fetchJson` (`packages/ingest/src/commons.ts:114`). Rejeita `not-on-commons`, `no-thumbnail`, `no-author`, `no-license` (`packages/ingest/src/commons.ts:119-138`) → `image:<motivo>` (`packages/ingest/src/pool.ts:207`).
12. Corte: primeira flag de `BLOCKING_FLAGS` (`packages/ingest/src/pool.ts:45-54`) → `flag:<x>` (`packages/ingest/src/pool.ts:213-214`); abaixo de `minConfidence` → `low-confidence` (`packages/ingest/src/pool.ts:215`).
13. Montagem do `MemeCard`: duas `sources` (pageviews + wikipedia), `toleranceMonths` via `toleranceFor` (`packages/ingest/src/pool.ts:109`: ≥80 → 0, ≥65 → 1, senão 2), `fact: ""`, `id = <locale>-<slug>`, retorno com `accepted: true` — `packages/ingest/src/pool.ts:217-256`.
14. Agregação: separa `cards` e `audits`, ordena cards por `peak` e `slug`, audits por `slug` — `packages/ingest/src/cli/build-pool.ts:58-69`.
15. Persistência (terminal): `mkdir(OUT_DIR)` e `writeFile` de `out/pool.<locale>.json` (array de `MemeCard`) e `out/pool.<locale>.audit.json` (`{locale, generatedAt, minConfidence, candidates, items}`) — `packages/ingest/src/cli/build-pool.ts:71-83`.
16. Relatório no console: contagem por motivo, por `detection.method` e por `needsManualReview`, mais aviso fixo de que o pool não é o deck — `packages/ingest/src/cli/build-pool.ts:89-129`.

## CLIs irmãos e encadeamento

- `candidates.ts`: `listCandidates` por categoria ou `listCandidatesFromWikidata` (`packages/ingest/src/wikipedia.ts:98` / `packages/ingest/src/wikipedia.ts:145`), escolhidos com `--source category|wikidata|both`; escreve `out/candidates.<locale>.json` (`packages/ingest/src/cli/candidates.ts:47-54`).
- `peaks.ts`: só diagnóstico, não escreve arquivo; lê `out/candidates.<locale>.json` (`packages/ingest/src/cli/peaks.ts:36-37`) e roda `fetchMonthlySeries` (`packages/ingest/src/cli/peaks.ts:47`) → `detectPeak` (`packages/ingest/src/cli/peaks.ts:50`).
- `curation-queue.ts`: lê `out/pool.<locale>.audit.json` (`packages/ingest/src/cli/curation-queue.ts:112-115`), filtra rejeições em `CURÁVEL` (`packages/ingest/src/cli/curation-queue.ts:78-87`), ordena por `priority()` (`packages/ingest/src/cli/curation-queue.ts:101`) e escreve `out/curation-queue.<locale>.json` (`packages/ingest/src/cli/curation-queue.ts:142-157`). Não usa `args.ts`: locale vem de `process.argv[2]` (`packages/ingest/src/cli/curation-queue.ts:110`).
- Cadeia real: `candidates → build-pool → curation-queue`; `peaks` é ramo lateral.
- Consumidor: `apps/web/src/server/pool.ts:8-20` ainda importa `@/data/seed.us.json`; `out/pool.us.json` é o alvo futuro ("troca de uma linha", `apps/web/src/server/pool.ts:8`).

## Shared hops (used by other flows too)

- `cached` (`packages/ingest/src/util/cache.ts:44`): 5 chamadores — `packages/ingest/src/commons.ts:111`, `packages/ingest/src/pageviews.ts:81`, `packages/ingest/src/wikipedia.ts:69`, `packages/ingest/src/wikipedia.ts:157`, `packages/ingest/src/wikipedia.ts:233`.
- `fetchJson` (`packages/ingest/src/util/http.ts:87`): 5 chamadores (mesmos arquivos). `fetchBuffer` (`packages/ingest/src/util/http.ts:126`) não tem chamador neste fluxo.
- `mapLimit`: `packages/ingest/src/cli/build-pool.ts:51` e `packages/ingest/src/cli/peaks.ts:24`.
- `buildCard`: um único chamador, `packages/ingest/src/cli/build-pool.ts:52`.

## State touched

- Lê `packages/ingest/out/candidates.<locale>.json`.
- Escreve `packages/ingest/out/pool.<locale>.json` e `packages/ingest/out/pool.<locale>.audit.json`.
- Cache `packages/ingest/.cache/{article/<project>, pageviews/<project>, commons}/*.json`, sem expiração (nenhum chamador passa `maxAgeMs`); `--refresh` ignora a leitura mas regrava. `out/` e `.cache/` estão no `.gitignore` (`.gitignore:4`, `.gitignore:16-17`).
- Memória por processo: `lastRequestAt` e `cooldownUntil` por host (`packages/ingest/src/util/http.ts:48-50`).
- Nenhuma variável de ambiente; paths saem de `import.meta.url` (`packages/ingest/src/config.ts:53-58`).

## Failure handling

- 404 em `fetchJson` → `NotFoundError` sem retry (`packages/ingest/src/util/http.ts:96`, `packages/ingest/src/util/http.ts:114`); `fetchArticleInfo`/`fetchMonthlySeries` transformam em `null` (que é cacheado para sempre); `fetchCommonsImage` não captura o 404.
- 429 → `throttleHost` congela o host pelo `Retry-After` (máx. 60 s; 5 s default) e tenta de novo (`packages/ingest/src/util/http.ts:74-80`, `packages/ingest/src/util/http.ts:100-104`).
- 5xx e erro de rede → backoff 1, 2, 4, 8, 16 s, até 6 tentativas (`packages/ingest/src/util/http.ts:88`, `packages/ingest/src/util/http.ts:109`, `packages/ingest/src/util/http.ts:117-118`). Outros 4xx falham na hora (`packages/ingest/src/util/http.ts:108`).
- Cache corrompido é engolido e vai à rede (`packages/ingest/src/util/cache.ts:58-60`).
- Por artigo: qualquer exceção vira audit `rejection: "fetch-error"` em `buildCard` (`packages/ingest/src/pool.ts:148-171`); a rodada continua.
- No script não há try/catch: locale inválido, arquivo ausente ou falha de `writeFile` derrubam o processo. Os dois `writeFile` não são atômicos (pool pode ser gravado e a auditoria falhar). `curation-queue` tem `main().catch` com `process.exitCode = 1` (`packages/ingest/src/cli/curation-queue.ts:177-180`).

## Tests covering this flow

- Só `packages/ingest/src/peak.test.ts` (chama `detectPeak` com séries sintéticas, ex. `packages/ingest/src/peak.test.ts:48`, `packages/ingest/src/peak.test.ts:224`).
- Sem testes para `pool.ts`, `pageviews.ts`, `commons.ts`, `wikipedia.ts`, `util/http.ts`, `util/cache.ts`, `util/concurrency.ts`, `cli/args.ts` nem para os CLIs.

## Open questions

- `packages/ingest/src/cli/curation-queue.ts:111` resolve a raiz com `new URL(import.meta.url).pathname.slice(1)`, que só funciona no Windows (tira a `/` de `/C:/…`); em Linux o caminho fica relativo. `config.ts` usa `fileURLToPath` (`packages/ingest/src/config.ts:53`). Bug ou só nunca rodou fora do Windows?
- Cache de 404 (`null`) e de artigo nunca expiram: artigo criado/renomeado depois da primeira coleta fica `article-missing` até `--refresh`. Intencional?
- `fetch-error` e `image:*` não estão em `CURÁVEL`, então somem da fila de curadoria. Intencional?
- `buildCard` nunca lança, então o teste `result === undefined` em `packages/ingest/src/cli/build-pool.ts:61` só cobre buracos do `mapLimit` (`packages/ingest/src/util/concurrency.ts:24`).
