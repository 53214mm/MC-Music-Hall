"""Actual vanilla model/texture views of saved V8 and V9, same camera."""
import sys
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/ground_v9'


def main():
    _,before=read_model(ROOT/'castle_v3/palette_v8/castle_v8.json');_,after=read_model(OUT/'castle_v9.json')
    models={k:{p:s for p,s in b.items() if s[2] in ('shell','terrain')} for k,b in [('before',before),('after',after)]}
    assets=VanillaAssets();font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    scenes=[]
    if '--near-only' not in sys.argv:scenes += [('01_整堡南东地表对照.png',(-90,98,-48,121,-84,182),35,'南东：暖色建筑落在土石地表上',True),('02_整堡西南地表对照.png',(-90,98,-48,121,-84,182),-35,'西南：墙根、前庭与外围地表衔接',True)]
    if '--far-only' not in sys.argv:scenes += [('03_入口地表近景.png',(-85,-5,-48,10,108,182),35,'入口坡道：浅石路面、裸土与苔色斑块',False)]
    for filename,region,angle,title,far in scenes:
        w,h,pw,ph=(2400,1560,1160,1360) if far else (2200,1460,1050,1260)
        img=Image.new('RGB',(w,h),'#eee8db');d=ImageDraw.Draw(img)
        d.text((28,20),'V9 地表单层换材｜'+title,font=font,fill='#3c4239')
        note='同原版纹理、相机和尺度；墙体与下面的岩壁保持，只换露天地表1格。不是游戏截图。' if far else '局部裁切 X=-85…-5 / Y=-48…10 / Z=108…182；截断建筑上部以显示地表，不是实际新增切口。'
        d.text((28,68),note,font=small,fill='#767967')
        for key,x,label in [('before',20,'V8 · 地表配色前'),('after',w//2+20,'V9 · 暖石铺地 / 黄褐裸土 / 局部苔色')]:
            d.text((x+10,112),label,font=font,fill='#414c3f')
            img.paste(render(assets,models[key],region,pw,ph,angle),(x,166));print(filename,key,'ready',flush=True)
        img.save(OUT/filename)


if __name__=='__main__':main()
