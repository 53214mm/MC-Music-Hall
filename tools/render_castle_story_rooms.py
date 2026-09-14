"""V16 actual-model comparisons and exact room-path plans, not game screenshots."""
from PIL import Image,ImageDraw,ImageFont
from castle_detail import ROOT,read_model
from vanilla_mesh import VanillaAssets,render
from build_castle_story_rooms import OUT


def main():
    d,a=read_model(OUT/'castle_v16.json');_,b=read_model(ROOT/'castle_v3/service_v15/castle_v15.json');assets=VanillaAssets();meta=d['storyV16']
    font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',32);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',23)
    def canvas(size,title,sub):
        im=Image.new('RGB',size,'#eee8db');dr=ImageDraw.Draw(im);dr.text((35,23),title,font=font,fill='#3f5846');dr.text((35,80),sub,font=small,fill='#6a785f');return im,dr
    def compare(name,title,sub,r,angle,size=(2800,1800)):
        im,dr=canvas(size,title,sub);half=size[0]//2
        for x,model,label in [(20,b,'V15 原布局'),(half+20,a,'V16 本轮内饰')]:
            dr.text((x+20,138),label,font=font,fill='#4a614c')
            im.paste(render(assets,model,r,half-40,size[1]-235,angle),(x,208))
        im.save(OUT/name);print(name,flush=True)
    compare('01_唱诗堂长席对照.png','唱诗堂｜保留高厅，座席有疏密，中央通路保持',
            '同相机裁切 X-7…21 / Y16…40 / Z58…79；展示原柱列和拱肋，屋顶/后殿仍在完整模型中。非游戏截图。',(-7,21,16,40,58,79),8,(2800,2050))
    im,dr=canvas((2600,1600),'长席细部｜薄背、楼梯座与灯端座','左为东侧Z70长席；右为缩短的西南席。各自按标注裁切、非同一比例，均为V16实际方块。')
    for x,r,angle,title in [(25,(12,20,16,19,69,71),173,'东长席 X12…20 / Y16…19 / Z69…71'),
                             (1325,(-5,3,16,19,75,77),173,'西南短席 X-5…3 / Y16…19 / Z75…77')]:
        dr.text((x+10,141),title,font=font,fill='#466049');im.paste(render(assets,a,r,1250,1240,angle),(x,224))
    dr.text((45,1505),'座面朝北；Y18薄木背位于同格南侧，与下方朝南楼梯的高侧相接。端灯下面是实心切制砂岩。',font=small,fill='#6a785f')
    im.save(OUT/'02_薄背长席细部.png');print('pew detail rendered',flush=True)
    compare('03_侧后殿纪念龛.png','后殿独席｜少量新石、一盆花与空谱架',
            'X10…17 / Y17…27 / Z79…85，同裁切/相机；西侧主路不在本图中。讲台未放书，非游戏截图。',(10,17,17,27,79,85),178,(2500,1800))
    compare('04_维修工台对照.png','维修夹廊｜先补工作平台，再改工台与访问入口',
            'X65…75 / Y14…23 / Z40…52，同裁切/相机。东墙、三座原路灯保持；两处栏杆口接连续地板。',(65,75,14,23,40,52),300,(2700,1750))
    im,dr=canvas((2700,1900),'夹层与零件｜工作平台的下方仍然是空间','左图延伸到旧底层地板；右图近看木架与短铜件。不同裁切与比例，完整墙体不按截图拆除。')
    dr.text((40,143),'夹层剖视 X65…75 / Y-4…23 / Z40…52',font=font,fill='#466049')
    im.paste(render(assets,a,(65,75,-4,23,40,52),1310,1050,280),(30,220))
    dr.text((40,1310),'支撑层特写：只显示Y14…15，楼板未拆',font=font,fill='#466049')
    im.paste(render(assets,a,(69,74,14,15,41,51),1310,455,300),(30,1390))
    dr.text((1400,143),'零件架 X71…74 / Y16…23 / Z49…52',font=font,fill='#466049')
    im.paste(render(assets,a,(71,74,16,23,49,52),1260,1300,295),(1400,230))
    for y,text in [(1585,'Y15两道横梁接东墙，Y14倒楼梯托臂收住端头。'),(1640,'木板只补工作夹层，下面不填成实心墙。'),(1695,'铜件/铁栏是静态备用零件；图中没有新音符盒。'),(1750,'底层不因这张剖视图而新增通路，仍按已登记路线行走。')]:
        dr.text((1400,y),text,font=small,fill='#6a785f')
    im.save(OUT/'05_夹廊支撑与零件架.png');print('mezzanine rendered',flush=True)
    im,dr=canvas((2700,1800),'室内通路｜每条绿线都有实际地板与三格空气','俯视设计坐标；格内灰绿为旧/新地面上的构件，橙框为拆栏杆位置。各图方格比例不同。')
    panels=[(45,180,(-7,21,16,58,79),38,'唱诗堂长席'),(1330,215,(7,19,17,79,86),58,'后殿台基'),(1530,905,(65,75,16,39,53),52,'维修夹廊')]
    for px,py,(x0,x1,y,z0,z1),scale,title in panels:
        dr.text((px,py-58),f'{title} · 地板Y{y}',font=font,fill='#456048')
        for x in range(x0,x1+1):
            dr.text((px+(x-x0)*scale+3,py-26),str(x),font=small,fill='#78806b')
        for z in range(z0,z1+1):
            dr.text((px-38,py+(z-z0)*scale+4),str(z),font=small,fill='#78806b')
            for x in range(x0,x1+1):
                X=px+(x-x0)*scale;Z=py+(z-z0)*scale;s=a.get((x,y+1,z));floor=a.get((x,y,z))
                fill='#b4b39a' if s else '#e7e2cf' if floor else '#cbcbbd'
                dr.rectangle((X,Z,X+scale-2,Z+scale-2),fill=fill)
                if s and s[0]=='lantern':dr.ellipse((X+scale*.3,Z+scale*.3,X+scale*.7,Z+scale*.7),fill='#b99440')
        for r in meta['routes']:
            for u,v in zip(r['points'],r['points'][1:]):
                if u[1]!=y or v[1]!=y or not all(x0<=p[0]<=x1 and z0<=p[2]<=z1 for p in(u,v)):continue
                dr.line([(px+(p[0]-x0+.5)*scale,py+(p[2]-z0+.5)*scale) for p in(u,v)],fill='#4f8166',width=7)
        for x,yy,z in meta['openings']:
            if yy==y+1 and x0<=x<=x1 and z0<=z<=z1:
                X=px+(x-x0)*scale;Z=py+(z-z0)*scale;dr.rectangle((X+2,Z+2,X+scale-4,Z+scale-4),outline='#b9833e',width=4)
    for y,text in [(1130,'西席与东席分别接回原中殿路线；'),(1185,'北侧短支路和后殿独席是可停留的末端。'),(1260,'维修环线从X67主廊进入，绕过工台后返回；'),(1315,'X70的三座原灯柱保持，行走线设在X71。'),(1390,'八个开口均先验同高地板，再拆旧栏杆。'),(1460,'新路线最低代理：6 / 10 / 8 / 9 / 9，非游戏光照。'),(1550,'橙框只表示本轮开口，不表示可以拆整段护栏。'),(1620,'准确方块状态与世界原点换算见离线逐层页面。')]:
        dr.text((65,y),text,font=small,fill='#677860')
    im.save(OUT/'06_两处室内通路.png');print('room paths rendered',flush=True)


if __name__=='__main__':main()
