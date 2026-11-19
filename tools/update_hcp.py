"""Weekly golf handicap update. Usage: python3 update_hcp.py handicaps.tsv YYYY-MM-DD index.html [more.html]
handicaps.tsv: one row per player: GolfID<TAB>Surname, First<TAB>DailyHcp<TAB>GAIndex[<TAB>M|F<TAB>Par3Daily] (from 'Golf handicaps' sheet, Golf Cart Options.xlsx)."""
import sys,re,json,base64,unicodedata,datetime
M=0xffffffff
def fnv(t):
    h=0x811c9dc5
    for b in t.encode(): h^=b; h=(h*0x01000193)&M
    return h
def norm(t):
    t=unicodedata.normalize('NFD',t); t=''.join(c for c in t if unicodedata.category(c)!='Mn').lower()
    return re.sub(r'\s+',' ',re.sub(r'[^a-z ]','',t)).strip()
def enc(key,text):
    x=fnv('k|'+key) or 1; o=bytearray()
    for b in text.encode(): x^=(x<<13)&M; x^=x>>17; x^=(x<<5)&M; o.append(b^(x&255))
    return base64.b64encode(bytes(o)).decode()
def tc(s):
    s=s.strip(); return ' '.join(w.capitalize() for w in s.split()) if (s.isupper() or s.islower()) else s
tsv,asat=sys.argv[1],sys.argv[2]
import os
WOMEN=set(json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'women.json'))))  # hashed Golf IDs of ladies (peach rows); add new ladies with add_lady.py
rows=[]
for line in open(tsv,encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if len(p)<4 or not p[0].strip().isdigit(): continue
    name=re.sub(r"I(?:Ã.?|Á)nson","I'Anson",p[1])
    sur,first=[tc(x) for x in name.split(',',1)]
    if sur=='Oshea': sur="O'Shea"
    gid=p[0].strip()
    rows.append(dict(id=gid,first=first,sur=sur,dh=int(float(p[2])),ga=float(p[3]),g=(p[4].strip() if len(p)>4 and p[4].strip() in ('M','F') else ('F' if f"{fnv('g|'+gid):08x}" in WOMEN else 'M')),p3=(p[5].strip() if len(p)>5 and p[5].strip().isdigit() else '')))
R={};byn={}
for r in rows:
    byn.setdefault(norm(r['first']+' '+r['sur']),[]).append(r)
    R[f"{fnv('i|'+r['id']):08x}"]=enc(r['id'],f"{r['first']}|{r['sur']}|{r['id']}|{r['dh']}|{r['ga']}|{r['g']}")
for k,v in byn.items():
    R[f"{fnv('i|'+k):08x}"]=enc(k,'DUP' if len(v)>1 else f"{v[0]['first']}|{v[0]['sur']}|{v[0]['id']}|{v[0]['dh']}|{v[0]['ga']}|{v[0]['g']}")
lad=sorted(rows,key=lambda r:(r['ga'],r['sur']))
body=''.join(f"<tr class=\"{'lf' if r['g']=='F' else 'lm'}\"><td>{i}</td><td>{r['first']} {r['sur'][0]}.</td><td>{r['dh']}</td><td>{r['p3'] or '–'}</td><td>{r['ga']:.1f}</td></tr>" for i,r in enumerate(lad,1))
d=datetime.date.fromisoformat(asat); nice=f"{d.day} {d.strftime('%b %Y')}"
for f in sys.argv[3:]:
    s=open(f,encoding='utf-8').read()
    s=re.sub(r'(<script id="hcp-data" type="application/json">).*?(</script>)',lambda m:m.group(1)+json.dumps({"as_at":asat,"r":R})+m.group(2),s,count=1,flags=re.S)
    s=s.replace('<th>Daily</th><th>GA</th>','<th>TSC Daily</th><th>Par 3</th><th>GA</th>')
    s=re.sub(r'(<tbody id="lad-b">).*?(</tbody>)',lambda m:m.group(1)+body+m.group(2),s,count=1,flags=re.S)
    s=re.sub(r'as at \d{1,2} [A-Z][a-z]{2} \d{4}( · updated (?:every Friday|Tuesdays &amp; Fridays))',f'as at {nice}\\1',s)
    s=re.sub(r'Handicap ladder · as at \d{1,2} [A-Z][a-z]{2} \d{4}',f'Handicap ladder · as at {nice}',s)
    s=re.sub(r'\d+ players · updated (every Friday|Tuesdays &amp; Fridays)',lambda m:f'{len(rows)} players · updated Tuesdays &amp; Fridays',s)
    open(f,'w',encoding='utf-8').write(s)
print(f"{len(rows)} players ({sum(r['g']=='F' for r in rows)} ladies), as at {nice}; duplicate names: {[k for k,v in byn.items() if len(v)>1]}")
