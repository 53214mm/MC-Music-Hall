"""Publish the V3 study separately, leaving the previous construction files intact."""
import json
from pathlib import Path
from castle_plan import plan

PROJECT=Path(__file__).resolve().parents[1]
OUT=PROJECT/'castle_v3'


def main():
    OUT.mkdir(exist_ok=True)
    p=plan()
    (OUT/'castle_plan.json').write_text(json.dumps(p,ensure_ascii=False,indent=2),encoding='utf-8')
    template=(PROJECT/'tools'/'castle_study_viewer.html').read_text(encoding='utf-8')
    (OUT/'余响堡_空间总图.html').write_text(template.replace('__PLAN__',json.dumps(p,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    (OUT/'法环城堡参考研究.md').write_bytes((PROJECT/'design'/'法环城堡参考研究.md').read_bytes())
    print(f'Generated V3 study: {len(p["masses"])} masses, {len(p["nodes"])} spaces, {len(p["edges"])} links. Not a final NBT blueprint.')


if __name__=='__main__':main()
