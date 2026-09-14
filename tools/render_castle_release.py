"""Four actual V17 geometry images for the portable construction book."""
from PIL import Image,ImageDraw,ImageFont
from castle_release import SOURCE,OUT
from castle_detail import read_model
from vanilla_mesh import VanillaAssets,render

def main():
    _,blocks=read_model(SOURCE);assets=VanillaAssets();OUT.mkdir(exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',30)
    def draw(file,title,subtitle,region,angle,w=2400,h=1850):
        im=Image.new('RGB',(w,h),'#eee8db');d=ImageDraw.Draw(im)
        d.text((35,25),title,font=font,fill='#405948');d.text((35,78),subtitle,font=font,fill='#6c7665')
        im.paste(render(assets,blocks,region,w-40,h-170,angle),(20,145));im.save(OUT/file)
        print(file,flush=True)
    draw('01_全堡南东.png','余响堡｜V17完整方块 · V18施工包','189×170×267；原版模型与纹理离线渲染，非游戏截图。',(-90,98,-48,121,-84,182),35)
    draw('02_全堡西南.png','余响堡｜从西侧回望层叠屋面','完整方块，无新改型；光照、自动连接与游戏更新仍需验收。',(-90,98,-48,121,-84,182),145)
    draw('03_唱诗堂剖面.png','唱诗堂｜空席与后殿','裁切 X-9…25 / Y15…29 / Z55…87；完整模型仍有屋顶。',(-9,25,15,29,55,87),210,2200,1650)
    draw('04_音乐内堡剖面.png','音乐内堡｜六层，十一段乐曲','裁切 X-8…50 / Y-35…43 / Z-37…4；南侧围护未画。',(-8,50,-35,43,-37,4),35,2200,1900)

if __name__=='__main__':main()
