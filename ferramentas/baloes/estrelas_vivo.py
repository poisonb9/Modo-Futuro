# Duas estrelas no celular, dos lados do preco da linha viva, soltando na
# rolagem (o mesmo efeito do cupom e do cifrao). Edita em BYTES, CRLF.
p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')
assert 'estrela-vivo' not in t

a = '      <div class="varal">\n'
assert t.count(a) == 1
t = t.replace(a, '      <span class="estrela-vivo esq"><picture><source media="(max-width: 759px)" srcset="/baloes/inaug_estrela_p.webp"><img src="/baloes/inaug_estrela.webp" alt="" decoding="async" fetchpriority="low"></picture></span>\n'
                 '      <span class="estrela-vivo dir"><picture><source media="(max-width: 759px)" srcset="/baloes/inaug_estrela_p.webp"><img src="/baloes/inaug_estrela.webp" alt="" decoding="async" fetchpriority="low"></picture></span>\n' + a)

b = '  /* ⭐ BALOES QUE SOBEM'
assert t.count(b) == 1
t = t.replace(b, '''  /* ⭐ DUAS ESTRELAS NO CELULAR, dos lados do PRECO da linha viva (24/09,
     print do Bryan com as duas areas marcadas). Na altura do nome a linha
     ocupa ~322 de 354 px; na do preco sobram ~80 px de cada lado -- e' ali.
     Mesmo efeito do cupom e do cifrao (animacao guiada pela rolagem), mas
     comecando MAIS TARDE (120 -> 520 px), porque elas moram mais embaixo:
     sobem e somem enquanto a pessoa passa pelo preco a caminho da vitrine.
     (Bryan achou que podia ficar apertado; ficou para ele ver no aparelho.) */
  .estrela-vivo { display: none; }
  @media (max-width: 759px) {
    .estrela-vivo { display: block; position: absolute; top: 262px; width: 30px;
      transform-origin: 50% 100%; opacity: .95; }
    .estrela-vivo.esq { left: 3vw; }
    .estrela-vivo.dir { right: 3vw; }
    .estrela-vivo img { width: 100%; height: auto; display: block; }
    .estrela-vivo picture { display: block; }
  }
  @media (max-height: 740px) and (max-width: 759px) { .estrela-vivo { top: 214px; width: 26px; } }
  @supports (animation-timeline: scroll()) {
    @media (max-width: 759px) and (prefers-reduced-motion: no-preference) {
      .estrela-vivo { animation: soltar linear both; animation-timeline: scroll(root);
        animation-range: 120px 520px; }
      .estrela-vivo picture { animation: balanca 6.2s ease-in-out -1.1s infinite alternate; }
      .estrela-vivo.dir picture { animation-duration: 7.4s; animation-delay: -3.7s; --gira: -2.5deg; }
    }
  }
  @supports not (animation-timeline: scroll()) {
    @media (max-width: 759px) and (prefers-reduced-motion: no-preference) {
      .estrela-vivo {
        transform: translateY(calc(var(--solta2, 0) * -150px)) scale(calc(1 - var(--solta2, 0) * .2));
        opacity: calc(.95 - var(--solta2, 0) * .95);
      }
    }
  }
''' + b)

v1 = '      var s = mq.matches ? Math.min(1, Math.max(0, y / 320)) : 0;\n'
v2 = '      alvo.style.setProperty("--solta", s.toFixed(3));\n'
assert t.count(v1) == 1 and t.count(v2) == 1
t = t.replace(v1, v1 + '      var s2 = mq.matches ? Math.min(1, Math.max(0, (y - 120) / 400)) : 0;\n')
t = t.replace(v2, v2 + '      alvo.style.setProperty("--solta2", s2.toFixed(3));\n')

t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
