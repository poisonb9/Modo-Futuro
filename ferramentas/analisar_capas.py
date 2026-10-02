import sys, json, base64, requests, mimetypes, io
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
R = r"C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine"
sys.path.insert(0, R)
from engine import keys
from PIL import Image
PASTA = Path(sys.argv[1]); SAIDA = Path(sys.argv[2])
P = """Esta imagem deve ser uma capa da revista Capricho (ou revista teen brasileira). Analise e responda SO' JSON:
{"e_capa": true/false, "revista": "<nome>", "ano_ou_epoca": "<se visivel ou estimado: 'c. 2007'>",
"quem_na_capa": "<nome(s) ou descricao>", "nome_em_destaque": "<o nome escrito grande, se houver>",
"chamada_principal": "<texto exato>", "chamadas_secundarias": ["<texto exato>", ...],
"brinde": "<poster, adesivo, teste, encarte... ou ''>",
"formulas": [lista entre: "nome_do_idolo","numero","segredo","bastidor","exclusivo","mico","intimidade_namoro","polemica","teste","voce","pergunta","transformacao","beleza_truque","moda","garotos","conquista","brinde","preco","comparacao","exclamacao","silabas_separadas"],
"palavras_gatilho": ["<palavras de impacto usadas>"],
"cores": "<paleta>", "logo": "<cor/posicao do logo>", "pose_olhar": "<olhar para camera? close? sorriso?>",
"hierarquia": "<o que o olho le primeiro, segundo, terceiro>"}
Use "" quando ilegivel. Nao invente texto."""
rot = keys.gemini()
def um(f):
    im = Image.open(f).convert("RGB"); im.thumbnail((1100, 1100))
    b = io.BytesIO(); im.save(b, "JPEG", quality=85)
    corpo = {"contents":[{"parts":[{"inline_data":{"mime_type":"image/jpeg","data":base64.b64encode(b.getvalue()).decode()}},{"text":P}]}],
             "generationConfig":{"temperature":0,"responseMimeType":"application/json"}}
    for _ in range(12):
        k = rot.proxima().strip()
        for modelo in ("gemini-3.6-flash", "gemini-3.5-flash"):
            try:
                r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent",
                                  headers={"x-goog-api-key": k}, json=corpo, timeout=120)
            except Exception:
                continue
            if r.status_code == 200:
                try:
                    d = json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"]); d["arquivo"] = f.name; return d
                except Exception:
                    continue
            if r.status_code in (403, 429):
                rot.queimar(k); break
    return {"arquivo": f.name, "erro": "sem resposta"}
fs = sorted(p for p in PASTA.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
velho = {x["arquivo"]: x for x in (json.loads(SAIDA.read_text(encoding="utf-8")) if SAIDA.exists() else []) if not x.get("erro")}
falta = [f for f in fs if f.name not in velho]
print("ja feitas", len(velho), "faltam", len(falta), flush=True)
import time
novos = []
for f in falta:
    novos.append(um(f)); time.sleep(4)
    if len(novos) % 10 == 0: print(len(novos), flush=True)
res = list(velho.values()) + novos
SAIDA.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(res), "feitas;", sum(1 for x in res if x.get("erro")), "erros;", sum(1 for x in res if x.get("e_capa")), "capas")
