# Builds day/index.html from src/day_base.html + src/content/dNN.txt.
# Run from anywhere: python3 src/build_day.py
import json,re,os,glob
import pathlib
SRC=pathlib.Path(__file__).resolve().parent
ROOT=SRC.parent
APP=str(SRC)
h=open(f'{APP}/day_base.html',encoding='utf-8').read()
a=h.index('const DECKS=')+len('const DECKS='); b=h.index(';\nconst $=')
D=json.loads(h[a:b].replace('<\\/','</'))
def fix(t): return t.replace('癒流','灌流').replace('娚下','嚥下')
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
rep('.unit.all{','.step{display:flex;align-items:center;gap:10px}\n.step .sn{width:22px;height:22px;border-radius:50%;background:var(--violet-soft);color:var(--violet);font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}\n.unit .sub{display:block;font-size:.75rem;color:var(--muted);font-weight:400}\n.minor{font-size:.78rem;color:var(--muted);padding:6px 4px 0}\n.unit.small{padding:7px 12px;font-size:.88rem}\n.reader{flex:1;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px 20px;display:flex;flex-direction:column;gap:12px;overflow-wrap:anywhere}\n.reader h2{font-family:var(--display);font-size:1.25rem;line-height:1.45;margin:0;text-wrap:balance}\n.reader p{margin:0;font-size:1rem;line-height:1.85}\n.reader ul,.reader ol{margin:0;padding-left:1.3em;display:flex;flex-direction:column;gap:4px;line-height:1.75}\n.reader figure{margin:2px 0;display:flex;flex-direction:column;gap:6px}\n.reader figure img{display:block;width:100%;height:auto;border-radius:10px;border:1px solid var(--line);background:#fff}\n.reader figcaption{font-size:.8rem;color:var(--muted);line-height:1.5}\n.dock{position:sticky;top:0;z-index:5;margin:0 -12px;padding:8px 12px;background:var(--surface);border-bottom:1px solid var(--line);display:flex;flex-direction:column;gap:6px}\n.dimg{height:clamp(160px,34vh,360px);display:flex;align-items:center;justify-content:center;background:#fff;border-radius:10px;border:1px solid var(--line);overflow:hidden;cursor:zoom-in}\n.dimg img{max-width:100%;max-height:100%;object-fit:contain;display:block}\n.dock.min .dimg{display:none}\n.dbar{display:flex;gap:6px;align-items:center}\n.dtabs{display:flex;gap:6px;flex:1;overflow-x:auto}\n.dtabs button,.dbar>button,.figref button{border:1px solid var(--violet);background:var(--surface);color:var(--violet);border-radius:999px;padding:4px 12px;font-size:.8rem;font-weight:700;cursor:pointer;flex:none}\n.dtabs button.on{background:var(--violet);color:var(--surface)}\n.reader p.figref{font-size:.86rem;line-height:1.6;color:var(--muted);background:var(--paper);border-radius:10px;padding:8px 10px}\n.figref button{margin-right:8px;padding:2px 10px}\n.zoom{position:fixed;inset:0;z-index:50;background:rgba(10,10,14,.95);display:flex;flex-direction:column}\n.zoom[hidden]{display:none}\n.zbar{display:flex;align-items:center;gap:12px;padding:10px 12px;color:#ddd;font-size:.8rem}\n.zbar button{background:#fff;color:#222;border:none;border-radius:999px;padding:6px 14px;font-weight:700}\n.zwrap{flex:1;overflow:auto;touch-action:pan-x pan-y;background:#fff}\n.zwrap img{display:block;width:100%;height:auto;max-width:none}\n.zcap{margin:0;padding:8px 12px 14px;color:#ddd;font-size:.8rem;line-height:1.5}\n.rtext{display:flex;flex-direction:column;gap:12px;min-width:0}\n@media (min-width:1000px){#read.hasfig{max-width:1480px}#read.hasfig .reader{flex-direction:row;align-items:flex-start;gap:32px;padding:24px 28px}#read.hasfig .dock{position:sticky;top:16px;flex:1.25 1 0;min-width:0;margin:0;padding:0;border-bottom:none;background:transparent}#read.hasfig .dimg{height:calc(100vh - 200px);min-height:320px}#read.hasfig .dock.min .dimg{display:flex}#read.hasfig #dMin{display:none}#read.hasfig .rtext{flex:1 1 0;max-width:720px}#read.hasfig .rnav,#read.hasfig .pdone{max-width:720px;width:100%;margin-left:auto}}\n.pdone{display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-weight:700;cursor:pointer}\n.pdone input{width:24px;height:24px;accent-color:var(--ok);margin:0;flex:none;cursor:pointer}\n.pdone.on{border-color:var(--ok);background:var(--ok-soft);color:var(--ok)}\n.rnav{display:grid;grid-template-columns:1fr 2fr;gap:10px;position:sticky;bottom:0;background:var(--paper);padding:10px 0 12px;margin-bottom:-12px}\n.rnav button{border-radius:12px;padding:14px 8px;font-weight:700;border:2px solid var(--violet);background:var(--surface);color:var(--violet)}\n.rnav button.go{background:var(--violet);color:var(--surface)}\n.rnav button:disabled{opacity:.35}\n.unit.all{')
# ---- reader view markup
rep('<main class="wrap" id="study" hidden>','''<main class="wrap" id="read" hidden>
  <div class="bar">
    <button class="back" id="rBack">← 単元一覧</button>
    <div class="where"><b id="rTitle"></b><span id="rSub"></span></div>
  </div>
  <div>
    <div class="stats"><span id="rPage"></span><span>① 読む</span></div>
    <div class="track"><div class="fill" id="rFill"></div></div>
  </div>
  <article class="reader" id="reader"></article>
  <label class="pdone" id="pdoneBox"><input type="checkbox" id="pdone"><span>このページは終わった</span></label>
  <div class="rnav"><button id="rPrev">← 前へ</button><button class="go" id="rNext">次へ →</button></div>
</main>
<div class="zoom" id="zoom" hidden><div class="zbar"><button type="button" id="zClose">✕ 閉じる</button><span>2本指で拡大 ・ ダブルタップで2.5倍</span></div><div class="zwrap" id="zWrap"><img id="zImg" alt=""></div><p class="zcap" id="zCap"></p></div>
<main class="wrap" id="study" hidden>''')
# ---- cardsOf with steps
rep("function cardsOf(ci,si){\n  const d=DECKS[ci]; let out=[];\n  if(si==='rev')","""function stepCards(ci,kind){const d=DECKS[ci];
  if(kind==='term') return (d.terms||[]).map(c=>({q:c.q,a:c.a,s:0,sec:'② 用語'}));
  if(kind==='fact') return (d.facts||[]).map(c=>({q:c.q,a:c.a,s:0,sec:'③ 部品',ci,pg:c.pg}));
  return own(ci,null);}
function revCards(r){return (DECKS[r].facts&&DECKS[r].facts.length)?stepCards(r,'fact'):own(r,null);}
function cardsOf(ci,si){
  const d=DECKS[ci]; let out=[];
  if(si==='term'||si==='fact'||si==='sum'){out=stepCards(ci,si);return starOnly&&si==='sum'?out.filter(c=>c.s>0):out;}
  if(si==='rev'){d.rev.forEach(r=>{out=out.concat(revCards(r).map(c=>({...c,sec:'Day '+(r+1)+' ・ '+c.sec})));});return starOnly?out.filter(c=>c.s>0||!c.s&&false):out;}
  if(si==='rev_old')""")
# ---- home units
o=h[h.index("    mk(d.from?'通しで始める'"):h.index("    det.appendChild(units); box.appendChild(det);")]
n='''    const mkStep=(num,label,sub,cnt,fn,cls,key)=>{const b=document.createElement('button');b.className='unit'+(cls?' '+cls:'');if(key)b.dataset.deck=key;
      const l=document.createElement('span');l.className='step';const sn=document.createElement('span');sn.className='sn';sn.textContent=num;
      const tx=document.createElement('span');tx.textContent=label;if(sub){const s=document.createElement('span');s.className='sub';s.textContent=sub;tx.append(s);}
      l.append(sn,tx);const c=document.createElement('span');c.className='count';c.textContent=cnt;b.append(l,c);b.disabled=!cnt||cnt==='0 枚';b.addEventListener('click',fn);units.appendChild(b);};
    if(d.from){ mk('通しで始める',n,null,'all'); }
    else{
      if(d.lesson&&d.lesson.length){
        mkStep('1','読む','この日の内容を基礎から',pagesLabel(ci),()=>openReader(ci));
        mkStep('2','用語','言葉の意味を先に覚える',(d.terms||[]).length+' 枚',()=>start(ci,'term'),null,ci+'|term');
        mkStep('3','部品','1枚1つの事実で積み上げる',(d.facts||[]).length+' 枚',()=>start(ci,'fact'),null,ci+'|fact');
        mkStep('4','まとめ','試験形式の一問一答',cardsOf(ci,'sum').length+' 枚',()=>start(ci,'sum'),null,ci+'|sum');
      } else {
        mkStep('4','まとめ','試験形式の一問一答(読む・用語・部品は準備中)',cardsOf(ci,'sum').length+' 枚',()=>start(ci,'sum'),null,ci+'|sum');
      }
      if(d.rev.length) mk('復習:'+d.rev.map(r=>'Day '+(r+1)).join('・'),cardsOf(ci,'rev').length,'rev');
      if(d.secs.length>1){const m=document.createElement('div');m.className='minor';m.textContent='まとめを単元ごとに';units.appendChild(m);
        d.secs.forEach((s,si)=>{mk(s.title,cardsOf(ci,si).length,si);units.lastChild.classList.add('small');});}
    }
'''
h=h.replace(o,n)
rep("n=cardsOf(ci,null).length; total+=n;","n=d.from?cardsOf(ci,null).length:(d.terms||[]).length+(d.facts||[]).length+own(ci,null).length; total+=d.from?0:n;")
# subtitle in study header
rep("(si==null?(DECKS[ci].from?'通し':'新規'):si==='rev'?'復習':DECKS[ci].secs[si].title)","({term:'② 用語',fact:'③ 部品',sum:'④ まとめ',rev:'復習'}[si]||(si==null?(DECKS[ci].from?'通し':'まとめ'):DECKS[ci].secs[si].title))")
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
function syncDock(){if($('read').hidden||!$('dock')||!dockFigs.length)return;const line=window.innerHeight*0.6;let k=0;
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
function renderPage(){const L=DECKS[rd.ci].lesson,pg=L[rd.p],box=$('reader');box.textContent='';
  const h2=document.createElement('h2');h2.textContent=pg.h;const tx=document.createElement('div');tx.className='rtext';let list=null,kind='';const figs=[];dockFigs=figs;
  if(figObs){figObs.disconnect();figObs=null;}
  if(pg.b.some(l=>/^!img\s/.test(l))){const dk=document.createElement('div');dk.className='dock'+(dockMin()?' min':'');dk.id='dock';
    dk.innerHTML='<div class="dimg" id="dImg"><img alt=""></div><div class="dbar"><div class="dtabs" id="dTabs"></div><button type="button" id="dZoom">拡大</button><button type="button" id="dMin"></button></div>';box.append(dk);}
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
    requestAnimationFrame(syncDock);}
  const done=!!loadPg()[pk(rd.ci,rd.p)];$('pdone').checked=done;$('pdoneBox').classList.toggle('on',done);
  $('rPage').textContent=(rd.p+1)+' / '+L.length+' ページ'+(pagesDone(rd.ci)?' ・ ✓'+pagesDone(rd.ci):'');$('rFill').style.width=((rd.p+1)/L.length*100)+'%';
  if(!jump){try{const R=loadRpos();R[rd.ci]=pg.h;localStorage.setItem(RPOS_KEY,JSON.stringify(R));}catch(e){}saveLast({type:'read',ci:rd.ci,p:rd.p,total:L.length,label:$('rTitle').textContent+' ・ ① 読む',t:Date.now()});}
  $('rPrev').disabled=rd.p===0;$('rNext').textContent=rd.p===L.length-1?(jump?'カードに戻る →':'② 用語へ進む →'):'次へ →';window.scrollTo(0,0);}
$('rPrev').addEventListener('click',()=>{if(rd.p>0){rd.p--;renderPage();}});
$('rNext').addEventListener('click',()=>{const L=DECKS[rd.ci].lesson;if(rd.p<L.length-1){rd.p++;renderPage();}else if(jump){leaveJump();}else{$('read').hidden=true;start(rd.ci,'term');}});
$('rBack').addEventListener('click',()=>{if(jump){leaveJump();return;}$('read').hidden=true;$('home').hidden=false;renderHome();});
function jumpToRead(e){if(e)e.stopPropagation();const c=queue[0];if(!c||!c.pg)return;const L=DECKS[c.ci].lesson||[];const i=L.findIndex(p=>p.h===c.pg);if(i<0)return;
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
open(ROOT/'day'/'index.html','w',encoding='utf-8').write(h)
# chapter version typo fixes
ci=open(ROOT/'index.html',encoding='utf-8').read()
ci=fix(ci)
ci=re.sub(r'\{"q":"テーマ [^}]*\},?','',ci)
open(ROOT/'index.html','w',encoding='utf-8').write(ci)
print('ok', sum(len(d.get('facts',[]))+len(d.get('terms',[])) for d in D))
