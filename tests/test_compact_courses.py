import unittest,json,sys,re,html
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'scripts'))
from build_compact_lectures import build
from validate_site import validate

def detail_texts(block):
 """Yield every sentence group of a detail block: paragraphs and labelled-list items."""
 for item in block['p']:
  if isinstance(item,str):yield item
  else:
   assert item['list'],block['h']
   for point in item['list']:
    assert re.match(r'^[가-힣A-Za-z0-9].*[가-힣A-Za-z0-9]$|^[가-힣A-Za-z0-9]$',point['l']),point['l']
    yield point['t']
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
   self.assertNotIn('<img ',source[source.index('<main id="main"'):])
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
  self.assertEqual({r['id'] for r in rows},set(courses))
  for vid,item in courses.items():
   self.assertEqual(len(item['three']),3)
   self.assertTrue(item['sections'])
   self.assertFalse(any(str(x).startswith(('핵심 원리:', '훈련의 구분:', '실천 방향:')) for x in item['three']),vid)
   self.assertTrue(item['question'] and item['answer'])
   self.assertTrue(all(str(x).endswith('다.') for x in item['three']),vid)
  self.assertFalse(build(check=True))
  self.assertEqual(validate(R),[])
