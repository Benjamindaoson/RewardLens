"""Rendering-only regression checks; fixture values are synthetic, never outcomes."""
import copy
import math
import re
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree as ET
from scripts.expanded_figures import figures
from stats import FACTORS

NS={"s":"http://www.w3.org/2000/svg"}

def text_box(node):
    # Conservative text bounds reproduce the observed tick/title collision.
    size=12 if node.get("class")=="small" else 16
    width=len(node.text or "")*size*.6
    x=float(node.get("x"));y=float(node.get("y"))
    if node.get("text-anchor")=="middle":x-=width/2
    elif node.get("text-anchor")=="end":x-=width
    corners=[(x,y-size),(x+width,y-size),(x,y),(x+width,y)]
    transform=node.get("transform")
    if transform:
        match=re.fullmatch(r"rotate\((-?[\d.]+) ([\d.]+) ([\d.]+)\)",transform)
        assert match,transform
        angle,cx,cy=map(float,match.groups());angle=math.radians(angle)
        corners=[(cx+(a-cx)*math.cos(angle)-(b-cy)*math.sin(angle),
                  cy+(a-cx)*math.sin(angle)+(b-cy)*math.cos(angle)) for a,b in corners]
    return min(a for a,b in corners),min(b for a,b in corners),max(a for a,b in corners),max(b for a,b in corners)

def overlaps(a,b):
    return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]

class FigureRenderingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.out=Path(cls.temp.name)
        cls.models=[{"model_id":"qa_model_"+str(i),"family":"qa_family_"+str(i)} for i in range(8)]
        table=[{**m,"factor":factor,"A":.5+i*.02,"PFC":.4+i*.02,"PSC":.6+i*.02,"U8":.5+i*.03}
               for factor in FACTORS for i,m in enumerate(cls.models)]
        rq2={"8":{f:{"delta_mae":.02,"bootstrap":{"ci95":[-.01,.03]},
                     "folds":[{"held_out_family":"qa_family","delta_mae":-.01}]} for f in FACTORS}}
        rq3={"matrix":[],"primary_4factor":{"column_standardized_matrix":{f:{g:(i-j)/3 for j,g in enumerate(FACTORS)} for i,f in enumerate(FACTORS)}}}
        pairs=[{"factor":f,"threshold_pp":n,"model_a":"qa_model_0","model_b":"qa_model_1",
                "delta_A_pp":.5,"delta_PFC":d,"delta_PSC":.1,"delta_U8":d}
               for f in FACTORS for n,d in [(1,0),(2,.5),(3,-.5)]]
        inputs=(table,cls.models,rq2,rq3,{"pairs":pairs})
        snapshot=copy.deepcopy(inputs)
        figures(cls.out,*inputs)
        assert inputs==snapshot,"rendering mutated source values"
        cls.docs={p.stem:ET.parse(p).getroot() for p in cls.out.glob("*.svg")}

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def test_scatter_axis_title_does_not_overlap_numeric_ticks(self):
        for key in ("A","PFC","PSC"):
            texts=self.docs[key+"_vs_U8"].findall(".//s:text",NS)
            labels=[n for n in texts if n.text=="U@8"]
            ticks=[n for n in texts if n.get("class")=="small" and n.text in ("0.0","0.2","0.4","0.6","0.8","1.0")]
            self.assertEqual(len(labels),4)
            for label in labels:
                self.assertFalse(any(overlaps(text_box(label),text_box(t)) for t in ticks),
                                 "U@8 title overlaps numeric tick text")

    def test_models_are_distinguishable_without_color(self):
        doc=self.docs["A_vs_U8"]
        ids={m["model_id"] for m in self.models}
        points=[n for n in doc.iter() if n.find("s:title",NS) is not None and n.find("s:title",NS).text in ids]
        self.assertEqual(len(points),32)
        signatures=[]
        for point in points[:8]:
            shapes=[point] if point.tag.endswith("circle") else [n for n in point if not n.tag.endswith("title")]
            signatures.append(tuple((n.tag,tuple(sorted((k,v) for k,v in n.attrib.items() if k not in ("fill","stroke","cx","cy")))) for n in shapes))
        self.assertEqual(len(set(signatures)),8,"model identity relies only on color")

    def test_matched_axes_have_numeric_scale_and_unchanged_coordinates(self):
        doc=self.docs["accuracy_matched_comparisons"]
        texts=doc.findall(".//s:text",NS)
        for value,x in [("-1.0",100),("0.0",300),("1.0",500)]:
            self.assertTrue(any(n.text==value and float(n.get("x","nan"))==x and float(n.get("y","nan"))==404 for n in texts),
                            "matched x-axis lacks calibrated numeric ticks")
        points=[n for n in doc.findall(".//s:circle",NS) if n.find("s:title",NS) is not None]
        self.assertEqual([(float(n.get("cx")),float(n.get("cy"))) for n in points[:3]],
                         [(300,255),(400,190),(200,320)])

    def test_lofo_identifies_metric_and_direction(self):
        content=" ".join(n.text or "" for n in self.docs["leave_one_family_out"].findall(".//s:text",NS))
        for word in ("MAE","M0","M1","Positive"):
            self.assertIn(word,content,"standalone LOFO figure lacks metric/direction context")

    def test_figures_have_text_alternatives_and_source_reference(self):
        self.assertEqual(len(self.docs),7)
        for doc in self.docs.values():
            self.assertEqual(doc.get("role"),"img")
            self.assertIsNotNone(doc.find("s:title",NS))
            desc=doc.find("s:desc",NS)
            self.assertIsNotNone(desc)
            self.assertIn("CSV",desc.text)

if __name__=="__main__":
    unittest.main()
