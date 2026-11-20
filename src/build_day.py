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
data=json.dumps(D,ensure_ascii=False,separators=(',',':')).replace('</','<\\/')
h=h[:a]+data+h[b:]
def rep(o,n,cnt=1):
    global h
    assert o in h,o[:60]; h=h.replace(o,n,cnt)
# ---- copy
rep('21日の学習ルートの順に並んでいます。その日のDayを開いて始めてください。','21日の学習ルートの順です。各Dayは「① 読む → ② 用語 → ③ 部品 → ④ まとめ」の順に進めると、知らない答えに出会わずに積み上げられます。')
# ---- css
rep('.unit.all{','.step{display:flex;align-items:center;gap:10px}\n.step .sn{width:22px;height:22px;border-radius:50%;background:var(--violet-soft);color:var(--violet);font-size:.75rem;font-weight:700;display:flex;align-items:center;justify-content:center;flex:none}\n.unit .sub{display:block;font-size:.75rem;color:var(--muted);font-weight:400}\n.minor{font-size:.78rem;color:var(--muted);padding:6px 4px 0}\n.unit.small{padding:7px 12px;font-size:.88rem}\n.reader{flex:1;background:var(--surface);border:1px solid var(--line);border-radius:16px;padding:22px 20px;display:flex;flex-direction:column;gap:12px;overflow-wrap:anywhere}\n.reader h2{font-family:var(--display);font-size:1.25rem;line-height:1.45;margin:0;text-wrap:balance}\n.reader p{margin:0;font-size:1rem;line-height:1.85}\n.reader ul,.reader ol{margin:0;padding-left:1.3em;display:flex;flex-direction:column;gap:4px;line-height:1.75}\n.pdone{display:flex;align-items:center;gap:12px;background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:12px 16px;font-weight:700;cursor:pointer}\n.pdone input{width:24px;height:24px;accent-color:var(--ok);margin:0;flex:none;cursor:pointer}\n.pdone.on{border-color:var(--ok);background:var(--ok-soft);color:var(--ok)}\n.rnav{display:grid;grid-template-columns:1fr 2fr;gap:10px;position:sticky;bottom:0;background:var(--paper);padding:10px 0 12px;margin-bottom:-12px}\n.rnav button{border-radius:12px;padding:14px 8px;font-weight:700;border:2px solid var(--violet);background:var(--surface);color:var(--violet)}\n.rnav button.go{background:var(--violet);color:var(--surface)}\n.rnav button:disabled{opacity:.35}\n.unit.all{')
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
<main class="wrap" id="study" hidden>''')
# ---- cardsOf with steps
rep("function cardsOf(ci,si){\n  const d=DECKS[ci]; let out=[];\n  if(si==='rev')","""function stepCards(ci,kind){const d=DECKS[ci];
  if(kind==='term') return (d.terms||[]).map(c=>({q:c.q,a:c.a,s:0,sec:'② 用語'}));
  if(kind==='fact') return (d.facts||[]).map(c=>({q:c.q,a:c.a,s:0,sec:'③ 部品'}));
  return own(ci,null);}
function revCards(r){return (DECKS[r].facts&&DECKS[r].facts.length)?stepCards(r,'fact'):own(r,null);}
function cardsOf(ci,si){
  const d=DECKS[ci]; let out=[];
  if(si==='term'||si==='fact'||si==='sum'){out=stepCards(ci,si);return starOnly&&si==='sum'?out.filter(c=>c.s>0):out;}
  if(si==='rev'){d.rev.forEach(r=>{out=out.concat(revCards(r).map(c=>({...c,sec:'Day '+(r+1)+' ・ '+c.sec})));});return starOnly?out.filter(c=>c.s>0||!c.s&&false):out;}
  if(si==='rev_old')""")
# ---- home units
o=h[h.index("    mk(d.from?'通しで始める'"):h.index("    det.appendChild(units); box.appendChild(det);")]
n='''    const mkStep=(num,label,sub,cnt,fn,cls)=>{const b=document.createElement('button');b.className='unit'+(cls?' '+cls:'');
      const l=document.createElement('span');l.className='step';const sn=document.createElement('span');sn.className='sn';sn.textContent=num;
      const tx=document.createElement('span');tx.textContent=label;if(sub){const s=document.createElement('span');s.className='sub';s.textContent=sub;tx.append(s);}
      l.append(sn,tx);const c=document.createElement('span');c.className='count';c.textContent=cnt;b.append(l,c);b.disabled=!cnt||cnt==='0 枚';b.addEventListener('click',fn);units.appendChild(b);};
    if(d.from){ mk('通しで始める',n,null,'all'); }
    else{
      if(d.lesson&&d.lesson.length){
        mkStep('1','読む','この日の内容を基礎から',pagesLabel(ci),()=>openReader(ci));
        mkStep('2','用語','言葉の意味を先に覚える',(d.terms||[]).length+' 枚',()=>start(ci,'term'));
        mkStep('3','部品','1枚1つの事実で積み上げる',(d.facts||[]).length+' 枚',()=>start(ci,'fact'));
        mkStep('4','まとめ','試験形式の一問一答',cardsOf(ci,'sum').length+' 枚',()=>start(ci,'sum'));
      } else {
        mkStep('4','まとめ','試験形式の一問一答(読む・用語・部品は準備中)',cardsOf(ci,'sum').length+' 枚',()=>start(ci,'sum'));
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
function loadPg(){try{return JSON.parse(localStorage.getItem(PG_KEY)||'{}')||{};}catch(e){return {};}}
function savePg(S){try{localStorage.setItem(PG_KEY,JSON.stringify(S));}catch(e){}}
function pagesDone(ci){const S=loadPg(),L=DECKS[ci].lesson||[];return L.filter((_,i)=>S[ci+'-'+i]).length;}
function pagesLabel(ci){const n=DECKS[ci].lesson.length,c=pagesDone(ci);return c?'✓'+c+'/'+n+' ページ':n+' ページ';}
function openReader(ci){const S=loadPg(),L=DECKS[ci].lesson;let f=L.findIndex((_,i)=>!S[ci+'-'+i]);rd={ci,p:f<0?0:f};const t=split(DECKS[ci].title);$('rTitle').textContent='Day '+t.n+' '+t.en;$('rSub').textContent='① 読む';
  $('home').hidden=true;$('read').hidden=false;renderPage();}
function renderPage(){const L=DECKS[rd.ci].lesson,pg=L[rd.p],box=$('reader');box.textContent='';
  const h2=document.createElement('h2');h2.textContent=pg.h;box.append(h2);let list=null,kind='';
  pg.b.forEach(line=>{let m;
    if((m=line.match(/^-\s+(.*)$/))){if(kind!=='ul'){list=document.createElement('ul');box.append(list);kind='ul';}const li=document.createElement('li');li.textContent=m[1];list.append(li);}
    else if((m=line.match(/^\d+\.\s+(.*)$/))){if(kind!=='ol'){list=document.createElement('ol');box.append(list);kind='ol';}const li=document.createElement('li');li.textContent=m[1];list.append(li);}
    else{kind='';const p=document.createElement('p');p.textContent=line;box.append(p);}});
  const done=!!loadPg()[rd.ci+'-'+rd.p];$('pdone').checked=done;$('pdoneBox').classList.toggle('on',done);
  $('rPage').textContent=(rd.p+1)+' / '+L.length+' ページ'+(pagesDone(rd.ci)?' ・ ✓'+pagesDone(rd.ci):'');$('rFill').style.width=((rd.p+1)/L.length*100)+'%';
  $('rPrev').disabled=rd.p===0;$('rNext').textContent=rd.p===L.length-1?'② 用語へ進む →':'次へ →';window.scrollTo(0,0);}
$('rPrev').addEventListener('click',()=>{if(rd.p>0){rd.p--;renderPage();}});
$('rNext').addEventListener('click',()=>{const L=DECKS[rd.ci].lesson;if(rd.p<L.length-1){rd.p++;renderPage();}else{$('read').hidden=true;start(rd.ci,'term');}});
$('rBack').addEventListener('click',()=>{$('read').hidden=true;$('home').hidden=false;renderHome();});
$('pdone').addEventListener('change',e=>{const S=loadPg(),k=rd.ci+'-'+rd.p;if(e.target.checked)S[k]=1;else delete S[k];savePg(S);
  $('pdoneBox').classList.toggle('on',e.target.checked);const L=DECKS[rd.ci].lesson;$('rPage').textContent=(rd.p+1)+' / '+L.length+' ページ'+(pagesDone(rd.ci)?' ・ ✓'+pagesDone(rd.ci):'');});
$('card').addEventListener('click',flip);''')
open(ROOT/'day'/'index.html','w',encoding='utf-8').write(h)
# chapter version typo fixes
ci=open(ROOT/'index.html',encoding='utf-8').read()
ci=fix(ci)
ci=re.sub(r'\{"q":"テーマ [^}]*\},?','',ci)
open(ROOT/'index.html','w',encoding='utf-8').write(ci)
print('ok', sum(len(d.get('facts',[]))+len(d.get('terms',[])) for d in D))
