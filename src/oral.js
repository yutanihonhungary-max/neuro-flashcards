// ---- 口頭練習(2026-11-27)。過去問(Signorelli 教授)の質問に、声に出して答える。
// 問いは src/oral.txt、要点のカードは src/oralmap.py が選ぶ(ビルドで ORAL に入る)。暗記の予定(Anki 方式)には入れない。
// 自己評価は問いごとに端末に保存し(neuro-oral-day = {英語の問い: {r:0言えなかった/1一部/2言えた, t:時刻, n:回数}})、端末間で同期する。
const ORAL_KEY='neuro-oral-day', ORAL_GOAL=120;
let oral={list:[],cur:-1,t0:0,timer:0,shown:false,onlyLearned:true};
function oralLoad(){try{return JSON.parse(localStorage.getItem(ORAL_KEY)||'{}')||{};}catch(e){return {};}}
function oralSave(q,r){const S=oralLoad(),p=S[q]||{};S[q]={r,t:Date.now(),n:(p.n||0)+1};try{localStorage.setItem(ORAL_KEY,JSON.stringify(S));}catch(e){}}
// 習ったDay = 日付の割り当てで、今日までに来ている Day(試験の日を過ぎたら全部)
function oralLearnedMax(){const td=today();let m=0;PLAN.forEach(e=>{if(dnum(e.d)<=td)e.c.forEach(ci=>{m=Math.max(m,ci+1);});});return m;}
function oralPool(){const m=oralLearnedMax();return ORAL.filter(x=>!oral.onlyLearned||x.days.every(d=>d<=m));}
function oralSummary(){const S=oralLoad(),P=oralPool();const ok=P.filter(x=>S[x.q]&&S[x.q].r===2).length;return ok+' / '+P.length+' 言えた';}
// 出す順:まだやっていない(★から) → 言えなかった → 一部 → 言えた(古い順)
function oralOrder(){const S=oralLoad();const rank=x=>{const s=S[x.q];if(!s)return x.star?0:1;return s.r===0?2:s.r===1?3:4;};
  return oralPool().map(x=>({x,k:rank(x),t:(S[x.q]&&S[x.q].t)||0,r:Math.random()})).sort((a,b)=>a.k-b.k||a.t-b.t||a.r-b.r).map(o=>o.x);}
function openOral(){oral.list=oralOrder();oral.cur=-1;$('home').hidden=true;$('study').hidden=true;$('oral').hidden=false;window.scrollTo(0,0);oralNext();}
function oralClose(){oralStop();$('oral').hidden=true;$('home').hidden=false;renderHome();}
function oralStop(){clearInterval(oral.timer);oral.timer=0;}
function oralTick(){const s=Math.floor((Date.now()-oral.t0)/1000);$('oTime').textContent=Math.floor(s/60)+':'+String(s%60).padStart(2,'0');
  $('oFill').style.width=Math.min(100,s/ORAL_GOAL*100)+'%';$('oTimerBox').classList.toggle('over',s>=ORAL_GOAL);}
function oralCounts(){const S=oralLoad(),P=oralPool();let a=0,b=0,c=0,n=0;P.forEach(x=>{const s=S[x.q];if(!s)n++;else if(s.r===2)a++;else if(s.r===1)b++;else c++;});
  $('oSum').textContent='言えた '+a+' ・ 一部 '+b+' ・ 言えなかった '+c+' ・ まだ '+n;}
function oralNext(){oralStop();
  if(!oral.list.length){$('oCard').hidden=true;$('oActs').hidden=true;$('oEmpty').hidden=false;oralCounts();return;}
  $('oEmpty').hidden=true;$('oCard').hidden=false;$('oActs').hidden=false;
  oral.cur=(oral.cur+1)%oral.list.length;const x=oral.list[oral.cur],S=oralLoad(),st=S[x.q];oral.shown=false;
  $('oPos').textContent=(oral.cur+1)+' / '+oral.list.length;
  $('oTag').textContent='Day '+x.days.join('・')+(x.star?' ・ ★ 何度も出た':'')+(st?' ・ 前回:'+['言えなかった','一部言えた','言えた'][st.r]:'');
  $('oQ').textContent=x.q;$('oJa').textContent=x.ja;
  $('oTime').textContent='0:00';$('oFill').style.width='0%';$('oTimerBox').classList.remove('over');$('oStart').textContent='▶ 話し始める';$('oStart').hidden=false;
  const fu=$('oFu');fu.textContent='';x.fu.forEach(t=>{const li=document.createElement('li');li.textContent=t;fu.append(li);});$('oFuBox').hidden=!x.fu.length;
  const pts=$('oPts');pts.textContent='';x.pts.forEach(p=>{const row=document.createElement('label');row.className='opt';
    const cb=document.createElement('input');cb.type='checkbox';cb.addEventListener('change',()=>row.classList.toggle('ok',cb.checked));
    const b=document.createElement('div');const q=document.createElement('b');q.textContent=(p.s?'★'.repeat(p.s)+' ':'')+p.q;
    const a=document.createElement('div');a.className='oa';renderAnswer(a,p.a);const dd=document.createElement('span');dd.className='od';dd.textContent='Day '+p.d;
    q.append(dd);b.append(q,a);row.append(cb,b);pts.append(row);});
  $('oAns').hidden=true;$('oShow').hidden=false;document.querySelectorAll('#oActs [data-r]').forEach(b=>b.hidden=true);
  oralCounts();}
function oralShow(){if(oral.shown)return;oral.shown=true;oralStop();$('oStart').hidden=true;$('oAns').hidden=false;$('oShow').hidden=true;
  document.querySelectorAll('#oActs [data-r]').forEach(b=>b.hidden=false);}
$('oStart').addEventListener('click',()=>{if(oral.timer){oralStop();$('oStart').textContent='▶ もう一度計る';return;}
  oral.t0=Date.now();oral.timer=setInterval(oralTick,250);oralTick();$('oStart').textContent='■ 止める';});
$('oShow').addEventListener('click',oralShow);
document.querySelectorAll('#oActs [data-r]').forEach(b=>b.addEventListener('click',()=>{const x=oral.list[oral.cur];if(!x)return;oralSave(x.q,+b.dataset.r);oralNext();}));
$('oSkip').addEventListener('click',oralNext);
$('oBack').addEventListener('click',oralClose);
$('oLearned').addEventListener('click',e=>{oral.onlyLearned=!oral.onlyLearned;e.currentTarget.setAttribute('aria-pressed',oral.onlyLearned);oral.list=oralOrder();oral.cur=-1;oralNext();});
document.addEventListener('keydown',e=>{if($('oral').hidden||e.altKey||e.ctrlKey||e.metaKey)return;
  if(e.key===' '||e.key==='Enter'){if(document.activeElement&&document.activeElement.tagName==='BUTTON')return;e.preventDefault();oralShow();}
  else if(oral.shown&&/^[1-3]$/.test(e.key)){const x=oral.list[oral.cur];oralSave(x.q,+e.key-1);oralNext();}});
window.addEventListener('neuro-sync',e=>{const ks=(e.detail&&e.detail.keys)||[];if(ks.indexOf(ORAL_KEY)>=0&&!$('oral').hidden)oralCounts();});
