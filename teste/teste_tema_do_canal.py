# -*- coding: utf-8 -*-
"""O tema do titulo contradiz a pasta do Drive? — e quando NAO contradiz.

⚠️ MEDIDO em 07/09/2026. O Bryan viu oito clipes de IA no @semanestesia.pod
(Sam Altman, "99% de desemprego em 2027"). O bruto do Yampolskiy tinha sido
posto na pasta `SEM ANESTESIA/` do Drive; dali pra frente todas as guardas
obedeceram esse rotulo, porque nenhuma tinha o direito de discordar dele.

Ordem do Bryan no mesmo dia: barrar e avisar, NUNCA redirecionar sozinho.

⚠️ O QUE ESTE ARQUIVO PROVA E' O CASO NEGATIVO.

Detector que acusa 100% passa em qualquer caso positivo — foi assim que 48
de 48 viraram 4 noutro projeto. Por isso o peso do teste esta' nos 31 brutos
que TEM de passar, e nos 250 titulos do manifesto que TEM de passar, e nao no
unico que tem de ser barrado.

Os dados sao reais, nao inventados:

    teste/dados/brutos_com_pasta.json    32 brutos que o vigia ja' despachou,
                                         com a pasta em que estavam de fato
                                         (extraidos de estado/vigia_raw.log)
    teste/dados/manifesto_titulos.json   255 clipes ja' publicados, com o
                                         canal que o manifesto lhes deu
"""
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from engine import tema

DADOS = RAIZ / "teste" / "dados"
BRUTOS = json.loads((DADOS / "brutos_com_pasta.json").read_text(encoding="utf-8"))
MANIFESTO = json.loads((DADOS / "manifesto_titulos.json").read_text(encoding="utf-8"))

# O bruto que originou tudo. A pasta dizia comportamento; o tema diz chips.
YAMPOLSKIY = ("The AI Safety Expert These Are The Only 5 Jobs That Will "
              "Remain In 2030! - Dr. Roman Yampolskiy")

# A fonte dos 8 clipes de IA que sairam no @semanestesia.pod.
#
# ⚠️ Rotulo, nao id. Este repositorio e' PUBLICO e id de arquivo do Drive nao
# entra nele (regra de canais/README.md). Os dados de teste trocam cada
# `fonte_id` real por um rotulo estavel; o do Yampolskiy e' este.
FONTE_DO_DEFEITO = "fonte-19"


def teste_positivo_barra_o_bruto_que_causou_o_defeito():
    achado = tema.conflito(YAMPOLSKIY, "semanestesia.pod")
    assert achado is not None, "o Yampolskiy tem de ser barrado"
    canal, nota_rival, nota_pasta = achado
    assert canal == "modofuturo"
    assert nota_rival > nota_pasta


def teste_negativo_os_31_brutos_legitimos_passam():
    """⚠️ ESTE e' o teste que vale. Um detector que barra tudo passa no de cima.

    Os 32 brutos sao os que o vigia realmente despachou com pasta de canal.
    Exatamente UM deles esta' na pasta errada — o Yampolskiy. Os outros 31
    foram cortados e publicados sem ninguem reclamar, entao barrar qualquer
    um deles e' falso positivo por definicao.
    """
    barrados = [b for b in BRUTOS
                if tema.conflito(b["nome"], b["canal_da_pasta"])]
    assert len(barrados) == 1, (
        f"esperava so' o Yampolskiy barrado, vieram {len(barrados)}: "
        + "; ".join(b["nome"][:50] for b in barrados))
    assert "Yampolskiy" in barrados[0]["nome"]


def teste_negativo_titulo_sem_evidencia_passa():
    """Falha ABERTA: o que o detector nao entende, ele deixa passar.

    ⚠️ Eu tinha escrito este teste sobre os titulos COREANOS do
    @truque.importado, supondo que nao pontuassem. Pontuam: o nome do arquivo
    traz "(RISABAE Makeup)" em letras latinas no fim. A medicao corrigiu a
    suposicao — quem de fato nao pontua em canal nenhum e' o nome mutilado
    pelo YTDown, que corta o titulo no meio.
    """
    sem_evidencia = [b for b in BRUTOS
                     if max(tema.pontuar(b["nome"]).values()) == 0]
    assert sem_evidencia, "os brutos sem evidencia sumiram dos dados de teste"
    for b in sem_evidencia:
        assert tema.conflito(b["nome"], b["canal_da_pasta"]) is None


def teste_plural_conta():
    """"CroissantS" tem de pontuar como `croissant`.

    Medido: sem isto, "How To Make Proper Croissants Completely By Hand"
    pontuava ZERO em todos os canais. Falha aberta nao estraga nada, mas cega
    o detector de graca.
    """
    assert tema.pontuar("How To Make Proper Croissants")["cozinha.importada"] > 0
    assert tema.pontuar("silicon wafers explained")["modofuturo"] > 0


def teste_negativo_goggins_e_do_semanestesia_por_decisao_do_bryan():
    """Goggins e Navy SEAL NAO sao sinal de @atefalhar.

    Em 04/09/2026 o Bryan reetiquetou os 8 clipes do Goggins de `modofuturo`
    para `semanestesia.pod`. Enquanto esses dois termos estiveram na lista do
    @atefalhar, o detector acusava 4 clipes legitimos do @semanestesia — os
    unicos falsos positivos que a medicao encontrou nos 255.
    """
    for t in ("Como David Goggins estuda e aprende mesmo tendo TDAH",
              "Onde voce foca, voce chega: a licao de um ex-Navy SEAL"):
        assert tema.conflito(t, "semanestesia.pod") is None, t


def teste_manifesto_so_acusa_defeito_conhecido():
    """Nos 255 clipes ja' publicados, todo acusado e' defeito DOCUMENTADO.

    Cinco sao acusados, e os cinco tem historia:
      - 4 dos 8 clipes de IA da fonte do Yampolskiy (o defeito de 07/09);
      - 1 clipe do biscoito Levain rotulado `modofuturo` — o incidente do
        Fahrenheit de 03/09, em que receitas foram cortadas por este motor.

    ⚠️ Este teste roda sobre TITULO DE CLIPE, que nao e' o que o vigia le' (ele
    le' o nome do bruto). Vale como pressao de falso positivo, nao como prova
    de sensibilidade — essa esta' no teste dos brutos.
    """
    acusados = [c for c in MANIFESTO if tema.conflito(c["titulo"], c["canal"])]
    assert len(acusados) == 5, (
        f"{len(acusados)} acusados: "
        + "; ".join(c["titulo"][:45] for c in acusados))
    do_defeito = [c for c in acusados if c["fonte_id"] == FONTE_DO_DEFEITO]
    assert len(do_defeito) == 4
    resto = [c for c in acusados if c["fonte_id"] != FONTE_DO_DEFEITO]
    assert len(resto) == 1 and "biscoito" in resto[0]["titulo"].lower()


def teste_o_vigia_usa_a_guarda():
    """A guarda so' serve se estiver ligada no caminho do disparo."""
    vigia = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")
    assert "from engine import tema" in vigia or "engine.tema" in vigia
    assert "tema.conflito" in vigia


def teste_nunca_redireciona():
    """Ordem do Bryan: barrar e avisar, nunca trocar o canal sozinho.

    O modulo devolve QUEM ele acha que e' — mas quem consome tem de tratar
    isso como aviso. Aqui a prova e' estrutural: `conflito` nao escreve nada,
    e o vigia nao pode passar o palpite como `canal` do disparo.
    """
    vigia = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")
    assert "canal=achado[0]" not in vigia
    assert "canal=rival" not in vigia


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
