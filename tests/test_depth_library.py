"""v14 깊이 서재: 주제 묶음, 문장 카드, 공유 메타, 타임라인 막대의 생성 계약."""
import json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build_compact_lectures import time_map,duration_seconds

class DepthLibrary(unittest.TestCase):
    def setUp(self):
        self.rows=json.loads((ROOT/'lectures.json').read_text(encoding='utf-8'))
        self.minis=json.loads((ROOT/'data/mini_courses.json').read_text(encoding='utf-8'))
        self.home=(ROOT/'index.html').read_text(encoding='utf-8')
    def test_every_lecture_has_one_of_few_topics(self):
        topics={r['topic'] for r in self.rows}
        self.assertLessEqual(len(topics),6)
        for topic in topics:self.assertIn(f'data-filter-for="topic" data-value="{topic}"',self.home)
    def test_cards_lead_with_the_key_sentence(self):
        for row in self.rows:
            with self.subTest(id=row['id']):
                card=re.search(r'<a class="lecture" data-video-id="'+re.escape(row['id'])+r'".*?</a>',self.home,re.S).group(0)
                self.assertIn('class="card-lead"',card)
                self.assertIn(f'data-topic="{row["topic"]}"',card)
    def test_lecture_pages_share_their_own_sentence(self):
        for row in self.rows:
            with self.subTest(id=row['id']):
                page=(ROOT/'lectures'/f'{row["id"]}.html').read_text(encoding='utf-8')
                lead=self.minis[row['id']]['lead'].replace('"','&quot;')
                self.assertIn(f'<meta property="og:description" content="{lead}">',page)
                self.assertIn(f'<meta name="description" content="{lead}">',page)
                self.assertEqual(page.count('<meta name="description"'),1)
    def test_time_map_uses_duration_and_keeps_order(self):
        self.assertEqual(duration_seconds('2시간 4분 2초'),7442)
        self.assertIsNone(duration_seconds('확인 중'))
        html=time_map('■ 핵심 세션\n0:00 시작\n30:00 중간\n—상세—\n■ 1. 첫 장\n0:00 a\n■ 2. 둘째 장\n30:00 b','1시간','https://www.youtube.com/watch?v=abcdefghijk')
        self.assertIn('x="500.0"',html)  # 30분은 1시간 막대의 가운데
        self.assertIn('x="498.5"',html)  # 표시는 그 위치를 가운데에 둔다
        self.assertNotRegex(html,r'<(?:ol|ul)\\b')  # 타임스탬프 영역에는 별도 링크 목록을 두지 않는다
        self.assertNotIn('style=',html)
        self.assertEqual(time_map('메모만 있다','1시간',None),'')

if __name__=='__main__':unittest.main()
