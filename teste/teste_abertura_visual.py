# -*- coding: utf-8 -*-
"""A imagem dos 2 primeiros segundos entra na escolha do trecho.

⚠️ MEDIDO em 08/09/2026, olhando o PRIMEIRO FRAME do melhor e do pior clipe
de dois canais — nao a metrica agregada, o frame mesmo:

    @atefalhar    608  o EXERCICIO acontecendo (pernas na maquina, anilha de
                       20 kg, movimento aos 0s E aos 2s)
                   97  uma pessoa GESTICULANDO pra camera, falando SOBRE o
                       exercicio. Nenhum exercicio na tela.

    @semanestesia 652  rosto inteiro, olhos visiveis
                  162  torso sem rosto, escuro, desfocado

⚠️ E OS DOIS PIORES TINHAM TEXTO DE OUTRA PLATAFORMA QUEIMADO NA IMAGEM:
"N THE DESCRIPTIO" cortado no rodape de um, "Y KEEP / SHIFTED" no outro.
Legenda alheia em ingles competindo com a nossa. Nenhum dos vencedores tinha.

## POR QUE ISTO IMPORTA MAIS DO QUE PARECE

E' o MESMO principio que a autopsia dos titulos ja' tinha achado — MOSTRAR a
coisa em vez de FALAR sobre ela — mas aparecendo num canal independente: um
achado veio do texto de 75 posts, o outro da imagem de 4 clipes. Dois
caminhos diferentes chegando na mesma regra e' o que separa padrao de
coincidencia.

E casa com a medicao que o projeto ja' tinha: a audiencia sai aos 0:02 e
98,7% do trafego vem da Para Você. Quase todo espectador e' alguem que nunca
viu o canal, decidindo pela imagem.

⚠️ ESTE TESTE NAO PROVA QUE A REGRA FUNCIONA. Ele prova que ela continua
escrita, e que continua sendo DESEMPATE e nao criterio unico — um trecho com
imagem boa e fala fraca continua ruim. A prova vem no export do mes que vem.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

SELECAO = (RAIZ / "engine" / "selecao.py").read_text(encoding="utf-8")


def teste_o_prompt_pede_o_que_a_abertura_MOSTRA():
    assert '"abertura_mostra"' in SELECAO
    for opcao in ("acao", "pessoa_falando", "texto_alheio", "parado"):
        assert opcao in SELECAO, f"falta a opcao {opcao!r}"


def teste_a_regra_prefere_ACAO_a_pessoa_falando():
    assert "ACONTECENDO na tela" in SELECAO
    assert "FALA sobre ela" in SELECAO or "FALA sobre" in SELECAO


def teste_a_regra_evita_texto_de_outra_plataforma():
    """Os dois piores clipes tinham legenda alheia queimada; nenhum dos dois
    melhores tinha."""
    assert "outra plataforma queimada" in SELECAO
    assert "N THE DESCRIPTIO" in SELECAO, "sumiu a evidencia que originou a regra"


def teste_rosto_e_olhos_quando_so_houver_pessoa():
    assert "ROSTO e OLHOS" in SELECAO


def teste_a_medicao_fica_junto_da_regra():
    """Regra sem o numero que a gerou vira gosto pessoal."""
    for n in ("608", "97", "652", "162", "0:02", "98,7%"):
        assert n in SELECAO, f"sumiu a medicao {n!r}"


def teste_NEGATIVO_a_imagem_NAO_vira_criterio_unico():
    """⚠️ O limite da regra. Sem isto ela viraria 'escolha por imagem', e o
    motor passaria a cortar trechos bonitos que nao dizem nada."""
    assert "NAO substitui a forca da frase" in SELECAO.replace("Ã", "A").replace("ç", "c") \
        or "NÃO substitui a força da frase" in SELECAO
    assert "desempate" in SELECAO


def teste_o_prompt_continua_montavel():
    """⚠️ O prompt e' uma f-string com chaves do JSON dentro. Texto novo em
    lugar errado quebra a montagem — e isso so' apareceria num run de corte,
    depois de ja' ter gasto download e API."""
    from engine import selecao
    p = selecao.PROMPT
    assert len(p) > 8000
    assert "abertura_mostra" in p, "a regra nao chegou no prompt montado"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
