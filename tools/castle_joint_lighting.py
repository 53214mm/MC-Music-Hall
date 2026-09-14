"""Conservative air-cell light comparison, explicitly not a game engine."""
from functools import lru_cache
from castle_joint import joint_castle
from castle_finish import EMISSION, spread_light
from castle_front import route_cells


@lru_cache(maxsize=1)
def lighting_audit():
    m=joint_castle();fields={}
    for key in ('before','after'):
        blocks=m[key]
        fields[key]=spread_light(blocks,{p:EMISSION[s[0]] for p,s in blocks.items() if s[0] in EMISSION})
    def stats(field,points):
        values=[field.get(tuple(p),0) for p in points]
        return dict(samples=len(values),minimum=min(values) if values else None,
                    mean=round(sum(values)/len(values),2) if values else None,
                    zero=sum(v==0 for v in values),below5=sum(v<5 for v in values))
    rows=[];allpoints=set();worse=[]
    for r in m['data']['routes']:
        points={(x,y+1,z) for x,y,z in route_cells(r['points'],r['width'])}
        allpoints.update(points)
        lower=[p for p in points if fields['after'].get(p,0)<fields['before'].get(p,0)]
        worse.extend((r['name'],p,fields['before'].get(p,0),fields['after'].get(p,0)) for p in lower)
        rows.append(dict(name=r['name'],before=stats(fields['before'],points),after=stats(fields['after'],points),dimmerSamples=len(lower)))
    zero_points=[dict(pos=p,inMusicProtection=(-8<=p[0]<=50 and -35<=p[1]<=45 and -37<=p[2]<=38),
                      occupyingBlock=m['after'].get(p)) for p in sorted(allpoints) if fields['after'].get(p,0)==0]
    report=dict(method='六邻域空气格传播代理；不透明异形方块按整格遮挡。无天空光、反射、游戏连接更新或刷怪判定。',
                sample='35条登记路线全宽支撑上方一格，汇总去重。不是所有房间或全部可走表面。',
                before=stats(fields['before'],allpoints),after=stats(fields['after'],allpoints),
                dimmerSamples=worse,zeroSampleLocations=zero_points,routes=rows,inGameTest=False)
    return report,fields
