from __future__ import annotations
import math, random, time, tkinter as tk
from dataclasses import dataclass, field
from pathlib import Path

FW="4.0.0"; BUILD="desktop-v6-001"
BG="#020b05"; G="#63ff72"; BR="#b7ffbe"; D="#1d7631"; GRID="#174d25"; Y="#ffe43b"; C="#41e9ff"
SM=("Consolas",9); FN=("Consolas",11); TI=("Consolas",14,"bold"); BIG=("Consolas",28,"bold")
DATA=Path(__file__).with_name("sdcard"); DATA.mkdir(exist_ok=True)
SCREENS={"F1":"SPECTRUM ANALYZER","F2":"DUPLEX FILTER TUNE","F3":"MEMORY / TRACE COMPARE","F4":"ANTENNA ANALYZER","F5":"MARKER READOUT","F6":"NOTCH ZOOM","F7":"INSERTION LOSS","F8":"SYSTEM SETUP"}
MENUS={
"SPECTRUM ANALYZER":["TG ON/OFF","TG LEVEL","MARKER SELECT","MARKER ON/OFF","MARKER FREQUENCY","MARKER TO PEAK","CENTER = MARKER","START","STOP","SPAN","RBW","VBW","STORE MEMORY TRACE","MEMORY OVERLAY ON/OFF"],
"DUPLEX FILTER TUNE":["TG ON/OFF","TG LEVEL","MARKER SELECT","MARKER ON/OFF","MARKER FREQUENCY","MARKER TO NOTCH","DELTA ON/OFF","SELECT NOTCH","NOTCH ZOOM","AUTO TRACK","RBW","VBW","INSERTION LOSS","STORE MEMORY TRACE","MEMORY OVERLAY ON/OFF","CALIBRATION"],
"MEMORY / TRACE COMPARE":["STORE MEMORY TRACE","MEMORY OVERLAY ON/OFF","AVERAGING","RBW","VBW"],
"ANTENNA ANALYZER":["TG ON/OFF","TG LEVEL","MARKER SELECT","MARKER ON/OFF","MARKER FREQUENCY","MARKER TO MIN SWR","SWR SCALE","SWR LIMIT","RETURN LOSS","OPEN/SHORT/LOAD","RBW","VBW","STORE MEMORY TRACE","MEMORY OVERLAY ON/OFF"],
"MARKER READOUT":["MARKER SELECT","MARKER ON/OFF","MARKER FREQUENCY","DELTA ON/OFF","CENTER = MARKER"],
"NOTCH ZOOM":["SELECT NOTCH","MARKER FREQUENCY","MARKER TO NOTCH","ZOOM SPAN","RBW","VBW","AUTO TRACK","BACK TO DUPLEX"],
"INSERTION LOSS":["TG LEVEL","START","STOP","RBW","VBW","AVERAGING","BACK TO DUPLEX"],
"SYSTEM SETUP":["TG LEVEL","DISPLAY INTENSITY","DIAGNOSTICS","SERVICE INFORMATION","ABOUT"]}

@dataclass
class Marker: enabled:bool=False; f:float=0.0
@dataclass
class State:
 screen:str="DUPLEX FILTER TUNE"; start:float=429.0; stop:float=433.0; rbw:float=30.0; vbw:float=30.0; sweep:float=250.0
 tg:bool=True; tgl:float=-10.0; markers:list[Marker]=field(default_factory=lambda:[Marker(True,430.3625),Marker(True,431.9625),Marker(False,431.2),Marker(False,432.4)])
 selected:int=0; delta:bool=True; auto_track:bool=False; swrmax:float=5.0; swrlim:float=2.0; averaging:int=4; menu:int=0; status:str="READY"; cal:bool=False; osl:bool=False
 @property
 def center(self): return (self.start+self.stop)/2
 @property
 def span(self): return self.stop-self.start

class App:
 def __init__(self):
  self.root=tk.Tk(); self.root.title("TR1604-Pro Desktop Display V6"); self.root.configure(bg="#111"); self.root.minsize(1180,760)
  self.c=tk.Canvas(self.root,bg="#111",highlightthickness=0); self.c.pack(fill="both",expand=True)
  self.s=State(); self.rng=random.Random(4132); self.mem=[]; self.mem_kind="DB"; self.mem_on=False
  self.dialog=None; self.startup=True; self.t0=time.monotonic()
  self.root.bind("<Key>",self.key); self.root.bind("<Configure>",lambda e:self.draw()); self.root.after(80,self.tick)
 def tick(self):
  if self.startup and time.monotonic()-self.t0>=3.8: self.startup=False; self.s.status="SELF TEST PASS - READY"
  if self.s.auto_track and not self.startup and self.s.screen in ("DUPLEX FILTER TUNE","NOTCH ZOOM"): self.track_notch()
  self.draw(); self.root.after(80,self.tick)
 def txt(self,x,y,t,col=G,font=FN,anchor="nw"): self.c.create_text(x,y,text=t,fill=col,font=font,anchor=anchor)
 def key(self,e):
  k=e.keysym or ""; ch=e.char.lower() if isinstance(e.char,str) and e.char else ""
  if self.startup:
   if k in ("Return","space"): self.t0=time.monotonic()-4
   return
  if self.dialog: self.dialog_key(k,ch); return
  if k in SCREENS: self.set_screen(SCREENS[k]); return
  if ch and ch in "1234": self.s.selected=int(ch)-1; self.s.status=f"MARKER {ch} SELECTED"; return
  if ch=="x": self.s.markers[self.s.selected].enabled=not self.s.markers[self.s.selected].enabled; return
  if k in ("Up","Down"): self.s.menu=(self.s.menu+(-1 if k=="Up" else 1))%len(MENUS[self.s.screen]); return
  if k=="Return": self.activate(); return
  if k in ("Left","Right"):
   self.s.auto_track=False; m=self.s.markers[self.s.selected]; step=self.s.span/1000
   if e.state&1: step/=10
   if e.state&4: step*=10
   m.f=max(self.s.start,min(self.s.stop,m.f+(-step if k=="Left" else step)))
 def set_screen(self,name):
  self.s.screen=name; self.s.menu=0
  p={"SPECTRUM ANALYZER":(140,150,145.425,146.195),"DUPLEX FILTER TUNE":(429,433,430.3625,431.9625),"MEMORY / TRACE COMPARE":(429,433,430.3625,431.9625),"ANTENNA ANALYZER":(140,150,145.425,147.0),"MARKER READOUT":(140,150,145.425,146.195),"NOTCH ZOOM":(430.15,430.58,430.3625,430.45),"INSERTION LOSS":(429,433,430.3625,431.9625)}
  if name in p:
   a,b,m1,m2=p[name]; self.s.start=a; self.s.stop=b; self.s.markers[0].f=m1; self.s.markers[1].f=m2
 def valdlg(self,title,target): self.dialog={"type":"value","title":title,"target":target,"value":""}
 def msg(self,title,text): self.dialog={"type":"msg","title":title,"text":text}
 def dialog_key(self,k,ch):
  d=self.dialog
  if d["type"]=="msg":
   if k in ("Return","Escape"): self.dialog=None
   return
  if k=="Escape": self.dialog=None; return
  if k=="BackSpace": d["value"]=d["value"][:-1]; return
  if k=="Return":
   try:v=float(d["value"])
   except: self.msg("INPUT ERROR","INVALID NUMBER"); return
   t=d["target"]
   if t=="tgl": self.s.tgl=max(-60,min(10,v))
   elif t=="mf": self.s.markers[self.s.selected].f=max(self.s.start,min(self.s.stop,v))
   elif t=="start" and v<self.s.stop: self.s.start=v
   elif t=="stop" and v>self.s.start: self.s.stop=v
   elif t=="span" and v>0: c=self.s.center; self.s.start=c-v/2; self.s.stop=c+v/2
   elif t=="rbw" and v>0: self.s.rbw=v
   elif t=="vbw" and v>0: self.s.vbw=v
   elif t=="swrmax": self.s.swrmax=max(1.1,v)
   elif t=="swrlim": self.s.swrlim=max(1.01,v)
   self.s.status=f"{d['title']} SET"; self.dialog=None; return
  if ch and ch in "0123456789.-": d["value"]+=ch
 def activate(self):
  it=MENUS[self.s.screen][self.s.menu]
  if it=="TG ON/OFF": self.s.tg=not self.s.tg
  elif it=="TG LEVEL": self.valdlg("TG LEVEL dBm","tgl")
  elif it=="MARKER SELECT": self.s.selected=(self.s.selected+1)%4
  elif it=="MARKER ON/OFF": self.s.markers[self.s.selected].enabled=not self.s.markers[self.s.selected].enabled
  elif it=="MARKER FREQUENCY": self.valdlg("MARKER FREQUENCY MHz","mf")
  elif it in ("MARKER TO NOTCH","SELECT NOTCH"): self.select_notch()
  elif it=="MARKER TO PEAK": self.s.markers[self.s.selected].f=145.425
  elif it=="MARKER TO MIN SWR": self.s.markers[self.s.selected].f=145.425
  elif it=="CENTER = MARKER": sp=self.s.span; c=self.s.markers[self.s.selected].f; self.s.start=c-sp/2; self.s.stop=c+sp/2
  elif it=="DELTA ON/OFF": self.s.delta=not self.s.delta; self.s.status=f"DELTA {'ON' if self.s.delta else 'OFF'}"
  elif it=="AUTO TRACK": self.s.auto_track=not self.s.auto_track; self.s.status=f"AUTO TRACK {'ON' if self.s.auto_track else 'OFF'}"
  elif it=="NOTCH ZOOM": self.set_screen("NOTCH ZOOM")
  elif it=="INSERTION LOSS": self.set_screen("INSERTION LOSS")
  elif it=="BACK TO DUPLEX": self.set_screen("DUPLEX FILTER TUNE")
  elif it in ("SPAN","ZOOM SPAN"): self.valdlg("SPAN MHz","span")
  elif it=="START": self.valdlg("START MHz","start")
  elif it=="STOP": self.valdlg("STOP MHz","stop")
  elif it=="RBW": self.valdlg("RBW kHz","rbw")
  elif it=="VBW": self.valdlg("VBW kHz","vbw")
  elif it=="STORE MEMORY TRACE": self.store_mem()
  elif it=="MEMORY OVERLAY ON/OFF": self.mem_on=bool(self.mem) and not self.mem_on
  elif it=="AVERAGING": self.s.averaging={1:4,4:8,8:16,16:32,32:1}[self.s.averaging]
  elif it=="SWR SCALE": self.valdlg("SWR SCALE MAX","swrmax")
  elif it=="SWR LIMIT": self.valdlg("SWR LIMIT","swrlim")
  elif it=="RETURN LOSS": self.msg("RETURN LOSS",f"{self.return_loss(self.s.markers[self.s.selected].f):.2f} dB")
  elif it=="OPEN/SHORT/LOAD": self.s.osl=True; self.msg("OSL CALIBRATION","OPEN  OK\nSHORT OK\nLOAD  OK")
  elif it=="CALIBRATION": self.s.cal=True; self.msg("CALIBRATION","LEVEL OK\nFREQUENCY OK")
  elif it=="DIAGNOSTICS": self.msg("DIAGNOSTICS","ADC OK\nDAC OK\nTG LOCKED\nSD OK\nBYPASS OK")
  elif it=="SERVICE INFORMATION": self.msg("SERVICE INFORMATION",f"FW {FW}\nBUILD {BUILD}\nRBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\nAUTO TRACK {'ON' if self.s.auto_track else 'OFF'}")
  elif it=="ABOUT": self.msg("TR1604-PRO",f"Firmware {FW}\nClean V6 renderer\nDigital Memory\nTracking Generator\nCRT Overlay")
  else: self.s.status=it
 def select_notch(self):
  self.s.selected=1 if self.s.selected==0 else 0; self.s.markers[self.s.selected].enabled=True; self.track_notch(); self.s.status=f"NOTCH {self.s.selected+1} SELECTED"
 def track_notch(self):
  target=430.3625 if self.s.selected==0 else 431.9625; self.s.markers[self.s.selected].f=target
  if self.s.screen=="NOTCH ZOOM": sp=self.s.span; self.s.start=target-sp/2; self.s.stop=target+sp/2
 def level(self,f):
  if self.s.screen=="SPECTRUM ANALYZER": return min(-4,-88+67/(1+((f-145.425)/.10)**2)+48/(1+((f-146.195)/.15)**2)+self.rng.uniform(-.3,.3))
  if self.s.screen in ("DUPLEX FILTER TUNE","NOTCH ZOOM","INSERTION LOSS","MEMORY / TRACE COMPARE"):
   return max(-110,-16-70/(1+((f-430.3625)/.055)**2)-68/(1+((f-431.9625)/.065)**2)+self.rng.uniform(-.15,.15))
  return -self.return_loss(f)
 def swr(self,f): return 1.04+3.7*(1-math.exp(-((f-145.425)/1.0)**2))
 def return_loss(self,f):
  q=(self.swr(f)-1)/(self.swr(f)+1); return 80 if q<=0 else -20*math.log10(q)
 def store_mem(self): self.mem=[self.swr(self.s.start+self.s.span*i/699) if self.s.screen=="ANTENNA ANALYZER" else self.level(self.s.start+self.s.span*i/699) for i in range(700)]; self.mem_kind="SWR" if self.s.screen=="ANTENNA ANALYZER" else "DB"; self.mem_on=True; self.s.status="MEMORY B STORED"
 def draw(self):
  self.c.delete("all"); w=max(1180,self.c.winfo_width()); h=max(760,self.c.winfo_height()); self.c.create_rectangle(20,20,w-20,h-20,fill=BG,outline="#2a322d",width=6)
  if self.startup: self.draw_startup(w,h); return
  if self.s.screen=="SYSTEM SETUP": self.draw_setup(w,h)
  else: self.draw_measure(w,h)
  if self.dialog: self.draw_dialog(w,h)
 def draw_startup(self,w,h):
  p=min(1,(time.monotonic()-self.t0)/3.8); self.txt(w/2,120,"TAKEDA RIKEN",G,BIG,"center"); self.txt(w/2,180,"TR1604-PRO",BR,("Consolas",38,"bold"),"center"); self.txt(w/2,230,"DIGITAL MEMORY & TRACKING GENERATOR",G,TI,"center")
  steps=["CPU / SDRAM","AD7616 ADC","VECTOR DAC / CRT","TRACKING GENERATOR","SD STORAGE","FAIL-SAFE BYPASS"]
  for i,s in enumerate(steps): self.txt(w/2-250,310+i*40,s); self.txt(w/2+250,310+i*40,"OK" if p>(i+1)/6 else "TEST" if p>i/6 else "--",G if p>(i+1)/6 else Y,TI,"e")
 def draw_measure(self,w,h):
  x0=55; y0=50; x1=w-55; y1=h-50; menu_w=300; pr=x1-menu_w-18; px0=x0+48; py0=y0+120; px1=pr; py1=y1-230
  self.txt(x0,y0,f"TR4132N / TR1604-PRO     {self.s.screen}",G,TI); self.txt(x0,y0+32,f"CENTER {self.s.center:.4f} MHz\nSPAN   {self.s.span:.4f} MHz"); self.txt(x0+250,y0+32,f"RBW {self.s.rbw:g} kHz\nVBW {self.s.vbw:g} kHz\nSWP {self.s.sweep:g} ms"); self.txt(pr-210,y0,f"TG {'ON' if self.s.tg else 'OFF'}  {self.s.tgl:.1f} dBm",G if self.s.tg else Y,TI)
  self.c.create_rectangle(px0,py0,px1,py1,outline=G,width=2)
  ant=self.s.screen=="ANTENNA ANALYZER"
  for i in range(11):
   xx=px0+(px1-px0)*i/10; yy=py0+(py1-py0)*i/10; self.c.create_line(xx,py0,xx,py1,fill=GRID,dash=(2,3)); self.c.create_line(px0,yy,px1,yy,fill=GRID,dash=(2,3))
  pts=[]
  for i in range(700):
   f=self.s.start+self.s.span*i/699; v=self.swr(f) if ant else self.level(f); xx=px0+(px1-px0)*i/699; yy=py0+(py1-py0)*((self.s.swrmax-v)/(self.s.swrmax-1) if ant else (-v)/110); pts.extend((xx,yy))
  self.c.create_line(*pts,fill=G,width=2)
  if self.mem_on and self.mem:
   for i in range(0,699,4):
    j=min(i+2,699); va=self.mem[i]; vb=self.mem[j]; ya=py0+(py1-py0)*((self.s.swrmax-va)/(self.s.swrmax-1) if ant and self.mem_kind=="SWR" else (-va)/110); yb=py0+(py1-py0)*((self.s.swrmax-vb)/(self.s.swrmax-1) if ant and self.mem_kind=="SWR" else (-vb)/110); xa=px0+(px1-px0)*i/699; xb=px0+(px1-px0)*j/699; self.c.create_line(xa,ya,xb,yb,fill=Y,width=2)
  cols=(Y,C,G,BR)
  for i,m in enumerate(self.s.markers):
   if not m.enabled: continue
   xx=px0+(px1-px0)*(m.f-self.s.start)/self.s.span; v=self.swr(m.f) if ant else self.level(m.f); yy=py0+(py1-py0)*((self.s.swrmax-v)/(self.s.swrmax-1) if ant else (-v)/110); self.c.create_line(xx,py0,xx,py1,fill=cols[i],dash=(5,4)); self.txt(xx,yy-16,str(i+1),cols[i],TI,"center")
  self.txt(px0,py1+8,f"START {self.s.start:.4f} MHz"); self.txt((px0+px1)/2,py1+8,f"CENTER {self.s.center:.4f} MHz",G,FN,"n"); self.txt(px1,py1+8,f"STOP {self.s.stop:.4f} MHz",G,FN,"ne")
  by=py1+48; bh=82; bw=(px1-px0)/4
  for i,m in enumerate(self.s.markers):
   xa=px0+i*bw; xb=xa+bw; self.c.create_rectangle(xa,by,xb,by+bh,outline=BR if i==self.s.selected else D,width=2 if i==self.s.selected else 1); val=(f"SWR {self.swr(m.f):.2f}" if ant else f"{self.level(m.f):.2f} dB") if m.enabled else "OFF"; self.txt(xa+8,by+8,f"M{i+1} {'ON' if m.enabled else 'OFF'}\n{m.f:.4f} MHz\n{val}",cols[i] if m.enabled else D,SM)
  sy=by+bh+10; active=[m for m in self.s.markers if m.enabled]
  delta="DELTA OFF"
  if self.s.delta and len(active)>=2:
   a,b=active[0],active[1]; da=(self.swr(b.f)-self.swr(a.f)) if ant else (self.level(b.f)-self.level(a.f)); delta=f"DELTA ON  dF {b.f-a.f:.6f} MHz  dA {da:+.2f}{' SWR' if ant else ' dB'}"
  self.txt(px0,sy,f"TRACE A LIVE   MEM B {'ON' if self.mem_on else 'OFF'}   {delta}   AUTO {'ON' if self.s.auto_track else 'OFF'}",Y if self.s.delta else D,SM)
  self.txt(px0,y1-18,"F1 SPECTRUM  F2 DUPLEX  F3 MEMORY  F4 ANTENNA  F5 MARKER  F6 ZOOM  F7 LOSS  F8 SETUP",G,SM)
  mx=pr+18; self.c.create_line(mx-10,y0+20,mx-10,y1,fill=G); self.txt(mx,y0+25,self.s.screen,G,TI); yy=y0+60
  for i,it in enumerate(MENUS[self.s.screen]):
   if i==self.s.menu: self.c.create_rectangle(mx-4,yy-2,x1-5,yy+19,outline=G); self.txt(mx+4,yy,"> "+it,BR,SM)
   else:self.txt(mx+4,yy,"  "+it,G,SM)
   yy+=24
 def draw_setup(self,w,h):
  x0=65; y0=60; x1=w-65; y1=h-60; self.txt(x0,y0,"TR1604-PRO SYSTEM SETUP",BR,BIG); self.txt(x0,y0+70,f"FIRMWARE       {FW}\nBUILD          {BUILD}\nTG LEVEL       {self.s.tgl:.1f} dBm\nRBW            {self.s.rbw:g} kHz\nVBW            {self.s.vbw:g} kHz\nAUTO TRACK     {'ON' if self.s.auto_track else 'OFF'}\nMEMORY B       {'ON' if self.mem_on else 'OFF'}")
  mx=x1-330; self.txt(mx,y0+25,"SYSTEM SETUP",G,TI); yy=y0+65
  for i,it in enumerate(MENUS["SYSTEM SETUP"]): self.txt(mx,yy,("> " if i==self.s.menu else "  ")+it,BR if i==self.s.menu else G,SM); yy+=28
  self.txt(x0,y1-20,"UP/DOWN SELECT   ENTER OPEN   F1-F8 SCREEN",D,SM)
 def draw_dialog(self,w,h):
  d=self.dialog; xa=w/2-280; ya=h/2-165; self.c.create_rectangle(xa,ya,xa+560,ya+330,fill=BG,outline=BR,width=3); self.txt(xa+20,ya+20,d["title"],BR,TI)
  if d["type"]=="value": self.txt(xa+30,ya+110,"VALUE: "+d["value"]+"_",G,("Consolas",20,"bold")); self.txt(xa+30,ya+275,"TYPE VALUE   ENTER ACCEPT   ESC CANCEL",D,SM)
  else: self.txt(xa+35,ya+90,d["text"],G,TI); self.txt(xa+35,ya+275,"ENTER / ESC CLOSE",D,SM)
 def run(self): self.root.mainloop()

if __name__=="__main__": App().run()
