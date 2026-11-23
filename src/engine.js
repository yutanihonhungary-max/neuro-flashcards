const $=id=>document.getElementById(id);
let starOnly=false, shuffle=false;
let full=[], queue=[], round=1, flipped=false, cur=null, cc=null, sess=null;
// cur = {ci, si, mode:'srs'|'cram', key}. srs = Anki-style scheduling, cram = run every card once without touching the schedule.

function own(ci,si){const out=[];DECKS[ci].secs.forEach((s,i)=>{ if(si==null||si===i) s.cards.forEach(c=>out.push({...c,sec:s.title})); });return out;}
function stepCards(ci,kind){const d=DECKS[ci];
  if(kind==='term') return (d.terms||[]).map(c=>({q:c.q,a:c.a,s:0,sec:'② 用語',k:'t'}));
  if(kind==='fact') return (d.facts||[]).map(c=>({q:c.q,a:c.a,s:0,sec:'③ 部品',ci,pg:c.pg,k:'f'}));
  return own(ci,null);}
function revCards(r){return stepCards(r,'term').concat(stepCards(r,'fact'),own(r,null));}
function cardsOf(ci,si){
  const d=DECKS[ci]; let out=[];
  if(si==='term'||si==='fact') return stepCards(ci,si);
  if(si==='sum') out=stepCards(ci,'sum');
  else if(si==='rev') d.rev.forEach(r=>{out=out.concat(revCards(r).map(c=>({...c,sec:'Day '+(r+1)+' ・ '+c.sec})));});
  else{
    if(d.from&&si==null){ d.from.forEach(r=>{out=out.concat(own(r,null).map(c=>({...c,sec:'Day '+(r+1)+' ・ '+c.sec})));}); if(d.star) out=out.filter(c=>c.s>0); }
    out=out.concat(own(ci,si));
  }
  return starOnly?out.filter(c=>c.s>0):out;
}
function isCram(ci,si){return !!DECKS[ci].from&&si==null;}
function revLabel(d){const n=d.rev.length;return n===1?'Day 1':n===2?'Day 1・2':'Day 1〜'+n;}
function subName(ci,si){return {term:'② 用語',fact:'③ 部品',sum:'④ まとめ',rev:'復習'}[si]||(si==null?(DECKS[ci].from?'通し':'まとめ'):DECKS[ci].secs[si].title);}

// ---------- Anki (SM-2) scheduler ----------
// Same defaults as Anki: learning steps 1m 10m, graduating 1 day, easy 4 days, start ease 250%,
// hard ×1.2, easy bonus ×1.3, lapse → relearn 10m then 1 day, ease −20% / −15% / +15%, new day at 4:00.
const SRS_KEY='neuro-srs-day';
const CFG={steps:[1,10],relearn:[10],grad:1,easy:4,ease0:2.5,easyBonus:1.3,hard:1.2,lapse:0,minIv:1,maxIv:36500,ahead:20,dayHour:4};
let SRS=(()=>{try{return JSON.parse(localStorage.getItem(SRS_KEY)||'{}')||{};}catch(e){return {};}})();
function saveSrs(){try{localStorage.setItem(SRS_KEY,JSON.stringify(SRS));}catch(e){}}
function today(t){t=t||Date.now();return Math.floor((t-new Date(t).getTimezoneOffset()*6e4-CFG.dayHour*36e5)/864e5);}
function cid(c){return (c.k||'s')+'|'+c.q;}
function stOf(c){return SRS[cid(c)]||null;}
function kindOf(s){return !s||s.q===0?'n':(s.q===2?'r':'l');}
function fuzz(iv){if(iv<3)return iv;const f=iv<7?1:iv<20?Math.round(iv*.1):Math.max(1,Math.round(iv*.05));return iv-f+Math.floor(Math.random()*(2*f+1));}
// s.q: 0 new, 1 learning, 2 review, 3 relearning. s.d = due time (ms) while (re)learning, due day number in review.
function sched(s0,b,fz){const now=Date.now(),T=today(now);
  const s=s0?{...s0}:{q:0,s:0,i:0,e:CFG.ease0,r:0,l:0};s.r=(s.r||0)+1;
  const toReview=iv=>{if(fz)iv=fuzz(iv);s.q=2;s.s=0;s.i=Math.min(CFG.maxIv,Math.max(1,iv));s.d=T+s.i;return s;};
  if(s.q===0){s.q=1;s.s=0;}
  if(s.q===1||s.q===3){const re=s.q===3,st=re?CFG.relearn:CFG.steps;
    if(b===1){s.s=0;s.d=now+st[0]*6e4;return s;}
    if(b===2){const m=s.s===0?(st.length>1?(st[0]+st[1])/2:st[0]*1.5):st[s.s];s.d=now+m*6e4;return s;}
    if(b===3){if(s.s+1<st.length){s.s++;s.d=now+st[s.s]*6e4;return s;}return toReview(re?s.i:CFG.grad);}
    return toReview(re?s.i+1:CFG.easy);}
  const I=s.i, late=Math.max(0,T-s.d);
  if(b===1){s.l=(s.l||0)+1;s.e=Math.max(1.3,s.e-0.2);s.i=Math.max(CFG.minIv,Math.round(I*CFG.lapse));
    if(CFG.relearn.length){s.q=3;s.s=0;s.d=now+CFG.relearn[0]*6e4;return s;}return toReview(s.i);}
  const hard=Math.round(Math.max(I+1,I*CFG.hard));
  const good=Math.max(hard+1,Math.round((I+late/2)*s.e));
  const easy=Math.max(good+1,Math.round((I+late)*s.e*CFG.easyBonus));
  if(b===2)s.e=Math.max(1.3,s.e-0.15); if(b===4)s.e+=0.15;
  return toReview(b===2?hard:b===3?good:easy);}
function dur(min){if(min<1)return '1分未満';if(min<60)return Math.round(min)+'分';const h=min/60;if(h<24)return Math.round(h)+'時間';
  const d=h/24;if(d<30)return Math.round(d)+'日';if(d<365)return (Math.round(d/30*10)/10)+'か月';return (Math.round(d/365*10)/10)+'年';}
function ivLabel(s0,b){const s=sched(s0,b,false);return s.q===2?dur(s.i*1440):dur((s.d-Date.now())/6e4);}
function counts(cards,noNew){const T=today();let n=0,l=0,r=0;const seen=new Set();
  cards.forEach(c=>{const id=cid(c);if(seen.has(id))return;seen.add(id);const s=SRS[id];
    if(!s||s.q===0){if(!noNew)n++;}else if(s.q===2){if(s.d<=T)r++;}else l++;});return {n,l,r};}
function fillCounts(el,k,noNew){el.textContent='';
  if(!k.n&&!k.l&&!k.r){const s=document.createElement('span');s.className='cdone';s.textContent=noNew?'期限のカードなし':'今日は完了';el.append(s);return;}
  [['新','n','cn'],['学','l','cl'],['復','r','cr']].forEach(([lab,f,cls])=>{if(f==='n'&&noNew)return;
    const s=document.createElement('span');s.className=cls+(k[f]?'':' zero');s.textContent=lab+' '+k[f];el.append(s);});}
function countsText(k,noNew){if(!k.n&&!k.l&&!k.r)return noNew?'期限のカードなし':'今日の分は完了';
  return (noNew?[]:['新 '+k.n]).concat(['学習中 '+k.l,'復習 '+k.r]).join(' ・ ');}

function pick(){const now=Date.now(),T=today(now),noNew=cur.si==='rev';const L=[],R=[],N=[],A=[];const seen=new Set();
  full.forEach(c=>{const id=cid(c);if(seen.has(id))return;seen.add(id);const s=SRS[id];
    if(!s||s.q===0){if(!noNew)N.push(c);}
    else if(s.q===2){if(s.d<=T)R.push(c);}
    else if(s.d<=now)L.push(c); else if(s.d<=now+CFG.ahead*6e4)A.push(c);});
  const rnd=id=>{if(!sess.rnd.has(id))sess.rnd.set(id,Math.random());return sess.rnd.get(id);};
  L.sort((x,y)=>stOf(x).d-stOf(y).d); A.sort((x,y)=>stOf(x).d-stOf(y).d);
  R.sort((x,y)=>stOf(x).d-stOf(y).d||rnd(cid(x))-rnd(cid(y)));
  N.sort((x,y)=>sess.rank.get(cid(x))-sess.rank.get(cid(y)));
  const notLast=a=>a.find(c=>cid(c)!==sess.last);
  return notLast(L)||notLast(R)||notLast(N)||notLast(A)||L[0]||R[0]||N[0]||A[0]||null;}

const DONE_KEY='neuro-done-day';
const PROG_KEY='neuro-prog-day', LAST_KEY='neuro-last-day';
function progKey(ci,si,star){return ci+'|'+si+((star==null?starOnly:star)?'|s':'');}
function hashFull(a){let h=5381;const s=a.map(c=>c.q).join('\n');for(let i=0;i<s.length;i++)h=((h<<5)+h+s.charCodeAt(i))|0;return h;}
function loadProg(){try{return JSON.parse(localStorage.getItem(PROG_KEY)||'{}')||{};}catch(e){return {};}}
function saveAll(S){try{localStorage.setItem(PROG_KEY,JSON.stringify(S));}catch(e){}}
function loadLast(){try{return JSON.parse(localStorage.getItem(LAST_KEY)||'null');}catch(e){return null;}}
function saveLast(L){try{localStorage.setItem(LAST_KEY,JSON.stringify(L));}catch(e){}}
function restoreProg(){const S=loadProg()[cur.key];if(!S||S.n!==full.length||S.h!==hashFull(full))return false;
  const q=S.q.map(i=>full[i]).filter(Boolean);if(!q.length)return false;queue=q;round=S.r||1;return true;}
function saveProg(){if(!cur||cur.mode!=='cram')return;const S=loadProg();S[cur.key]={n:full.length,h:hashFull(full),q:queue.map(c=>full.indexOf(c)),r:round,t:Date.now()};saveAll(S);
  if(isCram(cur.ci,cur.si))saveLast({type:'deck',mode:'cram',ci:cur.ci,si:cur.si,star:starOnly,label:$('uTitle').textContent+' ・ '+$('uSub').textContent,left:queue.length,n:full.length,r:round,t:Date.now()});}
function addProg(){
  document.querySelectorAll('#chapters .unit[data-deck]').forEach(b=>{const [ci0,si0]=b.dataset.deck.split('|');const ci=+ci0,si=si0==='null'?null:(isNaN(+si0)?si0:+si0);
    const c=b.querySelector('.count');
    if(isCram(ci,si)){const S=loadProg()[progKey(ci,si)];if(S&&(S.q.length<S.n||S.r>1)){c.textContent='残り '+S.q.length+'/'+S.n+(S.r>1?' ・'+S.r+'周目':'');b.classList.add('inprog');}return;}
    const all=cardsOf(ci,si);if(!all.length)return;const k=counts(all,si==='rev');fillCounts(c,k,si==='rev');b.classList.toggle('inprog',k.l+k.r>0);});
  renderResume();
}
function renderResume(){const box=$('resume');const L=loadLast();if(!L||!DECKS[L.ci]){box.hidden=true;return;}
  let sub='';
  if(L.type==='deck'&&L.mode==='cram'){sub='残り '+L.left+' / '+L.n+' 枚'+(L.r>1?' ・ '+L.r+' 周目':'')+(L.star?' ・★のみ':'');}
  else if(L.type==='deck'){const tmp=starOnly;starOnly=!!L.star;const k=counts(cardsOf(L.ci,L.si),L.si==='rev');starOnly=tmp;sub=countsText(k,L.si==='rev')+(L.star?' ・★のみ':'');}
  else if(L.type==='read'){sub=(L.p+1)+' / '+L.total+' ページ';}
  box.querySelector('span').textContent=L.label;box.querySelector('small').textContent=sub;box.hidden=false;}
function resumeLast(){const L=loadLast();if(!L)return;
  if(L.type==='deck'){if(!!L.star!==starOnly){starOnly=!!L.star;$('optStar').setAttribute('aria-pressed',starOnly);}start(L.ci,L.si);}
  else if(L.type==='read'&&typeof openReader==='function'){openReader(L.ci);}}
function split(t){const m=t.match(/^(\d+)\s+([^(（]+)[(（]?([^)）]*)/);return m?{n:m[1],en:m[2].trim(),ja:m[3]||''}:{n:'',en:t,ja:''};}
function renderHome(){
  const box=$('chapters'); const open=[...box.querySelectorAll('details')].map(d=>d.open); box.innerHTML='';
  let total=0;
  DECKS.forEach((d,ci)=>{
    const t=split(d.title), n=d.from?cardsOf(ci,null).length:(d.terms||[]).length+(d.facts||[]).length+own(ci,null).length; total+=d.from?own(ci,null).length:n;
    const det=document.createElement('details'); det.open=!!open[ci];
    const sum=document.createElement('summary');
    sum.innerHTML='<span class="num"></span><span class="ctitle"></span><span class="count"></span>';
    sum.children[0].textContent=t.n; if(d.sub) t.ja=d.sub;
    sum.children[1].textContent=t.en; if(t.ja){const sm=document.createElement('small');sm.textContent=t.ja;sum.children[1].appendChild(sm);}
    sum.children[2].textContent=n+' 枚';
    det.appendChild(sum);
    const units=document.createElement('div'); units.className='units';
    const mk=(label,cnt,si,cls,sub)=>{const b=document.createElement('button');b.className='unit'+(cls?' '+cls:'');
      const l=document.createElement('span');l.textContent=label;if(sub){const s=document.createElement('span');s.className='sub';s.textContent=sub;l.append(s);}
      const c=document.createElement('span');c.className='count';c.textContent=cnt+' 枚';
      b.append(l,c);b.dataset.deck=ci+'|'+si;b.disabled=cnt===0;b.addEventListener('click',()=>start(ci,si));units.appendChild(b);};
    const mkStep=(num,label,sub,cnt,fn,cls,key)=>{const b=document.createElement('button');b.className='unit'+(cls?' '+cls:'');if(key)b.dataset.deck=key;
      const l=document.createElement('span');l.className='step';const sn=document.createElement('span');sn.className='sn';sn.textContent=num;
      const tx=document.createElement('span');tx.textContent=label;if(sub){const s=document.createElement('span');s.className='sub';s.textContent=sub;tx.append(s);}
      l.append(sn,tx);const c=document.createElement('span');c.className='count';c.textContent=cnt;b.append(l,c);b.disabled=!cnt||cnt==='0 枚';b.addEventListener('click',fn);units.appendChild(b);};
    if(d.lesson&&d.lesson.length){
      mkStep('1','読む','この日の内容を基礎から',pagesLabel(ci),()=>openReader(ci));
      mkStep('2','用語','言葉の意味を先に覚える',(d.terms||[]).length+' 枚',()=>start(ci,'term'),null,ci+'|term');
      mkStep('3','部品','1枚1つの事実で積み上げる',(d.facts||[]).length+' 枚',()=>start(ci,'fact'),null,ci+'|fact');
      mkStep('4','まとめ','試験形式の一問一答',cardsOf(ci,'sum').length+' 枚',()=>start(ci,'sum'),null,ci+'|sum');
    } else if(own(ci,null).length){
      mkStep('4','まとめ',d.from?'この日の新しいカード':'試験形式の一問一答(読む・用語・部品は準備中)',cardsOf(ci,'sum').length+' 枚',()=>start(ci,'sum'),null,ci+'|sum');
    }
    if(d.rev.length) mk('復習:'+revLabel(d),cardsOf(ci,'rev').length,'rev',null,'前の全Dayから、今日が期限のカード');
    if(d.from) mk('通しで始める',cardsOf(ci,null).length,null,'all','模擬(予定は変えない)');
    else if(d.secs.length>1){const m=document.createElement('div');m.className='minor';m.textContent='まとめを単元ごとに';units.appendChild(m);
      d.secs.forEach((s,si)=>{mk(s.title,cardsOf(ci,si).length,si);units.lastChild.classList.add('small');});}
    det.appendChild(units); box.appendChild(det);
  });
  $('total').textContent=total;
  addChecks();
  addProg();
}
function addChecks(){
  const D=loadDone();
  document.querySelectorAll('#chapters details').forEach((det,ci)=>{
    const btns=[...det.querySelectorAll('.units .unit')]; let n=0,k=0;
    btns.forEach((b,bi)=>{
      const id=ci+'-'+bi, row=document.createElement('div'); row.className='urow';
      const lab=document.createElement('label'); lab.className='chk';
      const cb=document.createElement('input'); cb.type='checkbox'; cb.checked=!!D[id];
      cb.setAttribute('aria-label',b.firstChild.textContent.replace(/^\d/,'')+' 終わった');
      cb.addEventListener('change',()=>{const S=loadDone(); if(cb.checked)S[id]=1; else delete S[id]; saveDone(S); row.classList.toggle('done',cb.checked); prog();});
      lab.appendChild(cb); b.replaceWith(row); row.append(lab,b); row.classList.toggle('done',cb.checked);
    });
    const sum=det.querySelector('summary'), p=document.createElement('span'); p.className='prog'; sum.insertBefore(p,sum.lastChild);
    function prog(){const cs=[...det.querySelectorAll('.chk input')], c=cs.filter(x=>x.checked).length;
      p.textContent=c?'✓ '+c+'/'+cs.length:''; det.classList.toggle('done',c>0&&c===cs.length);}
    prog();
  });
}
function loadDone(){try{return JSON.parse(localStorage.getItem(DONE_KEY)||'{}')||{};}catch(e){return {};}}
function saveDone(S){try{localStorage.setItem(DONE_KEY,JSON.stringify(S));}catch(e){}}
function mix(a){for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];}return a;}
function start(ci,si,cram){
  full=cardsOf(ci,si); if(!full.length) return;
  const t=split(DECKS[ci].title);
  const mode=(cram||isCram(ci,si))?'cram':'srs';
  cur={ci,si,mode,key:progKey(ci,si)+(cram?'|c':'')};
  $('uTitle').textContent='Day '+t.n+' '+t.en;
  $('uSub').textContent=subName(ci,si)+(starOnly?' ・★のみ':'')+(cram?' ・ 練習(予定は変えない)':'');
  $('toast').hidden=true; $('doneBox').hidden=true; $('acts').classList.toggle('srs',mode==='srs');
  $('home').hidden=true; $('study').hidden=false; window.scrollTo(0,0);
  if(mode==='cram'){round=1; if(!restoreProg()) refill(); saveProg(); cc=queue[0]; show(); return;}
  const rank=new Map();(shuffle?mix(full.slice()):full).forEach((c,i)=>{const id=cid(c);if(!rank.has(id))rank.set(id,i);});
  const k=counts(full,si==='rev');sess={rank,rnd:new Map(),last:null,undo:[],init:k.n+k.l+k.r};
  saveLast({type:'deck',mode:'srs',ci,si,star:starOnly,label:$('uTitle').textContent+' ・ '+$('uSub').textContent,t:Date.now()});
  next();
}
function refill(){queue=full.slice(); if(shuffle) mix(queue);}
function next(){cc=pick(); if(cc){$('doneBox').hidden=true; show();} else showDone();}
function showDone(){
  $('card').hidden=true; $('acts').hidden=true; $('doneBox').hidden=false;
  const T=today(),noNew=cur.si==='rev';let tm=0,later=null;const seen=new Set();
  full.forEach(c=>{const id=cid(c);if(seen.has(id))return;seen.add(id);const s=SRS[id];if(!s)return;
    if(s.q===2&&s.d===T+1)tm++; if((s.q===1||s.q===3)&&(later==null||s.d<later))later=s.d;});
  $('doneTitle').textContent=noNew?'今日が期限の復習は全部終わりました':'このデッキの今日の分は終わりました';
  $('doneText').textContent=(later!=null?'学習中のカードが '+dur((later-Date.now())/6e4)+'後に戻ります。':'')+'明日の復習予定:'+tm+' 枚。';
  statsLine(); $('fill').style.width='100%'; $('undo').hidden=false; $('undo').disabled=!(sess&&sess.undo.length); $('restart').hidden=true; $('round').hidden=true;
}
function statsLine(){
  if(cur.mode==='cram'){$('left').textContent='残り '+queue.length+' / '+full.length+' 枚';$('round').textContent=round+' 周目';
    $('fill').style.width=((full.length-queue.length)/full.length*100)+'%';return;}
  const k=counts(full,cur.si==='rev');fillCounts($('left'),k,cur.si==='rev');
  const rem=k.n+k.l+k.r,base=Math.max(sess.init,rem,1);$('fill').style.width=((base-rem)/base*100)+'%';
}
function show(){
  flipped=false; const c=cc;
  $('card').hidden=false; $('acts').hidden=false;
  $('cSec').textContent=c.sec||''; $('cStar').textContent='★'.repeat(c.s||0);
  const kd=cur.mode==='srs'?kindOf(stOf(c)):'';$('cState').textContent={n:'新規',l:'学習中',r:'復習'}[kd]||'';$('cState').className='cstate '+kd;
  $('q').textContent=c.q;
  renderAnswer($('a'),c.a);
  $('noteText').textContent=c.n||'';
  paint();
  statsLine();
}
function nowCard(){return cc;}
function splitTop(t,sep){const out=[];let d=0,cur='';for(const ch of t){if(ch==='('||ch==='(')d++;else if(ch===')'||ch===')')d=Math.max(0,d-1);if(d===0&&ch===sep){if(cur.trim())out.push(cur.trim());cur='';}else cur+=ch;}if(cur.trim())out.push(cur.trim());return out;}
function splitArrows(t){const out=[];let d=0,cur='';for(const ch of t){if(ch==='('||ch==='(')d++;else if(ch===')'||ch===')')d=Math.max(0,d-1);if(ch==='→'&&(d===0||/^[((][^))]*$/.test(cur.trim())===false&&d===0)){out.push(cur.trim());cur='';}else cur+=ch;}out.push(cur.trim());return out.filter(x=>x);}
function inline(el,t){const re=/([((][^(())]*[))])/g;let last=0,m;while((m=re.exec(t))){if(m.index>last)el.append(t.slice(last,m.index));const s=document.createElement('span');s.className='paren';s.textContent=m[1];el.append(s);last=m.index+m[1].length;}if(last<t.length)el.append(t.slice(last));}
function body(parent,t){
  const parts=splitArrows(t);
  if(parts.length<3){
    let items=splitTop(t,'、'); if(items.length<3){const alt=t.split(/,\s+(?![^((]*[))])/); if(alt.length>=4) items=alt;}
    if(items.length>=3&&items.every(x=>x.length<=60)){const ul=document.createElement('ul');ul.className='items';items.forEach(x=>{const li=document.createElement('li');inline(li,x);ul.append(li);});parent.append(ul);return;}
    const p=document.createElement('div');inline(p,t);parent.append(p);return;}
  const ol=document.createElement('ol');ol.className='steps';let via='';
  parts.forEach(p=>{
    if(/^[((][^(())]*[))]$/.test(p)){via=p.slice(1,-1);return;}
    const li=document.createElement('li');
    if(via){const v=document.createElement('span');v.className='via';v.textContent=via;li.append(v);via='';}
    inline(li,p);ol.append(li);
  });
  parent.append(ol);
}
function topLabel(seg){let d=0;for(let i=0;i<seg.length&&i<=26;i++){const ch=seg[i];if(ch==='('||ch==='(')d++;else if(ch===')'||ch===')')d=Math.max(0,d-1);else if(ch==='→'||ch==='。')return null;else if(ch===':'&&d===0)return i>0&&i<seg.length-1?[seg,seg.slice(0,i),seg.slice(i+1)]:null;}return null;}
function renderAnswer(box,t){
  box.textContent='';
  splitTop(t,'。').forEach(seg=>{
    const d=document.createElement('div');d.className='seg';
    const m=topLabel(seg);
    if(m){const l=document.createElement('span');l.className='lab';l.textContent=m[1].trim();d.append(l);body(d,m[2].trim());}
    else{d.classList.add('plain');body(d,seg);}
    box.append(d);
  });
}
function paint(){
  const c=cc, srs=cur.mode==='srs';
  $('card').classList.toggle('flipped',flipped); $('rule').hidden=$('a').hidden=!flipped; $('note').hidden=!flipped||!c.n; $('hint').hidden=flipped;
  $('btnShow').hidden=flipped; $('btnAgain').hidden=$('btnOk').hidden=!flipped||srs;
  document.querySelectorAll('#acts [data-b]').forEach(b=>{b.hidden=!flipped||!srs;if(srs&&flipped)b.querySelector('small').textContent=ivLabel(stOf(c),+b.dataset.b);});
  $('undo').hidden=!srs; $('undo').disabled=!(sess&&sess.undo.length); $('restart').hidden=srs; $('round').hidden=srs;
}
function flip(){ if(cc&&!flipped&&!$('card').hidden){flipped=true; paint(); $('toast').hidden=true;} }
function verdict(known){
  if(!flipped||cur.mode!=='cram') return;
  const c=queue.shift();
  if(!known) queue.push(c);
  if(!queue.length){ round++; refill(); $('toast').hidden=false; }
  saveProg(); cc=queue[0]; show();
}
function answer(b){
  if(!flipped||!cc||cur.mode!=='srs') return;
  const id=cid(cc),prev=SRS[id]?{...SRS[id]}:null;
  sess.undo.push({id,prev,card:cc}); if(sess.undo.length>50) sess.undo.shift();
  SRS[id]=sched(prev,b,true); saveSrs(); sess.last=id; next();
}
function undo(){
  const u=sess&&sess.undo.pop(); if(!u) return;
  if(u.prev) SRS[u.id]=u.prev; else delete SRS[u.id]; saveSrs(); sess.last=null;
  $('doneBox').hidden=true; cc=u.card; show();
}
$('card').addEventListener('click',flip);
$('btnShow').addEventListener('click',flip);
$('btnAgain').addEventListener('click',()=>verdict(false));
$('btnOk').addEventListener('click',()=>verdict(true));
document.querySelectorAll('#acts [data-b]').forEach(b=>b.addEventListener('click',()=>answer(+b.dataset.b)));
$('undo').addEventListener('click',undo);
$('doneHome').addEventListener('click',()=>{$('study').hidden=true;$('home').hidden=false;renderHome();});
$('doneCram').addEventListener('click',()=>start(cur.ci,cur.si,true));
$('back').addEventListener('click',()=>{$('study').hidden=true;$('home').hidden=false;renderHome();});
$('resume').addEventListener('click',resumeLast);
$('restart').addEventListener('click',()=>{if(!cur||cur.mode!=='cram'||!confirm('このデッキを最初からやり直しますか?'))return;round=1;refill();saveProg();$('toast').hidden=true;cc=queue[0];show();});
$('optStar').addEventListener('click',e=>{starOnly=!starOnly;e.currentTarget.setAttribute('aria-pressed',starOnly);renderHome();});
$('optShuffle').addEventListener('click',e=>{shuffle=!shuffle;e.currentTarget.setAttribute('aria-pressed',shuffle);});
document.addEventListener('keydown',e=>{
  if($('study').hidden) return;
  if((e.key==='z'||e.key==='Z')&&cur&&cur.mode==='srs'){undo();return;}
  if(e.key===' '||e.key==='Enter'){ if(document.activeElement.tagName==='BUTTON') return; e.preventDefault(); flip(); }
  else if(cur&&cur.mode==='srs'){ if(/^[1-4]$/.test(e.key)) answer(+e.key); }
  else if(e.key==='ArrowRight') verdict(true);
  else if(e.key==='ArrowLeft') verdict(false);
});
