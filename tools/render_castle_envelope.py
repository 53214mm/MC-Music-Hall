"""Actual voxel diagrams for V5, independent of browser rendering."""
import json
from PIL import Image,ImageDraw,ImageFont
from render_castle_detail import panel,COLORS,ROOT

OUT=ROOT/'castle_v3'/'envelope_v5'


def main():
    p=json.loads((OUT/'envelope_comparison.json').read_text(encoding='utf-8'))
    COLORS.update(stone='#879180',tuff='#758367',andesite='#929984',light_blue_stained_glass='#8fb9b8',amethyst_block='#9e87ac',sea_lantern='#dcecc1')
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',26);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',19)
    img=Image.new('RGB',(2200,1270),'#f0eee4');d=ImageDraw.Draw(img)
    d.text((35,22),'余响堡｜V4 → V5 外壳扩展',font=font,fill='#304433')
    d.text((35,66),'整堡：同角度、同尺度，无剖切；这是实际方块示意，不是游戏材质与光影截图。',font=small,fill='#68725d')
    for key,x,label in [('before',20,'上一版：已包含V4南立面'),('after',1120,'本次：侧墙、高塔与屋顶接缝')]:
        d.text((x+12,112),label,font=font,fill='#304433')
        img.paste(panel(p,key,(-90,98,-48,125,-84,181),35,1060,1060),(x,165))
    img.save(OUT/'整堡_实际方块对照.png');print('Whole-castle image ready.',flush=True)
    img=Image.new('RGB',(1800,2000),'#f0eee4');d=ImageDraw.Draw(img)
    d.text((35,22),'V5细部｜主堡侧墙与冠塔',font=font,fill='#304433')
    d.text((35,64),'同角度比较。特写按坐标裁切，裁切边缘不是实际建筑破口。',font=small,fill='#68725d')
    for key,x,label in [('before',20,'上一版 V4'),('after',920,'本次 V5')]:
        d.text((x+12,105),label,font=font,fill='#304433')
        img.paste(panel(p,key,(51,63,0,55,-34,35),65,860,825),(x,150))
        img.paste(panel(p,key,(-18,16,45,125,-35,-1),35,860,930),(x,1000))
    img.save(OUT/'侧墙与冠塔_实际方块对照.png');print('Close-up image ready.',flush=True)


if __name__=='__main__':main()
