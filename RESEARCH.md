# O que influencia o conhecimento de uma base de código

Levantamento de literatura que fundamenta o `codebase-cartographer`. Pesquisa feita em
12/10/2026 com quatro levantamentos paralelos (compreensão humana de programas; agentes
LLM sobre repositórios; artefatos de conhecimento e efeito de IA na compreensão; modelo
de permissões do Claude Code). Toda citação foi conferida contra a página do editor,
DOI, arXiv ou página do autor; o que não foi possível confirmar está marcado como
**[não verificado]** ou **[parcial]**.

## 1. A pergunta

O que faz uma pessoa (ou um agente) *saber* uma base de código? E como desenhar um
fluxo agêntico que construa esse conhecimento, sem travar em prompts de aprovação e sem
transformar o humano em passageiro?

## 2. Síntese em uma página

**Conhecer uma base de código é ter, simultaneamente, três modelos** (von Mayrhauser &
Vans 1995): um modelo de *domínio* (que conceitos o sistema implementa), um modelo de
*programa* (estrutura, fluxo de controle, dependências) e um modelo de *situação*
(fluxo de dados e comportamento ponta a ponta). Especialistas alternam entre os três
sem esforço porque já têm uma base de conhecimento persistida na memória; novatos
ficam presos num só.

**O que mais influencia a formação desse conhecimento, segundo a evidência:**

1. **Estratégia de leitura.** Especialistas leem de cima para baixo guiados por
   hipóteses e *beacons* (Brooks 1983) e reconhecem *planos* idiomáticos (Soloway &
   Ehrlich 1984). Para tarefas de mudança, quem rastreia interações sistematicamente
   acerta; quem lê "conforme a necessidade" erra por efeitos não locais (Littman et al.
   1986; Robillard et al. 2004).
2. **Acesso ao "por quê".** As perguntas mais difíceis e mais adiadas são sobre
   racional e comportamento sob condições; a fonte costuma ser um colega indisponível
   ou o histórico (Ko et al. 2007; LaToza & Myers 2010). ADRs e mensagens de commit
   são o substituto barato (Nygard 2011; Codoban et al. 2015).
3. **Vocabulário.** Compreender é localizar conceitos no código (Rajlich & Wilde 2002).
   Nomes curtos custam 19% mais tempo para entender (Hofmeister et al. 2017) e dois
   desenvolvedores escolhem o mesmo nome só ~7% das vezes (Feitelson et al. 2022): o
   glossário conceito -> identificador é o índice de tudo.
4. **Concentração e perda de conhecimento.** 65% dos projetos populares têm truck
   factor <= 2 (Avelino et al. 2016); a saída dessas pessoas destrói conhecimento
   (Rigby et al. 2016). Conhecimento = autoria + interação (Fritz et al. 2010/2014).
5. **Documentação que sobrevive.** Docs de grão grosso continuam úteis mesmo
   desatualizadas; detalhe fino apodrece primeiro (Lethbridge et al. 2003). O maior
   problema de documentação é estar desatualizada (Aghajani et al. 2019/2020).
6. **Tempo.** ~58% do tempo é compreensão, e seniores gastam muito menos (Xia et al.
   2018); ~70% do tempo na IDE é navegação e inspeção (Minelli et al. 2015).

**Para agentes LLM**, a evidência converge para: esqueleto do repositório antes de
código, localização hierárquica (repo -> diretório -> arquivo -> símbolo), grafo de
dependências como guia de leitura, sub-agentes com contexto próprio que devolvem
resumos destilados, notas persistidas fora da janela, e verificação de cada símbolo
antes de afirmar (Agentless 2024; RepoUnderstander 2024; RepoGraph 2025; Anthropic
2025; Spracklen et al. 2025). Contextos longos degradam (Liu et al. 2023; Chroma 2025)
e leituras dominam o gasto de tokens (SWE-Pruner 2026: 76%).

**Para humanos usando IA**, explicação sob demanda melhora vazão mas não entendimento
medido (Nam et al. 2024); delegar reduz compreensão, sobretudo em depuração, e a sensação
de posse do código (Anthropic 2026; Bergh et al. 2026); desenvolvedores experientes em
repos que conhecem bem ficaram 19% *mais lentos* com IA achando que estavam mais rápidos
(METR 2025). O padrão de interação, não o uso de IA em si, decide se há aprendizado:
perguntas conceituais, explicar-de-volta e prever-depois-verificar preservam; delegação
total e depuração iterativa pela IA corroem.

## 3. Literatura por tema

### 3.1 Teorias cognitivas de compreensão de programas

- **Brooks, R. (1983).** Towards a theory of the comprehension of computer programs.
  *Int. J. Man-Machine Studies* 18(6), 543–554. DOI 10.1016/S0020-7373(83)80031-5.
  Compreensão é top-down e dirigida por hipóteses; *beacons* são marcas superficiais
  que sinalizam uma estrutura. Implicação: começar por uma hipótese arquitetural e
  pelos beacons que a confirmam ou refutam.
- **Soloway, E., & Ehrlich, K. (1984).** Empirical studies of programming knowledge.
  *IEEE TSE* SE-10(5), 595–609. DOI 10.1109/TSE.1984.5010283. Especialistas usam
  *planos* e *regras de discurso*; quando o código viola convenções, a vantagem deles
  desaparece. Implicação: extrair as convenções locais e sinalizar violações.
- **Letovsky, S. (1987).** Cognitive processes in program comprehension. *J. Systems
  and Software* 7(4), 325–339. DOI 10.1016/0164-1212(87)90032-X. A unidade cognitiva é a
  *inquirição*: pergunta -> conjectura -> busca de verificação. Implicação: o log de
  perguntas como motor do fluxo.
- **Pennington, N. (1987).** Stimulus structures and mental representations in expert
  comprehension of computer programs. *Cognitive Psychology* 19(3), 295–341.
  DOI 10.1016/0010-0285(87)90007-7. Primeiro o *modelo de programa* (controle), depois
  o *modelo de situação* (domínio e dados). Implicação: produzir dois artefatos.
- **Littman, D. C., Pinto, J., Letovsky, S., & Soloway, E. (1986/1987).** Mental models
  and software maintenance. *J. Systems and Software* 7(4), 341–355.
  DOI 10.1016/0164-1212(87)90033-1. Estratégia sistemática acerta modificações;
  as-needed falha por interações não vistas.
- **von Mayrhauser, A., & Vans, A. M. (1995).** Program comprehension during software
  maintenance and evolution. *IEEE Computer* 28(8), 44–55. DOI 10.1109/2.402076.
  Metamodelo integrado: domínio, programa, situação e base de conhecimento compartilhada.
- **Storey, M.-A. (2005/2006).** Theories, methods and tools in program comprehension.
  *IWPC 2005*, 181–191, DOI 10.1109/WPC.2005.38; *Software Quality J.* 14(3), 187–208,
  DOI 10.1007/s11219-006-9216-4. Survey; estratégia depende de pessoa, programa e tarefa.

### 3.2 Necessidades de informação e perguntas

- **LaToza, T. D., Venolia, G., & DeLine, R. (2006).** Maintaining mental models: a study
  of developer work habits. *ICSE 2006*, 492–501. O maior problema reportado é entender
  o *racional* do código; a transferência é majoritariamente presencial. [DOI não
  confirmado independentemente; venue e páginas confirmados]
- **Ko, A. J., Myers, B. A., Coblenz, M. J., & Aung, H. H. (2006).** An exploratory study
  of how developers seek, relate, and collect relevant information during software
  maintenance tasks. *IEEE TSE* 32(12), 971–987. DOI 10.1109/TSE.2006.116. Buscas com
  pistas limitadas falham com frequência; ~35% do tempo é navegação.
- **Ko, A. J., DeLine, R., & Venolia, G. (2007).** Information needs in collocated
  software development teams. *ICSE 2007*, 344–353. DOI 10.1109/ICSE.2007.45. 21 tipos de
  necessidade; as mais adiadas são racional de design e comportamento.
- **Sillito, J., Murphy, G. C., & De Volder, K. (2006; 2008).** Questions programmers ask
  during software evolution tasks, *FSE 2006*, DOI 10.1145/1181775.1181779; Asking and
  answering questions during a programming change task, *IEEE TSE* 34(4), 434–451,
  DOI 10.1109/TSE.2008.26. 44 tipos de pergunta em 4 grupos; ferramentas ajudam a achar
  pontos de foco, não a compor respostas entre subgrafos.
- **LaToza, T. D., & Myers, B. A. (2010).** Hard-to-answer questions about code.
  *PLATEAU 2010*. DOI 10.1145/1937117.1937125. 371 perguntas difíceis de 179
  profissionais; as mais duras: racional, história, comportamento condicional, impacto.

### 3.3 Onboarding e novatos

- **Begel, A., & Simon, B. (2008).** Novice software developers, all over again. *ICER
  2008*, 3–14. DOI 10.1145/1404520.1404522. Novatos escondem a falta de conhecimento de
  quem mais poderia ajudar.
- **Dagenais, B., Ossher, H., Bellamy, R. K. E., Robillard, M. P., & de Vries, J. P.
  (2010).** Moving into a new software project landscape. *ICSE 2010*, 275–284.
  DOI 10.1145/1806799.1806842. Integração depende de experimentação cedo, internalizar
  estruturas e cultura, e validar progresso.
- **Steinmacher, I., Silva, M. A. G., Gerosa, M. A., & Redmiles, D. F. (2015).** A
  systematic literature review on the barriers faced by newcomers to open source
  software projects. *IST* 59, 67–85. DOI 10.1016/j.infsof.2014.11.001. Barreiras:
  por onde começar, setup, documentação desatualizada.

### 3.4 Recuperação de conhecimento, documentação, conhecimento tácito

- **Rajlich, V., & Wilde, N. (2002).** The role of concepts in program comprehension.
  *IWPC 2002*, 271–278. DOI 10.1109/WPC.2002.1021348.
- **Dit, B., Revelle, M., Gethers, M., & Poshyvanyk, D. (2013).** Feature location in
  source code: a taxonomy and survey. *J. Softw.: Evol. and Process* 25(1), 53–95.
  DOI 10.1002/smr.567. Técnicas híbridas (texto + estático + dinâmico + histórico)
  superam qualquer técnica isolada.
- **Ducasse, S., & Pollet, D. (2009).** Software architecture reconstruction: a
  process-oriented taxonomy. *IEEE TSE* 35(4), 573–591. DOI 10.1109/TSE.2009.19.
- **Kuhn, A., Erni, D., Loretan, P., & Nierstrasz, O. (2010).** Software cartography.
  *J. Softw. Maint. and Evol.* 22(3), 209–229. DOI 10.1002/smr.414. Mapas com layout
  consistente ajudam orientação; estabilidade importa mais que fidelidade.
- **Avelino, G., Passos, L., Hora, A., & Valente, M. T. (2016).** A novel approach for
  estimating truck factors. *ICPC 2016*. DOI 10.1109/ICPC.2016.7503718. 65% de 133
  projetos com truck factor <= 2.
- **Rigby, P. C., Zhu, Y. C., Donadelli, S. M., & Mockus, A. (2016).** Quantifying and
  mitigating turnover-induced knowledge loss. *ICSE 2016*, 1006–1016.
  DOI 10.1145/2884781.2884851. Conhecimento em risco pode ser >3x o esperado; indicar
  sucessores reduz perda.
- **Fritz, T., Ou, J., Murphy, G. C., & Murphy-Hill, E. (2010).** A degree-of-knowledge
  model to capture source code familiarity. *ICSE 2010*, 385–394; versão estendida em
  *ACM TOSEM* 23(2), 2014. Conhecimento = autoria + interação.
- **Mockus, A., & Herbsleb, J. D. (2002).** Expertise Browser. *ICSE 2002*, 503–512.
- **Nygard, M. (2011).** Documenting architecture decisions. Blog, 15/11/2011.
  https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- **Conway, M. E. (1968).** How do committees invent? *Datamation* 14(4), 28–31.
- **Lethbridge, T. C., Singer, J., & Forward, A. (2003).** How software engineers use
  documentation: the state of the practice. *IEEE Software* 20(6), 35–39.
- **Forward, A., & Lethbridge, T. C. (2002).** The relevance of software documentation,
  tools and technologies. *DocEng 2002*.
- **Aghajani, E. et al. (2019; 2020).** Software documentation issues unveiled, *ICSE
  2019*, 1199–1210; Software documentation: the practitioners' perspective, *ICSE 2020*,
  590–601, DOI 10.1145/3377811.3380405. Desatualização, incompletude e ambiguidade no
  topo; praticantes preferem docs atuais e relevantes à tarefa a docs completas.
- **Prana, G. A. A., Treude, C., Thung, F., Atapattu, T., & Lo, D. (2019).** Categorizing
  the content of GitHub README files. *EMSE* 24, 1296–1327. DOI 10.1007/s10664-018-9660-3.
  READMEs raramente dizem *por quê* e *em que estado* o projeto está.
- **Robillard, M. P. (2009)** What makes APIs hard to learn? *IEEE Software* 26(6),
  27–34; **Robillard & DeLine (2011)**, *EMSE* 16, 703–732. Falta de intenção, racional
  e exemplos de uso são os maiores obstáculos.
- **Maalej, W., & Robillard, M. P. (2013).** Patterns of knowledge in API reference
  documentation. *IEEE TSE* 39(9), 1264–1282. 12 tipos de conhecimento; racional e
  padrões são raros e valiosos.
- C4 (Simon Brown), arc42 (Starke & Hruschka), Diátaxis (Procida 2020), MADR
  (Zimmermann et al.): úteis como formatos; **nenhum estudo controlado de efeito em
  onboarding foi encontrado** para eles.

### 3.5 Nomes e vocabulário

- **Lawrie, D., Morrell, C., Feild, H., & Binkley, D. (2006).** What's in a name? *ICPC
  2006*, 3–12.
- **Hofmeister, J., Siegmund, J., & Holt, D. V. (2017; 2019).** Shorter identifier names
  take longer to comprehend. *SANER 2017*, 217–227; *EMSE* 24, 417–443,
  DOI 10.1007/s10664-018-9621-x. Nomes com palavras: 19% mais rápido para achar defeitos.
- **Feitelson, D. G., Mizrahi, A., Noy, N. et al. (2022).** How developers choose names.
  *IEEE TSE* 48(1), 37–52. arXiv:2103.07487. Mesmo nome para a mesma coisa em ~6,9%
  dos casos (mediana).
- **Evans, E. (2003).** *Domain-Driven Design*. Addison-Wesley. "Linguagem ubíqua".

### 3.6 História como conhecimento

- **Hindle, A., Barr, E. T., Su, Z., Gabel, M., & Devanbu, P. (2012).** On the
  naturalness of software. *ICSE 2012*. Código "surpreendente" sinaliza onde o
  conhecimento está concentrado.
- **Silva, D., Tsantalis, N., & Valente, M. T. (2016).** Why we refactor? *FSE 2016*,
  858–870. arXiv:1607.02459.
- **Tian, Y. et al. (2022).** What makes a good commit message? *ICSE 2022*. arXiv:2202.02974.
- **Codoban, M., Ragavan, S. S., Dig, D., & Bailey, B. (2015).** Software history under
  the lens. *ICSME 2015*. Desenvolvedores consultam histórico para depurar e recuperar
  intenção, mas sofrem com mensagens vazias e sobrecarga.

### 3.7 Medindo o esforço de compreensão

- **Xia, X., Bao, L., Lo, D., Xing, Z., Hassan, A. E., & Li, S. (2018).** Measuring program
  comprehension: a large-scale field study with professionals. *IEEE TSE* 44(10),
  951–976. DOI 10.1109/TSE.2017.2734091. 78 profissionais, 3.148 h: ~58% é compreensão.
- **Minelli, R., Mocci, A., & Lanza, M. (2015).** I know what you did last summer. *ICPC
  2015*. DOI 10.1109/ICPC.2015.12. ~70% do tempo na IDE é compreensão.

### 3.8 Estratégias de leitura

- **Robillard, M. P., Coelho, W., & Murphy, G. C. (2004).** How effective developers
  investigate source code. *IEEE TSE* 30(12), 889–903. DOI 10.1109/TSE.2004.101.
  Investigação metódica com notas vence a oportunista; "cegueira por desatenção" ao rolar.

### 3.9 Agentes LLM sobre repositórios

- **Zhang, F. et al. (2023).** RepoCoder. *EMNLP 2023*. arXiv:2303.12570. Recuperação
  iterativa usando o que já foi gerado como consulta; duas iterações bastam.
- **Shrivastava, D. et al. (2023).** RepoFusion. arXiv:2306.10998.
- **Bairi, R. et al. (2024).** CodePlan. *FSE 2024*. arXiv:2309.12499. Planejamento sobre
  grafo de dependências.
- **Liu, X. et al. (2024).** CodexGraph. arXiv:2408.03910. Grafo MODULE/CLASS/FUNCTION
  consultável.
- **Ouyang, S. et al. (2025).** RepoGraph. *ICLR 2025*. arXiv:2410.14684. Grafo em nível
  de linha melhora quatro sistemas diferentes.
- **Liu, W. et al. (2024).** GraphCoder. *ASE 2024*. arXiv:2406.07003. Recuperação
  coarse-to-fine.
- **Ma, Y. et al. (2024).** How to understand whole software repository? (RepoUnderstander
  / Alibaba LingmaAgent). arXiv:2406.01422. Condensa o repo num grafo top-down e explora
  com MCTS; +18,5% relativo sobre SWE-agent.
- **Xia, C. S. et al. (2024).** Agentless. arXiv:2407.01489. Localização hierárquica
  arquivo -> classe/função -> linha a partir de um esqueleto.
- **Yang, J. et al. (2024).** SWE-agent. *NeurIPS 2024*. arXiv:2405.15793. Interface
  agente-computador com visões limitadas e busca com contagem.
- **Wang, X. et al. (2024; 2025).** CodeAct, *ICML 2024*, arXiv:2402.01030; OpenHands,
  *ICLR 2025*, arXiv:2407.16741.
- **Zhang, Y. et al. (2024).** AutoCodeRover. *ISSTA 2024*. arXiv:2404.05427. Busca
  consciente da estrutura (search_class, search_method).
- **Arora, D. et al. (2024).** MASAI. arXiv:2406.11638. Sub-agentes modulares com
  objetivos distintos.
- **Aider repo map.** Gauthier, P. (2023). https://aider.chat/docs/repomap.html.
  tree-sitter + ranking em grafo com orçamento de tokens. [uso de PageRank: secundário]
- **Sourcegraph Cody** (docs) e **Cursor** (codebase indexing, Merkle tree): contraponto
  com índice pré-computado e incremental.
- **Claude Code**: busca agêntica (grep/glob) em vez de RAG com vetores, segundo Boris
  Cherny [atribuição secundária].
- **Anthropic (2025).** Effective context engineering for AI agents; How we built our
  multi-agent research system; Building effective agents (2024);
  Claude Code best practices (code.claude.com). Orçamento de atenção, recuperação
  just-in-time, notas estruturadas, sub-agentes que devolvem resumos de 1–2k tokens,
  "exploração infinita" como modo de falha nomeado.
- **AGENTS.md** (OpenAI 2025; Linux Foundation 2025).

### 3.10 Benchmarks de compreensão

- **RepoQA** (Liu, J. et al. 2024, arXiv:2406.06025); **CrossCodeEval** (Ding et al.
  2023, arXiv:2310.11248); **Long Code Arena** (Bogomolov et al. 2024, arXiv:2406.11612);
  **CodeQA** (Liu & Wan 2021, arXiv:2109.08365); **SWE-bench** (Jimenez et al. 2024,
  arXiv:2310.06770) e **SWE-bench Verified** (OpenAI 2024); **LoCoBench** (arXiv:2509.09614);
  **CoReQA** (Chen et al. 2025, arXiv:2501.03447); **SWE-QA** (Peng et al. 2026,
  arXiv:2509.14635); **CodeRAG-Bench** (Wang et al. 2025, arXiv:2406.14497).
  Conclusão transversal: perguntas multi-salto entre arquivos são onde modelos falham.

### 3.11 Geração de documentação e memória de agentes

- **RepoAgent** (Luo et al. 2024, arXiv:2402.16667); **DocAgent** (Yang et al. 2025,
  arXiv:2504.08725: gerar em ordem topológica é crítico); **DeepWiki** (Cognition 2025);
  **Google Code Wiki** (preview 11/2025); **Devin Knowledge**.
- **MemGPT** (arXiv:2310.08560); **A-MEM** (arXiv:2502.12110); **Mem0** (arXiv:2504.19413);
  **Reflexion** (arXiv:2303.11366); **Voyager** (arXiv:2305.16291); **ExpeL**
  (arXiv:2308.10144); **SWE-Search** (arXiv:2410.20285); **Lingma SWE-GPT** (arXiv:2411.00622).

### 3.12 Modos de falha

- **Liu, N. F. et al. (2024).** Lost in the middle. *TACL* 12. arXiv:2307.03172.
- **Hong, K., Troynikov, A., & Huber, J. (2025).** Context rot. Chroma. [números via
  resumos secundários]
- **Spracklen, J. et al. (2025).** We have a package for you! *USENIX Security 2025*.
  arXiv:2406.10279. 5–22% dos pacotes gerados não existem.
- **SWE-Pruner** (arXiv:2601.16746): leituras consomem 76,1% dos tokens de um agente.

### 3.13 IA e compreensão humana

- **Nam, D., Macvean, A., Hellendoorn, V., Vasilescu, B., & Myers, B. (2024).** Using an
  LLM to help with code understanding. *ICSE 2024*. DOI 10.1145/3597503.3639187. Mais
  sub-tarefas concluídas, sem ganho significativo em tempo ou em quiz de compreensão.
- **Becker, J., Rush, N., Barnes, E., & Rein, D. (2025).** Measuring the impact of
  early-2025 AI on experienced open-source developer productivity. METR.
  arXiv:2507.09089. 16 devs, 246 issues: 19% mais lentos com IA (IC +2% a +39%),
  acreditando estar 20% mais rápidos.
- **Anthropic (2026).** How AI assistance impacts the formation of coding skills. RCT,
  52 engenheiros: quiz 50% vs 67%; maior lacuna em depuração; padrões que preservam
  aprendizado: perguntas conceituais, código + explicação, geração-depois-compreensão.
  (Preprint relacionado: Shen & Tamkin 2026, arXiv:2601.20245.)
- **Bergh, Tag, Vassar, & Renzella (2026).** Higher performance, lower retention, and
  reduced ownership. arXiv:2609.21194. Desempenho 89% vs 69%, retenção 41% vs 53%,
  atribuição de autoria 45% vs 81%.
- **Barke, S., James, M. B., & Polikarpova, N. (2023).** Grounded Copilot. *PACMPL*
  7(OOPSLA1). DOI 10.1145/3586030. Modos *aceleração* vs *exploração*.
- **Prather, J. et al. (2023).** "It's weird that it knows what I want". *ACM TOCHI*
  31(1). DOI 10.1145/3617367. Novatos "derivam" sem plano.
- **Mozannar, H., Bansal, G., Fourney, A., & Horvitz, E. (2024).** Reading between the
  lines. *CHI 2024*. DOI 10.1145/3613904.3641936. Verificar sugestões é fração grande
  da sessão. [percentual exato: parcial]
- **Vaithilingam, P., Zhang, T., & Glassman, E. L. (2022).** Expectation vs. experience.
  *CHI EA 2022*. Sem ganho de tempo; dificuldade de entender e depurar o gerado.
- **Sarkar, A. et al. (2022).** What is it like to program with artificial intelligence?
  *PPIG 2022*. arXiv:2208.06213. Verificar vira o gargalo.
- **Peng, S. et al. (2023).** arXiv:2302.06590 (Copilot, +55,8% em tarefa greenfield);
  **Ziegler, A. et al. (2022).** arXiv:2205.06537 (aceitação prevê produtividade
  *percebida*).
- **DORA 2024/2025** (Google Cloud): IA eleva volume de mudança; estabilidade cai;
  capacidade de revisão/compreensão é a restrição. **GitClear 2025**: clones x4, churn
  3,1% -> 5,7% (correlacional, relatório de fornecedor).
- **Singh et al. (2025).** Code Researcher. arXiv:2506.11060. Primeiro agente a usar
  histórico de commits como contexto. **Gao et al. (2026).** CodeMap. *ICPC 2026*.
  arXiv:2504.04553. Mapas hierárquicos reduzem em 79% a dependência de prosa do LLM.

### 3.14 Ciência da aprendizagem

- **Schulte, C. (2008).** Block Model. *ICER 2008*, 149–160. DOI 10.1145/1404520.1404535.
  Grade 4 níveis x 3 dimensões para gerar perguntas.
- **Xie, B. et al. (2019).** A theory of instruction for introductory programming
  skills. *CSE* 29(2–3), 205–253. Sequência: rastrear, depois reconhecer templates,
  depois escrever.
- **Lehtinen, T., Seppälä, O., & Korhonen, A. (2023).** Automated questions about
  learners' own code help to detect fragile knowledge. *ITiCSE 2023*.
  DOI 10.1145/3587102.3588787. 27% falham em perguntas sobre código que acabaram de
  fazer funcionar.
- **Roediger, H. L., & Karpicke, J. D. (2006).** Test-enhanced learning. *Psychological
  Science* 17(3). Recuperação vence releitura; releitura infla confiança.
- **Sweller, J. (1988).** Cognitive load. *Cognitive Science* 12(2); **Sweller & Cooper
  (1985).** Exemplos resolvidos para novatos, desvanecer com expertise.
- **Guo, P. J. (2021).** Ten million users and ten years later (Python Tutor). *UIST
  2021*. [parcial]

### 3.15 Modelo de permissões do Claude Code (docs em code.claude.com, 12/10/2026)

- `Read`, `Grep`, `Glob`, `Agent`, `AskUserQuestion` não pedem permissão dentro do
  diretório de trabalho. `Bash`, `Edit`, `Write`, `WebFetch`, `WebSearch` pedem, exceto
  um conjunto embutido de comandos read-only (`ls`, `cat`, `head`, `grep`, `find`, `wc`,
  formas read-only de `git`, etc.).
- Regras `permissions.allow/ask/deny` com sintaxe `Tool(spec)`; `Bash(git log *)`;
  `Write(./docs/**)`; ordem de avaliação deny > ask > allow; `allow` de projeto só vale
  após o diálogo de confiança; `deny` vale sempre.
- Sub-agentes: `tools`, `disallowedTools`, `permissionMode` (`plan`, `dontAsk`...),
  `maxTurns`; herdam regras do pai; `dontAsk` converte prompts em negações.
- Skills: `allowed-tools`, `disallowed-tools`, `context: fork` + `agent`, `$ARGUMENTS`,
  `${CLAUDE_SKILL_DIR}`; progressive disclosure com `references/` e `scripts/`.
- Hooks `PreToolUse` com saída `permissionDecision: allow|deny|ask`; `allow` do hook
  não vence `deny`.
- Plugins **não** carregam regras de permissão (só `agent` e `subagentStatusLine` em
  `settings.json`); por isso o template de settings é entregue separadamente.
- Não verificado: separador exato de múltiplas entradas em `allowed-tools` (usado
  vírgula, como na doc de comandos); existência de `LS`; esquema de `marketplace.json`.

## 4. Princípios de design e onde foram implementados

| # | Princípio (fonte) | Implementação |
|---|---|---|
| 1 | Esqueleto antes de código (Agentless; Aider; RepoUnderstander) | `repo_skeleton.py`, Fase 1 |
| 2 | Hipótese + beacons, com um beacon refutador (Brooks; Soloway & Ehrlich) | Fase 1, `reading-strategies.md` |
| 3 | Grafo de dependências guia a leitura (CodePlan; RepoGraph) | PageRank sobre imports no script |
| 4 | Localização hierárquica e busca por símbolo (Agentless; AutoCodeRover) | prompts de `cartographer`/`tracer` |
| 5 | Fan-out com orçamento, resumos destilados (Anthropic multi-agente; MASAI) | Fase 2, `maxTurns`, limite de palavras |
| 6 | Dois modelos: estrutura e situação (Pennington; von Mayrhauser & Vans) | `20-architecture.md`, `30-flows/` |
| 7 | Glossário conceito -> código (Rajlich & Wilde; Hofmeister; Feitelson) | Fase 3, `10-glossary.md` |
| 8 | "Por quê" via histórico, racional inferido rotulado (LaToza & Myers; Nygard; Codoban) | `historian`, `40-history.md` |
| 9 | Truck factor e posse como mapa do tácito (Avelino; Rigby; Fritz; Conway) | seção 4 do script, `40-history.md` |
| 10 | Rastreamento sistemático (Littman; Robillard) | `tracer`, `/trace-flow` |
| 11 | Pergunta -> conjectura -> verificação (Letovsky; Sillito) | `90-questions.md`, `question-catalog.md`, `/ask-codebase` |
| 12 | Evidência em toda afirmação (Mozannar; Spracklen; DocAgent) | regra `path:line`, `verifier`, `kb_lint.py` |
| 13 | Persistir grão grosso, regenerar fino; layout estável (Lethbridge; Aghajani; Kuhn) | layout da KB, `INDEX.md` <= 60 linhas, `@import` |
| 14 | Contextos curtos, notas fora da janela (Lost in the Middle; Context Rot; Anthropic) | guard rails da skill, delegação |
| 15 | Humano ativo: prever, explicar-de-volta, depurar primeiro (Nam; Anthropic 2026; Roediger & Karpicke; Schulte; Lehtinen) | `/quiz-me`, `95-learning-log.md` |
| 16 | Zero prompts: só ferramentas de leitura, `dontAsk`, escrita confinada, hook (docs Claude Code) | agentes, `allowed-tools`, `templates/`, `hooks/` |

## 5. Lacunas e itens não verificados

- Nenhum estudo controlado sobre efeito de C4/arc42/Diátaxis/ADRs em onboarding.
- Nenhum estudo rigoroso sobre orçamento de chamadas de ferramenta para agentes de
  código; o melhor número é o de leituras do SWE-Pruner.
- Follow-up da METR com devs retornando: só relato secundário.
- Figura "66%" de racional em LaToza et al. 2006 e "17%" em Shen & Tamkin: secundárias.
- Uso de PageRank no Aider e razões de Boris Cherny sobre busca agêntica: secundárias.
- O efeito do próprio `codebase-cartographer` não foi medido; a seção 6 propõe como.

## 6. Como medir se isto funciona

Dado o que a literatura diz, as métricas certas são de *entendimento*, não de vazão:

1. Perguntas estilo RepoQA (descrição -> função) e SWE-QA (multi-salto) respondidas
   só a partir da KB, antes e depois de `/learn-codebase`.
2. Taxa de citações quebradas por `kb_lint.py` e pelo `verifier` (meta: zero).
3. No humano: acerto em `/quiz-me` ao longo de sessões espaçadas, e autoatribuição de
   posse do código (Bergh et al. 2026).
4. Tokens e chamadas por sessão de exploração, com e sem KB existente (espera-se queda
   forte na segunda sessão, emulando a diferença sênior/júnior de Xia et al. 2018).
5. Número de prompts de permissão por sessão (meta: zero).
