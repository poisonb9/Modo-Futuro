# RETOMADA — 24/09/2026, balões parte 2 (fios, bios, varal, estrelas, %)

O anterior é [`RETOMADA_24-09-2026_BALOES.md`](RETOMADA_24-09-2026_BALOES.md).
Os dois bugs da barra de abas de [`RETOMADA_23-09-2026_PARTE3.md`](RETOMADA_23-09-2026_PARTE3.md)
continuam ABERTOS (não mexi). Os 2 testes vermelhos antigos também
(`teste_legenda_uma_linha`, `teste_categoria_externa`).

## 0. Estado no fechamento (08:45 UTC)

- Último commit de site: `32f2ea9` (% + letras vivas), já no GitHub.
- O vigia estava PUBLICANDO às 08:40 (primeiro ciclo depois de reativado).
  ⛔ **Primeira coisa da próxima sessão:** conferir no ar:
  `curl -s https://achadinhototal.com.br/ | grep -c inaug_porcento` ≥ 1 e
  `grep -c estrela-centro` ≥ 1; `/baloes/inaug_porcento.webp` = `image/webp`.
  Se não: `estado/publicar_ao_mudar.log` — agora o publicador IMPRIME o erro
  do wrangler (linhas `NAO publicou:` e `wrangler Error:`).
- O vigia (`AchadinhoTotal_Publicar_Ao_Mudar`) ficou DESATIVADO de 08:10 a
  08:33 a pedido do Bryan ("não publique ainda"). Foi reativado — conferir
  `Get-ScheduledTask ... | select State` = Ready.
- `git stash list` tem 3 entradas velhas. `stash@{0}` (de f452376) é só uma
  cópia VELHA de `site_no_ar/` — o DIARIO e o `estado/fotos_ocr.json` dele JÁ
  foram devolvidos à árvore. O modo automático recusou o `stash drop`; o
  Bryan pode rodar `git stash drop stash@{0}`. Os outros dois são anteriores.

## 1. O que foi ao ar nesta sessão (todos verificados no ar, salvo o item 0)

1. **Balões dos 24/09 no ar** — o deploy de 01:10 tinha caído com rc=1 (causa
   nunca vista: o stderr era engolido). Republiquei à mão 01:58, OK.
2. **Publicador imprime o erro do wrangler** (`publicar_bio.py`, `publicar_no_ar`).
   As linhas levam "NAO " e "Error" de propósito: é o filtro do log do vigia.
3. **Fio dos balões = o fio da FOTO ORIGINAL**, recuperado pelo contorno cinza
   da fita (o branco sumia no recorte). Bryan RECUSOU fio desenhado/ondulado.
   Webp = quadrado de antes (balão embaixo) + fio abaixo; CSS `width:100%;
   height:auto` → balão do mesmo tamanho, fio transborda.
4. **Versão `_p` (96 px) de cada balão para o celular**, com o fio engrossado
   ANTES de reduzir (MaxFilter): o fio de 2–3 px em 360 virava sub-pixel e o
   iPhone apagava. `<picture><source media="(max-width: 759px)">`.
5. **Bio de cada canal com o próprio balão** (`contra_capa.html`, `BALOES_CANAL`),
   ao lado do brasão. Até Falhar (sem balão) → lupa. Links conferidos:
   oachadinho, achadinhochef, pagomenos, achadinhodehoje, meulivro `.pages.dev`.
6. **Estado vazio** com a lupa pequena; **"se voltar a R$ X"** solta o cupom uma
   vez (listener delegado no documento); **404 só no site mãe**
   (`paginas/nao_achei.html` → `/404.html`, estrela, "Essa página voou.").
   ⛔ NUNCA pôr 404.html nas BIOS: `/c1`…`/c7` dependem de o Pages servir a
   raiz para caminho inexistente.
7. **Celular: cupom (etiqueta) e CIFRÃO** em segundo plano, espelhados na
   borda (5vw), altura de "ACHADINHO TOTAL", e SE SOLTAM na rolagem
   (`animation-timeline: scroll()`; acervo Kevin Powell, DEMONSTRADO). MF foi
   trocado pelo cifrão a pedido do Bryan. Cifrão tem caixa menor (é alto).
   **Fallback JS** no fim do `todos.html` para Safari sem o recurso (iPhone 12
   em iOS < 26): escreve `--solta` 0..1. ⚠️ Não testado em Safari antigo real
   — pedir ao Bryan para rolar no iPhone 12.
8. **Sem drop-shadow nos balões do celular**: no Safari iOS a sombra + camada
   animada pintava RETÂNGULOS claros que tampavam o `.clarao` (print 04:02).
9. **INAUGURAÇÃO = VARAL de 11 balões-letra** (a faixa inteira ficou "feia,
   espremida"). Letras recortadas da 1ª imagem do Bryan por erosão + dono mais
   próximo (as vizinhas se tocavam), MESMA escala (Ç e Ã não encolhem).
   `letra_01..11(.webp|_p.webp)`. Arco `--arco`, `--dy` recentra Ç/Ã.
   Celular: o varal toma o lugar da ESTRELA e da BOCA (`visibility:hidden`).
   PC: header desce para 80 px de padding-top. Balão laranja perdeu o escrito.
10. **Letras com vida própria**: dois movimentos independentes por letra
    (`translate` e `rotate`, períodos sorteados semente 2409, 3.1–5.3 s e
    4.3–7.9 s, 1–2 px, 1.5–3°). O painel de prévia tem reduced-motion ligado:
    a animação NÃO foi vista rodando, só os valores conferidos.
11. **PC ≥1280: duas estrelas no centro** (onde o Bryan marcou, ±~450 px do
    meio, top 110). **Balão "%" dourado** (`inaug_porcento`) no lugar da
    estrela na coluna esquerda.

## 2. Armadilhas medidas nesta sessão (não repetir)

- `sed -i` no `todos.html` converteu CRLF→LF (diff de 12.540 linhas). O
  arquivo é CRLF: editar em BYTES (python `rb`/`wb`) e conferir a contagem de
  `\r\n` antes/depois. `git diff --stat` com 1 arquivo gigante = alarme.
- `grep -v _p` excluiu `canal_pago_menos` (contém "_p"). Filtrar por sufixo.
- Heredoc/sed comendo `\n` dentro de string Python → escrever o script em
  arquivo (Write) e rodar.
- Stash/pull no meio do BACKUP do vigia (`site_no_ar/`): o pull falhou e o pop
  não voltou. Antes de stash/pull, conferir processos `publicar_bio|wrangler|
  backup_do_ar`. `git pull --rebase --autostash` funcionou melhor.
- Prévia local: `python -m http.server 8765` em `%TEMP%\prev` (cópia de
  `todos.html`, `contra_capa.html` em `/bio/`, `baloes/`). O logo NÃO carrega
  local (vem de fora) — simular com JS para medir encaixe.
- O painel de prévia não desenha quadros quando escondido: animação por
  rolagem ficou com `currentTime` nulo até tirar um screenshot.

## 3. PENDENTE

- **Balões para os vídeos do TikTok** (pedido de antes desta sessão): o Bryan
  ainda vai mandar QUANTOS, QUAIS e EM QUE MOMENTO. Plano combinado no handoff
  anterior (movimento por código, MP4 verde + .mov alfa, render na nuvem).
- **Black Friday**: o Bryan gerou e guardou 4 balões (varal "BLACK FRIDAY",
  etiqueta preta com % dourado, sacola preta com alças douradas, raio
  dourado). Manda semanas antes. Memória:
  `modofuturo-black-friday-baloes-campanha`. Prompts: alça = "same inflated
  foil material" (NUNCA "rope-style"); raio = "classic lightning bolt icon"
  (sem "black outline"). Pedir o arquivo original, não print.
- **Balão do Achadinho Total** (brasão virado balão): prompt entregue; se o
  Bryan mandar, pode substituir algum da coluna.
- Sobras recortadas sem uso: `inaug_verde`, `inaug_airfryer` (em
  `Desktop\inauguracao\recortados`).
- Até Falhar e Modo Futuro não têm host de bio no ar (a página já sabe o
  balão deles).

## 4. Ferramentas desta sessão (em `%TEMP%\fio\`, descartáveis)

`fio.py` (recupera o fio da foto), `pequeno.py` (gera `_p`), `letras.py`
(separa letras), `varal.py`, `estrelas.py`, `ajuste_celular.py`. Originais dos
balões: `Desktop\inauguracao\` e `\recortados\`. Se precisar refazer, a
lógica está descrita nos comentários do `todos.html`.
