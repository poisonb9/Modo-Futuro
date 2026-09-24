# A inauguracao nas BIOS (contra_capa.html): varal INAUGURACAO sobre o brasao
# + laranja e laco a` esquerda, cupom a` direita (abaixo do balao do canal).
import random
p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/contra_capa.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')
assert 'varal-bio' not in t

# ---- HTML: dentro do header.topo, antes do balao do canal
a = '    <span class="balao-canal" aria-hidden="true"><img id="balao_canal" alt="" decoding="async"></span>\n'
assert t.count(a) == 1
dy = {9: 0.1, 10: -0.11}
letras = ''
for i in range(1, 12):
    arco = ((i - 6) / 5) ** 2
    letras += '      <span style="--i:%d;--arco:%.2f;--dy:%s"><img src="/baloes/letra_%02d_p.webp" alt=""></span>\n' % (i, arco, dy.get(i, 0), i)
html = ('    <div class="varal-bio" aria-hidden="true">\n' + letras + '    </div>\n'
        '    <span class="festa-bio presente" aria-hidden="true"><img src="/baloes/inaug_presente_p.webp" alt=""></span>\n'
        '    <span class="festa-bio laco" aria-hidden="true"><img src="/baloes/inaug_laco_p.webp" alt=""></span>\n'
        '    <span class="festa-bio cupom" aria-hidden="true"><img src="/baloes/inaug_etiqueta_p.webp" alt=""></span>\n')
t = t.replace(a, html + a)

# ---- CSS: logo depois do bloco do balao do canal
b = '''  @keyframes flutuar {
    from { transform: translate3d(0, -5px, 0) rotate(-3deg); }
    to   { transform: translate3d(0, 5px, 0) rotate(3deg); }
  }
'''
assert t.count(b) == 1
random.seed(2409)
vidas = []
for i in range(1, 12):
    d1 = round(random.uniform(3.1, 5.3), 2); d2 = round(random.uniform(4.3, 7.9), 2)
    a1 = round(-random.uniform(0, d1), 2); a2 = round(-random.uniform(0, d2), 2)
    amp = round(random.uniform(1.0, 2.0), 1); rot = round(random.uniform(1.5, 3.0), 1)
    vidas.append('  .varal-bio span:nth-child(%d) img { --d1:%ss; --d2:%ss; --a1:%ss; --a2:%ss; --amp:%spx; --rot:%sdeg; }' % (i, d1, d2, a1, a2, amp, rot))
css = b + '''  /* ⭐ A INAUGURACAO NAS BIOS (24/09/2026, Bryan: "aplicar o conceito de
     inauguracao nos sites de cada bio tambem"). O mesmo varal do site mae,
     em arco por cima do brasao (as pontas descem pelos lados), letras com
     vida propria (dois periodos independentes, mesma semente 2409), e um arco
     pequeno de festa: laranja e laco a` esquerda, o balao do canal (que ja'
     existia) e o cupom a` direita. O topo ganha 30 px para o varal respirar.
     Enfeite puro: absoluto, aria-hidden, sem toque. */
  .topo { padding-top: 30px; }
  .varal-bio { position: absolute; left: 50%; top: 0; transform: translateX(-50%);
    display: flex; align-items: center; gap: 1px; pointer-events: none;
    --lh: 21px; --sag: 10px; z-index: 1; }
  .varal-bio span { display: block;
    transform: translateY(calc(var(--arco) * var(--sag) + var(--dy) * var(--lh))); }
  .varal-bio img { height: var(--lh); width: auto; display: block; }
  .festa-bio { position: absolute; pointer-events: none; transform-origin: 50% 100%; }
  .festa-bio img { width: 100%; height: auto; display: block; }
  .festa-bio.laranja { width: 30px; top: 40px; left: calc(50% - 132px); }
  .festa-bio.laco    { width: 30px; top: 14px; left: calc(50% - 98px); }
  .festa-bio.cupom   { width: 30px; top: 74px; left: calc(50% + 116px); }
  @media (prefers-reduced-motion: no-preference) {
    .varal-bio img { animation: vbSobe var(--d1) ease-in-out var(--a1) infinite alternate,
                               vbGira var(--d2) ease-in-out var(--a2) infinite alternate; }
    .festa-bio.laranja { animation: flutuar 6.1s ease-in-out -1.4s infinite alternate; }
    .festa-bio.laco    { animation: flutuar 7.3s ease-in-out -3.9s infinite alternate; }
    .festa-bio.cupom   { animation: flutuar 6.7s ease-in-out -2.2s infinite alternate; }
  }
  @keyframes vbSobe { from { translate: 0 calc(var(--amp) * -1); } to { translate: 0 var(--amp); } }
  @keyframes vbGira { from { rotate: calc(var(--rot) * -1); } to { rotate: var(--rot); } }
''' + '\n'.join(vidas) + '\n'
t = t.replace(b, css)
t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
