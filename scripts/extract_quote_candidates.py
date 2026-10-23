import re,json,hashlib,sys,collections,difflib
from pathlib import Path
from source_dom import parse
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1];RAW=ROOT/'data/raw/quotes_20261023'
(ROOT/'work/quote_catalog').mkdir(parents=True,exist_ok=True)
SOURCES=json.loads((RAW/'sources.json').read_text(encoding='utf-8'))
bad=re.compile(r'女子|妇人|妇女|妇德|妻妾|姬妾|婢|妾|奴才|奴仆|孽|奸淫|淫欲|嫖|娼|婊|贱人|下贱|夷狄|蛮夷|愚民|贱民|好色|淫|儿孙|子孙|报应|鬼神|神明|风水|因果|鬼|妖|佛|菩萨|成佛|神仙|寿夭|夭寿|长生|疾病|疾病|治病|服药|痰|肾|阴阳|脾胃|医药|命薄|杀|诛|屠|阉|刑罚|五伦|三纲|君臣|臣子|事君|忠孝|忠臣|为官|居官|做官|皇帝|天子|为政|治国|兵戈|兵法|太守|王侯|科举|功名|进士|帝王|圣人之治|天命|道光|咸丰|工资|续刻|校勘|版本|公有领域|版权|維基|维基|Wikipedia|Publicdomain|一作|一说|一无|译者|编者|注释|原序|自序|跋曰')
meaning=re.compile(r'心|情|人|世|身|己|友|知|岁|时|生|死|得|失|静|闲|清|真|梦|言|爱|乐|悲|忧|思|欲|忍|留|放|喜|怒|风|雨|花|月|山|水|云|夜|光|书|读|学|贫|富|笑|苦|淡|无|有')
topics=[('自我与内心',r'自|己|心|反省|独|吾'),('关系与知己',r'友|人情|知己|相知|相处|交|爱|待人'),('得失与选择',r'得|失|舍|取|欲|知足|名|利|贫|富'),('时间与成长',r'岁|年|时|日|少|老|学|读|书'),('清欢与生活',r'闲|静|清|花|风|月|山|水|云|雨|夜|酒|茶'),('处世与分寸',r'言|忍|怒|容|宽|进|退|事')]
def key(t):return re.sub(r'[^\u3400-\u9fffA-Za-z0-9]','',t).replace('馀','余')
def clean(t):
 t=re.sub(r'〈[^〈〉]*〉','',t)
 t=re.sub(r'\([^()]*\)','',t)
 t=re.sub(r'\s+|\u200b|\ufeff','',t)
 return t
def ancestors(n):
 while n.p:
  n=n.p;yield n
def candidates(src):
 if src['key'] in ('zhuangzi','renjiancihua'):return []
 doc=parse(RAW/src['file']);section='';anchor='';index=0;items=[];body=False
 for n in doc.nodes():
  if n.t in ('h2','h3'):
   section=clean(n.text());anchor=n.a.get('id','')
   if src['key']=='geyanlianbi' and section=='学问类':body=True
   if src['key']=='youmengying' and ('读书宜分四时' in section or '卷上' in section):body=True
   if src['key']=='renjiancihua' and ('词以' in section or '卷上' in section):body=True
   if src['key']=='laozi' and section in ('一章','老子《道德经》上篇'):body=True
   if src['key']=='laozi' and any(x in section for x in ('跋','音义','注释')):body=False
   continue
  if src['key']=='caigentan':
   if n.t!='li' or n.p.t!='ol':continue
  else:
   if n.t!='p':continue
   if src['key'] in ('geyanlianbi','youmengying','renjiancihua','laozi') and not body:continue
  if any(a.t in ('td','th','blockquote') or set(a.a.get('class','').split())&{'noprint','licenseContainer','licensetpl','licenseBanner','reference'} for a in ancestors(n)):continue
  raw=clean(n.text());index+=1
  if len(raw)<10 or bad.search(raw):continue
  author=src['author'];base=raw
  if src['key']=='lunyu':
   m=re.fullmatch(r'([\u4e00-\u9fff]{1,4})曰[:：][“「](.+)[”」]',raw)
   if not m or m[1].endswith(('问','对','答')) or re.search(r'[“”「」曰]',m[2]):continue
   speaker=m[1];author='孔子' if speaker=='子' else speaker
   base=m[2]
  if src['key']=='renjiancihua' and re.search(r'[①-⑳“”「」《》]',raw):continue
  # Only complete sentences within one source paragraph; never join unrelated passages.
  pieces=re.findall(r'[^。！？!?]+[。！？!?]?',base)
  variants=[base] if len(base)<=96 else []
  if len(base)>96:
   variants+=pieces
   variants+=[''.join(pieces[i:i+2]) for i in range(len(pieces)-1)]
  for t in variants:
   t=t.strip('，；： ')
   if len(key(t))<10 or len(t)>96 or not meaning.search(t) or bad.search(t):continue
   if re.search(r'[A-Za-z0-9\[\]{}〈〉①-⑳]|[\U00010000-\U0010ffff]',t):continue
   if t.count('“')!=t.count('”') or t.count('「')!=t.count('」') or t.count('（')!=t.count('）') or t.count('‘')!=t.count('’'):continue
   if t.startswith(('”','’','」','』')) or t.endswith(('其致之','之','而','以','其','于')):continue
   if src['key']=='laozi' and t[-1] not in '。！？!?':continue
   if re.search(r'郭林宗|秦始皇|刘季|梁武帝|侯景|公子荆|范文正|晋文公|三代之|下民脂膏|此八字|此四字|两句|一章|可以为法|曾子曰|子曰|公曰|又云|又曰|‘|’|论语|孟子|诗经|尔雅|仪礼|春秋|左传|史记|二程|濂洛|苏黄|后主|欧阳|小晏|少游|正中|白石|东坡|康伯|稼轩|永叔|词之|诗之|词人|词体|词句|句法|韵律|词品|诗品',t):continue
   if re.search(r'官|吏|朝廷|立朝|舍人|朝代|仁宣|文愍|夏言|嘉靖|天启|康熙|雍正|乾隆|周公|子路|孔明|诸葛|管仲|冉求|伯夷|叔齐|仁政|民自|使民|有马|礼乐|雅颂|学易|易经|爻|占卜|筮|下民|脂膏|疑案|确据|殓|造福|阴德|善报|福德|朵其颐|垂其涎|灵龟|不责人|只责己|但责己|训俗|后嗣|天下贞|天下式|家规|宗族|乡邻|吾自|有子|（|）',t):continue
   if re.search(r'祖父|祖宗|家声|家门|乡党|名教|邦有道|邦无道|上临|臣下|罚|刑|三教|神|禅|释氏|释家|天将|人属|贲|威仪|作圣|宗法|小人|圣人|愚人|庸|愚夫|愚妇|一字|八字|四字|者矣|何穷|定卜|不可与|不可言|六书|三馀|三余|典午|义熙|卫玠|安刘|绛侯|文章事功|搦管|鸦鸣|牛喘|口舌是非|无不可为之事|烈火中锻|凛闲居|百行|千圣|反鲁|夫子之|谓之',t):continue
   if t[-1] in '，；：、' or t.startswith(('故曰','故云','所以然','然则','此则','其一','其二','其三','由是','于是','如此','此谓','所谓','其所谓','夫所谓','一曰','二曰','三曰')):continue
   score=10+sum(min(len(re.findall(p,t)),3) for _,p in topics)
   if 16<=len(t)<=45:score+=5
   if '；' in t or '，' in t:score+=2
   if any(x in t for x in ('圣贤','贤人','君子','小人','道德','仁义')):score-=2
   if any(x in t for x in ('此八字','此四字','此之谓','而已矣','是以','必有','必无','不可不')):score-=2
   if any(x in t for x in ('知己','知足','孤独','闲时','忙处','心事','清风','明月','山水','性情','人情','天地','世路')):score+=3
   topic=max(topics,key=lambda x:len(re.findall(x[1],t)))[0]
   locator=f'{section or src["book"]}·原文段{index}'
   item=dict(id=src['key']+'-'+hashlib.sha256(key(t).encode()).hexdigest()[:10],text=t,author=author,work=src['book'],section=locator,source=src['url']+('#'+anchor if anchor else ''),verifiedAt='2026-10-23',kind='经典摘句',topic=topic,sourceKey=src['key'],sourceParagraph=index,score=score)
   items.append(item)
 return items
allitems=[i for s in SOURCES for i in candidates(s)]
unique={}
for x in sorted(allitems,key=lambda x:(-x['score'],x['id'])):unique.setdefault(key(x['text']),x)
items=list(unique.values());counts=collections.Counter(x['sourceKey'] for x in items)
(ROOT/'work/quote_catalog/candidates.json').write_text(json.dumps(items,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'candidates':len(items),'bySource':counts,'samples':[{k:x[k] for k in ('text','author','work','score')} for x in items[:25]]},ensure_ascii=False,indent=2))
