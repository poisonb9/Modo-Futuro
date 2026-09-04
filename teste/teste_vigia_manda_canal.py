# -*- coding: utf-8 -*-
"""O vigia tem de dizer de QUAL canal e' o video que ele despacha.

⚠️ MEDIDO em 02/09/2026: o `disparar()` do vigia nao mandava `canal` nenhum, o
workflow caia no default `modofuturo`, e TUDO que vinha do RAW nascia rotulado
como conteudo de tecnologia. No manifesto de agosto, 70 de 77 clipes ficaram
sem canal — e o agendador le' ausencia como modofuturo
(`v.get("canal") or "modofuturo"`), entao havia tutorial de maquiagem
elegivel pra postar no canal de chips.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import vigia_raw as V

from engine import canais_registro as cr

FONTE = (RAIZ / "vigia_raw.py").read_text(encoding="utf-8")


def teste_positivo_pastas_conhecidas():
    assert V.canal_da_pasta("SEM ANESTESIA/") == "semanestesia.pod"
    assert V.canal_da_pasta("MODO FUTURO/") == "modofuturo"
    assert V.canal_da_pasta("Truque Importado/") == "truque.importado"
    # ⚠️ CORRIGIDO, NAO AFROUXADO, em 04/09/2026. Este teste exigia
    # `cozinha.internacional`, que e' o @ do perfil no TikTok — e nao o nome
    # do canal NO BUFFER, que e' `cozinha.importada` e e' o que a guarda
    # CANAL_ESPERADO compara e o que os workflows usam pra escolher o token.
    # Com o nome do @ aqui, o `inputs.canal` nao batia no workflow, caia no
    # `else` e o token que saia era o do MODOFUTURO. O teste fixava o defeito.
    #
    # O que ele afere agora e' o que importa: a pasta resolve pro canal certo,
    # e o apelido antigo continua resolvendo pro mesmo lugar.
    assert V.canal_da_pasta("DOCES/") == "cozinha.importada"
    assert cr.canonico(V.canal_da_pasta("DOCES/")) == "cozinha.importada"
    assert cr.canonico("cozinha.internacional") == "cozinha.importada"


def teste_acento_e_caixa_nao_atrapalham():
    assert V.canal_da_pasta("sem anestésia/") == "semanestesia.pod"
    assert V.canal_da_pasta("2026-09/MODO FUTURO/") == "modofuturo"


def teste_negativo_pasta_generica_devolve_None():
    """⚠️ O CASO QUE CRIOU O PROBLEMA. "Geral - 01 setembro" nao diz canal
    nenhum. Devolver `modofuturo` aqui seria inventar dado — foi exatamente
    isso que pos biscoito e maquiagem no canal de tecnologia."""
    assert V.canal_da_pasta("Geral - 01 setembro/") is None
    assert V.canal_da_pasta("") is None
    assert V.canal_da_pasta(None) is None


def teste_negativo_sem_canal_NAO_dispara():
    """Video sem canal tem de ser PULADO, nao despachado com o default."""
    i = FONTE.index("sem_canal = [")
    bloco = FONTE[i:i + 900]
    assert "nao disparados" in bloco or "SEM CANAL" in bloco, \
        "o vigia nao avisa que pulou"
    assert "novos = [v for v in novos if canal_da_pasta" in FONTE, \
        "os sem canal nao estao sendo removidos da lista de disparo"


def teste_o_disparo_leva_o_canal():
    i = FONTE.index("def disparar(")
    corpo = FONTE[i:FONTE.index("\ndef ", i + 1)]
    assert '"canal": canal' in corpo, "o dispatch nao inclui o canal"
    # ⚠️ e so' inclui quando existe: mandar canal vazio faria o workflow cair
    # no default de novo, que e' o defeito original com outra roupa.
    assert "if canal else {}" in corpo, \
        "canal vazio esta' sendo mandado — o default volta a valer"


def teste_o_call_site_passa_o_canal_da_pasta():
    assert "canal=canal_da_pasta(" in FONTE, \
        "o laco de disparo nao deduz o canal da pasta"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
