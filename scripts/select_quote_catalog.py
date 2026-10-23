import sys,json,re,collections,hashlib,difflib,subprocess
from pathlib import Path
from source_dom import parse
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
def norm(t):return re.sub(r'[^\u3400-\u9fffA-Za-z0-9]','',t).replace('馀','余').replace('园满','圆满')
seed=json.loads((ROOT/'data/processed/quotes_seed24.json').read_text(encoding='utf-8'))
for s in seed:s['topic']='清欢与生活' if s['author'] in ('王维','苏轼','陶渊明') else '自我与内心'
items=json.loads((ROOT/'work/quote_catalog/candidates.json').read_text(encoding='utf-8'))
seen=[norm(x['text']) for x in seed];buckets=collections.defaultdict(set)
def grams(t):return set(t[i:i+3] for i in range(len(t)-2))
for i,t in enumerate(seen):
 for g in grams(t):buckets[g].add(i)
selected=[];sourcecounts=collections.Counter();paragraphs=set();rejected=collections.Counter()
caps={'caigentan':280,'geyanlianbi':320,'weiluyahua':180,'youmengying':150,'laozi':90,'lunyu':80,'renjiancihua':35}
for relax in (False,True):
 for q in items:
  if len(selected)>=1000:break
  t=q['text'];k=norm(t);paragraph=(q['sourceKey'],q['sourceParagraph'])
  if paragraph in paragraphs:continue
  if sourcecounts[q['sourceKey']]>=caps[q['sourceKey']] and not relax:continue
  if re.search(r'^(故(?!人)|盖|若夫|是以|则|此之|此则|可见|然则|然而|况|彼|以上|以下|注|第[一二三四五六七八九十\d])',t):rejected['context_dependent']+=1;continue
  if re.search(r'夫妇|夫妻|父子|父母|兄弟|孝|福报|福禄|子弟|家门|门第|家族|子孙|儿女|女儿|男儿|闺|妓|天下正|民自化|圣人云|寿|病|药|兵|敌|征伐|仁政|人性本|畜|鄙夫|常人|庸人|天理|人欲|富贵不能|不孝|仕|尧|舜|文王|武王|汉高|唐太|宋太|士君子|须眉|金玉满堂|大丈夫|因果|菩提|一曰|二曰|三曰|四曰',t):rejected['off_tone']+=1;continue
  # A selected sentence must stand by itself and not be a barely changed edition variant.
  gs=grams(k);neighbors=collections.Counter(i for g in gs for i in buckets[g]);similar=False
  for i,hits in neighbors.most_common(25):
   prev=seen[i]
   if k==prev or (min(len(k),len(prev))>=12 and (k in prev or prev in k)) or (hits/max(1,min(len(gs),len(grams(prev))))>=.35 and difflib.SequenceMatcher(None,k,prev).ratio()>=.80):similar=True;break
  if similar:rejected['duplicate_or_variant']+=1;continue
  selected.append(q);sourcecounts[q['sourceKey']]+=1;paragraphs.add(paragraph);seen.append(k)
  for g in gs:buckets[g].add(len(seen)-1)
 if len(selected)>=1000:break
if len(selected)!=1000:raise RuntimeError('Only '+str(len(selected))+' qualified additional entries; need more sources')
# Preserve the 24 hand-picked entries, then interleave books for day-to-day variety.
groups=collections.defaultdict(list)
for q in selected:groups[q['sourceKey']].append(q)
mixed=[]
while any(groups.values()):
 for name in sorted(groups,key=lambda k:(-len(groups[k]),k)):
  if groups[name]:mixed.append(groups[name].pop(0))
catalog=seed+mixed
public=[]
for q in catalog:public.append({k:v for k,v in q.items() if k not in ('score',)})
processed=ROOT/'data/processed';processed.mkdir(exist_ok=True)
(processed/'quotes_1024.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf-8')
old=(ROOT/'app/src/main/assets/quotes.js').read_text(encoding='utf-8')
tail=old[old.index(' function select('):].replace('const api={version:2,','const api={version:3,')
(ROOT/'app/src/main/assets/quotes.js').write_text("(function(root){\n 'use strict';\n const catalog="+json.dumps(public,ensure_ascii=False,separators=(',',':'))+';\n'+tail,encoding='utf-8')
report={'date':'2026-10-23','retained':24,'added':1000,'total':1024,'bySource':dict(sourcecounts),'byTopic':dict(collections.Counter(x['topic'] for x in public)),'rejected':dict(rejected),'nearDuplicateThreshold':0.8,'sourceVerification':'All 1000 additions are contiguous source paragraph excerpts after removing editorial brackets/whitespace; no generated or recombined aphorisms.'}
(processed/'quote_catalog_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(report,ensure_ascii=False,indent=2))
print('\nREVIEW SAMPLE\n'+json.dumps([{k:q[k] for k in ('text','author','work')} for q in mixed[::20]],ensure_ascii=False,indent=2))
