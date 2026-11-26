// v16 S2: 글래스 조작부·하단 막대·명령 팔레트 검색 (docs/design-overhaul-plan-2026-11-26.md 5절 공통 접근성 조건)
const {test,expect}=require('@playwright/test');
const index=require('../search-index.json');

test('slash opens search, keyboard picks a result, Escape returns focus',async({page})=>{
  await page.goto('/lectures/QmOF0crdyRU.html');
  const brand=page.locator('.site-brand');await brand.focus();
  await page.keyboard.press('/');
  const sheet=page.locator('.search-sheet');
  await expect(sheet).toBeVisible();
  await expect(sheet.getByRole('combobox',{name:'검색어'})).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(sheet).toBeHidden();
  await expect(brand).toBeFocused();
  await page.keyboard.press('Control+k');
  await expect(sheet).toBeVisible();
  await page.keyboard.type('목소리');
  const first=sheet.getByRole('option').first();
  await expect(first).toHaveAttribute('aria-selected','true');
  await expect(first).toContainText('목소리');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/lectures\/sAgj5V4Ewno\.html/);
});

test('a detail heading match opens that heading anchor',async({page})=>{
  const row=index.find(r=>r.s.some(h=>h.length>=6));
  const at=row.s.findIndex(h=>h.length>=6);
  await page.goto('/index.html');
  await page.locator('.header-search').click();
  await page.locator('.search-sheet input').fill(row.s[at]);
  const link=page.locator('.search-sheet [role=option] a').first();
  await expect(link).toHaveAttribute('href',new RegExp(`lectures/${row.id}\\.html#detail-${at+1}$`));
  await link.click();
  await expect(page.locator(`#detail-${at+1}`)).toHaveText(row.s[at]);
});

test('header search and dock buttons are named, reachable and work',async({browser})=>{
  const context=await browser.newContext({viewport:{width:390,height:844},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto('/lectures/sAgj5V4Ewno.html');
  await expect(page.getByRole('button',{name:'검색'}).first()).toBeVisible();
  const dock=page.getByRole('navigation',{name:'빠른 이동'});
  await expect(dock).not.toHaveClass(/is-visible/);
  await page.evaluate(()=>window.scrollTo({top:1600,behavior:'instant'}));
  await expect(dock).toHaveClass(/is-visible/);
  for(const name of ['목차','검색','보기','맨 위']){
    const b=dock.getByRole('button',{name});
    await expect(b).toBeVisible();
    const box=await b.boundingBox();
    expect(box.height,name).toBeGreaterThanOrEqual(44);expect(box.width,name).toBeGreaterThanOrEqual(44);
  }
  await dock.getByRole('button',{name:'보기'}).click();
  await expect(page.locator('#appearance-panel')).toBeVisible();
  await page.keyboard.press('Escape');
  await dock.getByRole('button',{name:'검색'}).click();
  await expect(page.locator('.search-sheet')).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(dock.getByRole('button',{name:'검색'})).toBeFocused();
  await dock.getByRole('button',{name:'맨 위'}).click();
  await expect.poll(()=>page.evaluate(()=>scrollY)).toBe(0);
  await context.close();
});

test('search says it is offline when the index cannot load',async({browser})=>{
  const context=await browser.newContext({serviceWorkers:'block'});
  const page=await context.newPage();
  await page.goto('/index.html');
  await page.route('**/search-index.json*',route=>route.abort('internetdisconnected'));
  await page.locator('.header-search').click();            // search.js는 온라인에서 불러온다
  await expect(page.locator('.search-sheet [role=status]')).toContainText('불러오지 못했습니다');
  await page.keyboard.press('Escape');
  await context.setOffline(true);
  await page.locator('.header-search').click();            // 다시 열면 색인을 다시 시도한다
  await expect(page.locator('.search-sheet [role=status]')).toContainText('오프라인');
  await context.close();
});

test('service worker keeps search usable offline after the first visit',async({browser,browserName})=>{
  test.skip(browserName!=='chromium','서비스 워커 오프라인 시나리오는 Chromium에서 본다');
  const context=await browser.newContext({serviceWorkers:'allow'});
  const page=await context.newPage();
  await page.goto('/index.html');
  await page.evaluate(()=>navigator.serviceWorker.ready);
  await expect.poll(()=>page.evaluate(async()=>{const keys=await caches.keys();for(const k of keys){const c=await caches.open(k);const urls=(await c.keys()).map(r=>r.url);if(urls.some(u=>u.endsWith('/search-index.json'))&&urls.some(u=>/assets\/search\.js\?v=/.test(u)))return true}return false}),{timeout:15000}).toBe(true);
  await page.reload();
  await context.setOffline(true);
  await page.locator('.header-search').click();
  await page.locator('.search-sheet input').fill('도파민');
  await expect(page.locator('.search-sheet [role=option]').first()).toContainText('도파민');
  await context.close();
});
