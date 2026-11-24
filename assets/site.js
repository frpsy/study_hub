/* Shared navigation, search, text copying and deployed-version feedback. */
(()=>{
  const header=document.querySelector('.site-header');
  const sidebar=document.querySelector('.sidebar');
  const readingNav=document.querySelector('.reading-nav');
  let headerHidden=false;
  function syncNavigationSize(){
    const headerHeight=header ? header.getBoundingClientRect().height : 0;
    const mobile=window.matchMedia('(max-width:780px)').matches;
    const sidebarHeight=mobile && sidebar ? sidebar.getBoundingClientRect().height : 0;
    document.documentElement.style.setProperty('--header-height',headerHeight+'px');
    // 강의 페이지는 헤더 아래에 목차가 붙어 있다. 앵커로 이동하면 섹션의 위 선이 목차 아래 선과 겹치게 둔다.
    const navHeight=readingNav ? readingNav.getBoundingClientRect().height : 0;
    const shownHeader=headerHidden ? 0 : headerHeight;
    const offset=readingNav ? shownHeader+navHeight-1 : shownHeader+sidebarHeight+16;
    document.documentElement.style.setProperty('--anchor-offset',offset+'px');
  }
  syncNavigationSize();
  window.addEventListener('resize',syncNavigationSize);
  if('ResizeObserver' in window){
    const sizes=new ResizeObserver(syncNavigationSize);
    if(header)sizes.observe(header);
    if(sidebar)sizes.observe(sidebar);
    if(readingNav)sizes.observe(readingNav);
  }
  // 본문을 내려 읽을 때는 헤더를 숨기고, 올리면 다시 보인다. 맨 위 근처와 헤더 안 초점 이동 중에는 항상 보인다.
  if(header){
    const root=document.documentElement;
    let lastY=window.scrollY,ticking=false,lockUntil=0;
    const setHidden=hidden=>{if(headerHidden!==hidden){headerHidden=hidden;root.classList.toggle('header-hidden',hidden);syncNavigationSize()}};
    function updateHeaderVisibility(){
      ticking=false;
      const y=Math.max(0,window.scrollY);
      if(performance.now()<lockUntil){lastY=y;return}
      const delta=y-lastY;
      const limit=header.getBoundingClientRect().height+60;
      if(y<=limit||delta<-6)setHidden(false);
      else if(delta>6&&!header.contains(document.activeElement))setHidden(true);
      if(Math.abs(delta)>6||y<=limit)lastY=y;
    }
    window.addEventListener('scroll',()=>{if(!ticking){ticking=true;requestAnimationFrame(updateHeaderVisibility)}},{passive:true});
    header.addEventListener('focusin',()=>setHidden(false));
    // 페이지 안 링크로 이동할 때는 도착 방향에 맞춰 헤더 상태를 먼저 정하고, 도착 위치가 목차와 맞도록 한다.
    document.addEventListener('click',event=>{
      const link=event.target.closest&&event.target.closest('a[href^="#"]');
      if(!link||link.getAttribute('href').length<2)return;
      let id;try{id=decodeURIComponent(link.getAttribute('href').slice(1))}catch{return}
      const target=document.getElementById(id);
      if(!target)return;
      const top=target.getBoundingClientRect().top;
      const arrivalY=window.scrollY+top;
      lockUntil=performance.now()+900;
      setHidden(top>0&&arrivalY>header.getBoundingClientRect().height+60);
    },true);
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
  const libraryKeys={bookmarks:'study-hub-bookmarks',read:'study-hub-read'};
  const library={bookmarks:new Set(),read:new Set()};
  const libraryButtons=[...document.querySelectorAll('[data-library-toggle]')];
  const refreshLibraryButtons=()=>{
    libraryButtons.forEach(button=>{
      const lecture=button.closest('[data-video-id]');
      const kind=button.dataset.libraryToggle;
      const selected=library[kind].has(lecture.dataset.videoId);
      button.setAttribute('aria-pressed',String(selected));
      if(kind==='bookmarks'){
        button.title=selected?'저장 취소':'나중에 읽을 강의 저장';
        button.setAttribute('aria-label',selected?'북마크 저장됨':'북마크 저장');
        const label=button.querySelector('[data-bookmark-label]');
        if(label)label.textContent=selected?'저장됨':'저장';
      }
      else{
        lecture.classList.toggle('is-read',selected);
        const label=button.querySelector('[data-read-label]');
        if(label)label.textContent=button.closest('.lecture-card')?'읽음':(selected?'읽음 완료':'읽음 표시');
      }
    });
  };
  const restoreLibrary=()=>{
    for(const [kind,key] of Object.entries(libraryKeys)){
      try{
        const values=JSON.parse(localStorage.getItem(key));
        library[kind]=new Set(Array.isArray(values)?values.filter(value=>typeof value==='string'):[]);
      }catch{}
    }
    refreshLibraryButtons();
  };
  restoreLibrary();
  libraryButtons.forEach(button=>{
    button.hidden=false;
    button.addEventListener('click',()=>{
      const id=button.closest('[data-video-id]').dataset.videoId;
      const kind=button.dataset.libraryToggle,ids=library[kind];
      if(ids.has(id))ids.delete(id);else ids.add(id);
      try{localStorage.setItem(libraryKeys[kind],JSON.stringify([...ids]))}catch{}
      refreshLibraryButtons();
      document.dispatchEvent(new Event('library-change'));
      if(button.closest('[hidden]'))document.querySelector('[data-bookmark-filter]')?.focus();
    });
  });
  window.addEventListener('pageshow',restoreLibrary);
  window.addEventListener('storage',event=>{
    if(event.key===null||Object.values(libraryKeys).includes(event.key)){
      restoreLibrary();
      document.dispatchEvent(new Event('library-change'));
    }
  });
  document.querySelectorAll('[data-filter-input]').forEach(input=>{
    const target=document.querySelector(input.dataset.filterInput);if(!target)return;
    const normalize=value=>value.normalize('NFKC').toLocaleLowerCase();
    const compactHangul=value=>value.replace(/([가-힣])\s+(?=[가-힣])/g,'$1');
    const searchIndex=[...target.querySelectorAll('[data-search]')].map(card=>{
      const sections=[...card.querySelectorAll('.search-section-link')].map(link=>({
        link,heading:normalize(link.querySelector('span').textContent),
        source:link.dataset.searchDetail||link.querySelector('span').textContent,
        text:normalize(link.dataset.searchDetail||link.querySelector('span').textContent)
      }));
      const lead=card.querySelector('.card-lead')?.textContent||'';
      const text=normalize([card.dataset.search,lead,...sections.map(section=>section.text)].join(' / '));
      return {card,text,compactText:compactHangul(text),sections};
    });
    const count=document.getElementById(input.dataset.count),empty=document.getElementById(input.dataset.empty);
    const topicLabel=target.querySelector('#catalog-topic');
    const clearButton=document.querySelector('[data-clear-for="'+input.id+'"]');
    const chips=[...target.querySelectorAll('[data-filter-for="topic"]')];
    const bookmarkFilter=target.querySelector('[data-bookmark-filter]');
    const persist=input.dataset.persistQuery==='true';
    const emptySearch=empty?.querySelector('[data-clear-search]');
    const emptyTopic=empty?.querySelector('[data-clear-topic]');
    const emptyMessage=empty?.querySelector('[data-empty-message]');
    const emptyBookmarks=empty?.querySelector('[data-clear-bookmarks]');
    const searchEmptyMessage=emptyMessage?.textContent;
    let topic='',bookmarkedOnly=false;
    const filter=(saveURL=false)=>{
      const words=normalize(input.value.trim()).split(/\s+/).filter(Boolean);let shown=0;
      const matches=(text,compactText)=>words.every(word=>text.includes(word)||(/[가-힣]/.test(word)&&compactText.includes(word)));
      const feature=target.querySelector('.today-line');
      if(feature)feature.hidden=words.length>0;
      searchIndex.forEach(({card,text,compactText,sections})=>{
        const matchesTopic=!topic||card.dataset.topic===topic;
        const matchesBookmark=!bookmarkedOnly||library.bookmarks.has(card.dataset.videoId);
        card.hidden=!matchesTopic||!matchesBookmark||!matches(text,compactText);
        if(!card.hidden)shown++;
        const match=!card.hidden&&words.length
          ? sections.find(section=>matches(section.heading,compactHangul(section.heading)))
            ||sections.filter(section=>matches(section.text,compactHangul(section.text)))
              .sort((a,b)=>words.reduce((score,word)=>score+b.text.split(word).length-a.text.split(word).length,0))[0]
          : undefined;
        sections.forEach(section=>{section.link.hidden=section!==match});
        const context=card.querySelector('.search-context');
        if(context){
          context.hidden=card.hidden||!words.length;
          context.replaceChildren();
          if(!context.hidden){
            const source=match?match.source:card.dataset.search||text;
            const lower=source.toLocaleLowerCase();
            const indices=words.map(word=>lower.indexOf(word)).filter(index=>index>=0);
            const start=Math.max(0,(indices.length?Math.min(...indices):0)-30);
            const excerpt=(start?'…':'')+source.slice(start,start+120)+(source.length>start+120?'…':'');
            context.append(document.createTextNode('검색된 문맥 · '));
            // Construct text nodes only: search terms and source text are never HTML.
            let rest=excerpt;
            while(rest){
              const found=words.map(word=>({word,index:rest.toLocaleLowerCase().indexOf(word)}))
                .filter(hit=>hit.index>=0).sort((a,b)=>a.index-b.index||b.word.length-a.word.length)[0];
              if(!found){context.append(document.createTextNode(rest));break}
              context.append(document.createTextNode(rest.slice(0,found.index)));
              const mark=document.createElement('mark');
              mark.textContent=rest.slice(found.index,found.index+found.word.length);context.append(mark);
              rest=rest.slice(found.index+found.word.length);
            }
          }
        }
      });
      if(topicLabel)topicLabel.textContent=[topic,bookmarkedOnly?'북마크':''].filter(Boolean).join(' · ')||'전체';
      bookmarkFilter?.setAttribute('aria-pressed',String(bookmarkedOnly));
      if(count)count.textContent=shown+'개 '+input.dataset.noun;
      if(empty)empty.hidden=shown!==0;
      if(emptyMessage){
        emptyMessage.textContent=bookmarkedOnly
          ? (library.bookmarks.size?'조건에 맞는 북마크가 없습니다.':'북마크한 강의가 없습니다.')
          : searchEmptyMessage;
      }
      if(emptyBookmarks)emptyBookmarks.hidden=!bookmarkedOnly;
      if(clearButton)clearButton.hidden=!input.value;
      if(emptySearch)emptySearch.hidden=!words.length;
      if(emptyTopic)emptyTopic.hidden=!topic;
      if(saveURL && persist){
        const url=new URL(location.href);
        if(input.value.trim())url.searchParams.set('q',input.value);else url.searchParams.delete('q');
        if(topic)url.searchParams.set('topic',topic);else url.searchParams.delete('topic');
        if(bookmarkedOnly)url.searchParams.set('bookmarks','1');else url.searchParams.delete('bookmarks');
        // Replacing this entry preserves the search when returning from a reading
        // page, without adding a browser-history entry for every keystroke.
        try{history.replaceState(history.state,'',url.href)}catch{}
      }
      chips.forEach(button=>button.setAttribute('aria-pressed',String((button.dataset.value||'')===topic)));
    };
    const fromURL=()=>{
      const params=new URLSearchParams(location.search);
      input.value=params.get('q')||'';
      const wanted=params.get('topic')||'';
      bookmarkedOnly=params.get('bookmarks')==='1'||wanted==='bookmarks';
      topic=chips.some(button=>button.dataset.value===wanted)?wanted:'';
    };
    fromURL();
    if(bookmarkFilter){
      bookmarkFilter.hidden=false;
      bookmarkFilter.addEventListener('click',()=>{bookmarkedOnly=!bookmarkedOnly;filter(true)});
    }
    document.addEventListener('library-change',()=>filter());
    input.addEventListener('input',()=>filter(true));filter();
    if(persist){
      const restore=()=>{fromURL();filter()};
      window.addEventListener('pageshow',restore);
      window.addEventListener('popstate',restore);
    }
    const clearSearch=()=>{input.value='';filter(true);input.focus()};
    clearButton?.addEventListener('click',clearSearch);
    emptySearch?.addEventListener('click',clearSearch);
    emptyTopic?.addEventListener('click',()=>{topic='';filter(true);chips.find(button=>!button.dataset.value)?.focus()});
    emptyBookmarks?.addEventListener('click',()=>{bookmarkedOnly=false;filter(true);bookmarkFilter?.focus()});
    chips.forEach(button=>button.addEventListener('click',()=>{
      const value=button.dataset.value||'';
      topic=topic===value?'':value;
      filter(true);
    }));
  });
  // 오늘의 한 문장: 날짜마다 다른 강의의 한 문장을 보여 준다. 스크립트가 없으면 최신 강의가 그대로 보인다.
  const today=document.querySelector('.today-line');
  if(today){
    const pool=[...document.querySelectorAll('#lecture-list .lecture-card')].filter(card=>card.querySelector('.card-lead'));
    if(pool.length){
      const now=new Date();
      const day=Math.floor((Date.UTC(now.getFullYear(),now.getMonth(),now.getDate())-Date.UTC(2026,0,1))/864e5);
      const quote=today.querySelector('.today-key'),source=today.querySelector('.today-source');
      const random=today.querySelector('.today-random');
      const render=card=>{
        const title=card.querySelector('.card-link');
        quote.textContent=card.querySelector('.card-lead').textContent;
        source.setAttribute('href',title.getAttribute('href'));
        source.textContent=title.textContent+' · '+card.dataset.creator;
      };
      render(pool[((day%pool.length)+pool.length)%pool.length]);
      const alternatives=()=>pool.filter(card=>card.querySelector('.card-lead').textContent!==quote.textContent);
      random.hidden=!alternatives().length;
      random.addEventListener('click',()=>{
        const choices=alternatives();
        if(!choices.length)return;
        quote.classList.remove('is-changing');
        render(choices[Math.floor(Math.random()*choices.length)]);
        if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
          void quote.offsetWidth;
          quote.classList.add('is-changing');
        }
      });
    }
  }
  document.querySelectorAll('.catalog-sort').forEach(select=>{
    const list=document.getElementById('lecture-list');if(!list)return;
    const cards=[...list.children].filter(el=>el.matches('[data-video-id],[data-kind]'));
    const original=new Map(cards.map((card,index)=>[card,index]));
    const modes=new Set([...select.options].map(option=>option.value));
    const stamp=(card,key)=>{const value=Date.parse(card.dataset[key]||'');return Number.isNaN(value)?-Infinity:value};
    const views=card=>{const raw=card.dataset.views;const value=raw===undefined||raw===''?NaN:Number(raw);return Number.isNaN(value)?-Infinity:value};
    const note=document.getElementById('views-note');
    const apply=(mode,save)=>{
      if(!modes.has(mode))mode='latest';
      const key=mode==='added'?'added':'date';
      const value=mode==='views'?views:card=>stamp(card,key);
      // 같은 값이면 등록 순서(최신순)를 유지하고, 값이 없는 자료는 맨 뒤로 보낸다.
      [...cards].sort((a,b)=>value(b)-value(a)||original.get(a)-original.get(b)).forEach(card=>list.appendChild(card));
      list.dataset.sortMode=mode;
      if(note)note.hidden=mode!=='views';
      select.value=mode;
      if(save){
        try{localStorage.setItem('study-hub-sort',mode)}catch{}
        const url=new URL(location.href);
        if(mode==='latest')url.searchParams.delete('sort');else url.searchParams.set('sort',mode);
        try{history.replaceState(history.state,'',url.href)}catch{}
      }
    };
    const saved=()=>{let mode=new URLSearchParams(location.search).get('sort');if(!mode){try{mode=localStorage.getItem('study-hub-sort')}catch{}}return mode||'latest'};
    select.hidden=false;
    select.addEventListener('change',()=>apply(select.value,true));
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
    // 섹션 제목이 목차 바로 아래 읽는 영역(화면 위쪽 4분의 1)에 들어오면 그 섹션을 현재 위치로 본다.
    const edge=nav.getBoundingClientRect().bottom+Math.max(32,innerHeight*.25);
    let active=0;
    sections.forEach((section,index)=>{if(section&&section.getBoundingClientRect().top<=edge)active=index});
    if(innerHeight+scrollY>=document.documentElement.scrollHeight-2)active=sections.length-1;
    links.forEach((link,index)=>{if(index===active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current')});
  };
  const schedule=()=>{if(!frame)frame=requestAnimationFrame(update)};
  addEventListener('scroll',schedule,{passive:true});
  addEventListener('resize',schedule);
  addEventListener('pageshow',schedule);
  update();
})();

// 깊이 목차: 섹션과 상세 요약 소제목을 한 시트에 모은다. 링크는 원래 앵커를 그대로 쓴다.
(()=>{
  const nav=document.querySelector('.reading-nav');
  if(!nav||typeof HTMLDialogElement!=='function')return;
  const detailLinks=[...document.querySelectorAll('.detail-toc a[href^="#"]')];
  const sheet=document.createElement('dialog');
  sheet.className='outline-sheet';
  sheet.setAttribute('aria-label','이 강의 전체 목차');
  const list=document.createElement('ol');
  [...nav.querySelectorAll('a[href^="#"]')].forEach(link=>{
    const item=document.createElement('li');
    const copy=link.cloneNode(true);copy.removeAttribute('aria-current');
    item.append(copy);
    if(link.hash==='#lecture-detail'&&detailLinks.length){
      const sub=document.createElement('ol');
      detailLinks.forEach(d=>{const li=document.createElement('li');li.append(d.cloneNode(true));sub.append(li)});
      item.append(sub);
    }
    list.append(item);
  });
  const head=document.createElement('div');head.className='outline-head';
  const title=document.createElement('strong');title.textContent='목차';
  const close=document.createElement('button');close.type='button';close.className='outline-close';close.textContent='닫기';
  head.append(title,close);sheet.append(head,list);
  const button=document.createElement('button');
  button.type='button';button.className='outline-fab';button.setAttribute('aria-haspopup','dialog');
  const label=document.createElement('span');const prefix=document.createElement('b');prefix.textContent='목차';button.append(prefix,label);
  document.body.append(sheet,button);
  const current=()=>nav.querySelector('[aria-current="location"]')||nav.querySelector('a');
  const sync=()=>{
    const active=current();label.textContent=active?active.textContent:'';
    const foot=document.querySelector('.site-footer');
    const nearFooter=foot&&foot.getBoundingClientRect().top<innerHeight;
    button.classList.toggle('is-visible',(nav.getBoundingClientRect().bottom<0||scrollY>480)&&!nearFooter);
    sheet.querySelectorAll(':scope>ol>li>a').forEach(a=>a.classList.toggle('is-current',active&&a.hash===active.hash));
  };
  button.addEventListener('click',()=>{sync();sheet.showModal()});
  close.addEventListener('click',()=>sheet.close());
  sheet.addEventListener('click',event=>{
    if(event.target===sheet){sheet.close();return}
    const link=event.target.closest('a[href^="#"]');
    if(link){sheet.close()}
  });
  let frame=0;
  addEventListener('scroll',()=>{if(!frame)frame=requestAnimationFrame(()=>{frame=0;sync()})},{passive:true});
  addEventListener('pageshow',sync);
  sync();
})();

// Keep only the latest unfinished lecture and its section, on this browser.
(()=>{
  const key='study-hub-resume';
  const banner=document.querySelector('.resume-reading');
  const lecture=document.querySelector('main.compact-lecture[data-video-id]');
  if(!banner&&!lecture)return;
  const load=()=>{try{return JSON.parse(localStorage.getItem(key))}catch{return null}};
  const isRead=id=>{try{const ids=JSON.parse(localStorage.getItem('study-hub-read'));return Array.isArray(ids)&&ids.includes(id)}catch{return false}};
  const clear=()=>{try{localStorage.removeItem(key)}catch{}if(banner)banner.hidden=true};
  const refresh=()=>{
    if(!banner)return;
    banner.hidden=true;
    const saved=load();
    if(!saved||typeof saved.id!=='string'||typeof saved.anchor!=='string'||
      !/^(lecture-(overview|detail|comment|sources)|detail-\d+)$/.test(saved.anchor))return;
    if(isRead(saved.id)){clear();return}
    const card=[...document.querySelectorAll('.lecture-card[data-video-id]')].find(card=>card.dataset.videoId===saved.id);
    const link=card?.querySelector('.card-link');if(!link)return;
    const resume=banner.querySelector('[data-resume-link]');
    resume.href=link.getAttribute('href')+'#'+saved.anchor;
    banner.querySelector('[data-resume-title]').textContent=link.textContent;
    banner.querySelector('[data-resume-section]').textContent=typeof saved.label==='string'?saved.label.slice(0,120):'';
    banner.hidden=false;
  };
  banner?.querySelector('[data-resume-clear]').addEventListener('click',clear);
  if(lecture){
    const headings=[...lecture.querySelectorAll('.lecture-section > h2,.detail-body > h3')];
    const save=()=>{
      if(isRead(lecture.dataset.videoId))return;
      if(scrollY<300)return;
      const edge=(document.querySelector('.reading-nav')?.getBoundingClientRect().bottom||0)+80;
      const current=headings.filter(h=>h.getBoundingClientRect().top<=edge).at(-1)||headings[0];
      if(!current)return;
      const anchor=current.id||current.parentElement.id;
      try{localStorage.setItem(key,JSON.stringify({id:lecture.dataset.videoId,anchor,label:current.textContent}))}catch{}
    };
    let timer;
    addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(save,250)},{passive:true});
    addEventListener('pagehide',()=>{clearTimeout(timer);save()});
    document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')save()});
    document.addEventListener('library-change',()=>{if(isRead(lecture.dataset.videoId)&&load()?.id===lecture.dataset.videoId)clear()});
  }
  document.addEventListener('library-change',refresh);
  addEventListener('pageshow',refresh);
  addEventListener('storage',event=>{if(event.key===key||event.key==='study-hub-read'||event.key===null)refresh()});
  refresh();
})();
