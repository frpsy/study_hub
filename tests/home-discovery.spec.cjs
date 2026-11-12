const {test,expect}=require('@playwright/test');

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
    await page.locator('[data-filter-for="search"][data-value="명상"]').click();
    await expect(page.locator('#lecture-list .lecture:visible')).toHaveCount(2);
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
  expect((await ids())[0]).toBe('KHd-luu3M8s');
  await expect(page).toHaveURL(/[?&]sort=added/);
  await page.reload();  // The choice survives a reload.
  await expect(page.locator('[data-sort="added"]')).toHaveAttribute('aria-pressed','true');
  await page.locator('[data-sort="latest"]').click();
  expect(await ids()).toEqual(latest);
  await expect(page).not.toHaveURL(/sort=/);
});
