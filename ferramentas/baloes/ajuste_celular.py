p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')
ini = t.index('  @media (max-width: 759px) {\n    .festa .balao:nth-child(4), .canais .balao:nth-child(5) {')
fim = t.index('  @media (max-height: 740px) { .lado { top: 8px;')
novo = '''  @media (max-width: 759px) {
    /* 24/09 04:02 (print do Bryan, iPhone 14 e 12): cupom descia sobre o "Eu"
       e o cifrao ficava solto no meio. Agora os dois ESPELHADOS, colados na
       borda de fora (5vw acompanha a largura do aparelho, inclusive o zoom de
       tela do iPhone 12) e na altura de "ACHADINHO TOTAL" -- a linha curta,
       onde sobra lateral. Tamanho casado pela ALTURA VISIVEL do balao: o
       cupom e' largo, o cifrao e' alto, entao caixas diferentes. */
    .festa .balao:nth-child(4), .canais .balao:nth-child(5) {
      display: flex; position: absolute; top: 92px; opacity: .9;
    }
    .festa .balao:nth-child(4) { left: 5vw; }
    .canais .balao:nth-child(5) { right: 5vw; }
    .festa .balao:nth-child(4) .flutua { --t: 34px; }
    .canais .balao:nth-child(5) .flutua { --t: 26px; }
    /* ⛔ Safari iOS: drop-shadow + camada animada pinta um RETANGULO que tampa
       o clarao quente atras do titulo (print 04:02, estrela/boca/chef). A
       sombra num balao de 36 px nem se ve'; no celular sai. */
    .lado .flutua img { filter: none; }
  }
  /* ⭐ SOLTAR NA ROLAGEM. Com suporte (Safari 26+/iOS 26, Chrome 115+) e' CSS
     puro; sem suporte (iPhone em iOS antigo) o script no fim da pagina
     escreve --solta (0..1) no .baloes a cada quadro de rolagem -- o MESMO
     efeito, com a mesma curva. */
  @keyframes soltar { to { transform: translateY(-150px) scale(.8); opacity: 0; } }
  @supports (animation-timeline: scroll()) {
    @media (max-width: 759px) and (prefers-reduced-motion: no-preference) {
      .festa .balao:nth-child(4), .canais .balao:nth-child(5) {
        animation: soltar linear both; animation-timeline: scroll(root);
        animation-range: 0 320px;
      }
    }
  }
  @supports not (animation-timeline: scroll()) {
    @media (max-width: 759px) and (prefers-reduced-motion: no-preference) {
      .festa .balao:nth-child(4), .canais .balao:nth-child(5) {
        transform: translateY(calc(var(--solta, 0) * -150px)) scale(calc(1 - var(--solta, 0) * .2));
        opacity: calc(.9 - var(--solta, 0) * .9);
      }
    }
  }
  @media (max-height: 740px) and (max-width: 759px) {
    .festa .balao:nth-child(4), .canais .balao:nth-child(5) { top: 70px; } }
'''
t = t[:ini] + novo + t[fim:]
js = '''<script>
/* 24/09: fallback do "soltar na rolagem" para Safari sem animation-timeline
   (ver CSS "SOLTAR NA ROLAGEM"). So' celular, so' sem reduced-motion. */
(function () {
  try {
    if (window.CSS && CSS.supports && CSS.supports("animation-timeline: scroll()")) { return; }
    var mq = matchMedia("(max-width: 759px) and (prefers-reduced-motion: no-preference)");
    var alvo = document.querySelector(".baloes"); if (!alvo) { return; }
    var pedido = false;
    function pinta() { pedido = false;
      var s = mq.matches ? Math.min(1, Math.max(0, (window.scrollY || 0) / 320)) : 0;
      alvo.style.setProperty("--solta", s.toFixed(3)); }
    addEventListener("scroll", function () { if (!pedido) { pedido = true; requestAnimationFrame(pinta); } }, { passive: true });
    pinta();
  } catch (e) {}
})();
</script>
</html>'''
assert t.count('</html>') == 1 and t.rstrip().endswith('</html>')
t = t.replace('</html>', js)
t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
