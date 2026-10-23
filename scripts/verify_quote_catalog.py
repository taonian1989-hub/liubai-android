"""Check each added quotation against the archived source text, not a model response."""
import sys,json,re,hashlib,collections
from pathlib import Path
try:from source_dom import parse
except ImportError:from inspect_sources import parse
ROOT=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
if not (ROOT/'app').exists():raise RuntimeError('Run inside the Liubai project or pass its root')
def clean(t):
 t=re.sub(r'〈[^〈〉]*〉','',t);t=re.sub(r'\([^()]*\)','',t)
 return re.sub(r'\s+|\u200b|\ufeff','',t)
raw=ROOT/'data/raw/quotes_20261023';manifest=json.loads((raw/'sources.json').read_text(encoding='utf-8'))
data=json.loads((ROOT/'data/processed/quotes_1024.json').read_text(encoding='utf-8'))
assert len(data)==1024
assert len({q['id'] for q in data})==1024
assert len({re.sub(r'\W','',q['text']) for q in data})==1024
texts={};sources={s['key']:s for s in manifest}
for k in {q['sourceKey'] for q in data[24:]}:
 s=sources[k];body=(raw/s['file']).read_bytes()
 assert hashlib.sha256(body).hexdigest()==s['sha256'],f'Source snapshot changed: {k}'
 texts[k]=clean(parse(raw/s['file']).text())
for q in data[24:]:
 assert q['text'] in texts[q['sourceKey']],f'Quote not found in source: {q["id"]}'
 assert q['source'].split('#')[0]==sources[q['sourceKey']]['url']
 if q['sourceKey']!='lunyu':assert q['author']==sources[q['sourceKey']]['author']
 assert 10<=len(q['text'])<=96
 assert not re.search(r'\([^)]*\)|〈|〉|[①-⑳]|<script|mw-parser|公有领域|校勘',q['text'])
 assert not q['text'].startswith(('”','’','」','』'))
 assert q['text'].count('“')==q['text'].count('”')
report={'total':len(data),'addedSourceMatches':1000,'snapshotHashesVerified':len(texts),'uniqueIds':len(data),'uniqueTexts':len(data),'topics':dict(collections.Counter(q['topic'] for q in data))}
out=ROOT/'work/quote_catalog/provenance_verification.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(report,ensure_ascii=False,indent=2))
