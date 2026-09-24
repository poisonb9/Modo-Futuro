import sys, numpy as np
from PIL import Image
D=r'C:/Users/Administrator/Desktop/inauguracao/'
def faz(n, out):
    im=Image.open(D+n+'.png').convert('RGBA'); bg=Image.new('RGBA',im.size,(255,255,255,255)); bg.alpha_composite(im)
    o=np.asarray(bg.convert('RGB')).astype(float)
    cut=Image.open(D+'recortados/'+n+'.png').convert('RGBA'); wc,hc=cut.size
    dark=255-o.min(axis=2)            # distancia do branco
    m=dark>30
    ys,xs=np.nonzero(m)
    # largura do balao: linhas com mais de 15% da largura marcada (o fio e' estreito)
    larg=m.sum(1); linhas=np.nonzero(larg>0.15*larg.max())[0]
    top,bot=linhas.min(),linhas.max()
    cols=np.nonzero(m[top:bot+1].any(0))[0]; left,right=cols.min(),cols.max()
    s=wc/(right-left+1)
    fim=ys.max()                        # ponta do fio
    b_orig=int(top+hc/s)                # base do balao no original
    # fio: da base-8% ate' a ponta, alfa pela escuridao (contorno cinza da fita)
    y0=int(top+0.45*hc/s)
    abaixo=m[b_orig+5:fim+1, left:right+1]
    cx=int(np.median(np.nonzero(abaixo)[1])) if abaixo.any() else (right-left)//2
    reg=o[y0:fim+1, left:right+1]
    alfa=np.clip((255-reg.min(axis=2)-6)*4.0,0,255)
    faixa=np.zeros_like(alfa); lb=int(0.12*(right-left)); faixa[:,max(0,cx-lb):cx+lb]=1
    alfa=alfa*faixa
    rgb=np.clip(reg*0.85,0,255)        # leve escurecida: fita le' sobre branco
    fio=Image.fromarray(np.dstack([rgb,alfa]).astype(np.uint8),'RGBA')
    fio=fio.resize((wc,max(1,round(fio.height*s))),Image.LANCZOS)
    H=round((y0-top)*s)+fio.height
    tela=Image.new('RGBA',(wc,max(H,hc)),(0,0,0,0))
    tela.alpha_composite(fio,(0,round((y0-top)*s)))
    tela.alpha_composite(cut,(0,0))    # balao por cima do nascimento do fio
    tela.save(out)
    print(n,'s=%.3f'%s,'balao',wc,hc,'total',tela.size,'fio/balao %.2f'%(tela.height/hc))
for n in sys.argv[2:]: faz(n, sys.argv[1]+'/'+n+'.png')
