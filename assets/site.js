/* Shared navigation, search, text copying and deployed-version feedback. */
(()=>{
  const header=document.querySelector('.site-header');
  const sidebar=document.querySelector('.sidebar');
  function syncNavigationSize(){
    const headerHeight=header ? header.getBoundingClientRect().height : 0;
    const mobile=window.matchMedia('(max-width:780px)').matches;
    const sidebarHeight=mobile && sidebar ? sidebar.getBoundingClientRect().height : 0;
    document.documentElement.style.setProperty('--header-height',headerHeight+'px');
    document.documentElement.style.setProperty('--anchor-offset',(headerHeight+sidebarHeight+16)+'px');
  }
  syncNavigationSize();
  window.addEventListener('resize',syncNavigationSize);
  if('ResizeObserver' in window){
    const sizes=new ResizeObserver(syncNavigationSize);
    if(header)sizes.observe(header);
    if(sidebar)sizes.observe(sidebar);
  }
  function revealAnchor(){
    let id;try{id=decodeURIComponent(location.hash.slice(1))}catch{return}if(!id)return;
    const target=document.getElementById(id);if(!target)return;
    for(let parent=target;parent;parent=parent.parentElement)if(parent.tagName==='DETAILS')parent.open=true;
    if(target.tagName==='SUMMARY')target.parentElement.open=true;
    target.scrollIntoView({block:'start'});
  }
  window.addEventListener('hashchange',revealAnchor);
  if(location.hash)revealAnchor();
  const links=[...document.querySelectorAll('.sidebar a[href^="#"]')];
  if('IntersectionObserver' in window){
    const observer=new IntersectionObserver(entries=>{
      const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>a.boundingClientRect.top-b.boundingClientRect.top)[0];
      if(!visible)return;
      links.forEach(a=>{if(a.hash==='#'+visible.target.id)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')});
    },{rootMargin:'-110px 0px -55% 0px'});
    links.forEach(a=>{const el=document.getElementById(a.hash.slice(1));if(el)observer.observe(el)});
  }
  document.querySelectorAll('[data-filter-input]').forEach(input=>{
    const target=document.querySelector(input.dataset.filterInput);if(!target)return;
    const cards=[...target.querySelectorAll('[data-search]')];
    const count=document.getElementById(input.dataset.count),empty=document.getElementById(input.dataset.empty);
    const clearButton=document.querySelector('[data-clear-for="'+input.id+'"]');
    const persist=input.dataset.persistQuery==='true';
    const filter=(saveURL=false)=>{
      const words=input.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);let shown=0;
      cards.forEach(card=>{const hay=(card.textContent+' '+card.dataset.search).toLocaleLowerCase();card.hidden=!words.every(word=>hay.includes(word));if(!card.hidden)shown++});
      if(count)count.textContent=shown+'개 '+input.dataset.noun;
      if(empty)empty.hidden=shown!==0;
      if(clearButton)clearButton.hidden=!input.value;
      if(saveURL && persist){
        const url=new URL(location.href);
        if(input.value.trim())url.searchParams.set('q',input.value);else url.searchParams.delete('q');
        // Replacing this entry preserves the search when returning from a reading
        // page, without adding a browser-history entry for every keystroke.
        try{history.replaceState(history.state,'',url.href)}catch{}
      }
      document.querySelectorAll('[data-filter-for="'+input.id+'"]').forEach(button=>{
        button.setAttribute('aria-pressed',String((button.dataset.value||'')===input.value.trim()));
      });
    };
    const query=new URLSearchParams(location.search).get('q');if(query)input.value=query;
    input.addEventListener('input',()=>filter(true));filter();
    if(persist){
      const restore=()=>{input.value=new URLSearchParams(location.search).get('q')||'';filter()};
      window.addEventListener('pageshow',restore);
      window.addEventListener('popstate',restore);
    }
    clearButton?.addEventListener('click',()=>{input.value='';filter(true);input.focus()});
    document.querySelectorAll('[data-filter-for="'+input.id+'"]').forEach(button=>button.addEventListener('click',()=>{input.value=button.dataset.value||'';filter(true)}));
  });
  document.querySelectorAll('.sort-toggle').forEach(group=>{
    const list=document.getElementById('lecture-list');if(!list)return;
    const cards=[...list.children].filter(el=>el.matches('[data-video-id],[data-kind]'));
    const original=new Map(cards.map((card,index)=>[card,index]));
    const buttons=[...group.querySelectorAll('[data-sort]')];
    const stamp=(card,key)=>{const value=Date.parse(card.dataset[key]||'');return Number.isNaN(value)?-Infinity:value};
    const apply=(mode,save)=>{
      if(!buttons.some(button=>button.dataset.sort===mode))mode='latest';
      const key=mode==='added'?'added':'date';
      // 같은 값이면 등록 순서(최신순)를 유지하고, 값이 없는 자료는 맨 뒤로 보낸다.
      [...cards].sort((a,b)=>stamp(b,key)-stamp(a,key)||original.get(a)-original.get(b)).forEach(card=>list.appendChild(card));
      buttons.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.sort===mode)));
      if(save){
        try{localStorage.setItem('study-hub-sort',mode)}catch{}
        const url=new URL(location.href);
        if(mode==='latest')url.searchParams.delete('sort');else url.searchParams.set('sort',mode);
        try{history.replaceState(history.state,'',url.href)}catch{}
      }
    };
    const saved=()=>{let mode=new URLSearchParams(location.search).get('sort');if(!mode){try{mode=localStorage.getItem('study-hub-sort')}catch{}}return mode||'latest'};
    buttons.forEach(button=>button.addEventListener('click',()=>apply(button.dataset.sort,true)));
    apply(saved(),false);
    window.addEventListener('pageshow',()=>apply(saved(),false));
  });
  document.querySelectorAll('[data-copy-target]').forEach(button=>{
    const originalLabel=button.textContent.trim();
    let resetTimer;
    button.addEventListener('click',async()=>{
      const source=document.getElementById(button.dataset.copyTarget);
      const status=button.parentElement.querySelector('[role="status"]')||document.getElementById('status');
      if(!source)return;
      clearTimeout(resetTimer);
      try{
        if(!navigator.clipboard?.writeText)throw new Error('Clipboard API unavailable');
        await navigator.clipboard.writeText(source.textContent);
        button.textContent='복사 완료 ✓';
        if(status)status.textContent='복사됨';
      }catch{
        const disclosure=source.closest?.('details');
        if(disclosure)disclosure.open=true;
        const selection=window.getSelection(),range=document.createRange();
        range.selectNodeContents(source);selection.removeAllRanges();selection.addRange(range);
        button.textContent='텍스트 선택됨';
        if(status)status.textContent='선택한 내용을 직접 복사해 주세요.';
      }
      resetTimer=setTimeout(()=>{button.textContent=originalLabel;if(status)status.textContent=''},2200);
    });
  });
  document.querySelectorAll('[data-expand-scope]').forEach(button=>button.addEventListener('click',()=>{
    document.querySelectorAll(button.dataset.expandScope+' details').forEach(d=>d.open=button.dataset.expand==='true');
  }));

  // The label identifies the JavaScript actually loaded by this tab. A fresh,
  // uncached version manifest allows comparison with the currently deployed site.
  const siteScriptURL=document.currentScript?.src;
  const CLIENT_VERSION=siteScriptURL ? new URL(siteScriptURL).searchParams.get('v') || 'unknown' : 'unknown';
  const footer=document.querySelector('.site-footer-inner');
  if(footer && siteScriptURL){
    const versionBox=document.createElement('span');
    versionBox.className='site-version';
    versionBox.setAttribute('role','status');
    versionBox.textContent='화면 v'+CLIENT_VERSION+' · 최신 버전 확인 중';
    footer.append(versionBox);
    const manifestURL=new URL('../build-info.json',siteScriptURL);
    manifestURL.searchParams.set('check',String(Date.now()));
    fetch(manifestURL.href,{cache:'no-store'})
      .then(response=>{if(!response.ok)throw new Error('Version check unavailable');return response.json()})
      .then(info=>{
        if(typeof info.version!=='string')throw new Error('Invalid version');
        if(info.version===CLIENT_VERSION){
          versionBox.textContent='화면 v'+CLIENT_VERSION+' · 최신 버전';
        }else{
          versionBox.textContent='화면 v'+CLIENT_VERSION+' · 최신 v'+info.version+' · ';
          const refresh=document.createElement('a');
          const url=new URL(location.href);
          url.searchParams.set('refresh',info.version);
          refresh.href=url.href;
          refresh.textContent='새 버전 열기';
          versionBox.append(refresh);
        }
      })
      .catch(()=>{versionBox.textContent='화면 v'+CLIENT_VERSION+' · 최신 버전 확인 실패'});
  }

  // Cache only same-origin public reading pages; no personal records are stored.
  if ('serviceWorker' in navigator && (location.protocol === 'https:' || location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
    const assetScript = document.currentScript;
    if (assetScript?.src) {
      const workerURL = new URL('../sw.js', assetScript.src);
      workerURL.searchParams.set('v', new URL(assetScript.src).searchParams.get('v') || 'unversioned');
      navigator.serviceWorker.register(workerURL.href).catch(() => {});
    }
  }
})();

/* Reading progress: a thin bar on long reading pages. Decorative only; no state is stored. */
(()=>{
  const page=document.querySelector('.compact-lecture,.summary-page');
  if(!page||page.classList.contains('offline-content'))return;
  const bar=document.createElement('div');
  bar.className='read-progress';
  bar.setAttribute('aria-hidden','true');
  const host=document.querySelector('.site-header')||document.body;
  host.append(bar);
  const motion=window.matchMedia('(prefers-reduced-motion: reduce)');
  let frame=0,current=0,target=0,last=0;
  const measure=()=>{
    const total=document.documentElement.scrollHeight-window.innerHeight;
    return total>0?Math.min(1,Math.max(0,window.scrollY/total)):0;
  };
  const paint=()=>bar.style.setProperty('--p',String(current));
  const animate=time=>{
    frame=0;
    const elapsed=last?Math.min(time-last,64):16;
    last=time;
    current=motion.matches?target:current+(target-current)*(1-Math.exp(-elapsed/85));
    if(Math.abs(target-current)<0.0001)current=target;
    paint();
    if(current!==target)frame=requestAnimationFrame(animate);else last=0;
  };
  const schedule=()=>{
    target=measure();
    if(!frame)frame=requestAnimationFrame(animate);
  };
  const restore=()=>{
    if(frame)cancelAnimationFrame(frame);
    frame=0;last=0;current=target=measure();paint();
  };
  window.addEventListener('scroll',schedule,{passive:true});
  window.addEventListener('resize',schedule);
  window.addEventListener('pageshow',restore);
  motion.addEventListener('change',schedule);
  if('ResizeObserver' in window)new ResizeObserver(schedule).observe(document.body);
  restore();
})();

// Highlight the section currently being read. Plain anchors work without JS.
(()=>{
  const nav=document.querySelector('.reading-nav');
  if(!nav)return;
  const links=[...nav.querySelectorAll('a[href^="#"]')];
  const sections=links.map(link=>document.getElementById(link.hash.slice(1)));
  let frame=0;
  const update=()=>{
    frame=0;
    const edge=nav.getBoundingClientRect().bottom+32;
    let active=0;
    sections.forEach((section,index)=>{if(section&&section.getBoundingClientRect().top<=edge)active=index});
    links.forEach((link,index)=>{if(index===active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current')});
  };
  const schedule=()=>{if(!frame)frame=requestAnimationFrame(update)};
  addEventListener('scroll',schedule,{passive:true});
  addEventListener('resize',schedule);
  addEventListener('pageshow',schedule);
  update();
})();
