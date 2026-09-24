import sys, numpy as np
from PIL import Image, ImageFilter
D=r'C:/Users/Administrator/Desktop/inauguracao/'
L=96   # largura final (48 px CSS @2x cobre o celular)
for n in sys.argv[1:]:
    big=Image.open('out/'+n+'.webp').convert('RGBA'); W,H=big.size
    cut=Image.open(D+'recortados/'+n+'.png'); wc,hc=cut.size; lado=max(wc,hc)
    k=W/L
    a=np.asarray(big).copy()
    fio=a.copy(); fio[:lado-int(0.25*hc)]=0          # so' abaixo da parte baixa do balao
    bal=a.copy(); bal[lado:]=0                       # balao (quadrado de cima)
    # fio: engrossa ANTES de reduzir para sobreviver com ~2 px na saida
    fa=Image.fromarray(fio[:,:,3]).filter(ImageFilter.MaxFilter(2*int(k)+1))
    fio_img=Image.new('RGBA',(W,H),(150,146,160,0)); fio_img.putalpha(fa.point(lambda v: min(255,int(v*0.9))))
    h=round(H/k)
    fio_s=fio_img.resize((L,h),Image.LANCZOS)
    bal_s=Image.fromarray(bal).resize((L,h),Image.LANCZOS)
    t=Image.new('RGBA',(L,h),(0,0,0,0)); t.alpha_composite(fio_s); t.alpha_composite(bal_s)
    t.save('out/'+n+'_p.webp','WEBP',quality=90,method=6)
    print(n,t.size)
