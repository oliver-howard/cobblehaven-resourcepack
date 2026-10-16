"""Structural verifier for this Minecraft Java 1.21.1 pack. Not a Minecraft renderer.
Usage: python verify_pack.py <extracted-pack-directory>
Uses the Python standard library only.
"""
from pathlib import Path
import sys,json,re,struct,hashlib
root=Path(sys.argv[1]); failures=[]; counts={'models':0,'elements':0,'faces':0,'custom_textures':0}
def check(ok,msg):
 if not ok: failures.append(msg)
def load(p): return json.loads(p.read_text(encoding='utf-8-sig'))
check(load(root/'pack.mcmeta')['pack']['pack_format']==34,'pack_format must be 34')
check(not (root/'assets/minecraft/items').exists(),'Unexpected 1.21.4+ item definitions')
# Expand the two custom directory sources according to atlas sprite naming rules.
atlas=set()
for s in load(root/'assets/minecraft/atlases/blocks.json')['sources']:
 check(s['type']=='minecraft:directory','Unknown atlas source')
 for ns in (root/'assets').iterdir():
  base=ns/'textures'/s['source']
  for p in base.rglob('*.png'):
   atlas.add(ns.name+':'+s['prefix']+p.relative_to(base).with_suffix('').as_posix())
counts['custom_textures']=len(atlas)
def resource_path(id,kind,suffix):
 ns,sep,path=id.partition(':')
 if not sep: ns,path='minecraft',ns
 check(bool(re.fullmatch('[a-z0-9_.-]+',ns)) and bool(re.fullmatch('[a-z0-9/._-]+',path)),f'Invalid ID {id}')
 return root/'assets'/ns/kind/(path+suffix)
models={}
for p in sorted((root/'assets').glob('*/models/**/*.json')):
 d=load(p); models[p]=d;counts['models']+=1
 for ref in [d.get('parent')]+[x['model'] for x in d.get('overrides',[])]:
  if ref and not ref.startswith('minecraft:'):check(resource_path(ref,'models','.json').is_file(),f'Missing model {ref}')
 textures=d.get('textures',{})
 def tex(ref,seen=None):
  seen=set() if seen is None else seen
  if ref.startswith('#'):
   k=ref[1:];check(k not in seen and k in textures,f'Unresolved/cyclic {ref} in {p}')
   if k in seen or k not in textures:return ''
   return tex(textures[k],seen|{k})
  return ref
 for ref in textures.values():
  ref=tex(ref)
  if ref and not ref.startswith('minecraft:'):
   path=resource_path(ref,'textures','.png');check(path.is_file(),f'Missing texture {ref}')
   check(ref in atlas,f'Texture absent from blocks atlas {ref}')
 for e in d.get('elements',[]):
  counts['elements']+=1
  for i in range(3):check(-16<=e['from'][i]<=e['to'][i]<=32,f'Invalid element bounds in {p}')
  if 'rotation' in e:
   rot=e['rotation'];check(rot['axis'] in ['x','y','z'] and rot['angle'] in [-45,-22.5,0,22.5,45],f'Invalid rotation in {p}')
  for face in e['faces'].values():
   counts['faces']+=1;ref=tex(face['texture']);check(ref in atlas or ref.startswith('minecraft:'),f'Unresolved face texture in {p}')
   check(all(0<=v<=16 for v in face.get('uv',[])),f'UV outside normalized texture bounds in {p}')
for p in (root/'assets/crates/textures').rglob('*.png'):
 b=p.read_bytes();check(b[:8]==b'\x89PNG\r\n\x1a\n',f'Not PNG {p}')
 w,h,depth,color,*_=struct.unpack('>IIBBBBB',b[16:29]);check(w>0 and h>0 and depth in [1,2,4,8,16],f'Invalid PNG header {p}')
# Simulate threshold/last-match selection, including reset outside the assigned interval.
for item,start,colors,prefix in [('tripwire_hook',1001,['aqua', 'magenta', 'gold', 'black_purple', 'black', 'bronze', 'dark', 'dark_red', 'green', 'light_pink', 'navy_blue', 'orange_green', 'pink', 'red', 'silver', 'yellow'],'crates:key/'),('carrot_on_a_stick',2001,['aqua', 'magenta', 'gold', 'black_purple', 'black', 'bronze', 'dark', 'dark_red', 'green', 'light_pink', 'navy_blue', 'orange_green', 'pink', 'red', 'silver', 'yellow'],'crates:item/static_')]:
 d=load(root/f'assets/minecraft/models/item/{item}.json');ov=d['overrides']
 vals=[o['predicate']['custom_model_data'] for o in ov];check(vals==sorted(vals),f'Descending overrides {item}')
 for i,c in enumerate(colors):
  hits=[o['model'] for o in ov if start+i>=o['predicate']['custom_model_data']];check(hits[-1]==prefix+c,f'Incorrect model dispatch {item} {start+i}')
 for n in [start-1,start+len(colors),99999]:
  hits=[o['model'] for o in ov if n>=o['predicate']['custom_model_data']]
  check(not hits or hits[-1]==f'cobblehaven:item/{item}_vanilla',f'Unbounded custom range {item}')
paper=load(root/'assets/minecraft/models/item/paper.json')['overrides']
for i,part in enumerate(load(root/'diagnostics/assembly.json')['ids'].values()):
 check(paper[i]['predicate']['custom_model_data']==2101+i and paper[i]['model']=='crates:crate/aqua/'+part,'Incorrect diagnostic paper dispatch')
for rel,sha in load(root/'diagnostics/source_hashes.json').items():check(hashlib.sha256((root/rel).read_bytes()).hexdigest()==sha,f'Original asset changed {rel}')
report={'status':'PASS' if not failures else 'FAIL','counts':counts,'failures':failures,'limitations':['No Minecraft client rendering performed','Static assembly offsets are a reconstruction','Vanilla minecraft: dependencies are assumed to come from Minecraft 1.21.1','Other packs/mods may override models or atlas sources at runtime']}
print(json.dumps(report,indent=2));sys.exit(bool(failures))
