const {defineConfig}=require('@playwright/test');
const crypto=require('node:crypto');
// 포트는 worktree마다 다르게 정한다(CI는 8765 고정). 고정 포트를 여러 세션이 나눠 쓰면
// 다른 브랜치의 서버를 그대로 재사용해 엉뚱한 내용으로 검사하게 된다. PW_PORT로 직접 지정할 수도 있다.
const root=require('node:path').resolve(__dirname,'..');
const PORT=Number(process.env.PW_PORT)||(process.env.CI?8765:20000+parseInt(crypto.createHash('sha1').update(root).digest('hex').slice(0,6),16)%20000);
module.exports=defineConfig({
  testDir:'.',
  testMatch:['browser-smoke.spec.cjs','pwa.spec.cjs','home-discovery.spec.cjs'],
  timeout:30000,
  retries:1,
  // 테스트는 서로 독립이다(각자 새 브라우저 컨텍스트). 파일 안에서도 병렬로 돌려 시간을 줄인다.
  fullyParallel:true,
  workers:process.env.PW_WORKERS?Number(process.env.PW_WORKERS):4,
  reporter:'list',
  use:{
    baseURL:`http://127.0.0.1:${PORT}`,
    browserName:process.env.BROWSER_NAME||'chromium',
    screenshot:'only-on-failure',
    trace:'retain-on-failure'
  },
  webServer:{
    command:`python3 -m http.server ${PORT} --bind 127.0.0.1`,
    cwd:root,
    url:`http://127.0.0.1:${PORT}`,
    reuseExistingServer:false, // 이미 떠 있는 서버가 있으면 실패해서 알린다(남의 서버로 검사하지 않는다)
    timeout:30000
  }
});
