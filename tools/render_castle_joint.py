"""Real model comparisons and clearly labeled numeric light proxy section."""
import sys
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from castle_joint_lighting import lighting_audit
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/detail_v11'


def main():
    _,b=read_model(ROOT/'castle_v3/detail_v10/castle_v10.json');_,a=read_model(OUT/'castle_v11.json')
    models={k:{p:s for p,s in m.items() if s[2] in ('shell','terrain')} for k,m in [('before',b),('after',a)]}
    assets=VanillaAssets();font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    scenes=[]
    if '--near-only' not in sys.argv:scenes+=[('01_整堡南东窗廊对照.png',(-90,98,-48,121,-84,182),35,'整堡南东：适配窗廊与龛内暖灯',True),('02_整堡西南窗廊对照.png',(-90,98,-48,121,-84,182),-35,'整堡西南：保留轮廓与暖色材料',True)]
    if '--far-only' not in sys.argv:scenes+=[
        ('03_烽塔平台窗廊.png',(-58,-44,59,81,-38,-29),15,'烽塔：平台分隔窗廊与有支撑的侧灯',False),
        ('04_维修塔低拱窗.png',(60,74,40,62,10,21),15,'维修塔：低拱收在原登塔平台之下',False),
        ('05_长墙拱龛挂灯.png',(80,89,-1,18,-30,-14),70,'东长墙：龛顶铁链与暖色灯笼',False)]
    for filename,r,angle,title,far in scenes:
        w,h,pw,ph=(2400,1560,1160,1360) if far else (2200,1360,1050,1170)
        img=Image.new('RGB',(w,h),'#eee8db');d=ImageDraw.Draw(img)
        d.text((28,20),'V11 窗廊与暖灯｜'+title,font=font,fill='#3c4239')
        note='同原版模型/纹理、相机和尺度；不模拟夜景，不是游戏截图。' if far else f'局部裁切 X={r[0]}…{r[1]} / Y={r[2]}…{r[3]} / Z={r[4]}…{r[5]}；不是新增结构切口。'
        d.text((28,68),note,font=small,fill='#767967')
        for key,x,label in [('before',20,'V10 · 共用窗位保留原样'),('after',w//2+20,'V11 · 平台保持，窗框与挂灯适配')]:
            d.text((x+10,112),label if '长墙' not in title else ('V10 · 拱龛未加灯' if key=='before' else 'V11 · 每龛一盏顶挂灯'),font=font,fill='#414c3f')
            img.paste(render(assets,models[key],r,pw,ph,angle),(x,166));print(filename,key,'ready',flush=True)
        img.save(OUT/filename)
    if '--far-only' in sys.argv:return
    report,fields=lighting_audit()
    im=Image.new('RGB',(2200,1360),'#eee8db');d=ImageDraw.Draw(im)
    d.text((28,22),'拱龛照明剖面｜六邻域代理数值，不是游戏实测或夜景效果图',font=font,fill='#3c4239')
    d.text((28,74),'固定 Z=-22；X 向右，Y 向上。方格数字为代理值；实为不透明占用格，灯/链为实际方块。',font=small,fill='#666e60')
    # The actual source and front air lie in this plane, not projected from another slice.
    for key,ox,label in [('before',180,'V10：原凹龛'),('after',1280,'V11：加顶挂灯')]:
        d.text((ox,130),label,font=font,fill='#3d4b3b')
        for x in range(82,90):d.text((ox+(x-82)*86+24,182),str(x),font=small,fill='#646d5e')
        for y in range(18,-1,-1):
            yy=218+(18-y)*48;d.text((ox-45,yy+10),str(y),font=small,fill='#646d5e')
            for x in range(82,90):
                xx=ox+(x-82)*86;p=(x,y,-22);s=models[key].get(p);v=fields[key].get(p,0)
                if s and s[0] not in ('lantern','iron_chain'):
                    fill='#62695f';txt='实';textcolor='#e5e5d5'
                else:
                    t=v/15;fill=tuple(round(c+(e-c)*t) for c,e in zip((32,40,50),(247,193,92)))
                    txt='灯15' if s and s[0]=='lantern' else '链'+str(v) if s else str(v);textcolor='#222c29' if v>7 else '#e7e7dc'
                d.rectangle((xx,yy,xx+81,yy+44),fill=fill)
                d.text((xx+20,yy+10),txt,font=small,fill=textcolor)
    d.text((28,1170),'26个新拱龛灯前方的空气格均变亮；示例灯坐标(85,12,-22)，前方(86,12,-22)代理值14。',font=small,fill='#4f5f4d')
    d.text((28,1210),f'35条路线全宽：{report["after"]["samples"]}个去重采样点；零值仍{report["after"]["zero"]}、低于5仍{report["after"]["below5"]}，没有变暗点。外墙补灯不等于全堡照明完成。',font=small,fill='#4f5f4d')
    d.text((28,1250),'部分异形方块按整格遮挡；不含天空光、连接更新、反射或刷怪判定。音乐保护区未在本轮插灯。',font=small,fill='#4f5f4d')
    im.save(OUT/'06_拱龛照明剖面_非游戏实测.png');print('light section ready',flush=True)


if __name__=='__main__':main()
