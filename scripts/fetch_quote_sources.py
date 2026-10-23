import concurrent.futures,json,hashlib,sys,urllib.request,urllib.parse
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[1]
(ROOT/'data/raw/quotes_20261023').mkdir(parents=True,exist_ok=True)
SOURCES=[
 ('caigentan','菜根譚','洪应明','菜根谭'),
 ('weiluyahua','圍爐夜話','王永彬','围炉夜话'),
 ('youmengying','幽夢影','张潮','幽梦影'),
 ('geyanlianbi','格言聯璧','金缨（辑）','格言联璧'),
 ('lunyu','論語/全覽','孔子及门人','论语'),
 ('laozi','道德經_(王弼本)','老子','道德经'),
 ('renjiancihua','人間詞話','王国维','人间词话'),
 ('zhuangzi','莊子','庄子及后学','庄子'),
]
def fetch(s):
 key,title,author,book=s;url='https://zh.wikisource.org/zh-hans/'+urllib.parse.quote(title,safe='')
 f=ROOT/'data/raw/quotes_20261023'/f'{key}.html'
 if not f.exists():
  req=urllib.request.Request(url,headers={'User-Agent':'LiubaiQuoteLibrary/0.1.1 (personal reference collection)'})
  with urllib.request.urlopen(req,timeout=45) as r:body=r.read()
  f.write_bytes(body)
 body=f.read_bytes();return dict(key=key,title=title,author=author,book=book,url=url,file=f.name,sha256=hashlib.sha256(body).hexdigest(),bytes=len(body))
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
 result=list(pool.map(fetch,SOURCES))
(ROOT/'data/raw/quotes_20261023/sources.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps([{k:v for k,v in s.items() if k in ('key','bytes')} for s in result],ensure_ascii=False))
