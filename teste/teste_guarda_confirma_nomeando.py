# -*- coding: utf-8 -*-
"""A guarda de publicacao confirma POR NOME, e o numero sai da verificacao.

## O DEFEITO QUE ISTO TRAVA

Ate' 16/09/2026 o fim de `publicar_bio.main` imprimia:

    confirmado em {len(PROJETOS)} projeto(s)

Um numero FIXO, que nao vinha da verificacao e nao sabia o que ela tinha
olhado. Na pratica ele dizia **5** logo depois de o passo anterior imprimir
**6** linhas de `publicado:` (as cinco bios mais o site mae), e as rotas
`/todos` e `/parceiros` — que sao o endereco escrito no perfil do Awin — nao
apareciam em canto nenhum.

⭐ Guarda que conta sem nomear e' guarda que sera' ignorada: com dois numeros
divergentes, quem le' nao tem como saber se sobrou um endereco ou se faltou
um, e a reacao barata e' parar de olhar.

## ⛔ O CASO NEGATIVO E' O QUE FAZ ESTE TESTE VALER

Uma guarda que aprovasse tudo passaria no caso positivo com nota dez. Por isso
o teste central aqui e' o do meio: com UMA pagina servindo conteudo velho, o
endereco tem de aparecer em `faltando` **pelo nome** e sumir de `conferidos`.
E a soma dos dois tem de continuar sendo o total de enderecos baixados — o que
prova que nada foi contado duas vezes nem esquecido.

⚠️ E o dublê aqui funciona porque `conferir_no_ar` faz `import requests`
DENTRO da funcao: a troca em `sys.modules` e' resolvida na hora da chamada.
Em 15/09/2026 um dublê parecido nao interceptou nada porque o alvo usava
`from . import x`, que le' o atributo do pacote e nao passa por `sys.modules`.
"""
import pathlib
import sys
import types

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "paginas"))

import publicar_bio  # noqa: E402

MARCA = 'name="v" content="aaaaaaaaaaaa"'
MARCA_P = 'name="v" content="bbbbbbbbbbbb"'
MARCA_C = 'name="v" content="cccccccccccc"'


class _Resposta:
    def __init__(self, texto):
        self.text = texto


def _dublê(velhas=(), quebradas=()):
    """Um `requests` de mentira que serve a marca certa, menos onde eu mandar.

    `velhas` sao URLs que respondem com HTML SEM a marca (deploy que nao
    chegou); `quebradas` sao as que levantam (endereco fora do ar).
    """
    baixadas = []

    def get(url, timeout=None):
        baixadas.append(url)
        if any(u in url for u in quebradas):
            raise OSError("connection reset")
        if any(u in url for u in velhas):
            return _Resposta("<html>pagina de ontem, sem carimbo novo</html>")
        # a rota decide QUAL marca o corpo carrega — trocar as marcas de lugar
        # faria um endereco confirmar com o carimbo do vizinho
        if url.rstrip("/").endswith("/parceiros"):
            return _Resposta(f"<meta {MARCA_P}>")
        if url.rstrip("/").endswith("/todos"):
            return _Resposta(f"<meta {MARCA_C}>")
        if publicar_bio.PROJETO_MAE in url:
            return _Resposta(f"<meta {MARCA_C}>")
        return _Resposta(f"<meta {MARCA}>")

    mod = types.ModuleType("requests")
    mod.get = get
    return mod, baixadas


def _rodar(**quais):
    mod, baixadas = _dublê(**quais)
    antigo = sys.modules.get("requests")
    sys.modules["requests"] = mod
    try:
        faltando, conferidos = publicar_bio.conferir_no_ar(
            MARCA, MARCA_P, MARCA_C)
    finally:
        if antigo is None:
            del sys.modules["requests"]
        else:
            sys.modules["requests"] = antigo
    return faltando, conferidos, baixadas


def teste_tudo_no_ar_confirma_todos_os_enderecos_pelo_nome():
    faltando, conferidos, baixadas = _rodar()
    assert faltando == [], faltando
    # ⛔ O NUMERO TEM DE SER O DAS PAGINAS BAIXADAS, nao o de PROJETOS. Este
    # assert e' literalmente o defeito de origem: eram 5 contra o que se mede.
    assert len(conferidos) == len(baixadas), (len(conferidos), len(baixadas))
    assert len(conferidos) > len(publicar_bio.PROJETOS), (
        f"a verificacao olha mais enderecos que PROJETOS ({len(conferidos)} "
        f"contra {len(publicar_bio.PROJETOS)}) — e' por isso que contar "
        f"PROJETOS mentia")
    # e o site mae, que nao esta' em PROJETOS, tem de estar entre eles
    assert any(publicar_bio.PROJETO_MAE in c for c in conferidos), conferidos
    # as rotas tambem se conferem, e aparecem nomeadas
    assert any(c.endswith("/todos") for c in conferidos), conferidos
    assert any(c.endswith("/parceiros") for c in conferidos), conferidos


def teste_uma_pagina_velha_e_denunciada_pelo_nome():
    """⛔ O CASO NEGATIVO. Sem ele, guarda que aprova tudo passa no positivo."""
    alvo = publicar_bio.PROJETOS[1]
    faltando, conferidos, baixadas = _rodar(velhas=(f"{alvo}.pages.dev/todos",))
    assert faltando == [f"{alvo}/todos"], faltando
    # ⚠️ E O NOME TEM DE SAIR DOS CONFIRMADOS. Guarda que acusa e confirma a
    # mesma coisa nao esta' medindo nada.
    assert f"{alvo}/todos" not in conferidos, conferidos
    # nada se perdeu nem se contou duas vezes
    assert len(faltando) + len(conferidos) == len(baixadas)


def teste_endereco_fora_do_ar_nao_vira_confirmado():
    faltando, conferidos, baixadas = _rodar(
        quebradas=(f"{publicar_bio.PROJETO_MAE}.pages.dev/",))
    assert faltando, "pagina que nem respondeu tem de cair em faltando"
    assert all("nao respondeu" not in c for c in conferidos), conferidos
    assert len(faltando) + len(conferidos) == len(baixadas)


def teste_o_numero_nao_vem_mais_de_len_projetos():
    """A prova de que o defeito nao volta por cima do conserto.

    ⚠️ LE' O CODIGO PELO `ast`, NAO O TEXTO DO ARQUIVO. A primeira versao
    procurava a frase no fonte cru e reprovou na hora — por causa da propria
    docstring acima, que CITA o defeito pra explicar por que ele e' defeito.
    E' a mesma armadilha da guarda da fonte Segoe, em 15/09/2026: guarda com
    alarme falso e' pior que guarda nenhuma, porque na vez em que ela acertar
    ninguem vai acreditar.
    """
    import ast
    fonte = (RAIZ / "paginas" / "publicar_bio.py").read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    # so' as f-strings que o codigo REALMENTE monta, sem comentario nem
    # docstring (docstring e' o primeiro Expr de modulo/def/classe, e as
    # constantes soltas caem fora do conjunto abaixo de qualquer jeito)
    vivas = [ast.unparse(n) for n in ast.walk(arvore)
             if isinstance(n, ast.JoinedStr)]
    assert not any("len(PROJETOS)" in s and "confirmado" in s for s in vivas), \
        [s for s in vivas if "len(PROJETOS)" in s]
    assert any("len(conferidos)" in s for s in vivas), vivas


if __name__ == "__main__":
    for nome, f in sorted(globals().items()):
        if nome.startswith("teste_"):
            f()
            print("  ok", nome)
    print("verde")
