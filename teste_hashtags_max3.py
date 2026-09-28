# -*- coding: utf-8 -*-
"""28/09/2026: o TikTok aceita no maximo 3 hashtags; os posts saiam com 5."""
import re

from engine import legenda_post


def test_montar_corta_pra_3():
    t = legenda_post.montar({"titulo": "T", "descricao": "D",
                             "tags": ["um", "dois", "tres", "quatro", "cinco"]})
    assert re.findall(r"#\w+", t) == ["#um", "#dois", "#tres"]


def test_limitar_sem_repetir_e_sem_buraco():
    assert legenda_post.limitar_hashtags("x\n\n#A #a #b #c #d") == "x\n\n#A #b #c"


if __name__ == "__main__":
    test_montar_corta_pra_3(); test_limitar_sem_repetir_e_sem_buraco(); print("ok")
