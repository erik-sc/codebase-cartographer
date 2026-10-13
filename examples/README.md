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
