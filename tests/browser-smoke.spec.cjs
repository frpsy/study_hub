const {test,expect}=require('@playwright/test');
const studyVersion=require('../build-info.json').version;
const studyLectures=require('../lectures.json');
const studyMaterials=require('../materials.json');
const expectedLibraryCount=studyLectures.length+studyMaterials.length;
const meditationCount=studyLectures.filter(x=>x.topic==='명상').length;
const kimLectureCount=studyLectures.filter(x=>x.creator==='김주환').length;
const sizes=[
  {width:360,height:780},
  {width:390,height:844},
  {width:768,height:900},
  {width:1280,height:800},
];

for(const viewport of sizes){
  test('shared home and timestamps remain usable at '+viewport.width+'px',async({browser})=>{
    const context=await browser.newContext({viewport,permissions:['clipboard-read','clipboard-write']});
    const page=await context.newPage();
    const pageErrors=[];
    page.on('pageerror',e=>pageErrors.push(e.message));
    for(const url of ['/index.html',...studyLectures.map(x=>'/lectures/'+x.id+'.html')]){
      await page.goto(url);
      await expect(page.locator('main')).toBeVisible();
      const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
      expect(overflow,'page overflow at '+url+' / '+viewport.width).toBeLessThanOrEqual(1);
    }
    await page.goto('/lectures/izYj8g-j00U.html#lecture-comment');
    const button=page.locator('[data-copy-target="comment"]');
    await expect(button).toBeVisible();
    await expect(button).toHaveText('타임스탬프 복사');
    const minHeight=await button.evaluate(el=>parseFloat(getComputedStyle(el).minHeight));
    expect(minHeight).toBeGreaterThanOrEqual(44);
    const comment=page.locator('#comment');
    const toggle=page.locator('#timeline-toggle');
    await expect(page.getByText('전체 타임스탬프 보기')).toHaveCount(0);
    await expect(comment).toBeVisible();
    const collapsed=await comment.evaluate(el=>({box:el.getBoundingClientRect().height,clipped:el.scrollHeight>el.clientHeight+1,overflowY:getComputedStyle(el).overflowY}));
    expect(collapsed.box).toBeLessThan(330);
    expect(collapsed.clipped,'collapsed timestamp box is cut off').toBe(true);
    expect(collapsed.overflowY,'collapsed timestamp box has no inner scroll').toBe('hidden');
    await comment.click();
    await expect(toggle).toBeChecked();
    const expanded=await comment.evaluate(el=>({box:el.getBoundingClientRect().height,scrolls:el.scrollHeight>el.clientHeight+1,overflowY:getComputedStyle(el).overflowY}));
    expect(expanded.box).toBeGreaterThan(collapsed.box+100);
    expect(expanded.scrolls,'expanded timestamp box shows everything').toBe(false);
    expect(expanded.overflowY).toBe('visible');
    await comment.click();
    await expect(toggle).not.toBeChecked();
    const source=await page.locator('#comment').textContent();
    await button.click();
    await expect(button).toHaveText('복사 완료 ✓');
    await expect(page.locator('#status')).toHaveText('복사됨');
    expect(await page.evaluate(()=>navigator.clipboard.readText())).toBe(source);
    await expect(button).toHaveText('타임스탬프 복사',{timeout:6000});
    await expect(page.locator('#status')).toBeEmpty();
    expect(pageErrors).toEqual([]);
    await context.close();
  });
}

test('glass header stays legible and cards stay compact on mobile',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/index.html');
  const info=await page.evaluate(()=>{
    const header=document.querySelector('.site-header');
    const card=document.querySelector('.lecture');
    const style=getComputedStyle(header);
    const match=style.backgroundColor.match(/rgba?\(([^)]+)\)/);
    const parts=match?match[1].split(',').map(Number):[];
    return {alpha:parts.length===4?parts[3]:1,blur:(style.backdropFilter||style.webkitBackdropFilter||''),headerHeight:header.getBoundingClientRect().height,cardHeight:card.getBoundingClientRect().height};
  });
  expect(info.alpha,'translucent header must keep enough opacity to stay legible').toBeGreaterThanOrEqual(0.7);
  if(info.alpha<1)expect(info.blur,'translucent header needs a backdrop blur').toContain('blur');
  expect(info.headerHeight,'mobile header should stay compact').toBeLessThan(80);
  expect(info.cardHeight,'cards should not stretch with empty space').toBeLessThan(400);
  await context.close();
});

test('home and lectures load from static cache without a network connection',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},serviceWorkers:'allow',reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/index.html');
  await page.waitForFunction(async()=>{
    const registration=await navigator.serviceWorker.ready;
    if(!navigator.serviceWorker.controller || !registration.active)return false;
    const names=await caches.keys();
    const name=names.find(n=>n.startsWith('study-home-static-'));
    if(!name)return false;
    const cache=await caches.open(name);
    return (await Promise.all(['./index.html','./lectures/izYj8g-j00U.html'].map(p=>cache.match(new URL(p,location.href))))).every(Boolean);
  },null,{timeout:15000});
  await context.setOffline(true);
  await page.goto('/lectures/izYj8g-j00U.html',{waitUntil:'domcontentloaded'});
  await expect(page.locator('#lecture-overview')).toBeVisible();
  await page.goto('/index.html',{waitUntil:'domcontentloaded'});
  await expect(page.locator('h1')).toHaveText('강의 요약');
  await context.close();
});

test('footer shows actual loaded version and checks deployed version separately',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844}});
  const page=await context.newPage();
  await page.goto('/index.html');
  await expect(page.locator('.site-version')).toContainText('화면 v'+studyVersion);
  await expect(page.locator('.site-version')).toContainText('최신 버전');
  await context.close();
});
test('footer provides a refresh link when deployed manifest is newer',async({browser})=>{
  const context=await browser.newContext();
  const page=await context.newPage();
  await page.route('**/build-info.json*',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({version:'2099.01.01.1'})}));
  await page.goto('/index.html');
  await expect(page.locator('.site-version')).toContainText('최신 v2099.01.01.1');
  await expect(page.locator('.site-version a')).toHaveAttribute('href',/refresh=2099.01.01.1/);
  await context.close();
});

test('login, record saving, and history UI are absent',async({page})=>{
 await page.goto('/index.html');
 for(const selector of ['#settings','#settings-toggle','#account-action','#account-history','#study-progress']){
  await expect(page.locator(selector)).toHaveCount(0);
 }
 await expect(page.getByRole('link',{name:'학습 이력'})).toHaveCount(0);
 await page.goto('/lectures/affirmation-20261101.html');
 await expect(page.locator('#study-progress')).toHaveCount(0);
 await expect(page.getByRole('button',{name:/학습 완료|복습 완료/})).toHaveCount(0);
 await expect(page.locator('#lecture-overview')).toBeVisible();
});

test('library identity and reading hierarchy stay consistent',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  for(const url of ['/index.html','/lectures/izYj8g-j00U.html']){
    await page.goto(url);
    await expect(page.locator('.site-brand .brand-name')).toContainText('내면의 서재');
    await expect(page.locator('.brand-symbol')).toBeVisible();
    expect(await page.locator('.brand-symbol').evaluate(el=>el.naturalWidth)).toBeGreaterThan(0);
    await expect(page).toHaveTitle(/내면의 서재/);
    await expect(page.locator('.global-nav')).toHaveCount(0);
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
    expect(overflow,'no horizontal overflow at '+url).toBeLessThanOrEqual(1);
  }
  await page.goto('/index.html');
  await expect(page.locator('.home-title')).toHaveText('강의 요약');
  const compact=await page.evaluate(()=>({
    headerHeight:document.querySelector('.site-header').getBoundingClientRect().height,
    titleHeight:document.querySelector('.home-title').getBoundingClientRect().height,
    cardCount:document.querySelectorAll('#home-catalog [data-kind]').length,
  }));
  expect(compact.headerHeight).toBeLessThan(80);
  expect(compact.titleHeight).toBeLessThan(95);
  expect(compact.cardCount).toBe(expectedLibraryCount);
  await page.locator('[data-filter-for="topic"][data-value="명상"]').click();
  await expect(page.locator('#count')).toHaveText(meditationCount+'개 강의');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(meditationCount);
  await page.locator('[data-filter-for="topic"][data-value="명상"]').click();  // 같은 주제를 다시 누르면 전체로 돌아간다.
  await expect(page.locator('#count')).toHaveText(expectedLibraryCount+'개 강의');
  await context.close();
});

test('home lists every lecture in one aligned column',async({browser})=>{
  for(const width of [360,390,768,1280]){
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto('/index.html');
    const m=await page.evaluate(()=>{
      const rect=el=>el.getBoundingClientRect();
      const cards=[...document.querySelectorAll('#lecture-list .lecture')].map(rect);
      return {lefts:[...new Set(cards.map(r=>Math.round(r.left)))],rights:cards.map(r=>r.right),width:cards[0].width,
        brand:rect(document.querySelector('.site-brand')).left,title:rect(document.querySelector('.home-title')).left,
        overflow:document.documentElement.scrollWidth-innerWidth};
    });
    expect(m.lefts).toHaveLength(1);
    expect(Math.abs(m.brand-m.title)).toBeLessThanOrEqual(1);
    expect(Math.abs(m.lefts[0]-m.title)).toBeLessThanOrEqual(1);
    expect(Math.max(...m.rights)).toBeLessThanOrEqual(width);
    expect(m.width).toBeGreaterThan(width<=780?width-40:700);
    expect(m.overflow).toBeLessThanOrEqual(1);
    await context.close();
  }
});

test('catalog searches by creator without losing video ID hooks',async({page})=>{
  await page.goto('/index.html');
  const items=page.locator('#lecture-list .lecture');
  await expect(items).toHaveCount(expectedLibraryCount);
  await expect(page.locator('[data-creator="Andrew Huberman"]')).toHaveCount(2);
  await page.locator('#search').fill('Huberman');
  await expect(page.locator('#count')).toHaveText('2개 강의');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(2);
  await expect(page.locator('#lecture-list .lecture[data-video-id="QmOF0crdyRU"]')).toBeVisible();
  await expect(page.locator('#lecture-list .lecture[data-video-id="9tRohh0gErM"]')).toBeVisible();
  await page.locator('#search').fill('김주환');
  await expect(page.locator('#count')).toHaveText(kimLectureCount+'개 강의');
});

test('catalog restores a shared search and returns to it after reading',async({page})=>{
  await page.goto('/index.html?q=Huberman&source=test#lectures');
  await expect(page.locator('#search')).toHaveValue('Huberman');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(2);
  await page.locator('#lecture-list .lecture:visible').first().click();
  await page.goBack();
  await expect(page.locator('#search')).toHaveValue('Huberman');
  await expect(page.locator('#count')).toHaveText('2개 강의');
  await page.locator('#search').fill('없는검색어');
  await expect(page.locator('#empty')).toBeVisible();
  await expect(page).toHaveURL(/q=/);
  await page.locator('[data-clear-for="search"]').click();
  await expect(page.locator('#search')).toBeFocused();
  await expect(page.locator('#search')).toHaveValue('');
  await expect(page.locator('#count')).toHaveText(expectedLibraryCount+'개 강의');
  expect(new URL(page.url()).searchParams.has('q')).toBe(false);
  expect(new URL(page.url()).searchParams.get('source')).toBe('test');
  await page.locator('[data-filter-for="topic"][data-value="마음근력"]').click();
  expect(new URL(page.url()).searchParams.get('topic')).toBe('마음근력');
  await page.reload();
  await expect(page.locator('#count')).toHaveText('6개 강의');
  await expect(page.locator('[data-filter-for="topic"][data-value="마음근력"]')).toHaveAttribute('aria-pressed','true');
  await page.locator('#search').fill('수용');  // 주제와 검색어는 함께 걸린다.
  await expect(page.locator('#count')).toHaveText('1개 강의');
});

test('a lecture card opens a page with the intro, detail summary and timestamps',async({page})=>{
  await page.goto('/index.html');
  await page.locator('#lecture-list [data-video-id="affirmation-20261101"]').click();
  await expect(page).toHaveURL(/\/lectures\/affirmation-20261101\.html$/);
  await expect(page.locator('main .lecture-section')).toHaveCount(3);
  await expect(page.locator('#lecture-overview>h2')).toHaveText('핵심 요약');
  await expect(page.locator('#lecture-detail>h2')).toHaveText('상세 요약');
  await expect(page.locator('#lecture-overview .intro-points li')).toHaveCount(3);
  await expect(page.locator('#lecture-overview .intro-steps details')).toHaveCount(4);
  const firstStep=page.locator('#lecture-overview .intro-steps details').first();
  await expect(firstStep.locator('ul')).toBeHidden();
  await firstStep.locator('summary').click();
  await expect(firstStep.locator('ul')).toBeVisible();
  await expect(page.locator('#lecture-comment>h2')).toHaveText('타임스탬프');
  for(const removed of ['핵심 요약','실천 포인트','5분 요약','미니강좌','용어와 개념']){
    await expect(page.getByText(removed,{exact:true})).toHaveCount(0);
  }
  await expect(page.locator('.summary-links')).toHaveCount(0);
  await page.locator('.breadcrumb a').click();
  await expect(page).toHaveURL(/\/index\.html$/);
});

test('lecture summary keeps a clear type hierarchy and readable width',async({browser})=>{
  for(const width of [360,390,768,1280]){
    const context=await browser.newContext({viewport:{width,height:844},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto('/lectures/affirmation-20261101.html');
    await expect(page.locator('#lecture-overview .intro-block>h3').first()).toHaveText('자기확언의 힘과 조건');
    await expect(page.locator('#lecture-overview .intro-points li')).toHaveCount(3);
    const m=await page.evaluate(()=>{
      const size=selector=>parseFloat(getComputedStyle(document.querySelector(selector)).fontSize);
      const box=document.querySelector('.compact-lecture').getBoundingClientRect();
      return {h1:size('h1'),h2:size('#lecture-overview>h2'),h3:size('#lecture-overview .intro-block>h3'),
        lead:size('#lecture-overview .summary-tier>.summary-lead'),list:size('#lecture-overview .intro-points li'),
        width:box.width,left:box.left,right:box.right,brand:document.querySelector('.site-brand').getBoundingClientRect().left,
        overflow:document.documentElement.scrollWidth-window.innerWidth};
    });
    expect(m.h1).toBeGreaterThan(m.h2);
    expect(m.h2).toBeGreaterThan(m.h3);
    expect(m.h3).toBeGreaterThanOrEqual(m.list);
    expect(m.list).toBeLessThanOrEqual(16);
    expect(m.lead).toBeLessThanOrEqual(17);
    expect(m.width).toBeLessThanOrEqual(width<=780 ? width-24 : 1041);
    expect(m.left).toBeGreaterThanOrEqual(width<=780 ? 12 : -1);
    expect(Math.abs(m.left-m.brand)).toBeLessThanOrEqual(1);
    expect(m.overflow).toBeLessThanOrEqual(1);
    await context.close();
  }
});

test('every lecture has a valid intro and source navigation',async({page})=>{
  test.setTimeout(90000);
  for(const row of studyLectures){
    await page.goto('/lectures/'+row.id+'.html');
    // 도입 형식: 블록의 종류와 개수는 강의 내용이 정한다. 구조와 출처 링크만 본다.
    await expect(page.locator('#lecture-overview>h2')).toHaveText('핵심 요약');
    await expect(page.locator('#lecture-overview .intro-points li').first()).toBeVisible();
    await expect(page.locator('#lecture-practice')).toHaveCount(1);
    await expect(page.locator('section#lecture-practice')).toHaveCount(0);
    const items=page.locator('#lecture-overview .practice-list>li');
    const count=await items.count();
    expect(count).toBeLessThanOrEqual(3);
    for(let i=0;i<count;i++){
      const item=items.nth(i);
      const labels=await item.locator('.practice-cells dt').allTextContents();
      expect(labels.slice(0,2)).toEqual(['언제','할 일']);
      expect([2,3]).toContain(labels.length);   // 확인 칸은 강연자가 말했을 때만 있다
      const source=item.locator('.practice-source');
      await expect(source).toBeVisible();
      if(row.creator==='김주환'){
        const expectedVideo=row.video_url||'https://www.youtube.com/watch?v='+row.id;
        const href=await source.getAttribute('href');
        expect(href).toContain(expectedVideo+'&t=');
        expect(href).toMatch(/&t=\d+s$/);
        expect(await source.getAttribute('target')).toBe('_blank');
        expect(await source.getAttribute('rel')).toContain('noopener');
        await expect(item.locator('.practice-quote')).toBeVisible();
      }
    }
  }
});

test('reading navigation and disclosures work on small screens without scripts',async({browser})=>{
  const context=await browser.newContext({viewport:{width:320,height:760},javaScriptEnabled:false,reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/lectures/izYj8g-j00U.html');
  await page.getByRole('navigation',{name:'이 강의 목차'}).getByRole('link',{name:'핵심 요약'}).click();
  await expect(page).toHaveURL(/#lecture-overview$/);
  // 도입의 해볼 일은 JS 없이 보이고, 영상 시각 링크도 바로 누를 수 있어야 한다.
  await expect(page.locator('#lecture-overview .practice-list>li').first()).toBeVisible();
  await expect(page.locator('#lecture-overview .practice-source').first()).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  await context.close();
});

test('reading navigation tracks sections and source disclosure opens',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/lectures/izYj8g-j00U.html');
  if(process.env.STUDY_SCREENSHOT_DIR)await page.screenshot({path:require('node:path').join(process.env.STUDY_SCREENSHOT_DIR,'study-hub-mobile.png')});
  const nav=page.getByRole('navigation',{name:'이 강의 목차'});
  await nav.getByRole('link',{name:'핵심 요약'}).click();
  await expect(nav.getByRole('link',{name:'핵심 요약'})).toHaveAttribute('aria-current','location');
  const geometry=await page.evaluate(()=>({heading:document.querySelector('#lecture-overview>h2').getBoundingClientRect().top,nav:document.querySelector('.reading-nav').getBoundingClientRect().bottom}));
  // 섹션은 목차 아래 선에 붙는다(다른 목차 테스트와 같은 2px 허용). 제목이 목차 아래로 가려지지 않는지 본다.
  expect(geometry.heading).toBeGreaterThanOrEqual(geometry.nav-2);
  if(process.env.STUDY_SCREENSHOT_DIR){
    await page.screenshot({path:require('node:path').join(process.env.STUDY_SCREENSHOT_DIR,'study-hub-practice.png')});
  }
  await nav.getByRole('link',{name:'출처'}).click();
  await expect(page.locator('#lecture-sources')).toHaveAttribute('open','');
  await context.close();
});

test('reading progress eases toward scroll position and respects reduced motion',async({page})=>{
 await page.emulateMedia({reducedMotion:'no-preference'});
 await page.goto('/lectures/VUHrJZbpIjI.html');
 await page.waitForTimeout(600);
 const sample=await page.evaluate(async()=>{
  const bar=document.querySelector('.read-progress');
  const value=()=>Number(bar.style.getPropertyValue('--p'));
  window.scrollTo({top:(document.documentElement.scrollHeight-innerHeight)/2,behavior:'instant'});
  await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
  return {value:value(),target:scrollY/(document.documentElement.scrollHeight-innerHeight)};
 });
 expect(sample.value).toBeGreaterThan(0);
 expect(sample.value).toBeLessThan(sample.target);
 await expect.poll(()=>page.locator('.read-progress').evaluate(el=>Number(el.style.getPropertyValue('--p')))).toBeCloseTo(sample.target,3);
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.evaluate(()=>window.scrollTo({top:0,behavior:'instant'}));
 await expect.poll(()=>page.locator('.read-progress').evaluate(el=>Number(el.style.getPropertyValue('--p')))).toBe(0);
});

for(const width of [390,1280]){
 test('progress stays visible below the header at '+width+'px',async({browser})=>{
  const context=await browser.newContext({viewport:{width,height:844},isMobile:width===390,hasTouch:width===390,reducedMotion:'no-preference'});
  const page=await context.newPage();
  await page.goto('/lectures/VUHrJZbpIjI.html');
  await page.evaluate(()=>window.scrollTo({top:800,behavior:'instant'}));
  const bar=page.locator('.site-header>.read-progress');
  // 아래로 읽으면 헤더가 숨고, 진행 막대는 화면 맨 위에 남는다.
  await expect(page.locator('html')).toHaveClass(/header-hidden/);
  await expect(bar).toBeVisible();
  await expect.poll(()=>bar.evaluate(el=>Math.round(el.getBoundingClientRect().top))).toBeGreaterThanOrEqual(0);
  await expect.poll(()=>bar.evaluate(el=>el.getBoundingClientRect().bottom)).toBeLessThanOrEqual(4);
  // 위로 올리면 헤더가 다시 보이고, 진행 막대는 헤더 아래에 붙는다.
  await page.evaluate(()=>window.scrollTo({top:700,behavior:'instant'}));
  await expect(page.locator('html')).not.toHaveClass(/header-hidden/);
  await expect.poll(()=>page.locator('.site-header').evaluate(el=>Math.round(el.getBoundingClientRect().top))).toBe(0);
  await expect.poll(()=>bar.evaluate(el=>Number(el.style.getPropertyValue('--p')))).toBeGreaterThan(0);
  const box=await bar.evaluate(el=>{
   const rect=el.getBoundingClientRect(),head=el.parentElement.getBoundingClientRect(),style=getComputedStyle(el,'::before');
   return {top:rect.top,bottom:rect.bottom,width:rect.width,headerBottom:head.bottom,transform:style.transform,background:style.backgroundColor};
  });
  expect(box.top).toBeGreaterThan(0);
  expect(Math.abs(box.bottom-box.headerBottom)).toBeLessThanOrEqual(1);
  expect(box.width).toBe(width);
  expect(box.background).not.toBe('rgba(0, 0, 0, 0)');
  expect(box.transform).not.toBe('matrix(0, 0, 0, 1, 0, 0)');
  await page.locator('.reading-nav a[href="#lecture-overview"]').click();
  await expect(bar).toBeVisible();
  await context.close();
 });
}

test('home opens with a daily key sentence that links to its lecture',async({page})=>{
  await page.goto('/index.html');
  const line=page.locator('.today-line');
  await expect(line).toBeVisible();
  const text=(await line.locator('blockquote').textContent()).trim();
  const href=await line.getAttribute('href');
  expect(await page.locator('#lecture-list .lecture[href="'+href+'"] .card-lead').textContent()).toBe(text);
  await line.click();
  await expect(page.locator('#lecture-overview .summary-lead')).toHaveText(text);
});

test('list markers sit on the first text line at every text size',async({browser})=>{
  for(const [width,size] of [[360,'lg'],[390,'md'],[1280,'sm']]){
    const context=await browser.newContext({viewport:{width,height:844}});
    await context.addInitScript(s=>{try{localStorage.setItem('study-site-text-size',s)}catch{}},size);
    const page=await context.newPage();
    for(const url of ['/lectures/ZCty0wvogDo.html','/lectures/sAgj5V4Ewno.html','/index.html']){
      await page.goto(url);
      const result=await page.evaluate(()=>{
        const off=[];
        for(const el of document.querySelectorAll('body *')){
          const cs=getComputedStyle(el,'::before');
          if(cs.content==='none'||cs.content==='normal'||cs.display==='none'||cs.position!=='absolute')continue;
          const h=parseFloat(cs.height),w=parseFloat(cs.width),top=parseFloat(cs.top);
          if(!(h>0&&h<40&&w>0&&w<40)||Number.isNaN(top))continue;
          const box=el.getBoundingClientRect();if(!box.height)continue;
          const m=cs.transform.match(/matrix\(([^)]+)\)/);const ty=m?Number(m[1].split(',')[5]):0;
          const walker=document.createTreeWalker(el,NodeFilter.SHOW_TEXT,{acceptNode:n=>n.textContent.trim()?1:3});
          const text=walker.nextNode();if(!text)continue;
          const range=document.createRange();range.setStart(text,0);range.setEnd(text,1);
          const line=range.getClientRects()[0];if(!line)continue;
          const d=box.top+top+ty+h/2-(line.top+line.bottom)/2;
          if(Math.abs(d)>3)off.push(el.parentElement.className+' '+Math.round(d));
        }
        const statics=[...document.querySelectorAll('#lecture-overview .summary-list li')]
          .map(li=>getComputedStyle(li,'::before').position).filter(p=>p!=='static');
        return {off,statics};
      });
      expect(result.off,url+' @'+width+'/'+size).toEqual([]);
      expect(result.statics,url).toEqual([]);
    }
    await context.close();
  }
});

test('outline sheet lists sections and detail headings and closes on navigation',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/lectures/sAgj5V4Ewno.html');
  await page.evaluate(()=>window.scrollTo({top:1400,behavior:'instant'}));
  const fab=page.locator('.outline-fab');
  await expect(fab).toHaveClass(/is-visible/);
  await fab.click();
  const sheet=page.locator('.outline-sheet');
  await expect(sheet).toBeVisible();
  expect(await sheet.locator('ol ol a').count()).toBe(await page.locator('.detail-toc a').count());
  await sheet.locator('ol ol a').first().click();
  await expect(sheet).toBeHidden();
  await expect(page).toHaveURL(/#detail-1$/);
  await context.close();
});

test('view settings change text size and keep it on this device only',async({page})=>{
  await page.goto('/lectures/sAgj5V4Ewno.html');
  const size=()=>page.locator('.detail-body p').first().evaluate(el=>parseFloat(getComputedStyle(el).fontSize));
  const base=await size();
  await page.locator('.view-settings>summary').click();
  await page.locator('.view-settings .text-size[data-text-size="lg"]').click();
  await expect(page.locator('.view-settings .text-size[data-text-size="lg"]')).toHaveAttribute('aria-pressed','true');
  expect(await size()).toBeGreaterThan(base);
  await page.reload();
  expect(await size()).toBeGreaterThan(base);
  await page.locator('.view-settings>summary').click();
  await page.locator('.view-settings .text-size[data-text-size="md"]').click();
  expect(await size()).toBe(base);
  expect(await page.evaluate(()=>localStorage.getItem('study-site-text-size'))).toBeNull();
});

test('section anchors sit flush under the reading nav and the current section follows',async({browser})=>{
  for(const width of [390,1280]){
    const context=await browser.newContext({viewport:{width,height:844},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto('/lectures/ZCty0wvogDo.html');
    const nav=page.getByRole('navigation',{name:'이 강의 목차'});
    for(const [id,name] of [['lecture-overview','핵심 요약'],['lecture-detail','상세 요약'],['lecture-comment','타임스탬프']]){
      await nav.getByRole('link',{name}).click();
      await page.waitForTimeout(150);
      const g=await page.evaluate(id=>({section:document.getElementById(id).getBoundingClientRect().top,nav:document.querySelector('.reading-nav').getBoundingClientRect().bottom,atBottom:innerHeight+scrollY>=document.documentElement.scrollHeight-2}),id);
      if(g.atBottom){
        // 페이지 끝 내용이 화면보다 짧아 섹션을 목차 아래에 맞출 수 없으면 페이지 끝에 닿고, 이때는 마지막 항목이 현재 위치이다.
        await expect(nav.getByRole('link',{name:'출처'})).toHaveAttribute('aria-current','location');
        expect(g.section).toBeGreaterThanOrEqual(g.nav-1);
      }else{
        await expect(nav.getByRole('link',{name})).toHaveAttribute('aria-current','location');
        // 섹션 위 선이 목차 아래 선과 겹친다. 두 선 사이 빈 띠가 없다.
        expect(Math.abs(g.section-(g.nav-1))).toBeLessThanOrEqual(2);
      }
    }
    await page.evaluate(()=>window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'}));
    await expect(nav.getByRole('link',{name:'출처'})).toHaveAttribute('aria-current','location');
    await context.close();
  }
});

test('outline button is opaque so body text never shows through it',async({page})=>{
  await page.setViewportSize({width:390,height:844});
  await page.goto('/lectures/sAgj5V4Ewno.html');
  const bg=await page.locator('.outline-fab').evaluate(el=>getComputedStyle(el).backgroundColor);
  const alpha=/rgba\([^)]*,\s*([\d.]+)\)/.exec(bg);
  expect(alpha?Number(alpha[1]):1).toBe(1);
});

test('outline sheet also changes text size and stays in sync with the footer settings',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/lectures/sAgj5V4Ewno.html');
  await page.evaluate(()=>window.scrollTo({top:1400,behavior:'instant'}));
  await page.locator('.outline-fab').click();
  const sheet=page.locator('.outline-sheet');
  await sheet.locator('.text-size[data-text-size="lg"]').click();
  await expect(page.locator('html')).toHaveAttribute('data-text-size','lg');
  await expect(page.locator('.site-footer .text-size[data-text-size="lg"]')).toHaveAttribute('aria-pressed','true');
  await expect(sheet).toBeVisible();
  await expect(page.locator('.site-header [data-theme-toggle]')).toHaveCount(0);
  await page.evaluate(()=>localStorage.removeItem('study-site-text-size'));
  await context.close();
});

test('intro section merges key points and practice and fits small screens',async({browser})=>{
  for(const width of [320,390,1280]){
    const context=await browser.newContext({viewport:{width,height:844},reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto('/lectures/chance-acceptance-20240526.html');
    await expect(page.locator('main .lecture-section').first().locator('h2')).toHaveText('핵심 요약');
    await expect(page.locator('#lecture-overview h3')).toHaveText(['우연을 받아들인다는 것','해볼 만한 일']);
    await expect(page.getByRole('navigation',{name:'이 강의 목차'}).getByRole('link',{name:'핵심 요약'})).toBeVisible();
    await expect(page.getByRole('navigation',{name:'이 강의 목차'}).getByRole('link',{name:'실천 포인트'})).toHaveCount(0);
    expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
    const m=await page.evaluate(()=>{
      const size=s=>parseFloat(getComputedStyle(document.querySelector(s)).fontSize);
      const card=document.querySelector('.practice-list>li').getBoundingClientRect();
      const dd=document.querySelector('.practice-cells dd').getBoundingClientRect();
      return {h1:size('h1'),h2:size('#lecture-overview>h2'),h3:size('#lecture-overview .intro-block>h3'),dd:size('.practice-cells dd'),
        ddInside:dd.left>=card.left&&dd.right<=card.right};
    });
    expect(m.h1).toBeGreaterThan(m.h2);expect(m.h2).toBeGreaterThan(m.h3);expect(m.dd).toBeLessThanOrEqual(16);expect(m.ddInside).toBe(true);
    await context.close();
  }
});

test('timestamp section is only the original text and the copy button',async({browser})=>{
  for(const width of [390,1100]){
    const context=await browser.newContext({viewport:{width,height:900},reducedMotion:'reduce'});
    await context.route(/youtube(-nocookie)?\.com/,route=>route.abort());
    const page=await context.newPage();
    for(const id of ['xA-4G4z-1MM','chance-acceptance-20240526','affirmation-20261101']){
      await page.goto('/lectures/'+id+'.html');
      const section=page.locator('#lecture-comment');
      await expect(section.locator('h2')).toHaveText('타임스탬프');
      await expect(section.locator('#copy')).toBeVisible();
      await expect(section.locator('#comment')).toHaveCount(1);
      // 영상 임베드와 구간 막대는 두지 않는다.
      for(const gone of ['.video-embed','.video-open','.time-map','iframe'])await expect(page.locator(gone)).toHaveCount(0);
      // 원문 박스는 제목·복사 버튼 아래에서 구간 전체 폭을 쓴다(그리드 자동 배치로 옆에 놓이거나 겹치지 않는다).
      const g=await page.evaluate(()=>{
        const r=s=>document.querySelector(s).getBoundingClientRect();
        const sec=r('#lecture-comment'),h2=r('#lecture-comment>h2'),btn=r('#copy'),box=r('#lecture-comment .timeline-box');
        return {boxTop:box.top,above:Math.max(h2.bottom,btn.bottom),boxWidth:box.width,secWidth:sec.width,boxLeft:box.left-sec.left};
      });
      expect(g.boxTop).toBeGreaterThanOrEqual(g.above);
      expect(g.boxWidth).toBeGreaterThanOrEqual(g.secWidth-2);
      expect(Math.abs(g.boxLeft)).toBeLessThanOrEqual(1);
    }
    await context.close();
  }
});

test('practice links open the video in a new tab at the quoted moment',async({page,context})=>{
  // 실제 유튜브로 나가지 않도록 빈 응답으로 바꿔 둔다(차단하면 팝업 주소가 오류 페이지로 바뀐다).
  await context.route(/youtube(-nocookie)?\.com/,route=>route.fulfill({status:200,contentType:'text/html',body:'<title>video</title>'}));
  await page.goto('/lectures/xA-4G4z-1MM.html');
  const links=page.locator('#lecture-overview .practice-source');
  const count=await links.count();
  expect(count).toBeGreaterThan(0);
  for(let i=0;i<count;i++){
    expect(await links.nth(i).getAttribute('target')).toBe('_blank');
    expect(await links.nth(i).getAttribute('rel')).toContain('noopener');
    expect(await links.nth(i).getAttribute('href')).toMatch(/[?&]t=\d+s$/);
  }
  const first=links.first();
  expect(await first.getAttribute('href')).toContain('&t=1473s');
  const [popup]=await Promise.all([context.waitForEvent('page'),first.click()]);
  expect(popup.url()).toContain('t=1473s');
  expect(page.url()).toContain('/lectures/xA-4G4z-1MM.html');   // 이 페이지는 그대로 남는다
  await expect(page.locator('iframe')).toHaveCount(0);
  await popup.close();
});

test('sources and editor notes share one closed disclosure at the page end',async({page})=>{
  await page.goto('/lectures/ZCty0wvogDo.html');
  const box=page.locator('main details.source-disclosure');
  await expect(box).toHaveCount(1);
  await expect(box.locator('>summary')).toHaveText('출처와 편집자 주');
  await expect(box).not.toHaveAttribute('open','');
  await expect(box.locator('h3')).toHaveText(['원본과 참고 자료','편집자 주']);
  await expect(page.locator('.pager-link.is-prev small')).toHaveText('← 최근 강의');
  await page.getByRole('navigation',{name:'이 강의 목차'}).getByRole('link',{name:'출처'}).click();
  await expect(box).toHaveAttribute('open','');
  // 편집자 주로 바로 가는 링크도 접힘을 연다.
  await page.goto('/lectures/ZCty0wvogDo.html#lecture-editor');
  await expect(page.locator('#lecture-sources')).toHaveAttribute('open','');
  await expect(page.locator('#lecture-editor>h3')).toBeVisible();
});

test('intro stays compact on a phone and every practice card puts the action first',async({browser})=>{
  test.setTimeout(90000);
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  let checked=0;
  for(const row of studyLectures){
    await page.goto('/lectures/'+row.id+'.html');
    if(!(await page.locator('#lecture-overview .intro-block').count()))continue;
    const m=await page.evaluate(()=>{
      const px=e=>e.getBoundingClientRect().height;
      const cell=n=>{const e=document.querySelector('.practice-cells>div:nth-child('+n+') dd');if(!e)return null;const st=getComputedStyle(e);return {size:parseFloat(st.fontSize),weight:Number(st.fontWeight)};};
      return {overview:px(document.querySelector('#lecture-overview')),cards:[...document.querySelectorAll('.practice-list>li')].map(px),when:cell(1),act:cell(2),overflow:document.documentElement.scrollWidth-innerWidth};
    });
    // 도입은 모바일에서 1.5화면 안(1,320px)에 들어야 하고, 해볼 일 카드 하나는 320px를 넘기지 않는다.
    expect(m.overview,row.id+' 도입 높이').toBeLessThanOrEqual(1320);
    for(const h of m.cards)expect(h,row.id+' 카드 높이').toBeLessThanOrEqual(320);
    // 위계: 할 일(둘째 칸)이 언제(첫째 칸)보다 크고 굵다.
    if(m.act){expect(m.act.size).toBeGreaterThan(m.when.size);expect(m.act.weight).toBeGreaterThanOrEqual(600);expect(m.when.weight).toBeLessThan(600);}
    expect(m.overflow).toBeLessThanOrEqual(1);
    checked++;
  }
  expect(checked).toBeGreaterThan(0);
  await context.close();
});

