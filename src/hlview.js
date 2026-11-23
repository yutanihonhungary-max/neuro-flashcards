// ---- 塗った所の一覧(ホームの「🖍 塗った所」から)----
// 蛍光ペンで塗った所だけを、Day → ページの順に並べる。Day・色で絞り込み、「前後の文も表示」で段落ごと見られる。
// 項目をタップすると、そのページの「読む」を開いてその段落まで移動する(「← 塗った所に戻る」で一覧へ)。
let hlvDay='',hlvCol='',hlvMode=null;
function hlvCtx(){if(hlvMode==null){try{hlvMode=localStorage.getItem('neuro-hlv-ctx')==='1';}catch(e){hlvMode=false;}}return hlvMode;}
function hlvRaw(){try{return JSON.parse(localStorage.getItem('neuro-hl-day')||'{}')||{};}catch(e){return {};}}
function hlvBlockText(line){let m;if(/^!img\s/.test(line))return null;if((m=line.match(/^-\s+(.*)$/))||(m=line.match(/^\d+\.\s+(.*)$/)))return m[1];return line;}
// 保存した塗りを、いまの本文に当てはめる(「読む」で開いたときと同じ付け直し方)
function hlvPages(){const H=hlvRaw(),out=[];
  Object.keys(H).forEach(k=>{const i=k.indexOf(':');const ci=+k.slice(0,i),h=k.slice(i+1);const D=DECKS[ci];if(!D||!D.lesson)return;
    const p=D.lesson.findIndex(x=>x.h===h);if(p<0)return;const blocks=[];
    D.lesson[p].b.forEach((line,bi)=>{const t=hlvBlockText(line);if(t!=null)blocks[bi]={text:t,a:new Array(t.length).fill(null)};});
    const all=blocks.map((b,bi)=>b&&{b,bi}).filter(Boolean);
    (H[k]||[]).forEach(([bi,s,e,c,t])=>{if(!t||!/^[ygpb]$/.test(c))return;let b=blocks[bi];
      if(!(b&&b.text.slice(s,e)===t)){let j=b?b.text.indexOf(t):-1;if(j<0){const f=all.find(x=>x.b.text.indexOf(t)>=0);if(f){b=f.b;j=b.text.indexOf(t);}}if(j<0)return;s=j;e=j+t.length;}
      for(let q=s;q<e;q++)b.a[q]=c;});
    const bl=[];blocks.forEach((b,bi)=>{if(b&&b.a.some(Boolean))bl.push({bi,text:b.text,a:b.a});});
    if(bl.length)out.push({ci,p,h,blocks:bl});});
  return out.sort((x,y)=>x.ci-y.ci||x.p-y.p);}
// 段落の中の、塗った所のかたまり(色が違っても続いていれば1つ)
function hlvGroups(b,col){const g=[];let i=0;const a=b.a;
  while(i<a.length){if(!a[i]){i++;continue;}let j=i;while(j<a.length&&a[j])j++;if(!col||a.slice(i,j).indexOf(col)>=0)g.push([i,j]);i=j;}return g;}
function hlvMarks(el,text,a,from,to){let i=from;while(i<to){let j=i;while(j<to&&a[j]===a[i])j++;const t=text.slice(i,j);
  if(a[i]){const m=document.createElement('mark');m.className='hl hl-'+a[i];m.textContent=t;el.append(m);}else el.append(document.createTextNode(t));i=j;}}
function hlvCount(){const b=$('hlvBtn');if(!b)return;let n=0;hlvPages().forEach(pg=>pg.blocks.forEach(bl=>{n+=hlvGroups(bl,'').length;}));
  b.querySelector('small').textContent=n?n+' か所':'まだありません';}
function hlvOpen(){$('home').hidden=true;$('hlv').hidden=false;
  const sel=$('hlvDay');if(!sel.options.length){sel.append(new Option('すべてのDay',''));DECKS.forEach((d,ci)=>{if(d.lesson&&d.lesson.length){const t=split(d.title);sel.append(new Option('Day '+t.n+' '+t.en,String(ci)));}});}
  hlvRender();window.scrollTo(0,0);}
function hlvRender(){const box=$('hlvList');box.textContent='';$('hlvDay').value=hlvDay;$('hlvCtx').checked=hlvCtx();
  [...$('hlvCols').children].forEach(b=>b.classList.toggle('on',b.dataset.c===hlvCol));
  const pages=hlvPages().filter(pg=>hlvDay===''||pg.ci===+hlvDay);let n=0,lastCi=-1;
  pages.forEach(pg=>{const items=[];pg.blocks.forEach(bl=>{const g=hlvGroups(bl,hlvCol);if(g.length)items.push({bl,g});});if(!items.length)return;
    if(pg.ci!==lastCi){lastCi=pg.ci;const t=split(DECKS[pg.ci].title);const h=document.createElement('h2');h.textContent='Day '+t.n+' '+t.en;box.append(h);}
    const sec=document.createElement('section');sec.className='hlvpg';const hd=document.createElement('button');hd.type='button';hd.className='hlvh';
    hd.innerHTML='<span></span><small>📖 開く</small>';hd.firstChild.textContent=pg.h;hd.addEventListener('click',()=>hlvGo(pg.ci,pg.p,null));sec.append(hd);
    items.forEach(({bl,g})=>{if(hlvCtx()){n+=g.length;const p=document.createElement('button');p.type='button';p.className='hli ctx';hlvMarks(p,bl.text,bl.a,0,bl.text.length);
        p.addEventListener('click',()=>hlvGo(pg.ci,pg.p,bl.bi));sec.append(p);}
      else g.forEach(([s,e])=>{n++;const p=document.createElement('button');p.type='button';p.className='hli';hlvMarks(p,bl.text,bl.a,s,e);
        p.addEventListener('click',()=>hlvGo(pg.ci,pg.p,bl.bi));sec.append(p);});});
    box.append(sec);});
  $('hlvSum').textContent=n?n+' か所':'';
  if(!n){const p=document.createElement('p');p.className='hlvnone';
    p.textContent=Object.keys(hlvRaw()).length?'この条件で塗った所はありません。':'まだ塗った所がありません。「読む」で文字を選ぶか、🖍 でなぞると塗れます。';box.append(p);}}
function hlvGo(ci,p,bi){jump={y:window.scrollY,list:true};rd={ci,p};const t=split(DECKS[ci].title);$('rTitle').textContent='Day '+t.n+' '+t.en;$('rSub').textContent='① 読む';setBackLabel();
  $('hlv').hidden=true;$('read').hidden=false;renderPage();try{history.pushState({jump:1},'');}catch(e){}
  if(bi!=null){const el=document.querySelector('#reader .rtext [data-bi="'+bi+'"]');if(el){el.scrollIntoView({block:'center'});el.classList.add('hlflash');setTimeout(()=>el.classList.remove('hlflash'),1600);}}}
$('hlvBtn').addEventListener('click',hlvOpen);
$('hlvBack').addEventListener('click',()=>{$('hlv').hidden=true;$('home').hidden=false;renderHome();});
$('hlvDay').addEventListener('change',e=>{hlvDay=e.target.value;hlvRender();});
$('hlvCols').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;hlvCol=b.dataset.c;hlvRender();});
$('hlvCtx').addEventListener('change',e=>{hlvMode=e.target.checked;try{localStorage.setItem('neuro-hlv-ctx',hlvMode?'1':'');}catch(err){}hlvRender();});
window.addEventListener('neuro-sync',e=>{const ks=(e.detail&&e.detail.keys)||[];if(ks.indexOf('neuro-hl-day')<0)return;if(!$('hlv').hidden)hlvRender();else if(!$('home').hidden)hlvCount();});
