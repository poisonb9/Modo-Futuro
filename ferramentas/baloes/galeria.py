# Aplica a GALERIA DO DESTAQUE (24/09/2026) em publicar_bio.py e todos.html.
# Edita em BYTES e confere o CRLF (o todos.html e' CRLF; `sed` ja' estragou).
import sys
R = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/'


def trocar(nome, pares):
    p = R + nome
    b = open(p, 'rb').read()
    crlf = b.count(b'\r\n') > 0
    t = b.decode('utf-8').replace('\r\n', '\n')
    n0 = t.count('\n')
    for velho, novo in pares:
        assert t.count(velho) == 1, (nome, t.count(velho), velho[:70])
        t = t.replace(velho, novo)
    if crlf:
        t = t.replace('\n', '\r\n')
    open(p, 'wb').write(t.encode('utf-8'))
    print(nome, 'ok', n0, '->', t.count('\r\n' if crlf else '\n'))


# ---------------- publicador ----------------
PY_FUNC = '''

# ⭐ A GALERIA DO DESTAQUE NO PC (24/09/2026, Bryan: "em vez dessa imagem
# gigante e muitas vezes desconexa ou esticada, varias imagens do mesmo
# anuncio de maneira organizada"). As fotos JA' existiam: `precos.puxar`
# guarda `product_small_image_urls` do Ali em `precos_agora.json` desde
# 18/09 (MEDIDO hoje: 164 de 168 produtos, 157 com 5), e so' serviam para
# escolher a capa. Sobem num arquivo AO LADO, que so' o PC baixa: no celular
# o custo e' zero.
#
# Acervo: Maestros/WooCommerce (DEMONSTRADO) -- principal + secundarias; e a
# regra de quando NAO usar: "se os produtos nao tiverem imagens secundarias".
# Por isso o piso: menos de GALERIA_MIN fotos boas = o produto fica com a
# foto unica de sempre.
#
# ⛔ QUEM SAI: foto JULGADA pelo modelo de visao (`foto_julga`) que e'
# colagem ou tem nota abaixo de GALERIA_NOTA_MIN. Foto NAO julgada entra,
# depois das julgadas boas: na galeria, detalhe com medida escrita ajuda; o
# que desmonta a vitrine e' colagem e banner. (Hoje so' 53 das 809 extras
# estao julgadas -- rodar `foto_julga.medir` nelas melhora o filtro.)
GALERIAS_ARQUIVO = "galerias.json"
GALERIA_MIN = 3
GALERIA_MAX = 5
GALERIA_NOTA_MIN = 5


def montar_galerias(dados: list[dict]) -> dict[str, list[str]]:
    from engine import foto_julga
    agora = _precos_agora()
    fim: dict[str, list[str]] = {}
    for p in dados:
        pid = str(p.get("id") or "")
        principal = p.get("imagem") or ""
        extras = (agora.get(pid) or {}).get("imagens") or []
        if not pid or not principal or not extras:
            continue
        boas, sem_julgamento = [], []
        for u in extras:
            if not u or u == principal:
                continue
            j = foto_julga.julgado(u)
            if not j:
                sem_julgamento.append(u)
            elif not j.get("colagem") and int(j.get("nota") or 0) >= GALERIA_NOTA_MIN:
                boas.append((int(j.get("nota") or 0), u))
        boas.sort(key=lambda x: -x[0])
        fotos = [principal] + [u for _, u in boas] + sem_julgamento
        vistas, lista = set(), []
        for u in fotos:
            if u not in vistas:
                vistas.add(u)
                lista.append(u)
        if len(lista) >= GALERIA_MIN:
            fim[pid] = lista[:GALERIA_MAX]
    return fim
'''

trocar('publicar_bio.py', [
    ('\ndef montar_catalogo() -> tuple[str, dict[str, str]]:',
     PY_FUNC + '\n\ndef montar_catalogo() -> tuple[str, dict[str, str]]:'),
    ('''    if links:
        arquivos[LINKS_ARQUIVO] = json.dumps({"links": links}, ensure_ascii=False)
''', '''    if links:
        arquivos[LINKS_ARQUIVO] = json.dumps({"links": links}, ensure_ascii=False)
    galerias = montar_galerias(dados)
    if galerias:
        arquivos[GALERIAS_ARQUIVO] = json.dumps({"galerias": galerias}, ensure_ascii=False)
    print(f"galerias: {len(galerias)} produto(s) com {GALERIA_MIN}+ fotos boas")
'''),
    ('''                        ('  var LINKS_ARQUIVO = "";',
                         '  var LINKS_ARQUIVO = "' + (LINKS_ARQUIVO if links else "") + '";'),
''', '''                        ('  var LINKS_ARQUIVO = "";',
                         '  var LINKS_ARQUIVO = "' + (LINKS_ARQUIVO if links else "") + '";'),
                        ('  var GALERIAS_ARQUIVO = "";',
                         '  var GALERIAS_ARQUIVO = "' + (GALERIAS_ARQUIVO if galerias else "") + '";'),
'''),
])

# ---------------- pagina: CSS ----------------
CSS = '''
  /* ⭐ A GALERIA DO DESTAQUE (24/09/2026, so' PC >= 1024; celular fica como
     esta', pedido do Bryan). Foto grande QUADRADA + grade 2x2 de miniaturas
     quadradas, todas `contain` sobre branco: nada esticado, nada cortado (o
     8:3 do `fundo-cena` cortava; o `contain` largo deixava a foto miuda e
     "desconexa"). Altura ~ a do heroi antigo, para a troca pos-carga nao
     empurrar a pagina. As classes `fundo-*` sao neutralizadas aqui: elas
     desenhavam o heroi de UMA foto. */
  .vgal { display: none; }
  @media (min-width: 1024px) {
    #vitrine .vitrine.com-galeria .vgal {
      display: flex; justify-content: center; gap: 12px;
      --gh: clamp(320px, 40vh, 440px); height: var(--gh);
      padding: 14px 14px 0; background: #fff; box-sizing: content-box;
    }
    #vitrine .vitrine.com-galeria .vgal .vfoto {
      height: 100%; width: auto; aspect-ratio: 1; object-fit: contain;
      padding: 3%; box-sizing: border-box; clip-path: none; border-radius: 16px;
      background: #fff; view-transition-name: vgal-grande;
    }
    #vitrine .vitrine.com-galeria > .vfoto { display: none; }
    .vmini { display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr;
      gap: 12px; height: 100%; aspect-ratio: 1; }
    .vmini button { all: unset; box-sizing: border-box; cursor: pointer; border-radius: 14px;
      background: #fff; border: 1px solid var(--linha, rgba(0,0,0,.08)); padding: 7%;
      display: grid; place-items: center; transition: border-color .2s, transform .2s; }
    .vmini button:hover { transform: translateY(-2px); border-color: var(--fraco); }
    .vmini button[aria-current="true"] { border-color: #c8921c; box-shadow: 0 0 0 1px #c8921c inset; }
    .vmini button:focus-visible { outline: 2px solid #c8921c; outline-offset: 2px; }
    .vmini img { width: 100%; height: 100%; object-fit: contain; display: block; }
  }
'''
# entra logo depois das regras de PC do heroi (8:3 etc.)
ancora_css = '    .vitrine.fundo-estudio .vfoto { aspect-ratio: 2 / 1; }\n'

JS_VAR = '  var LINKS_ARQUIVO = "";\n'
JS_FUNC = '''
  /* ⭐ GALERIA DO DESTAQUE (24/09/2026). Liga do MESMO jeito que o
     classificador de fundo acima: a primeira tela vem pronta do SERVIDOR e o
     `montar` nao roda nela -- a galeria tem de pegar qualquer vitrine que
     aparecer no #vitrine. So' PC (>= 1024): no celular nem baixa o arquivo.
     A miniatura do Ali vem em 350 px (`_350x350.jpg`: 30 KB contra 109 KB). */
  var GALERIAS = null, GALERIAS_PEDIDO = false;
  var mqGaleria = window.matchMedia ? matchMedia("(min-width: 1024px)") : null;
  function miniaturaDe(u) {
    return /aliexpress-media\\.com|alicdn\\.com/.test(u) && /\\.(jpe?g|png|webp)$/i.test(u) ? u + "_350x350.jpg" : u;
  }
  function aplicarGaleria() {
    if (!GALERIAS || !mqGaleria || !mqGaleria.matches) { return; }
    var alvo = document.getElementById("vitrine");
    var a = alvo && alvo.querySelector(".vitrine");
    if (!a || a.querySelector(".vgal")) { return; }
    var fotos = GALERIAS[a.getAttribute("data-pid") || ""];
    var velha = a.querySelector("img.vfoto");
    if (!fotos || fotos.length < 3 || !velha) { return; }
    var gal = el("div", "vgal");
    var grande = document.createElement("img");
    grande.className = "vfoto"; grande.alt = velha.alt || ""; grande.src = fotos[0];
    grande.decoding = "async";
    gal.appendChild(grande);
    var mini = el("div", "vmini");
    fotos.slice(1, 5).forEach(function (u, i) {
      var b = document.createElement("button");
      b.type = "button"; b.setAttribute("aria-label", "ver foto " + (i + 2));
      var im = document.createElement("img");
      im.src = miniaturaDe(u); im.alt = ""; im.loading = "lazy"; im.decoding = "async";
      b.appendChild(im);
      b.addEventListener("click", function (ev) {
        // o cartao inteiro e' um link: a miniatura troca a foto, NAO navega
        ev.preventDefault(); ev.stopPropagation();
        var troca = function () {
          var antes = grande.src;
          grande.src = u; im.src = miniaturaDe(antes);
          u = antes;
        };
        if (document.startViewTransition && !matchMedia("(prefers-reduced-motion: reduce)").matches) {
          document.startViewTransition(troca);
        } else { troca(); }
      });
      mini.appendChild(b);
    });
    gal.appendChild(mini);
    a.insertBefore(gal, velha);
    a.classList.add("com-galeria");
  }
  function pedirGalerias() {
    if (GALERIAS_PEDIDO || !GALERIAS_ARQUIVO || !mqGaleria || !mqGaleria.matches) { return; }
    GALERIAS_PEDIDO = true;
    fetch(GALERIAS_ARQUIVO, { cache: "no-cache" }).then(function (r) {
      if (!r.ok) { throw new Error("http " + r.status); }
      return r.json();
    }).then(function (j) { GALERIAS = (j && j.galerias) || {}; aplicarGaleria(); })
      .catch(function () { GALERIAS_PEDIDO = false; });
  }
  function ligarGaleria() {
    var alvo = document.getElementById("vitrine");
    if (!alvo) { return; }
    new MutationObserver(function () { aplicarGaleria(); }).observe(alvo, { childList: true });
    pedirGalerias();
    if (mqGaleria && mqGaleria.addEventListener) {
      mqGaleria.addEventListener("change", function () { pedirGalerias(); aplicarGaleria(); });
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ligarGaleria);
  } else { ligarGaleria(); }
'''
ancora_js = '''  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ligarClassificador);
  } else { ligarClassificador(); }
'''

trocar('todos.html', [
    (ancora_css, ancora_css + CSS),
    (JS_VAR, JS_VAR + '  var GALERIAS_ARQUIVO = "";\n'),
    (ancora_js, ancora_js + JS_FUNC),
])
