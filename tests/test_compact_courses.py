import unittest,json,sys,re,html
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from build_compact_lectures import build
from validate_site import validate
from quote_check import load_transcript,quote_problems,stamp_seconds,transcript_path

def detail_texts(block):
 """Yield every sentence group of a detail block: paragraphs and labelled-list items."""
 for item in block['p']:
  if isinstance(item,str):yield item
  elif 'image' in item:continue
  else:
   assert item['list'],block['h']
   for point in item['list']:
    assert re.match(r'^[가-힣A-Za-z0-9].*[가-힣A-Za-z0-9]$|^[가-힣A-Za-z0-9]$',point['l']),point['l']
    yield point['t']
def intro_texts(record):
 """Every visible sentence of an intro: block headings, points, practice cells and quotes, step headings and bodies."""
 for block in record.get('intro',[]):
  yield block['h']
  for item in block['items']:
   if block['kind']=='points':
    yield from ((item,) if isinstance(item,str) else (item['l'],item['t']))
   elif block['kind']=='practice':
    yield from (item[k] for k in ('when','do','check','quote') if k in item)
   else:
    yield item['h'];yield from item['b']
STAMP=r'^(\d+:[0-5]\d|\d+:[0-5]\d:[0-5]\d)$'   # 분·초는 59 이하
class CompactCourseChecks(unittest.TestCase):
 def test_timeline_text_is_preserved_and_copy_has_single_target(self):
  records=json.loads((R/'data/lecture_compact.json').read_text())
  for vid,record in records.items():
   source=(R/'lectures'/f'{vid}.html').read_text()
   if 'timeline' not in record:continue
   text=re.search(r'<pre id="comment"[^>]*><code>(.*?)</code></pre>',source,re.S).group(1)
   self.assertEqual(html.unescape(text),record['timeline'])
   self.assertEqual(source.count('id="comment"'),1)
   self.assertEqual(source.count('data-copy-target="comment"'),1)
   self.assertIn('<label class="timeline-box" for="timeline-toggle"><pre id="comment"',source)
   self.assertIn('type="checkbox" id="timeline-toggle"',source)
   for gone in ('전체 타임스탬프 보기','timeline-teaser','timeline-disclosure'):
    self.assertNotIn(gone,source)
   self.assertIn(html.escape("\n".join(record["timeline"].splitlines()[:3])),source)
   self.assertNotIn('class="timeline-preview"',source)
   # 본문 이미지는 대표 이미지(figure.lecture-hero) 한 장과 상세 요약 안 이미지(figure.detail-figure, 최대 3장)만 허용한다.
   main_html=source[source.index('<main id="main"'):]
   hero=main_html.count('<figure class="lecture-hero"><img ');inline=main_html.count('<figure class="detail-figure"><img ')
   self.assertEqual(main_html.count('<img '),hero+inline)
   self.assertLessEqual(hero,1);self.assertLessEqual(inline,3)
 def test_only_kim_lectures_have_timestamps_others_have_detailed_summary(self):
  rows=json.loads((R/'lectures.json').read_text());records=json.loads((R/'data/lecture_compact.json').read_text())
  for row in rows:
   vid=row['id'];record=records[vid];source=(R/'lectures'/f'{vid}.html').read_text()
   if row.get('creator')=='김주환':
    self.assertIn('timeline',record,vid);self.assertIn('id="lecture-comment"',source,vid);self.assertEqual('detail' in record,'id="lecture-detail"' in source,vid)
    for block in record.get('detail',[]):
     self.assertTrue(block['h'] and block['p'],vid)
     for text in detail_texts(block):self.assertRegex(text,r'[.)]$',vid+': '+text[:30])
   else:
    self.assertNotIn('timeline',record,vid);self.assertNotIn('id="lecture-comment"',source,vid);self.assertNotIn('timeline-toggle',source,vid)
    self.assertIn('id="lecture-detail"',source,vid);self.assertGreaterEqual(len(record['detail']),5,vid)
    self.assertGreaterEqual(len(record['sources']),3,vid)
    for block in record['detail']:
     self.assertTrue(block['h'] and block['p'],vid)
     for text in detail_texts(block):self.assertRegex(text,r'[.)]$',vid+': '+text[:30])
 def test_practice_section_renders_once_with_expandable_steps(self):
  records=json.loads((R/'data/lecture_compact.json').read_text())
  for vid,record in records.items():
   source=(R/'lectures'/f'{vid}.html').read_text()
   if 'practice' not in record:continue
   self.assertEqual(source.count('id="lecture-practice"'),1,vid)
   self.assertEqual(source.count('<details><summary>'),len(record['practice']['steps']),vid)
   self.assertEqual(len(record['practice']['today']),3,vid)
   for step in record['practice']['steps']:
    self.assertTrue(step['b'],vid)
    if 'timeline' in record:
     self.assertRegex(step['t'],r'^\d+:\d\d(:\d\d)?$',vid)
    else:
     self.assertNotIn('t',step,vid)
     self.assertIn(step['detail_index'],range(len(record['detail'])),vid)
 def test_kim_lectures_do_not_use_instructor_subject_phrasing(self):
  rows={r['id']:r for r in json.loads((R/'lectures.json').read_text(encoding='utf-8'))}
  for name in ('mini_courses','summaries','lecture_compact'):
   for vid,item in json.loads((R/'data'/f'{name}.json').read_text(encoding='utf-8')).items():
    if rows.get(vid,{}).get('creator')!='김주환':continue
    self.assertNotIn('강사',json.dumps(item,ensure_ascii=False),f'{name}:{vid}')
 def test_course_coverage_and_tiers(self):
  rows=json.loads((R/'lectures.json').read_text());courses=json.loads((R/'data/mini_courses.json').read_text())
  records=json.loads((R/'data/lecture_compact.json').read_text())
  self.assertEqual({r['id'] for r in rows},set(courses))
  for vid,item in courses.items():
   self.assertTrue(item['sections'])
   self.assertTrue(item['question'] and item['answer'])
   if 'intro' in records[vid]:
    # 핵심 세 가지의 원본은 intro 하나뿐이다(두 곳에 같은 내용을 두지 않는다).
    self.assertNotIn('three',item,vid);continue
   self.assertEqual(len(item['three']),3)
   self.assertFalse(any(str(x).startswith(('핵심 원리:', '훈련의 구분:', '실천 방향:')) for x in item['three']),vid)
   self.assertTrue(all(str(x).endswith('다.') for x in item['three']),vid)
  self.assertFalse(build(check=True))
  self.assertEqual(validate(R),[])

class EditorNoteChecks(unittest.TestCase):
 """본문에는 강의 내용만 둔다. 한계·보충은 맨 끝 접힌 ‘출처와 편집자 주’ 안의 ‘편집자 주’에만 있다(편집규칙.md 17절)."""
 BANNED=('[보충]','대조하지 않았','확인하지 못했','이 요약에서')
 def test_body_has_no_limits_or_supplement_markers(self):
  records=json.loads((R/'data/lecture_compact.json').read_text())
  minis=json.loads((R/'data/mini_courses.json').read_text())
  for vid,record in records.items():
   self.assertNotIn('note',record,vid)
   self.assertNotIn('note',record.get('practice',{}),vid)
   body=[minis[vid]['lead'],*minis[vid].get('three',[]),*intro_texts(record)]
   for block in record.get('detail',[]):body+=[block['h'],*detail_texts(block)]
   for step in record.get('practice',{}).get('steps',[]):body+=[step['h'],*step['b']]
   body+=record.get('practice',{}).get('today',[])
   for text in body:
    for marker in self.BANNED:self.assertNotIn(marker,text,f'{vid}: {text[:40]}')
 def test_editor_notes_render_as_closed_fold_at_page_end(self):
  records=json.loads((R/'data/lecture_compact.json').read_text())
  for vid,record in records.items():
   source=(R/'lectures'/f'{vid}.html').read_text()
   groups=record.get('editor')
   self.assertTrue(groups,vid)
   for group in groups:self.assertTrue(group['h'] and group['items'],vid)
   self.assertEqual(source.count('id="lecture-editor"'),1,vid)
   self.assertIn('<summary>출처와 편집자 주</summary>',source)
   self.assertNotIn('<summary>편집자 주</summary>',source)                       # 두 접힘을 하나로 합쳤다
   self.assertEqual(source.count('<details class="source-disclosure"'),1,vid)
   self.assertNotIn('<details class="source-disclosure" id="lecture-sources" open',source)
   self.assertIn('<h3>편집자 주</h3>',source)
   self.assertLess(source.index('id="lecture-sources"'),source.index('id="lecture-editor"'),vid)
   self.assertLess(source.index('id="lecture-editor"'),source.index('class="lecture-pager"'),vid)

# 2026-11-22 현재 아직 옛 형식(핵심 세 가지 + 실천 포인트)인 강의. 이 밖의 강의는 모두 intro를 써야 한다. 옮기면 이 목록에서 지워도 된다.
LEGACY_FORMAT=frozenset(['2VTv6WW8Kn8', '7R3-3HR6-u4', '9tRohh0gErM', 'ENm40KZM1_g', 'R9O1OowpEuE', 'a2SVP-H_wPY', 'kLizfh-5vuE', 'peaceful-life-live', 'two-stages-meditation', 'vNqK0GhTP6s'])
class IntroChecks(unittest.TestCase):
 """도입 섹션: 핵심 세 가지와 실천 포인트를 하나로 합친 구조. 개수와 블록은 강의 내용이 정하고, 강의에 없는 말은 막는다(편집규칙.md 19절)."""
 def intro_lectures(self):
  rows={r['id']:r for r in json.loads((R/'lectures.json').read_text())}
  records=json.loads((R/'data/lecture_compact.json').read_text())
  return [(rows[v],r) for v,r in records.items() if 'intro' in r]
 def test_new_lectures_use_intro_not_the_old_format(self):
  records=json.loads((R/'data/lecture_compact.json').read_text())
  self.assertTrue(LEGACY_FORMAT<=set(records))
  for vid,record in records.items():
   if vid not in LEGACY_FORMAT:self.assertIn('intro',record,vid+': 새 강의는 intro를 쓴다(편집규칙 19절)')
 def test_intro_replaces_key_summary_and_practice_sections(self):
  found=self.intro_lectures();self.assertTrue(found)
  for row,record in found:
   vid=row['id'];source=(R/'lectures'/f'{vid}.html').read_text()
   self.assertNotIn('practice',record,vid)
   self.assertEqual(source.count('id="lecture-overview"'),1,vid)
   self.assertIn('<h2>도입</h2>',source,vid)
   self.assertNotIn('<h2>핵심 요약</h2>',source,vid);self.assertNotIn('<h2>실천 포인트</h2>',source,vid)
   self.assertNotIn('핵심 세 가지',source,vid);self.assertNotIn('오늘의 실천 세 가지',source,vid)
   self.assertNotIn('<section id="lecture-practice"',source,vid)
   self.assertEqual(source.count('id="lecture-practice"'),1,vid)   # 옛 #lecture-practice 링크가 이 페이지에 도착하도록 남긴 빈 앵커
   self.assertIn('<a href="#lecture-overview">도입</a>',source,vid);self.assertNotIn('>실천 포인트</a>',source,vid)
 def test_intro_blocks_follow_the_lecture_content(self):
  for row,record in self.intro_lectures():
   vid=row['id'];kim=row.get('creator')=='김주환';blocks=record['intro']
   self.assertTrue(1<=len(blocks)<=3,vid)
   kinds=[b['kind'] for b in blocks]
   self.assertEqual(len(kinds),len(set(kinds)),vid)               # 같은 종류의 블록을 두 번 쓰지 않는다
   self.assertTrue(set(kinds)<=set(('points','practice','steps')),vid)
   self.assertIn('points',kinds,vid)                              # 강의가 무엇을 말하는지는 항상 있어야 한다
   for block in blocks:
    self.assertTrue(block['h'] and len(block['h'])<=24 and not re.search(r'(한|두|세|네|다섯|여섯|일곱|여덟|아홉|열|\d+)\s*가지',block['h']),vid+': '+block['h'])   # 제목에 개수를 못 박지 않는다
    items=block['items'];kind=block['kind']
    if kind=='points':
     self.assertTrue(1<=len(items)<=4,vid)
     for item in items:
      text=item if isinstance(item,str) else item['t']
      if not isinstance(item,str):self.assertTrue(item['l'] and set(item)=={'l','t'},vid)
      self.assertTrue(text.endswith('다.') and len(text)<=90 and text.count(',')<=1,vid+': '+text)
    elif kind=='practice':
     self.assertTrue(1<=len(items)<=3,vid)
     for item in items:
      self.assertTrue(set(item)>={'when','do'},vid)   # 확인(check)은 강연자가 점검 기준을 말했을 때만 둔다
      self.assertTrue(set(item)<={'when','do','check','quote','t','detail_index'},vid)
      self.assertTrue(item['when'] and len(item['when'])<=45 and not item['when'].endswith('.'),vid+': '+item['when'])
      for key in ('do','check'):
       if key in item:self.assertTrue(item[key].endswith('다.') and len(item[key])<=80,vid+': '+item[key])
      if kim:
       self.assertRegex(item['t'],STAMP,vid);self.assertNotIn('detail_index',item,vid)
       self.assertTrue(15<=len(item['quote'])<=170,vid+': '+item['quote'])   # 김주환 강의는 강연자의 말을 인용으로 남긴다
      else:
       self.assertNotIn('t',item,vid);self.assertNotIn('quote',item,vid);self.assertIn(item['detail_index'],range(len(record['detail'])),vid)
    else:
     self.assertTrue(2<=len(items)<=7,vid)
     for item in items:
      self.assertTrue(item['h'] and item['b'] and all(isinstance(x,str) and x.strip() for x in item['b']),vid)
      if kim:self.assertRegex(item['t'],STAMP,vid)
      else:self.assertNotIn('t',item,vid);self.assertIn(item['detail_index'],range(len(record['detail'])),vid)
 def test_practice_quotes_are_the_lecturers_words(self):
  """인용의 낱말이 인용 시각 근처의 원본 자막에 같은 순서로 있어야 한다(scripts/quote_check.py). 군더더기·오인식 교정과 띄어쓰기 차이는 허용한다."""
  for row,record in self.intro_lectures():
   if row.get('creator')!='김주환':continue
   path=transcript_path(R,row);self.assertIsNotNone(path,row['id']+': 자막 파일이 없다')
   lines=load_transcript(path)
   for block in record['intro']:
    if block['kind']!='practice':continue
    for item in block['items']:
     if 'quote' not in item:continue
     problems=quote_problems(item['quote'],lines,stamp_seconds(item['t']))
     self.assertEqual(problems,[],f"{row['id']} {item['t']}: {problems}")
 def test_practice_quotes_do_not_repeat_the_lead(self):
  """도입에서 같은 말을 두 번 보이지 않는다: 한 문장(lead)과 12자 이상 겹치는 인용은 쓰지 않는다."""
  norm=lambda x:re.sub(r'[^0-9A-Za-z가-힣]','',x)
  minis=json.loads((R/'data/mini_courses.json').read_text())
  for row,record in self.intro_lectures():
   lead=norm(minis[row['id']]['lead'])
   for block in record['intro']:
    if block['kind']!='practice':continue
    for item in block['items']:
     if 'quote' not in item:continue
     quote=norm(item['quote'])
     overlap=[lead[i:i+12] for i in range(max(0,len(lead)-11)) if lead[i:i+12] in quote]
     self.assertFalse(overlap,f"{row['id']} {item['t']}: 인용이 한 문장과 겹친다 ‘{overlap[:1]}’")
 def test_every_block_kind_renders(self):
  """합성 기록으로 세 블록이 모두 기대한 HTML이 되는지 본다(실제 강의에는 블록이 일부만 있다)."""
  from build_compact_lectures import render
  row={'id':'abcdefghijk','title':'시험 강의','duration':'10분','creator':'김주환','date':'2026-11-22'}
  record={'aliases':[],'sources':[{'label':'원본','url':'https://example.com/'}],'editor':[],'timeline':'■ 핵심 세션\n0:00 시작',
   'intro':[{'kind':'points','h':'핵심','items':['첫째 주장이다.',{'l':'라벨','t':'둘째 주장이다.'}]},
    {'kind':'practice','h':'해볼 일','items':[{'when':'화가 날 때','do':'숨을 고른다.','check':'몸이 풀렸는지 본다.','t':'1:05','quote':'숨을 고르세요'},{'when':'잠들기 전','do':'불을 끈다.','t':'2:10','quote':'불을 끄세요'}]},
    {'kind':'steps','h':'순서','items':[{'h':'1단계','t':'2:00','b':['먼저 한다.']},{'h':'2단계','t':'3:00','b':['다음에 한다.']}]}]}
  html_=render(row,record,{'lead':'“한 문장이다.”'})
  self.assertEqual(html_.count('class="practice-cells"'),2)
  for label in ('<dt>언제</dt>','<dt>할 일</dt>','<dt>확인</dt>'):self.assertIn(label,html_)
  self.assertEqual(html_.count('<dt>확인</dt>'),1)   # 확인 칸이 없는 항목에는 빈 칸을 그리지 않는다
  self.assertRegex(html_,r'<blockquote class="practice-quote"><p>“숨을 고르세요” <a class="practice-source"[^>]*>영상 1:05부터 보기 ↗</a></p></blockquote>')   # 링크는 인용 줄 끝에 둔다
  self.assertIn('v=abcdefghijk&amp;t=65s',html_)
  self.assertIn('<li><strong>라벨</strong>. 둘째 주장이다.</li>',html_)
  self.assertEqual(html_.count('<details><summary>'),2)
  self.assertEqual(html_.count('class="summary-tier intro-block'),3)
  only=dict(record,intro=record['intro'][:1]);short=render(row,only,{'lead':'“한 문장이다.”'})
  self.assertNotIn('practice-cells',short);self.assertNotIn('<details>',short);self.assertIn('<h2>도입</h2>',short)
 def test_generator_refuses_data_it_cannot_render(self):
  from build_compact_lectures import render
  row={'id':'abcdefghijk','title':'시험 강의','duration':'10분','creator':'김주환'}
  base={'aliases':[],'sources':[],'editor':[],'timeline':'■ 핵심 세션\n0:00 시작'}
  points={'kind':'points','h':'핵심','items':['주장이다.']}
  mini={'lead':'“한 문장이다.”'}
  bad={'알 수 없는 종류':[points,{'kind':'video','h':'영상','items':[{'h':'x','b':['y.']}]}],
   '같은 종류 두 번':[points,points],'빈 목록':[],
   '해볼 일에 할 일이 빠짐':[points,{'kind':'practice','h':'해볼 일','items':[{'when':'화날 때','check':'몸이 풀렸는지 본다.'}]}],
   'detail_index 범위 밖':[points,{'kind':'steps','h':'순서','items':[{'h':'1','b':['가.'],'detail_index':5}]}]}
  for label,intro in bad.items():
   with self.assertRaises(ValueError,msg=label):render(row,dict(base,intro=intro),mini)
  with self.assertRaises(ValueError):render(row,dict(base,intro=[points],practice={'today':[],'steps':[]}),mini)

