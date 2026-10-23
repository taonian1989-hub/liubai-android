from html.parser import HTMLParser
from pathlib import Path
class N:
 def __init__(self,t='',a=None,p=None):self.t=t;self.a=dict(a or []);self.p=p;self.c=[]
 def text(self):
  if self.t in {'style','script','sup'} or {'mw-editsection','reference','mw-cite-backlink','noprint'}.intersection(self.a.get('class','').split()):return ''
  return ''.join(c if isinstance(c,str) else c.text() for c in self.c)
 def nodes(self):
  yield self
  for c in self.c:
   if isinstance(c,N):yield from c.nodes()
class P(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.root=N();self.cur=self.root
 def handle_starttag(self,t,a):
  n=N(t,a,self.cur);self.cur.c.append(n)
  if t not in {'br','hr','img','meta','link','input','wbr','source','area','base','embed','param'}:self.cur=n
 def handle_endtag(self,t):
  n=self.cur
  while n.p and n.t!=t:n=n.p
  if n.p:self.cur=n.p
 def handle_data(self,s):self.cur.c.append(s)
def parse(file):
 p=P();p.feed(Path(file).read_text(encoding='utf-8'));return max((n for n in p.root.nodes() if 'mw-parser-output' in n.a.get('class','').split()),key=lambda n:len(n.text()))
if __name__=='__main__':
 import sys
 root=parse(sys.argv[1]);i=0
 for n in root.nodes():
  if n.t in {'p','dd','li','h2','h3'}:
   s=n.text().strip()
   if s and len(s)>4:
    print(n.t,str(n.a),repr(s[:240]));i+=1
    if i>=45:break
