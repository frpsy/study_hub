/* The inline head script applies stored appearance before styles load. */
(()=>{
  'use strict';
  const root=document.documentElement;
  const media=matchMedia('(prefers-color-scheme: dark)');
  const controls=[
    {selector:'[data-theme-choice]', field:'themeMode', option:'themeChoice', key:'study-site-appearance', fallback:'auto'},
    {selector:'.text-size', field:'textSize', option:'textSize', key:'study-site-text-size', fallback:'md'}
  ];
  const apply=()=>{
    const mode=root.dataset.themeMode||'auto';
    const theme=mode==='auto'?(media.matches?'dark':'light'):mode;
    root.dataset.theme=theme;
    root.style.colorScheme=theme;
    const bar=document.querySelector('meta[name="theme-color"]');
    if(bar)bar.content=theme==='dark'?'#121417':'#faf9f6';
    for(const {selector,field,option,fallback} of controls){
      const value=root.dataset[field]||fallback;
      document.querySelectorAll(selector).forEach(button=>button.setAttribute('aria-pressed',String(button.dataset[option]===value)));
    }
  };
  const settings=document.querySelector('.header-settings');
  if(settings){
    const toggle=settings.querySelector('.appearance-toggle');
    const panel=settings.querySelector('#appearance-panel');
    const setOpen=open=>{
      panel.hidden=!open;
      toggle.setAttribute('aria-expanded',String(open));
    };
    toggle.addEventListener('click',()=>setOpen(panel.hidden));
    document.addEventListener('click',event=>{
      if(!settings.contains(event.target))setOpen(false);
    });
    document.addEventListener('keydown',event=>{
      if(event.key==='Escape'&&!panel.hidden){
        setOpen(false);
        toggle.focus();
      }
    });
    for(const {selector,field,option,key,fallback} of controls){
      settings.querySelectorAll(selector).forEach(button=>button.addEventListener('click',()=>{
        const value=button.dataset[option];
        if(value===fallback)delete root.dataset[field];else root.dataset[field]=value;
        if(field==='themeMode')root.dataset.themeMode=value;
        try{if(value===fallback)localStorage.removeItem(key);else localStorage.setItem(key,value)}catch{}
        apply();
      }));
    }
  }
  const restore=()=>{
    for(const {selector,field,option,key,fallback} of controls){
      try{
        const value=localStorage.getItem(key)||fallback;
        if([...document.querySelectorAll(selector)].some(button=>button.dataset[option]===value)){
          if(value===fallback&&field!=='themeMode')delete root.dataset[field];else root.dataset[field]=value;
        }
      }catch{}
    }
    apply();
  };
  addEventListener('pageshow',restore);
  addEventListener('storage',event=>{
    if(event.key===null||controls.some(control=>control.key===event.key))restore();
  });
  if(media.addEventListener)media.addEventListener('change',apply);
  else media.addListener(apply);
  apply();
})();
