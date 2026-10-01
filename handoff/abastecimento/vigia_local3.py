import sys,json,re,time,unicodedata
from pathlib import Path
sys.path.insert(0,'.')
import contas_drive as cd, enviar_bruto_drive as eb
T=sys.argv[1]
PASTA={'cozinha.importada':'COZINHA','truque.importado':'TRUQUE IMPORTADO','atefalhar':'ATE FALHAR','modofuturo':'MODO FUTURO'}
def n(s): return re.sub(r'[^a-z0-9]','',"".join(c for c in unicodedata.normalize("NFKD",s.lower()) if c.isascii()))
falta={}
for f in ('sel.json','sel2.json'):
    for k,its in json.load(open(f'{T}/{f}',encoding='utf-8')).items():
        for i in its: falta[i['id']]=(k,i)
raiz=Path.home()/'Downloads'/'abastecer'
# ja' subidos antes da cota encher: o que nao existe mais local e ja' foi -> so' os que ainda aparecerem
t0=time.time()
while falta and time.time()-t0<4*3600:
    for v in raiz.rglob('*.mp4'):
        a=v.stat().st_size; time.sleep(10)
        if not v.exists() or v.stat().st_size!=a: continue
        base=n(v.name)
        hit=next((vid for vid,(k,i) in falta.items() if n(i['titulo'])[:25] and n(i['titulo'])[:25] in base),None)
        if not hit: continue
        k,i=falta.pop(hit)
        conta=cd.escolher()
        if not conta: print('TODAS AS CONTAS CHEIAS — parei',flush=True); sys.exit(1)
        s=cd.servico(conta); dest=eb._achar_ou_criar_subpasta(s,conta['raw'],PASTA[k])
        print('>>',conta['nome'],k,i['titulo'][:60],flush=True)
        try: eb.enviar(v,dest,apagar_local=True,conta=conta['nome'],subpasta='',url=i['url'])
        except Exception as e: print('ERRO',e,flush=True); falta[hit]=(k,i)
    if not any(raiz.rglob('*')) : pass
    time.sleep(30)
