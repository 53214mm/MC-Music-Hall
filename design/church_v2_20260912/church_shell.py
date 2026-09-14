"""White/blue Gothic church surrounding the unchanged central music machinery."""
import math


def make_church(core):
    b={p:s for p,s in core.items() if p[1]<=68}
    def put(x,y,z,n='white_concrete',props=None): b[(x,y,z)]=(n,props or {},'shell')
    def rect(xa,xb,ya,yb,za,zb,n='white_concrete'):
        for x in range(xa,xb+1):
            for y in range(ya,yb+1):
                for z in range(za,zb+1):put(x,y,z,n)
    def pointed(face,fixed,center,bottom,width,height):
        # Stained glass with a stepped pointed outer frame and thin tracery.
        for u in range(-width,width+1):
            top=bottom+height-max(0,abs(u)-1)*2
            for y in range(bottom,top+1):
                frame=abs(u)==width or y in [bottom,top] or (u==0 and y<bottom+height-3)
                n='smooth_quartz' if frame else ('purple_stained_glass' if (y-bottom+abs(u))%11==0 else 'light_blue_stained_glass')
                if face=='x':put(fixed,y,center+u,n)
                else:put(center+u,y,fixed,n)
    def spire(cx,cz,base,radius,height):
        for y in range(base,base+height+1):
            r=max(0,round(radius*(1-(y-base)/height)))
            for x in range(cx-r,cx+r+1):
                for z in range(cz-r,cz+r+1):
                    d=abs(x-cx)+abs(z-cz)
                    if d in [r,max(0,r-1)]:put(x,y,z,'smooth_quartz' if x==cx or z==cz else 'dark_prismarine')
        put(cx,base+height+1,cz,'sea_lantern')
    # Main central roof: steep nave profile, stone ribs and blue crystalline skylights.
    for x in range(-7,50):
        y=91-round(abs(x-21)*.78)
        for z in range(-37,39):
            rib=z in [-37,-25,-13,-1,11,23,38] or x in [20,21,22]
            put(x,y,z,'smooth_quartz' if rib else 'light_blue_stained_glass' if abs(x-21)<10 else 'dark_prismarine')
    for z in [-37,38]:
        for x in range(-7,50):
            top=91-round(abs(x-21)*.78)
            for y in range(69,top+1):put(x,y,z,'smooth_quartz' if x in [20,21,22] or y==top else 'white_concrete')
    # Tall pointed bays break up the previous rectangular glass curtain wall.
    for x in [-7,49]:
        for z in [-25,-9,7,23]:
            for y in [3,27,51]:pointed('x',x,z,y,5,17)
    for z in [-37,38]:
        for x in [5,21,37]:
            for y in [3,27,51]:pointed('z',z,x,y,5,17)
    for z in [-37,38]:
        for dx in range(-7,8):
            for dy in range(-7,8):
                r=math.hypot(dx,dy)
                if r<=7:
                    rib=r>=6 or dx==0 or dy==0 or abs(dx)==abs(dy)
                    put(21+dx,79+dy,z,'smooth_quartz' if rib else 'light_blue_stained_glass')
    # Projecting buttress piers and high flying arches on both sides of the core.
    for side in [-1,1]:
        wall=-8 if side<0 else 50
        outer=-15 if side<0 else 57
        for z in [-29,-13,3,19,33]:
            rect(outer-1,outer+1,-2,42,z-1,z+1,'smooth_quartz')
            rect(outer-2,outer+2,-2,1,z-2,z+2,'polished_andesite')
            for step in range(8):
                x=wall+side*step;y=60-round(2.2*step)
                rect(x,x,y-2,y,z-1,z+1,'smooth_quartz')
            spire(outer,z,43,2,12)
    # Central lantern tower / crossing spire.
    for y in range(87,99):
        for x in range(15,28):
            for z in range(-5,8):
                if x in [15,27] or z in [-5,7]:
                    n='smooth_quartz' if x in [15,16,26,27] or z in [-5,-4,6,7] or y in [87,98] else 'light_blue_stained_glass'
                    put(x,y,z,n)
    spire(21,1,99,6,10)
    # Foundation for the added nave, transepts, buttresses, and entry forecourt.
    for x in range(-29,72):
        for z in range(-40,96):
            present=(-17<=x<=59 and -40<=z<=38) or (-11<=x<=53 and 39<=z<=95) or (-29<=x<=71 and -13<=z<=15)
            if present:
                put(x,-1,z,'smooth_stone')
                if x in [-29,-17,-11,53,59,71] or z in [-40,-13,15,38,95]:put(x,-2,z,'polished_andesite')
    # Long front nave and lowered aisles.
    for z in range(39,88):
        for x in range(7,36):
            roof=56-abs(x-21)
            put(x,roof,z,'smooth_quartz' if z%12==3 or x==21 else 'dark_prismarine')
        for x in [7,35]:
            for y in range(0,43):put(x,y,z,'white_concrete')
        for side in [-1,1]:
            for dist in range(1,15):
                x=7-dist if side<0 else 35+dist
                roof=35-round(dist*.7)
                put(x,roof,z,'smooth_quartz' if z%12==3 else 'dark_prismarine')
            x=-7 if side<0 else 49
            for y in range(0,26):put(x,y,z,'white_concrete')
    for x in [-7,7,35,49]:
        for z in [46,58,70]:pointed('x',x,z,4 if x in [-7,49] else 25,4,17 if x in [-7,49] else 15)
    # Interior arcades under the nave clerestory.
    for x in [7,35]:
        for center in [46,58,70,82]:
            for dz in range(-4,5):
                top=21-abs(dz)*2
                for y in range(0,top):b.pop((x,y,center+dz),None)
    # Front gable and rose window.
    for x in range(-7,50):
        top=56-abs(x-21) if 7<=x<=35 else 25
        for y in range(0,top+1):put(x,y,87,'smooth_quartz' if y==top else 'white_concrete')
    for dx in range(-10,11):
        for dy in range(-10,11):
            radius=math.hypot(dx,dy)
            if radius<=10:
                rib=radius>=9 or abs(dx)<=0 or abs(dy)<=0 or abs(abs(dx)-abs(dy))==0 or 4<=radius<=5
                put(21+dx,39+dy,88,'smooth_quartz' if rib else 'purple_stained_glass' if radius<4 else 'light_blue_stained_glass')
                b.pop((21+dx,39+dy,87),None)
    # Pointed main portal and the connecting arch into the music core.
    for z in [38,87]:
        for dx in range(-7,8):
            top=18-abs(dx)*2
            for y in range(0,top+1):
                if abs(dx)==7 or y==top:put(21+dx,y,z,'smooth_quartz')
                else:b.pop((21+dx,y,z),None)
    # Portal archivolts, alternating stone ribs and empty recesses.
    for depth in range(1,4):
        for dx in range(-7-depth,8+depth):
            top=18+depth-abs(dx)*1.6
            y=round(top)
            if y>=0:rect(21+dx,21+dx,y,y+1,87+depth,87+depth,'smooth_quartz')
        rect(13-depth,13-depth,0,6,87+depth,87+depth,'smooth_quartz')
        rect(29+depth,29+depth,0,6,87+depth,87+depth,'smooth_quartz')
    # Paired bell towers framing the south entrance.
    for cx in [0,42]:
        for y in range(0,70):
            for x in range(cx-7,cx+8):
                for z in range(74,91):
                    if x not in [cx-7,cx+7] and z not in [74,90]:continue
                    band=y in [0,19,20,39,40,59,60,68,69]
                    pillar=x in [cx-7,cx-6,cx+6,cx+7] or z in [74,75,89,90]
                    put(x,y,z,'smooth_quartz' if band or pillar else 'white_concrete')
        for bottom in [5,26,47]:pointed('z',90,cx,bottom,4,16)
        spire(cx,82,70,8,22)
        for dx in [-7,7]:
            for z in [74,90]:spire(cx+dx,z,68,2,11)
    # Transepts to either side: lower gabled wings, unmistakable cross-shaped plan.
    for xa,xb in [(-29,-8),(50,71)]:
        for x in range(xa,xb+1):
            for z in range(-11,14):put(x,49-abs(z-1),z,'smooth_quartz' if x%10==1 or z==1 else 'dark_prismarine')
            for z in [-11,13]:
                for y in range(0,38):put(x,y,z,'white_concrete')
        outer=xa if xa<0 else xb
        for z in range(-11,14):
            for y in range(0,50-abs(z-1)):put(outer,y,z,'white_concrete')
        pointed('x',outer,1,10,7,30)
        for z in [-11,13]:pointed('z',z,(xa+xb)//2,5,5,25)
    # Smaller nave buttresses and pinnacles continue the facade rhythm.
    for x in [-10,52]:
        for z in [43,55,67]:
            rect(x-1,x+1,0,27,z-1,z+1,'smooth_quartz');spire(x,z,28,2,9)
    # Church benches, aisle inlay, and safe passive lights.
    for z in range(40,94):
        for x in range(18,25):put(x,-1,z,'polished_andesite' if x in [18,24] else 'smooth_quartz')
    for z in [49,55,61,67,73]:
        for xa,xb in [(10,16),(26,32)]:
            for x in range(xa,xb+1):put(x,0,z,'spruce_stairs',{'facing':'south','half':'bottom','shape':'straight','waterlogged':'false'})
    for x in [-5,5,37,47]:
        for z in [42,54,66,78]:put(x,0,z,'sea_lantern')
    add_gothic_details(b)
    return b


def add_gothic_details(b):
    """Hand-buildable relief and vaults, wholly outside the machinery envelopes.

    These are original block patterns, informed by the cited Gothic tutorials;
    they are not a traced copy of an author's downloadable build.
    """
    def put(x,y,z,n='smooth_quartz',props=None):
        b[(x,y,z)]=(n,props or {},'shell')
    def slab(x,y,z,top=False):
        put(x,y,z,'smooth_quartz_slab',{'type':'top' if top else 'bottom','waterlogged':'false'})
    def stair(x,y,z,facing,top=False):
        put(x,y,z,'smooth_quartz_stairs',{'facing':facing,'half':'top' if top else 'bottom','shape':'straight','waterlogged':'false'})
    def column(x,z,lo,hi):
        for y in range(lo,hi+1):put(x,y,z,'quartz_pillar',{'axis':'y'})
        for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1)]:
            put(x+dx,lo,z+dz,'chiseled_quartz_block')
            slab(x+dx,hi+1,z+dz,True)
        put(x,hi+2,z,'chiseled_quartz_block')
    def wallpost(x,y,z):
        put(x,y,z,'diorite_wall',{'up':'true','north':'none','east':'none','south':'none','west':'none','waterlogged':'false'})
    def window(face,fixed,c,lo,w,h,out):
        # Glass is one block behind the wall; the hood and jambs project one block.
        def p(u,y,d,n='smooth_quartz',props=None):
            xyz=(fixed+out*d,y,c+u) if face=='x' else (c+u,y,fixed+out*d)
            put(*xyz,n,props)
        def erase(u,y,d):
            xyz=(fixed+out*d,y,c+u) if face=='x' else (c+u,y,fixed+out*d)
            b.pop(xyz,None)
        for u in range(-w,w+1):
            top=lo+h-abs(u)*2
            for y in range(lo,top+1):
                edge=abs(u)==w or y in [lo,top]
                if edge:p(u,y,0)
                else:
                    erase(u,y,0)
                    p(u,y,-1,'purple_stained_glass' if (y-lo+abs(u))%9==0 else 'light_blue_stained_glass')
            # Cover the old, wider pointed head with a white spandrel.
            for y in range(top+1,min(lo+h,top+2)+1):p(u,y,0,'white_concrete')
            p(u,top+1,1)
            p(u,lo-1,1,'smooth_quartz_slab',{'type':'top','waterlogged':'false'})
        for u in [-w-1,w+1]:
            shoulder=lo+h-w*2
            for y in range(lo,shoulder+1):p(u,y,1,'quartz_pillar',{'axis':'y'})
            p(u,lo-1,1,'chiseled_quartz_block');p(u,shoulder+1,1,'chiseled_quartz_block')
        # A pair of narrow lancets and a small stone diamond in the upper light.
        for y in range(lo+1,lo+h-4):p(0,y,0)
        for u,y in [(-1,lo+h-5),(1,lo+h-5),(0,lo+h-4)]:p(u,y,0)
    # Recess the existing windows, using a repeatable 11-wide construction bay.
    for x,out in [(-7,-1),(49,1)]:
        for z in [-25,-9,7,23]:
            for y in [3,27,51]:window('x',x,z,y,5,17,out)
    for z,out in [(-37,-1),(38,1)]:
        for x in [5,21,37]:
            for y in [3,27,51]:
                # Keep the central entrance arch open, not glazed over.
                if z==38 and x==21 and y==3:continue
                window('z',z,x,y,5,17,out)
    for x,out in [(-7,-1),(7,-1),(35,1),(49,1)]:
        for z in [46,58,70]:window('x',x,z,4 if x in [-7,49] else 25,4,17 if x in [-7,49] else 15,out)
    # Bundled pilasters articulate the formerly flat central curtain wall.
    for x,out in [(-7,-1),(49,1)]:
        for z in [-33,-17,-1,15,31]:
            for y in range(1,68):
                put(x+out,y,z,'quartz_pillar',{'axis':'y'})
                if y%12 not in [9,10]:
                    put(x+out,y,z-1,'smooth_quartz');put(x+out,y,z+1,'smooth_quartz')
            for y in [11,23,35,47,59,67]:
                for dz in [-2,-1,0,1,2]:slab(x+out*2,y,z+dz,True)
    # Exterior cornices, corbels and a pierced parapet above the core walls.
    for x,out in [(-7,-1),(49,1)]:
        for z in range(-32,34):
            slab(x+out,68,z,True)
            if z%4==1:
                stair(x+out,67,z,'east' if out<0 else 'west',True)
                wallpost(x+out,69,z);slab(x+out,70,z)
    for z,out in [(-37,-1),(38,1)]:
        for x in range(-1,44):
            slab(x,68,z+out,True)
            if x%4==1:wallpost(x,69,z+out)
    # Ridge crockets and gable edging use real slabs/stairs, not full-cube lumps.
    for z in list(range(-34,-7,4))+list(range(11,38,4)):
        wallpost(21,92,z);slab(21,93,z)
    for z in [-38,39]:
        for x in range(-6,49):
            y=91-round(abs(x-21)*.78)
            stair(x,y,z,'east' if x<21 else 'west')
            if abs(x-21)%6==0 and abs(x-21)>3:wallpost(x,y+1,z)
    for z in range(42,86,4):wallpost(21,57,z)
    for z in [42,54,66,78,86]:
        for x in range(8,35):
            y=56-abs(x-21)
            if x%6==3:stair(x,y+1,z,'east' if x<21 else 'west')
    # Bell towers: recessed openings on three faces, corner shafts and airy crowns.
    for cx in [0,42]:
        for bottom in [5,26,47]:
            window('z',90,cx,bottom,4,16,1)
            for x,out in [(cx-7,-1),(cx+7,1)]:window('x',x,82,bottom,4,16,out)
        for dx in [-8,8]:
            for z in [74,90]:column(cx+dx,z,1,66)
        for x in range(cx-6,cx+7):
            if x%2==0:
                wallpost(x,70,91);slab(x,71,91)
        # Three deep, smaller blind niches below the belfry windows.
        for u in [-4,0,4]:
            for y in range(21,24):wallpost(cx+u,y,91)
            stair(cx+u,24,91,'north',True)
    # Three-level rose-window rim and radiating tracery on the entrance face.
    for dx in range(-12,13):
        for dy in range(-12,13):
            r=math.hypot(dx,dy)
            if 10<r<=11:put(21+dx,39+dy,89,'chiseled_quartz_block')
            elif 11<r<=12:slab(21+dx,39+dy,90,dy<0)
    for x in [9,33]:column(x,89,22,51)
    for x in range(10,33):
        if x%2==0:wallpost(x,25,89)
        slab(x,26,89,True)
    # Layered portal jambs: clear central passage X=15..27, not blocked by statues.
    for depth in [1,2,3]:
        for x in [13-depth,29+depth]:column(x,87+depth,0,5+depth)
    for x in [11,31]:
        put(x,10,92,'chiseled_quartz_block');wallpost(x,11,92);wallpost(x,12,92)
        slab(x,13,92,True);put(x,14,92,'sea_lantern');stair(x,15,92,'north')
    # Side-aisle plinths, eaves and blind arcades give close-range scale.
    for x,out in [(-7,-1),(49,1)]:
        for z in range(39,74):
            slab(x+out,1,z);slab(x+out,25,z,True)
            if z%4==3:stair(x+out,24,z,'east' if out<0 else 'west',True)
    for x,out in [(-29,1),(71,-1)]:
        # Transept end lies on the bounding-box edge: recess inward, no extension.
        for z in [-10,12]:column(x+out,z,1,34)
        for z in range(-9,12):slab(x,36,z,True)
    # Nave interior: repeated clustered piers and four-part ribs below the roof.
    for za,zb in [(40,52),(52,64),(64,76),(76,86)]:
        mid=(za+zb)/2
        for x in range(8,35):
            for z in range(za,zb+1):
                ax=abs(x-21)/13;az=abs(z-mid)/((zb-za)/2)
                ceiling=min(52-round(24*min(ax,az)),54-abs(x-21))
                put(x,ceiling,z,'calcite')
    for zc in [40,52,64,76,86]:
        for x in [8,34]:
            column(x,zc,0,23)
            for y in range(2,24):
                wallpost(x+(1 if x==8 else -1),y,zc)
        previous=None
        for x in range(8,35):
            y=26+round(24*(1-abs(x-21)/13))
            for yy in range(min(y,previous if previous is not None else y),max(y,previous if previous is not None else y)+1):
                put(x,yy,zc,'smooth_quartz')
            if x not in [20,21,22]:stair(x,min(y,previous if previous is not None else y)-1,zc,'east' if x<21 else 'west',True)
            previous=y
    for za,zb in [(40,52),(52,64),(64,76),(76,86)]:
        mid=(za+zb)//2
        for start in [za,zb]:
            previous=None
            for x in range(8,35):
                f=1-abs(x-21)/13
                y=26+round(f*24)
                z=round(start+(mid-start)*f)
                put(x,y,z,'smooth_quartz')
                if previous is not None:
                    _,py,pz=previous
                    for yy in range(min(py,y),max(py,y)+1):put(x,yy,pz)
                    for zz in range(min(pz,z),max(pz,z)+1):put(x,y,zz)
                previous=(x,y,z)
        put(21,50,mid,'chiseled_quartz_block')
        # Passive chandelier: it cannot power nearby music circuitry.
        for y in range(39,50):
            put(21,y,mid,'iron_chain',{'axis':'y','waterlogged':'false'})
        for dx,dz in [(0,0),(1,0),(-1,0),(0,1),(0,-1),(2,0),(-2,0),(0,2),(0,-2)]:
            put(21+dx,38,mid+dz,'iron_bars',{'north':'true','east':'true','south':'true','west':'true','waterlogged':'false'})
        for dx,dz in [(2,0),(-2,0),(0,2),(0,-2)]:
            put(21+dx,37,mid+dz,'lantern',{'hanging':'true','waterlogged':'false'})
    # Choir steps and tessellated floor borders; keep a wide central access aisle.
    for z in range(41,85):
        for x in [9,17,25,33]:
            put(x,-1,z,'chiseled_quartz_block' if z%4==0 else 'polished_diorite')
    for z in [41,47,53,59,65,71,77,83]:
        for x in range(10,33):
            if 18<=x<=24:continue
            put(x,-1,z,'polished_diorite')
    # Decorative corner finials around the central lantern.
    for x in [15,27]:
        for z in [-5,7]:
            column(x,z,94,99)
            for y in range(102,105):wallpost(x,y,z)
            put(x,105,z,'sea_lantern')
