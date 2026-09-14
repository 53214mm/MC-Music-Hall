"""Pure release transforms. V18 never alters the authoritative V17 model."""
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'castle_v3/watch_v17/castle_v17.json'
OUT=ROOT/'castle_v3/release_v18'
TITLE='余响堡_V18全堡施工总册.html'
EDGE=32


def item_cost(name,props):
    if name in ('air','cave_air','void_air','piston_head'):return {}
    if name in ('moving_piston','water','lava','fire'):raise ValueError(('Unsupported release block',name))
    if name.endswith('_door'):
        if props.get('half') not in ('lower','upper'):raise ValueError(('Missing door half',name,props))
        return {name:1} if props['half']=='lower' else {}
    if name.endswith('_slab'):
        if props.get('type') not in ('top','bottom','double'):raise ValueError(('Missing slab type',name,props))
        return {name:2 if props['type']=='double' else 1}
    if name.startswith('potted_'):return {'flower_pot':1,name.removeprefix('potted_'):1}
    return {{'redstone_wire':'redstone','redstone_wall_torch':'redstone_torch'}.get(name,name):1}


def material_report(blocks):
    counts=Counter();items=Counter();groups=defaultdict(Counter);state_counts=Counter()
    for n,p,g in blocks.values():
        counts[n]+=1;cost=item_cost(n,p);items.update(cost)
        groups['music' if g=='control' or g.isdigit() else g].update(cost)
        state_counts[(n,tuple(sorted(p.items())))]+=1
    return dict(blocks=dict(counts),items=dict(items),byGroup=dict(groups),blockTotal=sum(counts.values()),
                itemTotal=sum(items.values()),itemKinds=len(items),
                generatedParts=dict(piston_head=counts['piston_head']),
                doubleSlabs=sum(c for (n,p),c in state_counts.items() if n.endswith('_slab') and dict(p).get('type')=='double'),
                note='全新手建所需成品物品，非原料合成成本。不含工具、脚手架、施工损耗；不扣回收。按64一组换算，零头向上占一格。')


def tile_manifest(low,size):
    if len(low)!=3 or len(size)!=3 or not all(type(v) is int for v in (*low,*size)) or min(size)<=0:
        raise ValueError('Integer 3D origin and positive size required')
    result=[]
    for y in range(0,size[1],EDGE):
        for x in range(0,size[0],EDGE):
            for z in range(0,size[2],EDGE):
                off=[x,y,z];dims=[min(EDGE,size[i]-off[i]) for i in range(3)]
                result.append(dict(order=len(result)+1,file=f'castle_{x//EDGE}_{y//EDGE}_{z//EDGE}.nbt',
                    offset=off,designMin=[low[i]+off[i] for i in range(3)],size=dims))
    return result


def tile_blocks(blocks,tile):
    origin=tile['designMin'];sx,sy,sz=tile['size']
    return {(x,y,z):blocks.get((x+origin[0],y+origin[1],z+origin[2]),('air',{},'air'))
            for x in range(sx) for y in range(sy) for z in range(sz)}


def design_to_world(p,origin):return [p[i]+origin[i] for i in range(3)]
