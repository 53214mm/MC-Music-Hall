"""Draw an orthographic voxel-data diagram with Pillow, not a browser screenshot."""
import json
import math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageColor

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'castle_v3'/'detail_v4'
COLORS={'stone_bricks':'#9da28e','polished_andesite':'#c3c7b1','polished_andesite_slab':'#c3c7b1','stone_brick_stairs':'#a6ad95','stone_brick_slab':'#adb399','stone_brick_wall':'#a3ad93','chiseled_stone_bricks':'#b2b69e','mossy_stone_bricks':'#778664','cracked_stone_bricks':'#818b73','deepslate_tiles':'#354a3e','deepslate_tile_stairs':'#405042','deepslate_tile_slab':'#405042','deepslate_brick_wall':'#405042','gray_stained_glass_pane':'#4e5a50','iron_bars':'#5c6959','spruce_planks':'#866448','spruce_stairs':'#755b41','spruce_log':'#55412c','lantern':'#e4b761'}


def shape(n,p):
    if n.endswith('_slab'):return [(0,.5 if p.get('type')=='top' else 0,0,1,.5 if p.get('type')=='bottom' else 1,1)]
    if n.endswith('_stairs'):
        top=p.get('half')=='top';a,b=(0,.5) if top else(.5,1)
        second={'east':(.5,a,0,1,b,1),'west':(0,a,0,.5,b,1),'south':(0,a,.5,1,b,1),'north':(0,a,0,1,b,.5)}[p['facing']]
        return [(0,.5 if top else 0,0,1,1 if top else .5,1),second]
    if n.endswith('_glass_pane'):return [(0,0,.44,1,1,.56)] if p.get('east')=='true' else[(.44,0,0,.56,1,1)]
    if n.endswith('_wall'):return[(.25,0,.25,.75,1.5,.75)]
    if n=='iron_bars':return[(.44,0,0,.56,1,1),(0,0,.44,1,1,.56)]
    if n=='lantern':return[(.25,.1,.25,.75,.8,.75)]
    return[(0,0,0,1,1,1)]


def panel(payload,key,region,angle,width,height,facade=False):
    extras=set(map(tuple,payload['facadeExtras']));blocks={}
    for b in payload[key]['blocks']:
        p=tuple(b[i]-payload['offset'][i] for i in range(3))
        if not all(region[2*i]<=p[i]<=region[2*i+1] for i in range(3)):continue
        if facade and p[2]>47 and p not in extras:continue
        blocks[p]=payload[key]['palette'][b[3]]
    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    def raw(x,y,z):return(x*c-z*s,(x*s+z*c)*.42-y*.92)
    corners=[raw(x,y,z) for x in(region[0],region[1]+1) for y in(region[2],region[3]+1) for z in(region[4],region[5]+1)]
    lx,hx=min(p[0] for p in corners),max(p[0] for p in corners);ly,hy=min(p[1] for p in corners),max(p[1] for p in corners)
    scale=min((width-30)/(hx-lx),(height-30)/(hy-ly))
    def project(p):
        u,v=raw(*p);return((u-(lx+hx)/2)*scale+width/2,(v-(ly+hy)/2)*scale+height/2)
    solid={p for p,v in blocks.items() if shape(v[0],v[1])==[(0,0,0,1,1,1)]}
    faces=[]
    def face(p,vertices,color,shade,normal,boundary):
        if boundary and tuple(p[i]+normal[i] for i in range(3)) in solid:return
        world=[tuple(p[i]+v[i] for i in range(3)) for v in vertices];center=[sum(q[i] for q in world)/4 for i in range(3)]
        depth=(center[0]*s+center[2]*c)*.92+center[1]*.42
        rgb=ImageColor.getrgb(color);rgb=tuple(round(v*(1-shade)) for v in rgb)
        faces.append((depth,[project(q) for q in world],rgb))
    for p,(n,props,g) in blocks.items():
        color=COLORS.get(n,'#9ca48c')
        for a,l,d,A,H,B in shape(n,props):
            face(p,[(a,H,d),(A,H,d),(A,H,B),(a,H,B)],color,0,(0,1,0),H==1)
            face(p,[(A,l,d),(A,l,B),(A,H,B),(A,H,d)],color,.18,(1,0,0),A==1)
            face(p,[(a,l,B),(A,l,B),(A,H,B),(a,H,B)],color,.3,(0,0,1),B==1)
    img=Image.new('RGB',(width,height),'#dbe0d2');draw=ImageDraw.Draw(img)
    for _,points,color in sorted(faces,key=lambda f:f[0]):draw.polygon(points,fill=color)
    return img


def main():
    p=json.loads((OUT/'detail_comparison.json').read_text(encoding='utf-8'))
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',25);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',17)
    result=Image.new('RGB',(1600,1650),'#f0eee4');draw=ImageDraw.Draw(result)
    draw.text((35,22),'余响堡｜实际方块外饰对照',font=font,fill='#2f4234')
    draw.text((35,64),'同相机、同尺度。上排剖去前方唱诗堂；下排只看飞扶壁一跨。非游戏光影效果。',font=small,fill='#5b6d54')
    for key,left,label in [('before',20,'修改前'),('after',810,'外饰精修后')]:
        draw.text((left+15,106),label,font=font,fill='#2f4234')
        result.paste(panel(p,key,(-12,55,0,70,40,53),12,770,840,True),(left,145))
        result.paste(panel(p,key,(22,40,15,44,58,68),35,770,555),(left,1010))
    draw.text((35,1590),'窗框进深 / 石制窗棂 / 托石檐口 / 拱臂下方留空',font=font,fill='#344932')
    target=OUT/'外立面_实际方块对照.png';result.save(target)
    print(target)


if __name__=='__main__':main()
