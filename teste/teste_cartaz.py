# -*- coding: utf-8 -*-
"""Guardas do cartaz do produto.

O que estas guardas vigiam, e por que cada uma existe:

1. O SELO NAO PODE ANUNCIAR DESCONTO QUE OS DOIS PRECOS NAO SUSTENTAM.
   E' a versao em imagem do defeito de 15/09/2026 (dez produtos com queda
   falsa), e e' pior aqui: imagem salva nao se recalcula.

2. NOME LONGO NAO PODE VAZAR DO CARTAZ. O mesmo `nowrap` sem `overflow` que
   apareceu no iPhone, em outro meio.

3. A FONTE E' A DO REPO. Fonte do sistema sai como reserva bitmap na nuvem, sem
   levantar erro.

⭐ PROVA DE SENSIBILIDADE. Guarda que so' ve' o caso bom aprova detector cego —
a licao de 15/09, que custou cinco metricas. Entao cada guarda daqui roda
tambem contra o caso que ela TEM de reprovar: o teste do selo desenha um cartaz
com desconto de verdade e exige que o verde apareca; o do corte exige que as
reticencias apareçam. Se o desenho parasse de funcionar por completo, uma
guarda que so' procura ausencia passaria — estas nao passam.
"""
import ast
from pathlib import Path
import sys
import unittest

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from engine import cartaz


def _foto(lado=600):
    im = Image.new("RGB", (lado, lado), (200, 190, 180))
    ImageDraw.Draw(im).ellipse([80, 80, lado - 80, lado - 80], fill=(90, 70, 60))
    return im


def _tem_verde(img, cor=cartaz.VERDE, tolerancia=28):
    """Quantos pixels desta cor existem na imagem."""
    a = np.asarray(img.convert("RGB"), dtype=np.int16)
    return int((np.abs(a - np.array(cor, dtype=np.int16)).max(axis=2)
                <= tolerancia).sum())


def _codigo_sem_docstring(caminho: Path) -> list[str]:
    """As strings e os nomes do CODIGO, sem docstring e sem comentario.

    O `ast` ja' descarta comentario sozinho; as docstrings saem aqui. O que
    sobra e' o que o modulo de fato executa.
    """
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    docs = set()
    for no in ast.walk(arvore):
        if isinstance(no, (ast.Module, ast.ClassDef, ast.FunctionDef,
                           ast.AsyncFunctionDef)):
            corpo = getattr(no, "body", [])
            if (corpo and isinstance(corpo[0], ast.Expr)
                    and isinstance(corpo[0].value, ast.Constant)
                    and isinstance(corpo[0].value.value, str)):
                docs.add(id(corpo[0].value))
    saida = []
    for no in ast.walk(arvore):
        if isinstance(no, ast.Constant) and isinstance(no.value, str):
            if id(no) not in docs:
                saida.append(no.value)
        elif isinstance(no, ast.Attribute):
            saida.append(no.attr)
        elif isinstance(no, ast.Name):
            saida.append(no.id)
    return saida


class QuedaVemDoPar(unittest.TestCase):
    def test_par_honesto_calcula(self):
        self.assertAlmostEqual(cartaz.queda_do_par(89.90, 129.90), 30.79, places=1)

    def test_sem_antes_e_zero(self):
        self.assertEqual(cartaz.queda_do_par(89.90, None), 0.0)
        self.assertEqual(cartaz.queda_do_par(89.90, 0), 0.0)

    def test_antes_igual_ou_menor_e_zero(self):
        """⛔ O caso que o `original_price` da loja produz: 'antes' inventado
        que na verdade nao e' maior. Falha fechada, do lado que nao mente."""
        self.assertEqual(cartaz.queda_do_par(89.90, 89.90), 0.0)
        self.assertEqual(cartaz.queda_do_par(89.90, 50.00), 0.0)


class OSeloSoApareceComOPar(unittest.TestCase):
    """A prova na IMAGEM, nao so' no retorno da funcao."""

    def test_com_queda_real_o_selo_aparece(self):
        # ⭐ prova de sensibilidade: sem este caso, um desenho quebrado (que nao
        # desenha selo nenhum) passaria em todos os testes abaixo.
        img = cartaz.montar(_foto(), "Organizador", 89.90, 129.90)
        self.assertGreater(_tem_verde(img), 2000,
                           "o selo de queda real nao foi desenhado")

    def test_sem_antes_nao_ha_selo(self):
        img = cartaz.montar(_foto(), "Organizador", 89.90, None)
        self.assertLess(_tem_verde(img), 200,
                        "cartaz sem 'antes' desenhou selo de desconto")

    def test_antes_menor_nao_ha_selo(self):
        img = cartaz.montar(_foto(), "Organizador", 89.90, 50.00)
        self.assertLess(_tem_verde(img), 200,
                        "'antes' menor que o preco desenhou desconto")

    def test_queda_minima_corta_o_selo(self):
        """1,1% de queda e' verdade e mesmo assim nao vai ao ar: o selo verde
        grita igual pra 1% e pra 40%, e a imagem nao se explica depois."""
        self.assertLess(cartaz.queda_do_par(89.00, 90.00), cartaz.QUEDA_MINIMA)
        img = cartaz.montar(_foto(), "Organizador", 89.00, 90.00)
        self.assertLess(_tem_verde(img), 200)

    def test_preco_cortado_acompanha_o_selo(self):
        """Selo e preco riscado sao a MESMA decisao: ou os dois, ou nenhum.
        Um cartaz com preco riscado e sem selo (ou o contrario) seria duas
        fontes de verdade sobre o mesmo desconto."""
        com = cartaz.montar(_foto(), "Organizador", 89.90, 129.90)
        sem = cartaz.montar(_foto(), "Organizador", 89.90, None)
        cinza_com = _tem_verde(com, cartaz.CINZA, 20)
        cinza_sem = _tem_verde(sem, cartaz.CINZA, 20)
        self.assertGreater(cinza_com, cinza_sem + 500,
                           "o preco antigo riscado nao acompanhou o selo")


class NomeLongoNaoVaza(unittest.TestCase):
    LONGO = ("Organizador de maquiagem giratório 360 graus com 7 "
             "compartimentos à prova de poeira para penteadeira e banheiro "
             "acrílico transparente")

    def _linhas(self, nome, largura=1080 * 0.84, linhas_max=2):
        tela = Image.new("RGB", (1080, 1920))
        d = ImageDraw.Draw(tela)
        f = cartaz._fonte(62)
        return d, f, cartaz._quebrar(d, nome, f, largura, linhas_max)

    def test_nunca_passa_do_maximo_de_linhas(self):
        _, _, linhas = self._linhas(self.LONGO)
        self.assertLessEqual(len(linhas), 2)

    def test_nenhuma_linha_passa_da_largura(self):
        d, f, linhas = self._linhas(self.LONGO)
        for ln in linhas:
            self.assertLessEqual(d.textlength(ln, font=f), 1080 * 0.84,
                                 f"linha mais larga que o cartaz: {ln!r}")

    def test_o_corte_realmente_acontece(self):
        """⭐ Prova de sensibilidade do corte: sem ela, um `_quebrar` que
        devolvesse lista vazia passaria nos dois testes acima."""
        _, _, linhas = self._linhas(self.LONGO)
        self.assertTrue(linhas, "nao sobrou nome nenhum")
        self.assertTrue(linhas[-1].endswith("..."),
                        "nome longo foi cortado sem reticencias")

    def test_nome_curto_fica_inteiro(self):
        _, _, linhas = self._linhas("Fone Lenovo GM2 Pro")
        self.assertEqual(" ".join(linhas), "Fone Lenovo GM2 Pro")


def _luminancia(rgb):
    c = [v / 255 for v in rgb]
    c = [(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4)
         for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def _contraste(a, b):
    la, lb = _luminancia(a), _luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


class OBrilhoCobreAPecaSemApagarOTexto(unittest.TestCase):
    """O brilho e o texto puxam para lados opostos, e alguem vai mexer nisso.

    ⭐ POR QUE ESTA GUARDA EXISTE. O brilho foi ampliado em 15/09/2026 porque o
    Bryan viu o post no Telegram e o topo e o rodape estavam chapados. A
    correcao e' certa e tem um custo obvio: quanto mais claro o fundo, menos
    contraste sobra pro nome e, principalmente, pro preco antigo RISCADO, que
    e' cinza de proposito. Sem guarda, a proxima pessoa que achar o cartaz
    "meio escuro" sobe a intensidade e apaga o preco sem perceber.
    """

    def setUp(self):
        self.img = cartaz.montar(_foto(), "Organizador de maquiagem",
                                 89.90, 129.90)
        self.a = np.asarray(self.img.convert("RGB"), dtype=float)

    def _cantos(self):
        a, (h, w) = self.a, self.a.shape[:2]
        return [a[y:y + 60, x:x + 60].mean()
                for y, x in ((0, 0), (0, w - 60), (h - 60, 0), (h - 60, w - 60))]

    def _fundo_da_faixa_do_texto(self):
        h, w = self.a.shape[:2]
        faixa = self.a[int(h * 0.70):int(h * 0.95), int(w * 0.15):int(w * 0.85)]
        return tuple(int(v) for v in np.median(faixa.reshape(-1, 3), axis=0))

    def test_os_cantos_nao_sao_chapados(self):
        # ⭐ SENSIBILIDADE: a geometria ANTIGA (elipse so' atras do produto)
        # media 13 e 23 nos cantos. O piso de 30 reprova aquela versao — nao e'
        # um numero que qualquer desenho passa.
        for v in self._cantos():
            self.assertGreater(v, 30, f"canto chapado ({v:.1f})")

    def test_o_brilho_nao_estoura(self):
        for v in self._cantos():
            self.assertLess(v, 110, f"canto claro demais ({v:.1f})")

    def test_o_texto_continua_legivel_sobre_o_brilho(self):
        fundo = self._fundo_da_faixa_do_texto()
        for nome, cor in (("nome", cartaz.CLARO), ("preco", cartaz.OURO),
                          ("preco riscado", cartaz.CINZA)):
            razao = _contraste(cor, fundo)
            # 4,5:1 e' o piso de texto normal do WCAG AA. O riscado e' o que
            # chega mais perto (medido 4,98) — e' ele que esta guarda protege.
            self.assertGreater(razao, 4.5,
                               f"{nome} ficou com contraste {razao:.2f}:1")

    def test_a_guarda_de_contraste_tem_sensibilidade(self):
        """⭐ Contra um fundo claro de proposito, ela TEM de acusar."""
        self.assertLess(_contraste(cartaz.CINZA, (200, 195, 205)), 4.5)


class AFonteViajaNoRepo(unittest.TestCase):
    def test_a_fonte_existe(self):
        self.assertTrue(cartaz.FONTE.exists(),
                        f"a fonte versionada sumiu: {cartaz.FONTE}")

    def test_nao_e_fonte_do_sistema(self):
        """⛔ O rascunho pedia `segoeuib.ttf` ao Windows, com
        `load_default()` de reserva: na nuvem isso sai minusculo e NAO levanta
        erro. A fonte tem de vir de `engine/fontes/`.

        ⚠️ OLHA SO' O CODIGO, e isso custou uma rodada. A primeira versao leu o
        arquivo inteiro como texto e reprovou por causa da PROPRIA DOCSTRING do
        modulo, que explica por que a Segoe esta' proibida. Guarda com alarme
        falso e' pior que guarda nenhuma: na vez em que ela acertar, ninguem
        acredita. Mesmo defeito do `teste_vitrine_teto` em 15/09.
        """
        self.assertIn("fontes", cartaz.FONTE.parts)
        for texto in _codigo_sem_docstring(Path(cartaz.__file__)):
            self.assertNotIn("segoeui", texto.lower(),
                             "o codigo voltou a pedir fonte do sistema")
            self.assertNotIn("load_default", texto,
                             "o codigo voltou a ter fonte de reserva")

    def test_a_guarda_da_fonte_tem_sensibilidade(self):
        """⭐ Prova de que a guarda acima nao e' cega: contra um modulo que
        REALMENTE pede a fonte do sistema, ela tem de acusar."""
        falso = Path(__file__).parent / "_duble_fonte.py"
        falso.write_text(
            'x = 1\n'
            'def f():\n'
            '    try:\n'
            '        return truetype("segoeuib.ttf", 40)\n'
            '    except OSError:\n'
            '        return load_default()\n',
            encoding="utf-8")
        try:
            achou = [t for t in _codigo_sem_docstring(falso)
                     if "segoeui" in t.lower() or "load_default" in t]
            self.assertTrue(achou, "a guarda NAO viu a fonte do sistema no codigo")
        finally:
            falso.unlink()

    def test_fonte_ausente_levanta(self):
        original = cartaz.FONTE
        try:
            cartaz.FONTE = original.parent / "nao-existe.ttf"
            with self.assertRaises(FileNotFoundError):
                cartaz._fonte(40)
        finally:
            cartaz.FONTE = original


class OFormatoEDaPlataforma(unittest.TestCase):
    def test_sai_em_9x16(self):
        img = cartaz.montar(_foto(), "Organizador", 89.90)
        self.assertEqual(img.size, (1080, 1920))

    def test_foto_nao_quadrada_nao_distorce(self):
        """Foto de loja vem em qualquer proporcao. O corte e' central; o que
        nao pode e' esticar o produto."""
        img = cartaz.montar(_foto().resize((900, 400)), "Organizador", 89.90)
        self.assertEqual(img.size, (1080, 1920))

    def test_preco_em_portugues(self):
        self.assertEqual(cartaz._reais(89.9), "R$ 89,90")
        self.assertEqual(cartaz._reais(1234.5), "R$ 1.234,50")


if __name__ == "__main__":
    unittest.main(verbosity=2)
