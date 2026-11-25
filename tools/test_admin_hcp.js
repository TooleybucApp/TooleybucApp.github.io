// Check admin-hcp.js gives the same page as ga_csv.py + update_hcp.py.
// Usage: node tools/test_admin_hcp.js men.csv ladies.csv before.html expected.html YYYY-MM-DD
const fs=require('fs');require('../admin-hcp.js');const H=globalThis.TSCHcp;
const [men,lad,before,expect,date]=process.argv.slice(2);
const a=H.readExport(fs.readFileSync(men,'utf8')),b=H.readExport(fs.readFileSync(lad,'utf8'));
const exps=[a,b].sort((x,y)=>x.kind==='M'?-1:1);
const rows=H.players(exps[0].rows.concat(exps[1].rows));
const out=H.apply(fs.readFileSync(before,'utf8'),rows,date);
const ok=out.html===fs.readFileSync(expect,'utf8');
console.log(out.players,'players',out.ladies,'ladies dups',out.dups,'skipped',a.skipped,b.skipped,ok?'IDENTICAL':'DIFFERENT');
if(!ok){fs.writeFileSync('/tmp/claude-0/t/js.html',out.html);process.exit(1)}
