"""Generate lecture pages: an intro (one sentence + content-driven blocks) plus timestamps (김주환 lectures) or a detailed summary (other creators)."""
from pathlib import Path
import html,json,re,sys
from build_library import page,R
E=html.escape
def block_html(t):
 """A detail item is a paragraph (str), a labelled list ({"list": [{"l": label, "t": text}, ...]}) or an inline image ({"image": {"src","alt","width","height","caption"}})."""
 if isinstance(t,str):return '<p>'+E(t)+'</p>'
 if 'image' in t:
  g=t['image'];cap=('<figcaption>'+E(g['caption'])+'</figcaption>') if g.get('caption') else ''
  return f'<figure class="detail-figure"><img src="../{E(g["src"],quote=True)}" width="{int(g["width"])}" height="{int(g["height"])}" alt="{E(g["alt"],quote=True)}" loading="lazy" decoding="async">{cap}</figure>'
 return '<ul class="detail-points">'+''.join('<li><strong class="point-label">'+E(i['l'])+'</strong>'+E(i['t'])+'</li>' for i in t['list'])+'</ul>'

def editor_html(groups):
 """Limits, supplements and evidence checks live only here, inside the closed sources-and-notes fold at the page end."""
 if not groups:return ''
 return '<div class="editor-notes" id="lecture-editor"><h3>편집자 주</h3>'+''.join('<h4>'+E(g['h'])+'</h4><ul class="editor-list">'+''.join('<li>'+E(t)+'</li>' for t in g['items'])+'</ul>' for g in groups)+'</div>'

def load(name):return json.loads((R/'data'/name).read_text(encoding='utf-8'))
def seconds(stamp):
 total=0
 for part in stamp.split(':'):total=total*60+int(part)
 return total
def source_link(step, record, youtube_url):
 # Source navigation is separate from any disclosure: opening an explanation never
 # launches a video. Non-Kim lectures link to a real summary section, not a time.
 stamp=step.get('t')
 if stamp and youtube_url:
  return f'<a class="practice-source" href="{E(youtube_url,quote=True)}&amp;t={seconds(stamp)}s" target="_blank" rel="noopener">영상 {E(stamp)}부터 보기 ↗</a>'
 if 'detail_index' in step:
  index=step['detail_index']
  return f'<a class="practice-source" href="#detail-{index+1}">관련 해설 · {E(record["detail"][index]["h"])}</a>'
 return ''
def practice_step(step, record, youtube_url):
 stamp=step.get('t')
 label=(' <small>('+E(stamp)+')</small>') if stamp else ''
 return '<details><summary>'+E(step['h'])+label+'</summary><ul>'+''.join('<li>'+E(t)+'</li>' for t in step['b'])+'</ul>'+source_link(step,record,youtube_url)+'</details>'
INTRO_KINDS=('points','practice','steps')
def check_intro(vid, record):
 """Refuse data the intro cannot render faithfully. Editorial limits (counts, lengths, quotes) are checked by tests."""
 intro=record['intro']
 if not isinstance(intro,list) or not intro:raise ValueError(f'{vid}: intro must be a non-empty list of blocks')
 if 'practice' in record:raise ValueError(f'{vid}: intro and practice must not be used together')
 kinds=[b.get('kind') for b in intro]
 if len(set(kinds))!=len(kinds) or not set(kinds)<=set(INTRO_KINDS):raise ValueError(f'{vid}: intro kinds must be unique and one of {INTRO_KINDS}: {kinds}')
 for b in intro:
  if not b.get('h') or not b.get('items'):raise ValueError(f'{vid}: every intro block needs a heading and items')
  for item in b['items']:
   if b['kind']=='practice' and not all(item.get(k) for k in ('when','do')):raise ValueError(f'{vid}: practice items need when and do (check is optional)')
   if 'detail_index' in item and not 0<=item['detail_index']<len(record.get('detail',[])):raise ValueError(f'{vid}: detail_index out of range')
def point_html(item):
 """A point is a sentence (str) or a labelled sentence ({"l": label, "t": sentence})."""
 if isinstance(item,str):return '<li>'+E(item)+'</li>'
 return '<li><strong class="point-label">'+E(item['l'])+'</strong>'+E(item['t'])+'</li>'
def action_html(item, record, youtube_url):
 """One thing to try: when / what to do, plus how to check only when the lecturer gave a criterion, and the lecturer's own words and a link to the moment."""
 cells=''.join(f'<div><dt>{label}</dt><dd>{E(item[key])}</dd></div>' for key,label in (('when','언제'),('do','할 일'),('check','확인')) if item.get(key))
 link=source_link(item,record,youtube_url)
 # With a quote the moment link ends the quote line (an inline link keeps the card short); without one it stands alone.
 quote=('<blockquote class="practice-quote"><p>“'+E(item['quote'])+'”'+((' '+link) if link else '')+'</p></blockquote>',) if item.get('quote') else ('',)
 return '<li><dl class="practice-cells">'+cells+'</dl>'+quote[0]+('' if item.get('quote') else link)+'</li>'
def intro_block_html(block, record, youtube_url):
 kind=block['kind'];head='<h3>'+E(block['h'])+'</h3>'
 if kind=='points':body='<ul class="summary-list">'+''.join(point_html(i) for i in block['items'])+'</ul>'
 elif kind=='practice':body='<ol class="practice-list">'+''.join(action_html(i,record,youtube_url) for i in block['items'])+'</ol>'
 else:body=''.join(practice_step(i,record,youtube_url) for i in block['items'])
 return f'<div class="summary-tier intro-block intro-{kind}">{head}{body}</div>'
def intro_html(mini, record, youtube_url):
 """The lecture's opening section: the one-sentence lead, then only the blocks this lecture's content calls for."""
 blocks=''.join(intro_block_html(b,record,youtube_url) for b in record['intro'])
 return f'<section id="lecture-overview" class="lecture-section"><span id="overview"></span><h2>도입</h2><div class="summary-tier"><span class="eyebrow">한 문장</span><p class="summary-lead">{E(mini["lead"])}</p></div>{blocks}</section>'
def pager(prev,nxt):
 cell=lambda r,cls,label:(f'<a class="pager-link {cls}" href="{E(r["id"],quote=True)}.html"><small>{label}</small><span>{E(r["title"])}</span></a>' if r else '<span class="pager-link is-empty" aria-hidden="true"></span>')
 return f'<nav class="lecture-pager" aria-label="다른 강의">{cell(prev,"is-prev","← 최근 강의")}{cell(nxt,"is-next","지난 강의 →")}</nav>'
def render(row,record,mini,prev=None,nxt=None):
 vid=row['id']; title=E(row['title'])
 # A lecture may be indexed by a stable internal content key before its actual YouTube ID is verified.
 youtube_url=row.get('video_url') or (f'https://www.youtube.com/watch?v={vid}' if len(vid)==11 and all(c.isascii() and (c.isalnum() or c in '-_') for c in vid) else None)
 date_info=(f'<time datetime="{E(row["date"],quote=True)}">{E(row["date"]).replace("-",".")}</time> · ' if row.get("date") else '')
 source_info=(f'<a href="{E(youtube_url,quote=True)}" target="_blank" rel="noopener">원본 영상 ↗</a>' if youtube_url else '<span>원본 영상 주소 확인 중</span>')
 if 'intro' not in record:raise ValueError(f'{vid}: every lecture needs an intro (편집규칙 19절)')
 if 'three' in mini:raise ValueError(f'{vid}: three is gone; the intro holds the key points')
 check_intro(vid,record)
 aliases=set(record['aliases'])-{'lecture-overview','overview','lecture-comment','timeline','lecture-detail','lecture-sources'}
 # Old links to #lecture-practice keep landing on the page now that practice lives inside the intro.
 aliases|={'lecture-practice'}
 old=''.join(f'<span id="{E(a)}" class="legacy-anchor" aria-hidden="true"></span>' for a in sorted(aliases))
 editor=editor_html(record.get('editor'))
 timed='timeline' in record
 detailed='detail' in record
 second='';actions=[]
 if detailed:
  actions.append('<a class="btn secondary" href="#lecture-detail">상세 요약으로 이동</a>')
  blocks=''.join(f'<h3 id="detail-{i+1}">'+E(b['h'])+'</h3>'+''.join(block_html(t) for t in b['p']) for i,b in enumerate(record['detail']))
  # In-section outline: the question headings double as a map of the summary.
  outline=''.join(f'<li><a href="#detail-{i+1}">'+E(b['h'])+'</a></li>' for i,b in enumerate(record['detail']))
  second+=f'<section id="lecture-detail" class="lecture-section"><h2>상세 요약</h2><nav class="detail-toc" aria-label="상세 요약 소제목"><ol>{outline}</ol></nav><div class="detail-body">{blocks}</div></section>'
 if timed:
  timeline_text=E(record['timeline'])
  actions.append('<a class="btn secondary" href="#lecture-comment">타임스탬프로 이동</a>')
  second+=f'<section id="lecture-comment" class="lecture-section"><span id="timeline"></span><h2>타임스탬프</h2><div class="actions"><button id="copy" data-copy-target="comment" type="button">타임스탬프 복사</button><span id="status" role="status" aria-live="polite"></span></div><input type="checkbox" id="timeline-toggle" class="timeline-toggle" aria-label="타임스탬프 전체 펼치기"><label class="timeline-box" for="timeline-toggle"><pre id="comment" tabindex="0"><code>{timeline_text}</code></pre></label></section>'
 action=''.join(actions)
 sources=''.join(f'<li><a href="{E(s["url"],quote=True)}" target="_blank" rel="noopener">{E(s["label"])}</a></li>' for s in record['sources'])
 sections=[('lecture-overview','도입')]+([('lecture-detail','상세 요약')] if detailed else [])+([('lecture-comment','타임스탬프')] if timed else [])+[('lecture-sources','출처')]
 section_nav='<nav class="reading-nav" aria-label="이 강의 목차">'+''.join(f'<a href="#{target}">{label}</a>' for target,label in sections)+'</nav>'
 overview_html=intro_html(mini,record,youtube_url)
 body=f'''<div class="site-shell"><nav class="breadcrumb" aria-label="현재 위치"><a href="../index.html">강의 목록</a><span aria-hidden="true">/</span><span>{title}</span></nav><main id="main" class="compact-lecture" data-layout="compact"><header class="summary-head"><h1>{title}</h1><p class="meta">{date_info}{E(row['duration'])} · {E(row.get("creator","출처 미기재"))} · {source_info}</p><div class="actions">{action}</div></header>{old}{overview_html}{second}<details class="source-disclosure" id="lecture-sources"><summary>출처와 편집자 주</summary><div class="notes-block"><h3>원본과 참고 자료</h3><ul>{sources}</ul></div>{editor}</details>{pager(prev,nxt)}</main></div>'''
 body=body.replace('<div class="actions">'+action+'</div>','')
 img=row.get('image')
 hero=''
 if img:
  hero=f'<figure class="lecture-hero"><img src="../{E(img["src"],quote=True)}" width="{int(img["width"])}" height="{int(img["height"])}" alt="{E(img["alt"],quote=True)}" decoding="async" fetchpriority="high"></figure>'
 body=body.replace('</header>'+old,'</header>'+hero+section_nav+old)
 return page(row['title'],body,base='../',description=mini['lead'],path=f'lectures/{vid}.html')
def build(check=False):
 records=load('lecture_compact.json');minis=load('mini_courses.json');issues=[]
 rows=json.loads((R/'lectures.json').read_text(encoding='utf-8'))
 for i,row in enumerate(rows):
  vid=row['id'];content=render(row,records[vid],minis[vid],rows[i-1] if i else None,rows[i+1] if i+1<len(rows) else None)
  p=R/'lectures'/f'{vid}.html'
  if check:
   if not p.exists() or p.read_text(encoding='utf-8')!=content:issues.append(str(p.relative_to(R)))
  else:p.parent.mkdir(exist_ok=True);p.write_text(content,encoding='utf-8')
 if check:print('FAIL: '+', '.join(issues) if issues else 'PASS: lecture pages match source')
 return bool(issues)
if __name__=='__main__':sys.exit(build('--check' in sys.argv))
