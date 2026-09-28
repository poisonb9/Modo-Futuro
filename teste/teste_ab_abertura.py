# -*- coding: utf-8 -*-
"""28/09/2026: A/B da abertura na cozinha (grupo B = `## Abertura (A/B)` do guia)."""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import ab_abertura, guia_voz  # noqa: E402

COZ = "cozinha.importada"


def test_grupo_estavel_e_dos_dois_lados():
    gs = {ab_abertura.grupo("fonte", i) for i in range(40)}
    assert gs == {"A", "B"}
    assert ab_abertura.grupo("f", 12.0) == ab_abertura.grupo("f", 12.04)


def test_so_b_recebe_a_regra():
    os.environ["AB_ABERTURA"] = "A"
    assert "ABERTURA" not in guia_voz.bloco_prompt(COZ)
    os.environ["AB_ABERTURA"] = "B"
    assert "ABERTURA" in guia_voz.bloco_prompt(COZ)
    os.environ.pop("AB_ABERTURA")


def test_outro_canal_fica_fora_e_limpa_o_env():
    os.environ["AB_ABERTURA"] = "B"
    c = {"inicio_s": 3}
    assert ab_abertura.aplicar(c, "x", "truque.importado") is None
    assert "ab_abertura" not in c and "AB_ABERTURA" not in os.environ


if __name__ == "__main__":
    test_grupo_estavel_e_dos_dois_lados(); test_so_b_recebe_a_regra()
    test_outro_canal_fica_fora_e_limpa_o_env(); print("tudo verde")
