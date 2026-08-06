"""TR1604-Pro Windows CRT simulator V2.

The approved CRT slideshow is the UI specification. All interaction is rendered
inside the simulated CRT, including SD save/recall dialogs. Tkinter is used only
as the host window and keyboard input layer.
"""
from __future__ import annotations

import csv
import json
import math
import random
import tkinter as tk
from dataclasses import asdict, dataclass, field
from pathlib import Path

BG="#020b05"; GREEN="#63ff72"; BRIGHT="#b7ffbe"; DIM="#1d7631"
GRID="#174d25"; YELLOW="#ffe43b"; CYAN="#41e9ff"; RED="#ff6d62"
FONT=("Consolas",11); SMALL=("Consolas",9); TITLE=("Consolas",14,"bold"); BIG=("Consolas",20,"bold")
DATA=Path(__file__).with_name("sdcard"); DATA.mkdir(exist_ok=True)

SCREENS={"F1":"SPECTRUM ANALYZER","F2":"DUPLEX FILTER TUNE","F3":"MEMORY / TRACE COMPARE","F4":"ANTENNA ANALYZER","F5":"MARKER READOUT","F6":"NOTCH ZOOM","F7":"INSERTION LOSS","F8":"SYSTEM SETUP"}
MENUS={
 "SPECTRUM ANALYZER":["TG ON/OFF","TG LEVEL","MARKER SELECT","MARKER FREQUENCY","MARKER TO PEAK","CENTER = MARKER","START / STOP","SPAN","RBW / VBW","TRACE MODE","SAVE TRACE TO SD"],
 "MARKER READOUT":["MARKER SELECT","MARKER ON/OFF","MARKER FREQUENCY","MARKER TO PEAK","NEXT PEAK","DELTA ON/OFF","CENTER = MARKER"],
 "DUPLEX FILTER TUNE":["TG ON/OFF","TG LEVEL","MARKER SELECT","MARKER FREQUENCY","MARKER TO NOTCH","DELTA ON/OFF","NOTCH ZOOM","INSERTION LOSS","PASS/FAIL LIMITS","SAVE PROFILE TO SD","LOAD PROFILE FROM SD","CALIBRATION"],
 "NOTCH ZOOM":["SELECT NOTCH","MARKER FREQUENCY","ZOOM SPAN","RBW / VBW","AUTO TRACK","BACK TO DUPLEX"],
 "INSERTION LOSS":["TG LEVEL","START / STOP","REFERENCE NORMALIZE","LIMIT","AVERAGING","SAVE RESULT TO SD","BACK TO DUPLEX"],
 "MEMORY / TRACE COMPARE":["TG ON/OFF","TG LEVEL","TRACE B ON/OFF","STORE TRACE B","A-B","MAX HOLD","MIN HOLD","AVERAGING","SAVE TRACE TO SD","RECALL TRACE FROM SD"],
 "ANTENNA ANALYZER":["TG ON/OFF","TG LEVEL","MARKER SELECT","MARKER FREQUENCY","MARKER TO MIN SWR","SWR SCALE","SWR LIMIT","BANDWIDTH SWR<LIMIT","RETURN LOSS","OPEN/SHORT/LOAD","SAVE RESULT TO SD"],
 "SYSTEM SETUP":["FREQUENCY SETUP","AMPLITUDE SETUP","SWEEP SETUP","TG LEVEL","DISPLAY INTENSITY","SAVE SETTINGS TO SD","LOAD SETTINGS FROM SD","DIAGNOSTICS","ABOUT"],
}

@dataclass
class Marker:
 enabled: bool=False
 frequency_mhz: float=0.0
 color: str=GREEN

@dataclass
class State:
 screen:str="DUPLEX FILTER TUNE"
 start_mhz:float=429.0; stop_mhz:float=433.0
 ref_dbm:float=-20.0; db_div:float=10.0; rbw_khz:float=30.0; vbw_khz:float=30.0; sweep_ms:float=250.0
 tg_enabled:bool=True; tg_level_dbm:float=-10.0
 selected_marker:int=0
 markers:list[Marker]=field(default_factory=lambda:[Marker(True,430.3625,YELLOW),Marker(True,431.9625,CYAN),Marker(False,431.1625,GREEN),Marker(False,432.5,BRIGHT)])
 menu_open:bool=True; menu_index:int=0; delta:bool=True
 trace_b_on:bool=False; trace_b:list[float]=field(default_factory=list); trace_mode:str="LIVE"; averaging:int=4
 swr_limit:float=2.0; swr_max:float=5.0; reject_limit_db:float=-60.0; insertion_limit_db:float=2.0
 calibrated:bool=False; osl_calibrated:bool=False; normalized:bool=False; status:str="READY"; intensity:int=80
 dialog:str=""; dialog_title:str=""; dialog_value:str=""; dialog_index:int=0; dialog_files:list[str]=field(default_factory=list)
 @property
 def center(self): return (self.start_mhz+self.stop_mhz)/2
 @property
 def span(self): return self.stop_mhz-self.start_mhz

class Simulator:
 def __init__(self):
  self.root=tk.Tk(); self.root.title("TR1604-Pro CRT Simulator V2"); self.root.configure(bg="#111"); self.root.minsize(1180,760)
  self.c=tk.Canvas(self.root,bg="#111",highlightthickness=0); self.c.pack(fill="both",expand=True)
  self.s=State(); self.rng=random.Random(4132)
  self.root.bind("<Key>",self.key); self.root.bind("<Configure>",lambda _e:self.draw()); self.root.after(40,self.draw)
 def set_screen(self,name):
  self.s.screen=name; self.s.menu_index=0
  presets={"SPECTRUM ANALYZER":(140,150,145.425,146.275),"MARKER READOUT":(140,150,145.425,146.275),"DUPLEX FILTER TUNE":(429,433,430.3625,431.9625),"NOTCH ZOOM":(430.15,430.58,430.3625,430.45),"INSERTION LOSS":(429,433,430.3625,431.9625),"MEMORY / TRACE COMPARE":(429,433,430.3625,431.9625),"ANTENNA ANALYZER":(140,150,145.425,147),"SYSTEM SETUP":(140,150,145.425,147)}
  a,b,m1,m2=presets[name]; self.s.start_mhz=a; self.s.stop_mhz=b; self.s.markers[0].frequency_mhz=m1; self.s.markers[1].frequency_mhz=m2; self.s.status=name
 def key(self,e):
  k=e.keysym or ""; ch=e.char if isinstance(e.char,str) else ""
  if self.s.dialog: self.dialog_key(k,ch); self.draw(); return
  if k in SCREENS:self.set_screen(SCREENS[k])
  elif ch in "1234" and ch:self.s.selected_marker=int(ch)-1;self.s.markers[self.s.selected_marker].enabled=True
  elif k in ("Up","Down") and self.s.menu_open:n=len(MENUS[self.s.screen]);self.s.menu_index=(self.s.menu_index+(-1 if k=="Up" else 1))%n
  elif k in ("Left","Right"):
   step=self.s.span/1000; step=step/10 if e.state&1 else step; step=step*10 if e.state&4 else step
   m=self.s.markers[self.s.selected_marker];m.frequency_mhz=max(self.s.start_mhz,min(self.s.stop_mhz,m.frequency_mhz+(-step if k=="Left" else step)))
  elif k=="Return":self.activate()
  elif k=="Escape":self.s.menu_open=False
  elif ch.lower()=="m":self.s.menu_open=not self.s.menu_open
  elif ch.lower()=="g":self.open_value("TG LEVEL","-10.0","tg")
  elif ch.lower()=="t":self.s.tg_enabled=not self.s.tg_enabled
  self.draw()
 def dialog_key(self,k,ch):
  if self.s.dialog=="value":
   if k=="Return":self.commit_value()
   elif k=="Escape":self.close_dialog()
   elif k=="BackSpace":self.s.dialog_value=self.s.dialog_value[:-1]
   elif ch and ch in "0123456789.-":self.s.dialog_value+=ch
  elif self.s.dialog=="files":
   if k in ("Up","Down") and self.s.dialog_files:self.s.dialog_index=(self.s.dialog_index+(-1 if k=="Up" else 1))%len(self.s.dialog_files)
   elif k=="Return":self.commit_file_selection()
   elif k=="Escape":self.close_dialog()
  elif self.s.dialog=="message" and k in ("Return","Escape"):self.close_dialog()
 def close_dialog(self):self.s.dialog="";self.s.dialog_title="";self.s.dialog_value="";self.s.dialog_files=[]
 def open_value(self,title,initial,target):self.s.dialog="value";self.s.dialog_title=title;self.s.dialog_value="";self.value_target=target;self.value_initial=initial
 def open_files(self,title,pattern,action):
  self.s.dialog="files";self.s.dialog_title=title;self.s.dialog_files=sorted(p.name for p in DATA.glob(pattern));self.s.dialog_index=0;self.file_action=action
 def message(self,title,text):self.s.dialog="message";self.s.dialog_title=title;self.s.dialog_value=text
 def commit_value(self):
  try:v=float(self.s.dialog_value)
  except ValueError:self.message("INPUT ERROR","Invalid numeric value");return
  t=self.value_target
  if t=="tg":self.s.tg_level_dbm=max(-60,min(10,v))
  elif t=="marker":self.s.markers[self.s.selected_marker].frequency_mhz=max(self.s.start_mhz,min(self.s.stop_mhz,v))
  elif t=="span":c=self.s.center;self.s.start_mhz=c-v/2;self.s.stop_mhz=c+v/2
  elif t=="rbw":self.s.rbw_khz=max(.1,v)
  elif t=="vbw":self.s.vbw_khz=max(.1,v)
  elif t=="swrmax":self.s.swr_max=max(1.1,v)
  elif t=="swrlimit":self.s.swr_limit=max(1.01,v)
  elif t=="reject":self.s.reject_limit_db=v
  elif t=="insert":self.s.insertion_limit_db=max(0,v)
  self.close_dialog();self.s.status=f"{self.s.dialog_title} SET"
 def commit_file_selection(self):
  if not self.s.dialog_files:self.message("SD CARD","No matching files");return
  name=self.s.dialog_files[self.s.dialog_index]
  if self.file_action=="load_profile":
   d=json.loads((DATA/name).read_text(encoding="utf-8"))
   for k,v in d.items():
    if k=="markers":self.s.markers=[Marker(**m) for m in v]
    elif hasattr(self.s,k):setattr(self.s,k,v)
  elif self.file_action=="load_trace":
   vals=[]
   with (DATA/name).open(newline="",encoding="utf-8") as f:
    for row in csv.DictReader(f):vals.append(float(row["value"]))
   self.s.trace_b=vals;self.s.trace_b_on=True
  self.close_dialog();self.s.status=f"LOADED {name}"
 def save_profile(self,prefix):
  name=f"{prefix}_{len(list(DATA.glob(prefix+'*.json')))+1:03d}.json";(DATA/name).write_text(json.dumps(asdict(self.s),indent=2),encoding="utf-8");self.message("SD CARD",f"SAVED\n{name}\n\nPress ENTER")
 def save_trace(self,prefix):
  name=f"{prefix}_{len(list(DATA.glob(prefix+'*.csv')))+1:03d}.csv";vals=self.trace()
  with (DATA/name).open("w",newline="",encoding="utf-8") as f:
   w=csv.writer(f);w.writerow(["frequency_mhz","value"])
   for i,v in enumerate(vals):w.writerow([self.s.start_mhz+self.s.span*i/(len(vals)-1),v])
  self.message("SD CARD",f"SAVED\n{name}\n{len(vals)} POINTS\n\nPress ENTER")
 def activate(self):
  item=MENUS[self.s.screen][self.s.menu_index]
  if item=="TG ON/OFF":self.s.tg_enabled=not self.s.tg_enabled
  elif item=="TG LEVEL":self.open_value("TG LEVEL",str(self.s.tg_level_dbm),"tg")
  elif item=="MARKER SELECT":self.s.selected_marker=(self.s.selected_marker+1)%4;self.s.markers[self.s.selected_marker].enabled=True
  elif item=="MARKER ON/OFF":self.s.markers[self.s.selected_marker].enabled=not self.s.markers[self.s.selected_marker].enabled
  elif item=="MARKER FREQUENCY":self.open_value("MARKER FREQUENCY",str(self.s.markers[self.s.selected_marker].frequency_mhz),"marker")
  elif "MARKER TO" in item or item=="NEXT PEAK":self.marker_feature()
  elif item=="CENTER = MARKER":sp=self.s.span;c=self.s.markers[self.s.selected_marker].frequency_mhz;self.s.start_mhz=c-sp/2;self.s.stop_mhz=c+sp/2
  elif item in ("SPAN","ZOOM SPAN"):self.open_value("SPAN MHz",str(self.s.span),"span")
  elif item=="RBW / VBW":self.open_value("RBW kHz",str(self.s.rbw_khz),"rbw")
  elif item=="DELTA ON/OFF":self.s.delta=not self.s.delta
  elif item=="NOTCH ZOOM":self.set_screen("NOTCH ZOOM")
  elif item=="INSERTION LOSS":self.set_screen("INSERTION LOSS")
  elif item=="BACK TO DUPLEX":self.set_screen("DUPLEX FILTER TUNE")
  elif item=="TRACE B ON/OFF":self.s.trace_b_on=not self.s.trace_b_on
  elif item=="STORE TRACE B":self.s.trace_b=self.trace();self.s.trace_b_on=True
  elif item in ("A-B","MAX HOLD","MIN HOLD"):self.s.trace_mode=item
  elif item=="AVERAGING":self.s.averaging={1:4,4:8,8:16,16:32,32:1}[self.s.averaging]
  elif "SAVE TRACE TO SD"==item:self.save_trace("TRACE")
  elif "SAVE RESULT TO SD"==item:self.save_trace("RESULT")
  elif item=="RECALL TRACE FROM SD":self.open_files("SD RECALL TRACE","*.csv","load_trace")
  elif item=="SAVE PROFILE TO SD":self.save_profile("PROFILE")
  elif item=="LOAD PROFILE FROM SD":self.open_files("SD LOAD PROFILE","*.json","load_profile")
  elif item=="SAVE SETTINGS TO SD":self.save_profile("SETTINGS")
  elif item=="LOAD SETTINGS FROM SD":self.open_files("SD LOAD SETTINGS","*.json","load_profile")
  elif item=="SWR SCALE":self.open_value("SWR SCALE MAX",str(self.s.swr_max),"swrmax")
  elif item=="SWR LIMIT":self.open_value("SWR LIMIT",str(self.s.swr_limit),"swrlimit")
  elif item=="RETURN LOSS":self.message("RETURN LOSS",f"M{self.s.selected_marker+1} {self.return_loss(self.s.markers[self.s.selected_marker].frequency_mhz):.2f} dB")
  elif item=="BANDWIDTH SWR<LIMIT":self.message("SWR BANDWIDTH",f"SWR < {self.s.swr_limit:.2f}\n{self.swr_bandwidth():.3f} MHz")
  elif item=="OPEN/SHORT/LOAD":self.s.osl_calibrated=True;self.message("OSL CALIBRATION","OPEN  OK\nSHORT OK\nLOAD  OK")
  elif item=="CALIBRATION":self.s.calibrated=True;self.message("CALIBRATION","100 MHz CAL\nLEVEL OK\nFREQUENCY OK")
  elif item=="PASS/FAIL LIMITS":self.open_value("REJECTION LIMIT dB",str(self.s.reject_limit_db),"reject")
  elif item=="REFERENCE NORMALIZE":self.s.normalized=True
  elif item=="LIMIT":self.open_value("INSERTION LIMIT dB",str(self.s.insertion_limit_db),"insert")
  elif item=="ABOUT":self.message("TR1604-PRO","Digital Memory\nTracking Generator\nCRT Overlay Simulator V2")
  elif item=="DIAGNOSTICS":self.message("DIAGNOSTICS","ADC OK\nDAC OK\nTG LOCKED\nSD OK\nBYPASS OK")
  else:self.message(item,"Function active in simulator")
  self.s.status=item
 def marker_feature(self):
  targets=(430.3625,431.9625) if self.s.screen in ("DUPLEX FILTER TUNE","NOTCH ZOOM","INSERTION LOSS","MEMORY / TRACE COMPARE") else ((145.425,) if self.s.screen=="ANTENNA ANALYZER" else (145.425,146.275))
  m=self.s.markers[self.s.selected_marker];m.frequency_mhz=min(targets,key=lambda x:abs(x-m.frequency_mhz))
 def return_loss(self,f):return 4+38/(1+((f-145.425)/.42)**2)
 def swr(self,f):
  g=10**(-self.return_loss(f)/20);return min(self.s.swr_max,(1+g)/max(1e-6,1-g))
 def swr_bandwidth(self):
  fs=[self.s.start_mhz+self.s.span*i/1000 for i in range(1001)];ok=[f for f in fs if self.swr(f)<self.s.swr_limit]
  return max(ok)-min(ok) if ok else 0
 def level(self,f):
  if self.s.screen=="SPECTRUM ANALYZER":return min(-4,-88+67/(1+((f-145.425)/.10)**2)+49/(1+((f-146.275)/.16)**2)+self.rng.uniform(-.5,.5))
  if self.s.screen in ("DUPLEX FILTER TUNE","NOTCH ZOOM","INSERTION LOSS","MEMORY / TRACE COMPARE","MARKER READOUT"):
   v=-17
   for m,d,w in zip(self.s.markers[:2],(70,68),(.055,.065)):v-=d/(1+((f-m.frequency_mhz)/w)**2)
   return max(-110,v+self.rng.uniform(-.2,.2))
  return -self.return_loss(f)
 def trace(self,n=700):return [self.level(self.s.start_mhz+self.s.span*i/(n-1)) for i in range(n)]
 def text(self,x,y,t,color=GREEN,font=FONT,anchor="nw"):self.c.create_text(x,y,text=t,fill=color,font=font,anchor=anchor)
 def draw(self):
  self.c.delete("all");w=max(1180,self.c.winfo_width());h=max(760,self.c.winfo_height());p=22
  self.c.create_rectangle(p,p,w-p,h-p,fill=BG,outline="#2a322d",width=6);x0,y0,x1,y1=p+28,p+24,w-p-28,h-p-24
  if self.s.screen=="SYSTEM SETUP":self.draw_setup(x0,y0,x1,y1)
  else:self.draw_measurement(x0,y0,x1,y1)
  if self.s.dialog:self.draw_dialog(x0,y0,x1,y1)
 def draw_measurement(self,x0,y0,x1,y1):
  mw=290 if self.s.menu_open else 0;pr=x1-mw-(18 if mw else 0);px0=x0+45;py0=y0+120;px1=pr;py1=y1-175
  self.text(x0,y0,f"TR4132N  TR1604-PRO  {self.s.screen}",font=TITLE)
  self.text(x0,y0+32,f"START {self.s.start_mhz:.4f} MHz\nSTOP  {self.s.stop_mhz:.4f} MHz\nSPAN  {self.s.span:.4f} MHz")
  self.text(x0+250,y0+32,f"RBW {self.s.rbw_khz:g} kHz\nVBW {self.s.vbw_khz:g} kHz\nSWP {self.s.sweep_ms:g} ms")
  self.text(pr-210,y0,f"TG {'ON' if self.s.tg_enabled else 'OFF'}  {self.s.tg_level_dbm:.1f} dBm",color=GREEN if self.s.tg_enabled else YELLOW,font=TITLE)
  ant=self.s.screen=="ANTENNA ANALYZER"
  self.c.create_rectangle(px0,py0,px1,py1,outline=GREEN,width=2)
  for i in range(11):
   x=px0+(px1-px0)*i/10;y=py0+(py1-py0)*i/10;self.c.create_line(x,py0,x,py1,fill=GRID,dash=(2,3));self.c.create_line(px0,y,px1,y,fill=GRID,dash=(2,3))
   if ant:self.text(px0-10,y,f"{self.s.swr_max-(self.s.swr_max-1)*i/10:.1f}",anchor="e",font=SMALL)
   else:self.text(px0-10,y,f"{-10*i:>4}",anchor="e",font=SMALL)
  vals=[]
  for i in range(700):
   f=self.s.start_mhz+self.s.span*i/699;v=self.swr(f) if ant else self.level(f);x=px0+(px1-px0)*i/699;y=py0+(py1-py0)*((self.s.swr_max-v)/(self.s.swr_max-1) if ant else (-v)/110);vals.extend((x,y))
  self.c.create_line(*vals,fill=GREEN,width=2)
  for i,m in enumerate(self.s.markers):
   if not m.enabled:continue
   x=px0+(px1-px0)*(m.frequency_mhz-self.s.start_mhz)/self.s.span;v=self.swr(m.frequency_mhz) if ant else self.level(m.frequency_mhz);y=py0+(py1-py0)*((self.s.swr_max-v)/(self.s.swr_max-1) if ant else (-v)/110)
   self.c.create_line(x,py0,x,py1,fill=m.color,dash=(5,4));self.c.create_polygon(x,y,x-7,y-13,x+7,y-13,fill=m.color);self.text(x,y+8,str(i+1),m.color,anchor="n")
  self.text(px0,py1+10,f"START {self.s.start_mhz:.4f} MHz");self.text((px0+px1)/2,py1+10,f"CENTER {self.s.center:.4f} MHz",anchor="n");self.text(px1,py1+10,f"STOP {self.s.stop_mhz:.4f} MHz",anchor="ne")
  by=py1+60;bw=(px1-px0)/4
  for i in range(4):self.c.create_rectangle(px0+i*bw,by,px0+(i+1)*bw,y1-35,outline=DIM)
  if ant:
   m=self.s.markers[self.s.selected_marker];self.text(px0+12,by+10,f"MKR {self.s.selected_marker+1}\n{m.frequency_mhz:.4f} MHz\nSWR {self.swr(m.frequency_mhz):.2f}",YELLOW);self.text(px0+bw+12,by+10,f"RETURN LOSS\n{self.return_loss(m.frequency_mhz):.2f} dB\nOSL {'OK' if self.s.osl_calibrated else '---'}");self.text(px0+2*bw+12,by+10,f"RESONANCE\n145.4250 MHz\nMIN SWR {self.swr(145.425):.2f}");self.text(px0+3*bw+12,by+10,f"BANDWIDTH\nSWR < {self.s.swr_limit:.2f}\n{self.swr_bandwidth():.3f} MHz")
  else:
   for i,m in enumerate(self.s.markers[:2]):self.text(px0+i*bw+12,by+10,f"MKR {i+1}\n{m.frequency_mhz:.4f} MHz\n{self.level(m.frequency_mhz):.2f} dB",m.color)
   self.text(px0+2*bw+12,by+10,f"DELTA\n{self.s.markers[1].frequency_mhz-self.s.markers[0].frequency_mhz:.4f} MHz\nTRACE {self.s.trace_mode}");self.text(px0+3*bw+12,by+10,f"TG LEVEL\n{self.s.tg_level_dbm:.1f} dBm\nCAL {'OK' if self.s.calibrated else '---'}")
  self.text(px0,y1-22,f"{self.s.status}   |   F1 SPECTRUM F2 DUPLEX F3 MEMORY F4 ANTENNA F5 MARKER F6 ZOOM F7 LOSS F8 SETUP",font=SMALL)
  if self.s.menu_open:self.draw_menu(pr+18,y0+34,x1,y1)
 def draw_menu(self,x,y,x1,y1):
  self.c.create_line(x-10,y-8,x-10,y1,fill=GREEN);self.text(x,y,self.s.screen,font=TITLE)
  yy=y+38
  for i,item in enumerate(MENUS[self.s.screen]):
   if i==self.s.menu_index:self.c.create_rectangle(x-4,yy-2,x1-6,yy+19,outline=GREEN);self.text(x+4,yy,"> "+item,BRIGHT,font=SMALL)
   else:self.text(x+4,yy,"  "+item,font=SMALL)
   yy+=24
 def draw_setup(self,x0,y0,x1,y1):
  self.text(x0,y0,"TR1604-PRO SYSTEM SETUP",font=BIG);self.text(x0,y0+55,f"TG LEVEL        {self.s.tg_level_dbm:.1f} dBm\nRBW / VBW       {self.s.rbw_khz:g} / {self.s.vbw_khz:g} kHz\nDISPLAY         {self.s.intensity}%\nCALIBRATION     {'OK' if self.s.calibrated else 'NOT RUN'}\nOSL CAL          {'OK' if self.s.osl_calibrated else 'NOT RUN'}\nSD CARD          READY\nFILES            {len(list(DATA.iterdir()))}")
  self.draw_menu(x1-330,y0+25,x1,y1);self.text(x0,y1-25,"UP/DOWN SELECT  ENTER OPEN  ESC CLOSE  F1-F8 SCREEN",font=SMALL)
 def draw_dialog(self,x0,y0,x1,y1):
  w=560;h=330;cx=(x0+x1)/2;cy=(y0+y1)/2;xa=cx-w/2;ya=cy-h/2
  self.c.create_rectangle(xa,ya,xa+w,ya+h,fill=BG,outline=BRIGHT,width=3);self.text(xa+20,ya+18,self.s.dialog_title,font=BIG)
  if self.s.dialog=="value":self.text(xa+30,ya+100,f"VALUE: {self.s.dialog_value}_",font=BIG);self.text(xa+30,ya+h-50,"TYPE VALUE   ENTER ACCEPT   ESC CANCEL",font=SMALL)
  elif self.s.dialog=="message":self.text(xa+35,ya+95,self.s.dialog_value,font=TITLE);self.text(xa+35,ya+h-45,"ENTER / ESC CLOSE",font=SMALL)
  else:
   self.text(xa+25,ya+65,"SD CARD FILES",font=TITLE);yy=ya+100
   if not self.s.dialog_files:self.text(xa+35,yy,"<NO FILES>",YELLOW)
   for i,name in enumerate(self.s.dialog_files[:8]):
    self.text(xa+35,yy+(i*25),("> " if i==self.s.dialog_index else "  ")+name,BRIGHT if i==self.s.dialog_index else GREEN)
   self.text(xa+25,ya+h-40,"UP/DOWN SELECT   ENTER LOAD   ESC CANCEL",font=SMALL)
 def run(self):self.root.mainloop()

if __name__=="__main__":Simulator().run()
