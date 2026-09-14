"""Small fail-closed reader/renderer for vanilla block models, not a game engine.

Reads locally owned resource assets. Does not unpack or distribute a texture pack.
Supports variants/multipart, parents, model rotations, and element rotations.
UV locking and biome tint are not reproduced; models needing them are annotated.
"""
import copy
import io
import json
import math
import zipfile
from functools import lru_cache
from PIL import Image,ImageEnhance

JAR=r'E:\PCL\PCL 正式版 2.8.12\.minecraft\versions\26.3-snapshot-9\26.3-snapshot-9.jar'
NORMALS={'east':(1,0,0),'west':(-1,0,0),'up':(0,1,0),'down':(0,-1,0),'south':(0,0,1),'north':(0,0,-1)}


def rotate(p,axis,degrees,origin=(.5,.5,.5)):
    x,y,z=[p[i]-origin[i] for i in range(3)];s=math.sin(math.radians(degrees));c=math.cos(math.radians(degrees))
    if axis=='y':q=(x*c-z*s,y,x*s+z*c)
    elif axis=='x':q=(x,y*c-z*s,y*s+z*c)
    else:q=(x*c-y*s,x*s+y*c,z)
    return tuple(round(q[i]+origin[i],10) for i in range(3))


def matches(condition,props):
    if 'OR' in condition:return any(matches(c,props) for c in condition['OR'])
    if 'AND' in condition:return all(matches(c,props) for c in condition['AND'])
    return all(str(props.get(k)) in str(v).split('|') for k,v in condition.items())


class VanillaAssets:
    def __init__(self,path=JAR):self.jar=zipfile.ZipFile(path)

    @lru_cache(maxsize=None)
    def read(self,kind,name):
        name=name.removeprefix('minecraft:')
        return json.loads(self.jar.read(f'assets/minecraft/{kind}/{name}.json'))

    @lru_cache(maxsize=None)
    def model(self,name):
        raw=self.read('models',name)
        parent=self.model(raw['parent']) if raw.get('parent') else {}
        result={**parent,**raw,'textures':{**parent.get('textures',{}),**raw.get('textures',{})}}
        return result

    @lru_cache(maxsize=None)
    def texture(self,name):
        im=Image.open(io.BytesIO(self.jar.read('assets/minecraft/textures/'+name.removeprefix('minecraft:')+'.png'))).convert('RGBA')
        # Animated textures use the first frame only.
        return im.crop((0,0,im.width,min(im.width,im.height)))

    @lru_cache(maxsize=None)
    def elements(self,name,properties=()):
        props=dict(properties);states=self.read('blockstates',name);applies=[]
        if 'variants' in states:
            for key,value in states['variants'].items():
                condition=dict(item.split('=',1) for item in key.split(',') if item)
                if matches(condition,props):applies.append(value)
            if len(applies)!=1:raise ValueError(f'Expected one variant for {name} {props}, got {len(applies)}')
        elif 'multipart' in states:
            for part in states['multipart']:
                if matches(part.get('when',{}),props):applies.append(part['apply'])
        else:raise ValueError(f'Unsupported blockstate {name}')
        result=[]
        for app in applies:
            if isinstance(app,list):app=app[0] # deterministic first weighted appearance
            model=self.model(app['model'])
            if 'elements' not in model:raise ValueError(f'No explicit block geometry: {name}')
            def transform(p):
                for axis in('x','y'):
                    if app.get(axis):p=rotate(p,axis,app[axis])
                return p
            for e in model['elements']:
                x,y,z=[v/16 for v in e['from']];X,Y,Z=[v/16 for v in e['to']]
                verts={'south':[(x,Y,Z),(X,Y,Z),(X,y,Z),(x,y,Z)],'north':[(X,Y,z),(x,Y,z),(x,y,z),(X,y,z)],'east':[(X,Y,Z),(X,Y,z),(X,y,z),(X,y,Z)],'west':[(x,Y,z),(x,Y,Z),(x,y,Z),(x,y,z)],'up':[(x,Y,z),(X,Y,z),(X,Y,Z),(x,Y,Z)],'down':[(x,y,Z),(X,y,Z),(X,y,z),(x,y,z)]}
                default_uv={'south':[x*16,16-Y*16,X*16,16-y*16],'north':[16-X*16,16-Y*16,16-x*16,16-y*16],'east':[16-Z*16,16-Y*16,16-z*16,16-y*16],'west':[z*16,16-Y*16,Z*16,16-y*16],'up':[x*16,z*16,X*16,Z*16],'down':[x*16,16-Z*16,X*16,16-z*16]}
                faces=[]
                for side,f in e['faces'].items():
                    texture=f['texture'];visited=set()
                    while isinstance(texture,dict) or texture.startswith('#'):
                        if isinstance(texture,dict):texture=texture['sprite'];continue
                        if texture in visited:raise ValueError('Cyclic texture reference')
                        visited.add(texture);texture=model['textures'][texture[1:]]
                    vertices=verts[side];normal=NORMALS[side]
                    if 'rotation' in e:
                        r=e['rotation'];origin=tuple(v/16 for v in r['origin'])
                        vertices=[rotate(p,r['axis'],r['angle'],origin) for p in vertices]
                        normal=rotate(normal,r['axis'],r['angle'],(0,0,0))
                        if r.get('rescale'):
                            factor=1/math.cos(math.radians(r['angle']));axis='xyz'.index(r['axis'])
                            vertices=[tuple(origin[i]+(p[i]-origin[i])*(1 if i==axis else factor) for i in range(3)) for p in vertices]
                    vertices=[transform(p) for p in vertices]
                    for axis in('x','y'):
                        if app.get(axis):normal=rotate(normal,axis,app[axis],(0,0,0))
                    faces.append(dict(vertices=vertices,normal=normal,texture=texture,uv=f.get('uv',default_uv[side]),rotation=f.get('rotation',0),cullface=bool(f.get('cullface')),shade=e.get('shade',True)))
                result.append(dict(faces=faces))
        return result

    @lru_cache(maxsize=None)
    def swatch(self,name,props=()):
        element=self.elements(name,props)[0]
        face=next((f for f in element['faces'] if f['normal']==(0,0,1)),element['faces'][0])
        im=self.texture(face['texture']).resize((1,1)).convert('RGB')
        return '#%02x%02x%02x'%im.getpixel((0,0))


def render(assets,blocks,region,width,height,angle=22):
    c=math.cos(math.radians(angle));s=math.sin(math.radians(angle));view=(s,.55,c)
    def raw(p):
        x,y,z=p;return x*c-z*s,(x*s+z*c)*.38-y*.94
    corners=[raw((x,y,z)) for x in(region[0],region[1]+1) for y in(region[2],region[3]+1) for z in(region[4],region[5]+1)]
    lo=[min(p[i] for p in corners) for i in(0,1)];hi=[max(p[i] for p in corners) for i in(0,1)]
    scale=min((width-30)/(hi[0]-lo[0]),(height-30)/(hi[1]-lo[1]))
    def project(p):
        u,v=raw(p);return (u-(hi[0]+lo[0])/2)*scale+width/2,(v-(hi[1]+lo[1])/2)*scale+height/2
    selected={p:v for p,v in blocks.items() if all(region[2*i]<=p[i]<=region[2*i+1] for i in range(3))}
    opaque=set();mesh={}
    for n,pr,g in selected.values():
        key=(n,tuple(sorted(pr.items())))
        if key not in mesh:mesh[key]=assets.elements(*key)
    opaque_keys=set()
    for key,el in mesh.items():
        if len(el)==1 and len(el[0]['faces'])==6:
            points={v for f in el[0]['faces'] for v in f['vertices']}
            if len(points)==8 and all(all(q in(0,1) for q in v) for v in points) and all(assets.texture(f['texture']).getextrema()[3]==(255,255) for f in el[0]['faces']):opaque_keys.add(key)
    culled_keys={key for key in opaque_keys if all(f['cullface'] for f in mesh[key][0]['faces'])}
    for p,(n,pr,g) in selected.items():
        if (n,tuple(sorted(pr.items()))) in opaque_keys:opaque.add(p)
    faces=[]
    for p,(n,pr,g) in selected.items():
        key=(n,tuple(sorted(pr.items())))
        if key in culled_keys and all(tuple(p[i]+normal[i] for i in range(3)) in opaque for normal in NORMALS.values()):continue
        for element in mesh[key]:
            for f in element['faces']:
                normal=f['normal']
                if sum(normal[i]*view[i] for i in range(3))<=.001:continue
                neighbor=tuple(round(p[i]+normal[i]) for i in range(3))
                if f['cullface'] and neighbor in opaque:continue
                world=[tuple(p[i]+v[i] for i in range(3)) for v in f['vertices']];center=[sum(v[i] for v in world)/4 for i in range(3)]
                depth=(center[0]*s+center[2]*c)*.94+center[1]*.38
                shade=1 if not f['shade'] else .68+.23*max(0,normal[1])+.09*max(0,normal[0])
                faces.append((depth,[project(v) for v in world],f,shade))
    image=Image.new('RGBA',(width,height),'#deded2')
    cache={}
    for _,points,f,shade in sorted(faces,key=lambda r:r[0]):
        uv=tuple(f['uv']);key=(f['texture'],uv,f['rotation'],shade)
        if key not in cache:
            tex=assets.texture(f['texture']);u0,v0,u1,v1=uv;k=tex.width/16
            tile=tex.crop((int(min(u0,u1)*k),int(min(v0,v1)*k),max(int(max(u0,u1)*k),int(min(u0,u1)*k)+1),max(int(max(v0,v1)*k),int(min(v0,v1)*k)+1)))
            if u1<u0:tile=tile.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            if v1<v0:tile=tile.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            if f['rotation']:tile=tile.rotate(-f['rotation'],expand=True)
            alpha=tile.getchannel('A');tile=ImageEnhance.Brightness(tile).enhance(shade);tile.putalpha(alpha);cache[key]=tile
        tile=cache[key];p0,p1,_,p3=points
        a,b=p1[0]-p0[0],p3[0]-p0[0];d,e=p1[1]-p0[1],p3[1]-p0[1];det=a*e-b*d
        if abs(det)<.01:continue
        x0=max(0,math.floor(min(v[0] for v in points)));x1=min(width,math.ceil(max(v[0] for v in points)))
        y0=max(0,math.floor(min(v[1] for v in points)));y1=min(height,math.ceil(max(v[1] for v in points)))
        if x1<=x0 or y1<=y0:continue
        tx,ty=x0-p0[0],y0-p0[1]
        coefficients=(tile.width*e/det,-tile.width*b/det,tile.width*(e*tx-b*ty)/det,-tile.height*d/det,tile.height*a/det,tile.height*(-d*tx+a*ty)/det)
        patch=tile.transform((x1-x0,y1-y0),Image.Transform.AFFINE,coefficients,resample=Image.Resampling.NEAREST)
        image.alpha_composite(patch,(x0,y0))
    return image.convert('RGB')
