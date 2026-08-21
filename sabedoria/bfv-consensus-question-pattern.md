---
name: bfv-consensus-question-pattern
description: O formato exato das perguntas de Bryan ao Consensus (research search engine) — como compor prompts otimizados de extração de conhecimento
metadata:
  type: reference
---

Consensus (consensus.app) é o motor de busca de literatura que Bryan usa para extrair conhecimento metodológico. O padrão canônico das perguntas está em `docs/project_memory/archive/assistant_prose_all_chats.md` (buscar "Pergunta para o Consensus"). Estrutura:

```
## Pergunta para o Consensus

standard:

<UMA pergunta metodológica neutra, em inglês acadêmico, respondível pela literatura — não sobre segredos do projeto>

Context:
- The project is research/backtest-only. No live trading, no broker, no API use.
- <bullets de enquadramento específico e neutro>
- I do not want trading advice, live trading, broker integration, or API use.

Please explain:
1. ... (lista numerada de sub-perguntas específicas)

Please cite multiple independent sources from <campos relevantes>.

Do not give trading advice.
Do not recommend live trading.
Do not treat backtests as proof of edge.
```

Regras de ouro de Bryan: **uma pergunta por vez** (não todas de uma vez), sequenciadas para que a resposta de cada uma afie a próxima ("extrair o conhecimento exato"). O conhecimento do Consensus vira depois **regra de bloco futuro** (padrão histórico). As respostas chegam como PDF em `C:\Users\drbry\Documents\ia mind\conhecimentoNNN.pdf`.

Sequência do parecer Fable ([[fable5-sublime-audit-objectives]]): Q1 integridade de dados (conhecimento162, respondido — forte), Q2 pré-registro confirmatório + kill/aceitação (conhecimento163, respondido — forte, é o gabarito do Passo 3 THIRD-BRANCH-PREREGISTRATION), Q3 regras objetivas sem data-snooping, Q4 custos realistas, Q5 multi-mercado cripto+FX.
