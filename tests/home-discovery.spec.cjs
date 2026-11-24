const {test,expect}=require('@playwright/test');
const studyLectures=require('../lectures.json');
const meditationCount=studyLectures.filter(x=>x.topic==='명상').length;
const latestAddedId=[...studyLectures].sort((a,b)=>Date.parse(b.added)-Date.parse(a.added))[0].id;

// Measures actual browser geometry before and after the catalog intro adjustment.
for(const viewport of [{width:390,height:844},{width:1280,height:800}]){
  test('home discovery paths and first-title visibility at '+viewport.width+'px',async({browser})=>{
    const context=await browser.newContext({viewport,reducedMotion:'reduce'});
    const page=await context.newPage();
    await page.goto('/index.html');
    const first=page.locator('#lecture-list .lecture').first();
    await expect(first).toBeVisible();
    const layout=await page.evaluate(()=>{
      const title=document.querySelector('#lecture-list .lecture h2').getBoundingClientRect();
      const search=document.querySelector('#search').getBoundingClientRect();
      const chips=document.querySelector('.filter-chips').getBoundingClientRect();
      const card=document.querySelector('#lecture-list .lecture').getBoundingClientRect();
      return {viewportHeight:innerHeight,searchTop:Math.round(search.top),
        firstCardTop:Math.round(card.top),firstTitleBottom:Math.round(title.bottom),
        scrollToSeeFirstTitle:Math.max(0,Math.ceil(title.bottom-innerHeight)),
        filterHeight:Math.round(chips.height),horizontalOverflow:document.documentElement.scrollWidth-innerWidth};
    });
    expect(layout.horizontalOverflow).toBeLessThanOrEqual(1);
    expect(layout.scrollToSeeFirstTitle,'first card title must appear above fold').toBe(0);
    if(viewport.width===390)expect(layout.filterHeight,'topic chips stay on one compact row').toBeLessThanOrEqual(48);
    if(process.env.STUDY_SCREENSHOT_DIR&&viewport.width===1280)await page.screenshot({path:require('node:path').join(process.env.STUDY_SCREENSHOT_DIR,'study-hub-home.png')});
    await first.click();  // No search: one card tap.
    await expect(page).toHaveURL(/\/lectures\/.*\.html$/);
    await page.goto('/index.html');
    await page.locator('[data-filter-for="topic"][data-value="명상"]').click();
    await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(meditationCount);
    await page.locator('#lecture-list .lecture:visible').first().click(); // Filter + card: two taps.
    await expect(page.locator('#lecture-overview')).toBeVisible();
    await page.goto('/index.html');
    await page.locator('#search').click();
    await page.locator('#search').fill('Huberman');
    await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(2);
    await page.locator('#lecture-list .lecture:visible').first().click(); // Search + card: two taps, typing excluded.
    await expect(page.locator('#lecture-detail')).toBeVisible();
    await expect(page.locator('.source-disclosure a[href^="https://"]').first()).toHaveAttribute('href',/^https:\/\//);
    console.log('HOME_DISCOVERY_METRICS '+JSON.stringify({viewport,...layout,taps:{first:1,filter:2,search:2}}));
    await context.close();
  });
}

test('home sort toggle orders by lecture date or by when it was added',async({page})=>{
  await page.goto('/index.html');
  const ids=()=>page.locator('#lecture-list .lecture').evaluateAll(cards=>cards.map(card=>card.dataset.videoId));
  const latest=await ids();
  const dates=await page.locator('#lecture-list .lecture').evaluateAll(cards=>cards.map(card=>card.dataset.date));
  expect(dates).toEqual([...dates].sort().reverse());
  await expect(page.locator('[data-sort="latest"]')).toHaveAttribute('aria-pressed','true');
  await page.locator('[data-sort="added"]').click();
  await expect(page.locator('[data-sort="added"]')).toHaveAttribute('aria-pressed','true');
  const added=await page.locator('#lecture-list .lecture').evaluateAll(cards=>cards.map(card=>Date.parse(card.dataset.added)));
  expect(added).toEqual([...added].sort((a,b)=>b-a));
  expect(await ids()).not.toEqual(latest);
  expect((await ids())[0]).toBe(latestAddedId);
  await expect(page).toHaveURL(/[?&]sort=added/);
  await page.reload();  // The choice survives a reload.
  await expect(page.locator('[data-sort="added"]')).toHaveAttribute('aria-pressed','true');
  await page.locator('[data-sort="latest"]').click();
  expect(await ids()).toEqual(latest);
  await expect(page).not.toHaveURL(/sort=/);
});

test('home sort toggle can order by YouTube view count and shows the count only then',async({page})=>{
  await page.goto('/index.html');
  const views=()=>page.locator('#lecture-list .lecture').evaluateAll(cards=>cards.map(card=>Number(card.dataset.views)));
  await expect(page.locator('#lecture-list .lecture .views').first()).toBeHidden();
  await expect(page.locator('#views-note')).toBeHidden();
  await page.locator('[data-sort="views"]').click();
  await expect(page.locator('[data-sort="views"]')).toHaveAttribute('aria-pressed','true');
  const counts=await views();
  expect(counts.length).toBeGreaterThan(1);
  expect(counts).toEqual([...counts].sort((a,b)=>b-a));
  await expect(page.locator('#lecture-list .lecture .views')).toHaveCount(0);
  await expect(page.locator('#views-note')).toBeVisible();
  await expect(page).toHaveURL(/[?&]sort=views/);
  await page.reload();
  await expect(page.locator('[data-sort="views"]')).toHaveAttribute('aria-pressed','true');
  await page.locator('[data-sort="latest"]').click();
  await expect(page.locator('#lecture-list .lecture .views').first()).toBeHidden();
  await expect(page.locator('#views-note')).toBeHidden();
});

test('sleep search aliases and independent empty-state resets',async({page})=>{
  await page.goto('/index.html');
  const search=page.locator('#search');
  await search.fill('불면증');
  await expect(page.locator('[data-video-id="VUHrJZbpIjI"]')).toBeVisible();
  await search.fill('잠이 안 와요');
  await expect(page.locator('[data-video-id="VUHrJZbpIjI"]')).toBeVisible();
  await page.locator('[data-value="명상"]').click();
  await expect(page.locator('#empty')).toBeVisible();
  await page.getByRole('button',{name:'주제 필터 해제'}).click();
  await expect(search).toHaveValue('잠이 안 와요');
  await expect(page.locator('[data-video-id="VUHrJZbpIjI"]')).toBeVisible();
  await page.locator('[data-value="명상"]').click();
  await page.getByRole('button',{name:'검색어 지우기'}).click();
  await expect(search).toBeEmpty();
  await expect(page.locator('#catalog-topic')).toHaveText('명상');
  await search.fill('잠');
  await page.getByRole('button',{name:'검색창 비우기'}).click();
  await expect(search).toBeEmpty();
});

test('random hero changes both the quote and its lecture destination',async({page})=>{
  await page.goto('/index.html');
  const quote=page.locator('.today-line .today-key');
  const original=await quote.textContent();
  await page.getByRole('button',{name:'다른 문장 보기'}).click();
  await expect(quote).not.toHaveText(original);
  const selected=await quote.textContent();
  await page.locator('.today-source').click();
  await expect(page).toHaveURL(/\/lectures\/[^/]+\.html$/);
  await expect(page.locator('#lecture-overview .intro-points li').first()).toContainText(selected);
});

test('bookmark filtering and read state survive navigation and reload',async({page})=>{
  await page.goto('/index.html');
  const card=page.locator('article[data-video-id="VUHrJZbpIjI"]');
  const bookmark=card.getByRole('button',{name:'북마크'});
  const read=card.getByRole('button',{name:'읽음 표시'});
  for(const button of [bookmark,read]){
    const bounds=await button.boundingBox();
    expect(bounds.width).toBeGreaterThanOrEqual(44);
    expect(bounds.height).toBeGreaterThanOrEqual(44);
  }
  await bookmark.click();
  await read.click();
  await expect(page).toHaveURL(/\/index\.html$/);
  await expect(card).toHaveClass(/is-read/);
  await page.locator('[data-bookmark-filter]').click();
  await expect(page.locator('#count')).toHaveText('1개 강의');
  await page.locator('[data-value=명상]').click();
  await expect(page.locator('#count')).toHaveText('0개 강의');
  await expect(page.locator('[data-bookmark-filter]')).toHaveAttribute('aria-pressed','true');
  await page.locator('[data-value=명상]').click();
  await page.reload();
  await expect(bookmark).toHaveAttribute('aria-pressed','true');
  await expect(read).toHaveAttribute('aria-pressed','true');
  await expect(read.locator('.read-mark')).toHaveCSS('background-color',await read.evaluate(el=>getComputedStyle(el).color));
  const meta=card.locator('.meta');
  await meta.scrollIntoViewIfNeeded();
  const box=await meta.boundingBox();
  await page.mouse.click(box.x+8,box.y+box.height/2);
  const detailRead=page.locator('.detail-read');
  await expect(detailRead).toHaveText('읽음 완료');
  await expect(detailRead).toHaveAttribute('aria-pressed','true');
  await detailRead.click();
  await expect(detailRead).toHaveText('읽음 표시');
  await page.goBack();
  await expect(read).toHaveAttribute('aria-pressed','false');
  await bookmark.click();
  await expect(page.locator('#count')).toHaveText('0개 강의');
  await expect(page.locator('#empty')).toBeVisible();
  await expect(page.locator('[data-empty-message]')).toHaveText('북마크한 강의가 없습니다.');
  await page.locator('[data-value="몸과 수면"]').click();
  await page.locator('#search').fill('불면증');
  await page.getByRole('button',{name:'전체 강의 보기'}).click();
  await expect(page.locator('#search')).toHaveValue('불면증');
  await expect(page.locator('[data-value="몸과 수면"]')).toHaveAttribute('aria-pressed','true');
  await expect(page.locator('[data-bookmark-filter]')).toHaveAttribute('aria-pressed','false');
  await expect(card).toBeVisible();
});

test('search finds secondary key points and opens the matching section',async({page})=>{
  await page.setViewportSize({width:320,height:760});
  await page.goto('/index.html');
  const search=page.locator('#search');
  const sleep=page.locator('[data-video-id="VUHrJZbpIjI"]');
  const voice=page.locator('[data-video-id="sAgj5V4Ewno"]');
  await search.fill('아데노신 수용체');
  await expect(sleep).toBeVisible();
  await expect(sleep.locator('.search-section-link:visible')).toHaveCount(0);
  await search.fill('핑크노이즈');
  const section=voice.getByRole('link',{name:/해당 부분 읽기/});
  await expect(section).toHaveText(/핑크 노이즈/);
  expect(await page.evaluate(()=>document.documentElement.scrollWidth-innerWidth)).toBeLessThanOrEqual(1);
  await page.getByRole('button',{name:'몸과 수면'}).click();
  await expect(voice).toBeHidden();
  await page.getByRole('button',{name:'명상'}).click();
  await expect(section).toBeVisible();
  await section.click();
  await expect(page).toHaveURL(/sAgj5V4Ewno\.html#detail-7$/);
  await expect(page.locator('#detail-7')).toHaveText('잠들 때 핑크 노이즈는 어떻게 쓰는가');
  await page.goBack();
  await expect(search).toHaveValue('핑크노이즈');
  await expect(section).toBeVisible();
  await search.clear();
  await expect(section).toHaveCount(0);
});
