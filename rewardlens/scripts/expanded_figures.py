"""Self-contained vector figures and source CSVs; no plotting dependency."""
import html
import math
from scripts.phase2_report import text_once,csv_text
from stats import FACTORS
COLORS=("#0072B2","#D55E00","#009E73","#CC79A7","#E69F00","#56B4E9","#000000","#999933")
LABELS=("Qwen3-VL","Gemma3","Molmo","Skywork","Idefics3","Phi3.5-V","InternVL3","LLaVA-OV")

MARKERS=(
    '<circle cx="0" cy="0" r="6"/>',
    '<rect x="-5" y="-5" width="10" height="10"/>',
    '<path d="M0 -7L7 6H-7Z"/>',
    '<path d="M0 7L7 -6H-7Z"/>',
    '<path d="M0 -7L7 0L0 7L-7 0Z"/>',
    '<path d="M-2 -6H2V-2H6V2H2V6H-2V2H-6V-2H-2Z"/>',
    '<path d="M-2 -6H2V-2H6V2H2V6H-2V2H-6V-2H-2Z" transform="rotate(45)"/>',
    '<path d="M-7 0L-3.5 -6H3.5L7 0L3.5 6H-3.5Z"/>',
)

def marker(x,y,index,label):
    return f'<g transform="translate({x} {y})" fill="{COLORS[index]}" stroke="#222" stroke-width="1"><title>{html.escape(label)}</title>{MARKERS[index]}</g>'

def start(title,width=1200,height=1000):
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img">',
            f'<title>{html.escape(title)}</title><desc>Exact source values are in the same-named CSV. N/A is not zero.</desc>',
            '<rect width="100%" height="100%" fill="white"/>',
            '<style>text{font-family:Arial,Helvetica,sans-serif;fill:#222;font-size:16px}.title{font-size:23px;font-weight:bold}.small{font-size:12px}</style>',
            f'<text x="40" y="35" class="title">{html.escape(title)}</text>']

def save(path,parts):
    text_once(path,"".join(parts)+"</svg>")

def scatter(out,table,models,key):
    parts=start(key+" versus downstream U@8")
    ids=[r["model_id"] for r in models]
    for idx,factor in enumerate(FACTORS):
        x=85+(idx%2)*570;y=85+(idx//2)*365
        parts.append(f'<text x="{x}" y="{y}">{factor.title()}</text>')
        for step in range(6):
            tick=step/5
            xx=x+420*tick;yy=y+275-235*tick
            parts.extend([f'<path d="M{xx} {y+40}V{y+275} M{x} {yy}H{x+420}" stroke="#ddd" fill="none"/>',
                f'<text class="small" x="{xx-8}" y="{y+297}">{tick:.1f}</text>',
                f'<text class="small" x="{x-35}" y="{yy+5}">{tick:.1f}</text>'])
        parts.append(f'<text x="{x+190}" y="{y+323}">{key}</text><text x="{x-55}" y="{y+157.5}" text-anchor="middle" transform="rotate(-90 {x-55} {y+157.5})">U@8</text>')
        for row in table:
            if row["factor"]!=factor or row.get(key) is None:continue
            i=ids.index(row["model_id"])
            parts.append(marker(x+420*row[key],y+275-235*row["U8"],i,row["model_id"]))
    for i,model in enumerate(ids):
        x=40+(i%4)*285;y=855+(i//4)*45
        parts.append(marker(x,y-5,i,LABELS[i])+f'<text x="{x+15}" y="{y}">{LABELS[i]}</text>')
    save(out/(key+"_vs_U8.svg"),parts)
    text_once(out/(key+"_vs_U8.csv"),csv_text(table,["model_id","family","factor",key,"U8"]))

def figures(out,table,models,rq2,rq3,matched):
    for key in ("A","PFC","PSC"):scatter(out,table,models,key)
    cells=rq3["matrix"]
    summary=rq3["primary_4factor"]
    grid=summary["column_standardized_matrix"] if summary else None
    parts=start("RQ3: within-column standardized incremental prediction",1100,820)
    for j,f in enumerate(FACTORS):
        parts.append(f'<text x="{260+j*190}" y="105">{f.title()}</text>')
    for i,af in enumerate(FACTORS):
        parts.append(f'<text x="40" y="{200+i*130}">{af.title()}</text>')
        for j,df in enumerate(FACTORS):
            value=grid[af][df] if grid else None
            shade="#eee" if value is None else "#0072B2" if value>=0 else "#D55E00"
            opacity=0.12 if value is None else min(0.9,0.15+abs(value)*0.3)
            x=230+j*190;y=130+i*130
            parts.append(f'<rect x="{x}" y="{y}" width="180" height="120" fill="{shade}" fill-opacity="{opacity}" stroke="#333"/>')
            label="N/A" if value is None else f"{value:.3f}"
            parts.append(f'<text x="{x+60}" y="{y+68}">{label}</text>')
    parts.append('<text x="40" y="710">Rows: audit predictor factor. Columns: downstream outcome factor.</text>')
    parts.append('<text x="40" y="745">Blue positive, orange negative. N/A is not zero.</text>')
    parts.append('<text x="40" y="780">If any cell is unestimable, the standardized matrix is N/A; available raw cells remain in JSON.</text>')
    save(out/"rq3_heatmap.svg",parts)
    zrows=[{"audit_factor":af,"downstream_factor":df,"standardized_contribution":grid[af][df] if grid else None} for af in FACTORS for df in FACTORS]
    text_once(out/"rq3_heatmap.csv",csv_text(zrows))
    parts=start("RQ2: incremental held-out prediction by factor",1100,540)
    xs=[fit["delta_mae"] for fit in rq2["8"].values() if fit["delta_mae"] is not None]
    bound=max([abs(x) for x in xs]+[0.01])*1.4
    inc=[]
    for i,f in enumerate(FACTORS):
        fit=rq2["8"][f];v=fit["delta_mae"];y=115+i*85
        parts.append(f'<text x="40" y="{y+6}">{f.title()}</text><path d="M600 {y-28}V{y+28}" stroke="#555"/>')
        if v is None:
            parts.append(f'<text x="610" y="{y+6}">Not identifiable</text>')
        else:
            endpoint=600+v/bound*360
            parts.append(f'<path d="M600 {y}H{endpoint}" stroke="{COLORS[0] if v>=0 else COLORS[1]}" stroke-width="18"/>')
            parts.append(f'<text x="950" y="{y+6}">{v:.4f}</text>')
        inc.append({"factor":f,"delta_mae":v,"conditional_family_bootstrap_ci95":fit["bootstrap"]["ci95"] if fit["bootstrap"] else None})
    parts.append('<text x="200" y="490">M0 MAE minus M1 MAE. Positive favors added PFC/PSC; zero at center.</text>')
    save(out/"incremental_validity.svg",parts)
    text_once(out/"incremental_validity.csv",csv_text(inc))
    folds=[{"factor":f,**fold} for f,fit in rq2["8"].items() for fold in fit["folds"]]
    parts=start("Leave-one-family-out robustness",1250,max(500,110+len(folds)*27))
    parts.append('<text class="small" x="35" y="60">Delta MAE = M0 MAE - M1 MAE. Positive favors added PFC/PSC; N/A means not identifiable.</text>')
    bound=max([abs(r["delta_mae"]) for r in folds if r["delta_mae"] is not None]+[0.01])
    for i,r in enumerate(folds):
        y=85+i*27;v=r["delta_mae"]
        parts.append(f'<text class="small" x="35" y="{y}">{r["factor"]} / {html.escape(r["held_out_family"])}</text>')
        parts.append(f'<path d="M760 {y-12}V{y+5}" stroke="#777"/>')
        if v is None:parts.append(f'<text class="small" x="780" y="{y}">N/A</text>')
        else:parts.append(f'<path d="M760 {y-4}H{760+v/bound*340}" stroke="{COLORS[0] if v>=0 else COLORS[1]}" stroke-width="10"/><text class="small" x="1130" y="{y}">{v:.4f}</text>')
    save(out/"leave_one_family_out.svg",parts)
    text_once(out/"leave_one_family_out.csv",csv_text(folds))
    pairs=matched["pairs"]
    parts=start("Accuracy-matched comparisons: all predefined 1/2/3 pp bands",1200,1000)
    for i,f in enumerate(FACTORS):
        x=85+(i%2)*570;y=95+(i//2)*360
        subset=[r for r in pairs if r["factor"]==f]
        parts.append(f'<text x="{x}" y="{y}">{f.title()}</text>')
        for tick in (-1,-.5,0,.5,1):
            xx=x+215+tick*200;yy=y+160-tick*130
            stroke="#888" if tick==0 else "#ddd"
            parts.append(f'<path d="M{xx} {y+30}V{y+290} M{x+15} {yy}H{x+415}" stroke="{stroke}" fill="none"/>')
            parts.append(f'<text class="small" text-anchor="middle" x="{xx}" y="{y+309}">{tick:.1f}</text>')
            parts.append(f'<text class="small" text-anchor="end" x="{x-3}" y="{yy+4}">{tick:.1f}</text>')
        for row in subset:
            if row["delta_PFC"] is None:continue
            xx=x+215+row["delta_PFC"]*200;yy=y+160-row["delta_U8"]*130
            parts.append(f'<circle cx="{xx}" cy="{yy}" r="{3+row["threshold_pp"]}" fill="none" stroke="{COLORS[row["threshold_pp"]-1]}" stroke-opacity=".65"><title>{html.escape(row["model_a"]+" minus "+row["model_b"])}: {row["threshold_pp"]} pp</title></circle>')
        parts.append(f'<text class="small" text-anchor="middle" x="{x+215}" y="{y+333}">Delta PFC</text>')
        parts.append(f'<text class="small" text-anchor="middle" x="{x-50}" y="{y+160}" transform="rotate(-90 {x-50} {y+160})">Delta U@8</text>')
    parts.append('<text x="40" y="860">Blue/small: 1 pp; orange/medium: 2 pp; green/large: 3 pp. Nested bands retain repeated pairs.</text>')
    parts.append('<text x="40" y="900">No outcome-selected pairs. All PFC/PSC and utility differences are in the source CSV.</text>')
    save(out/"accuracy_matched_comparisons.svg",parts)
    text_once(out/"accuracy_matched_comparisons.csv",csv_text(pairs))
