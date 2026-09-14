"""Identical-camera comparisons of exact before/after blocks, no AI mockup."""
import argparse
from PIL import Image,ImageDraw,ImageFont
from castle_facade_v19 import OUT,SOURCE
from castle_detail import read_model
from vanilla_mesh import VanillaAssets,render

SCENES=[
 ('01_北东转角前后.png',(-31,85,-9,121,-74,32),145,'截图中的北墙与东侧：前后使用相同模型裁切/相机/尺度',3200,2250),
 ('02_北墙正面前后.png',(-1,52,-9,75,-49,-38),180,'北墙：两扇旧长窗保持，凸跨与盲拱填补上部空白',3200,2100),
 ('03_山墙接坡前后.png',(16,37,48,73,-47,-21),148,'中央山墙交接：原坡保留，新坡后收；两侧小窗见上图',3000,1800),
 ('04_东侧扶壁前后.png',(53,65,-9,54,-37,-10),94,'东侧：厚基脚逐段收窄，托石与薄檐间隔放置',2900,1900),
 ('05_整堡同角度前后.png',(-90,98,-48,121,-84,182),145,'整堡：与V18同一相机方向，旧灯/地表/音乐不变',3200,2200),
 ('06_盲拱退深与细部.png',(4,20,32,49,-44,-39),132,'盲拱近景：真实退一层，背后有实墙，非可穿行窗口',2800,1700)]

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--only',type=int,nargs='*');args=ap.parse_args()
    _,b=read_model(SOURCE);_,a=read_model(OUT/'castle_v19.json');assets=VanillaAssets()
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',30);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',22)
    for i,(name,r,angle,title,w,h) in enumerate(SCENES,1):
        if args.only and i not in args.only:continue
        im=Image.new('RGB',(w,h),'#eee8db');d=ImageDraw.Draw(im)
        d.text((30,18),'V19 北墙与转角精修｜'+title,font=font,fill='#425743')
        d.text((30,64),f'X{r[0]}…{r[1]} / Y{r[2]}…{r[3]} / Z{r[4]}…{r[5]}；仅模型裁切，不是拆墙范围或游戏截图。',font=small,fill='#777867')
        for x,m,label in [(20,b,'V18原模型'),(w//2+20,a,'V19精修候选')]:
            d.text((x+15,115),label,font=font,fill='#425743');im.paste(render(assets,m,r,w//2-40,h-195,angle),(x,180))
        im.save(OUT/name);print(name,flush=True)

if __name__=='__main__':main()
