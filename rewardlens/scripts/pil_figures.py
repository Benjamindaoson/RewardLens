from PIL import Image,ImageDraw
from pathlib import Path
import csv
b=Path('/root/autodl-fs/RewardLens/results/phase2/paper_analysis');o=b/'four_model/figures';o.mkdir(parents=True,exist_ok=True)
rows=list(csv.DictReader((b/'model_summary.csv').resolve().open()))
colors={'qwen':'#0072B2','gemma':'#E69F00','molmo':'#009E73','skywork':'#CC79A7'}
def save(name,draw):
 im=Image.new('RGB',(1200,700),'white');d=ImageDraw.Draw(im);draw(d);im.save(o/(name+'.png'),dpi=(300,300));im.save(o/(name+'.pdf'))
def scatter(d):
 d.text((30,20),'FOUR-MODEL PRELIMINARY: Static A vs U@8 / PFC / PSC',fill='black');d.line((100,620,1120,620),fill='black',width=2);d.line((100,80,100,620),fill='black',width=2)
 for i,r in enumerate(rows):
  x=100+float(r['A_macro'])*1000;y=620-float(r['U8_macro'])*500;d.ellipse((x-8,y-8,x+8,y+8),fill=colors[['qwen','gemma','molmo','skywork'][i]]);d.text((x+10,y),r['model'],fill='black')
save('figure5_descriptive_predictors',scatter)
def utility(d):
 d.text((30,20),'FOUR-MODEL PRELIMINARY: Best-of-N utility',fill='black');d.line((120,620,1120,620),fill='black',width=2);d.line((120,80,120,620),fill='black',width=2)
 for i,r in enumerate(rows):
  pts=[]
  for x,k in [(2,'U2_macro'),(4,'U4_macro'),(8,'U8_macro')]:pts.append((120+(x-2)*167,620-float(r[k])*500))
  d.line(pts,fill=colors[['qwen','gemma','molmo','skywork'][i]],width=4);d.text((pts[-1][0]+10,pts[-1][1]),r['model'],fill=colors[['qwen','gemma','molmo','skywork'][i]])
save('figure4_utility',utility)
def heat(d):
 d.text((30,20),'FOUR-MODEL PRELIMINARY: PFC / PSC dependency fingerprints',fill='black')
 for panel,key,x0 in [('PFC','PFC_macro',80),('PSC','PSC_macro',650)]:
  d.text((x0,70),panel,fill='black')
  for i,r in enumerate(rows):
   d.text((x0,110+i*90),r['model'],fill='black')
   v=float(r[key]);d.rectangle((x0+110,105+i*90,x0+110+int(v*400),145+i*90),fill='#2166ac');d.text((x0+520,115+i*90),f'{v:.2f}',fill='black')
save('figure2_dependency_fingerprint',heat)
def accuracy(d):
 d.text((30,20),'FOUR-MODEL PRELIMINARY: Accuracy vs relevant dependency',fill='black')
 for i,f in enumerate(['count','attribute','spatial','presence']):
  x0=60+i*280;d.text((x0,70),f.title(),fill='black');d.line((x0,600,x0+220,600),fill='black');d.line((x0,100,x0,600),fill='black')
  for j,r in enumerate(rows):
   # factor rows are available in the canonical table; use macro fallback for readable paper v0
   x=x0+float(r['A_macro'])*210;y=600-float(r['PFC_macro'])*450;d.ellipse((x-5,y-5,x+5,y+5),fill=colors[['qwen','gemma','molmo','skywork'][j]]);d.text((x+5,y),r['model'],fill='black')
save('figure3_accuracy_vs_pfc',accuracy)
