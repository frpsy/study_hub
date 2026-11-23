"""Ensure all study leads are complete, concrete and consistent across pages."""
import json
import re
import unittest
from pathlib import Path

R = Path(__file__).resolve().parents[1]
from sys import path as syspath
syspath.insert(0, str(R/'scripts'))
from content_registry import catalog_leads


class KoreanLeads(unittest.TestCase):
    def test_archived_one_sentence_leads_keep_editorial_format(self):
        minis = json.loads((R/'data/mini_courses.json').read_text(encoding='utf-8'))
        summaries = catalog_leads(R)
        registry = json.loads((R/'lectures.json').read_text(encoding='utf-8'))
        self.assertEqual(set(minis), {r['id'] for r in registry})
        self.assertEqual(set(minis), set(summaries))
        for vid, record in minis.items():
            with self.subTest(lecture=vid):
                lead = record['lead']
                # 인용형 한 문장: 큰따옴표로 감싼 강연자 발언 한 문장(안쪽 15~170자, 마침표 하나로 끝남).
                quoted = lead.startswith('“') and lead.endswith('”')
                body = lead[1:-1] if quoted else lead
                self.assertEqual(sum(body.count(c) for c in '.!?'), 1)
                if quoted:
                    self.assertTrue(body.endswith('.'), vid)
                    self.assertNotIn('“', body, vid)
                    self.assertNotIn('”', body, vid)
                    self.assertGreaterEqual(len(body), 15, vid)
                else:
                    self.assertTrue(lead.endswith('다.'), vid)
                    self.assertGreaterEqual(len(lead), 55, vid)
                self.assertLessEqual(len(body), 170, vid)
                self.assertFalse(re.search(r'\s{2,}', lead), vid)
                self.assertEqual(lead, summaries[vid], '카탈로그의 한 문장과 다름: '+vid)



if __name__ == '__main__':
    unittest.main()
