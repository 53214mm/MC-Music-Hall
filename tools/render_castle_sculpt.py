"""V9/V10 real block-model comparisons, never an AI illustration or game screenshot."""
import sys
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/detail_v10'


def main():
    _,b=read_model(ROOT/'castle_v3/ground_v9/castle_v9.json');_,a=read_model(OUT/'castle_v10.json')
    models={k:{p:s for p,s in m.items() if s[2] in ('shell','terrain')} for k,m in [('before',b),('after',a)]}
    assets=VanillaAssets();font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    scenes=[]
    if '--near-only' not in sys.argv:scenes += [('01_整堡南东形状对照.png',(-90,98,-48,121,-84,182),35,'南东整堡：长墙与长檐的凹凸',True),('02_整堡西南形状对照.png',(-90,98,-48,121,-84,182),-35,'西南整堡：长墙、窗廊与山墙收口',True)]
    if '--far-only' not in sys.argv:scenes += [
        ('03_长墙拱龛近景.png',(80,89,-10,23,-30,-14),70,'东长墙：浅凹龛、薄拱框与收分扶垛',False),
        ('04_塔窗薄框近景.png',(-15,-8,44,65,-54,-40),75,'北阶塔东窗：厚外框改为墙状细柱与薄窗台',False),
        ('05_维修翼檐口近景.png',(72,78,25,38,30,59),70,'维修翼东檐：闭合接缝、木百叶与间隔托架',False),
        ('06_西翼山墙收边近景.png',(-52,-10,37,54,13,20),20,'西翼南山墙：顺屋坡的薄收边与木托',False)]
    for filename,r,angle,title,far in scenes:
        w,h,pw,ph=(2400,1560,1160,1360) if far else (2200,1360,1050,1170)
        img=Image.new('RGB',(w,h),'#eee8db');d=ImageDraw.Draw(img)
        d.text((28,20),'V10 外墙形状精修｜'+title,font=font,fill='#3c4239')
        note='同原版纹理、相机和尺度；保留V8墙体配色家族与V9地表。不是游戏截图。' if far else f'局部裁切 X={r[0]}…{r[1]} / Y={r[2]}…{r[3]} / Z={r[4]}…{r[5]}；图边界不是建筑真正的切口。'
        d.text((28,68),note,font=small,fill='#767967')
        for key,x,label in [('before',20,'V9 · 形状精修前'),('after',w//2+20,'V10 · 真正退让、薄构件与墙檐回接')]:
            d.text((x+10,112),label,font=font,fill='#414c3f');img.paste(render(assets,models[key],r,pw,ph,angle),(x,166));print(filename,key,'ready',flush=True)
        img.save(OUT/filename)


if __name__=='__main__':main()
