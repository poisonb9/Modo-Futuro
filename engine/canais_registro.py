# -*- coding: utf-8 -*-
"""A UNICA fonte dos canais: nome, ids do Buffer e variavel do token.

POR QUE ESTE ARQUIVO EXISTE

Ate' 04/09/2026 a mesma tabela estava copiada em CINCO arquivos
(`painel_filas`, `escolher_impulsionar`, `registrar_desempenho`,
`conferir_postados`, `repor_fila`). Copia nao se contradiz sozinha — ela se
contradiz quando alguem edita UMA. Foi o que aconteceu com a cozinha:

    cozinha.importada      em repor_fila, canais/, cortar.yml, cortar_de_bruto
    cozinha.internacional  em painel_filas, vigia_raw, escolher_impulsionar,
                           registrar_desempenho

⚠️ E os dois nomes estao CERTOS — sao coisas diferentes que foram usadas como
se fossem a mesma:

    nome_buffer  o nome do canal DENTRO do Buffer. E' o que a guarda
                 CANAL_ESPERADO compara antes de publicar, e o que os
                 workflows usam pra escolher o token. Medido em 04/09: o da
                 cozinha e' `cozinha.importada`.
    arroba       o @ do perfil no TikTok, que e' o que o Bryan le' no painel.
                 O da cozinha e' `@cozinha.internacional`.

Confundir os dois tem caminho de estrago conhecido: o vigia mandava
`cozinha.internacional` como `canal`, o workflow comparava com
`cozinha.importada`, nao batia, caia no `else` e o token que saia era o do
**modofuturo**. So' nao houve estrago porque o `engine/escopo.py` barra a
cozinha antes — duas guardas independentes e nenhuma sabendo da outra.

⚠️ CANAL NOVO SE ACRESCENTA AQUI, E SO' AQUI. A fase 2 traz dois canais de
achadinhos; sem esta tabela seriam doze edicoes espalhadas, e a chance de as
doze concordarem e' a mesma que ja' falhou uma vez.
"""
from __future__ import annotations


class Canal:
    """Um canal. `motor=False` quer dizer que ESTE motor nao o serve."""

    def __init__(self, nome_buffer: str, arroba: str, org: str, canal_id: str,
                 env: str, motor: bool = True, servico: str = "tiktok",
                 apelidos: tuple[str, ...] = ()):
        self.nome_buffer = nome_buffer
        self.arroba = arroba
        self.org = org
        self.canal_id = canal_id
        self.env = env
        self.motor = motor
        self.servico = servico
        self.apelidos = apelidos

    def __repr__(self) -> str:
        return f"<Canal {self.nome_buffer}>"


CANAIS: dict[str, Canal] = {
    c.nome_buffer: c for c in [
        Canal("modofuturo", "@modofuturo",
              "6a6ca3c3aba3767824bf6234", "6a6cd9d54b2d03035f771631",
              "BUFFER_TOKEN"),
        Canal("truque.importado", "@truque.importado",
              "6a94c752e0b1602e8c5cf1ae", "6a94c8f3065799be465981f6",
              "BUFFER_TOKEN_TRUQUEIMPORTADO"),
        Canal("semanestesia.pod", "@semanestesia.pod",
              "6a937e2ccae8f6fdedefa317", "6a938ce8065799be46508cc6",
              "BUFFER_TOKEN_SEMANESTESIA"),
        Canal("atefalhar", "@atefalhar",
              "6a94a9f9ca5d8883aa924198", "6a94aaf5065799be46581e1d",
              "BUFFER_TOKEN_ATEFALHAR"),
        # ⚠️ motor=False: a cozinha precisa de conversao de medidas, que nao
        # existe neste repositorio. Quem a serve e' o `bryanaw2121-sketch/
        # pipeline`. Aqui a gente so' RELATA a fila dela.
        Canal("cozinha.importada", "@cozinha.internacional",
              "6a90dddb9bb05f07b058e9bc", "6a90de80ccaf649a672ebe15",
              "BUFFER_TOKEN_COZINHA", motor=False,
              apelidos=("cozinha.internacional", "cozinha")),
    ]
}

# apelido -> nome_buffer. Existe pra que o nome antigo, que ainda circula em
# manifesto e em log, continue resolvendo — e nao pra autorizar nome novo.
APELIDOS: dict[str, str] = {
    a: c.nome_buffer for c in CANAIS.values() for a in c.apelidos
}


def canonico(nome: str | None) -> str | None:
    """O `nome_buffer` de um canal, aceitando apelido e `@`.

    ⚠️ DEVOLVE None PARA DESCONHECIDO, nunca um palpite. Chutar canal foi a
    causa medida de oito clipes de podcast irem parar no canal de chips.
    """
    n = (nome or "").strip().lower().lstrip("@")
    if not n:
        return None
    if n in CANAIS:
        return n
    return APELIDOS.get(n)


def do_motor() -> set[str]:
    return {n for n, c in CANAIS.items() if c.motor}


def tabela(env_por_nome: bool = True) -> dict:
    """(org, canal_id, env) por canal — o formato que os scripts ja' usavam."""
    return {n: (c.org, c.canal_id, c.env) for n, c in CANAIS.items()}
