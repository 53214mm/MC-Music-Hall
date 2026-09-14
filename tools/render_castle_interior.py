"""V13 real block cuts and exact room-route coordinate maps; no game screenshots."""
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from castle_front import route_cells
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/interior_v13'


def main():
    d,b=read_model(ROOT/'castle_v3/light_v12/castle_v12.json');full,a=read_model(OUT/'castle_v13.json');assets=VanillaAssets()
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    scenes=[('01_长屋床位对照.png',(-68,-57,0,4,39,67),25,'长屋：低木床、不同织物与可进入的床边'),
            ('02_厨房内饰对照.png',(-69,-53,0,5,10,26),25,'厨房：熄火炉、薄台面与工作灯'),
            ('03_下厅桌柜对照.png',(-45,-33,16,23,4,13),-25,'下厅：挑空下的整理桌与待归档柜'),
            ('04_上廊书柜对照.png',(-47,-40,32,38,-9,8),30,'上廊：外侧归档柜，旧灯和内栏杆不挪动')]
    for filename,r,angle,title in scenes:
        im=Image.new('RGB',(2400,1450),'#eee8db');draw=ImageDraw.Draw(im)
        draw.text((30,22),'V13 生活与藏谱｜'+title,font=font,fill='#39453a')
        draw.text((30,70),f'裁切 X={r[0]}…{r[1]} / Y={r[2]}…{r[3]} / Z={r[4]}…{r[5]}；上方屋顶与裁切外内容仍在完整模型中。非游戏截图。',font=small,fill='#687461')
        for key,model,x,label in [('before',b,20,'V12 · 原内饰'),('after',a,1220,'V13 · 家具与室内入口')]:
            draw.text((x+15,116),label,font=font,fill='#465740')
            im.paste(render(assets,model,r,1150,1230,angle),(x,174));print(filename,key,flush=True)
        im.save(OUT/filename)
    r=(-47,-20,16,37,-9,12)
    im=Image.new('RGB',(2400,1600),'#eee8db');draw=ImageDraw.Draw(im)
    draw.text((34,24),'藏谱室剖视｜下厅整理桌在真实挑空内，上廊绕其上方回环',font=font,fill='#39453a')
    draw.text((34,74),'裁切 X=-47…-20 / Y=16…37 / Z=-9…12；保留两层楼板、内栏杆和本裁切内所有方块。顶部屋顶剖去，非游戏截图。',font=small,fill='#687461')
    im.paste(render(assets,a,r,2300,1390,30),(50,136));im.save(OUT/'05_藏谱上下层剖视.png');print('stacked section ready',flush=True)
    im=Image.new('RGB',(2600,1540),'#eee8db');draw=ImageDraw.Draw(im)
    draw.text((36,22),'室内通路定位｜绿色为新增实走路线，蓝色为保留主路，橙框为拆开的室内栏杆',font=font,fill='#39453a')
    draw.text((36,72),'俯视：X向右、Z向下；采样层为支撑上方1格。每步检查真实地板和三格净空，图示不是穿墙箭头。',font=small,fill='#687461')
    old={(x,y+1,z) for r0 in d['routes'] for x,y,z in route_cells(r0['points'],r0['width'])}
    new={(x,y+1,z) for r0 in full['interiorV13']['routes'] for x,y,z in r0['points']}
    openings={tuple(p) for p in full['interiorV13']['openings']}
    for title,r,foot,ox,oy,scale in [('收容长屋 · 脚部Y=1',(-68,-57,39,67),1,60,160,35),('厨房 · 脚部Y=1',(-69,-53,10,26),1,670,160,40),('藏谱下厅 · 脚部Y=17',(-45,-30,4,13),17,1540,160,47)]:
        draw.text((ox,oy),title,font=font,fill='#41573d');top=oy+65
        for x in range(r[0],r[1]+1):draw.text((ox+(x-r[0])*scale+1,top-26),str(x),font=small,fill='#697961')
        for z in range(r[2],r[3]+1):
            draw.text((ox-34,top+(z-r[2])*scale+6),str(z),font=small,fill='#697961')
            for x in range(r[0],r[1]+1):
                p=x,foot,z;s=a.get(p);q=(ox+(x-r[0])*scale,top+(z-r[2])*scale)
                color='#c0baa6' if s else '#f7f2e5' if (x,foot-1,z) in a else '#494b48'
                if p in old:color='#9fbec4'
                if p in new:color='#66986b'
                draw.rectangle((q[0],q[1],q[0]+scale-2,q[1]+scale-2),fill=color)
                if p in openings:draw.rectangle((q[0],q[1],q[0]+scale-2,q[1]+scale-2),outline='#cc782e',width=4)
        end=top+(r[3]-r[2]+1)*scale+20
        labels=['床边三个支路，不拆灯柱','厨房从原主路进出，形成一圈','桌位在挑空内；从主路转入']
        draw.text((ox,end),labels[['收容长屋 · 脚部Y=1','厨房 · 脚部Y=1','藏谱下厅 · 脚部Y=17'].index(title)],font=small,fill='#52634b')
    draw.text((670,1120),'灰格：该层有方块；浅格：有原地板的空气；深格：该层下方无支撑。',font=small,fill='#53664b')
    draw.text((670,1160),'5个开口均只拆室内Y1栏杆格；周边同高地板保持。新通路宽1格，不作为运输大车道。',font=small,fill='#53664b')
    draw.text((670,1200),'上廊继续使用旧路线，书柜靠外侧，中央挑空与S2旧梯井不变。',font=small,fill='#53664b')
    draw.text((670,1270),'此图检查的是几何与登记路径；尚未进行游戏碰撞、连接更新或灯光实测。',font=small,fill='#53664b')
    im.save(OUT/'06_室内通路定位.png');print('room circulation map ready',flush=True)


if __name__=='__main__':main()
