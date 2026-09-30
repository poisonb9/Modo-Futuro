# 30/09/2026: refaz SO o visual (layout zona segura) de um video de oferta ja publicado,
# reaproveitando o AUDIO do original e os dados de preco EXATOS do dia (pasta r/estado
# com os arquivos do commit do run). Uso: python ferramentas/refazer_visual_oferta.py <pasta> <numero>
import sys,json,subprocess,urllib.request
from pathlib import Path
sp=Path(sys.argv[1]); num=int(sys.argv[2])
sys.path.insert(0,'ferramentas');sys.path.insert(0,'.')
import video_oferta as vo
feitas=[json.loads(l) for l in open('estado/ofertas_feitas.jsonl',encoding='utf-8')]
vo.RAIZ=sp/'r'   # dados de preco EXATOS do run 36743009796 (commit 062bbab)
for f in feitas:
    if f['numero']!=num: continue
    c=f['canal']; nome=f"{f['dia']}_{c.replace('.','-')}_{f['id']}"
    orig=sp/'out'/(nome+'_orig.mp4')
    urllib.request.urlretrieve(f"https://github.com/poisonb9/Modo-Futuro/releases/download/ofertas-2026-09/{nome}.mp4",orig)
    d=vo.dados(f['id']); d['gancho']=''; d['marca']=vo.MARCAS[c]; d['numero']=num; d['id']=f['id']; d['festa']=True
    assert abs(d['agora']-f['agora'])<0.005 and d['hora'] in f['comentario'], (d['agora'],d['hora'])
    cart=[vo.cartao(vo.baixar(u),820) for u in d['imagens']]; fundo=vo.base_fundo()
    saida=sp/'out'/(nome+'_v2.mp4')
    p=subprocess.Popen(["ffmpeg","-y","-v","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{vo.W}x{vo.H}","-r",str(vo.FPS),"-i","-",
        "-i",str(orig),"-map","0:v","-map","1:a","-t",str(vo.DUR),"-c:v","libx264","-preset","medium","-crf","19",
        "-pix_fmt","yuv420p","-c:a","copy","-movflags","+faststart",str(saida)],stdin=subprocess.PIPE)
    for i in range(int(vo.DUR*vo.FPS)):
        p.stdin.write(vo.quadro(i/vo.FPS,d,fundo,cart).tobytes())
    p.stdin.close();p.wait();orig.unlink()
    print(c,saida.name,round(saida.stat().st_size/1e6,1),'MB')
