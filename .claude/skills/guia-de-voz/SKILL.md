---
name: guia-de-voz
description: O Guia de voz de cada canal — tom, voz, pronúncia de nomes, glossário e o que é proibido. Consultar ANTES de mexer em tradução, narração ou voz de qualquer canal, e ao revisar uma dublagem que saiu estranha (nome pronunciado errado, tom fora do canal, termo traduzido errado). O motor lê estes arquivos em tempo de execução.
---

# Guia de voz

Um arquivo por canal em `canais/<nome_buffer>.md` (o `nome_buffer` do
`engine/canais_registro.py`: `modofuturo`, `truque.importado`, ...).

## Quem lê

- **O motor**, em `engine/guia_voz.py`:
  - `## Tom`, `## Glossário` e `## Proibido` entram no prompt da narração
    (`engine/traducao.py`, campo `{guia}`).
  - `## Pronúncia` troca a GRAFIA pela FALA **só no texto que vai para a voz**
    (`voz_clonada._falar`). A legenda na tela continua com a grafia oficial.
- **Quem revisa** uma dublagem: comparar com esta bíblia antes de mexer no código.

## Formato (o motor depende dele — manter as seções com estes nomes)

```
## Tom            texto livre, curto (vai no prompt)
## Voz            qual voz e por quê (documentação; o disparo é que escolhe)
## Pronúncia      tabela | escrita | falada |
## Glossário      lista "- termo: como tratar" (vai no prompt)
## Proibido       lista "- ..." (vai no prompt)
```

## Regras

- ⚠️ Repositório PÚBLICO: nada privado aqui (sem token, sem dado de pessoa).
- Pronúncia marcada `(a conferir)` é proposta: o dono confirma ouvindo.
- Mudou algo? Rodar `python teste/teste_guia_voz.py`.
- Canal sem arquivo = motor segue como antes (falha aberta).
