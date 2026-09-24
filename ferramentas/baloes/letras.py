from PIL import Image; import numpy as np
from scipy import ndimage as nd
im=Image.open(r'C:\Users\Administrator\.claude\uploads\db30843c-ef0a-4247-afa8-e2299545dad0\ba3413b9-image.png').convert('RGBA')
A=np.asarray(im); a=A[:,:,3]>40
for it in range(2,40,2):
    e=nd.binary_erosion(a,iterations=it); lab,n=nd.label(e)
    sz=nd.sum(e,lab,range(1,n+1)); k=int((sz>800).sum())
    print(it,n,k)
    if k>=11: break
seeds=np.zeros_like(lab); j=0
for i,s in enumerate(sz):
    if s>800: j+=1; seeds[lab==i+1]=j
# cada pixel do contorno vai para a semente mais proxima
d,(iy,ix)=nd.distance_transform_edt(seeds==0,return_indices=True)
dono=seeds[iy,ix]*a
cx=[np.nonzero(dono==k)[1].mean() for k in range(1,j+1)]
ordem=np.argsort(cx)
import os; os.makedirs('letras',exist_ok=True)
for pos,k in enumerate(ordem,1):
    m=dono==k+1; ys,xs=np.nonzero(m)
    L=A.copy(); L[~m,3]=0
    c=Image.fromarray(L).crop((xs.min(),ys.min(),xs.max()+1,ys.max()+1))
    c.save('letras/%02d.png'%pos); print(pos,c.size,'x=%d'%xs.mean())
