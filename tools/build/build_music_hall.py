"""Generate an auditable shell and spatial module assembly. No implicit redstone simulation."""
import gzip
import json
import math
import struct
from collections import Counter, defaultdict
from pathlib import Path

try:
    from nbt_structure_to_json import read_nbt
except ModuleNotFoundError:  # 允许直接运行 python tools/build/build_music_hall.py
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'viewer'))
    from nbt_structure_to_json import read_nbt

PROJECT = Path(__file__).resolve().parents[2]
OUTPUT = PROJECT / 'build' / 'music_hall'
OFFSET = (29, 3, 40)
OPPOSITE = {'north':'south','south':'north','east':'west','west':'east'}
_MODULE_CACHE = {}


def is_north(number):
    floor, side = divmod(number-1, 2)
    return side == floor % 2


def transform(number, point):
    x,y,z = point
    y += ((number-1)//2)*12
    return (42-x,y,-1-z) if is_north(number) else (x,y,8+z)


def rotate_properties(props):
    result = {}
    for key, value in props.items():
        if key == 'facing': value = OPPOSITE.get(value,value)
        if key == 'rotation': value = str((int(value)+8)%16)
        result[OPPOSITE.get(key,key)] = value
    return result


def make_core_shell():
    blocks = {}
    def put(x,y,z,name): blocks[(x,y,z)] = (name,{},'shell')
    def inside(x,z,inset=0):
        return -7+inset<=x<=49-inset and -37+inset<=z<=38-inset and min(x+7-inset,49-inset-x)+min(z+37-inset,38-inset-z)>=5
    def edge(x,z,inset=0):
        return inside(x,z,inset) and any(not inside(x+dx,z+dz,inset) for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)])
    # Foundation is a floor with two perimeter courses, not a solid three-block slab.
    for x in range(-7,50):
        for z in range(-37,39):
            if not inside(x,z): continue
            put(x,-1,z,'smooth_stone')
            if edge(x,z):
                for y in [-3,-2]: put(x,y,z,'polished_andesite')
    # Facade: clipped corners, vertical mullions, luminous floor bands.
    for y in range(0,69):
        for x in range(-7,50):
            for z in range(-37,39):
                if not edge(x,z): continue
                if z==38 and 17<=x<=25 and y<=5: continue
                band = y in [0,11,12,23,24,35,36,47,48,59,60,67,68]
                pillar = x in [-7,-2,5,13,21,29,37,44,49] if z in [-37,38] else z in [-37,-32,-23,-14,-5,4,13,22,31,38]
                material = 'white_concrete' if band or pillar else 'light_blue_stained_glass'
                if y in [12,24,36,48,60] and not pillar: material='sea_lantern'
                if y in [0,67,68]: material='smooth_quartz'
                put(x,y,z,material)
    # External service galleries; the west side is intentionally reserved for future control routing.
    for y in [11,23,35,47,59,71]:
        for x in range(44,48):
            for z in range(-33,35): put(x,y,z,'smooth_quartz')
        for x in range(0,44):
            for z in [-34,-33,34,35]: put(x,y,z,'smooth_quartz')
        # Bridges end clear of the center wiring allowance X=22..29.
        for x in list(range(0,22))+list(range(30,44)):
            for z in [2,3,4,5]: put(x,y,z,'white_concrete')
    # Main listening platform, centered on the audited listening position.
    for x in range(14,22):
        for z in range(1,7): put(x,29,z,'smooth_quartz')
    for x in range(22,48):
        for z in [4,5]: put(x,29,z,'smooth_quartz')
    # Ladder shaft at east side, clear of machine and future western control slot.
    for y in range(0,73):
        put(47,y,1,'white_concrete')
        blocks[(46,y,1)] = ('ladder',{'facing':'west','waterlogged':'false'},'shell')
    # Cut openings in gallery floors for the ladder.
    for y in [11,23,35,47,59,71]:
        blocks[(46,y,1)] = ('ladder',{'facing':'west','waterlogged':'false'},'shell')
    # Straight twelve-step flights, each joined by the east gallery.
    for base in range(0,61,12):
        for step in range(12):
            for x in [44,45]:
                blocks[(x,base+step,12+step)] = ('smooth_quartz_stairs',{'facing':'south','half':'bottom','shape':'straight','waterlogged':'false'},'shell')
    # Stepped glazed dome, shrinking in plan with closed annular shoulders.
    for y in range(69,79):
        inset=(y-68)*2
        previous=inset-2
        for x in range(-7,50):
            for z in range(-37,39):
                if inside(x,z,previous) and not inside(x,z,inset):
                    material='white_concrete' if x in [20,21,22] or z in [0,1,2] else 'light_blue_stained_glass'
                    put(x,y,z,material)
    for x in range(-7,50):
        for z in range(-37,39):
            if inside(x,z,20): put(x,79,z,'light_blue_stained_glass')
    # A small violet crystal crown, with a solid amethyst pedestal.
    for y,r in [(80,3),(81,2),(82,1),(83,0)]:
        for x in range(21-r,22+r):
            for z in range(1-r,2+r):
                if abs(x-21)+abs(z-1)<=r:
                    put(x,y,z,'amethyst_block' if y==80 else 'purple_stained_glass')
    # Interior ring and listening-platform lamps, no powered redstone lighting.
    for y in [10,22,34,46,58,70]:
        for z in range(-26,31,8): put(47,y,z,'sea_lantern')
    return blocks


def make_shell():
    from church_shell import make_church
    return make_church(make_core_shell())


def encode_structure(blocks, data_version):
    """Serialize a nonnegative sparse structure, only standard string-valued block states."""
    def string(s):
        raw=s.encode('utf-8'); return struct.pack('>H',len(raw))+raw
    def named(t,n,p): return bytes([t])+string(n)+p
    def int_tag(n,v): return named(3,n,struct.pack('>i',v))
    def ints(n,vs): return named(9,n,b'\x03'+struct.pack('>i',len(vs))+b''.join(struct.pack('>i',v) for v in vs))
    palette=[]; indexes={}; block_tags=[]
    for position,(name,properties,_) in sorted(blocks.items()):
        if any(v<0 for v in position): raise ValueError('NBT coordinates must be nonnegative')
        key=(name,tuple(sorted(properties.items())))
        if key not in indexes:
            indexes[key]=len(palette)
            tag=named(8,'Name',string('minecraft:'+name))
            if properties:
                tag+=named(10,'Properties',b''.join(named(8,k,string(v)) for k,v in sorted(properties.items()))+b'\0')
            palette.append(tag+b'\0')
        block_tags.append(int_tag('state',indexes[key])+ints('pos',position)+b'\0')
    size=[max((p[i]+1 for p in blocks),default=1) for i in range(3)]
    root=int_tag('DataVersion',data_version)+ints('size',size)
    root+=named(9,'palette',b'\x0a'+struct.pack('>i',len(palette))+b''.join(palette))
    root+=named(9,'blocks',b'\x0a'+struct.pack('>i',len(block_tags))+b''.join(block_tags))
    root+=named(9,'entities',b'\x0a'+struct.pack('>i',0))+b'\0'
    return b'\x0a\0\0'+root


def load_modules():
    """构建输入：11 个模块的实测方块。结果缓存，测试与审计重复调用时不再重算。"""
    key = _module_cache_key()
    if key not in _MODULE_CACHE:
        _MODULE_CACHE[key] = _load_modules_uncached()
    return _MODULE_CACHE[key]


def _module_cache_key():
    probe = PROJECT / 'nbt_export'
    files = sorted(probe.glob('*.nbt'))
    return tuple((p.name, p.stat().st_mtime_ns, p.stat().st_size) for p in files)


def _load_modules_uncached():
    blocks={}; placement=[]
    for number in range(1,12):
        filename='module_01.nbt' if number==1 else f'departures_module_{number:02}.nbt'
        root=read_nbt(PROJECT/'nbt_export'/filename)
        for item in root['blocks']:
            state=root['palette'][item['state']]; name=state['Name'].removeprefix('minecraft:')
            if name in ['air','cave_air','void_air','oak_wall_sign']: continue
            pos=transform(number,item['pos'])
            if pos in blocks: raise ValueError(f'Module collision {pos}')
            props=state.get('Properties',{})
            blocks[pos]=(name,rotate_properties(props) if is_north(number) else props,str(number).zfill(2))
        placement.append({'module':number,'baseY':((number-1)//2)*12,'north':is_north(number),
                          'buttonDesign':transform(number,(19,6 if number==11 else 9,2)),
                          'rotation':180 if is_north(number) else 0})
    return blocks,placement


def main(argv=None):
    import argparse
    parser = argparse.ArgumentParser(description='生成教堂外壳 + 空间模块装配')
    parser.add_argument('--phase1', action='store_true',
                        help='用阶段 1 的总体体块（tools/build/phase1_massing.py）替换现有外壳')
    parser.add_argument('--out', default=None, help='输出目录，默认 build/music_hall')
    args = parser.parse_args(argv)

    from hall_connections import generate_connections,verify_rising_signal
    output = OUTPUT if args.out is None else (PROJECT / args.out)
    output.mkdir(parents=True,exist_ok=True)
    modules,placement=load_modules()
    if args.phase1:
        import phase1_massing
        shell=phase1_massing.generate()
    else:
        shell=make_shell()
    control,connection_report=generate_connections(modules,transform,is_north)
    signal_report=verify_rising_signal(modules,control,transform)
    # Reserve service apertures around wiring, preserving electrical headroom.
    removed_shell=[]
    clear=set(control)
    for (x,y,z),state in control.items():
        if state[0] in ['redstone_wire','repeater','stone_button']:
            for dx in [-1,0,1]:
                for dy in [0,1]:
                    for dz in [-1,0,1]:clear.add((x+dx,y+dy,z+dz))
    for p in clear:
        if p in shell:removed_shell.append(p);del shell[p]
    overlap=set(modules)&set(shell)
    if overlap: raise ValueError(f'Shell collisions: {sorted(overlap)[:10]}')
    merged={**modules,**shell,**control}
    for (x,y,z),state in control.items():
        if state[0]=='redstone_wire' and (x,y+1,z) in merged:
            # A roof above dust can prevent a stair connection; reserve it regardless.
            raise ValueError(f'Covered control dust {(x,y,z)}')
    for (x,y,z),(name,_,_) in modules.items():
        if name=='note_block' and (x,y+1,z) in merged:
            raise ValueError(f'Covered note block {(x,y,z)}')
    # 偏移改为按实际最小坐标自动计算：阶段 1 的外壳向南北两端都变大了，写死偏移会出现负坐标。
    offset=tuple(-min(p[i] for p in merged) for i in range(3))
    normalized={tuple(p[i]+offset[i] for i in range(3)):s for p,s in merged.items()}
    # 1519 is the source version; selected shell blocks all existed in 1.13 except
    # amethyst/smooth_quartz. Use the target runtime version when supplied by its version.json.
    version_file=PROJECT/'design'/'target_version.json'
    if not version_file.exists(): raise ValueError('Missing verified target_version.json')
    version=json.loads(version_file.read_text(encoding='utf-8'))['world_version']
    # Unified NBT is an interchange/reference file, too large for a single structure-block load.
    (output/'music_hall_reference.nbt').write_bytes(gzip.compress(encode_structure(normalized,version)))
    chunks=defaultdict(dict)
    for pos,state in normalized.items():
        tile=tuple(v//32 for v in pos); local=tuple(v%32 for v in pos)
        chunks[tile][local]=state
    chunk_dir=output/'structure_tiles'; chunk_dir.mkdir(exist_ok=True)
    manifest=[]
    for tile,bs in sorted(chunks.items()):
        name='hall_'+'_'.join(f'{v:02}' for v in tile)
        (chunk_dir/(name+'.nbt')).write_bytes(gzip.compress(encode_structure(bs,version)))
        manifest.append({'file':name+'.nbt','offset':[v*32 for v in tile],'blocks':len(bs)})
    (output/'tile_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    groups=defaultdict(Counter)
    for name,_,group in merged.values(): groups[group][name]+=1
    total=Counter()
    for counts in groups.values(): total.update(counts)
    report={'status':'教堂外壳与全部连接已生成；已通过坐标、音符与上升沿模型核验，尚未在Minecraft实机播放验收。播放期间不要重复按启动键。','offset':offset,
            'size':[max(p[i] for p in normalized)+1 for i in range(3)],'totalBlocks':len(merged),
            'noteBlocks':total['note_block'],'coveredNotes':0,'shellModuleCollisions':0,
            'placement':placement,'materials':dict(total),'byGroup':{g:dict(c) for g,c in groups.items()},
            'controlOpenings':len(removed_shell),'signalVerification':signal_report}
    (output/'build_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'connection_report.json').write_text(json.dumps(connection_report,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 水晶教堂材料表（外壳+音乐模块+连接线路）','',f'总方块数：{len(merged)}。原模块的11块版权告示牌未复制；02—11原正面按钮替换为输入中继器，侧面另加测试按钮。','',
           '| 方块ID | 总数量 | 组+余数（每组64） | 外壳用量 | 连接用量 |','|---|---:|---|---:|---:|']
    for name,count in sorted(total.items(),key=lambda p:-p[1]):
        lines.append(f'| {name} | {count} | {count//64}组+{count%64} | {groups["shell"][name]} | {groups["control"][name]} |')
    (output/'材料表.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    palette=[]; ix={}; compact=[]
    for pos,(name,props,group) in sorted(normalized.items()):
        key=(name,tuple(sorted(props.items())),group)
        if key not in ix:
            ix[key]=len(palette);palette.append([name,props,group])
        compact.append([*pos,ix[key]])
    payload={'size':report['size'],'offset':offset,'palette':palette,'blocks':compact,'report':report}
    template=(Path(__file__).resolve().parent/'music_hall_viewer.html').read_text(encoding='utf-8')
    (output/'水晶音乐馆施工图.html').write_text(template.replace('__DATA__',json.dumps(payload,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['size','totalBlocks','noteBlocks','coveredNotes','shellModuleCollisions']},ensure_ascii=False))


if __name__=='__main__': main()
