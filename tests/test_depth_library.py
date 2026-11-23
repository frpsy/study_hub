"""v14 깊이 서재: 주제 묶음, 문장 카드, 공유 메타의 생성 계약."""
import json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))

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
                card=re.search(r'<article class="lecture-card lecture" data-video-id="'+re.escape(row['id'])+r'".*?</article>',self.home,re.S).group(0)
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

if __name__=='__main__':unittest.main()
