"""Recover explicit key/value pairs from cached source HTML, without inferring values."""
from pathlib import Path
from lxml import html
import json,hashlib,re
ROOT=Path(__file__).resolve().parents[1]; DATA=(ROOT/'dist' if (ROOT/'dist').exists() else ROOT)/'data'
catalog=json.loads((DATA/'catalog.json').read_text());products=sum([json.loads((DATA/x).read_text()) for x in catalog['parts']],[])
result={}
clean=lambda s:' '.join(s.split()).strip(' :')
for p in products:
 f=Path('/tmp/hf-catalog-cache')/(hashlib.sha256(p['url'].encode()).hexdigest()+'.html')
 if not f.exists():continue
 t=html.fromstring(f.read_bytes());nodes=t.xpath('//*[@id="product-details"]/@data-product')
 if not nodes:continue
 d=json.loads(nodes[0]);pairs=list(p.get('features',[]));seen={x['name'].casefold() for x in pairs}
 def add(k,v):
  k,v=clean(k),clean(v)
  if k and v and len(k)<90 and len(v)<350 and k.casefold() not in seen:seen.add(k.casefold());pairs.append({'name':k,'value':v})
 for field in ['description_short','description']:
  raw=d.get(field,'')
  if not raw:continue
  tree=html.fromstring('<div>'+raw+'</div>')
  for row in tree.xpath('.//tr'):
   cells=row.xpath('./th|./td')
   if len(cells)==2:add(cells[0].text_content(),cells[1].text_content())
  for dt in tree.xpath('.//dt'):
   dd=dt.getnext()
   if dd is not None and dd.tag=='dd':add(dt.text_content(),dd.text_content())
  for label in tree.xpath('.//*[contains(@class,"product-attribute-label")]'):
   values=label.getparent().xpath('./*[contains(@class,"product-attribute-value")]')
   if values and clean(values[0].text_content()):add(label.text_content(),values[0].text_content())
   else:
    bits=re.split(r'(?:\xa0+| {2,})',label.text_content().strip(),maxsplit=1)
    if len(bits)==2:add(*bits)
 if pairs:result[str(p['id'])]=pairs
(DATA/'specifications.json').write_text(json.dumps(result,ensure_ascii=False,separators=(',',':')))
print('Products with explicit structured specifications:',len(result),'pairs:',sum(map(len,result.values())))
print('Example:',result.get('37'))
