# Troca os 2 baloes FIXOS da rolagem (PC) por UM BALAO POR BLOCO da grade.
p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')

# 1. sai o HTML fixo
import re
m = re.search(r'<div class="sobe-rolagem" aria-hidden="true">.*?</div>\n', t)
assert m; t = t.replace(m.group(0), '')
# 2. sai o CSS fixo (inclui o premium), do marcador ate' o varal
i = t.index('  /* ⭐ BALOES QUE SOBEM COM A ROLAGEM'); j = t.index('  /* ⭐ O VARAL "INAUGURACAO"')
velho_css = t[i:j]
assert 'subirTela' in velho_css and 'sobeDeriva' in velho_css
novo_css = '''  /* ⭐ UM BALAO POR BLOCO DE PRODUTOS (24/09/2026, Bryan: "um balao por bloco
     ate' o 3o bloco; se estender, repete o primeiro; posicao aleatoria, sem
     dois visiveis na mesma tela -- vao fazer as pessoas olharem mais o bloco").
     Substitui os 2 baloes FIXOS da rolagem. A grade nao tem blocos no DOM (os
     cartoes entram direto no #grade), entao "bloco" = ~1,4 altura de tela:
     o script `baloesPorBloco` espalha um balao a cada bloco, na MARGEM (so'
     >= 1440, onde a grade de 1180 deixa lateral), lado alternado, tipo em
     ciclo. Cada um sobe enquanto o PROPRIO trecho passa pela tela
     (animation-timeline: view()) -- um de cada vez, por construcao.
     Premium (mantido): deriva lateral e balanco pelo RELOGIO no <img>. */
  .balao-bloco { display: none; }
  @media (min-width: 1440px) {
    #grade { position: relative; }
    .balao-bloco { display: block; position: absolute; width: 92px; pointer-events: none; z-index: 0; }
    .balao-bloco.esq { left: calc((1180px - 100vw) / 4 - 46px); }
    .balao-bloco.dir { right: calc((1180px - 100vw) / 4 - 46px); }
    .balao-bloco img { width: 100%; height: auto; display: block; transform-origin: 50% 90%;
      filter: drop-shadow(0 14px 18px rgba(20, 16, 30, .12)); }
  }
  @supports (animation-timeline: view()) {
    @media (min-width: 1440px) and (prefers-reduced-motion: no-preference) {
      .balao-bloco { animation: blocoSobe linear both; animation-timeline: view();
        animation-range: cover 0% cover 100%; }
    }
  }
  @media (min-width: 1440px) and (prefers-reduced-motion: no-preference) {
    .balao-bloco img { animation: sobeDeriva 4.9s ease-in-out infinite alternate,
                                  sobeBalanco 3.7s ease-in-out infinite alternate; }
    .balao-bloco:nth-of-type(2n) img { animation-duration: 5.6s, 4.3s; animation-delay: -2.1s, -1.3s; }
  }
  @keyframes blocoSobe {
    0%   { transform: translateY(30vh) scale(.92); opacity: 0; }
    5%   { opacity: 1; }
    95%  { opacity: 1; }
    100% { transform: translateY(-30vh) scale(1.04); opacity: 0; }
  }
  @keyframes sobeDeriva  { from { translate: -10px 0; } to { translate: 10px 0; } }
  @keyframes sobeBalanco { from { rotate: -5deg; } to { rotate: 5deg; } }
'''
t = t[:i] + novo_css + t[j:]
# 3. sai o trecho --prog do fallback
v = '''
      var sr = document.querySelector(".sobe-rolagem");
      if (sr) { var tot = Math.max(1, document.documentElement.scrollHeight - innerHeight);
        sr.style.setProperty("--prog", Math.min(1, y / tot).toFixed(4)); } }'''
assert t.count(v) == 1
t = t.replace(v, ' }')
# 4. o script que espalha os baloes
ancora = '''  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ligarTremor);
  } else { ligarTremor(); }
'''
assert t.count(ancora) == 1
js = '''
  /* ⭐ BALOES POR BLOCO (24/09/2026) -- ver o CSS `.balao-bloco`. Um a cada
     ~1,4 tela de grade, lado ALTERNADO, altura sorteada sem nunca juntar dois,
     tipo em ciclo: 1o, 2o, 3o, e recomeca. Refaz quando a grade cresce
     ("ver mais") ou a janela muda; ignora as proprias insercoes. */
  var BALOES_BLOCO = ["inaug_laranja", "inaug_porcento", "inaug_estrela"];
  var mqBloco = window.matchMedia ? matchMedia("(min-width: 1440px)") : null;
  var alturaBloco = 0, qtdBloco = 0;
  function baloesPorBloco() {
    var g = document.getElementById("grade");
    if (!g || !mqBloco || !mqBloco.matches) { return; }
    // passo = 1,4 tela; o sorteio de altura nunca deixa o vao entre dois
    // baloes menor que 1 tela + 220 px (altura do balao): nunca dois juntos.
    var h = g.offsetHeight, passo = Math.round(innerHeight * 1.4);
    var folga = Math.max(0, passo - innerHeight - 220);
    var n = Math.max(0, Math.floor((h - 200) / passo));
    if (n === qtdBloco && Math.abs(h - alturaBloco) < passo / 2) { return; }
    alturaBloco = h; qtdBloco = n;
    Array.prototype.slice.call(g.querySelectorAll(".balao-bloco")).forEach(function (b) { b.remove(); });
    // lado ALTERNA (Bryan: "um de um lado, um do outro"); so' o 1o e' sorteado
    var comeca = Math.random() < .5 ? 0 : 1;
    for (var i = 0; i < n; i++) {
      var lado = (i + comeca) % 2 ? "dir" : "esq";
      var s = document.createElement("span");
      s.className = "balao-bloco " + lado; s.setAttribute("aria-hidden", "true");
      s.style.top = (200 + i * passo + Math.round(Math.random() * folga)) + "px";
      var im = document.createElement("img");
      im.src = "/baloes/" + BALOES_BLOCO[i % BALOES_BLOCO.length] + ".webp";
      im.alt = ""; im.loading = "lazy"; im.decoding = "async";
      s.appendChild(im); g.appendChild(s);
    }
  }
  function ligarBaloesBloco() {
    var g = document.getElementById("grade");
    if (!g || !mqBloco) { return; }
    var pedido = false;
    var refaz = function () { if (pedido) { return; } pedido = true;
      setTimeout(function () { pedido = false; baloesPorBloco(); }, 400); };
    new MutationObserver(function (lista) {
      for (var k = 0; k < lista.length; k++) {
        var ns = lista[k].addedNodes;
        for (var m = 0; m < ns.length; m++) {
          if (!(ns[m].classList && ns[m].classList.contains("balao-bloco"))) { refaz(); return; }
        }
      }
    }).observe(g, { childList: true });
    addEventListener("resize", refaz, { passive: true });
    if (mqBloco.addEventListener) { mqBloco.addEventListener("change", refaz); }
    refaz();
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", ligarBaloesBloco);
  } else { ligarBaloesBloco(); }
'''
t = t.replace(ancora, ancora + js)
t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
