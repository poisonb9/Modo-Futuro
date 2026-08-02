"""Gera .ass com efeito karaokê (palavra acende conforme é falada) e
destaque de palavra por grupo (ver engine/destaque.py).
"""
import itertools
import os
from pathlib import Path

from . import destaque as _destaque

MAX_LINHA = 3          # palavras por tela — Shorts pede pouco texto e grande
BASE = "&H00FFFFFF"      # branco

# Paleta do destaque de palavra — girada por grupo, na ordem abaixo.
# Valores em BGR (formato de override do ASS, "&HBBGGRR&"), sem rosa: pedido
# do Bryan em 02/08/2026 foi mapear a referência (rosa/vermelho/azul) para
# azul/verde/vermelho, mantendo vermelho como vermelho.
_AZUL = "&HFF9900&"       # RGB(0,153,255)
_VERDE = "&H76E600&"      # RGB(0,230,118)
_VERMELHO = "&H303BFF&"   # RGB(255,59,48)
PALETA = (_AZUL, _VERDE, _VERMELHO)
_RESET = "&HFFFFFF&"      # branco, pra voltar depois da palavra destacada


def _t(seg: float) -> str:
    seg = max(0.0, seg)
    h, resto = divmod(seg, 3600)
    m, s = divmod(resto, 60)
    return f"{int(h)}:{int(m):02d}:{s:05.2f}"


def escrever(palavras: list[dict], destino: Path, largura: int, altura: int) -> Path | None:
    """Cria o arquivo .ass. Devolve None se não houver o que legendar."""
    if not palavras:
        return None

    # fonte proporcional à altura: mesma leitura em 9:16 e 16:9. Menor que
    # antes e com margem lateral generosa — texto fica num bloco central,
    # nunca encosta na borda mesmo em frase mais longa.
    corpo = max(22, int(altura * 0.038))
    # LEGENDA_MARGEM_V_FRAC: override pontual pra vídeo específico com algo
    # cobrindo a legenda na posição normal (ex: caixa branca de UI na fonte).
    #
    # Padrão subiu de 0.18 para 0.30 em 28/07/2026: a 18% da base a legenda
    # cai justamente na faixa que a UI do TikTok ocupa — nome do perfil,
    # curtir, comentar, compartilhar. O corpus recomenda o texto
    # ligeiramente acima do centro (PLAYBOOK §5). Legenda escondida atrás
    # de botão não é lida, e legenda é uma das 3 camadas de edição que
    # sustentam o RPM.
    frac_v = float(os.environ.get("LEGENDA_MARGEM_V_FRAC", "0.30"))
    margem_v = int(altura * frac_v)   # sobe o texto: no Shorts a UI cobre a base
    margem_lat = int(largura * 0.12)
    contorno = max(2, corpo // 14)

    cab = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {largura}
PlayResY: {altura}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: K,Inter Black,{corpo},{BASE},{BASE},&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,{contorno},2,2,{margem_lat},{margem_lat},{margem_v},1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""

    grupos = [palavras[i:i + MAX_LINHA] for i in range(0, len(palavras), MAX_LINHA)]
    destaques = _destaque.marcar(grupos)
    cores = itertools.cycle(PALETA)

    linhas = []
    for grupo, idx_destaque in zip(grupos, destaques):
        ini, fim = grupo[0]["inicio"], grupo[-1]["fim"]
        if fim <= ini:
            fim = ini + 0.4
        cor = next(cores) if idx_destaque is not None else None
        partes = []
        # \k usa centésimos de segundo
        for j, p in enumerate(grupo):
            dur = max(1, int((p["fim"] - p["inicio"]) * 100))
            palavra = p["palavra"].upper()
            if j == idx_destaque:
                partes.append(f"{{\\k{dur}\\c{cor}}}{palavra} {{\\c{_RESET}}}")
            else:
                partes.append(f"{{\\k{dur}}}{palavra} ")
        texto = "".join(partes).strip()
        linhas.append(f"Dialogue: 0,{_t(ini)},{_t(fim)},K,,0,0,0,,{texto}")

    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(cab + "\n".join(linhas) + "\n", encoding="utf-8")
    return destino
