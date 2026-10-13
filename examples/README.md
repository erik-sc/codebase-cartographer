# Exemplos

## memeline-kb/

Saída real de `/learn-codebase` rodado numa cópia descartável do projeto `memeline`
(monorepo TypeScript: Next.js + CLIs de ingestão) em 12/10/2026, sem nenhuma edição
manual. Números do run:

| Métrica | Valor |
|---|---|
| Arquivos da KB | 10 (715 linhas) |
| Citações `caminho:linha` / commit | 859, todas válidas após `kb_lint.py` |
| Sub-agentes | 8 (4 cartographer, 3 tracer, 1 verifier); historian feito inline (repo com 10 commits) |
| Chamadas de ferramenta do orquestrador | ~16 |
| Prompts de permissão | 0 |
| Achados | 3 bugs plausíveis (id de puzzle UTC vs local em `/move`; caminho raiz só-Windows em `curation-queue.ts`; flag `series-edge` ausente em `CURÁVEL`) e ~12 comentários desatualizados |

Na primeira passada o linter apontou 14 citações quebradas, todas caminhos abreviados
dentro de tabelas (`http.ts:87` em vez de `apps/web/src/server/http.ts:87`). Isso virou
a regra "caminho completo mesmo em tabelas" no SKILL.md.

O que fica aqui é uma fotografia: o código do memeline continua evoluindo, então as
linhas citadas valem para o commit em que o run foi feito.

## O que o `verifier` pegou que o linter não pega

Depois do run, o agente `verifier` checou ~110 citações lendo uma janela em volta de
cada uma. Todas as 7 afirmações de maior impacto se sustentaram, mas ele achou:

- 7 citações deslocadas em 1–2 linhas (`CLAUDE.md:48` -> `:49`, `package.json:15` -> `:17`,
  etc.). O linter aceita porque a linha existe; só a leitura mostra que não sustenta a frase.
- 1 "discrepância documentação vs código" falsa (o comentário sobre 120 ms registrava um
  experimento que falhou, e o código concorda com ele).
- 1 impacto exagerado (`CURÁVEL` sem `series-edge` perde só os memes sinalizados
  *apenas* por essa flag, porque `article-predates-data` vem antes na ordem de flags).

As correções foram aplicadas nesta cópia. É por isso que a Fase 5 da skill roda o
linter **e** entrega ao `verifier` a lista das afirmações que sustentam o resto.
