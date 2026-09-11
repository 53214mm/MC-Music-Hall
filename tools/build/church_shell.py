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
    return b
