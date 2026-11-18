"""Mark a new player as a lady: python3 add_lady.py <GolfID>"""
import sys,json,os
M=0xffffffff
def fnv(t):
    h=0x811c9dc5
    for b in t.encode(): h^=b; h=(h*0x01000193)&M
    return h
p=os.path.join(os.path.dirname(os.path.abspath(__file__)),'women.json');W=set(json.load(open(p)))
for i in sys.argv[1:]: W.add(f"{fnv('g|'+i.strip()):08x}")
json.dump(sorted(W),open(p,'w'));print(len(W),'ladies')
