# PC: ao rolar a pagina, um balao sobe pela margem DIREITA e depois outro
# pela ESQUERDA; o segundo chega ao topo JUNTO com o fim da rolagem.
p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')

a = '<div class="luz" aria-hidden="true"></div>\n'
assert t.count(a) == 1
t = t.replace(a, a + '<div class="sobe-rolagem" aria-hidden="true">'
              '<span class="sobe dir"><img src="/baloes/inaug_laranja.webp" alt="" decoding="async" loading="lazy"></span>'
              '<span class="sobe esq"><img src="/baloes/inaug_porcento.webp" alt="" decoding="async" loading="lazy"></span></div>\n')

b = '  /* ⭐ O VARAL "INAUGURACAO"'
assert t.count(b) == 1
t = t.replace(b, '''  /* ⭐ BALOES QUE SOBEM COM A ROLAGEM, NO PC (24/09/2026, Bryan: "quando
     estiver rolando a pagina sobe um balao do lado direito e depois um do
     lado esquerdo, casando com o fim do rolamento"). Fixos nas MARGENS (so'
     >= 1440 px, onde a grade de 1180 deixa lateral livre), guiados pela
     rolagem da pagina inteira: o da direita atravessa a tela entre 15% e 60%
     do caminho; o da esquerda entre 55% e 100% -- chega ao topo exatamente no
     fim. Sem suporte ao recurso, o script do fim da pagina escreve --prog. */
  .sobe-rolagem { display: none; }
  @media (min-width: 1440px) {
    .sobe-rolagem { display: block; position: fixed; inset: 0; pointer-events: none; z-index: 0; }
    .sobe { position: absolute; top: 0; width: 92px; opacity: 0; }
    .sobe img { width: 100%; height: auto; display: block;
      filter: drop-shadow(0 8px 12px rgba(20, 16, 30, .14)); }
    .sobe.dir { right: calc((100vw - 1180px) / 4 - 46px); }
    .sobe.esq { left: calc((100vw - 1180px) / 4 - 46px); }
  }
  @keyframes subirTela {
    0%   { transform: translateY(105vh) rotate(-4deg); opacity: 0; }
    8%   { opacity: 1; }
    92%  { opacity: 1; }
    100% { transform: translateY(-45vh) rotate(4deg); opacity: 0; }
  }
  @supports (animation-timeline: scroll()) {
    @media (min-width: 1440px) and (prefers-reduced-motion: no-preference) {
      .sobe { animation: subirTela linear both; animation-timeline: scroll(root); }
      .sobe.dir { animation-range: 15% 60%; }
      .sobe.esq { animation-range: 55% 100%; }
    }
  }
  @supports not (animation-timeline: scroll()) {
    @media (min-width: 1440px) and (prefers-reduced-motion: no-preference) {
      .sobe.dir { --f: clamp(0, calc((var(--prog, 0) - .15) / .45), 1); }
      .sobe.esq { --f: clamp(0, calc((var(--prog, 0) - .55) / .45), 1); }
      .sobe { transform: translateY(calc(105vh - var(--f) * 150vh)) rotate(calc(-4deg + var(--f) * 8deg));
        opacity: clamp(0, calc(min(var(--f), 1 - var(--f)) * 12), 1); }
    }
  }
''' + b)

# fallback (Safari sem animation-timeline): progresso 0..1 da pagina inteira
velho = '''      alvo.style.setProperty("--solta2", s2.toFixed(3)); }'''
assert t.count(velho) == 1
t = t.replace(velho, '''      alvo.style.setProperty("--solta2", s2.toFixed(3));
      var sr = document.querySelector(".sobe-rolagem");
      if (sr) { var tot = Math.max(1, document.documentElement.scrollHeight - innerHeight);
        sr.style.setProperty("--prog", Math.min(1, y / tot).toFixed(4)); } }''')
# o fallback so' ligava no celular; os baloes do PC precisam dele tambem
velho2 = '''    var mq = matchMedia("(max-width: 759px) and (prefers-reduced-motion: no-preference)");'''
assert t.count(velho2) == 1
t = t.replace(velho2, velho2 + '''
    if (matchMedia("(prefers-reduced-motion: reduce)").matches) { return; }''')

t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
