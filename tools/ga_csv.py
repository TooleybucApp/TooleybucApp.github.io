"""Turn the two GA Connect 'Member GA Handicap Listing' CSV exports into the TSV update_hcp.py reads.
Usage: python3 ga_csv.py men.csv women.csv > handicaps.tsv
Men export: Blue, Men + Par 3, Men ticked. Women export: Red, Women + GA. Par 3, Women ticked.
Daily handicap = Blue, Men / Red, Women; GA = GA Handicap. Rows with no handicap (Pending) are skipped."""
import csv,sys
def rows(f,col,g):
    r=[x for x in csv.reader(open(f,encoding='utf-8-sig')) if x]
    h=r[0]; i=h.index(col); j=h.index('GA Handicap')
    for x in r[1:]:
        x=[v.strip().strip('=').strip('"') for v in x]
        try: float(x[i]); float(x[j])
        except ValueError: continue
        print('\t'.join([x[0],x[1],x[i],x[j],g]))
rows(sys.argv[1],'Blue, Men','M'); rows(sys.argv[2],'Red, Women','F')
