# Backup do que está no ar — achadinhototal.com.br

Pedido do Bryan em 20/09/2026: *"deixa uma cópia de backup na pasta do projeto
de tudo que você subiu pra nuvem ... pra um dia precisar refazer"*.

Gerado por `ferramentas/backup_do_ar.py`. Para atualizar:

```
python -X utf8 ferramentas/backup_do_ar.py
```

## O que tem aqui

| arquivo | o que é |
|---|---|
| `MANIFESTO.json` | URL, tamanho, tipo, `Cache-Control` e **sha256** de cada arquivo, mais o commit que os gerou |
| `index.html` | o site mãe (catálogo) como o visitante recebe |
| `motor.js` | o motor da página, servido separado desde 20/09 |
| `links.json` | os links de afiliado (ficam fora do HTML desde 19/09) |
| `*.json` | as categorias externas (Kabum, Nike, Lauri, Arno, SharkNinja, Exypna) |
| `robots.txt`, `sitemap.xml`, `icone.png` | indexação e ícone |
| `parceiros/`, `privacidade/` | as duas rotas fixas |
| `bios/<canal>/` | as 5 bios, cada uma com `index.html`, `todos.html` e `parceiros.html` |
| `cloudflare.json` | a configuração da conta: projetos Pages, domínios ligados, branch, rulesets |

**Os bytes vêm DO AR, não da pasta de build.** A pasta de build é apagada no
fim de cada publicação, e o que interessa guardar é o que o visitante recebeu.
É a mesma doutrina da verificação de publicação: a prova é o byte servido.

## O que este backup NÃO tem — e isso importa na hora de refazer

- **Registros de DNS** e **configurações de SSL/TLS** da zona. O token de
  publicação responde **403** neles (só tem Pages e leitura parcial de zona).
  Refazer do zero exige recriar isso à mão no painel.
- A **Redirect Rule `www` → raiz** continua pendente no painel (ver
  `PARA_FAZER_NO_CLOUDFLARE.md`); hoje o desvio é feito por JavaScript.
- **Nenhum segredo.** Token e id da conta ficam no `.env` e o script aborta se
  algum deles aparecer na saída — isso tem caso negativo provado.

## Como refazer, se um dia precisar

1. Recriar a zona `achadinhototal.com.br` no Cloudflare e apontar os
   nameservers (`carl.ns.cloudflare.com`, `joyce.ns.cloudflare.com`).
2. Criar os projetos Pages com os nomes de `cloudflare.json` e ligar os
   domínios listados em `domains`.
3. Publicar pelo repositório: `python -X utf8 paginas/publicar_bio.py --subir`.
   O conteúdo se refaz sozinho — os arquivos daqui servem de conferência
   (compare os sha256) e de socorro se o motor estiver quebrado.
