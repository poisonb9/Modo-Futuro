# Canais

Um diretorio por canal. Cada `README.md` guarda a **receita de disparo** — os
parametros exatos do `workflow_dispatch` que produzem o corte daquele canal, e
o porque de cada um.

Isto existe porque a receita vivia so' no handoff e na memoria de quem
disparava. Em 30/08/2026 dois runs do Sem Anestesia morreram no teto de 6h do
GitHub Actions por uma combinacao de parametros que nao estava escrita em
lugar nenhum.

⚠️ **Nenhum segredo entra aqui.** Este repositorio e' PUBLICO. Token, id de
pasta do Drive e chave de API ficam em `Desktop/Tiktok/CREDENCIAIS.md`, fora
de qualquer repo.

| canal | @ | tema | receita |
|---|---|---|---|
| [Modo Futuro](modofuturo/) | `@modofuturo` | chips, fabrica, tecnologia | narracao de contexto |
| [Cozinha Internacional](cozinha.importada/) | `@cozinha.internacional` | receitas do mundo | narracao + conversao de medidas |
| [Sem Anestesia](semanestesia.pod/) | `@semanestesia.pod` | comportamento e mente | fala literal + voice over |
| [Ate Falhar](atefalhar/) | `@atefalhar` | disciplina, corpo e dor | fala literal + voice over |
| [Truque Importado](truque.importado/) | `@truque.importado` | maquiagem | narracao + **voz feminina** |

## A regra que vale pros cinco

⚠️ O Truque Importado ainda NAO EXISTE — a receita esta' escrita antes de
criar, de proposito. Ver o README dele.

**O valor de `canal` tem que ser identico ao NOME do canal no Buffer.** A
guarda em `agendar_buffer.py` compara os dois e aborta antes de publicar se
divergirem. Ela e' de FALHA FECHADA: sem `CANAL_ESPERADO` nada muda, com ele
um destino errado nao publica.

Publicar no canal errado nao tem desfazer bonito: o post sai, o alcance conta,
e apagar deixa o video em 0 pra sempre.

⚠️ O nome no Buffer nem sempre e' igual ao @ do TikTok. A cozinha e' o caso:
`@cozinha.internacional` no TikTok, `cozinha.importada` no Buffer. **O valor
segue o Buffer.**

## Cadencia, igual nos quatro que existem

4 posts/dia, **intervalo minimo de 3 horas**. Teto do plano do Buffer: **10
posts agendados por canal** — e' limite de FILA, nao de total: a cada post
enviado, um slot volta.

## Rotulo de IA

`metadata.tiktok.isAiGenerated = true` em **todo** post de todos. A interface
do Buffer nao expoe esse campo; so' a API expoe.
