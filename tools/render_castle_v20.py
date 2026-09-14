from PIL import Image,ImageDraw,ImageFont
from castle_v20 import SOURCE,OUT
from castle_detail import read_model
from vanilla_mesh import VanillaAssets,render

def main():
    _,before=read_model(SOURCE);_,after=read_model(OUT/'castle_v20.json');assets=VanillaAssets();font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28)
    scenes=[('01_完整转角对照.png',(-31,92,-16,121,-74,76),145,3200,2350,'V19 → V20；完整包含外城墙装饰，不再裁到X85'),
            ('02_东城墙扶垛.png',(82,90,-18,19,-45,18),112,2800,1550,'保留旧凹拱；间隔扶垛由三格厚基脚向上收分'),
            ('03_长廊凸窗.png',(74,80,14,34,27,67),104,2800,1750,'原墙保留，三组封闭凸窗与薄深色雨檐'),
            ('04_全堡总览.png',(-90,98,-48,121,-84,182),145,2600,2200,'V20完整模型；同一本施工总册的当前外观')]
    for name,r,angle,w,h,title in scenes:
        im=Image.new('RGB',(w,h),'#eee8db');dr=ImageDraw.Draw(im);dr.text((30,22),title,font=font,fill='#344d43');dr.text((30,65),'实际方块模型/纹理离线渲染，非游戏截图；不模拟真实照明。',font=font,fill='#5c665b')
        if name.startswith('04'):
            im.paste(render(assets,after,r,w-40,h-150,angle),(20,130))
        else:
            for x,m,label in [(20,before,'V19'),(w//2+20,after,'V20')]:
                dr.text((x,110),label,font=font,fill='#344d43');im.paste(render(assets,m,r,w//2-40,h-175,angle),(x,160))
        im.save(OUT/name);print(name,flush=True)

if __name__=='__main__':main()
