p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')
a = '      <div class="varal">\n'
assert t.count(a) == 1
t = t.replace(a, '      <span class="estrela-centro esq"><img src="/baloes/inaug_estrela.webp" alt="" decoding="async" fetchpriority="low"></span>\n'
                 '      <span class="estrela-centro dir"><img src="/baloes/inaug_estrela.webp" alt="" decoding="async" fetchpriority="low"></span>\n' + a)
b = '  /* ⭐ O VARAL "INAUGURACAO"'
assert t.count(b) == 1
t = t.replace(b, '''  /* ⭐ DUAS ESTRELAS NO MEIO (24/09/2026, print do Bryan com as duas areas
     marcadas no PC, entre as colunas de baloes e o titulo). Espelhadas,
     cada uma no seu ritmo. So' a partir de 1280 px: abaixo disso as areas
     encostam nas colunas. A estrela SAI da coluna da esquerda (fica o vao ate'
     chegar o balao novo que o Bryan vai gerar). */
  .estrela-centro { display: none; }
  @media (min-width: 1280px) {
    .estrela-centro { display: block; position: absolute; top: 110px; width: 104px;
      transform-origin: 50% 100%; }
    .estrela-centro.esq { left: calc(50% - 470px); }
    .estrela-centro.dir { left: calc(50% + 366px); }
    .estrela-centro img { width: 100%; height: auto; display: block;
      filter: drop-shadow(0 8px 12px rgba(20, 16, 30, .14)); }
    .festa .balao:nth-child(3) { visibility: hidden; }
  }
  @media (min-width: 1280px) and (prefers-reduced-motion: no-preference) {
    .estrela-centro.esq { animation: balanca 6.6s ease-in-out -1.5s infinite alternate; }
    .estrela-centro.dir { animation: balanca 7.3s ease-in-out -4.1s infinite alternate; --gira: -2.5deg; }
  }
''' + b)
t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
