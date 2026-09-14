"""V17 exact-model near views and a labeled sightline plan."""
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from vanilla_mesh import VanillaAssets,render
from build_castle_watchrooms import OUT


def main():
    d,a=read_model(OUT/'castle_v17.json');_,b=read_model(ROOT/'castle_v3/story_v16/castle_v16.json');assets=VanillaAssets()
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',32);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
    def canvas(size,title,sub):
        im=Image.new('RGB',size,'#eee8db');dr=ImageDraw.Draw(im);dr.text((35,23),title,font=font,fill='#3f5846');dr.text((35,80),sub,font=small,fill='#6a785f');return im,dr
    def compare(name,title,sub,r,angle,size=(2800,1800)):
        im,dr=canvas(size,title,sub);half=size[0]//2
        for x,model,label in [(20,b,'V16 原布局'),(half+20,a,'V17 水痕与守望')]:
            dr.text((x+20,140),label,font=font,fill='#4a614c');im.paste(render(assets,model,r,half-40,size[1]-245,angle),(x,213))
        im.save(OUT/name);print(name,flush=True)
    compare('01_退水池西壁对照.png','蓄水池｜水痕只留在原因明确的位置',
        '同相机裁切 X-43…-23 / Y-13…-3 / Z33…52；地下顶板、东墙与主环路在完整模型中，非游戏截图。',(-43,-23,-13,-3,33,52),75,(2800,1800))
    im,dr=canvas((2800,1800),'堵塞与检水｜细拱、低石屑、空盆和后来补的木板','左为西壁进水口，右为井底检水角；不同裁切与比例，背墙和旧池底都真实保留。')
    for x,r,angle,title in [(25,(-43,-39,-12,-3,36,44),78,'进水格栅 X-43…-39 / Y-12…-3 / Z36…44'),(1420,(-33,-28,-13,-9,46,51),205,'检水角 X-33…-28 / Y-13…-9 / Z46…51')]:
        dr.text((x+15,143),title,font=small,fill='#49604b');im.paste(render(assets,a,r,1350,1460,angle),(x,245))
    im.save(OUT/'02_进水口与检水角.png');print('inlet detail rendered',flush=True)
    compare('03_烽塔双折观景台.png','烽塔｜先登高，才能回望来路',
        'X-61…-43 / Y75…87 / Z-51…-35，同裁切/相机；原塔墙与城垛保留。图裁去塔南段，非实机。',(-61,-43,75,87,-51,-35),150,(2800,2100))
    compare('04_冠塔薄抄谱台.png','冠塔｜原灯和旧书架留在原处',
        'X-12…-3 / Y63…70 / Z-27…-12，同相机裁切。空谱架、薄台面与后补木框，不含可读书本。',(-12,-3,63,70,-27,-12),60,(2700,1900))
    compare('05_北阶塔换岗角.png','北阶塔｜换岗的人停在通路一旁',
        'X-30…-18 / Y47…54 / Z-55…-45，同相机裁切；主路、塔墙和楼板不挪，非游戏截图。',(-30,-18,47,54,-55,-45),15,(2700,1800))
    im,dr=canvas((2800,1950),'巡检阁｜塔内Y55，外廊Y54，一阶真正接入','左为V17小修台；右为Z13局部阶梯剖面。不同裁切/比例，Z14旧实墙与窗廊不拆。')
    dr.text((45,142),'巡检阁 X62…74 / Y53…61 / Z-2…16',font=font,fill='#49604b')
    im.paste(render(assets,a,(62,74,53,61,-2,16),1350,1570,220),(25,240))
    dr.text((1450,142),'接入剖面 X62…67 / Y53…56 / Z12…13',font=font,fill='#49604b')
    im.paste(render(assets,a,(62,67,53,56,12,13),1310,1200,190),(1440,265))
    for y,s in [(1550,'旧(64,54,13) → 新(65,55,13)东向下半楼梯。'),(1610,'Y55原木楼板继续向塔内延伸；不是悬空箭头。'),(1700,'旧路全宽及三格空气保持；图中未裁入的外墙仍在。'),(1770,'须在创造档复核真实楼梯半格表面与双向行走。')]:dr.text((1440,y),s,font=small,fill='#677860')
    im.save(OUT/'06_巡检阁与一阶接入.png');print('maintenance rendered',flush=True)
    im,dr=canvas((2000,2000),'守望位置｜回望东门塔，辨认唱诗堂屋脊','实际完整模型的屋顶俯视与占用格视线检查；X向右、Z向下，不是第一人称游戏截图。')
    x0,x1,z0,z1=-72,40,-60,125;scale=8;ox=95;oz=240
    tops={}
    for (x,y,z),s in a.items():
        if x0<=x<=x1 and z0<=z<=z1 and s[2]!='terrain' and ((x,z) not in tops or y>tops[x,z][0]):tops[x,z]=(y,s[0])
    for (x,z),(y,n) in tops.items():
        color=d['colors'].get(n,'#aaa68c');dr.rectangle((ox+(x-x0)*scale,oz+(z-z0)*scale,ox+(x-x0+1)*scale-1,oz+(z-z0+1)*scale-1),fill=color)
    point=lambda p:(ox+(p[0]-x0)*scale,oz+(p[2]-z0)*scale)
    for i,v in enumerate(d['watchV17']['sightlines']):
        u,w=point(v['eye']),point(v['target']);color=['#923f43','#436f72'][i]
        dr.line((u,w),fill=color,width=5)
        for X,Y in(u,w):dr.ellipse((X-8,Y-8,X+8,Y+8),fill=color)
        dr.text((1090,400+i*280),v['name'],font=font,fill=color)
        dr.text((1090,455+i*280),'目标方块 '+str(tuple(v['targetBlock'])),font=small,fill='#677860')
        dr.text((1090,500+i*280),'射线至该方块顶面上方：无占用格阻挡',font=small,fill='#677860')
    for y,s in [(185,'观景点地板 (-57,84,-40)'),(240,'脚底Y85；眼点 (-56.5,86.62,-39.5)'),(1080,'两条线只是视线，不是走路或铺桥。'),(1160,'铁栏、玻璃和楼梯按整格遮挡，'),(1205,'未通过纹理空隙让射线穿墙。'),(1300,'不含服务器额外的地形、树木和建筑。'),(1390,'只验证两个指定地标，不宣称360°无遮挡。'),(1530,'原Y76楼板、塔墙、城垛和登塔线保持。'),(1620,'平台一格高铁栏不能换成1.5格高墙/栅栏。')]:dr.text((1090,y),s,font=small,fill='#677860')
    im.save(OUT/'07_守望位置与地标.png');print('sightline plan rendered',flush=True)


if __name__=='__main__':main()
