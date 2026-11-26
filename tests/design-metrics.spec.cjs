// 디자인 개편 v16 측정 기준선 (docs/design-overhaul-plan-2026-11-26.md 6절).
// - 목표값(TARGETS)은 단계가 끝날 때 enforce를 true로 바꿔 강제한다. 그 전에는 값만 기록한다.
// - 가로 넘침·레이아웃 이동처럼 지금도 지켜지는 계약은 처음부터 검사한다.
// - 측정 결과는 콘솔의 DESIGN_METRICS 줄과 test-results/design-metrics/*.json에 남는다.
const {test,expect}=require('@playwright/test');
const fs=require('node:fs');
const path=require('node:path');

const ROOT=path.resolve(__dirname,'..');
const lectures=require('../lectures.json');
const FIXTURES=['QmOF0crdyRU','MdDj5RZkMB4']; // 대표 이미지 있는 강의, 상세 요약이 가장 긴 강의
const PAGES=[{name:'home',url:'/index.html'},...FIXTURES.map(id=>({name:id,url:`/lectures/${id}.html`}))];
const FOLD={width:390,height:844};

const TARGETS={
  homeDestinationsAboveFold:{min:6,enforce:false,stage:'S3'},
  homeTodayLineAboveFold:{enforce:true,stage:'S0.5'},           // 지금도 지켜진다
  lectureFirstPointAboveFold:{enforce:false,stage:'S4'},
  siteJsBytes:{max:29254,enforce:true,stage:'S0.5'},           // 원본 바이트, 최소화 안 함
  searchIndexBytes:{max:50*1024,enforce:false,stage:'S2b'},
  precacheGrowth:{maxRatio:1.10,enforce:false,stage:'S2b'},     // S0.5 기록값 대비
  // 홈은 오늘의 한 문장을 스크립트가 바꾸며 0.0385가 난다. S3 벤토 타일에서 고치고 homeMax를 0.01로 내린다.
  layoutShift:{max:0.01,homeMax:0.1,stage:'S3에서 homeMax 0.01'}
};
// S0.5에서 잰 사전 캐시 총량(바이트). 기준을 다시 잡을 때만 고친다.
const PRECACHE_BASELINE_BYTES=1808331;

function record(name,data){
  const dir=path.join(ROOT,'test-results','design-metrics');
  fs.mkdirSync(dir,{recursive:true});
  fs.writeFileSync(path.join(dir,name+'.json'),JSON.stringify(data,null,2));
  console.log('DESIGN_METRICS '+name+' '+JSON.stringify(data));
}
async function freshPage(browser,{viewport=FOLD,theme='light',size='md'}={}){
  const context=await browser.newContext({viewport,reducedMotion:'reduce',colorScheme:theme});
  await context.addInitScript(([theme,size])=>{
    try{localStorage.setItem('study-site-appearance',theme);localStorage.setItem('study-site-text-size',size);}catch{}
  },[theme,size]);
  return {context,page:await context.newPage()};
}
const overflow=page=>page.evaluate(()=>document.documentElement.scrollWidth-innerWidth);

test('first screen at 390x844: home destinations and lecture first point',async({browser})=>{
  const {context,page}=await freshPage(browser);
  await page.goto('/index.html');
  await expect(page.locator('#lecture-list .lecture').first()).toBeVisible();
  const home=await page.evaluate(()=>{
    const inFold=el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&r.top>=0&&r.bottom<=innerHeight;};
    const links=[...document.querySelectorAll('main a[href]')]
      .filter(a=>!a.getAttribute('href').startsWith('#')&&inFold(a));
    const today=document.querySelector('.today-line, [data-today-line]');
    return {
      destinationsAboveFold:new Set(links.map(a=>a.href)).size,
      topicFiltersAboveFold:[...document.querySelectorAll('main [data-filter-for]')].filter(inFold).length,
      todayLineBottom:today?Math.round(today.getBoundingClientRect().bottom):null,
      firstCardTitleBottom:Math.round(document.querySelector('#lecture-list .lecture h2').getBoundingClientRect().bottom)
    };
  });
  const lecture={};
  for(const id of FIXTURES){
    await page.goto(`/lectures/${id}.html`);
    lecture[id]=await page.evaluate(()=>{
      const first=document.querySelector('#lecture-overview li, #lecture-overview p');
      const hero=document.querySelector('.lecture-hero');
      return {
        firstPointBottom:first?Math.round(first.getBoundingClientRect().bottom):null,
        heroHeight:hero?Math.round(hero.getBoundingClientRect().height):0
      };
    });
  }
  record('first-screen',{viewport:FOLD,home,lecture,targets:TARGETS});
  if(TARGETS.homeTodayLineAboveFold.enforce)expect(home.todayLineBottom).toBeLessThanOrEqual(FOLD.height);
  if(TARGETS.homeDestinationsAboveFold.enforce)expect(home.destinationsAboveFold).toBeGreaterThanOrEqual(TARGETS.homeDestinationsAboveFold.min);
  if(TARGETS.lectureFirstPointAboveFold.enforce)for(const id of FIXTURES)expect(lecture[id].firstPointBottom,id).toBeLessThanOrEqual(FOLD.height);
  await context.close();
});

for(const {name,url} of PAGES){
  test(`layout shift stays near zero after load: ${name}`,async({browser,browserName})=>{
    test.skip(browserName!=='chromium','layout-shift 항목은 Chromium만 지원한다');
    test.setTimeout(60000);
    const {context,page}=await freshPage(browser);
    // CPU 4배 감속: 첫 그림이 스크립트보다 먼저 나오는 느린 기기를 흉내 내 결과를 매번 같게 만든다.
    const cdp=await context.newCDPSession(page);
    await cdp.send('Emulation.setCPUThrottlingRate',{rate:4});
    await page.addInitScript(()=>{
      window.__cls=0;
      new PerformanceObserver(list=>{for(const e of list.getEntries())if(!e.hadRecentInput)window.__cls+=e.value;})
        .observe({type:'layout-shift',buffered:true});
    });
    await page.goto(url,{waitUntil:'load'});
    await page.waitForTimeout(3000);
    const value=Number((await page.evaluate(()=>window.__cls)).toFixed(4));
    record(`layout-shift-${name}`,{cls:value});
    expect(value,name).toBeLessThan(TARGETS.layoutShift[name==='home'?'homeMax':'max']);
    await context.close();
  });
}

test('asset and precache size budget',async()=>{
  const size=p=>fs.existsSync(path.join(ROOT,p))?fs.statSync(path.join(ROOT,p)).size:0;
  const core=['index.html','offline.html','manifest.webmanifest','assets/icon.svg','assets/icon-512.png',
    'assets/apple-touch-icon.png','assets/site.css','assets/site.js','assets/theme.js','lectures.json'];
  const pages=lectures.map(l=>`lectures/${l.id}.html`);
  const images=lectures.filter(l=>l.image&&/^assets\/lectures\/[\w-]+\.jpg$/.test(l.image.src)).map(l=>l.image.src);
  const searchIndex=fs.existsSync(path.join(ROOT,'search-index.json'))?size('search-index.json'):null;
  const data={
    siteJsBytes:size('assets/site.js'),siteCssBytes:size('assets/site.css'),
    searchIndexBytes:searchIndex,
    precacheBytes:[...core,...pages,...images].reduce((sum,p)=>sum+size(p),0),
    precacheFiles:core.length+pages.length+images.length
  };
  record('size',data);
  if(TARGETS.siteJsBytes.enforce)expect(data.siteJsBytes).toBeLessThanOrEqual(TARGETS.siteJsBytes.max);
  if(TARGETS.searchIndexBytes.enforce&&searchIndex!==null)expect(searchIndex).toBeLessThanOrEqual(TARGETS.searchIndexBytes.max);
  if(TARGETS.precacheGrowth.enforce&&PRECACHE_BASELINE_BYTES)
    expect(data.precacheBytes).toBeLessThanOrEqual(Math.round(PRECACHE_BASELINE_BYTES*TARGETS.precacheGrowth.maxRatio));
});

// 분기점(360·390·768·780·1024px) 앞뒤 1px과 대표 폭, 가로 모드, 200% 확대 상당(640px).
const WIDTHS=[359,360,361,389,390,391,767,768,769,779,780,781,1023,1024,1025,1280];
for(const {name,url} of PAGES){
  test(`no horizontal overflow across widths: ${name}`,async({browser})=>{
    const {context,page}=await freshPage(browser);
    await page.goto(url);
    const result={};
    for(const width of WIDTHS){
      await page.setViewportSize({width,height:844});
      result[width]=await overflow(page);
    }
    await page.setViewportSize({width:844,height:390}); result['844x390']=await overflow(page);
    await page.setViewportSize({width:640,height:450}); result['zoom200']=await overflow(page);
    record(`overflow-${name}`,result);
    for(const [key,value] of Object.entries(result))expect(value,`${name} @ ${key}`).toBeLessThanOrEqual(1);
    await context.close();
  });

  test(`no horizontal overflow across text sizes and themes: ${name}`,async({browser})=>{
    test.setTimeout(90000);
    const result={};
    for(const width of [360,1280])for(const theme of ['light','dark'])for(const size of ['sm','md','lg']){
      const {context,page}=await freshPage(browser,{viewport:{width,height:844},theme,size});
      await page.goto(url);
      result[`${width}-${theme}-${size}`]=await overflow(page);
      await context.close();
    }
    record(`overflow-settings-${name}`,result);
    for(const [key,value] of Object.entries(result))expect(value,`${name} @ ${key}`).toBeLessThanOrEqual(1);
  });
}
