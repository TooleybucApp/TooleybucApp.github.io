"""Ladies-only golf handicap update (John's new layout, 19 Nov 2026).
Usage: python3 update_ladies.py ladies.tsv YYYY-MM-DD index.html [more.html]
ladies.tsv: GolfID<TAB>Surname, First<TAB>Daily (Red, Women)<TAB>GA Handicap  - rows with no number are skipped.
Men's rows/data already in the app are kept as they are; ladies are replaced, the ladder re-sorted.
New ladies are added to women.json automatically (this sheet is ladies only)."""
import sys,re,json,os,datetime
sys.argv,args=sys.argv[:1],sys.argv[1:]
here=os.path.dirname(os.path.abspath(__file__))
exec(open(os.path.join(here,'update_hcp.py')).read().split('tsv,asat=sys.argv')[0])  # fnv, norm, enc, tc
tsv,asat,files=args[0],args[1],args[2:]
wpath=os.path.join(here,'women.json'); W=json.load(open(wpath))
rows=[]
for line in open(tsv,encoding='utf-8'):
    p=line.rstrip('\n').split('\t')
    if len(p)<4 or not p[0].strip().isdigit(): continue
    try: dh=int(float(p[2])); ga=float(p[3])
    except ValueError: continue
    name=re.sub(r"IÃ.?nson","I'Anson",p[1]); sur,first=[tc(x) for x in name.split(',',1)]
    gid=p[0].strip(); h=f"{fnv('g|'+gid):08x}"
    if h not in W: W.append(h); print('new lady added to women.json:',first,sur)
    rows.append(dict(id=gid,first=first,sur=sur,dh=dh,ga=ga))
json.dump(W,open(wpath,'w'))
d=datetime.date.fromisoformat(asat); nice=f"{d.day} {d.strftime('%b %Y')}"
for f in files:
    s=open(f,encoding='utf-8').read()
    data=json.loads(re.search(r'<script id="hcp-data" type="application/json">(.*?)</script>',s,re.S).group(1))
    R=data['r']
    for r in rows:
        v=f"{r['first']}|{r['sur']}|{r['id']}|{r['dh']}|{r['ga']}|F"
        R[f"{fnv('i|'+r['id']):08x}"]=enc(r['id'],v)
        k=norm(r['first']+' '+r['sur']); R[f"{fnv('i|'+k):08x}"]=enc(k,v)
    body=re.search(r'<tbody id="lad-b">(.*?)</tbody>',s,re.S).group(1)
    old=re.findall(r'<tr class="(l[fm])"><td>\d+</td><td>(.*?)</td><td>(.*?)</td><td>(.*?)</td></tr>',body)
    men=[dict(g='M',n=n,dh=int(dh),ga=float(ga)) for c,n,dh,ga in old if c=='lm']
    lad=men+[dict(g='F',n=f"{r['first']} {r['sur'][0]}.",dh=r['dh'],ga=r['ga']) for r in rows]
    lad.sort(key=lambda r:r['ga'])
    nb=''.join(f"<tr class=\"{'lf' if r['g']=='F' else 'lm'}\"><td>{i}</td><td>{r['n']}</td><td>{r['dh']}</td><td>{r['ga']:.1f}</td></tr>" for i,r in enumerate(lad,1))
    s=re.sub(r'(<script id="hcp-data" type="application/json">).*?(</script>)',lambda m:m.group(1)+json.dumps({"as_at":asat,"r":R})+m.group(2),s,count=1,flags=re.S)
    s=re.sub(r'(<tbody id="lad-b">).*?(</tbody>)',lambda m:m.group(1)+nb+m.group(2),s,count=1,flags=re.S)
    s=re.sub(r'as at \d{1,2} [A-Z][a-z]{2} \d{4}( · updated every Friday)',f'as at {nice}\\1',s)
    s=re.sub(r'Handicap ladder · as at \d{1,2} [A-Z][a-z]{2} \d{4}',f'Handicap ladder · as at {nice}',s)
    s=re.sub(r'\d+ players · updated every Friday',f'{len(lad)} players · updated every Friday',s)
    open(f,'w',encoding='utf-8').write(s)
    print(f"{f}: {len(lad)} players ({len(rows)} ladies, {len(men)} men kept), as at {nice}")
