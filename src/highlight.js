// ---- 蛍光ペン(「読む」の本文に色を塗る)----
// 2つの塗り方:
//  ・文字を選ぶ(長押し/ドラッグ)と色のボタンが出る → 押すと塗る。塗った所をタップすると色を変える・消す。
//  ・🖍 ボタンでペンモード → 指やマウスで文字の上をなぞると塗れる(スマホは横になぞると塗り、縦の動きはスクロール)。
// 保存:neuro-hl-day = { ページのキー(Day:見出し): [[段落番号, 始め, 終わり, 色, 塗った文字], ...] }。端末間で同期する。
const HL_KEY='neuro-hl-day',HL_COLS=['y','g','p','b'],HL_NAME={y:'黄',g:'緑',p:'ピンク',b:'青'};
let hlBlocks=[],hlDrag=null,hlPen=false,hlTarget=null;
function hlLoad(){try{return JSON.parse(localStorage.getItem(HL_KEY)||'{}')||{};}catch(e){return {};}}
function hlCol(){try{const c=localStorage.getItem('neuro-hl-col');return c==='x'||HL_COLS.indexOf(c)>=0?c:'y';}catch(e){return 'y';}}
// 段落ごとの塗り(runs)から、1文字ずつの色の並びを作る
function hlArr(b){const a=new Array(b.text.length).fill(null);b.runs.forEach(([s,e,c])=>{for(let i=s;i<e&&i<a.length;i++)a[i]=c;});return a;}
function hlRunsOf(a){const r=[];let i=0;while(i<a.length){if(!a[i]){i++;continue;}let j=i;while(j<a.length&&a[j]===a[i])j++;r.push([i,j,a[i]]);i=j;}return r;}
function hlPaint(b,dr){const a=hlArr(b);if(dr)for(let i=dr.s;i<dr.e&&i<a.length;i++)a[i]=dr.c;
  const el=b.el;el.textContent='';let i=0;
  while(i<a.length){let j=i;while(j<a.length&&a[j]===a[i])j++;const t=b.text.slice(i,j);
    if(a[i]){const m=document.createElement('mark');m.className='hl hl-'+a[i];m.dataset.s=i;m.dataset.e=j;m.textContent=t;el.append(m);}
    else el.append(document.createTextNode(t));i=j;}}
// ページを描いたあとに呼ぶ:保存した塗りを本文に戻す(本文が書き直されていたら、同じ文字列を探して付け直す)
function hlPage(){hlHide();hlDrag=null;hlBlocks=[];
  document.querySelectorAll('#reader .rtext [data-bi]').forEach(el=>{hlBlocks[+el.dataset.bi]={el,text:el.textContent,runs:[]};});
  const all=hlBlocks.filter(Boolean),saved=hlLoad()[pk(rd.ci,rd.p)]||[];
  saved.forEach(([bi,s,e,c,t])=>{if(HL_COLS.indexOf(c)<0||!t)return;let b=hlBlocks[bi];
    if(!(b&&b.text.slice(s,e)===t)){let k=b?b.text.indexOf(t):-1;
      if(k<0){b=all.find(x=>x.text.indexOf(t)>=0);k=b?b.text.indexOf(t):-1;}
      if(k<0)return;s=k;e=k+t.length;}
    b.runs.push([s,e,c]);});
  all.forEach(b=>{b.runs=hlRunsOf(hlArr(b));hlPaint(b,null);});}
function hlStore(){const H=hlLoad(),k=pk(rd.ci,rd.p),out=[];
  hlBlocks.forEach((b,bi)=>{if(b)b.runs.forEach(([s,e,c])=>out.push([bi,s,e,c,b.text.slice(s,e)]));});
  if(out.length)H[k]=out;else delete H[k];try{localStorage.setItem(HL_KEY,JSON.stringify(H));}catch(e){}}
// ranges = [{bi,s,e}]、c = 色(null で消す)
function hlApply(ranges,c){ranges.forEach(r=>{const b=hlBlocks[r.bi];if(!b)return;const a=hlArr(b);for(let i=r.s;i<r.e&&i<a.length;i++)a[i]=c;b.runs=hlRunsOf(a);});
  hlStore();hlBlocks.forEach(b=>{if(b)hlPaint(b,null);});}
// 画面上の位置(DOM)→ 段落番号と、その段落の何文字目か
function hlOff(node,off){if(!node)return null;const el=(node.nodeType===1?node:node.parentNode);const bl=el&&el.closest&&el.closest('#reader .rtext [data-bi]');if(!bl)return null;
  const r=document.createRange();try{r.setStart(bl,0);r.setEnd(node,off);}catch(e){return null;}return {bi:+bl.dataset.bi,o:r.toString().length};}
function hlCaret(x,y){let n,o;
  if(document.caretPositionFromPoint){const p=document.caretPositionFromPoint(x,y);if(!p)return null;n=p.offsetNode;o=p.offset;}
  else if(document.caretRangeFromPoint){const r=document.caretRangeFromPoint(x,y);if(!r)return null;n=r.startContainer;o=r.startOffset;}
  else return null;return hlOff(n,o);}
// 2点の間(段落をまたいでもよい)を、段落ごとの範囲にする
function hlSpan(a,f){if(f.bi<a.bi||(f.bi===a.bi&&f.o<a.o))[a,f]=[f,a];const out=[];
  hlBlocks.forEach((b,bi)=>{if(!b||bi<a.bi||bi>f.bi)return;const s=bi===a.bi?a.o:0,e=bi===f.bi?f.o:b.text.length;if(e>s)out.push({bi,s,e});});return out;}
function hlSelRanges(){const sel=getSelection();if(!sel||sel.isCollapsed||!sel.rangeCount)return [];const R=sel.getRangeAt(0),out=[];
  hlBlocks.forEach((b,bi)=>{if(!b||!R.intersectsNode(b.el))return;
    const s=b.el.contains(R.startContainer)?(hlOff(R.startContainer,R.startOffset)||{o:0}).o:0;
    const e=b.el.contains(R.endContainer)?(hlOff(R.endContainer,R.endOffset)||{o:b.text.length}).o:b.text.length;
    if(e>s)out.push({bi,s,e});});return out;}
// ---- 色のボタン(文字を選んだとき・塗った所をタップしたとき)----
function hlHide(){hlTarget=null;const p=$('hlPop');if(p)p.hidden=true;}
function hlShow(rect,ranges,onMark){hlTarget=ranges;const p=$('hlPop');p.classList.toggle('onmark',!!onMark);p.hidden=false;
  const w=p.offsetWidth,h=p.offsetHeight;let top=rect.bottom+10;if(top+h>innerHeight-8)top=Math.max(8,rect.top-h-10);
  p.style.top=top+'px';p.style.left=Math.max(8,Math.min(innerWidth-w-8,rect.left+rect.width/2-w/2))+'px';}
let hlSelT=0;
document.addEventListener('selectionchange',()=>{if(hlPen||$('read').hidden)return;clearTimeout(hlSelT);hlSelT=setTimeout(()=>{
  const rs=hlSelRanges();if(rs.length){const sel=getSelection();hlShow(sel.getRangeAt(0).getBoundingClientRect(),rs,false);}
  else if(hlTarget&&!$('hlPop').classList.contains('onmark'))hlHide();},250);});
$('hlPop').addEventListener('pointerdown',e=>e.preventDefault());
$('hlPop').addEventListener('click',e=>{const bt=e.target.closest('button');if(!bt||!hlTarget)return;const c=bt.dataset.c;
  hlApply(hlTarget,c==='x'?null:c);try{getSelection().removeAllRanges();}catch(err){}hlHide();});
$('reader').addEventListener('click',e=>{if(hlPen)return;const mk=e.target.closest('mark.hl');const sel=getSelection();
  if(!mk||(sel&&!sel.isCollapsed))return;const bl=mk.closest('[data-bi]');if(!bl)return;
  hlShow(mk.getBoundingClientRect(),[{bi:+bl.dataset.bi,s:+mk.dataset.s,e:+mk.dataset.e}],true);});
document.addEventListener('pointerdown',e=>{if(!$('hlPop').hidden&&!e.target.closest('#hlPop')&&!e.target.closest('mark.hl'))setTimeout(()=>{if(!hlSelRanges().length)hlHide();},0);});
$('reader').addEventListener('scroll',()=>{if(hlTarget)hlHide();},{capture:true,passive:true});
// ---- ペンモード ----
function hlSetPen(on){hlPen=on;hlHide();hlDrag=null;$('read').classList.toggle('pen',on);$('penBtn').setAttribute('aria-pressed',on?'true':'false');$('penBar').hidden=!on;
  if(on){try{getSelection().removeAllRanges();}catch(e){}}hlPenCols();}
function hlPenCols(){const c=hlCol();[...$('penBar').querySelectorAll('button[data-c]')].forEach(b=>b.classList.toggle('on',b.dataset.c===c));}
$('penBtn').addEventListener('click',()=>hlSetPen(!hlPen));
$('penBar').addEventListener('click',e=>{const bt=e.target.closest('button');if(!bt)return;
  if(bt.id==='penDone'){hlSetPen(false);return;}try{localStorage.setItem('neuro-hl-col',bt.dataset.c);}catch(err){}hlPenCols();});
const hlIn=t=>t&&t.closest&&t.closest('#reader .rtext');
document.addEventListener('selectstart',e=>{if(hlPen&&hlIn(e.target.nodeType===1?e.target:e.target.parentNode))e.preventDefault();});
$('reader').addEventListener('contextmenu',e=>{if(hlPen&&hlIn(e.target))e.preventDefault();});
$('reader').addEventListener('pointerdown',e=>{if(!hlPen||!e.isPrimary||e.button>0||!hlIn(e.target)||e.target.closest('button,input,label,.figref'))return;
  const c=hlCaret(e.clientX,e.clientY);if(!c)return;if(e.pointerType==='mouse')e.preventDefault();
  hlDrag={a:c,f:c,x:e.clientX,y:e.clientY,moved:false,mk:e.target.closest('mark.hl'),id:e.pointerId};
  try{$('reader').setPointerCapture(e.pointerId);}catch(err){}});
function hlDraw(){const col=hlCol(),c=col==='x'?null:col,rs=hlDrag.moved?hlSpan(hlDrag.a,hlDrag.f):[];
  hlBlocks.forEach((b,bi)=>{if(!b)return;const r=rs.find(x=>x.bi===bi);hlPaint(b,r?{s:r.s,e:r.e,c}:null);});}
$('reader').addEventListener('pointermove',e=>{if(!hlDrag||e.pointerId!==hlDrag.id)return;
  if(!hlDrag.moved&&Math.hypot(e.clientX-hlDrag.x,e.clientY-hlDrag.y)<4)return;hlDrag.moved=true;
  const c=hlCaret(e.clientX,e.clientY);if(c)hlDrag.f=c;hlDraw();});
function hlEnd(e,cancel){if(!hlDrag||e.pointerId!==hlDrag.id)return;const d=hlDrag;hlDrag=null;const col=hlCol();
  if(cancel){hlBlocks.forEach(b=>{if(b)hlPaint(b,null);});return;}
  if(d.moved){const rs=hlSpan(d.a,d.f);if(rs.length){hlApply(rs,col==='x'?null:col);return;}}
  else if(d.mk&&col==='x'){const bl=d.mk.closest('[data-bi]');if(bl){hlApply([{bi:+bl.dataset.bi,s:+d.mk.dataset.s,e:+d.mk.dataset.e}],null);return;}}
  hlBlocks.forEach(b=>{if(b)hlPaint(b,null);});}
$('reader').addEventListener('pointerup',e=>hlEnd(e,false));
$('reader').addEventListener('pointercancel',e=>hlEnd(e,true));
document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('read').hidden){if(!$('hlPop').hidden)hlHide();else if(hlPen)hlSetPen(false);}});
// 別の端末で塗った分が届いたら、開いているページを描き直す
window.addEventListener('neuro-sync',e=>{const ks=(e.detail&&e.detail.keys)||[];if(ks.indexOf(HL_KEY)>=0&&!$('read').hidden&&!hlDrag&&!hlTarget)hlPage();});
