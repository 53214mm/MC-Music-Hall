"""Render actual V6 block data and conservative illumination, never a game screenshot."""
import json
import math
from PIL import Image,ImageDraw,ImageFont,ImageColor
from castle_finish import COLORS,EMISSION,spread_light,ROOT
from render_castle_detail import shape as old_shape

OUT=ROOT/'castle_v3/finish_v6'
FONT='C:/Windows/Fonts/msyh.ttc'


def shape(n,p):
    if n=='iron_chain':return[(.43,0,.43,.57,1,.57)]
    return old_shape(n,p)


def panel(blocks,region,angle,width,height,night=False,field=None):
    selected={p:s for p,s in blocks.items() if all(region[2*i]<=p[i]<=region[2*i+1] for i in range(3))}
    c,s=math.cos(math.radians(angle)),math.sin(math.radians(angle))
    def raw(x,y,z):return x*c-z*s,(x*s+z*c)*.42-y*.92
    corners=[raw(x,y,z) for x in(region[0],region[1]+1) for y in(region[2],region[3]+1) for z in(region[4],region[5]+1)]
    lx,hx=min(p[0] for p in corners),max(p[0] for p in corners);ly,hy=min(p[1] for p in corners),max(p[1] for p in corners)
    scale=min((width-24)/(hx-lx),(height-24)/(hy-ly))
    def project(p):
        u,v=raw(*p);return (u-(lx+hx)/2)*scale+width/2,(v-(ly+hy)/2)*scale+height/2
    solid={p for p,v in selected.items() if shape(v[0],v[1])==[(0,0,0,1,1,1)]};faces=[]
    def face(p,vertices,n,color,shade,normal,boundary):
        neighbor=tuple(p[i]+normal[i] for i in range(3))
        if boundary and neighbor in solid:return
        world=[tuple(p[i]+v[i] for i in range(3)) for v in vertices];center=[sum(q[i] for q in world)/4 for i in range(3)]
        depth=(center[0]*s+center[2]*c)*.92+center[1]*.42
        rgb=ImageColor.getrgb(color)
        if night:
            emission=EMISSION.get(n,0);level=emission or max(field.get(neighbor,0),field.get(p,0))
            strength=.16+.84*(level/15)**1.2
            rgb=tuple(round(v*strength*(1-shade*.6)) for v in rgb)
            if emission:rgb=ImageColor.getrgb(COLORS.get(n,'#ffcf81'))
        else:rgb=tuple(round(v*(1-shade)) for v in rgb)
        faces.append((depth,[project(q) for q in world],rgb))
    for p,(n,props,g) in selected.items():
        color=COLORS.get(n,'#92998b')
        for a,l,d,A,H,B in shape(n,props):
            face(p,[(a,H,d),(A,H,d),(A,H,B),(a,H,B)],n,color,0,(0,1,0),H==1)
            face(p,[(A,l,d),(A,l,B),(A,H,B),(A,H,d)],n,color,.18,(1,0,0),A==1)
            face(p,[(a,l,B),(A,l,B),(A,H,B),(a,H,B)],n,color,.3,(0,0,1),B==1)
    im=Image.new('RGB',(width,height),'#101922' if night else '#d9ded5');d=ImageDraw.Draw(im)
    for _,points,col in sorted(faces,key=lambda f:f[0]):d.polygon(points,fill=col)
    return im


def main():
    p=json.loads((OUT/'finish_comparison.json').read_text(encoding='utf-8'))
    models={key:{tuple(b[i]-p['offset'][i] for i in range(3)):p[key]['palette'][b[3]] for b in p[key]['blocks']} for key in('before','after')}
    font=ImageFont.truetype(FONT,26);small=ImageFont.truetype(FONT,18)
    region=tuple(v for i in range(3) for v in(p['report']['designMin'][i],p['report']['designMax'][i]+2))
    img=Image.new('RGB',(2200,1260),'#ece9de');d=ImageDraw.Draw(img)
    d.text((28,20),'余响堡 V6｜材质按部位成片变化，补入实际灯具',font=font,fill='#354335')
    d.text((28,64),'同角度、同尺度的实际方块数据。没有游戏材质贴图；暖灰、深灰、浅色切石用于区分结构。',font=small,fill='#6c7767')
    for key,x,label in [('before',20,'V5｜单一石砖占大面，少量灯源'),('after',1120,'V6｜灰石、凝灰岩基座、木架填墙与灯位')]:
        d.text((x+10,107),label,font=font,fill='#3c4e40');img.paste(panel(models[key],region,35,1060,1070),(x,157))
    img.save(OUT/'V5_V6材质对照.png');print('Day comparison rendered.',flush=True)
    blocks=models['after'];sources={q:EMISSION[s[0]] for q,s in blocks.items() if s[0] in EMISSION};field=spread_light(blocks,sources)
    img=Image.new('RGB',(2000,1300),'#101922');d=ImageDraw.Draw(img)
    d.text((28,22),'V6｜实际灯源 + 简化遮光的夜间分布示意',font=font,fill='#e5d6b9')
    d.text((28,65),'非游戏截图 / 无天空光 / 部分方块保守按整格遮光 / 不能用于防刷怪验收',font=small,fill='#a9b5b4')
    img.paste(panel(blocks,region,35,1260,1130,True,field),(20,120))
    d.text((1300,130),'唱诗堂灯具特写（裁切）',font=font,fill='#e5d6b9')
    img.paste(panel(blocks,(-7,24,16,31,52,77),35,660,800,True,field),(1310,205))
    d.text((1325,1040),'暖色灯笼与灯龛：入口、回廊、塔楼',font=small,fill='#c0bda9')
    d.text((1325,1080),'海晶灯：音乐核心与其上方水晶灯井',font=small,fill='#c0bda9')
    d.text((1325,1120),'裁切边缘不代表建筑真实破口',font=small,fill='#899797')
    img.save(OUT/'V6夜间照明示意.png');print('Night diagram rendered.',flush=True)
    # Height bands avoid superposing every floor into one misleading light plan.
    data=json.loads((OUT/'castle_v6.json').read_text(encoding='utf-8'))
    img=Image.new('RGB',(1800,1430),'#eeebe1');d=ImageDraw.Draw(img)
    d.text((26,20),'V6｜按高度分开的真实灯位与已登记路线',font=font,fill='#3c4e40')
    d.text((26,64),'灰：该高度段建筑投影 / 橙：暖光灯源 / 蓝：海晶灯 / 绿：路线 / 红：静态模型暗点（需实机核查）',font=small,fill='#6b786b')
    for i,(lo,hi,label) in enumerate([(-48,-1,'地底与山道'),(0,15,'前庭与生活翼'),(16,35,'藏谱厅与唱诗堂'),(36,59,'上廊与塔楼'),(60,85,'高塔中段'),(86,130,'冠塔顶层')]):
        ox=20+(i%3)*595;oy=120+(i//3)*645
        d.rectangle((ox,oy,ox+570,oy+620),fill='#dce0d6');d.text((ox+14,oy+12),f'{label}  Y={lo}…{hi}',font=small,fill='#3d5042')
        def project(x,z):return ox+45+(x+95)*2.5,oy+60+(z+86)*1.95
        footprint={(x,z) for (x,y,z),s in blocks.items() if lo<=y<=hi and s[2]=='shell'}
        for x,z in footprint:
            u,v=project(x,z);d.rectangle((u,v,u+2,v+2),fill='#aeb7a7')
        for r in data['routes']:
            for x,y,z in r['points']:
                if lo<=y<=hi:
                    u,v=project(x,z);color='#bc6850' if field.get((x,y+1,z),0)==0 else '#5a816b';d.ellipse((u-1,v-1,u+1,v+1),fill=color)
        for (x,y,z),s in blocks.items():
            if lo<=y<=hi and s[0] in EMISSION:
                u,v=project(x,z);color='#a9dfe7' if s[0]=='sea_lantern' else '#e9ae51';d.ellipse((u-3,v-3,u+3,v+3),fill=color,outline='#655e49')
    img.save(OUT/'V6分层灯位图.png');print('Height-banded light map rendered.',flush=True)


if __name__=='__main__':main()
