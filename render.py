#!/usr/bin/env python3
"""Deterministic original CG journey. No downloaded audiovisual assets."""
import argparse, json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops
ROOT=Path(__file__).resolve().parent
CUTS=[0,5,16,29,43,59,70]
JP=['地球を離れる','太陽系を越えて','銀河系の外へ','無数の銀河','宇宙の巨大な網','観測可能な宇宙']
EN=['Leaving Earth','Beyond the Solar System','Beyond the Milky Way','Countless Galaxies','The Cosmic Web','The Observable Universe']
def smooth(x):
    x=np.clip(x,0,1); return x*x*(3-2*x)
def audio(path):
    sr=48000; t=np.arange(70*sr,dtype=np.float64)/sr
    a=np.zeros_like(t); rng=np.random.default_rng(19)
    # Slow minor/add9 orchestral-synth pads, sub bass, pulses and transition sweeps.
    for j,notes in enumerate([[55,82.4069,110,130.8128,164.8138],[43.6535,65.4064,87.3071,110,130.8128],[65.4064,98,130.8128,155.5635,196],[49,73.4162,98,123.4708,146.8324]]):
        start=j*17.5; env=smooth((t-start)/3)*(1-smooth((t-start-15)/2.5))
        for k,f in enumerate(notes):
            a+=env*(.075/(1+k*.3))*(np.sin(2*np.pi*f*t+.18*np.sin(t*.31))+ .22*np.sin(2*np.pi*f*2*t))
    a+=.035*np.sin(2*np.pi*27.5*t)*(1+np.sin(t*1.8))
    noise=rng.normal(0,1,len(t)); noise=np.convolve(noise,np.ones(18)/18,mode='same')
    for start in [0,4,15,28,42,58]:
        u=t-start; e=np.exp(-np.maximum(u,0)*1.7)*(u>=0)
        a+=.26*e*np.sin(2*np.pi*(70*u-13*u*u))+ .42*noise*np.exp(-((u-.45)/.45)**2)
    a*=smooth(t/.025)*(1-smooth((t-67)/3))
    stereo=np.stack([a,a*.96+.025*np.sin(2*np.pi*220*t)*np.sin(t*.4)],axis=1)
    stereo*=.82/max(np.max(np.abs(stereo)),.001)
    with wave.open(str(path),'wb') as w:
        w.setnchannels(2);w.setsampwidth(2);w.setframerate(sr);w.writeframes((stereo*32767).astype('<i2').tobytes())
    return float(np.max(np.abs(stereo)))
class Renderer:
    def __init__(self,w,h):
        self.w,self.h=w,h; self.s=w/1080; self.rng=np.random.default_rng(1024); self.boxes=[]
        font='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
        if not Path(font).exists(): raise RuntimeError('Install fonts-noto-cjk')
        self.fonts={n:ImageFont.truetype(font,max(10,round(n*self.s))) for n in [22,26,30,36,44,54,66]}
        self.stars=self.rng.uniform([-1.4,-2,.3],[1.4,2,2.3],(900,3))
        self.clouds=[]
        n=5200; r=self.rng.power(1.5,n)*1.2; arm=self.rng.integers(0,4,n); theta=r*5+arm*np.pi/2+self.rng.normal(0,.2,n)
        self.clouds.append(np.column_stack([r*np.cos(theta),r*np.sin(theta)*.48,self.rng.normal(0,.055,n)]))
        centers=self.rng.normal(0,.75,(65,3)); group=[]
        for c in centers:
            q=self.rng.normal(0,[.045,.016,.025],(45,3));group.extend(c+q)
        self.clouds.append(np.array(group))
        nodes=self.rng.uniform(-1.1,1.1,(65,3)); web=[]
        for i,p in enumerate(nodes):
            for j in np.argsort(np.linalg.norm(nodes-p,axis=1))[1:4]:
                if j<i:continue
                u=self.rng.uniform(0,1,(85,1));web.extend(p*(1-u)+nodes[j]*u+self.rng.normal(0,.019,(85,3)))
        self.clouds.append(np.array(web))
        self.earth=self.make_earth(1000)
    def make_earth(self,n):
        y,x=np.mgrid[-1:1:complex(n),-1:1:complex(n)]; rr=x*x+y*y;z=np.sqrt(np.maximum(0,1-rr))
        lon=np.arctan2(x,z);lat=np.arcsin(np.clip(y,-1,1))
        terrain=np.sin(lon*4+np.sin(lat*5)*1.5)+.5*np.cos(lon*9-lat*7)+.28*np.sin(lat*19+lon*13)
        land=terrain>.58;cloud=np.maximum(0,np.sin(lon*21+lat*17+np.sin(lat*14)*2)-.72)*2
        col=np.where(land[...,None],np.array([48,133,106]),np.array([9,65,147])).astype(float)
        col=col*(.22+.78*np.maximum(0,-x*.5-y*.25+z*.8))[...,None]
        col+=cloud[...,None]*100;col+=(np.maximum(0,1-z)**5)[...,None]*np.array([25,100,170])
        arr=np.zeros((n,n,4),dtype=np.uint8);arr[:,:,:3]=np.clip(col,0,255);arr[:,:,3]=(rr<=1)*255
        return Image.fromarray(arr)
    def text(self,img,txt,y,size=44,color=(235,244,255),anchor='mm'):
        d=ImageDraw.Draw(img);f=self.fonts[size]; pos=(self.w*.47,self.h*y)
        box=d.textbbox(pos,txt,font=f,anchor=anchor,stroke_width=2)
        assert box[0]>=self.w*.055 and box[2]<=self.w*.89 and box[1]>=0 and box[3]<=self.h*.84,(txt,box)
        self.boxes.append(list(box));d.text(pos,txt,font=f,fill=color,anchor=anchor,stroke_width=max(1,round(2*self.s)),stroke_fill=(2,5,16))
    def points(self,img,pts,t,u,color,spread=1):
        # Perspective rotation and continuous retreat: depth changes the apparent speed.
        angle=.012*t; ca,sa=np.cos(angle),np.sin(angle)
        x=pts[:,0]*ca+pts[:,2]*sa;z=-pts[:,0]*sa+pts[:,2]*ca
        dist=1.15+3.6*smooth(u);den=np.maximum(.25,dist+z*.5)
        xx=self.w*(.47+x/den*.9*spread); yy=self.h*.46+pts[:,1]/den*self.w*.9*spread
        d=ImageDraw.Draw(img)
        for i in np.flatnonzero((xx>0)&(xx<self.w)&(yy>0)&(yy<self.h)):
            bright=.6+.4*np.sin(i*2.17)**2; c=tuple(int(v*bright) for v in color)
            radius=max(.55,self.s*(2.5/den[i]));d.ellipse((xx[i]-radius,yy[i]-radius,xx[i]+radius,yy[i]+radius),fill=c)
    def scene(self,k,t):
        u=(t-CUTS[k])/(CUTS[k+1]-CUTS[k]); im=Image.new('RGB',(self.w,self.h),(2,5,15)); d=ImageDraw.Draw(im)
        self.points(im,self.stars,t,t/70,(115,148,185),2.8)
        cx,cy=self.w*.47,self.h*.46
        if k==0:
            r=self.w*(1.12*np.exp(-4*smooth(u))+.035);n=max(4,int(2*r));earth=self.earth.resize((n,n),Image.Resampling.LANCZOS)
            glow=Image.new('RGB',im.size);gd=ImageDraw.Draw(glow);gd.ellipse((cx-r*1.05,cy-r*1.05,cx+r*1.05,cy+r*1.05),fill=(12,80,155));glow=glow.filter(ImageFilter.GaussianBlur(float(max(1,r*.06))));im=ImageChops.add(im,glow)
            im.paste(earth,(int(cx-r),int(cy-r)),earth)
            if t<2.8:self.text(im,'地球から宇宙の果てへ',.22,54)
        elif k==1:
            scale=np.exp(-2.7*smooth(u));d=ImageDraw.Draw(im)
            for j in range(8,0,-1):
                r=self.w*(.16+j*.24)*scale;d.ellipse((cx-r,cy-r*.36,cx+r,cy+r*.36),outline=(26,49,73),width=max(1,round(self.s)))
                a=j*2.4+t*.1/(j*.4+1); px=cx+r*np.cos(a);py=cy+r*.36*np.sin(a);pr=max(2,self.w*(.006+j*.001)*scale)
                d.ellipse((px-pr,py-pr,px+pr,py+pr),fill=[(100,143,195),(207,165,109),(106,173,220)][j%3])
            r=max(7,self.w*.085*scale);d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=(255,208,117))
            # Earth and Moon visible in the opening solar-system view.
            ex=cx+self.w*.36*scale;ey=cy+self.w*.12*scale;er=max(3,16*self.s*scale)
            d.ellipse((ex-er,ey-er,ex+er,ey+er),fill=(57,151,235));d.ellipse((ex+er*3,ey-er*3,ex+er*4,ey-er*2),fill=(195,200,210))
        else:
            pts=self.clouds[min(k-2,2)];self.points(im,pts,t,u,[(170,195,255),(212,184,244),(107,172,236),(145,185,247)][k-2],1.75 if k==2 else 1.35)
            if k==5:
                d=ImageDraw.Draw(im);r=self.w*(.46-.07*smooth(u))
                d.ellipse((cx-r,cy-r,cx+r,cy+r),outline=(151,197,255),width=max(2,int(3*self.s)))
                self.text(im,'直径 約930億光年',.65,36);self.text(im,'Diameter ≈ 93 billion light-years',.685,26)
        # Optical bloom preserves sharp native-resolution particles underneath.
        small=im.resize((self.w//4,self.h//4)).filter(ImageFilter.GaussianBlur(3)).resize(im.size)
        return ImageChops.add(im,small,scale=1.3)
    def frame(self,t):
        k=min(5,int(np.searchsorted(CUTS,t,side='right')-1));im=self.scene(k,t)
        if k<5 and t>CUTS[k+1]-1.15:
            im=Image.blend(im,self.scene(k+1,t),float(smooth((t-(CUTS[k+1]-1.15))/1.15)))
        self.text(im,'S P A C E   /   0 0 1',.105,26,(140,181,224))
        self.text(im,JP[k],.745,54);self.text(im,EN[k],.787,36,(167,202,238))
        self.text(im,'CG・模式表現 / Not to scale',.825,22,(135,156,181))
        if t>68:im=Image.blend(im,Image.new('RGB',im.size),float(smooth((t-68)/2)))
        return im

def main():
    p=argparse.ArgumentParser();p.add_argument('--preview',action='store_true');p.add_argument('--out',default='output');a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True);w,h=(720,1280) if a.preview else (1080,1920)
    peak=audio(out/'score.wav');r=Renderer(w,h);target=out/('space_001_preview.mp4' if a.preview else 'space_001.mp4')
    cmd=['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{w}x{h}','-r','30','-i','-','-i',str(out/'score.wav'),'-map','0:v','-map','1:a','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-threads','4','-c:a','aac','-b:a','192k','-movflags','+faststart','-t','70',str(target)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for i in range(2100):
            im=r.frame(i/30);proc.stdin.write(im.tobytes())
            if i in [30,240,660,1080,1500,1920]:im.save(out/f'frame_{i:04d}.jpg',quality=92)
            if i%150==0:print(f'{i}/2100 frames',flush=True)
    finally:proc.stdin.close()
    if proc.wait():raise RuntimeError('ffmpeg encoding failed')
    (out/'layout.json').write_text(json.dumps({'subtitle_boxes_checked':len(r.boxes),'safe_area':[.055,0,.89,.84],'audio_source_peak':peak,'resolution':[w,h]}))
    subprocess.run(['python',str(ROOT/'verify.py'),str(target)],check=True)
if __name__=='__main__':main()
