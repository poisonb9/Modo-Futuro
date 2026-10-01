import sys,json,re,time,unicodedata
from pathlib import Path
sys.path.insert(0,'.')
import contas_drive as cd, enviar_bruto_drive as eb
sel=json.load(open(sys.argv[1],encoding='utf-8'))
PASTA={'cozinha.importada':'COZINHA','truque.importado':'TRUQUE IMPORTADO','atefalhar':'ATE FALHAR'}
def n(s): return re.sub(r'[^a-z0-9]','',"".join(c for c in unicodedata.normalize("NFKD",s.lower()) if c.isascii()))
c=cd.conta_por_nome('principal'); s=cd.servico(c)
dest={k:eb._achar_ou_criar_subpasta(s,c['raw'],v) for k,v in PASTA.items()}
falta={i['id']:(k,i) for k,its in sel.items() for i in its}
raiz=Path.home()/'Downloads'/'abastecer'
t0=time.time()
while falta and time.time()-t0<4*3600:
    for v in raiz.rglob('*.mp4'):
        if v.name.endswith('.part'): continue
        a=v.stat().st_size; time.sleep(10)
        if not v.exists() or v.stat().st_size!=a: continue
        base=n(v.name)
        hit=next((vid for vid,(k,i) in falta.items() if n(i['titulo'])[:25] and n(i['titulo'])[:25] in base),None)
        if not hit: continue
        k,i=falta.pop(hit)
        print('>>',k,i['titulo'][:60],flush=True)
        try: eb.enviar(v,dest[k],apagar_local=True,conta='principal',subpasta='',url=i['url'])
        except Exception as e: print('ERRO',e,flush=True); falta[hit]=(k,i)
    time.sleep(30)
print('FALTARAM:',[i['titulo'][:50] for k,i in falta.values()])
