"""Import public French catalogue pages; no credentials or private endpoints.
Run: python scripts/import_catalog.py
Requires lxml. HTML cache and progress live in /tmp/hf-catalog-cache.
"""
import urllib.request,urllib.parse,concurrent.futures,re,json,time,hashlib,collections
from pathlib import Path
from lxml import html,etree
ROOT='https://www.discounthoreca.be'; CACHE=Path('/tmp/hf-catalog-cache');CACHE.mkdir(exist_ok=True)
PROJECT=Path(__file__).resolve().parents[1]
OUT=(PROJECT/'dist' if (PROJECT/'dist').is_dir() else PROJECT)/'data'; OUT.mkdir(parents=True,exist_ok=True)
def fetch(u):
 p=CACHE/(hashlib.sha256(u.encode()).hexdigest()+'.html')
 if p.exists():return p.read_bytes()
 for attempt in range(3):
  try:
   req=urllib.request.Request(u,headers={'User-Agent':'HFConcept-CatalogPreview/1.0'})
   with urllib.request.urlopen(req,timeout=35) as r:b=r.read()
   p.write_bytes(b);return b
  except Exception:
   if attempt==2:raise
   time.sleep(1+attempt)
def txt(x):
 if not x:return ''
 try:t=html.fromstring('<div>'+x+'</div>');return '\n'.join(' '.join(z.split()) for z in t.xpath('//text()') if z.strip())
 except:return re.sub('<[^>]+>',' ',x)
def canon(u):return urllib.parse.urljoin(ROOT,u).split('#')[0]
def catid(u):
 m=re.search(r'/fr/(\d+)-[^/]*$',u.split('?')[0]);return int(m.group(1)) if m else None
def prodid(u):
 m=re.search(r'/fr/[^/]+/(\d+)-[^/]+\.html',u);return int(m.group(1)) if m else None
home=html.fromstring(fetch(ROOT+'/fr/'));cats={};family={}
for li in home.xpath('//ul[@class="menu"]/li'):
 a=li.xpath('./a');
 if not a:continue
 name=' '.join(a[0].text_content().split());id=catid(a[0].get('href',''))
 if not id:continue
 if 'armoire tables' in name.lower():name='Inox'
 if 'hotte' in name.lower():name='Hottes & ventilation'
 for x in li.xpath('.//a[@href]'):
  i=catid(x.get('href'))
  if i:cats[i]={'id':i,'name':' '.join(x.text_content().split()),'url':x.get('href'),'family':name};family[i]=name
sitemap=etree.fromstring(fetch(ROOT+'/sitemap.xml'));seed=sitemap.xpath('//*[local-name()="loc"]/text()')
products={prodid(u):u for u in seed if prodid(u)};members=collections.defaultdict(set);errors=[];pages=0
queue=set(v['url'] for v in cats.values())|{u for u in seed if catid(u)};seen=set()
def listing(u):
 t=html.fromstring(fetch(u));i=catid(u);found={};links=[]
 for a in t.xpath('//article[@data-id-product]//a[@href]'):
  url=canon(a.get('href'));pid=prodid(url)
  if pid:found[pid]=url
 for a in t.xpath('//nav[contains(@class,"pagination")]//a[@href]'):
  url=canon(a.get('href'))
  if catid(url)==i and ('?' not in url or re.search(r'\?page=\d+$',url)):links.append(url)
 h=t.xpath('//h1');name=' '.join(h[0].text_content().split()) if h else ''
 return i,found,links,name
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 while queue:
  batch=sorted(queue-seen);queue=set()
  if not batch:break
  print("CATEGORY BATCH",len(batch),flush=True)
  futures={ex.submit(listing,u):u for u in batch}
  for f in concurrent.futures.as_completed(futures):
   u=futures[f];seen.add(u);pages+=1
   try:
    i,found,links,name=f.result();products.update(found)
    for pid in found:members[pid].add(i)
    for link in links:
     if link not in seen:queue.add(link)
    if i and i not in cats:cats[i]={'id':i,'name':name,'url':u.split('?')[0],'family':''}
   except Exception as e:errors.append({'stage':'listing','url':u,'error':str(e)})
   if pages%40==0:print('LISTINGS',pages,'PRODUCTS',len(products),flush=True)
print('DISCOVERED',len(products),'products from',pages,'category pages',flush=True)
(OUT/'discovery.json').write_text(json.dumps({'products':products,'categories':cats,'pages':pages,'errors':errors},ensure_ascii=False))
def detail(item):
 pid,u=item;t=html.fromstring(fetch(u));nodes=t.xpath('//*[@id="product-details"]/@data-product')
 if not nodes:raise ValueError('No product data (removed or redirected)')
 d=json.loads(nodes[0]);actual=int(d.get('id') or d.get('id_product'))
 if actual!=pid:raise ValueError('Redirected to different product '+str(actual))
 brand='';availability=''
 for node in t.xpath('//script[@type="application/ld+json"]'):
  try:
   ld=json.loads(node.text or '{}')
   if ld.get('@type')=='Product':brand=(ld.get('brand')or{}).get('name','');availability=(ld.get('offers')or{}).get('availability','')
  except:pass
 images=[]
 for im in d.get('images',[]):
  by=im.get('bySize',{});large=by.get('large_default',{}).get('url') or im.get('large',{}).get('url')
  if large:images.append(large)
 cover=d.get('cover') or {};small=cover.get('bySize',{}).get('home_default',{}).get('url') or (images[0] if images else '')
 cat_ids=sorted(members.get(pid,set())|{int(d.get('id_category_default',0))});families=list(dict.fromkeys(cats[i]['family'] for i in cat_ids if i in cats and cats[i]['family']))
 cname=d.get('category_name','');name=d.get('name','').strip()
 features=[{'name':f.get('name',''),'value':f.get('value','')} for f in d.get('features',[])]
 price=float(d.get('price_amount') or 0);old=float(d.get('price_without_reduction') or price);tax=float(d.get('rate') or 21)
 return {'id':pid,'name':name,'reference':d.get('reference',''),'brand':brand,'category':families[0] if families else cname,'families':families,'categoryIds':cat_ids,'subcategory':cname,'price':round(price,2),'old':round(old,2),'taxRate':tax,'priceTtc':round(price*(1+tax/100),2),'discount':round(float(str(d.get('discount_percentage_absolute') or 0).replace('%','').replace(',','.')),2),'image':small,'images':images,'description':txt(d.get('description','')),'summary':txt(d.get('description_short','')),'features':features,'url':u,'sourceAvailability':d.get('availability_message',''),'availabilitySchema':availability,'availableForOrder':str(d.get('available_for_order'))=='1','attachments':[{'name':a.get('name',''),'url':ROOT+'/fr/index.php?controller=attachment&id_attachment='+str(a.get('id_attachment'))} for a in d.get('attachments',[]) if a.get('id_attachment')],'fetchedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
records=[];n=0
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
 futures={ex.submit(detail,item):item for item in products.items()}
 for f in concurrent.futures.as_completed(futures):
  pid,u=futures[f];n+=1
  try:records.append(f.result())
  except Exception as e:errors.append({'stage':'product','id':pid,'url':u,'error':str(e)})
  if n%50==0:
   print('DETAILS',n,'/',len(products),'OK',len(records),flush=True)
   (CACHE/'checkpoint.json').write_text(json.dumps(records,ensure_ascii=False))
records.sort(key=lambda p:p['id']);catalog={'source':ROOT+'/fr/','importedAt':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'count':len(records),'discoveredCount':len(products),'categoryPages':pages,'categories':list(cats.values()),'products':records,'errors':errors}
(OUT/'catalog.json').write_text(json.dumps(catalog,ensure_ascii=False,separators=(',',':')))
print('COMPLETE',len(records),'PRODUCTS',len(errors),'ERRORS','BRANDS',dict(collections.Counter(p['brand'] for p in records)),flush=True)
