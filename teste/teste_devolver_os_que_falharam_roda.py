# -*- coding: utf-8 -*-
"""`devolver_os_que_falharam` tem de RODAR — nao so' estar escrita direito.

⚠️ POR QUE ESTE ARQUIVO EXISTE, medido em 02/09/2026.

Eu acrescentei a checagem de "resposta ruim do modelo" DEPOIS do
`item.pop("run_id")` que ja' estava no meio da funcao. O orquestrador morreu
com `KeyError: 'run_id'` nas duas passadas seguintes, nada ficou em voo, e a
fila parou ate' alguem olhar.

O teste que eu tinha escrito conferia o TEXTO do arquivo — que as duas
contagens existiam, que estavam separadas, que o detector tinha duas marcas.
Passou com o codigo quebrado, porque nenhuma dessas coisas executa a funcao.

**Teste de estrutura nao pega erro de ORDEM.** So' rodar pega.
"""
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import cortar_fila as cf


class _Cenario:
    """Troca as consultas de rede por respostas fixas."""

    def __init__(self, concluido="failure", cota=False, sumiu=False, vazia=False):
        self.concluido, self.cota, self.sumiu, self.vazia = concluido, cota, sumiu, vazia

    def __enter__(self):
        self._orig = (cf._gh, cf.falhou_por_cota, cf.fonte_sumiu,
                      cf.falhou_por_selecao_vazia)
        cf._gh = lambda *a, **k: {"status": "completed", "conclusion": self.concluido}
        cf.falhou_por_cota = lambda rid: self.cota
        cf.fonte_sumiu = lambda rid: self.sumiu
        cf.falhou_por_selecao_vazia = lambda rid: self.vazia
        return self

    def __exit__(self, *a):
        (cf._gh, cf.falhou_por_cota, cf.fonte_sumiu,
         cf.falhou_por_selecao_vazia) = self._orig


def _item(**kw):
    base = {"estado": "disparado", "run_id": 123, "nome": "fonte de teste",
            "canal": "semanestesia.pod", "drive_file_id": "ABC"}
    base.update(kw)
    return {"itens": [base]}


def teste_o_caso_que_quebrou_em_producao():
    """⚠️ O KeyError exato. Sem cota e sem fonte sumida, o fluxo cai no ramo
    do modelo — que era onde o `run_id` ja' tinha sido removido."""
    d = _item()
    with _Cenario(vazia=True):
        cf.devolver_os_que_falharam(d)      # antes: KeyError: 'run_id'
    assert d["itens"][0]["tentativas_modelo"] == 1


def teste_modelo_nao_gasta_a_tentativa_da_fonte():
    d = _item()
    with _Cenario(vazia=True):
        cf.devolver_os_que_falharam(d)
    it = d["itens"][0]
    assert it.get("tentativas", 0) == 0, "resposta do modelo gastou tentativa da fonte"
    assert it["estado"] == "pendente"


def teste_negativo_falha_comum_ainda_gasta_tentativa():
    """⚠️ TEOREMATICO. Se o ramo do modelo engolisse TUDO, fonte de fato
    quebrada nunca sairia da fila e giraria pra sempre."""
    d = _item()
    with _Cenario(vazia=False):
        cf.devolver_os_que_falharam(d)
    it = d["itens"][0]
    assert it["tentativas"] == 1, "falha comum tem de contar"
    assert "tentativas_modelo" not in it


def teste_negativo_cota_nao_gasta_nenhum_dos_dois():
    d = _item()
    with _Cenario(cota=True):
        cf.devolver_os_que_falharam(d)
    it = d["itens"][0]
    assert it.get("tentativas", 0) == 0 and "tentativas_modelo" not in it


def teste_negativo_sucesso_vira_pronto_e_nao_conta_nada():
    d = _item()
    with _Cenario(concluido="success"):
        cf.devolver_os_que_falharam(d)
    it = d["itens"][0]
    assert it["estado"] == "pronto", it
    assert it.get("tentativas", 0) == 0


def teste_teto_do_modelo_expulsa():
    d = _item(tentativas_modelo=cf.TETO_TENTATIVAS_MODELO - 1)
    with _Cenario(vazia=True):
        cf.devolver_os_que_falharam(d)
    assert d["itens"][0]["estado"] == "desistido"


def teste_fonte_sumida_e_terminal():
    d = _item()
    with _Cenario(sumiu=True):
        cf.devolver_os_que_falharam(d)
    assert d["itens"][0]["estado"] == "sem_fonte"


if __name__ == "__main__":
    n = 0
    for nome, fn in sorted(globals().items()):
        if nome.startswith("teste_") and callable(fn):
            fn(); n += 1; print(f"  ok  {nome}")
    print(f"{n} testes verdes")
