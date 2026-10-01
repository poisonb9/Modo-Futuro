import sys,json,re,glob,requests,time
sys.path.insert(0,'.')
from engine import keys
usados=set()
for f in glob.glob('*.json')+glob.glob('estado/**/*.json',recursive=True):
    if 'radar_' in f: continue
    try: usados|=set(re.findall(r'(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})',open(f,encoding='utf-8',errors='ignore').read()))
    except: pass
TEMA={'atefalhar':'disciplina, treino, força mental, rotina (masculino, motivação dura)',
      'modofuturo':'tecnologia, chips, fábricas, engenharia, futuro — com imagem que se mexe (NÃO slideshow, NÃO análise/geopolítica)'}
rot=keys.gemini()
PED="""Você é curador de vídeos-fonte para cortes de TikTok do canal com tema: {tema}.
Assista ao vídeo e avalie com rigor. Critérios:
1) GANCHO: existem pelo menos 5 momentos que prendem nos 3 primeiros segundos (frase forte, surpresa, promessa)?
2) AUTOSSUFICIÊNCIA: trechos de 30-90s fazem sentido sozinhos (gancho, retenção, recompensa)?
3) IMAGEM: a câmera/cena se mexe (não é slideshow, tela parada ou só narração sobre fotos)?
4) TEMA: fica 100% no tema do canal?
Responda SÓ JSON: {{"nota":0-10,"gancho":0-10,"autossuficiencia":0-10,"imagem":0-10,"tema":0-10,"motivo":"uma frase","melhor_momento":"mm:ss"}}"""
def avaliar(url,tema):
    for _ in range(min(4,len(rot))):
        k=rot.proxima().strip()
        r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={k}",
          json={"contents":[{"parts":[{"file_data":{"file_uri":url}},{"text":PED.format(tema=tema)}]}],
                "generationConfig":{"temperature":0,"responseMimeType":"application/json","mediaResolution":"MEDIA_RESOLUTION_LOW"}},timeout=300)
        if r.status_code in (403,429): rot.queimar(k); continue
        if r.status_code!=200: return {"erro":r.status_code,"txt":r.text[:150]}
        return json.loads(r.json()["candidates"][0]["content"]["parts"][0]["text"])
    return {"erro":"chaves esgotadas"}
res={}
for canal,arq in [('atefalhar','radar_atefalhar.json'),('modofuturo','radar_modofuturo.json')]:
    its=[i for i in json.load(open(arq,encoding='utf-8')) if i['id'] not in usados and i.get('views',0)>=150_000]
    its.sort(key=lambda i:-i.get('nota',0)); por={}; cand=[]
    for i in its:
        c=i.get('canal','').strip()
        if por.get(c,0)>=2: continue
        por[c]=por.get(c,0)+1; cand.append(i)
        if len(cand)==10: break
    print(f"== {canal}: {len(its)} novos, {len(cand)} vão ao Gemini",flush=True)
    for i in cand:
        a=avaliar(i['url'],TEMA[canal]); i['gemini']=a
        print(f"  {a.get('nota','ERR')} {i['titulo'][:55]} | {a.get('motivo',a)}",flush=True)
    res[canal]=cand
json.dump(res,open(sys.argv[1],'w',encoding='utf-8'),ensure_ascii=False,indent=1)
