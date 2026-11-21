# -*- coding: utf-8 -*-
"""Build the lecture list from the registry: python scripts/build_library.py"""
from pathlib import Path
import json,html,sys
R=Path(__file__).resolve().parents[1]
SITE_NAME='내면의 서재'
SITE_DESCRIPTION='강의별 핵심 요약과 타임스탬프·상세 요약을 모은 서재'
SITE_URL='https://frpsy.github.io/study_hub/'
ASSET_VERSION=json.loads((R/'build-info.json').read_text(encoding='utf-8'))['version']
def header(base=''):
    return f'<a class="skip-link" href="#main">본문으로 건너뛰기</a><header class="site-header"><div class="site-header-inner"><a class="site-brand" href="{base}index.html"><img class="brand-symbol" src="{base}assets/icon.svg" width="32" height="32" alt="" aria-hidden="true"><span class="brand-name">{SITE_NAME}</span></a></div></header>'
def footer(base=''):
    # 화면 테마 버튼은 늘 보이게 두고, 강조 색·글자 크기는 보기 설정 패널에 모은다. 값은 이 기기에만 저장하고 학습 기록은 남기지 않는다.
    swatches=''.join(f'<button type="button" class="accent-swatch" data-accent="{k}" aria-label="강조 색 {n}" aria-pressed="{str(k=="red").lower()}"></button>' for k,n in (('red','레드'),('blue','블루'),('green','그린')))
    sizes=''.join(f'<button type="button" class="text-size" data-text-size="{k}" aria-pressed="{str(k=="md").lower()}">{n}</button>' for k,n in (('sm','작게'),('md','보통'),('lg','크게')))
    return f'<footer class="site-footer"><div class="site-footer-inner"><span>{SITE_NAME}</span><a href="{base}index.html">강의 목록</a><details class="view-settings"><summary>보기 설정</summary><div class="view-settings-panel"><div class="view-row"><span>강조 색</span><div class="accent-picker" role="group" aria-label="강조 색">{swatches}</div></div><div class="view-row"><span>글자 크기</span><div class="text-size-picker" role="group" aria-label="글자 크기">{sizes}</div></div></div></details><button type="button" class="theme-toggle" data-theme-toggle aria-label="화면 테마 변경">화면 · 시스템</button></div></footer>'
def share_meta(title,description,path):
    # 공유 미리보기: 강의마다 한 문장 핵심을 설명으로 쓴다. 이미지는 사이트 아이콘이다.
    d=html.escape(description,quote=True);t=html.escape(title,quote=True)
    return f'<meta name="description" content="{d}"><meta property="og:type" content="{"article" if path else "website"}"><meta property="og:site_name" content="{SITE_NAME}"><meta property="og:title" content="{t}"><meta property="og:description" content="{d}"><meta property="og:url" content="{SITE_URL}{html.escape(path,quote=True)}"><meta property="og:image" content="{SITE_URL}assets/icon-512.png"><meta name="twitter:card" content="summary">'
def page(title,body,base='',description=None,path=''):
    return f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#ffffff"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="apple-mobile-web-app-title" content="{SITE_NAME}"><meta name="apple-mobile-web-app-status-bar-style" content="default">{share_meta(title,description or SITE_DESCRIPTION,path)}<title>{SITE_NAME} · {html.escape(title)}</title><link rel="icon" href="{base}assets/icon.svg" type="image/svg+xml"><link rel="apple-touch-icon" sizes="180x180" href="{base}assets/apple-touch-icon.png"><link rel="manifest" href="{base}manifest.webmanifest"><script src="{base}assets/theme.js?v={ASSET_VERSION}"></script><link rel="stylesheet" href="{base}assets/site.css?v={ASSET_VERSION}"><script defer src="{base}assets/site.js?v={ASSET_VERSION}"></script></head><body>{header(base)}{body}{footer(base)}</body></html>'
def topic_of(row):
    # 홈의 주제 묶음. 등록부의 topic이 우선이고, 없으면 첫 태그를 쓴다.
    return row.get('topic') or row.get('filter_tag') or row['tags'][0]
def views_text(count):
    # 1만 미만은 쉼표 숫자, 이상은 '5.4만회'처럼 줄여 쓴다.
    if count<10000:return f'{count:,}회'
    if count<100000000:
        man=count/10000
        if man>=100:return f'{round(man):,}만회'
        man=round(man,1)
        return (f'{man:.0f}' if man==int(man) else f'{man:.1f}')+'만회'
    return f'{count/100000000:.1f}억회'
def render(rows, materials=None, leads=None):
    materials=materials or [];leads=leads or {}
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
        searchable=html.escape(" ".join([row['title'],row.get('description',''),row.get('creator',''),topic_of(row)]+row['tags']),quote=True)
        lead=leads.get(row['id'])
        text=f'<p class="card-lead">{html.escape(lead)}</p>' if lead else f'<p>{html.escape(row["description"])}</p>'
        cards+=f'<a class="lecture" data-video-id="{row["id"]}" data-kind="lecture" data-topic="{topic}" data-date="{row.get("date","")}" data-added="{row.get("added","")}"'+(f' data-views="{row["views"]}"' if isinstance(row.get("views"),int) else '')+f' data-creator="{html.escape(row.get("creator",""),quote=True)}" data-search="{searchable}" href="lectures/{row["id"]}.html"><div class="meta"><span class="card-topic">{topic}</span>'+(f'<time datetime="{row["date"]}">{row["date"].replace("-",".")}</time>' if row.get("date") else '')+f'<span>{html.escape(row["duration"])}</span><span class="creator">{creator}</span>'+(f'<span class="views">조회수 {views_text(row["views"])}</span>' if isinstance(row.get("views"),int) else '')+f'</div><h2>{html.escape(row["title"])}</h2>{text}</a>'
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
        cards+=f'<a class="lecture" data-kind="{kind}" data-topic="{html.escape(topic_of(item),quote=True)}" data-search="{searchable}" href="{html.escape(url,quote=True)}"><div class="meta"><span>{type_names[kind]}</span><span class="creator">{creator}</span></div><h2>{html.escape(item["title"])}</h2><p>{html.escape(item.get("description",""))}</p><div class="tags">{tags}</div><span class="read">자료 읽기 →</span></a>'
    total=len(rows)+len(materials)
    viewed=[r for r in rows if isinstance(r.get('views'),int)]
    checked=max((r.get('views_checked','') for r in viewed),default='')
    views_button='<button type="button" data-sort="views" aria-pressed="false">조회수순</button>' if viewed else ''
    views_note=f'<p class="views-note" id="views-note" hidden>유튜브 조회수는 {checked.replace("-",".")} 기준이며 이후 달라질 수 있습니다.</p>' if viewed and checked else ''
    noun='자료' if materials else '강의'
    # 오늘의 한 문장: 가장 최근 강의의 한 문장 핵심을 첫 화면에 둔다.
    feature=''
    first=next((r for r in rows if leads.get(r['id'])),None)
    if first:
        feature=f'<a class="today-line" href="lectures/{first["id"]}.html"><span class="eyebrow">오늘의 한 문장</span><blockquote>{html.escape(leads[first["id"]])}</blockquote><span class="today-source">{html.escape(first["title"])} · {html.escape(first.get("creator",""))}</span></a>'
    body=f'''<div class="site-shell"><main id="main" class="home-main"><section id="lectures"><div id="home-catalog"><h1 class="home-title">강의 요약</h1><p class="catalog-intro">한 문장에서 시작해 깊이 읽는 강의 서재</p>{feature}<div class="search-panel"><label for="search">{noun} 검색</label><div class="search-controls"><input class="search" id="search" type="search" placeholder="제목, 강연자, 주제로 검색" data-filter-input="#home-catalog" data-count="count" data-empty="empty" data-noun="{noun}" data-persist-query="true"><button type="button" class="btn secondary" data-clear-for="search" hidden>초기화</button></div><div class="filter-chips" role="group" aria-label="주제">{chips}</div><p class="search-summary" id="count" aria-live="polite">{total}개 {noun}</p></div><div class="catalog-order"><span>모든 {noun}</span><div class="sort-toggle" role="group" aria-label="정렬"><button type="button" data-sort="latest" aria-pressed="true">최신순</button><button type="button" data-sort="added" aria-pressed="false">추가된순</button>{views_button}</div></div>{views_note}<div class="lecture-grid" id="lecture-list">{cards}</div></div><p class="empty" id="empty" hidden>검색 결과가 없습니다. 다른 단어로 찾거나 ‘전체’를 선택해 주세요.</p></section></main></div>'''
    return page('강의 요약',body)

def load_leads(root=R):
    path=root/'data'/'mini_courses.json'
    if not path.exists():return {}
    minis=json.loads(path.read_text(encoding='utf-8'))
    return {k:v['lead'] for k,v in minis.items() if isinstance(v,dict) and v.get('lead')}
def build(check=False):
    leads=load_leads()
    result=render(json.loads((R/'lectures.json').read_text(encoding='utf-8')),json.loads((R/'materials.json').read_text(encoding='utf-8')),leads)
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
        return 0 if matches else 1
    target.write_text(result,encoding='utf-8')
    return 0

if __name__=='__main__':sys.exit(build('--check' in sys.argv))
