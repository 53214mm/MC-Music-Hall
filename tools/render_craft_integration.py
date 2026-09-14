"""Texture/model-based same-camera comparisons of the saved V6 and V7 models."""
import sys
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/integration_v7'
FONT='C:/Windows/Fonts/msyh.ttc'


def main():
    _,before=read_model(ROOT/'castle_v3/finish_v6/castle_v6.json');_,after=read_model(OUT/'castle_v7.json')
    assets=VanillaAssets();models={k:{p:s for p,s in b.items() if s[2] in ('shell','terrain')} for k,b in [('before',before),('after',after)]}
    allp=set(before)|set(after);region=tuple(v for i in range(3) for v in (min(p[i] for p in allp),max(p[i] for p in allp)))
    font=ImageFont.truetype(FONT,28);small=ImageFont.truetype(FONT,18)
    far=[] if '--near-only' in sys.argv else [('01_整堡南东对照.png',35,'从南东看：唱诗堂与主堡'),('02_整堡西南对照.png',-35,'从西南看：门楼、生活翼与高塔')]
    for filename,angle,title in far:
        img=Image.new('RGB',(2400,1560),'#eee8db');d=ImageDraw.Draw(img)
        d.text((28,20),'V7 第一轮整堡接入｜'+title,font=font,fill='#3c4239')
        d.text((28,68),'左右使用相同原版模型、纹理、相机和尺度；显示建筑与岩体。不是游戏截图，尚未完成全部立面精修。',font=small,fill='#767967')
        for key,x,label in [('before',20,'V6 · 原底稿'),('after',1220,'V7 · 暖石饰面、砖墙与首批异形构件')]:
            d.text((x+10,112),label,font=font,fill='#414c3f')
            img.paste(render(assets,models[key],region,1160,1360,angle),(x,166))
            print(filename,key,'ready',flush=True)
        img.save(OUT/filename)
    scenes=[('03_长窗接入近景.png',(-8,10,5,38,39,47),22,'主堡南窗｜薄窗套、细窗棂、退后的玻璃','为露出主堡窗跨，此处剖去Z≥48的唱诗堂前景；不是整堡正面。'),
            ('04_唱诗堂屋面近景.png',(-15,33,37,61,49,81),55,'唱诗堂屋面｜接入东坡变坡老虎窗','实际周边屋坡一同显示；对应东坡Z=71的新构件，另有西坡Z=58一组。'),
            ('05_生活翼接入近景.png',(-57,-43,0,25,51,71),70,'收容长屋｜外挑窗与半格托架','显示长屋东墙、屋檐和新木窗；局部铜帽不替换生活翼的整片深色主屋面。')]
    for filename,r,angle,title,note in ([] if '--far-only' in sys.argv else scenes):
        img=Image.new('RGB',(2000,1360),'#eee8db');d=ImageDraw.Draw(img)
        d.text((28,20),title,font=font,fill='#3c4239');d.text((28,66),note,font=small,fill='#767967')
        for key,x,label in [('before',20,'V6'),('after',1020,'V7 第一轮')]:
            d.text((x+10,110),label,font=font,fill='#414c3f');img.paste(render(assets,models[key],r,950,1170,angle),(x,170))
        img.save(OUT/filename);print(filename,'ready',flush=True)


if __name__=='__main__':main()
