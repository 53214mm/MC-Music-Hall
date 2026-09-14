"""Full castle in design coordinates. The translated musical assembly is immutable."""
import copy
import math
from functools import lru_cache
from build_music_hall import load_modules,make_core_shell,transform,is_north,PROJECT
from nbt_structure_to_json import read_nbt
from hall_connections import generate_connections,verify_rising_signal
from castle_front import combined_model,grid_route,route_cells,DIRECTIONS


def shift(p):return (p[0],p[1]-32,p[2])


def relocate_music(blocks):return {shift(p):v for p,v in blocks.items()}


def check_source_entities(root):
    if root.get('entities'):raise ValueError('Source has entities unsupported by the block-only exporter')
    for b in root['blocks']:
        if 'nbt' in b and root['palette'][b['state']]['Name']!='minecraft:oak_wall_sign':
            raise ValueError('Source has a required block entity; refusing to discard its NBT')


def translate_connections(report):
    result=copy.deepcopy(report)
    for c in result['connections']:
        for k in ('tapPosition','nextRelayPosition'):c[k]=list(shift(c[k]))
        c['timerPositions']=[list(shift(p)) for p in c['timerPositions']]
    for path in result['paths']:path['positions']=[list(shift(p)) for p in path['positions']]
    return result


def protected(p):
    x,y,z=p
    return -8<=x<=50 and -35<=y<=45 and -37<=z<=38


def footprint(cx,cz,r):
    return {(x,z) for x in range(cx-r,cx+r+1) for z in range(cz-r,cz+r+1) if abs(x-cx)+abs(z-cz)<=int(r*1.45)}


def polygon(vertices):
    result=set()
    for x in range(min(p[0] for p in vertices),max(p[0] for p in vertices)+1):
        for z in range(min(p[1] for p in vertices),max(p[1] for p in vertices)+1):
            inside=False
            for a,b in zip(vertices,vertices[1:]+vertices[:1]):
                if (a[1]>z)!=(b[1]>z) and x<(b[0]-a[0])*(z-a[1])/(b[1]-a[1])+a[0]:inside=not inside
            if inside:result.add((x,z))
    return result


@lru_cache(maxsize=1)
def complete_model():
    previous=combined_model();old=previous['blocks']
    for i in range(1,12):
        file='module_01.nbt' if i==1 else f'departures_module_{i:02}.nbt'
        check_source_entities(read_nbt(PROJECT/'nbt_save'/file))
    modules,placement=load_modules()
    control,connections=generate_connections(modules,transform,is_north)
    signal=verify_rising_signal(modules,control,transform)
    original={**modules,**control};music=relocate_music(original)
    # Reuse only the old internal galleries/platform and foundation, not the glass facade.
    core=make_core_shell();electrical_clear=set(control)
    for (x,y,z),v in control.items():
        if v[0] in ('redstone_wire','repeater','stone_button'):
            electrical_clear.update((x+dx,y+dy,z+dz) for dx in(-1,0,1) for dy in(0,1) for dz in(-1,0,1))
    interior={}
    for p,(n,props,g) in core.items():
        x,y,z=p
        if p in electrical_clear or p in original:continue
        if (y>=69 and not (44<=x<=47 and (n in ('ladder','smooth_quartz_stairs') or y==71 or x==47 and z==1))) or n=='light_blue_stained_glass':continue
        # Mullions on the old outer edge are removed along with the glass.
        if y>=0 and (x<=-2 or x>=49 or z<=-32 or z>=33):continue
        n={'white_concrete':'polished_andesite','smooth_quartz':'stone_bricks','smooth_quartz_stairs':'stone_brick_stairs','smooth_stone':'stone_bricks'}.get(n,n)
        interior[shift(p)]=(n,props,'shell')
    # The old dome overwrote one ladder at original Y=70; restore the full shaft.
    for y in range(-32,41):interior[46,y,1]=('ladder',dict(facing='west',waterlogged='false'),'shell')
    blocks={};routes=[];rooms=[]
    def put(x,y,z,n='stone_bricks',props=None,group='shell'):
        p=(x,y,z)
        if not protected(p):blocks[p]=(n,props or {},group)
    def box(x0,y0,z0,x1,y1,z1,n='stone_bricks',props=None,group='shell'):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):put(x,y,z,n,props,group)
    def clear(x0,y0,z0,x1,y1,z1):
        for x in range(x0,x1+1):
            for y in range(y0,y1+1):
                for z in range(z0,z1+1):blocks.pop((x,y,z),None)
    def stair(x,y,z,facing,half='bottom',n='stone_brick_stairs'):
        put(x,y,z,n,dict(facing=facing,half=half,shape='straight',waterlogged='false'))
    def rail(x,y,z):put(x,y,z,'stone_brick_wall',dict(up='true',east='none',west='none',north='none',south='none',waterlogged='false'))
    def lamp(x,y,z):put(x,y,z,'lantern',dict(hanging='false',waterlogged='false'))
    def barrel(x,y,z):put(x,y,z,'barrel',dict(facing='up',open='false'))
    def route(name,vertices,width=3,kind='explore'):
        r=dict(name=name,points=grid_route(vertices),width=width,kind=kind);routes.append(r);return r
    def story(name,pos,text):rooms.append(dict(name=name,pos=pos,text=text))
    def outline(area):return {p for p in area if any((p[0]+dx,p[1]+dz) not in area for dx,dz in DIRECTIONS)}
    def hall(name,area,floor,top,ridge_x,roof_rise):
        edge=outline(area);walls=edge|{(x+dx,z+dz) for x,z in edge for dx,dz in DIRECTIONS if (x+dx,z+dz) in area}
        for x,z in area:
            put(x,floor,z)
            if (x,z) in walls:box(x,floor+1,z,x,top,z)
            ry=top+2+max(0,roof_rise-abs(x-ridge_x)//2)
            stair(x,ry,z,'east' if x<ridge_x else 'west',n='deepslate_tile_stairs')
            # A closed triangular gable at each varying polygon end.
            if (x,z-1) not in area or (x,z+1) not in area:box(x,top,z,x,ry-1,z)
        for x,z in edge:
            if z%9==0:
                box(x,floor-4,z,x,top-5,z,'polished_andesite')
                stair(x,top-4,z,'east' if x<ridge_x else 'west')
        return walls
    def tower(cx,cz,r,base,top,levels,roof=True):
        outer=footprint(cx,cz,r);inner=footprint(cx,cz,r-2);crown=footprint(cx,cz,r+1)
        for x,z in outer:
            if (x,z) not in inner:box(x,base,z,x,top,z)
            else:clear(x,base+1,z,x,top,z)
            for y in levels:put(x,y,z,'spruce_planks' if y>40 else 'stone_bricks')
        for x,z in crown:
            if (x,z) not in inner:
                box(x,top+1,z,x,top+2,z,'polished_andesite')
                if (x+z)%3==0:stair(x,top,z,'east' if x<cx else 'west',half='top')
        if roof:
            for x,z in crown:
                d=max(abs(x-cx),abs(z-cz),math.ceil((abs(x-cx)+abs(z-cz))/1.45))
                put(x,top+3+max(0,r+1-d),z,'deepslate_tiles')
        else:
            for x,z in outline(crown):
                box(x,top+3,z,x,top+3+int((x+z)%4<2)*2,z)
        for yy in levels:
            if yy+9>=top:continue
            for xx,zz,dx,dz in((cx-r,cz,1,0),(cx+r,cz,-1,0),(cx,cz-r,0,1),(cx,cz+r,0,-1)):
                clear(min(xx,xx+dx),yy+3,min(zz,zz+dz),max(xx,xx+dx),yy+9,max(zz,zz+dz))
                for y in range(yy+3,yy+9):put(xx,y,zz,'iron_bars',dict(east=str(not dx).lower(),west=str(not dx).lower(),north=str(bool(dx)).lower(),south=str(bool(dx)).lower(),waterlogged='false'))
    # North/east island joins the previous south cliff without modifying its blocks.
    land=polygon([(-83,79),(-81,0),(-62,-72),(-17,-85),(51,-75),(87,-29),(99,34),(75,93),(9,101),(-43,97)])
    heights={}
    for x,z in land:
        h=round(-5+3*math.sin(x*.14)+2*math.sin(z*.11))
        if x>75:h-=round((x-75)*.45)
        heights[x,z]=h
    for (x,z),top in heights.items():
        low=min(top-2,*(heights.get((x+dx*3,z+dz*3),-49) for dx,dz in DIRECTIONS))
        for y in range(max(-48,low),top+1):
            # Reserve whole inhabited substructures, not merely centerline tunnels.
            if (-64<=x<=-10 and -19<=z<=80 and y>=-14) or (-13<=x<=57 and -42<=z<=44 and y>=-37):continue
            put(x,y,z,'tuff' if y%17<3 else 'stone',group='terrain')
        put(x,-48,z,'stone',group='terrain')
    # Massive clipped keep: a three-block envelope outside the musical reservation.
    keep={(x,z) for x in range(-13,58) for z in range(-42,45) if min(x+13,57-x)+min(z+42,44-z)>=7}
    inner={(x,z) for x in range(-10,55) for z in range(-39,42) if min(x+10,54-x)+min(z+39,41-z)>=6}
    for x,z in keep:
        put(x,-36,z)
        if (x,z) not in inner:box(x,-35,z,x,46,z)
        # Hipped main roof with a bounded central crystal lantern opening.
        d=max(abs(x-21),int(abs(z-1)*.65));ry=48+max(0,(36-d)//2)
        if abs(x-21)<=9 and abs(z-10)<=9:continue
        put(x,ry,z,'deepslate_tiles')
    # Vertical facade bays are deep and sparse; no bright full-width floor bands.
    for z in range(-31,36,13):
        for x in(-14,58):
            box(x,-36,z,x+1,35,z+2,'polished_andesite')
            for k in range(4):stair(x,36+k,z+1,'east' if x<0 else 'west')
            for y0 in(-20,3,26):
                xx=-13 if x<0 else 57
                for zz in range(z+5,z+8):
                    clear(xx-2 if x>0 else xx,y0,zz,xx if x>0 else xx+2,y0+9-abs(zz-z-6),zz)
                    for y in range(y0,y0+9-abs(zz-z-6)):
                        put(xx,y,zz,'iron_bars',dict(north='true',south='true',east='false',west='false',waterlogged='false'))
    # South frontage: recessed tall blind arches, a stone oculus and setback feet.
    for cx in(-1,10,21,32,43):
        for x in range(cx-3,cx+4):
            upper=29-abs(x-cx)*2
            clear(x,5,43,x,upper,44)
            box(x,5,42,x,upper,42,'polished_andesite')
            stair(x,upper+1,45,'north',half='top')
        for x in(cx-4,cx+4):box(x,-30,45,x,31,46)
    for x in range(14,29):
        for y in range(30,45):
            radius=math.hypot(x-21,y-37)
            if 5<radius<7:put(x,y,45,'polished_andesite')
            elif radius<=5:
                clear(x,y,42,x,y,44)
                put(x,y,42,'iron_bars',dict(east='true',west='true',north='false',south='false',waterlogged='false'))
    # Crystal is a local vertical light well, never an exterior glass curtain wall.
    for x in range(11,32):
        for z in range(0,21):
            edge=abs(x-21)==10 or abs(z-10)==10
            if edge:box(x,49,z,x,64,z,'polished_andesite' if (x+z)%5==0 else 'light_blue_stained_glass')
            y=65+max(0,10-max(abs(x-21),abs(z-10)))//2
            put(x,y,z,'amethyst_block' if x==21 or z==10 else 'light_blue_stained_glass')
    tower(-1,-18,13,46,104,[46,64,82,100],roof=True)
    tower(-22,-47,10,-4,62,[16,32,48,60],roof=True)
    tower(-51,-43,10,-8,78,[0,32,48,64,76],roof=False)
    tower(67,4,11,-5,59,[-3,16,36,55],roof=True)
    # Low, irregular domestic wings sit below the raised archive/choir.
    hall('收容长屋',polygon([(-70,70),(-50,74),(-50,39),(-67,34)]),0,14,-59,7)
    hall('旧厨房',polygon([(-70,8),(-51,8),(-49,30),(-66,34),(-73,26)]),0,13,-61,7)
    box(-72,7,13,-69,31,16,'stone_bricks') # offset kitchen chimney
    clear(-71,30,14,-70,31,15)
    # Choir has a polygonal apse, paired aisles, a tall empty nave and transverse ribs.
    choir=polygon([(-10,48),(16,48),(29,58),(29,78),(14,89),(-10,80)])
    hall('失声唱诗堂',choir,16,38,7,14)
    for z in(53,62,71,79):
        for x in(-5,19):
            box(x,17,z,x+1,34,z+1,'polished_andesite')
        for x in range(-4,20):
            y=33+min(x+4,19-x)//2
            box(x,y,z,x,y+1,z+1)
    for x in range(-6,24,5):
        for z in(58,64,70,76):
            if 3<=x<=11:continue
            stair(x,17,z,'north',n='spruce_stairs')
    # Choir west lean-to, east open arcade, and a small apse dais.
    for x in range(-13,-9):
        for z in range(51,78):put(x,27+(x+13),z,'deepslate_tiles')
    for x,z in choir:
        if z>=80:put(x,17,z,'polished_andesite')
    for z in(53,62,71):
        clear(26,23,z,29,32,z+2)
        for yy in range(23,32):put(28,yy,z+1,'iron_bars',dict(east='false',west='false',north='true',south='true',waterlogged='false'))
    # Raised east garden/courtyard, with a lower inhabited passage underneath.
    box(31,15,47,59,16,71)
    for x in(31,59):
        for z in range(47,72):rail(x,17,z)
    for z in(47,71):
        for x in range(31,60):rail(x,17,z)
    hall('维修长廊',polygon([(59,19),(76,19),(76,72),(59,72)]),-4,29,67,7)
    for z in(24,39,54,69):
        for x in(59,76):
            clear(x,1,z,x,12,z+4)
            box(x,13,z,x,16,z+4)
    # East court contains an empty planter and one solitary seat, not a glass garden.
    for x in range(39,51):
        for z in range(63,69):
            if x in(39,50) or z in(63,68):put(x,17,z,'stone_brick_slab',dict(type='bottom',waterlogged='false'))
            else:put(x,16,z,'dirt')
    for x in(37,38,39):stair(x,17,51,'south',n='spruce_stairs')
    # Narrative props: occupied in layers, with deliberate empty places.
    for z in(42,49,56,63):
        box(-66,1,z,-63,1,z+1,'spruce_planks');box(-66,2,z,-63,2,z+1,'spruce_slab',dict(type='bottom',waterlogged='false'))
        barrel(-52,1,z);lamp(-52,2,z)
    box(-68,1,17,-66,3,22,'stone_bricks');box(-68,4,17,-66,4,22,'spruce_slab',dict(type='top',waterlogged='false'))
    for z in(19,22,25):barrel(-53,1,z)
    box(-64,1,25,-59,1,26,'spruce_planks');lamp(-61,2,25)
    box(71,17,45,72,18,48,'spruce_planks')
    for z in(44,47,50):barrel(73,17,z)
    for yy in(65,83):
        for z in range(-23,-12):put(-10,yy,z,'bookshelf')
        box(-8,yy,-25,-4,yy,-24,'spruce_planks');lamp(-6,yy+1,-25)
    for x,z in((-54,-48),(-48,-48),(-54,-38)):
        barrel(x,65,z)
    story('借来的床位',[-59,0,55],'旧驻军长屋只留下四组木床；每组旁边是一只不同位置的储物桶，走廊留空。床是木构造景，不具备重生点功能。')
    story('熄火的厨房',[-60,0,21],'烟囱与炉台还在，桌上只留一盏灯。回廊上方能看到厨房的低屋顶，先看见生活痕迹，再进入藏谱室。')
    story('失声唱诗堂',[8,16,68],'成排座椅向北面向音乐内堡，中央保留空席和高挑中殿。乐声来自墙后的机器，不在每张座位旁增设音符盒。')
    story('空土庭',[45,16,58],'封闭石墙间的一块未栽种土床；在这里向下看维修长廊，向上看高塔，让内外层级再次重合。')
    story('守曲人的工台',[70,16,46],'工具台与材料桶靠墙，下一段楼梯通往真正的机器，而不是装饰性的死胡同。')
    story('最后的合唱',[21,-3,4],'站在集中试听平台，上下六层音乐模块同时围绕你。晶体只从主堡顶部采光，厚石墙保留音乐机完整空间。')
    story('未送出的谱',[-6,64,-24],'塔上少量书架和书桌，与下层完整藏谱室形成差异。这里是可到达的支路，不是另一座填满楼层的复制塔。')
    story('熄灭的烽台',[-51,76,-43],'露天台上没有发光火焰；箱桶表示守卫曾驻留。可从这里回望来时的桥、低门塔与中殿屋顶。')
    # New routes only connect to already-clear points of the immutable old sample.
    route('前庭—收容长屋—厨房—西阶',[(-38,0,74),(-38,0,76),(-59,0,76),(-59,0,55),(-59,0,34),(-60,0,34),(-60,0,21),(-52,0,21),(-52,0,43),(-47,0,43)],kind='main')
    route('回望悬桥—唱诗堂',[(-19,16,42),(-13,16,42),(-13,16,66),(8,16,66),(8,16,68)],kind='main')
    route('唱诗堂—空土庭—守曲人长廊',[(8,16,68),(8,16,58),(45,16,58),(67,16,58),(67,16,36)],kind='main')
    route('东侧长阶下降至音乐门厅',[(67,16,36),(65,16,36),(65,16,35),(65,1,20),(65,1,5)],kind='main')
    # A raised single-lane bridge passes OVER the old obstructing line, then descends.
    access=route('音乐门厅—避线高桥—中央试听位',[(65,1,5),(23,1,5),(19,-3,5),(19,-3,4),(21,-3,4)],width=1,kind='main')
    access_floors=route_cells(access['points'],1)
    electric={p for p,v in music.items() if v[0] in ('redstone_wire','repeater','redstone_wall_torch','redstone_torch','stone_button','note_block')}
    electric_halo={(x+dx,y+dy,z+dz) for x,y,z in electric for dx in(-1,0,1) for dy in(-1,0,1) for dz in(-1,0,1)}
    assert not access_floors&electric_halo
    route('空土庭返回前庭的常开环路',[(45,16,58),(45,16,76),(45,0,92),(45,0,96),(-11,0,96),(-11,0,77),(-19,0,77),(-19,0,74),(-38,0,74)])
    route('唱诗堂后殿纪念席',[(8,16,68),(8,16,79),(8,17,80),(8,17,84)],kind='deadend')
    # A genuine stair wraps beyond the north archive, rather than puncturing its roof.
    route('藏谱南廊—外墙阶—北塔', [(-31,16,19),(-65,16,19),(-65,16,15),(-65,32,-1),(-65,32,-22),(-22,32,-22),(-22,32,-47)])
    route('北塔—主堡屋顶步道', [(-22,32,-47),(-22,32,-55),(-17,32,-55),(-17,32,-52),(-17,48,-36),(-17,48,-31),(-22,48,-31),(-22,48,-47)])
    route('北塔—烽台下廊', [(-22,48,-47),(-51,48,-47),(-51,48,-43)])
    for base in (48,64):
        half=8 if base==48 else 6
        route(f'烽塔 {base}→{base+2*half} 层',[(-51,base,-43),(-51,base,-33),(-47,base,-33),(-47,base,-36),(-47,base+half,-36-half),(-47,base+half,-39-half),(-55,base+half,-39-half),(-55,base+half,-36-half),(-55,base+2*half,-36),(-55,base+2*half,-33),(-51,base+2*half,-33),(-51,base+2*half,-43)])
    route('北塔—偏置冠塔入口',[(-22,48,-47),(-22,48,-33),(-14,48,-33),(-14,48,-30),(-14,46,-28),(-14,46,-25),(-1,46,-25),(-1,46,-18)])
    for base in (46,64,82):
        route(f'冠塔 {base}→{base+18} 层',[(-1,base,-18),(-1,base,-6),(4,base,-6),(4,base,-9),(4,base+9,-18),(4,base+9,-27),(-6,base+9,-27),(-6,base+9,-18),(-6,base+18,-9),(-6,base+18,-6),(-1,base+18,-6),(-1,base+18,-18)])
    for base,span in((16,10),(36,9)):
        route(f'维修塔 {base}→{base+span*2} 层',[(67,base,36),(71,base,36),(71,base,13),(71,base+span,13-span),(71,base+span,10-span),(63,base+span,10-span),(63,base+span,13-span),(63,base+2*span,13),(63,base+2*span,16),(67,base+2*span,16),(67,base+2*span,36)])
    # Retaining curtain rises and falls with ground: major breaks at towers and entries.
    for z in range(-58,72):
        for x in(-79,83):
            top=9 if z>0 else 16
            box(x,-15,z,x+2,top,z)
            if z%4<2:box(x,top+1,z,x+2,top+3,z)
    for x in range(-57,66):
        z=-68
        box(x,-14,z,x,18,z+2)
        if x%4<2:box(x,19,z,x,21,z+2)
    # Bridges, terraces and stairs receive three-high clearance together.
    floors={};air=set()
    for r in routes:
        for p in route_cells(r['points'],r['width']):floors.setdefault(p,None)
        for a,b in zip(r['points'],r['points'][1:]):
            if a[1]==b[1]:continue
            low,high=(a,b) if a[1]<b[1] else (b,a)
            facing=DIRECTIONS[high[0]-low[0],high[2]-low[2]]
            for p in route_cells([a,b],r['width']):
                if p[1]==high[1]:floors[p]=facing
        for x,y,z in route_cells(r['points'],r['width']):air.update((x,y+d,z) for d in(1,2,3))
    assert not set(floors)&air,('New routes intersect vertically',list(set(floors)&air)[:8])
    for p,facing in floors.items():
        if p in music:raise ValueError(f'Visitor floor intersects immutable music {p}')
        if protected(p):
            if p in access_floors:
                interior[p]=('stone_brick_stairs',dict(facing=facing,half='bottom',shape='straight',waterlogged='false'),'shell') if facing else ('stone_bricks',{},'shell')
            elif p not in interior:raise ValueError(f'New floor in protected music space {p}')
        elif facing:stair(*p,facing)
        else:put(*p)
    old_clash=set(air)&set(old)
    if old_clash:raise ValueError(f'Visitor clearance intersects old unit: {[(p,old[p][0]) for p in sorted(old_clash)][:24]}')
    for p in air:
        if p in music:raise ValueError(f'Visitor clearance intersects music {p}')
        if p in interior and p in electric_halo:raise ValueError(f'Removing an electrical neighbor from core {p}')
        blocks.pop(p,None);interior.pop(p,None)
    # Hand-designed guard edges for the raised music bridge. No new conducting
    # neighbor or downward pier is allowed inside the music reservation.
    access_rails={(x,2,z) for x in range(23,66) for z in(4,6)}
    access_rails.update([(18,-2,4),(18,-2,5),(19,-2,3),(19,-2,6),(20,-2,3),(20,-1,6),(21,-2,3),(21,0,6),(22,1,4),(22,1,6)])
    access_rails={p for p in access_rails if p not in air and p not in floors and (p[0],p[1]+1,p[2]) not in floors}
    assert not access_rails&electric_halo
    for x,y,z in access_rails:
        p=(x,y,z);assert p not in music
        interior[p]=('stone_brick_wall',dict(up='true',east='none',west='none',north='none',south='none',waterlogged='false'),'shell')
        below=(x,y-1,z)
        if below not in electric_halo and below not in air and below not in floors and below not in music:
            interior[below]=('stone_bricks',{},'shell')
    # Guard exposed new walking edges; all reserved walking cells take precedence.
    for r in routes:
        if r['width']==1:continue # inherited listening bridge must not gain conducting rails
        for a,b in zip(r['points'],r['points'][1:]):
            along_x=a[0]!=b[0];half=r['width']//2+1
            for x,y,z in(a,b):
                for j in(-half,half):
                    p=(x if along_x else x+j,y,z+j if along_x else z);q=(p[0],y+1,p[2])
                    if p in air or p in floors or q in air or q in floors or p in old or q in old:continue
                    if q in blocks and blocks[q][0] not in ('stone_brick_wall',):continue
                    put(*p);rail(*q)
    # Piers under new bridges, with open space between bays.
    for r in routes:
        if r['name'].startswith(('回望悬桥','北塔—','空土庭返回')):
            for x,y,z in r['points'][::9]:
                for yy in range(-4,y):
                    p=(x,yy,z)
                    if p not in air and p not in floors and p not in old:put(*p)
    # Do not fill the old well shaft or any old route's air with new work.
    for p in list(blocks):
        x,y,z=p
        if -31<=x<=-25 and -11<=y<=15 and 38<=z<=46:blocks.pop(p)
    for r in previous['routes']:
        for x,y,z in route_cells(r['points'],r['width']):
            for dy in(1,2,3):blocks.pop((x,y+dy,z),None)
    blocks.update(interior);blocks.update(old);blocks.update(music)
    signal=verify_rising_signal(relocate_music(modules),blocks,lambda i,p:shift(transform(i,p)))
    # Update only new rail states, leaving the previous gate/west bytes unchanged.
    for p,(n,props,g) in list(blocks.items()):
        if p in old or n!='stone_brick_wall':continue
        props=dict(props)
        for side,(dx,dz) in zip(('east','west','south','north'),DIRECTIONS):
            props[side]='low' if (p[0]+dx,p[1],p[2]+dz) in blocks else 'none'
        blocks[p]=(n,props,g)
    moved_placement=[]
    for item in placement:
        i=item['module'];h=6 if i==11 else 9
        moved_placement.append(dict(module=i,baseY=item['baseY']-32,north=item['north'],rotation=item['rotation'],
                                    originalInputPosition=list(shift(item['buttonDesign'])),
                                    testButton=list(shift(transform(i,(19,h,2) if i==1 else (18,h,1))))))
    return dict(blocks=blocks,routes=previous['routes']+routes,shortcuts=previous['shortcuts'],rooms=rooms,
                markers=previous['markers']+[dict(name=r['name'],pos=r['pos']) for r in rooms],
                connections=translate_connections(connections),placement=moved_placement,signal=signal,
                originalMusic=original,previousBlocks=old,
                integration=dict(preservedGateWestBlocks=len(old),relocatedMusicBlocks=len(music),musicShift=[0,-32,0],newRouteCount=len(routes)))
