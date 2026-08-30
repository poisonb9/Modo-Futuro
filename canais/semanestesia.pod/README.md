# Sem Anestesia — `@semanestesia.pod`

Cortes de podcast estrangeiro sobre comportamento, mente e vida. Terceiro
canal, aberto em 30/08/2026.

## Receita de disparo

| parametro | valor |
|---|---|
| `canal` | `semanestesia.pod` |
| `idioma` | o da fonte (`en` na maioria) |
| `dublar` | `true` |
| `fala_literal` | **`true`** |
| `voice_over` | **`true`** |
| `recorte` | **use** — ver o teto de 6h |

`fala_literal=true` porque aqui a fala da pessoa **e'** o argumento: dubla o
que ela realmente disse, em vez da narracao de contexto que e' o padrao da
casa. E' excecao editorial deliberada, nao esquecimento.

`voice_over=true` mantem o audio original audivel por baixo da dublagem. A voz
da pessoa faz parte do que se esta' vendendo.

⚠️ `voice_over` **EXIGE** `fala_literal=true`. Com narracao de contexto as duas
faixas se contradizem, e o motor recusa.

## ⚠️ O TETO DE 6 HORAS

O GitHub Actions mata qualquer job em **6 horas** (o workflow nao declara
`timeout-minutes`, entao vale o limite duro da plataforma). Em 30/08/2026 dois
runs deste canal morreram nele:

| run | fonte | duracao da fonte | resultado |
|---|---|---|---|
| #183 Tara Swart | podcast inteiro | 124,6 min | ❌ **6h00m16s** |
| #186 Goggins | podcast inteiro | 157,6 min | ❌ **6h00m18s** |

Os dois foram cancelados no mesmo minuto de vida. Nao e' coincidencia nem
defeito do motor: e' um teto.

**Nenhum dos dois terminou o PRIMEIRO clipe** — nenhum imprimiu a linha
`N frase(s)`, que so' sai quando a dublagem do clipe fecha.

Para comparar, no mesmo passo de corte:

| run | fonte | flags | resultado |
|---|---|---|---|
| #184 | PT, 30,5 min | `--dublar` | 83 min ✅ |
| #185 | EN, 22,7 min | `--dublar` (voz clonada tambem) | **2h01**, 5 clipes ✅ |

O #185 sintetizou 8 a 10 frases por clipe. Fala literal de podcast e' fala
CONTINUA, entao rende muito mais frases — e o Chatterbox sintetiza frase a
frase, em CPU de 2 nucleos.

### A regra pratica

**Nao dispare sobre podcast inteiro.** Use `recorte INICIO-FIM` (em segundos),
que pula a selecao do Gemini e ataca so' o trecho.

⚠️ **O que ainda NAO foi isolado:** os dois runs mudaram fonte longa E receita
literal ao mesmo tempo. Com o que existe, nao da' pra dizer qual das duas pesa
mais. Os runs #188 e #189 (recorte de ~85s, receita literal intacta) foram
disparados justamente para separar isso.

## Onde nasceu a receita

O Bryan ouviu os cortes do #184 e gostou: *"estao com duas dublagens, um de um
homem e um de mulher, gostei da dinamica de mudar os locutores"*. Nao era
recurso do motor — era fonte em portugues, cujo audio original ficou intacto
com os dois locutores reais.

O motor **nao sabe** alternar vozes hoje. Ver `VOZ_MULTIPLA.md` fora do repo.
