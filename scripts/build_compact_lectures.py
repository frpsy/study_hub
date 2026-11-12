"""Generate lecture pages: a key summary (one sentence, three points) plus timestamps (김주환 lectures) or a detailed summary (other creators)."""
from pathlib import Path
import html,json,sys
from build_library import page,R
E=html.escape
def load(name):return json.loads((R/'data'/name).read_text(encoding='utf-8'))
def practice_step(step, record, youtube_url):
 # Keep disclosure and source navigation separate: opening an explanation never
 # launches a video. Non-Kim lectures link to a real summary section, not a time.
 stamp=step.get('t')
 label=(' <small>('+E(stamp)+')</small>') if stamp else ''
 source=''
 if stamp and youtube_url:
  seconds=0
  for part in stamp.split(':'):seconds=seconds*60+int(part)
  source=f'<a class="practice-source" href="{E(youtube_url,quote=True)}&amp;t={seconds}s" target="_blank" rel="noopener">영상에서 {E(stamp)} 보기 ↗</a>'
 elif 'detail_index' in step:
  index=step['detail_index']
  source=f'<a class="practice-source" href="#detail-{index+1}">관련 해설 · {E(record["detail"][index]["h"])}</a>'
 return '<details><summary>'+E(step['h'])+label+'</summary><ul>'+''.join('<li>'+E(t)+'</li>' for t in step['b'])+'</ul>'+source+'</details>'
def pager(prev,nxt):
 cell=lambda r,cls,label:(f'<a class="pager-link {cls}" href="{E(r["id"],quote=True)}.html"><small>{label}</small><span>{E(r["title"])}</span></a>' if r else '<span class="pager-link is-empty" aria-hidden="true"></span>')
 return f'<nav class="lecture-pager" aria-label="다른 강의">{cell(prev,"is-prev","← 더 최근 강의")}{cell(nxt,"is-next","지난 강의 →")}</nav>'
def render(row,record,mini,prev=None,nxt=None):
 vid=row['id']; title=E(row['title'])
 # A lecture may be indexed by a stable internal content key before its actual YouTube ID is verified.
 youtube_url=row.get('video_url') or (f'https://www.youtube.com/watch?v={vid}' if len(vid)==11 and all(c.isascii() and (c.isalnum() or c in '-_') for c in vid) else None)
 date_info=(f'<time datetime="{E(row["date"],quote=True)}">{E(row["date"]).replace("-",".")}</time> · ' if row.get("date") else '')
 source_info=(f'<a href="{E(youtube_url,quote=True)}" target="_blank" rel="noopener">원본 영상 ↗</a>' if youtube_url else '<span>원본 영상 주소 확인 중</span>')
 practice=record.get('practice')
 aliases=set(record['aliases'])-{'lecture-overview','overview','lecture-comment','timeline','lecture-detail','lecture-sources'}-({'lecture-practice'} if practice else set())
 old=''.join(f'<span id="{E(a)}" class="legacy-anchor" aria-hidden="true"></span>' for a in sorted(aliases))
 note=f'<p class="source-note">{E(record["note"])}</p>' if record.get('note') else ''
 timed='timeline' in record
 detailed='detail' in record
 second='';actions=[]
 if detailed:
  actions.append('<a class="btn secondary" href="#lecture-detail">상세 요약으로 이동</a>')
  blocks=''.join(f'<h3 id="detail-{i+1}">'+E(b['h'])+'</h3>'+''.join('<p>'+E(t)+'</p>' for t in b['p']) for i,b in enumerate(record['detail']))
  # In-section outline: the question headings double as a map of the summary.
  outline=''.join(f'<li><a href="#detail-{i+1}">'+E(b['h'])+'</a></li>' for i,b in enumerate(record['detail']))
  second+=f'<section id="lecture-detail" class="lecture-section"><h2>상세 요약</h2><nav class="detail-toc" aria-label="상세 요약 소제목"><ol>{outline}</ol></nav><div class="detail-body">{blocks}</div></section>'
 if timed:
  timeline_text=E(record['timeline'])
  actions.append('<a class="btn secondary" href="#lecture-comment">타임스탬프로 이동</a>')
  second+=f'<section id="lecture-comment" class="lecture-section"><span id="timeline"></span><h2>타임스탬프</h2><div class="actions"><button id="copy" data-copy-target="comment" type="button">타임스탬프 복사</button><span id="status" role="status" aria-live="polite"></span></div><input type="checkbox" id="timeline-toggle" class="timeline-toggle" aria-label="타임스탬프 전체 펼치기"><label class="timeline-box" for="timeline-toggle"><pre id="comment" tabindex="0"><code>{timeline_text}</code></pre></label></section>'
 action=''.join(actions)
 practice_html=''
 if practice:
  steps=''.join(practice_step(x,record,youtube_url) for x in practice['steps'])
  today=''.join('<li>'+E(t)+'</li>' for t in practice['today'])
  practice_html='<section id="lecture-practice" class="lecture-section"><h2>실천 포인트</h2><div class="summary-tier"><h3>오늘의 실천 세 가지</h3><ol class="summary-list">'+today+'</ol></div><div class="summary-tier"><h3>'+E(practice.get('steps_title','단계별 따라 하기'))+'</h3>'+steps+'<p class="source-note">'+E(practice['note'])+'</p></div></section>'
 sources=''.join(f'<li><a href="{E(s["url"],quote=True)}" target="_blank" rel="noopener">{E(s["label"])}</a></li>' for s in record['sources'])
 sections=[('lecture-overview','핵심 요약')]+([('lecture-practice','실천 포인트')] if practice else [])+([('lecture-detail','상세 요약')] if detailed else [])+([('lecture-comment','타임스탬프')] if timed else [])+[('lecture-sources','참고 자료')]
 section_nav='<nav class="reading-nav" aria-label="이 강의 목차">'+''.join(f'<a href="#{target}">{label}</a>' for target,label in sections)+'</nav>'
 body=f'''<div class="site-shell"><nav class="breadcrumb" aria-label="현재 위치"><a href="../index.html">강의 목록</a><span aria-hidden="true">/</span><span>{title}</span></nav><main id="main" class="compact-lecture" data-layout="compact"><header class="summary-head"><span class="eyebrow">강의 요약</span><h1>{title}</h1><p class="meta">{date_info}{E(row['duration'])} · {E(row.get("creator","출처 미기재"))} · {source_info}</p><div class="actions">{action}</div></header>{old}<section id="lecture-overview" class="lecture-section"><span id="overview"></span><h2>핵심 요약</h2><div class="summary-tier"><span class="eyebrow">한 문장</span><p class="summary-lead">{E(mini['lead'])}</p></div><div class="summary-tier"><h3>핵심 세 가지</h3><ol class="summary-list">{''.join('<li>'+E(t)+'</li>' for t in mini['three'])}</ol></div></section>{practice_html}{second}<details class="source-disclosure"><summary>원본과 참고 자료</summary><ul>{sources}</ul>{note}</details>{pager(prev,nxt)}<nav class="summary-links" aria-label="탐색"><a class="btn secondary" href="../index.html">강의 목록</a></nav></main></div>'''
 body=body.replace('<div class="actions">'+action+'</div>','')
 body=body.replace('</header>'+old,'</header>'+section_nav+old)
 body=body.replace('<details class="source-disclosure">','<details class="source-disclosure" id="lecture-sources">')
 return page(row['title'],body,base='../')
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
