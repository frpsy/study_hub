/* 명령 팔레트 검색: site.js가 처음 열 때만 불러온다. 색인은 search-index.json(제목·한 줄 요약·강연자·주제·태그·상세 요약 소제목).
   결과는 텍스트 노드로만 만든다(검색어와 색인 문자열을 HTML로 해석하지 않는다). */
(()=>{
  'use strict';
  const script=document.currentScript;
  const base=new URL('../',script.src);
  const normalize=v=>v.normalize('NFKC').toLocaleLowerCase();
  const compact=v=>v.replace(/([가-힣])\s+(?=[가-힣])/g,'$1');
  let items=null,loading=null,active=0,results=[],opener=null;
  const sheet=document.createElement('dialog');
  sheet.className='search-sheet';
  sheet.setAttribute('aria-label','강의 검색');
  sheet.innerHTML='<form method="dialog" class="search-sheet-bar" role="search"><svg aria-hidden="true" viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 4 4"/></svg><input type="search" placeholder="제목·내용·소제목 검색" aria-label="검색어" autocomplete="off" role="combobox" aria-expanded="true" aria-controls="search-sheet-results" aria-autocomplete="list"><button type="submit" class="search-sheet-close">닫기</button></form><p class="search-sheet-status" role="status" aria-live="polite"></p><ul id="search-sheet-results" class="search-sheet-results" role="listbox" aria-label="검색 결과"></ul><p class="search-sheet-hint" aria-hidden="true"><kbd>↑</kbd><kbd>↓</kbd> 이동 · <kbd>Enter</kbd> 열기 · <kbd>Esc</kbd> 닫기</p>';
  document.body.append(sheet);
  const input=sheet.querySelector('input'),list=sheet.querySelector('ul'),status=sheet.querySelector('[role=status]');
  const load=()=>loading||(loading=fetch(new URL('search-index.json',base),{cache:'no-cache'})
    .then(r=>{if(!r.ok)throw new Error('index');return r.json()})
    .then(rows=>{items=rows.map(row=>({row,title:normalize(row.t),body:normalize([row.l,row.c,row.p,...row.g].join(' ')),heads:row.s.map(h=>normalize(h))}));render()})
    .catch(()=>{loading=null;status.textContent=navigator.onLine===false?'오프라인 상태라 검색할 수 없습니다. 인터넷에 연결한 뒤 다시 열어 주세요.':'검색 색인을 불러오지 못했습니다.'}));
  const has=(text,word)=>text.includes(word)||(/[가-힣]/.test(word)&&compact(text).includes(word));
  const search=query=>{
    const words=normalize(query.trim()).split(/\s+/).filter(Boolean);
    if(!words.length)return items.slice(0,8).map(item=>({item,score:0}));
    const out=[];
    for(const item of items){
      const all=[item.title,item.body,...item.heads].join(' / ');
      if(!words.every(w=>has(all,w)))continue;
      const head=item.heads.findIndex(h=>words.some(w=>has(h,w)));
      const score=words.reduce((s,w)=>s+(has(item.title,w)?4:0)+(head>=0&&has(item.heads[head],w)?2:0)+(has(item.body,w)?1:0),0);
      out.push({item,score,head});
    }
    return out.sort((a,b)=>b.score-a.score).slice(0,20);
  };
  const select=index=>{
    const options=[...list.children];if(!options.length)return;
    active=(index+options.length)%options.length;
    options.forEach((o,i)=>o.setAttribute('aria-selected',String(i===active)));
    input.setAttribute('aria-activedescendant',options[active].id);
    options[active].scrollIntoView({block:'nearest'});
  };
  const render=()=>{
    if(!items)return;
    results=search(input.value);
    list.replaceChildren(...results.map(({item,head},i)=>{
      const li=document.createElement('li');li.id='search-opt-'+i;li.setAttribute('role','option');
      const a=document.createElement('a');a.tabIndex=-1;
      const row=item.row,anchor=head>=0?'#detail-'+(head+1):'';
      a.href=new URL('lectures/'+row.id+'.html'+anchor,base).href;
      const t=document.createElement('strong');t.textContent=row.t;
      const d=document.createElement('span');d.textContent=head>=0?'상세 요약 · '+row.s[head]:row.l;
      const m=document.createElement('small');m.textContent=row.p+' · '+row.c;
      a.append(t,d,m);li.append(a);return li;
    }));
    status.textContent=input.value.trim()?(results.length?results.length+'개 강의':'검색 결과가 없습니다.'):'최근 강의';
    select(0);
  };
  input.addEventListener('input',render);
  input.addEventListener('keydown',event=>{
    if(event.key==='ArrowDown'){event.preventDefault();select(active+1)}
    else if(event.key==='ArrowUp'){event.preventDefault();select(active-1)}
    else if(event.key==='Enter'){const link=list.children[active]?.querySelector('a');if(link){event.preventDefault();location.href=link.href}}
  });
  list.addEventListener('mousemove',event=>{const li=event.target.closest('li');if(li)select([...list.children].indexOf(li))});
  sheet.addEventListener('click',event=>{if(event.target===sheet)sheet.close()});
  sheet.addEventListener('close',()=>{opener?.focus?.();opener=null});
  window.studySearchOpen=from=>{
    opener=from||document.activeElement;
    if(!sheet.open)sheet.showModal();
    input.select();load();render();
  };
})();
