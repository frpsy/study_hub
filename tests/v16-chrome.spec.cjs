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
  await page.evaluate(()=>window.scrollTo({top:1700,behavior:'instant'}));
  await expect(page.locator('html')).toHaveClass(/header-hidden/);            // 내려 읽는 중에는 막대가 비켜 있다
  await expect.poll(()=>dock.evaluate(el=>getComputedStyle(el).opacity)).toBe('0');
  await page.evaluate(()=>window.scrollTo({top:1600,behavior:'instant'}));  // 위로 올리면 다시 보인다
  await expect(page.locator('html')).not.toHaveClass(/header-hidden/);
  await expect(dock).toHaveClass(/is-visible/);
  await expect.poll(()=>dock.evaluate(el=>getComputedStyle(el).opacity)).toBe('1');
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

// S5 대비: v16에서 새로 만든 면의 글자 대비를 라이트·다크에서 4.5:1 이상으로 지킨다. 반투명 면은 종이색 위에 합성해 잰다.
const parseColor=value=>{
  let m=/rgba?\(([^)]+)\)/.exec(value);
  if(m){const p=m[1].split(/[\s,/]+/).filter(Boolean).map(Number);return {r:p[0]/255,g:p[1]/255,b:p[2]/255,a:p.length>3?p[3]:1}}
  m=/color\(srgb\s+([^)]+)\)/.exec(value);
  if(m){const p=m[1].split(/[\s/]+/).filter(Boolean).map(Number);return {r:p[0],g:p[1],b:p[2],a:p.length>3?p[3]:1}}
  throw new Error('색을 읽지 못함: '+value);
};
const over=(top,bottom)=>({r:top.r*top.a+bottom.r*(1-top.a),g:top.g*top.a+bottom.g*(1-top.a),b:top.b*top.a+bottom.b*(1-top.a),a:1});
const lum=c=>[c.r,c.g,c.b].map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
const ratio=(fg,bg)=>{const a=lum(fg),b=lum(bg);return (Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
for(const theme of ['light','dark']){
  test(`v16 surfaces keep text contrast at 4.5:1 in ${theme}`,async({browser})=>{
    const context=await browser.newContext({viewport:{width:390,height:844},colorScheme:theme,reducedMotion:'reduce'});
    const page=await context.newPage();
    const pairs=[];
    const read=async(url,list,prep)=>{
      await page.goto(url);if(prep)await prep();
      pairs.push(...await page.evaluate(list=>{
        const b=getComputedStyle(document.body).backgroundColor,paper=/rgba\([^)]*,\s*0\)/.test(b)?getComputedStyle(document.documentElement).backgroundColor:b;
        return list.map(([name,fgSel,bgSel])=>{const fg=document.querySelector(fgSel),bg=document.querySelector(bgSel);
          return {name,fg:fg&&getComputedStyle(fg).color,bg:bg&&getComputedStyle(bg).backgroundColor,paper}})},list));
    };
    await read('/index.html',[
      ['today sentence','.bento .today-key','.bento .today-line'],['today source','.bento .today-source','.bento .today-line'],
      ['topic title','.bento-topic strong','.bento-topic'],['topic count','.bento-topic small','.bento-topic'],
      ['pick label','.bento-pick small','.bento-pick'],['pick title','.bento-pick strong','.bento-pick']]);
    await read('/lectures/QmOF0crdyRU.html',[
      ['key point','#lecture-overview .intro-points li','#lecture-overview .intro-points'],
      ['current tab','.reading-nav a[aria-current="location"]','.reading-nav a[aria-current="location"]'],
      ['dock label','.dock button','.dock']],async()=>{await page.evaluate(()=>scrollTo(0,10));await page.waitForTimeout(100)});
    await page.locator('.header-search').click();
    await page.locator('.search-sheet input').fill('도파민');
    await expect(page.locator('.search-sheet [role=option]').first()).toBeVisible();
    pairs.push(...await page.evaluate(()=>{const b=getComputedStyle(document.body).backgroundColor,paper=/rgba\([^)]*,\s*0\)/.test(b)?getComputedStyle(document.documentElement).backgroundColor:b;
      const sheet=getComputedStyle(document.querySelector('.search-sheet')).backgroundColor;
      const sel=document.querySelector('.search-sheet [aria-selected="true"] a');
      return [['result title',sel.querySelector('strong')],['result detail',sel.querySelector('span')],['result meta',sel.querySelector('small')]]
        .map(([name,el])=>({name,fg:getComputedStyle(el).color,bg:getComputedStyle(sel).backgroundColor,paper,under:sheet}))}));
    for(const p of pairs){
      expect(p.fg,`${p.name}: 요소 없음`).toBeTruthy();
      expect(parseColor(p.paper).a,`${p.name}: 종이색이 투명함`).toBe(1);
      let bg=over(parseColor(p.bg||'rgba(0,0,0,0)'),over(parseColor(p.under||'rgba(0,0,0,0)'),parseColor(p.paper)));
      const value=ratio(over(parseColor(p.fg),bg),bg);
      expect(value,`${theme}: ${p.name} ${p.fg} on ${p.bg}`).toBeGreaterThanOrEqual(4.5);
    }
    await context.close();
  });
}
