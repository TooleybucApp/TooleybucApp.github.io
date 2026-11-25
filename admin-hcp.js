/* TSC admin – golf handicap update. Browser port of tools/ga_csv.py + tools/update_hcp.py.
   Must give byte-identical output to the Python scripts (tested with node, see tools/test_admin_hcp.js). */
(function (root) {
  'use strict';
  var M = 0xffffffff;
  function utf8(s) { return new TextEncoder().encode(s); }
  function fnv(t) {
    var h = 0x811c9dc5, b = utf8(t);
    for (var i = 0; i < b.length; i++) { h ^= b[i]; h = Math.imul(h, 0x01000193) >>> 0; }
    return h >>> 0;
  }
  function hex8(n) { return ('00000000' + (n >>> 0).toString(16)).slice(-8); }
  function b64(bytes) {
    var s = '', CH = 0x8000;
    for (var i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    return btoa(s);
  }
  function enc(key, text) {
    var x = fnv('k|' + key) || 1, b = utf8(text), o = new Uint8Array(b.length);
    for (var i = 0; i < b.length; i++) {
      x = (x ^ ((x << 13) >>> 0)) >>> 0; x = (x ^ (x >>> 17)) >>> 0; x = (x ^ ((x << 5) >>> 0)) >>> 0;
      o[i] = b[i] ^ (x & 255);
    }
    return b64(o);
  }
  function norm(t) {
    t = t.normalize('NFD').replace(/\p{Mn}/gu, '').toLowerCase();
    return t.replace(/[^a-z ]/g, '').replace(/\s+/g, ' ').trim();
  }
  function cased(s) { return s.toLowerCase() !== s.toUpperCase(); }
  function isUpper(s) { var c = false; for (var ch of s) { if (cased(ch)) { c = true; if (ch !== ch.toUpperCase()) return false; } } return c; }
  function isLower(s) { var c = false; for (var ch of s) { if (cased(ch)) { c = true; if (ch !== ch.toLowerCase()) return false; } } return c; }
  function cap(w) { var a = Array.from(w); return a.length ? a[0].toUpperCase() + a.slice(1).join('').toLowerCase() : ''; }
  function tc(s) {
    s = s.trim();
    return (isUpper(s) || isLower(s)) ? s.split(/\s+/).filter(Boolean).map(cap).join(' ') : s;
  }
  function pyFloatStr(v) { return Number.isInteger(v) ? v.toFixed(1) : String(v); }
  function num(s) { s = String(s).trim(); return /^[+-]?(\d+\.?\d*|\.\d+)$/.test(s) ? parseFloat(s) : NaN; }

  // ---- CSV (GA Connect export) ----
  function parseCSV(text) {
    if (text.charCodeAt(0) === 0xfeff) text = text.slice(1);
    var rows = [], row = [], f = '', q = false;
    for (var i = 0; i < text.length; i++) {
      var c = text[i];
      if (q) {
        if (c === '"') { if (text[i + 1] === '"') { f += '"'; i++; } else q = false; }
        else f += c;
      } else if (c === '"') q = true;
      else if (c === ',') { row.push(f); f = ''; }
      else if (c === '\n' || c === '\r') {
        if (c === '\r' && text[i + 1] === '\n') i++;
        row.push(f); rows.push(row); row = []; f = '';
      } else f += c;
    }
    if (f !== '' || row.length) { row.push(f); rows.push(row); }
    return rows.filter(function (r) { return !(r.length === 1 && r[0] === '') && r.length; });
  }
  function clean(v) { return v.trim().replace(/^=+|=+$/g, '').replace(/^"+|"+$/g, ''); }
  // Returns {kind:'M'|'F', rows:[[id,name,daily,ga,g,p3]], skipped:[names]}
  function readExport(text) {
    var r = parseCSV(text); if (!r.length) throw new Error('The file is empty.');
    var h = r[0].map(function (s) { return s.trim(); });
    var kind, col, p3col;
    if (h.indexOf('Blue, Men') >= 0) { kind = 'M'; col = 'Blue, Men'; p3col = 'Par 3, Men'; }
    else if (h.indexOf('Red, Women') >= 0) { kind = 'F'; col = 'Red, Women'; p3col = 'GA. Par 3, Women'; }
    else throw new Error('This file has no "Blue, Men" or "Red, Women" column – check the tee markers were ticked before Export.');
    var i = h.indexOf(col), j = h.indexOf('GA Handicap'), k = h.indexOf(p3col);
    if (j < 0) throw new Error('This file has no "GA Handicap" column.');
    var out = [], skipped = [];
    r.slice(1).forEach(function (x) {
      x = x.map(clean);
      if (isNaN(num(x[i])) || isNaN(num(x[j]))) { if (x[1]) skipped.push(x[1]); return; }
      out.push([x[0], x[1], x[i], x[j], kind, k >= 0 ? (x[k] || '') : '']);
    });
    return { kind: kind, rows: out, skipped: skipped, hasPar3: k >= 0 };
  }

  // ---- update_hcp.py ----
  function players(tsvRows) {
    var rows = [];
    tsvRows.forEach(function (p) {
      if (p.length < 4 || !/^\d+$/.test(p[0].trim())) return;
      var name = p[1].replace(/I(?:Ã.?|Á)nson/g, "I'Anson");
      var ci = name.indexOf(','); if (ci < 0) return;
      var sur = tc(name.slice(0, ci)), first = tc(name.slice(ci + 1));
      if (sur === 'Oshea') sur = "O'Shea";
      var p3 = (p.length > 5 && /^\d+$/.test(p[5].trim())) ? p[5].trim() : '';
      rows.push({ id: p[0].trim(), first: first, sur: sur, dh: Math.trunc(num(p[2])), ga: num(p[3]), g: p[4].trim(), p3: p3 });
    });
    return rows;
  }
  function esc(s) { return s.replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  function build(rows, asat) {
    var parts = [], byn = new Map();
    rows.forEach(function (r) {
      var k = norm(r.first + ' ' + r.sur);
      if (!byn.has(k)) byn.set(k, []);
      byn.get(k).push(r);
      parts.push([hex8(fnv('i|' + r.id)), enc(r.id, r.first + '|' + r.sur + '|' + r.id + '|' + r.dh + '|' + pyFloatStr(r.ga) + '|' + r.g)]);
    });
    var dups = [];
    byn.forEach(function (v, k) {
      if (v.length > 1) dups.push(k);
      var t = v.length > 1 ? 'DUP' : (v[0].first + '|' + v[0].sur + '|' + v[0].id + '|' + v[0].dh + '|' + pyFloatStr(v[0].ga) + '|' + v[0].g);
      parts.push([hex8(fnv('i|' + k)), enc(k, t)]);
    });
    // keep insertion order and let later keys overwrite earlier ones (as a Python dict does)
    var order = [], val = {};
    parts.forEach(function (kv) { if (!(('#' + kv[0]) in val)) order.push(kv[0]); val['#' + kv[0]] = kv[1]; });
    var json = '{"as_at": ' + JSON.stringify(asat) + ', "r": {' + order.map(function (k) { return JSON.stringify(k) + ': ' + JSON.stringify(val['#' + k]); }).join(', ') + '}}';
    var lad = rows.map(function (r, i) { return [r, i]; }).sort(function (a, b) {
      return a[0].ga - b[0].ga || (a[0].sur < b[0].sur ? -1 : a[0].sur > b[0].sur ? 1 : 0) || a[1] - b[1];
    }).map(function (a) { return a[0]; });
    var body = lad.map(function (r, i) {
      return '<tr class="' + (r.g === 'F' ? 'lf' : 'lm') + '"><td>' + (i + 1) + '</td><td>' + r.first + ' ' + Array.from(r.sur)[0] + '.</td><td>' + r.dh + '</td><td>' + (r.p3 || '–') + '</td><td>' + r.ga.toFixed(1) + '</td></tr>';
    }).join('');
    return { json: json, body: body, dups: dups, ladder: lad };
  }
  var MON = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  function nice(asat) { var p = asat.split('-'); return (+p[2]) + ' ' + MON[+p[1] - 1] + ' ' + p[0]; }
  function apply(html, rows, asat) {
    var b = build(rows, asat), n = nice(asat);
    var s = html;
    var before = s;
    s = s.replace(/(<script id="hcp-data" type="application\/json">)[\s\S]*?(<\/script>)/, function (m, a, c) { return a + b.json + c; });
    if (s === before) throw new Error('Could not find the handicap data in the app page.');
    s = s.split('<th>Daily</th><th>GA</th>').join('<th>TSC Daily</th><th>Par 3</th><th>GA</th>');
    before = s;
    s = s.replace(/(<tbody id="lad-b">)[\s\S]*?(<\/tbody>)/, function (m, a, c) { return a + b.body + c; });
    if (s === before && html.indexOf('<tbody id="lad-b">') < 0) throw new Error('Could not find the handicap ladder in the app page.');
    s = s.replace(/as at \d{1,2} [A-Z][a-z]{2} \d{4}( · updated (?:every Friday|Tuesdays &amp; Fridays))/g, function (m, a) { return 'as at ' + n + a; });
    s = s.replace(/Handicap ladder · as at \d{1,2} [A-Z][a-z]{2} \d{4}/g, 'Handicap ladder · as at ' + n);
    s = s.replace(/\d+ players · updated (every Friday|Tuesdays &amp; Fridays)/g, rows.length + ' players · updated Tuesdays &amp; Fridays');
    return { html: s, dups: b.dups, ladder: b.ladder, players: rows.length, ladies: rows.filter(function (r) { return r.g === 'F'; }).length };
  }
  // Current ladder rows from the live page: [{name, dh, p3, ga, g}]
  function currentLadder(html) {
    var m = html.match(/<tbody id="lad-b">([\s\S]*?)<\/tbody>/); if (!m) return [];
    var re = /<tr class="(l[fm])"><td>\d+<\/td><td>([^<]*)<\/td><td>([^<]*)<\/td><td>([^<]*)<\/td><td>([^<]*)<\/td><\/tr>/g, out = [], x;
    while ((x = re.exec(m[1]))) out.push({ g: x[1] === 'lf' ? 'F' : 'M', name: x[2], dh: x[3], p3: x[4], ga: x[5] });
    return out;
  }
  function currentAsAt(html) { var m = html.match(/"as_at": "([0-9-]+)"/); return m ? m[1] : ''; }
  root.TSCHcp = { readExport: readExport, players: players, apply: apply, currentLadder: currentLadder, currentAsAt: currentAsAt, nice: nice, b64: b64 };
})(typeof window !== 'undefined' ? window : globalThis);
