"""V12 additive path lights; exact music-air exceptions, never a global unlock."""
import json
from functools import lru_cache
from castle_detail import ROOT,read_model
from castle_finish import EMISSION,protected,spread_light
from castle_front import route_cells
from castle_sculpt import FULL

HANGING=((20,1,4,3),(30,5,5,15),(38,5,5,15))
PEDESTALS=((-51,-4,85),(-47,-4,85),(-46,-23,170),(-40,-22,170))


def hanging_parts(x,y,z,roof):
    return {(x,yy,z):('lantern',{'hanging':'true','waterlogged':'false'},'shell') if yy==y
            else ('iron_chain',{'axis':'y','waterlogged':'false'},'shell') for yy in range(y,roof)}


def approved_music_parts():
    return {p:s for spec in HANGING for p,s in hanging_parts(*spec).items()}


class AirOnlyLightingEditor:
    """One local pass: append only, frozen air wins over exact exceptions."""
    def __init__(self,before,frozen,approved):
        self.before=before;self.blocks=dict(before);self.frozen=frozen;self.approved=approved

    def apply(self,name,parts):
        conflicts=[]
        for p,s in parts.items():
            if p in self.blocks or p in self.frozen or not s or s[2]!='shell' or s[0] not in {'lantern','iron_chain','chiseled_tuff_bricks'}:
                conflicts.append(p)
            elif protected(p) and self.approved.get(p)!=s:conflicts.append(p)
        if conflicts:raise ValueError(f'{name}: unsafe additive placement, no edits applied: {conflicts}')
        self.blocks.update(parts)


@lru_cache(maxsize=1)
def pathlight_castle():
    data,before=read_model(ROOT/'castle_v3/detail_v11/castle_v11.json')
    music={p for p,s in before.items() if s[2]=='control' or s[2].isdigit()}
    halo={(x+dx,y+dy,z+dz) for x,y,z in music for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    frozen=set(halo)
    for r in data['routes']:
        for x,y,z in route_cells(r['points'],r['width']):frozen.update((x,y+k,z) for k in range(4))
    for f in data['features'][:12]:
        r=f['region'];frozen.update((x,y,z) for x in range(r[0],r[1]+1) for y in range(r[2],r[3]+1) for z in range(r[4],r[5]+1))
    for f in data['fixtures']:
        frozen.update(map(tuple,f['supports']));frozen.update(map(tuple,f['parts']))
    for p,s in before.items():
        if s[0] in EMISSION:frozen.update((p,(p[0],p[1]-1,p[2]),(p[0],p[1]+1,p[2])))
    editor=AirOnlyLightingEditor(before,frozen,approved_music_parts());fixtures=[];features=[]
    def commit(name,kind,parts,anchor,note):
        base=before.get(anchor)
        if not base or not (base[0] in FULL or base[0].endswith('_wall') and base[1].get('up')=='true'):
            raise ValueError(f'{name}: no original full block or upright wall anchor {anchor}')
        editor.apply(name,parts)
        pos=next(p for p,s in parts.items() if s[0]=='lantern')
        fixtures.append(dict(name=name,kind=kind,zone=name,pos=pos,parts=list(parts),supports=[anchor]))
        ps=list(parts)+[anchor]
        features.append(dict(name=name,family='path_light',changed=len(parts),anchors=[anchor],note=note,
            region=[v for i in range(3) for v in(min(p[i] for p in ps),max(p[i] for p in ps))]))
    for spec,name in zip(HANGING,['中央试听位梁下灯','避线高桥中段悬灯','避线高桥东段悬灯']):
        x,y,z,roof=spec
        commit(name,'梁下悬灯',hanging_parts(*spec),(x,roof,z),
            f'原梁Y={roof}不拆；灯Y={y}，其上接竖铁链。位置与材料精确白名单，音乐一格邻域及三格通路净空不动。')
    for anchor,name in zip(PEDESTALS,['前庭落差左柱灯','前庭落差右柱灯','南入口坡道西柱灯','南入口坡道东侧高位灯']):
        x,y,z=anchor
        parts={(x,y+1,z):('chiseled_tuff_bricks',{},'shell'),
               (x,y+2,z):('lantern',{'hanging':'false','waterlogged':'false'},'shell')}
        commit(name,'端柱座灯',parts,anchor,'利用既有栏杆柱或高一格的原土面，加雕纹凝灰岩砖灯座与灯笼；不替换栏杆、台阶或地表。')
    added=set(editor.blocks)-set(before)
    separation=[dict(name=f['name'],minimumChebyshevDistance=min(max(abs(p[i]-q[i]) for i in range(3)) for p in map(tuple,f['parts']) for q in music)) for f in fixtures[:3]]
    return dict(data=data,before=before,after=editor.blocks,added=added,frozen=frozen,musicHalo=halo,fixtures=fixtures,features=features,
                approved=approved_music_parts(),separation=separation)


def audit_models(data,before,after,former_zeros):
    fields={key:spread_light(b,{p:EMISSION[s[0]] for p,s in b.items() if s[0] in EMISSION}) for key,b in [('before',before),('after',after)]}
    def stats(field,points):
        vs=[field.get(p,0) for p in points]
        return dict(samples=len(vs),minimum=min(vs),mean=round(sum(vs)/len(vs),2),zero=sum(v==0 for v in vs),below5=sum(v<5 for v in vs))
    allpoints=set();rows=[];worse=[]
    for r in data['routes']:
        points={(x,y+1,z) for x,y,z in route_cells(r['points'],r['width'])};allpoints.update(points)
        lower=[p for p in points if fields['after'].get(p,0)<fields['before'].get(p,0)]
        worse.extend(dict(route=r['name'],pos=p,before=fields['before'].get(p,0),after=fields['after'].get(p,0)) for p in sorted(lower))
        rows.append(dict(name=r['name'],before=stats(fields['before'],points),after=stats(fields['after'],points),dimmerSamples=len(lower)))
    former=[dict(pos=d['pos'],before=fields['before'].get(tuple(d['pos']),0),after=fields['after'].get(tuple(d['pos']),0),
                 inMusicProtection=d['inMusicProtection']) for d in former_zeros]
    low=[dict(pos=p,value=fields['after'].get(p,0)) for p in sorted(allpoints) if fields['after'].get(p,0)<5]
    report=dict(method='与V11相同的保守六邻域空气格代理；不透明异形方块整格遮挡，无天空光/反射/刷怪判定。',
        sample='35条登记路线全宽支撑上方一格，去重；不代表全堡每个可走表面。',
        before=stats(fields['before'],allpoints),after=stats(fields['after'],allpoints),routes=rows,
        dimmerSamples=worse,formerZeros=former,remainingBelow5=low,inGameTest=False)
    return report,fields


@lru_cache(maxsize=1)
def pathlight_audit():
    m=pathlight_castle();former=json.loads((ROOT/'castle_v3/detail_v11/照明代理与待验坐标.json').read_text(encoding='utf-8'))['zeroSampleLocations']
    return audit_models(m['data'],m['before'],m['after'],former)
