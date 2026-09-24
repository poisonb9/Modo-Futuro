p = r'C:/Users/Administrator/Desktop/Tiktok/YouTube videos para Google Drive/ATUALIZADA/clip_engine/paginas/todos.html'
t = open(p, 'rb').read().decode('utf-8'); n0 = t.count('\r\n'); t = t.replace('\r\n', '\n')
a = '  @media (max-height: 740px) and (max-width: 759px) { .faixa-inaug { top: 0; width: 170px; } }\n'
assert t.count(a) == 1
t = t.replace(a, '''  /* ⛔ 1a tentativa (medida na previa): estrela e boca na FRENTE das pontas
     cobriam o "IN" e o "AO" -- o vao entre elas e' de 112 px. No celular a
     faixa TOMA O LUGAR das duas e vira o trecho do meio do arco (laranja,
     laco, faixa, chef, carrinho). `visibility`, nao `display`: a grade de 3
     colunas nao pode reposicionar os vizinhos. */
  @media (max-width: 759px) {
    .festa .balao:nth-child(3), .canais .balao:nth-child(1) { visibility: hidden; }
    .faixa-inaug { top: 4px; width: 206px; }
  }
  @media (max-height: 740px) and (max-width: 759px) { .faixa-inaug { top: 0; width: 176px; } }
''')
t = t.replace('\n', '\r\n'); open(p, 'wb').write(t.encode('utf-8')); print('ok', n0, t.count('\r\n'))
