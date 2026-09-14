"""Same-shape, same-camera V7/V8 comparison, using actual Java block models."""
import sys
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/palette_v8'
FONT='C:/Windows/Fonts/msyh.ttc'


def main():
    _,before=read_model(ROOT/'castle_v3/integration_v7/castle_v7.json');_,after=read_model(OUT/'castle_v8.json')
    models={k:{p:s for p,s in b.items() if s[2] in ('shell','terrain')} for k,b in [('before',before),('after',after)]}
    assets=VanillaAssets();font=ImageFont.truetype(FONT,28);small=ImageFont.truetype(FONT,18)
    far=[] if '--near-only' in sys.argv else [
        ('01_整堡南东配色对照.png',(-90,98,-48,121,-84,182),35,'南东远景：暖褐主堡与砖红侧翼'),
        ('02_整堡西南配色对照.png',(-90,98,-48,121,-84,182),-35,'西南远景：门楼、长墙和高塔的色彩呼应')]
    near=[] if '--far-only' in sys.argv else [
        ('03_主堡窗墙配色近景.png',(-8,10,5,38,39,47),22,'主堡窗墙：浅色窗套嵌入暖褐墙身'),
        ('04_长墙塔身配色近景.png',(-86,-35,-2,70,-68,-27),-35,'西北长墙与烽塔：墙身、窗廊和压顶')]
    for filename,region,angle,title in far+near:
        is_far=(filename,region,angle,title) in far
        w,h,pw,ph=(2400,1560,1160,1360) if is_far else (2000,1360,950,1170)
        img=Image.new('RGB',(w,h),'#eee8db');d=ImageDraw.Draw(img)
        d.text((28,20),'V8 整堡配色扩展｜'+title,font=font,fill='#3c4239')
        note='同原版纹理、相机和尺度；只换同形材料，岩体与深灰屋顶保留。不是游戏截图。'
        if filename.startswith('03'):note='裁去Z≥48的唱诗堂前景以露出主堡窗跨；不是全堡新增切口，窗洞与形状未变。'
        if filename.startswith('04'):note='局部裁切 X=-86…-35 / Y=-2…70 / Z=-68…-27；不是整堡真实边界。'
        d.text((28,68),note,font=small,fill='#767967')
        for key,x,label in [('before',20,'V7 · 配色扩展前'),('after',w//2+20,'V8 · 暖褐墙身 / 砖红上层 / 浅色细构件')]:
            d.text((x+10,112),label,font=font,fill='#414c3f')
            img.paste(render(assets,models[key],region,pw,ph,angle),(x,166))
            print(filename,key,'ready',flush=True)
        img.save(OUT/filename)


if __name__=='__main__':main()
