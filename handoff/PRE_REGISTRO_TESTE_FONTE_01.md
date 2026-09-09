# PRÉ-REGISTRO — Teste 01: fonte escolhida por ENGAJAMENTO, não por views

**Escrito em 09/09/2026. NADA foi disparado. Este documento existe para ser
aprovado ou recusado ANTES de qualquer corte.**

---

## 1. De onde veio a hipótese

A medição de 08-09/09 (18 posts do @modofuturo, `estado/seguidores_por_video.jsonl`)
eliminou quase tudo e deixou **um** sinal de pé:

    correlacao com SEGUIDOR        n=18    sem o outlier
      curtida %                   +0,35        +0,52
      completo %                  +0,22        +0,17
      tempo medio                 -0,06        +0,18
      views                       +0,95        +0,18   <- era so' o outlier

    mediana de curtida   COM seguidor 3,17%   SEM seguidor 1,77%

**Curtida é o único preditor de seguidor que temos.** E o radar mede
engajamento na fonte do YouTube — que é a mesma coisa, do outro lado do funil.

⚠️ Hoje o radar é lido por **views**, e views é justamente o que NÃO prevê
conversão. Olhando o `radar_modofuturo.json` pelos dois critérios, eles
discordam de forma brutal:

    titulo                                    views/h    eng
    Inside Samsung's Futuristic Factory        1690,6    0,78
    Inside a Modern Pringles Factory           1363,6    0,50
    How Lay's Potato Chips Are Made             719,1    0,69
    I shrunk down into an M5 chip                634,8    6,67   <- 8x o engajamento
    Making RAM at Home                          591,2    5,31
    China Just Built What ASML Feared Most      587,5    4,05

As fábricas ganham em volume e perdem em engajamento por quase 10x. São vídeo
de assistir passivamente. **É exatamente o perfil dos nossos posts que não
convertem.**

## 2. A hipótese, em uma frase

Fonte com engajamento alto no YouTube gera clipe com curtida alta no TikTok; e
curtida é o único sinal que prevê seguidor.

## 3. O teste

**Fonte:** `I shrunk down into an M5 chip` (eng 6,67 — o maior do radar).
Reserva: `Making RAM at Home` (5,31).

**Volume: 1 post. No máximo 2.** Ordem do Bryan, e ela é certa — mais que isso
vira mudança de linha editorial e deixa de ser teste.

**Canal:** @modofuturo (é dele que vêm os 18 posts de comparação).

**Slot:** o de sempre. ⚠️ NÃO usar o das 16:27 (melhor medido, 1,50x) — mexer
nele junto impede atribuir o efeito.

**Tudo o mais igual:** mesmo motor, mesmas calibragens, mesma voz.

## 4. O que se mede, e quando

**Em 48h:** `curtida %` do post (curtidas / views).
**No próximo export mensal:** `Novos seguidores`, lido na tela do Studio.

Comparação: contra os 18 posts de `estado/seguidores_por_video.jsonl`
(mediana de curtida do canal: **1,77% nos que não converteram, 3,17% nos que
converteram**).

## 5. ⚠️ A CONDIÇÃO QUE DERRUBA A HIPÓTESE

**Se a curtida do post ficar abaixo de 2,5%, a hipótese cai.** Quer dizer que
engajamento na fonte não atravessa para o clipe, e o radar continua sendo lido
por views porque não há nada melhor.

Escrito ANTES de rodar, de propósito: uma ressalva pessimista não incomoda
ninguém depois, e é por isso que ela tem que estar escrita antes.

## 6. O que este teste NÃO responde

- **Não responde por que o post de 22/08 converteu 28 vezes.** Aquilo continua
  inexplicado, e a §23.9 do playbook registra que o Studio foi esgotado.
- **Não separa "assunto" de "engajamento".** A fonte escolhida é de chip, igual
  ao miolo do canal — de propósito, para não trocar duas coisas ao mesmo tempo.
- **n=1.** Um post não prova nada sozinho. Ele decide se vale gastar um bloco
  de 5 no mês seguinte.

## 7. ⚠️ Ressalva de contaminação

Em 09/09 entraram DUAS mudanças globais de retenção (punch 6,5s->3,0s e card
de título 3,5s->2,0s, ver `estado/calibragens.jsonl`). Este post nasce depois
delas. Isso **não invalida** o teste — a comparação de curtida é contra a
mediana histórica do canal, e as duas mudanças afetariam qualquer post novo
igualmente — mas se a curtida subir, parte do efeito pode ser delas.

Para separar: qualquer post normal publicado depois de 09/09 serve de controle.
Basta comparar a curtida dele com a deste.

---

**Status: AGUARDANDO APROVAÇÃO DO BRYAN. Nada disparado.**
