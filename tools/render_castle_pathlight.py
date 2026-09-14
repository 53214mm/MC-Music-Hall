"""Real-model V12 construction crops, including music; numerical light graph."""
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from castle_pathlight import pathlight_audit
from vanilla_mesh import VanillaAssets,render

OUT=ROOT/'castle_v3/light_v12'


def main():
    data,b=read_model(ROOT/'castle_v3/detail_v11/castle_v11.json');_,a=read_model(OUT/'castle_v12.json')
    # No filtering away notes/control in the music crop: show real neighbors.
    models={'before':b,'after':a};assets=VanillaAssets()
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',28);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',18)
    scenes=[
        ('01_试听走廊梁下灯.png',(16,46,-5,16,3,7),15,'试听位与高桥：三盏梁下灯，不改邻近音乐',2600,1220),
        ('02_前庭落差端柱灯.png',(-55,-42,-9,5,77,91),35,'前庭落差：暖灯接原栏杆柱',2200,1360),
        ('03_南入口坡道双灯.png',(-50,-36,-31,-14,162,180),-30,'南入口：双灯顺应原地表高差',2200,1360)]
    for filename,r,angle,title,w,h in scenes:
        im=Image.new('RGB',(w,h),'#eee8db');d=ImageDraw.Draw(im)
        d.text((28,20),'V12 入口与试听走廊｜'+title,font=font,fill='#3c4239')
        d.text((28,68),f'裁切 X={r[0]}…{r[1]} / Y={r[2]}…{r[3]} / Z={r[4]}…{r[5]}；保留附近音乐/控制。图边不是真正切口，非游戏截图。',font=small,fill='#727865')
        for key,x,label in [('before',20,'V11 · 原灯位'),('after',w//2+20,'V12 · 只添灯、链和端柱灯座')]:
            d.text((x+10,112),label,font=font,fill='#414c3f')
            im.paste(render(assets,models[key],r,w//2-50,h-190,angle),(x,166));print(filename,key,'ready',flush=True)
        im.save(OUT/filename)
    report,fields=pathlight_audit()
    im=Image.new('RGB',(2400,1360),'#eee8db');d=ImageDraw.Draw(im)
    d.text((42,24),'照明采样对照｜沿用同一六邻域代理，不是游戏光照或刷怪验收',font=font,fill='#39493e')
    d.text((42,75),'35条登记路线全宽，支撑上方一格；6,331个去重采样点。新增7盏灯，原方块全部保留。',font=small,fill='#687461')
    for i,(label,old,new) in enumerate([('零值点',28,0),('低于5的点数',87,24),('最低代理值',0,3),('原28个零点','0','8～12')]):
        x=42+i*590;d.rectangle((x,126,x+555,266),fill='#f8f3e7')
        d.text((x+24,147),label,font=small,fill='#62745f');d.text((x+24,192),f'{old} → {new}',font=font,fill='#344e3c')
    route=next(r for r in data['routes'] if r['name']=='音乐门厅—避线高桥—中央试听位')
    points=[(x,y+1,z) for x,y,z in route['points']]
    d.text((100,316),'音乐门厅 → 避线高桥 → 中央试听位：按实际路线顺序的采样',font=font,fill='#3b5140')
    x0,x1,y0,y1=120,2280,404,1074
    def at(i,v):return x0+(x1-x0)*i/(len(points)-1),y1-(y1-y0)*v/15
    d.rectangle((x0,y0,x1,y1),fill='#f8f5e9')
    for v in range(0,16):
        yy=at(0,v)[1];d.line((x0,yy,x1,yy),fill='#d0d4c8' if v!=5 else '#bc8c46',width=1 if v!=5 else 2)
        d.text((75,yy-11),str(v),font=small,fill='#61765c')
    for key,color,offset,label in [('before','#818899',0,'V11'),('after','#a86628',240,'V12')]:
        vs=[fields[key].get(p,0) for p in points];xy=[at(i,v) for i,v in enumerate(vs)]
        d.line(xy,fill=color,width=5)
        for x,y in xy:d.ellipse((x-4,y-4,x+4,y+4),fill=color)
        d.line((1420+offset,338,1470+offset,338),fill=color,width=5);d.text((1482+offset,324),label,font=small,fill=color)
    for i in [0,10,20,30,40,len(points)-1]:
        xx=at(i,0)[0];d.line((xx,y1,xx,y1+9),fill='#62765c')
        d.text((xx-40,y1+18),str(i+1)+'号',font=small,fill='#53674e')
        d.text((xx-66,y1+49),str(points[i]),font=small,fill='#6d7966')
    d.text((120,1205),'音乐路线最低0 → 5，平均4.42 → 9.98；全路线无变暗点。数值5仅为观察参考线，不是生物生成阈值。',font=small,fill='#4f634a')
    d.text((120,1245),'剩余24个全路线低值点为3～4，另附坐标；尚未检查全堡每个角落、游戏连接更新或实际音乐播放。',font=small,fill='#4f634a')
    d.text((120,1285),'算法将不透明异形方块按整格遮挡，无天空光、反射或真实游戏光照；不通过换算法制造改善。',font=small,fill='#4f634a')
    im.save(OUT/'04_照明采样对照_非游戏实测.png');print('route proxy graph ready',flush=True)


if __name__=='__main__':main()
