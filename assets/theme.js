/* Apply saved appearance before CSS paints. No account or learning data is stored. */
(()=>{
  'use strict';
  const key='study-site-appearance';
  if(navigator.standalone === true || window.matchMedia('(display-mode: standalone)').matches)document.documentElement.dataset.standalone='true';
  const media=window.matchMedia('(prefers-color-scheme: dark)');
  const modes=['auto','light','dark'];
  let choice='auto';
  try{const stored=localStorage.getItem(key);if(modes.includes(stored))choice=stored}catch{}
  const active=()=>choice==='auto'?(media.matches?'dark':'light'):choice;
  const labels={auto:'시스템',light:'라이트',dark:'다크'};
  const apply=()=>{
    const theme=active();
    document.documentElement.dataset.theme=theme;
    document.documentElement.dataset.themeMode=choice;
    document.documentElement.style.colorScheme=theme;
    const bar=document.querySelector('meta[name="theme-color"]');
    if(bar)bar.content=theme==='dark'?'#0b0b0c':'#ffffff';
    const button=document.querySelector('[data-theme-toggle]');
    if(button){
      const next=modes[(modes.indexOf(choice)+1)%modes.length];
      button.textContent='화면 · '+labels[choice];
      button.setAttribute('aria-label','화면 테마: '+labels[choice]+'. 누르면 '+labels[next]+' 모드');
      button.title='화면 테마: '+labels[choice];
    }
  };
  const accentKey='study-site-accent';
  const accents=['red','blue','green'];
  let accent='red';
  try{const stored=localStorage.getItem(accentKey);if(accents.includes(stored))accent=stored}catch{}
  const applyAccent=()=>{
    if(accent==='red')delete document.documentElement.dataset.accent;else document.documentElement.dataset.accent=accent;
    document.querySelectorAll('.accent-swatch[data-accent]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.accent===accent)));
  };
  // 글자 크기: 긴 글을 읽는 보기 설정. 이 기기에만 저장한다.
  const sizeKey='study-site-text-size';
  const sizes=['sm','md','lg'];
  let size='md';
  try{const stored=localStorage.getItem(sizeKey);if(sizes.includes(stored))size=stored}catch{}
  const applySize=()=>{
    if(size==='md')delete document.documentElement.dataset.textSize;else document.documentElement.dataset.textSize=size;
    document.querySelectorAll('.text-size[data-text-size]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.textSize===size)));
  };
  applyAccent();
  applySize();
  apply();
  const initialize=()=>{
    apply();
    applyAccent();
    applySize();
    document.querySelectorAll('.text-size').forEach(b=>b.addEventListener('click',()=>{
      size=b.dataset.textSize;
      try{if(size==='md')localStorage.removeItem(sizeKey);else localStorage.setItem(sizeKey,size)}catch{}
      applySize();
    }));
    document.querySelectorAll('.accent-swatch').forEach(b=>b.addEventListener('click',()=>{
      accent=b.dataset.accent;
      try{if(accent==='red')localStorage.removeItem(accentKey);else localStorage.setItem(accentKey,accent)}catch{}
      applyAccent();
    }));
    const button=document.querySelector('[data-theme-toggle]');
    button?.addEventListener('click',()=>{
      choice=modes[(modes.indexOf(choice)+1)%modes.length];
      try{if(choice==='auto')localStorage.removeItem(key);else localStorage.setItem(key,choice)}catch{}
      apply();
    });
  };
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',initialize,{once:true});
  else initialize();
  const systemChange=()=>{if(choice==='auto')apply()};
  if(media.addEventListener)media.addEventListener('change',systemChange);
  else if(media.addListener)media.addListener(systemChange);
})();
