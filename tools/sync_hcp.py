"""Copy the golf handicap data from one copy of the app to another (e.g. live GitHub index.html -> Claude artifact HTML).
Usage: python3 sync_hcp.py FROM.html TO.html   – only copies when FROM's as_at is newer (or same date but different data).
Copies: <script id="hcp-data">, ladder <tbody id="lad-b">, the "as at" dates and the "<n> players" line. Prints what it did."""
import re,sys,json
src=open(sys.argv[1],encoding='utf-8').read(); dst=open(sys.argv[2],encoding='utf-8').read()
H=r'(<script id="hcp-data" type="application/json">)(.*?)(</script>)'; L=r'(<tbody id="lad-b">)(.*?)(</tbody>)'
hs=re.search(H,src,re.S); hd=re.search(H,dst,re.S)
if not hs or not hd: sys.exit('hcp-data block missing in '+('FROM' if not hs else 'TO'))
a_s=json.loads(hs.group(2))['as_at']; a_d=json.loads(hd.group(2))['as_at']
if a_s<a_d or (a_s==a_d and hs.group(2)==hd.group(2)):
    print(f'no change (FROM as_at {a_s}, TO as_at {a_d})'); sys.exit(0)
out=dst.replace(hd.group(0),hs.group(0),1)
ls=re.search(L,src,re.S); out=re.sub(L,lambda m:ls.group(0),out,count=1,flags=re.S)
out=out.replace('<th>Daily</th><th>GA</th>','<th>TSC Daily</th><th>Par 3</th><th>GA</th>')
for pat in [r'as at \d{1,2} [A-Z][a-z]{2} \d{4}(?= · updated )',r'Handicap ladder · as at \d{1,2} [A-Z][a-z]{2} \d{4}',r'\d+ players · updated (?:every Friday|Tuesdays &amp; Fridays)']:
    m=re.search(pat,src)
    if m: out=re.sub(pat,lambda _:m.group(0),out)
open(sys.argv[2],'w',encoding='utf-8').write(out)
n=len(re.findall(r'<tr class="l[fm]">',ls.group(2)))
print(f'synced handicaps as at {a_s} ({n} players) – was {a_d}')
