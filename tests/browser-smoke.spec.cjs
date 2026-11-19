const {test,expect}=require('@playwright/test');
const studyVersion=require('../build-info.json').version;
const studyLectures=require('../lectures.json');
const studyMaterials=require('../materials.json');
const expectedLibraryCount=studyLectures.length+studyMaterials.length;
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
  await expect(page.locator('#count')).toHaveText('4개 강의');
  await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(4);
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

test('a lecture card opens a page with the key summary, practice points and timestamps',async({page})=>{
  await page.goto('/index.html');
  await page.locator('#lecture-list [data-video-id="affirmation-20261101"]').click();
  await expect(page).toHaveURL(/\/lectures\/affirmation-20261101\.html$/);
  await expect(page.locator('main .lecture-section')).toHaveCount(3);
  await expect(page.locator('#lecture-overview>h2')).toHaveText('핵심 요약');
  await expect(page.locator('#lecture-practice>h2')).toHaveText('실천 포인트');
  await expect(page.locator('#lecture-practice .summary-list li')).toHaveCount(3);
  await expect(page.locator('#lecture-practice details')).toHaveCount(4);
  const firstStep=page.locator('#lecture-practice details').first();
  await expect(firstStep.locator('ul')).toBeHidden();
  await firstStep.locator('summary').click();
  await expect(firstStep.locator('ul')).toBeVisible();
  await expect(page.locator('#lecture-comment>h2')).toHaveText('타임스탬프');
  for(const removed of ['5분 요약','미니강좌','용어와 개념']){
    await expect(page.getByText(removed)).toHaveCount(0);
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
    await expect(page.locator('#lecture-overview .summary-tier>h3')).toHaveText('핵심 세 가지');
    await expect(page.locator('#lecture-overview .summary-list li')).toHaveCount(3);
    const m=await page.evaluate(()=>{
      const size=selector=>parseFloat(getComputedStyle(document.querySelector(selector)).fontSize);
      const box=document.querySelector('.compact-lecture').getBoundingClientRect();
      return {h1:size('h1'),h2:size('#lecture-overview>h2'),h3:size('#lecture-overview .summary-tier>h3'),
        lead:size('#lecture-overview .summary-tier>.summary-lead'),list:size('#lecture-overview .summary-list li'),
        width:box.width,left:box.left,right:box.right,brand:document.querySelector('.site-brand').getBoundingClientRect().left,
        overflow:document.documentElement.scrollWidth-window.innerWidth};
    });
    expect(m.h1).toBeGreaterThan(m.h2);
    expect(m.h2).toBeGreaterThan(m.h3);
    expect(m.h3).toBeGreaterThanOrEqual(m.list);
    expect(m.list).toBeLessThanOrEqual(16);
    expect(m.lead).toBeLessThanOrEqual(17);
    expect(m.width).toBeLessThanOrEqual(width<=780 ? width-24 : 761);
    expect(m.left).toBeGreaterThanOrEqual(width<=780 ? 12 : -1);
    expect(Math.abs(m.left-m.brand)).toBeLessThanOrEqual(1);
    expect(m.overflow).toBeLessThanOrEqual(1);
    await context.close();
  }
});

test('every lecture offers practice and valid source navigation',async({page})=>{
  test.setTimeout(90000);
  for(const row of studyLectures){
    await page.goto('/lectures/'+row.id+'.html');
    await expect(page.locator('#lecture-practice .summary-list li')).toHaveCount(3);
    const steps=page.locator('#lecture-practice details');
    expect(await steps.count()).toBeGreaterThanOrEqual(3);
    await steps.first().locator('summary').click();
    const source=steps.first().locator('.practice-source');
    await expect(source).toBeVisible();
    if(row.creator==='김주환'){
      const expectedVideo=row.video_url||'https://www.youtube.com/watch?v='+row.id;
      const href=await source.getAttribute('href');
      expect(href).toContain(expectedVideo+'&t=');
      expect(href).toMatch(/&t=\d+s$/);
    }else{
      const hash=await source.getAttribute('href');
      await source.click();
      await expect(page.locator(hash)).toBeVisible();
      expect(await page.locator(hash).evaluate(el=>el.getBoundingClientRect().top)).toBeGreaterThan(100);
    }
  }
});

test('reading navigation and disclosures work on small screens without scripts',async({browser})=>{
  const context=await browser.newContext({viewport:{width:320,height:760},javaScriptEnabled:false,reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/lectures/izYj8g-j00U.html');
  await page.getByRole('navigation',{name:'이 강의 목차'}).getByRole('link',{name:'실천 포인트'}).click();
  await expect(page).toHaveURL(/#lecture-practice$/);
  const summary=page.locator('#lecture-practice summary').first();
  await summary.focus();
  await page.keyboard.press('Enter');
  await expect(page.locator('#lecture-practice details').first()).toHaveAttribute('open','');
  await expect(page.locator('#lecture-practice details').first().locator('.practice-source')).toBeVisible();
  expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  await context.close();
});

test('reading navigation tracks sections and source disclosure opens',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/lectures/izYj8g-j00U.html');
  if(process.env.STUDY_SCREENSHOT_DIR)await page.screenshot({path:require('node:path').join(process.env.STUDY_SCREENSHOT_DIR,'study-hub-mobile.png')});
  const nav=page.getByRole('navigation',{name:'이 강의 목차'});
  await nav.getByRole('link',{name:'실천 포인트'}).click();
  await expect(nav.getByRole('link',{name:'실천 포인트'})).toHaveAttribute('aria-current','location');
  const geometry=await page.evaluate(()=>({heading:document.querySelector('#lecture-practice>h2').getBoundingClientRect().top,nav:document.querySelector('.reading-nav').getBoundingClientRect().bottom}));
  expect(geometry.heading).toBeGreaterThanOrEqual(geometry.nav);
  if(process.env.STUDY_SCREENSHOT_DIR){
    await page.locator('#lecture-practice summary').first().click();
    await page.screenshot({path:require('node:path').join(process.env.STUDY_SCREENSHOT_DIR,'study-hub-practice.png')});
  }
  await nav.getByRole('link',{name:'참고 자료'}).click();
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
  await expect(bar).toBeVisible();
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
  await page.locator('.reading-nav a[href="#lecture-practice"]').click();
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

test('time map places chapters and key sessions on the lecture length above the original text',async({page})=>{
  await page.goto('/lectures/izYj8g-j00U.html');
  const map=page.locator('#lecture-comment .time-map');
  await expect(map).toBeVisible();
  expect(await map.locator('rect.mark').count()).toBeGreaterThanOrEqual(2);
  expect(await map.locator('rect.seg').count()).toBeGreaterThanOrEqual(2);
  const order=await page.evaluate(()=>document.querySelector('.time-map').getBoundingClientRect().bottom<=document.querySelector('#comment').getBoundingClientRect().top);
  expect(order).toBe(true);
});

test('time map and practice links play the lecture inside the page from that time',async({page})=>{
  await page.route(/youtube(-nocookie)?\.com/,route=>route.abort());
  await page.goto('/lectures/xA-4G4z-1MM.html');
  await expect(page.locator('.video-embed iframe')).toHaveCount(0);
  const mark=page.locator('#lecture-comment .time-map a').nth(1);
  const href=await mark.getAttribute('href');
  const start=/[?&]t=(\d+)s/.exec(href)[1];
  await mark.click();
  const frame=page.locator('.video-embed iframe');
  await expect(frame).toHaveCount(1);
  expect(await frame.getAttribute('src')).toContain('embed/xA-4G4z-1MM?start='+start+'&');
  expect(page.context().pages().length).toBe(1);
  const practice=page.locator('#lecture-practice details').first();
  await practice.locator('summary').click();
  await practice.locator('.practice-source').click();
  expect(await frame.getAttribute('src')).toContain('start=1889&');
  await expect(page.locator('.video-embed iframe')).toHaveCount(1);
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
        const statics=[...document.querySelectorAll('#lecture-overview .summary-list li,#lecture-practice .summary-tier:first-of-type .summary-list li')]
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
    for(const [id,name] of [['lecture-practice','실천 포인트'],['lecture-detail','상세 요약'],['lecture-comment','타임스탬프']]){
      await nav.getByRole('link',{name}).click();
      await expect(nav.getByRole('link',{name})).toHaveAttribute('aria-current','location');
      const g=await page.evaluate(id=>({section:document.getElementById(id).getBoundingClientRect().top,nav:document.querySelector('.reading-nav').getBoundingClientRect().bottom}),id);
      // 섹션 위 선이 목차 아래 선과 겹친다. 두 선 사이 빈 띠가 없다.
      expect(Math.abs(g.section-(g.nav-1))).toBeLessThanOrEqual(2);
    }
    await page.evaluate(()=>window.scrollTo({top:document.documentElement.scrollHeight,behavior:'instant'}));
    await expect(nav.getByRole('link',{name:'참고 자료'})).toHaveAttribute('aria-current','location');
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
