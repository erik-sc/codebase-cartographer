# codebase-cartographer

Um fluxo agêntico **somente leitura** para aprender e entender uma base de código no
Claude Code, sem cair no limbo de aprovações. Ele constrói uma base de conhecimento
verificada (`docs/codebase-knowledge/`) com evidência `arquivo:linha` em cada afirmação,
e depois ajuda *você* a internalizar o que foi mapeado, em vez de só delegar o
entendimento ao modelo.

O desenho inteiro deriva da literatura de compreensão de programas e de agentes de
código. A pesquisa completa, com referências verificadas, está em [RESEARCH.md](RESEARCH.md).

## O problema

1. **Entender código é a maior parte do trabalho.** ~58% do tempo de um desenvolvedor
   é compreensão (Xia et al. 2018); seniores gastam bem menos porque já carregam o mapa.
2. **O agente re-explora tudo a cada sessão** e, pior, cada `Bash`, `Edit` ou `Write`
   pede aprovação. Explorar vira uma sequência de "Allow?" que quebra o fluxo.
3. **Delegar a compreensão não ensina.** Explicação sob demanda aumenta a vazão, mas
   não o entendimento medido (Nam et al. 2024); quem delega entende e "possui" menos o
   código (Anthropic 2026; Bergh et al. 2026).

## O que este repositório entrega

| Peça | O que faz |
|---|---|
| `/learn-codebase [área]` | Esqueleto do repo -> hipótese arquitetural + beacons -> sub-agentes read-only em paralelo -> glossário, arquitetura, fluxos, história, convenções, log de perguntas -> verificação -> `INDEX.md` |
| `/ask-codebase <pergunta>` | Responde onde/como/por quê com evidência, consultando a KB antes de explorar |
| `/trace-flow <gatilho>` | Rastreia um comportamento ponta a ponta e grava em `30-flows/` |
| `/quiz-me [área]` | Prática de recuperação, prever-e-verificar, explicar-de-volta, graduado contra o código |
| Agentes `cartographer`, `historian`, `tracer`, `verifier` | Sub-agentes com **só** Read/Grep/Glob (e git read-only no historian/verifier), `permissionMode: dontAsk`, orçamento de turnos |
| `scripts/repo_skeleton.py` | Inventário read-only sem dependências: linguagens, beacons, PageRank sobre o grafo de imports, hotspots e truck factor via git |
| `scripts/kb_lint.py` | Verifica que toda citação `caminho:linha` e `commit sha` da KB existe |
| `hooks/allow_readonly.py` | Hook `PreToolUse` que auto-aprova uma lista estrita de comandos read-only |
| `templates/settings.project.json` | Regras `allow`/`deny` mínimas: ferramentas de leitura, git read-only, escrita **apenas** em `docs/codebase-knowledge/` |

## Como o "limbo de aprovação" é eliminado

No Claude Code, `Read`, `Grep`, `Glob` e `Agent` nunca pedem permissão dentro do diretório
de trabalho. Tudo aqui se apoia nisso:

- Os sub-agentes recebem `tools: Read, Grep, Glob` (sem Bash) e `permissionMode: dontAsk`:
  uma tentativa de escrita é **negada** em vez de ficar pendente.
- Comandos git de leitura (`log`, `blame`, `show`, `shortlog`...) já fazem parte do conjunto
  read-only embutido do Claude Code; o template de settings os lista explicitamente mesmo
  assim, e nega `push`, `reset`, `checkout`, `rm`.
- A única escrita permitida é `Write(./docs/codebase-knowledge/**)`. Nada mais é tocado.
- Os scripts são pré-aprovados pelo `allowed-tools` da skill
  (`Bash(python ${CLAUDE_SKILL_DIR}/scripts/*)`).
- Para o que sobrar (`rg`, `tree`, `tokei`, `git log --follow`...), o hook auto-aprova
  apenas comandos sem operadores de shell, sem redirecionamento e sem flags que escrevem.
  Regras `deny` continuam valendo sobre o hook.

Se você quiser uma sessão de estudo ainda mais estrita, use
`templates/settings.readonly-session.json` (modo `plan` por padrão).

## Instalação

**Como plugin (recomendado):**

```bash
claude plugin marketplace add C:/Users/eriks/Documents/projetos/codebase-cartographer
```

```bash
claude plugin install codebase-cartographer@codebase-cartographer-marketplace
```

Plugins não podem carregar regras de permissão, então copie também o template de
settings para o projeto que você quer estudar (ou use o instalador abaixo em modo
`project`).

**Copiando para o usuário ou para um projeto:**

```powershell
.\install.ps1                                  # ~/.claude (todos os projetos)
```

```powershell
.\install.ps1 -Scope project -Target C:\code\meu-app   # .claude do projeto + permissões + CLAUDE.md
```

Em Linux/macOS: `./install.sh` ou `./install.sh project /caminho/do/app`.

Na primeira abertura do projeto, aceite o diálogo de confiança do workspace: só a partir
daí as regras `allow` do `.claude/settings.json` valem (as `deny` valem sempre).

## Uso

```
/learn-codebase                 # mapa completo; 10-25 min num repo médio
/learn-codebase módulo de pagamentos
/ask-codebase por que o rate limit fica em memória e não no Redis?
/trace-flow POST /api/play/move
/quiz-me fluxo de sessão
```

A saída fica em `docs/codebase-knowledge/`:

```
INDEX.md            resumo <= 60 linhas; importe no CLAUDE.md com @docs/codebase-knowledge/INDEX.md
00-overview.md      hipótese, beacons, como buildar/rodar/testar (só o verificado)
10-glossary.md      conceito -> código (concept location)
20-architecture.md  modelo estrutural (program model)
30-flows/*.md       um comportamento ponta a ponta por arquivo (situation model)
40-history.md       decisões, hotspots, truck factor, ADRs inferidos
50-conventions.md   os "planos" locais e suas violações
90-questions.md     pergunta -> conjectura -> status -> evidência
95-learning-log.md  resultado dos quizzes (grau de conhecimento por área)
```

Commite a pasta: ela é a memória de longo prazo do time e do agente. A próxima sessão
começa dela, e `git diff` nela mostra como o entendimento mudou.

## Por que cada fase existe (resumo)

| Fase | Fundamento |
|---|---|
| Esqueleto antes de código | Agentless 2024; RepoUnderstander 2024; mapa de repo do Aider |
| Hipótese + beacons | Brooks 1983; Soloway & Ehrlich 1984 |
| Fan-out de sub-agentes com orçamento, resumos destilados | Anthropic, sistema multi-agente 2025; MASAI 2024; Context Rot 2025 |
| Glossário primeiro | Rajlich & Wilde 2002; Hofmeister et al. 2017; Feitelson et al. 2022 |
| Dois modelos: estrutura e comportamento | Pennington 1987; von Mayrhauser & Vans 1995 |
| Rastreamento sistemático de fluxos | Littman et al. 1986; Robillard et al. 2004 |
| "Por quê" vem da história | LaToza & Myers 2010; Ko et al. 2007; Nygard 2011; Codoban et al. 2015 |
| Truck factor e posse | Avelino et al. 2016; Rigby et al. 2016; Fritz et al. 2010 |
| Pergunta -> conjectura -> verificação | Letovsky 1987; Sillito et al. 2008 |
| Evidência em toda afirmação | Mozannar et al. 2024; Spracklen et al. 2025 |
| Persistir o grosso, regenerar o fino | Lethbridge et al. 2003; Aghajani et al. 2019/2020 |
| Quiz em vez de re-explicar | Roediger & Karpicke 2006; Nam et al. 2024; Anthropic 2026 |

## Estrutura do repositório

```
.claude-plugin/     plugin.json, marketplace.json
skills/             learn-codebase (+ references/, scripts/), ask-codebase, trace-flow, quiz-me
agents/             cartographer, historian, tracer, verifier
hooks/              hooks.json, allow_readonly.py
templates/          settings.project.json, settings.readonly-session.json, CLAUDE.md.snippet
install.ps1 / .sh   instaladores
RESEARCH.md         pesquisa e referências
```

## Limitações conhecidas

- O script de esqueleto resolve imports por heurística (relativos, aliases `@/`,
  pacotes de workspace). Linguagens com resolução complexa (Java por classpath, C++ por
  include path) terão grafo parcial; o PageRank ainda é útil, mas confira.
- Hooks de plugin usam `${CLAUDE_PLUGIN_ROOT}`; se você instalar copiando (sem plugin),
  registre o hook manualmente apontando para o caminho do script.
- Nada roda testes nem build: perguntas que exigem execução vão para `90-questions.md`
  com o comando exato para você rodar.

## Licença

MIT.
