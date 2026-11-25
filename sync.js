// 端末間の同期(章別版・Day別版の共通)。
// 進み具合は今までどおり端末のブラウザ(localStorage)に保存し、それを Supabase に送って、
// 同じ「同期コード」を使う別の端末と合わせる。項目(カード1枚・ページ1つ…)ごとに新しい方を残す。
// ページより先に読み込む(<head> 内)。読み込めなくてもアプリは今までどおり動く。
(function(){
'use strict';
const URL_ = 'https://luddhhtgzqmesxlosgok.supabase.co/rest/v1/rpc/';
const KEY  = 'sb_publishable_OZQIVjV5kMPM6WjP-Qh2qw_ezUGPPLj';
// 同期するキー。図の幅・図を畳むかなど、画面の大きさで変わる設定は端末ごとのまま。
const SYNC  = ['neuro-srs-day','neuro-prog-day','neuro-last-day','neuro-readpos-day','neuro-hl-day',
               'neuro-prog-chapter','neuro-last-chapter'];
const WHOLE = new Set(['neuro-last-day','neuro-last-chapter']);   // 中身を分けずに丸ごと1項目として扱うキー
const CODE_KEY = 'nsync-code', META_KEY = 'nsync-meta';
const ABC = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

let ls; try { ls = window.localStorage; ls.getItem('x'); } catch(e) { return; }
const P = Storage.prototype, oGet = P.getItem, oSet = P.setItem, oRem = P.removeItem;
const rawGet = k => oGet.call(ls, k), rawSet = (k, v) => oSet.call(ls, k, v);
const isSync = (st, k) => st === ls && SYNC.indexOf(String(k)) >= 0;
const parse = s => { try { return s == null ? null : JSON.parse(s); } catch(e) { return null; } };
const asMap = v => (v && typeof v === 'object' && !Array.isArray(v)) ? v : {};
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);
// キーの中身を {項目名: 値} の形で見る(丸ごとのキーは項目名 '')
const entries = (k, v) => WHOLE.has(k) ? (v == null ? {} : {'': v}) : asMap(v);
// まだ同期していない記録に付ける時刻。分かるものは実際の時刻に近い値、分からないものは 1(どの新しい記録にも負ける)
function stampOf(k, v){
  if (!v || typeof v !== 'object') return 1;
  if (typeof v.t === 'number' && v.t > 1e12) return v.t;
  if (k === 'neuro-srs-day' && typeof v.d === 'number') {        // Anki 方式のカード:最後に答えたおおよその時刻
    const t = v.q === 2 && typeof v.i === 'number' ? (v.d - v.i) * 864e5 : v.d > 1e12 ? v.d - 6e5 : 1;
    return Math.max(1, Math.min(t, Date.now() - 1));
  }
  return 1;
}

let meta = asMap(parse(rawGet(META_KEY)));
meta.seq = meta.seq || 0; meta.st = asMap(meta.st); meta.dirty = asMap(meta.dirty);
const saveMeta = () => { try { rawSet(META_KEY, JSON.stringify(meta)); } catch(e) {} };
let code = (rawGet(CODE_KEY) || '').replace(/[^A-Z2-9]/g, '');
function newCode(){ const a = new Uint32Array(24); crypto.getRandomValues(a); return Array.from(a, x => ABC[x % 32]).join(''); }
if (code.length < 20) { code = newCode(); rawSet(CODE_KEY, code); }

let clock = 0;   // 同じミリ秒に2回変えても順番が付くように
const now = () => (clock = Math.max(Date.now(), clock + 1));
function mark(k, sk, t){ (meta.st[k] = meta.st[k] || {})[sk] = t; (meta.dirty[k] = meta.dirty[k] || {})[sk] = 1; }

// 初回:今ある記録をすべて「古い記録」として送る(別の端末の新しい記録には負ける)
if (!meta.init) {
  SYNC.forEach(k => { const E = entries(k, parse(rawGet(k)));
    Object.keys(E).forEach(sk => { if (meta.st[k] && meta.st[k][sk] != null) return; mark(k, sk, stampOf(k, E[sk])); }); });
  meta.init = 1; saveMeta();
}

// ---- アプリの読み書きを横から見る ----
// base = アプリが最後に読んだ・書いた中身。アプリが書いたときは base との差だけを「アプリの変更」とし、
// 別の端末から届いた項目(アプリはまだ知らない)を古い中身で上書きしないようにする。
const base = {};
P.getItem = function(k){ const v = oGet.call(this, k); if (isSync(this, k)) base[k] = parse(v); return v; };
P.setItem = function(k, v){ if (!isSync(this, k)) return oSet.call(this, k, v); write(String(k), parse(v)); };
P.removeItem = function(k){ if (!isSync(this, k)) return oRem.call(this, k); write(String(k), null); };

function write(k, next){
  const curV = parse(rawGet(k));
  const was = entries(k, k in base ? base[k] : curV), nu = entries(k, next);
  let out = WHOLE.has(k) ? curV : Object.assign({}, asMap(curV));
  const diff = [];
  new Set(Object.keys(was).concat(Object.keys(nu))).forEach(sk => {
    const a = was[sk], b = nu[sk];
    if (same(a, b)) return;
    diff.push(sk);
    if (WHOLE.has(k)) out = b == null ? null : b;
    else if (b === undefined) delete out[sk]; else out[sk] = b;
  });
  // 先に保存する(容量超過などはアプリと同じく例外で知らせ、そのときは送らない)
  if (out == null) oRem.call(ls, k); else oSet.call(ls, k, JSON.stringify(out));
  base[k] = next;
  if (diff.length) { diff.forEach(sk => mark(k, sk, now())); saveMeta(); soon(); }
}

// ---- サーバーとのやり取り ----
async function rpc(fn, body, keepalive){
  const r = await fetch(URL_ + fn, { method: 'POST', keepalive: !!keepalive,
    headers: { apikey: KEY, Authorization: 'Bearer ' + KEY, 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
  if (!r.ok) throw new Error('HTTP ' + r.status);
  return r.json();
}
function pending(){ const out = [];
  Object.keys(meta.dirty).forEach(k => { const E = entries(k, parse(rawGet(k)));
    Object.keys(meta.dirty[k]).forEach(sk => out.push({ k, sk, v: E[sk] === undefined ? null : E[sk], t: (meta.st[k] || {})[sk] || 1 })); });
  return out; }
async function push(keepalive){
  const items = pending(); if (!items.length) return;
  for (let i = 0; i < items.length; i += 1500) {
    const part = items.slice(i, i + 1500);
    await rpc('sync_push', { p_code: code, p_items: part }, keepalive && items.length <= 300);
    part.forEach(x => { if ((meta.st[x.k] || {})[x.sk] === x.t && meta.dirty[x.k]) { delete meta.dirty[x.k][x.sk];
      if (!Object.keys(meta.dirty[x.k]).length) delete meta.dirty[x.k]; } });
    saveMeta();
  }
}
async function pull(){
  const changed = new Set();
  for (let guard = 0; guard < 50; guard++) {
    const r = await rpc('sync_pull', { p_code: code, p_since: meta.seq });
    const byKey = {};
    (r.items || []).forEach(x => { meta.seq = Math.max(meta.seq, x.seq);
      if (SYNC.indexOf(x.k) < 0) return;
      const mine = (meta.st[x.k] || {})[x.sk];
      if (mine != null && mine >= x.t) return;          // こちらの方が新しい(または同じ)
      (byKey[x.k] = byKey[x.k] || []).push(x); });
    Object.keys(byKey).forEach(k => {
      let v = parse(rawGet(k));
      if (!WHOLE.has(k)) v = Object.assign({}, asMap(v));
      byKey[k].forEach(x => {
        (meta.st[k] = meta.st[k] || {})[x.sk] = x.t;
        if (meta.dirty[k]) delete meta.dirty[k][x.sk];
        if (WHOLE.has(k)) v = x.v; else if (x.v == null) delete v[x.sk]; else v[x.sk] = x.v;
      });
      try { if (v == null) oRem.call(ls, k); else rawSet(k, JSON.stringify(v)); changed.add(k); } catch(e) {}
    });
    saveMeta();
    if (!r.more) break;
  }
  if (changed.size) window.dispatchEvent(new CustomEvent('neuro-sync', { detail: { keys: [...changed] } }));
}

const S = { state: 'idle', last: Number(rawGet('nsync-last')) || 0, err: '' };
let running = null, again = false, timer = 0;
function sync(){
  if (running) { again = true; return running; }
  running = (async () => {
    do { again = false; setState('busy');
      try { await pull(); await push(); S.last = Date.now(); rawSet('nsync-last', String(S.last)); S.err = ''; setState('ok'); }
      catch(e) { S.err = navigator.onLine === false ? 'offline' : 'error'; setState('err'); }
    } while (again);
    running = null;
  })();
  return running;
}
function soon(){ clearTimeout(timer); timer = setTimeout(sync, 3000); }
document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'hidden') { clearTimeout(timer); push(true).catch(() => {}); } else sync(); });
window.addEventListener('pagehide', () => { push(true).catch(() => {}); });
window.addEventListener('online', sync);
setInterval(() => { if (document.visibilityState === 'visible') sync(); }, 60000);

// 別の端末の同期コードにつなぐ。この端末の記録も全部送り直して合わせる。
async function link(c){
  c = String(c || '').toUpperCase().replace(/[^A-Z2-9]/g, '');
  if (c.length < 20) throw new Error('short');
  if (c === code) return;
  code = c; rawSet(CODE_KEY, code); meta.seq = 0;
  SYNC.forEach(k => { const E = entries(k, parse(rawGet(k)));
    Object.keys(E).forEach(sk => { const t = (meta.st[k] || {})[sk] || stampOf(k, E[sk]); mark(k, sk, t); }); });
  saveMeta(); await sync(); if (S.state === 'err') throw new Error('net');
}

// ---- 画面 ----
const grp = c => c.match(/.{1,4}/g).join('-');
const linkURL = () => location.origin + location.pathname.replace(/day\/(index\.html)?$/, '').replace(/index\.html$/, '') + 'day/#sync=' + code;
function hhmm(t){ const d = new Date(t); return d.getHours() + ':' + String(d.getMinutes()).padStart(2, '0'); }
function stateText(){
  if (S.state === 'busy') return '同期中…';
  if (S.state === 'err') return S.err === 'offline' ? 'オフライン(つながったら送ります)' : '同期できませんでした(あとで再試行)';
  return S.last ? '同期済み ' + hhmm(S.last) : '同期の準備中';
}
let btn = null, dlg = null;
function setState(s){ S.state = s; if (btn) btn.querySelector('small').textContent = stateText(); if (dlg && dlg.open) $q('#nsState').textContent = stateText(); }
const $q = s => dlg.querySelector(s);
const CSS = `
.nsync{display:flex;align-items:center;gap:8px;width:100%;margin-top:2px;background:none;border:1px dashed var(--line,#ccc);border-radius:10px;padding:8px 12px;color:var(--muted,#666);font-size:.85rem;cursor:pointer;text-align:left}
.nsync b{color:var(--ink,#222);font-weight:600}.nsync small{margin-left:auto;font-size:.78rem}
.nsdlg{border:1px solid var(--line,#ccc);border-radius:14px;padding:0;max-width:440px;width:calc(100% - 32px);background:var(--surface,#fff);color:var(--ink,#222)}
.nsdlg::backdrop{background:rgba(0,0,0,.35)}
.nsdlg .in{padding:18px 18px 14px;display:flex;flex-direction:column;gap:12px;font-size:.92rem;line-height:1.6}
.nsdlg h2{margin:0;font-size:1.05rem}.nsdlg p{margin:0}.nsdlg .mut{color:var(--muted,#666);font-size:.82rem}
.nsdlg .code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:1.02rem;letter-spacing:.04em;background:var(--paper,#f4f4f4);border:1px solid var(--line,#ccc);border-radius:8px;padding:8px 10px;user-select:all;word-break:break-all}
.nsdlg .row{display:flex;gap:8px;flex-wrap:wrap}
.nsdlg button{border:1px solid var(--line,#ccc);background:var(--paper,#f4f4f4);color:var(--ink,#222);border-radius:8px;padding:8px 12px;font-size:.88rem;cursor:pointer}
.nsdlg button.go{background:var(--violet,#5b4bd6);border-color:var(--violet,#5b4bd6);color:#fff}
.nsdlg input{flex:1;min-width:0;font:inherit;font-family:ui-monospace,Menlo,Consolas,monospace;border:1px solid var(--line,#ccc);border-radius:8px;padding:8px 10px;background:var(--surface,#fff);color:var(--ink,#222)}
.nsdlg hr{border:none;border-top:1px solid var(--line,#ccc);margin:2px 0}
.nsdlg .msg{font-size:.85rem;min-height:1.2em}`;
function ui(){
  const home = document.getElementById('home'); if (!home) return;
  const st = document.createElement('style'); st.textContent = CSS; document.head.appendChild(st);
  btn = document.createElement('button'); btn.type = 'button'; btn.className = 'nsync';
  btn.innerHTML = '<span>☁</span><b>端末間の同期</b><small></small>';
  const anchor = home.querySelector('.opts'); anchor ? anchor.after(btn) : home.prepend(btn);
  dlg = document.createElement('dialog'); dlg.className = 'nsdlg';
  dlg.innerHTML = `<div class="in">
    <h2>端末間の同期</h2>
    <p>カードの予定・進み具合・読んだページ・チェックは、自動でサーバーに保存され、同じ同期コードの端末どうしで合わさります。</p>
    <p class="mut" id="nsState"></p>
    <hr>
    <p><b>この端末の同期コード</b></p>
    <div class="code" id="nsCode"></div>
    <div class="row"><button type="button" id="nsShare">別の端末に送る</button><button type="button" id="nsCopy">コードをコピー</button></div>
    <p class="mut">送ったリンクを別の端末で開くと、自動でこのコードにつながります。コードを知っている人は記録を見たり変えたりできるので、人には教えないでください。</p>
    <hr>
    <p><b>別の端末のコードにつなぐ</b></p>
    <div class="row"><input id="nsIn" placeholder="XXXX-XXXX-XXXX-…" autocomplete="off" autocapitalize="characters" spellcheck="false"><button type="button" class="go" id="nsLink">つなぐ</button></div>
    <p class="mut">この端末の記録は消えず、つないだ先の記録と合わさります(同じカードは新しく答えた方を残します)。</p>
    <p class="msg" id="nsMsg"></p>
    <div class="row" style="justify-content:flex-end"><button type="button" id="nsNow">今すぐ同期</button><button type="button" class="go" id="nsClose">閉じる</button></div>
  </div>`;
  document.body.appendChild(dlg);
  const msg = t => { $q('#nsMsg').textContent = t; };
  const fill = () => { $q('#nsCode').textContent = grp(code); $q('#nsState').textContent = stateText(); msg(''); };
  btn.addEventListener('click', () => { fill(); dlg.showModal ? dlg.showModal() : dlg.setAttribute('open', ''); });
  $q('#nsClose').addEventListener('click', () => dlg.close ? dlg.close() : dlg.removeAttribute('open'));
  $q('#nsNow').addEventListener('click', () => sync());
  const copy = async (t, ok) => { try { await navigator.clipboard.writeText(t); msg(ok); } catch(e) { msg('コピーできませんでした。上のコードを長押しして選んでください'); } };
  $q('#nsCopy').addEventListener('click', () => copy(grp(code), 'コードをコピーしました'));
  $q('#nsShare').addEventListener('click', async () => {
    const u = linkURL();
    if (navigator.share) { try { await navigator.share({ title: '脳解剖学 単語帳(同期)', url: u }); return; } catch(e) { if (e && e.name === 'AbortError') return; } }
    copy(u, 'リンクをコピーしました。別の端末で開いてください');
  });
  $q('#nsLink').addEventListener('click', async () => {
    const v = $q('#nsIn').value.toUpperCase().replace(/[^A-Z2-9]/g, '');
    if (v.length < 20) { msg('コードが短すぎます(24文字)'); return; }
    if (v === code) { msg('この端末のコードと同じです'); return; }
    msg('つないでいます…');
    try { await link(v); fill(); $q('#nsIn').value = ''; msg('つなぎました。記録を合わせました'); }
    catch(e) { fill(); msg('コードは変えましたが、サーバーにつながりませんでした。ネットにつながったら自動で合わせます'); }
  });
  setState(S.state);
}

// リンク(#sync=コード)から開いたとき
function fromHash(){
  const m = location.hash.match(/sync=([A-Za-z2-9-]{20,})/); if (!m) return false;
  try { history.replaceState(null, '', location.pathname + location.search); } catch(e) {}
  const c = m[1].toUpperCase().replace(/[^A-Z2-9]/g, '');
  if (c === code) return false;
  if (!confirm('この端末を同期コード ' + grp(c) + ' につなぎますか?\nこの端末の記録は消えず、つないだ先の記録と合わさります。')) return false;
  link(c).then(() => alert('つなぎました。これからはこの端末の記録も自動で合わさります。'))
         .catch(() => alert('コードは設定しました。ネットにつながったら記録を合わせます。'));
  return true;
}

window.neuroSync = { sync, link, get code(){ return code; } };
function boot(){ ui(); if (!fromHash()) sync(); }
window.addEventListener('hashchange', fromHash);
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot); else boot();
})();
