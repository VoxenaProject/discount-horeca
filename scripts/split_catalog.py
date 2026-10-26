"""Split the imported catalogue into small JSON files for static hosting."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
DATA=(ROOT/'dist' if (ROOT/'dist').is_dir() else ROOT)/'data'
p=DATA/'catalog.json';d=json.loads(p.read_text())
products=d.pop('products',None)
if products is None:
 products=[]
 for name in d['parts']:products+=json.loads((DATA/name).read_text())
parts=[]
for i,start in enumerate(range(0,len(products),200)):
 name=f'products-{i+1:02}.json';(DATA/name).write_text(json.dumps(products[start:start+200],ensure_ascii=False,separators=(',',':')));parts.append(name)
errors=d.pop('errors',[])
if errors:(DATA/'import-report.json').write_text(json.dumps({'source':d['source'],'importedAt':d['importedAt'],'coverage':d.get('coverage'),'errors':errors},ensure_ascii=False,indent=2))
d['parts']=parts;p.write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
print('Parts:',len(parts),'products:',len(products))
