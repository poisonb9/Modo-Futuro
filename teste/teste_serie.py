"""Serie numerada no titulo (Sem Anestesia, 27/09/2026)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engine import serie  # noqa: E402

erros = 0
def checar(ok, msg):
    global erros
    erros += not ok
    print("  ok  " if ok else "  ERRO", msg)

T = ["Goggins sem filtro #2: a lista na geladeira", "GOGGINS SEM FILTRO #7: x",
     "Protocolo #1: agua fria", "outro titulo"]
checar(serie.ultimo("Goggins sem filtro", T) == 7, "maior numero, sem ligar p/ caixa")
checar(serie.ultimo("Seu cérebro desiste antes", T) == 0, "serie nova comeca do 0")
u = {}
c = serie.numerar({"titulo": "135 kg e 3 empregos", "serie": "goggins sem filtro"},
                  "semanestesia.pod", u, T)
checar(c["titulo"] == "Goggins sem filtro #8: 135 kg e 3 empregos", c["titulo"])
c2 = serie.numerar({"titulo": "outro", "serie": "Goggins sem filtro"},
                   "semanestesia.pod", u, T)
checar(c2["titulo"].startswith("Goggins sem filtro #9:"), "2o do mesmo run: +1")
checar(serie.numerar({"titulo": "x", "serie": "Protocolo"}, "modofuturo", {}, T)["titulo"] == "x",
       "canal sem series: titulo intacto")
checar(serie.numerar({"titulo": "x", "serie": "inventada"}, "semanestesia.pod", {}, T)["titulo"] == "x",
       "serie fora da lista: intacto")
checar(serie.numerar({"titulo": "x", "serie": None}, "semanestesia.pod", {}, T)["titulo"] == "x",
       "sem serie: intacto")
print("\ntudo verde" if not erros else f"\n{erros} ERRO(S)")
sys.exit(1 if erros else 0)
