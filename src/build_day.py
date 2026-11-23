# Builds day/index.html from src/day_base.html + src/content/dNN.txt.
# Run from anywhere: python3 src/build_day.py
import json,re,os,glob
import pathlib
SRC=pathlib.Path(__file__).resolve().parent
ROOT=SRC.parent
APP=str(SRC)
h=open(f'{APP}/day_base.html',encoding='utf-8').read()
h=h.replace('/*ENGINE*/',open(f'{APP}/engine.js',encoding='utf-8').read().rstrip('\n'))
a=h.index('const DECKS=')+len('const DECKS='); b=h.index(';\nconst $=')
D=json.loads(h[a:b].replace('<\\/','</'))
def fix(t): return t.replace('癒流','灌流').replace('娚下','嚥下')
# 復習 = 前の全Day(Day N なら Day 1〜N-1)
for i,d in enumerate(D): d['rev']=list(range(i))
for d in D:
    for s in d['secs']:
        s['cards']=[c for c in s['cards'] if not c['q'].startswith('テーマ ')]
        for c in s['cards']:
            for k in ('q','a','n'):
                if k in c: c[k]=fix(c[k])
def parse(path):
    lesson=[];terms=[];facts=[];mode=None
    for raw in open(path,encoding='utf-8').read().split('\n'):
        line=raw.rstrip()
        if line.startswith('@'): mode=line[1:].strip(); continue
        if mode=='lesson':
            if line.startswith('## '): lesson.append({'h':line[3:].strip(),'b':[]})
            elif lesson and line.strip(): lesson[-1]['b'].append(line.strip())
        elif mode in('term','fact') and '|' in line:
            q,ans=[x.strip() for x in line.split('|',1)]
            (terms if mode=='term' else facts).append({'q':q,'a':ans})
    return lesson,terms,facts
for i,d in enumerate(D):
    p=f'{APP}/content/d{i+1:02d}.txt'
    if os.path.exists(p):
        d['lesson'],d['terms'],d['facts']=parse(p)
import sys; sys.path.insert(0,APP); import linkmap
print('links',dict(linkmap.assign(D)))
data=json.dumps(D,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
h=h[:a]+data+h[b:]
def rep(o,n,cnt=1):
    global h
    assert o in h,o[:60]; h=h.replace(o,n,cnt)
# ---- copy
rep('21日の学習ルートの順に並んでいます。その日のDayを開いて始めてください。','21日の学習ルートの順です。各Dayは「① 読む → ② 用語 → ③ 部品 → ④ まとめ」の順に進めると、知らない答えに出会わずに積み上げられます。')
# ---- links from cards to reading pages
rep("s.cards.forEach(c=>out.push({...c,sec:s.title}));","s.cards.forEach(c=>out.push({...c,sec:s.title,ci}));")
rep('<div class="hint" id="hint">','<button class="toread" id="toRead" type="button" hidden></button>\n    <div class="hint" id="hint">')
rep("$('noteText').textContent=c.n||'';","$('noteText').textContent=c.n||''; $('toRead').textContent=c.pg?'📖 読むで確認:'+c.pg:'';")
rep("$('hint').hidden=flipped;","$('hint').hidden=flipped; $('toRead').hidden=!flipped||!c.pg;")
rep('.note{','.toread{display:block;width:100%;text-align:left;background:var(--surface);border:1px solid var(--line);border-radius:10px;padding:10px 12px;font-size:.88rem;font-weight:600;color:var(--violet);cursor:pointer;line-height:1.5}\n.note{')
# ---- css
rep('</style>','#read{box-sizing:border-box;height:100vh;height:100dvh;overflow:hidden;padding:12px 14px 10px;gap:8px}#read .rbar{gap:10px;align-items:center}#read .back{padding:5px 10px;font-size:.85rem}#read .where b{font-size:.92rem;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}#read .rmeta{display:block;font-size:.76rem;font-variant-numeric:tabular-nums}#read .track{height:4px;margin-top:5px}#read .reader{flex:1 1 auto;min-height:0;overflow:hidden;padding:0;gap:0}#read .rtext{flex:1 1 auto;min-height:0;overflow-y:auto;overscroll-behavior:contain;padding:16px}#read .rtext .pdone{margin-top:8px}#read .dock{position:relative;margin:0;padding:8px 8px 0;border-bottom:none;flex:none}#read .dock.min{padding-bottom:8px;border-bottom:1px solid var(--line)}#read .dbar{position:absolute;left:14px;right:14px;bottom:6px;pointer-events:none}#read .dbar button{pointer-events:auto;background:color-mix(in srgb,var(--surface) 88%,transparent);-webkit-backdrop-filter:blur(4px);backdrop-filter:blur(4px);padding:2px 10px;font-size:.75rem}#read .dtabs button.on{background:var(--violet);color:var(--surface)}#read .dock.min .dbar{position:static}#read .rnav{position:static;margin:0;padding:0;flex:none;gap:8px}#read .rnav button{padding:8px;font-size:.95rem;border-radius:10px}@media (max-width:759.98px){#read .dimg{height:min(var(--figh,clamp(130px,30dvh,340px)),calc(100dvh - 230px));min-height:80px}#read.hasfig .splitter{display:block;flex:none;height:18px;cursor:row-resize;touch-action:none;position:relative}#read.hasfig .splitter::before{content:'';position:absolute;left:0;right:0;top:8px;height:2px;background:var(--line)}#read.hasfig .splitter .grip{position:absolute;left:calc(50% - 22px);top:3px;width:44px;height:12px;border-radius:6px;background:var(--surface);border:2px solid var(--violet);box-sizing:border-box}#read.hasfig .splitter:hover::before,#read.hasfig .splitter:focus-visible::before,body.dragging #read.hasfig .splitter::before{background:var(--violet);height:3px}#read.hasfig .dock.min+.splitter{display:none}body.dragging.vsplit{cursor:row-resize}}@media (min-width:760px){#read.hasfig{max-width:none;padding:10px 14px 8px}#read.hasfig .reader{flex-direction:row;align-items:stretch;padding:0}#read.hasfig .dock{position:relative;flex:0 0 calc(var(--figr) * (100% - 22px));display:flex;flex-direction:column;padding:12px 0 12px 12px;border-bottom:none;box-sizing:border-box;min-height:0}#read.hasfig .dimg{flex:1 1 auto;height:auto;min-height:0}#read.hasfig .dbar,#read.hasfig .dock.min .dbar{position:absolute;left:20px;right:8px;bottom:20px}#read.hasfig .splitter .grip{position:absolute;top:calc(50% - 22px);left:5px;margin:0}#read.hasfig .rtext{padding:16px 20px 16px 6px}#read.hasfig .rtext .pdone{width:auto;margin:8px 0 0}#read.hasfig .rnav{width:calc((1 - var(--figr)) * (100% - 22px));margin:0 0 0 auto}}\n</style>')
rep('.unit.all{','.step{display:flex;align-items:center;gap:10px}\n.step .sn{width:22px;height:22px;border-radius:50%;background:var(--violet-soft);color:var(--violet);font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}\n.unit .sub{display:block;font-size:.75rem;color:var(--muted);font-weight:400}\n.minor{font-size:.78rem;color:var(--muted);padding:6px 4px 0}\n.unit.small{padding:7px 12px;font-size:.88rem}\n.reader{flex:1;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px 20px;display:flex;flex-direction:column;gap:12px;overflow-wrap:anywhere}\n.reader h2{font-family:var(--display);font-size:1.25rem;line-height:1.45;margin:0;text-wrap:balance}\n.reader p{margin:0;font-size:1rem;line-height:1.85}\n.reader ul,.reader ol{margin:0;padding-left:1.3em;display:flex;flex-direction:column;gap:4px;line-height:1.75}\n.reader figure{margin:2px 0;display:flex;flex-direction:column;gap:6px}\n.reader figure img{display:block;width:100%;height:auto;border-radius:10px;border:1px solid var(--line);background:#fff}\n.reader figcaption{font-size:.8rem;color:var(--muted);line-height:1.5}\n.dock{position:sticky;top:0;z-index:5;margin:0 -12px;padding:8px 12px;background:var(--surface);border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:6px}\n.dimg{height:clamp(160px,34vh,360px);display:flex;align-items:center;justify-content:center;background:#fff;border-radius:10px;border:1px solid var(--line);overflow:hidden;cursor:zoom-in}\n.dimg img{max-width:100%;max-height:100%;object-fit:contain;display:block}\n.dock.min .dimg{display:none}\n.dbar{display:flex;gap:6px;align-items:center}\n.dtabs{display:flex;gap:6px;flex:1;overflow-x:auto}\n.dtabs button,.dbar>button,.figref button{border:1px solid var(--violet);background:var(--surface);color:var(--violet);border-radius:999px;padding:4px 12px;font-size:.8rem;font-weight:700;cursor:pointer;flex:none}\n.dtabs button.on{background:var(--violet);color:var(--surface)}\n.reader p.figref{font-size:.86rem;line-height:1.6;color:var(--muted);background:var(--paper);border-radius:10px;padding:8px 10px}\n.figref button{margin-right:8px;padding:2px 10px}\n.zoom{position:fixed;inset:0;z-index:50;background:rgba(10,10,14,.95);display:flex;flex-direction:column}\n.zoom[hidden]{display:none}\n.zbar{display:flex;align-items:center;gap:12px;padding:10px 12px;color:#ddd;font-size:.8rem}\n.zbar button{background:#fff;color:#222;border:none;border-radius:999px;padding:6px 14px;font-weight:700}\n.zwrap{flex:1;overflow:auto;touch-action:pan-x pan-y;background:#fff}\n.zwrap img{display:block;width:100%;height:auto;max-width:none}\n.zcap{margin:0;padding:8px 12px 14px;color:#ddd;font-size:.8rem;line-height:1.5}\n.rtext{display:flex;flex-direction:column;gap:12px;min-width:0}\n@media (min-width:760px){#read.hasfig{max-width:1600px;--figr:0.55}#read.hasfig .reader{flex-direction:row;align-items:flex-start;gap:0;padding:24px 28px}#read.hasfig .dock{position:sticky;top:16px;flex:0 0 calc(var(--figr) * (100% - 22px));min-width:0;margin:0;padding:0;border-bottom:none;background:transparent}#read.hasfig .dimg{height:calc(100vh - 200px);min-height:320px}#read.hasfig .dock.min .dimg{display:flex}#read.hasfig #dMin{display:none}#read.hasfig .splitter{display:block;flex:0 0 22px;align-self:stretch;cursor:col-resize;touch-action:none;position:relative}#read.hasfig .splitter::before{content:'';position:absolute;left:10px;top:0;bottom:0;width:2px;background:var(--line);border-radius:2px}#read.hasfig .splitter .grip{position:sticky;top:calc(50vh - 22px);display:block;margin:min(30vh,240px) 0 0 5px;width:12px;height:44px;border-radius:6px;background:var(--surface);border:2px solid var(--violet);box-sizing:border-box}#read.hasfig .splitter:hover::before,#read.hasfig .splitter:focus-visible::before,body.dragging #read.hasfig .splitter::before{background:var(--violet);width:3px}#read.hasfig .rtext{flex:1 1 0;max-width:none}#read.hasfig .rnav,#read.hasfig .pdone{max-width:none;width:calc((1 - var(--figr)) * (100% - 80px));margin-left:auto;margin-right:29px}}\n.splitter{display:none}body.dragging{user-select:none;-webkit-user-select:none;cursor:col-resize}\n.pdone{display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-weight:700;cursor:pointer}\n.pdone input{width:24px;height:24px;accent-color:var(--ok);margin:0;flex:none;cursor:pointer}\n.pdone.on{border-color:var(--ok);background:var(--ok-soft);color:var(--ok)}\n.rnav{display:grid;grid-template-columns:1fr 2fr;gap:10px;position:sticky;bottom:0;background:var(--paper);padding:10px 0 12px;margin-bottom:-12px}\n.rnav button{border-radius:12px;padding:14px 8px;font-weight:700;border:2px solid var(--violet);background:var(--surface);color:var(--violet)}\n.rnav button.go{background:var(--violet);color:var(--surface)}\n.rnav button:disabled{opacity:.35}\n.unit.all{')
# ---- reader view markup
rep('<main class="wrap" id="study" hidden>','''<main class="wrap" id="read" hidden>
  <div class="bar rbar">
    <button class="back" id="rBack">← 単元一覧</button>
    <div class="where"><b id="rTitle"></b><span class="rmeta"><span id="rSub"></span> ・ <span id="rPage"></span></span>
      <div class="track"><div class="fill" id="rFill"></div></div></div>
  </div>
  <article class="reader" id="reader"></article>
  <label class="pdone" id="pdoneBox"><input type="checkbox" id="pdone"><span>このページは終わった</span></label>
  <div class="rnav"><button id="rPrev">← 前へ</button><button class="go" id="rNext">次へ →</button></div>
</main>
<div class="zoom" id="zoom" hidden><div class="zbar"><button type="button" id="zClose">✕ 閉じる</button><span>2本指で拡大 ・ ダブルタップで2.5倍</span></div><div class="zwrap" id="zWrap"><img id="zImg" alt=""></div><p class="zcap" id="zCap"></p></div>
<main class="wrap" id="study" hidden>''')
# reader logic
rep("$('card').addEventListener('click',flip);",r'''let rd={ci:0,p:0};
const PG_KEY='neuro-done-pages';
function pk(ci,i){return ci+':'+DECKS[ci].lesson[i].h;}
function loadPg(){let S;try{S=JSON.parse(localStorage.getItem(PG_KEY)||'{}')||{};}catch(e){return {};}
  let mig=false;Object.keys(S).forEach(k=>{const m=k.match(/^(\d+)-(\d+)$/);if(!m)return;mig=true;delete S[k];
    let ci=+m[1],i=+m[2];if((ci===0&&i>=14)||(ci===1&&i>=2))i++;if(DECKS[ci]&&DECKS[ci].lesson&&DECKS[ci].lesson[i])S[pk(ci,i)]=1;});
  if(mig)savePg(S);return S;}
function savePg(S){try{localStorage.setItem(PG_KEY,JSON.stringify(S));}catch(e){}}
function pagesDone(ci){const S=loadPg(),L=DECKS[ci].lesson||[];return L.filter((_,i)=>S[pk(ci,i)]).length;}
function pagesLabel(ci){const n=DECKS[ci].lesson.length,c=pagesDone(ci);return c?'✓'+c+'/'+n+' ページ':n+' ページ';}
let jump=null;
let dockFigs=[],dockCur=0,figObs=null,zScale=1;
function dockMin(){try{return localStorage.getItem('neuro-dockmin')==='1';}catch(e){return false;}}
function dockShow(k,force){const f=dockFigs[k];if(!f||!$('dock'))return;dockCur=k;const im=$('dImg').querySelector('img');if(im.getAttribute('src')!==f.src){im.src=f.src;im.alt=f.cap;}
  [...$('dTabs').children].forEach((b,i)=>b.classList.toggle('on',i===k));
  if(force&&dockMin()){try{localStorage.setItem('neuro-dockmin','');}catch(e){}$('dock').classList.remove('min');$('dMin').textContent='小さく';}}
function splitGet(){try{const v=parseFloat(localStorage.getItem('neuro-split'));return v>=0.2&&v<=0.8?v:0.55;}catch(e){return 0.55;}}
function splitSet(v,save){v=Math.min(0.75,Math.max(0.25,v));$('read').style.setProperty('--figr',v);if(save){try{localStorage.setItem('neuro-split',String(v));}catch(e){}}}
const MQ=matchMedia('(min-width:760px)');
function splitH(){try{const v=parseFloat(localStorage.getItem('neuro-splith'));return v>=60?v:0;}catch(e){return 0;}}
function splitHSet(px,save){px=Math.round(Math.max(80,Math.min(px,innerHeight-230)));$('read').style.setProperty('--figh',px+'px');if(save){try{localStorage.setItem('neuro-splith',String(px));}catch(e){}}}
function splitHReset(){$('read').style.removeProperty('--figh');try{localStorage.removeItem('neuro-splith');}catch(e){}}
function splitOrient(){const sp=$('splitter');if(!sp)return;const v=MQ.matches;sp.setAttribute('aria-orientation',v?'vertical':'horizontal');
  sp.setAttribute('aria-label',v?'図と本文の幅を変える':'図の高さを変える');sp.title=v?'ドラッグで幅を変更・ダブルクリックで元に戻す':'ドラッグで図の高さを変更・ダブルタップで元に戻す';}
MQ.addEventListener('change',splitOrient);
function splitBind(){const sp=$('splitter');if(!sp)return;splitSet(splitGet(),false);const h0=splitH();if(h0)splitHSet(h0,false);splitOrient();
  sp.addEventListener('pointerdown',e=>{e.preventDefault();sp.setPointerCapture(e.pointerId);const pc=MQ.matches;document.body.classList.add('dragging');document.body.classList.toggle('vsplit',!pc);
    const mv=ev=>{if(pc){const rc=$('reader').getBoundingClientRect();splitSet((ev.clientX-rc.left-11)/(rc.width-22),false);}
      else{const r=$('dImg').getBoundingClientRect();splitHSet(ev.clientY-r.top-9,false);}};
    const up=()=>{try{sp.releasePointerCapture(e.pointerId);}catch(err){}sp.removeEventListener('pointermove',mv);sp.removeEventListener('pointerup',up);sp.removeEventListener('pointercancel',up);document.body.classList.remove('dragging','vsplit');
      if(pc)splitSet(parseFloat(getComputedStyle($('read')).getPropertyValue('--figr'))||0.55,true);
      else{const v=parseFloat($('read').style.getPropertyValue('--figh'));if(v)splitHSet(v,true);}};
    sp.addEventListener('pointermove',mv);sp.addEventListener('pointerup',up);sp.addEventListener('pointercancel',up);});
  sp.addEventListener('dblclick',()=>{if(MQ.matches)splitSet(0.55,true);else splitHReset();});
  sp.addEventListener('keydown',e=>{if(MQ.matches){const v=splitGet();if(e.key==='ArrowLeft'){splitSet(v-0.03,true);e.preventDefault();}else if(e.key==='ArrowRight'){splitSet(v+0.03,true);e.preventDefault();}}
    else{const hh=$('dImg').getBoundingClientRect().height;if(e.key==='ArrowUp'){splitHSet(hh-20,true);e.preventDefault();}else if(e.key==='ArrowDown'){splitHSet(hh+20,true);e.preventDefault();}}});}
document.addEventListener('keydown',e=>{if($('read').hidden||!$('zoom').hidden||e.altKey||e.ctrlKey||e.metaKey)return;const t=e.target;if(t&&(t.id==='splitter'||/^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)))return;
  const L=DECKS[rd.ci].lesson;if(e.key==='ArrowLeft'&&rd.p>0){$('rPrev').click();e.preventDefault();}else if(e.key==='ArrowRight'&&rd.p<L.length-1){$('rNext').click();e.preventDefault();}});
function syncDock(){if($('read').hidden||!$('dock')||!dockFigs.length)return;const rt=document.querySelector('#reader .rtext');const rc=rt.getBoundingClientRect();const line=rc.top+rc.height*0.55;let k=0;
  document.querySelectorAll('#reader .figref').forEach(el=>{if(el.getBoundingClientRect().top<line)k=+el.dataset.k;});if(k!==dockCur)dockShow(k,false);}
let syncQ=false;window.addEventListener('scroll',()=>{if(syncQ)return;syncQ=true;requestAnimationFrame(()=>{syncQ=false;syncDock();});},{passive:true});
function zoomOpen(k){const f=dockFigs[k];if(!f)return;$('zImg').src=f.src;$('zImg').alt=f.cap;$('zCap').textContent='図'+(k+1)+'  '+f.cap;zScale=1;zApply();$('zoom').hidden=false;document.body.style.overflow='hidden';
  try{history.pushState({zoom:1},'');}catch(e){}}
function zoomClose(){$('zoom').hidden=true;document.body.style.overflow='';}
function zApply(){$('zImg').style.width=(zScale*100)+'%';}
function setBackLabel(){$('rBack').textContent=jump?'← カードに戻る':'← 単元一覧';}
const RPOS_KEY='neuro-readpos-day';
function loadRpos(){try{return JSON.parse(localStorage.getItem(RPOS_KEY)||'{}')||{};}catch(e){return {};}}
function openReader(ci,at){jump=null;setBackLabel();const S=loadPg(),L=DECKS[ci].lesson;let f=L.findIndex((_,i)=>!S[pk(ci,i)]);const R=loadRpos()[ci];
  if(at==null&&R!=null){const j=L.findIndex(x=>x.h===R);if(j>=0)at=j;}rd={ci,p:at!=null&&at<L.length?at:(f<0?0:f)};const t=split(DECKS[ci].title);$('rTitle').textContent='Day '+t.n+' '+t.en;$('rSub').textContent='① 読む';
  $('home').hidden=true;$('read').hidden=false;renderPage();}
function renderPage(){const L=DECKS[rd.ci].lesson,pg=L[rd.p],box=$('reader');const pdb=$('pdoneBox');box.textContent='';
  const h2=document.createElement('h2');h2.textContent=pg.h;const tx=document.createElement('div');tx.className='rtext';let list=null,kind='';const figs=[];dockFigs=figs;
  if(figObs){figObs.disconnect();figObs=null;}
  if(pg.b.some(l=>/^!img\s/.test(l))){const dk=document.createElement('div');dk.className='dock'+(dockMin()?' min':'');dk.id='dock';
    dk.innerHTML='<div class="dimg" id="dImg"><img alt=""></div><div class="dbar"><div class="dtabs" id="dTabs"></div><button type="button" id="dZoom">拡大</button><button type="button" id="dMin"></button></div>';box.append(dk);const sp=document.createElement('div');sp.className='splitter';sp.id='splitter';sp.tabIndex=0;sp.setAttribute('role','separator');sp.setAttribute('aria-orientation','vertical');sp.setAttribute('aria-label','図と本文の幅を変える');sp.title='ドラッグで幅を変更・ダブルクリックで元に戻す';sp.innerHTML='<span class="grip"></span>';box.append(sp);}
  box.append(tx);tx.append(h2);$('read').classList.toggle('hasfig',!!$('dock'));
  pg.b.forEach(line=>{let m;
    if((m=line.match(/^!img\s+(\S+)\s*\|\s*(.*)$/))){kind='';const k=figs.length;figs.push({src:'../img/'+m[1],cap:m[2]});
      const fp=document.createElement('p');fp.className='figref';fp.dataset.k=k;const bt=document.createElement('button');bt.type='button';bt.textContent='図'+(k+1);
      bt.addEventListener('click',()=>dockShow(k,true));fp.append(bt,document.createTextNode(m[2]));tx.append(fp);return;}
    if((m=line.match(/^-\s+(.*)$/))){if(kind!=='ul'){list=document.createElement('ul');tx.append(list);kind='ul';}const li=document.createElement('li');li.textContent=m[1];list.append(li);}
    else if((m=line.match(/^\d+\.\s+(.*)$/))){if(kind!=='ol'){list=document.createElement('ol');tx.append(list);kind='ol';}const li=document.createElement('li');li.textContent=m[1];list.append(li);}
    else{kind='';const p=document.createElement('p');p.textContent=line;tx.append(p);}});
  if(figs.length){const tb=$('dTabs');figs.forEach((f,k)=>{const b=document.createElement('button');b.type='button';b.textContent='図'+(k+1);b.addEventListener('click',()=>dockShow(k,true));tb.append(b);});
    $('dMin').textContent=dockMin()?'大きく':'小さく';$('dMin').addEventListener('click',()=>{const m=!dockMin();try{localStorage.setItem('neuro-dockmin',m?'1':'');}catch(e){}$('dock').classList.toggle('min',m);$('dMin').textContent=m?'大きく':'小さく';});
    $('dZoom').addEventListener('click',()=>zoomOpen(dockCur));$('dImg').addEventListener('click',()=>zoomOpen(dockCur));dockShow(0,false);
    splitBind();requestAnimationFrame(syncDock);}
  tx.append(pdb);tx.addEventListener('scroll',()=>{if(syncQ)return;syncQ=true;requestAnimationFrame(()=>{syncQ=false;syncDock();});},{passive:true});
  const done=!!loadPg()[pk(rd.ci,rd.p)];$('pdone').checked=done;$('pdoneBox').classList.toggle('on',done);
  $('rPage').textContent=(rd.p+1)+' / '+L.length+' ページ'+(pagesDone(rd.ci)?' ・ ✓'+pagesDone(rd.ci):'');$('rFill').style.width=((rd.p+1)/L.length*100)+'%';
  if(!jump){try{const R=loadRpos();R[rd.ci]=pg.h;localStorage.setItem(RPOS_KEY,JSON.stringify(R));}catch(e){}saveLast({type:'read',ci:rd.ci,p:rd.p,total:L.length,label:$('rTitle').textContent+' ・ ① 読む',t:Date.now()});}
  $('rPrev').disabled=rd.p===0;$('rNext').textContent=rd.p===L.length-1?(jump?'カードに戻る →':'② 用語へ進む →'):'次へ →';window.scrollTo(0,0);}
$('rPrev').addEventListener('click',()=>{if(rd.p>0){rd.p--;renderPage();}});
$('rNext').addEventListener('click',()=>{const L=DECKS[rd.ci].lesson;if(rd.p<L.length-1){rd.p++;renderPage();}else if(jump){leaveJump();}else{$('read').hidden=true;start(rd.ci,'term');}});
$('rBack').addEventListener('click',()=>{if(jump){leaveJump();return;}$('read').hidden=true;$('home').hidden=false;renderHome();});
function jumpToRead(e){if(e)e.stopPropagation();const c=nowCard();if(!c||!c.pg)return;const L=DECKS[c.ci].lesson||[];const i=L.findIndex(p=>p.h===c.pg);if(i<0)return;
  jump={y:window.scrollY};rd={ci:c.ci,p:i};const t=split(DECKS[c.ci].title);$('rTitle').textContent='Day '+t.n+' '+t.en;$('rSub').textContent='① 読む';setBackLabel();
  $('study').hidden=true;$('read').hidden=false;renderPage();try{history.pushState({jump:1},'');}catch(err){}}
function backToCard(){if(!jump)return;const y=jump.y;jump=null;setBackLabel();$('read').hidden=true;$('study').hidden=false;window.scrollTo(0,y);}
function leaveJump(){if(history.state&&history.state.jump){history.back();}else{backToCard();}}
window.addEventListener('popstate',()=>{if(!$('zoom').hidden){zoomClose();return;}if(jump)backToCard();});
$('zClose').addEventListener('click',()=>{if(history.state&&history.state.zoom)history.back();else zoomClose();});
(()=>{const w=$('zWrap');let last=0,d0=0,s0=1;
  w.addEventListener('click',e=>{const now=Date.now();if(now-last<300){const r=w.getBoundingClientRect(),fx=(e.clientX-r.left+w.scrollLeft)/w.scrollWidth,fy=(e.clientY-r.top+w.scrollTop)/w.scrollHeight;
    zScale=zScale>1?1:2.5;zApply();w.scrollLeft=fx*w.scrollWidth-(e.clientX-r.left);w.scrollTop=fy*w.scrollHeight-(e.clientY-r.top);last=0;}else last=now;});
  const dist=t=>Math.hypot(t[0].clientX-t[1].clientX,t[0].clientY-t[1].clientY);
  w.addEventListener('touchstart',e=>{if(e.touches.length===2){d0=dist(e.touches);s0=zScale;}},{passive:true});
  w.addEventListener('touchmove',e=>{if(e.touches.length===2&&d0){e.preventDefault();zScale=Math.min(5,Math.max(1,s0*dist(e.touches)/d0));zApply();}},{passive:false});
  w.addEventListener('touchend',e=>{if(e.touches.length<2)d0=0;});})();
$('toRead').addEventListener('click',jumpToRead);
$('pdone').addEventListener('change',e=>{const S=loadPg(),k=pk(rd.ci,rd.p);if(e.target.checked)S[k]=1;else delete S[k];savePg(S);
  $('pdoneBox').classList.toggle('on',e.target.checked);const L=DECKS[rd.ci].lesson;$('rPage').textContent=(rd.p+1)+' / '+L.length+' ページ'+(pagesDone(rd.ci)?' ・ ✓'+pagesDone(rd.ci):'');});
$('card').addEventListener('click',flip);''')
# ---- 蛍光ペン(「読む」の本文。仕組みは src/highlight.js)
rep("pg.b.forEach(line=>{let m;","pg.b.forEach((line,bi)=>{let m;")
rep("const li=document.createElement('li');li.textContent=m[1];list.append(li);","const li=document.createElement('li');li.textContent=m[1];li.dataset.bi=bi;list.append(li);",2)
rep("const p=document.createElement('p');p.textContent=line;tx.append(p);","const p=document.createElement('p');p.textContent=line;p.dataset.bi=bi;tx.append(p);")
rep("'次へ →';window.scrollTo(0,0);}","'次へ →';hlPage();window.scrollTo(0,0);}")
rep('<div class="track"><div class="fill" id="rFill"></div></div></div>\n  </div>','<div class="track"><div class="fill" id="rFill"></div></div></div>\n    <button class="penbtn" id="penBtn" type="button" aria-pressed="false" aria-label="蛍光ペン" title="蛍光ペン(なぞって塗る)">🖍</button>\n  </div>\n  <div class="penbar" id="penBar" hidden><span class="pl">なぞって塗る</span><button type="button" data-c="y" class="sw hl-y" aria-label="黄"></button><button type="button" data-c="g" class="sw hl-g" aria-label="緑"></button><button type="button" data-c="p" class="sw hl-p" aria-label="ピンク"></button><button type="button" data-c="b" class="sw hl-b" aria-label="青"></button><button type="button" data-c="x" class="er">消しゴム</button><button type="button" id="penDone" class="pd">終わる</button></div>')
rep('<div class="zoom" id="zoom" hidden>','<div class="hlpop" id="hlPop" hidden><button type="button" data-c="y" class="sw hl-y" aria-label="黄で塗る"></button><button type="button" data-c="g" class="sw hl-g" aria-label="緑で塗る"></button><button type="button" data-c="p" class="sw hl-p" aria-label="ピンクで塗る"></button><button type="button" data-c="b" class="sw hl-b" aria-label="青で塗る"></button><button type="button" data-c="x" class="er">消す</button></div>\n<div class="zoom" id="zoom" hidden>')
rep('</style>','.hl-y{--hl:rgba(255,226,0,.5)}.hl-g{--hl:rgba(60,215,110,.4)}.hl-p{--hl:rgba(255,95,170,.36)}.hl-b{--hl:rgba(70,170,255,.38)}\n:root[data-theme="dark"] .hl-y{--hl:rgba(255,215,0,.38)}@media (prefers-color-scheme: dark){:root:not([data-theme="light"]) .hl-y{--hl:rgba(255,215,0,.38)}}\n.rtext mark.hl{background:var(--hl);color:inherit;border-radius:3px;-webkit-box-decoration-break:clone;box-decoration-break:clone}\n#read .penbtn{flex:none;width:40px;height:36px;border-radius:10px;border:1px solid var(--line);background:var(--surface);font-size:1.1rem;line-height:1;cursor:pointer;padding:0}\n#read .penbtn[aria-pressed="true"]{border:2px solid var(--violet);background:var(--violet-soft)}\n.penbar{display:flex;align-items:center;gap:8px;flex:none;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:6px 10px;overflow-x:auto}.penbar[hidden]{display:none}\n.penbar .pl{font-size:.78rem;color:var(--muted);white-space:nowrap;margin-right:2px}\n.sw{width:30px;height:30px;border-radius:50%;border:2px solid var(--line);background:linear-gradient(var(--hl),var(--hl)),var(--surface);cursor:pointer;flex:none;padding:0}\n.penbar .sw.on,.penbar .er.on{outline:3px solid var(--violet);outline-offset:2px}\n.penbar .er,.penbar .pd,.hlpop .er{flex:none;border:1px solid var(--line);background:var(--surface);color:var(--ink);border-radius:999px;padding:5px 12px;font-size:.8rem;font-weight:700;cursor:pointer;white-space:nowrap}\n.penbar .pd{margin-left:auto;border-color:var(--violet);color:var(--violet)}\n.hlpop{position:fixed;z-index:40;display:flex;gap:8px;align-items:center;background:var(--surface);border:1px solid var(--line);border-radius:999px;padding:6px 8px;box-shadow:0 6px 20px rgba(0,0,0,.18)}.hlpop[hidden]{display:none}\n.hlpop.onmark .er{border-color:var(--again);color:var(--again)}\n@media (max-width:459.98px){.penbar .pl{display:none}.penbar{gap:6px;padding:6px 8px}.penbar .sw{width:28px;height:28px}}\n#read.pen .rtext{touch-action:pan-y;-webkit-touch-callout:none;cursor:text}#read.pen .rtext [data-bi]{cursor:crosshair}\n</style>')
rep("$('card').addEventListener('click',flip);",open(f'{APP}/highlight.js',encoding='utf-8').read().rstrip('\n')+"\n$('rBack').addEventListener('click',hlHide);\n$('card').addEventListener('click',flip);")
open(ROOT/'day'/'index.html','w',encoding='utf-8').write(h)
# chapter version typo fixes
ci=open(ROOT/'index.html',encoding='utf-8').read()
ci=fix(ci)
ci=re.sub(r'\{"q":"テーマ [^}]*\},?','',ci)
open(ROOT/'index.html','w',encoding='utf-8').write(ci)
print('ok', sum(len(d.get('facts',[]))+len(d.get('terms',[])) for d in D))
