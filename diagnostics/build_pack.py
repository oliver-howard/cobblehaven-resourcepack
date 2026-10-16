from pathlib import Path
import json,shutil,copy,zipfile,hashlib
src=Path('inspect/cobblehaven-resourcepack(2)'); dst=Path('work/cobblehaven-verified-1.21.1')
if dst.exists(): shutil.rmtree(dst)
shutil.copytree(src,dst)
def write(path,obj):
 p=dst/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(obj,indent=2)+'\n')
colors=['aqua', 'magenta', 'gold', 'black_purple', 'black', 'bronze', 'dark', 'dark_red', 'green', 'light_pink', 'navy_blue', 'orange_green', 'pink', 'red', 'silver', 'yellow']
write(Path('pack.mcmeta'),{'pack':{'pack_format':34,'description':'Cobblehaven 1.21.1 | atlas + keys + static crate reconstruction'}})
# This directory belongs to the 1.21.4+ model format, not 1.21.1.
shutil.rmtree(dst/'assets/minecraft/items')
write(Path('assets/minecraft/atlases/blocks.json'),{'sources':[{'type':'minecraft:directory','source':'crate','prefix':'crate/'},{'type':'minecraft:directory','source':'key','prefix':'key/'}]})
def carrier(item,start,targets):
 write(Path(f'assets/minecraft/models/item/{item}.json'),{'parent':'minecraft:item/generated','textures':{'layer0':f'minecraft:item/{item}'},'overrides':[{'predicate':{'custom_model_data':start+i},'model':m} for i,m in enumerate(targets)]+[{'predicate':{'custom_model_data':start+len(targets)},'model':f'cobblehaven:item/{item}_vanilla'}]})
 write(Path(f'assets/cobblehaven/models/item/{item}_vanilla.json'),{'parent':'minecraft:item/generated','textures':{'layer0':f'minecraft:item/{item}'}})
carrier('tripwire_hook',1001,[f'crates:key/{c}' for c in colors])
# Static reconstruction, not a claim to recover missing bone transformations.
assembly={'bottom':[0,-8,0],'up2':[0,2,7.5],'up':[0,-1,-9],'center':[0,-1,-9],'down':[0,-1,-9]}
for c in colors:
 elements=[]
 for part,offset in assembly.items():
  d=json.loads((src/f'assets/crates/models/crate/{c}/{part}.json').read_text())
  for original in d['elements']:
   e=copy.deepcopy(original)
   for key in ['from','to']: e[key]=[v+offset[i] for i,v in enumerate(e[key])]
   if 'rotation' in e: e['rotation']['origin']=[v+offset[i] for i,v in enumerate(e['rotation']['origin'])]
   elements.append(e)
 write(Path(f'assets/crates/models/item/static_{c}.json'),{'textures':{'0':f'crates:crate/{c}','particle':f'crates:crate/{c}'},'elements':elements,'display':{'fixed':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[1,1,1]},'gui':{'rotation':[25,135,0],'translation':[0,0,0],'scale':[0.65,0.65,0.65]}}})
carrier('carrot_on_a_stick',2001,[f'crates:item/static_{c}' for c in colors])
# Diagnostic access to untouched, local-coordinate Aqua components.
parts=['bottom','center','down','key','lock_left','lock_left_sub','lock_right','lock_right_sub','pokeball_1','up','up2']
carrier('paper',2101,[f'crates:crate/aqua/{p}' for p in parts])
write(Path('diagnostics/assembly.json'),{'status':'static reconstruction; original rig transforms unavailable','offsets_model_units':assembly,'omitted':['key','lock_left','lock_left_sub','lock_right','lock_right_sub','pokeball_1'],'reason':'Key/interior and articulated parts are not required for the closed shell; original rig placement cannot be recovered from these JSONs alone. Front badge placement is reconstructed.','display_origin':'At bottom-center of block, use entity y=blockY+0.5: item rendering subtracts [8,8,8]/16.','ids':dict(zip(map(str,range(2101,2112)),parts))})
write(Path('diagnostics/source_hashes.json'),{str(p.relative_to(src)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((src/'assets/crates').rglob('*')) if p.is_file()})
print(dst)
