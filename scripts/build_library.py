# -*- coding: utf-8 -*-
"""Build the lecture list from the registry: python scripts/build_library.py"""
from pathlib import Path
import json,html,sys
from reading_text import reading_minutes, section_text
R=Path(__file__).resolve().parents[1]
SITE_NAME='내면의 서재'
SITE_DESCRIPTION='강의별 핵심 요약과 타임스탬프·상세 요약을 모은 서재'
SITE_URL='https://frpsy.github.io/study_hub/'
ASSET_VERSION=json.loads((R/'build-info.json').read_text(encoding='utf-8'))['version']
APPEARANCE_BOOT = """<script>(()=>{const root=document.documentElement;let mode='auto',size='';try{mode=localStorage.getItem('study-site-appearance');size=localStorage.getItem('study-site-text-size')}catch{}mode=['light','dark'].includes(mode)?mode:'auto';const theme=mode==='auto'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):mode;root.dataset.theme=theme;root.dataset.themeMode=mode;root.style.colorScheme=theme;if(['sm','lg'].includes(size))root.dataset.textSize=size;if(navigator.standalone||matchMedia('(display-mode: standalone)').matches)root.dataset.standalone='true'})()</script>"""

def header(base=''):
    sizes=''.join(f'<button type="button" class="text-size" data-text-size="{k}" aria-pressed="{str(k=="md").lower()}">{n}</button>' for k,n in (('sm','작게'),('md','보통'),('lg','크게')))
    themes=''.join(f'<button type="button" data-theme-choice="{k}" aria-pressed="{str(k=="auto").lower()}">{n}</button>' for k,n in (('auto','시스템'),('light','라이트'),('dark','다크')))
    settings=f'<div class="header-settings"><button type="button" class="appearance-toggle" aria-label="보기 설정" aria-expanded="false" aria-controls="appearance-panel"><span aria-hidden="true">Aa</span> <span>보기</span></button><div id="appearance-panel" class="view-settings-panel" hidden><div class="view-row"><span>글자 크기</span><div class="text-size-picker" role="group" aria-label="글자 크기">{sizes}</div></div><div class="view-row"><span>테마</span><div class="text-size-picker" role="group" aria-label="테마">{themes}</div></div></div></div>'
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html"><img class="brand-symbol" src="{base}assets/icon.svg" width="32" height="32" alt="" aria-hidden="true"><span class="brand-name">{SITE_NAME}</span></a>{settings}</div></header>'

def footer(base=''):
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>{SITE_NAME}</span><a href="{base}index.html">강의 목록</a></div></footer>'

def share_meta(title,description,path):
    # 공유 미리보기: 강의마다 한 문장 핵심을 설명으로 쓴다. 이미지는 사이트 아이콘이다.
    d=html.escape(description,quote=True);t=html.escape(title,quote=True)
    return f'<meta name="description" content="{d}"><meta property="og:type" content="{"article" if path else "website"}"><meta property="og:site_name" content="{SITE_NAME}"><meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:url" content="{SITE_URL}{html.escape(path,quote=True)}"><meta property="og:image" content="{SITE_URL}assets/icon-512.png"><meta name="twitter:card" content="summary">'
def page(title,body,base='',description=None,path=''):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8">{APPEARANCE_BOOT}<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#faf9f6"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="{SITE_NAME}"><meta name="apple-mobile-web-app-status-bar-style" content="default">{share_meta(title,description or SITE_DESCRIPTION,path)}<title>{SITE_NAME} · {html.escape(title)}</title><link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" sizes="180x180" href="{base}assets/apple-touch-icon.png"><link rel="manifest" href="{base}manifest.webmanifest"><script defer src="{base}assets/theme.js?v={ASSET_VERSION}"></script><link rel="stylesheet" href="{base}assets/site.css?v={ASSET_VERSION}"><script defer src="{base}assets/site.js?v={ASSET_VERSION}"></script></head><body>{header(base)}{body}{footer(base)}</body></html>'
def topic_of(row):
    # 홈의 주제 묶음. 등록부의 topic이 우선이고, 없으면 첫 태그를 쓴다.
    return row.get('topic') or row.get('filter_tag') or row['tags'][0]
def render(rows, materials=None, leads=None, records=None):
    materials=materials or [];leads=leads or {};records=records or {}
    # 기본 목록 순서는 레지스트리 배열 순서(최신순)이다. 화면의 정렬 버튼은 data-date(강의 날짜)·data-added(사이트에 추가한 시각)로 다시 정렬한다. 날짜가 없는 강의에는 임의의 공개일을 만들지 않는다.
    topics=list(dict.fromkeys(topic_of(row) for row in rows+materials))
    count={t:sum(topic_of(r)==t for r in rows+materials) for t in topics}
    chips='<button type="button" data-filter-for="topic" data-value="" aria-pressed="true">전체</button>'
    for tag in topics:
        label=html.escape(tag, quote=True)
        chips+=f'<button type="button" data-filter-for="topic" data-value="{label}" aria-pressed="false">{label}<small>{count[tag]}</small></button>'
    cards=''
    for row in rows:
        creator=html.escape(row.get('creator','출처 미기재'))
        topic=html.escape(topic_of(row),quote=True)
        record=records.get(row['id'],{})
        points=[item if isinstance(item,str) else item['l']+' '+item['t']
                for block in record.get('intro',[]) if block['kind']=='points'
                for item in block['items']]
        searchable=html.escape(" ".join([row['title'],row.get('description',''),row.get('creator',''),topic_of(row)]+row['tags']+points),quote=True)
        sections=''.join(
            f'<a class="search-section-link" href="lectures/{row["id"]}.html#detail-{index}" data-search-detail="{html.escape(section_text(block),quote=True)}" hidden>해당 부분 읽기 · <span>{html.escape(block["h"])}</span></a>'
            for index,block in enumerate(record.get('detail',[]),1)
        )
        minutes=reading_minutes(record)
        reading=f'<span class="card-reading" title="공백 제외 분당 500자를 기준으로 계산한 예상 시간">요약 약 {minutes}분</span>' if minutes else ''
        lead=leads.get(row['id'])
        text=f'<p class="card-lead">{html.escape(lead)}</p>' if lead else f'<p>{html.escape(row["description"])}</p>'
        actions=f'<div class="card-actions"><button type="button" data-library-toggle="bookmarks" aria-label="북마크 저장" aria-pressed="false" hidden><span aria-hidden="true">☆</span><span data-bookmark-label>저장</span></button><button type="button" data-library-toggle="read" aria-label="읽음 표시" aria-pressed="false" hidden><span class="read-mark" aria-hidden="true"></span><span data-read-label>읽음</span></button></div>'
        cards+=f'<article class="lecture-card lecture" data-video-id="{row["id"]}" data-kind="lecture" data-topic="{topic}" data-date="{row.get("date","")}" data-added="{row.get("added","")}"'+(f' data-views="{row["views"]}"' if isinstance(row.get("views"),int) else '')+f' data-creator="{html.escape(row.get("creator",""),quote=True)}" data-search="{searchable}"><h2><a class="card-link stretched-link" href="lectures/{row["id"]}.html">{html.escape(row["title"])}</a></h2>{text}<div class="card-context"><div class="meta"><span class="card-topic">{topic}</span><span class="creator">{creator}</span><span class="card-timing">'+(f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time><span class="meta-dot" aria-hidden="true">·</span>' if row.get("date") else '')+f'<span>원본 {html.escape(row["duration"])}</span></span>{reading}</div>{actions}</div><p class="search-context" hidden></p>{sections}</article>'
    # Other material types have their own pages and are not assumed to have a YouTube ID.
    type_names={'book':'책','paper':'연구','article':'글','note':'학습 노트'}
    for item in materials:
        kind=item['kind']
        if kind not in type_names:raise ValueError('지원하지 않는 자료 유형: '+kind)
        url=item['url']
        if not isinstance(url,str) or not url or url.startswith(('/', '#')) or ':' in url or '..' in url.split('/'):
            raise ValueError('자료 주소는 사이트 내부 상대 경로만 허용합니다')
        creator=html.escape(item.get('creator','출처 미기재'))
        tags=''.join('<span>'+html.escape(x)+'</span>' for x in item['tags'][:2])
        searchable=html.escape(" ".join([item['title'],item.get('description',''),item.get('creator',''),kind]+item['tags']),quote=True)
        cards+=f'<a class="lecture" data-kind="{kind}" data-topic="{html.escape(topic_of(item),quote=True)}" data-search="{searchable}" href="{html.escape(url,quote=True)}"><h2>{html.escape(item["title"])}</h2><div class="meta"><span>{type_names[kind]}</span><span class="creator">{creator}</span></div><p>{html.escape(item.get("description",""))}</p><div class="tags">{tags}</div><span class="read">자료 읽기 →</span></a>'
    total=len(rows)+len(materials)
    viewed=[r for r in rows if isinstance(r.get('views'),int)]
    checked=max((r.get('views_checked','') for r in viewed),default='')
    views_option='<option value="views">조회수순</option>' if viewed else ''
    views_note=f'<p class="views-note" id="views-note" hidden>유튜브 조회수는 {checked.replace("-",".")} 기준이며 이후 달라질 수 있습니다.</p>' if viewed and checked else ''
    noun='자료' if materials else '강의'
    # 오늘의 한 문장: 가장 최근 강의의 첫 핵심 요점을 첫 화면에 둔다.
    feature=''
    first=next((r for r in rows if leads.get(r['id'])),None)
    if first:
        feature=f'<section class="today-line" aria-label="오늘의 한 문장"><div class="today-heading"><span class="eyebrow">오늘의 한 문장</span><button type="button" class="today-random" hidden><span aria-hidden="true">↻</span> 다른 문장 보기</button></div><div aria-live="polite"><p class="today-key">{html.escape(leads[first["id"]])}</p><a class="today-source stretched-link" href="lectures/{first["id"]}.html">{html.escape(first["title"])} · {html.escape(first.get("creator",""))}</a></div></section>'
    body=f'''<div class="site-shell"><main id="main" class="home-main"><section id="lectures"><div id="home-catalog"><h1 class="home-title">강의 요약</h1><p class="catalog-intro">한 문장에서 시작해 깊이 읽는 강의 서재</p>{feature}<section class="discovery-panel" aria-label="강의 탐색"><div class="search-panel"><label for="search">{noun} 검색</label><div class="search-controls"><div class="search-field"><svg class="search-icon" aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6"/><path d="m15 15 4 4"/></svg><input class="search" id="search" type="search" placeholder="주제·궁금한 내용 검색" data-filter-input="#home-catalog" data-count="count" data-empty="empty" data-noun="{noun}" data-persist-query="true"><button type="button" class="search-clear" aria-label="검색창 비우기" data-clear-for="search" hidden><span aria-hidden="true">×</span></button></div><button type="button" class="bookmark-filter" data-bookmark-filter aria-pressed="false" hidden><span aria-hidden="true">★</span> 북마크만</button></div><div class="filter-chips" role="group" aria-label="주제">{chips}</div></div><div class="catalog-order"><p class="catalog-results" aria-live="polite"><strong id="catalog-topic">전체</strong><span aria-hidden="true"> · </span><span id="count">{total}개 {noun}</span></p><select class="catalog-sort" id="catalog-sort" aria-label="강의 정렬" hidden><option value="latest">최신순</option><option value="added">추가된순</option>{views_option}</select></div>{views_note}</section><aside class="resume-reading" aria-label="이어서 읽기" hidden><a data-resume-link><strong>이어서 읽기</strong><span data-resume-title></span><small data-resume-section></small></a><button type="button" data-resume-clear aria-label="읽던 위치 지우기">×</button></aside><div class="lecture-grid" id="lecture-list">{cards}</div></div><div class="empty" id="empty" hidden><svg class="empty-icon" aria-hidden="true" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 5h5a4 4 0 0 1 4 4v11a3 3 0 0 0-3-3H3zM21 5h-5a4 4 0 0 0-4 4v11a3 3 0 0 1 3-3h6z"/></svg><p data-empty-message>검색 결과가 없습니다. 다른 단어로 찾거나 ‘전체’를 선택해 주세요.</p><div class="empty-actions"><button type="button" class="btn secondary" data-clear-bookmarks hidden>전체 강의 보기</button><button type="button" class="btn secondary" data-clear-search hidden>검색어 지우기</button><button type="button" class="btn secondary" data-clear-topic hidden>주제 필터 해제</button></div></div></section></main></div>'''
    return page('강의 요약',body)

def first_key_point(record):
    for block in record.get('intro', []):
        if block['kind']=='points' and block['items']:
            item=block['items'][0]
            return item if isinstance(item,str) else item['t']
    return ''

def load_records(root=R):
    path=root/'data'/'lecture_compact.json'
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

def load_leads(root=R):
    return {vid:first_key_point(record) for vid,record in load_records(root).items()}

def render_catalog(rows,materials,root=R):
    records=load_records(root)
    leads={vid:first_key_point(record) for vid,record in records.items()}
    return render(rows,materials,leads,records)

def build(check=False):
    result=render_catalog(json.loads((R/'lectures.json').read_text(encoding='utf-8')),json.loads((R/'materials.json').read_text(encoding='utf-8')))
    offline_page=page('오프라인', '<main id="main" class="site-shell"><article class="summary-page offline-content"><h1>인터넷에 연결되지 않았습니다</h1><p>이미 열어 본 강의는 오프라인에서도 읽을 수 있습니다. 처음 여는 강의는 인터넷 연결이 필요합니다.</p><p><a href="index.html">강의 목록으로 돌아가기</a></p></article></main>')
    offline_target=R/'offline.html'
    target=R/'index.html'
    if check:
        matches=target.read_text(encoding='utf-8')==result
        print('PASS: generated home matches index.html' if matches else 'FAIL: regenerate index.html with scripts/build_library.py')
        if not matches:
            current=target.read_text(encoding='utf-8')
            first=next((i for i,(a,b) in enumerate(zip(result,current)) if a!=b),min(len(result),len(current)))
            print('First mismatch at',first)
            print('Expected:',repr(result[max(0,first-100):first+180]))
            print('Actual:  ',repr(current[max(0,first-100):first+180]))
        offline_matches=offline_target.read_text(encoding="utf-8")==offline_page
        if not offline_matches:print("FAIL: regenerate offline.html with scripts/build_library.py")
        return 0 if matches and offline_matches else 1
    target.write_text(result,encoding='utf-8')
    offline_target.write_text(offline_page,encoding='utf-8')
    return 0

if __name__=='__main__':sys.exit(build('--check' in sys.argv))
