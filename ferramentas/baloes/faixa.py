p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')
a = '    <div class="baloes" aria-hidden="true">\n'
assert t.count(a) == 1
t = t.replace(a, a + '      <picture class="faixa-inaug"><source media="(max-width: 759px)" srcset="/baloes/faixa_inauguracao_p.webp"><img src="/baloes/faixa_inauguracao.webp" alt="" decoding="async" fetchpriority="low"></picture>\n')
b = '  .baloes { position: absolute; inset: 0; pointer-events: none; }\n'
assert t.count(b) == 1
t = t.replace(b, b + '''  /* ⭐ A FAIXA "INAUGURACAO" (24/09/2026, arte do Bryan). O arco dela
     CONTORNA o logo por cima: as letras do meio passam acima do brasao e as
     pontas descem pelos lados. No celular as pontas encostam na estrela e na
     boca e ficam ATRAS delas (a faixa vem antes dos .lado no HTML), entao le'
     como faixa amarrada nos dois baloes -- sem empurrar o topo para baixo
     ("topo entrega produto"). O vao entre as pontas e' ~49% da largura: cabe
     o logo de 86 px a partir de ~180 px de faixa. */
  .faixa-inaug { position: absolute; left: 50%; top: 6px; width: 212px;
    transform: translateX(-50%); display: block; }
  .faixa-inaug img { width: 100%; height: auto; display: block; }
  @media (prefers-reduced-motion: no-preference) {
    .faixa-inaug { animation: faixaBalanca 7.8s ease-in-out -2.4s infinite alternate; }
  }
  @keyframes faixaBalanca {
    from { transform: translateX(-50%) translateY(-2px) rotate(-.8deg); }
    to   { transform: translateX(-50%) translateY(2px) rotate(.8deg); }
  }
  @media (max-height: 740px) and (max-width: 759px) { .faixa-inaug { top: 0; width: 170px; } }
  @media (min-width: 760px) { .faixa-inaug { top: 2px; width: 290px; } }
''')
t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
