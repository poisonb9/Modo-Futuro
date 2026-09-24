p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')

# 1. HTML: a faixa sai, entra o varal de 11 letras
velho = '      <picture class="faixa-inaug"><source media="(max-width: 759px)" srcset="/baloes/faixa_inauguracao_p.webp"><img src="/baloes/faixa_inauguracao.webp" alt="" decoding="async" fetchpriority="low"></picture>\n'
assert t.count(velho) == 1
# arco: desce nas pontas (0 no meio, 1 nas pontas); dy corrige Ç (cedilha embaixo) e Ã (til em cima)
dy = {9: 0.1, 10: -0.11}
letras = ''
for i in range(1, 12):
    arco = ((i - 6) / 5) ** 2
    letras += ('        <span style="--i:%d;--arco:%.2f;--dy:%s"><picture><source media="(max-width: 759px)" srcset="/baloes/letra_%02d_p.webp">'
               '<img src="/baloes/letra_%02d.webp" alt="" decoding="async" fetchpriority="low"></picture></span>\n') % (i, arco, dy.get(i, 0), i, i)
t = t.replace(velho, '      <div class="varal">\n' + letras + '      </div>\n')

# 2. CSS: troca o bloco da faixa pelo do varal
ini = t.index('  /* ⭐ A FAIXA "INAUGURACAO"')
fimm = '  @media (min-width: 760px) { .faixa-inaug { top: 2px; width: 290px; } }' + chr(10)
fim = t.index(fimm) + len(fimm)
css = '''  /* ⭐ O VARAL "INAUGURACAO" (24/09/2026, arte do Bryan, letra por letra).
     A faixa inteira ficou "espremida, enfiada de qualquer jeito" (Bryan) --
     cada letra agora e' um balao: separadas por erosao + dono mais proximo
     (as vizinhas se tocavam), MESMA escala para todas (o Ç e o Ã sao mais
     altos e nao podem encolher). Em arco suave acima do logo, espaco igual
     entre letras, e cada uma balanca com atraso da vizinha: uma onda passa
     pelo varal. `--arco` (0 no meio, 1 nas pontas) desce as pontas; `--dy`
     recentra o Ç (cedilha) e o Ã (til). O wrapper leva a posicao, a
     <picture> leva o balanco -- os dois `transform` nao podem brigar. */
  .varal { position: absolute; left: 50%; top: 8px; transform: translateX(-50%);
    display: flex; align-items: center; gap: var(--vg, 1px); z-index: 1;
    --lh: 22px; --sag: 9px; }
  .varal span { display: block;
    transform: translateY(calc(var(--arco) * var(--sag) + var(--dy) * var(--lh))); }
  .varal picture { display: block; transform-origin: 50% 100%; }
  .varal img { height: var(--lh); width: auto; display: block; }
  @media (prefers-reduced-motion: no-preference) {
    .varal picture { animation: onda 2.6s ease-in-out calc(var(--i) * -.19s) infinite alternate; }
  }
  @keyframes onda {
    from { transform: translateY(-1.5px) rotate(-4deg); }
    to   { transform: translateY(1.5px) rotate(4deg); }
  }
  /* celular: o varal toma o lugar da estrela e da boca (o vao entre elas e'
     de 112 px, nao cabe). `visibility` para a grade nao reposicionar. */
  @media (max-width: 759px) {
    .festa .balao:nth-child(3), .canais .balao:nth-child(1) { visibility: hidden; }
  }
  @media (max-height: 740px) and (max-width: 759px) {
    .varal { top: 2px; --lh: 17px; --sag: 7px; }
    header { padding-top: 24px; }
  }
  /* PC: letras maiores, e o cabecalho desce 46 px para o varal respirar */
  @media (min-width: 760px) {
    .varal { top: 10px; --lh: 44px; --sag: 16px; --vg: 3px; }
    header { padding-top: 80px; }
  }
'''
t = t[:ini] + css + t[fim:]
# 3. o z-index da faixa (ajuste anterior) nao existe mais -- confere que nada sobrou
assert 'faixa-inaug' not in t, [l for l in t.split('\n') if 'faixa-inaug' in l]
t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
