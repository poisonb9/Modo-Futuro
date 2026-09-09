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
        # ⚠️ O @ MUDOU EM 08/09/2026: era `@truque.importado`, virou
        # `@achadinho.make` (renomeado pelo Bryan, confirmado por ele).
        #
        # O `nome_buffer` NAO muda junto, e isso e' de proposito: ele e' o
        # nome do canal DENTRO do Buffer, com o qual a guarda CANAL_ESPERADO
        # compara e pelo qual os workflows escolhem o token. Trocar os dois
        # ao mesmo tempo quebraria a publicacao inteira desse canal.
        #
        # Foi lendo os LINKS do export do TikTok que isso apareceu: os videos
        # de maquiagem apontavam para tiktok.com/@achadinho.make. O nome do
        # arquivo de export segue o @ atual, entao ele chega como
        # `Content_achadinho.make.zip` — quem importar sem saber disso vai
        # achar que e' um sexto canal, e que o truque sumiu.
        Canal("truque.importado", "@achadinho.make",
              "6a94c752e0b1602e8c5cf1ae", "6a94c8f3065799be465981f6",
              "BUFFER_TOKEN_TRUQUEIMPORTADO",
              apelidos=("truque.importado", "achadinho.make")),
        Canal("semanestesia.pod", "@semanestesia.pod",
              "6a937e2ccae8f6fdedefa317", "6a938ce8065799be46508cc6",
              "BUFFER_TOKEN_SEMANESTESIA"),
        Canal("atefalhar", "@atefalhar",
              "6a94a9f9ca5d8883aa924198", "6a94aaf5065799be46581e1d",
              "BUFFER_TOKEN_ATEFALHAR"),
        # ⚠️ motor=False: a cozinha precisa de conversao de medidas, que nao
        # existe neste repositorio. Quem a serve e' o `bryanaw2121-sketch/
        # pipeline`. Aqui a gente so' RELATA a fila dela.
        #
        # ⚠️⚠️ MUDANCA AGENDADA PARA 26/09/2026 — NAO APLICAR ANTES.
        #
        # Decisao do Bryan em 09/09/2026: o canal vira **@achadinho.chef**. O
        # NOME DE EXIBICAO ele ja' pode trocar (e nao afeta nada aqui); o @
        # tem carencia do TikTok e so' libera em 26/09.
        #
        # Quando o @ mudar, sao TRES lugares, e esquecer qualquer um quebra
        # alguma coisa em silencio:
        #
        #   1. AQUI: `arroba` vira "@achadinho.chef", e "cozinha.internacional"
        #      CONTINUA em apelidos (o nome antigo circula em arquivo velho).
        #   2. O NOME DO ARQUIVO DE EXPORT muda junto: passa a chegar
        #      `Content_achadinho.chef.zip`. Ja' enganou uma vez com o
        #      truque->achadinho.make: quem importa sem saber acha que
        #      apareceu um canal novo e que o antigo sumiu.
        #   3. O OUTRO REPOSITORIO (`bryanaw2121-sketch/pipeline`), que e'
        #      quem de fato serve este canal. Se o @ estiver escrito la',
        #      muda nos dois — dois registros discordando e' exatamente o
        #      defeito que o cabecalho deste arquivo documenta.
        #
        # ⚠️ E O `nome_buffer` NAO MUDA. Continua "cozinha.importada", pelo
        # mesmo motivo do truque.importado logo acima: e' com ele que a guarda
        # CANAL_ESPERADO compara e por ele que o workflow escolhe o token.
        #
        # ⚠️ Havera' DOIS canais "achadinho" (make e chef). E' de proposito,
        # e' familia de marca. Nao e' duplicata, nao "conserte".
        Canal("cozinha.importada", "@cozinha.internacional",
              "6a90dddb9bb05f07b058e9bc", "6a90de80ccaf649a672ebe15",
              "BUFFER_TOKEN_COZINHA", motor=False,
              apelidos=("cozinha.internacional", "cozinha")),

        # ⚠️⚠️ AS DUAS DE BAIXO EXISTEM NO TIKTOK E **NAO** NO BUFFER.
        #
        # Descobertas em 09/09/2026, na tela de "Mudar de conta": o app tem
        # SETE contas e este registro tinha CINCO. Elas ficavam invisiveis pra
        # maquina — sem guarda CANAL_ESPERADO, sem aparecer em relatorio, e um
        # export chegando como `Content_fatura.chora.zip` pareceria canal novo
        # do nada.
        #
        # Sao a FASE 2 (ver FASE2.md): canais de achadinho puro, com link de
        # afiliado, pagina na bio e grupo de WhatsApp. Decisao do Bryan em
        # 09/09: os dois canais Achadinho apontam para o grupo.
        #
        # ⚠️ `org`, `canal_id` e `env` estao VAZIOS DE PROPOSITO — elas nao
        # existem no Buffer ainda, e nao ha' token. Preencher com valor
        # inventado seria pior que nao ter: a publicacao sairia pelo token
        # errado, em silencio, que e' o defeito que o cabecalho deste arquivo
        # documenta. `motor=False` mantem as duas fora de tudo que publica.
        #
        # ⚠️ E ha' um teste guardando isto: `teste_canal_sem_buffer.py`. Quando
        # elas ganharem token, o teste ACUSA — e' o lembrete de preencher os
        # tres campos no mesmo commit.
        Canal("achadinhos.instantaneos", "@achadinhos.instantaneos",
              "", "", "", motor=False,
              apelidos=("achadinhos.instantaneos", "instantaneos")),
        Canal("fatura.chora", "@fatura.chora",
              "", "", "", motor=False,
              apelidos=("fatura.chora", "fatura")),
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
