"""Ensure all study leads are complete, concrete and consistent across pages."""
import json
import re
import unittest
import warnings
from pathlib import Path

R = Path(__file__).resolve().parents[1]
from sys import path as syspath
syspath.insert(0, str(R/'scripts'))
from content_registry import catalog_leads


class KoreanLeads(unittest.TestCase):
    def test_short_direct_leads_match_all_published_surfaces(self):
        import html
        from build_library import load_leads
        minis = json.loads((R/'data/mini_courses.json').read_text(encoding='utf-8'))
        summaries = catalog_leads(R)
        visible_leads = load_leads(R)
        registry = json.loads((R/'lectures.json').read_text(encoding='utf-8'))
        home = (R/'index.html').read_text(encoding='utf-8')
        self.assertEqual(set(minis), {r['id'] for r in registry})
        self.assertEqual(summaries, visible_leads, '보관 lead와 공개 첫 핵심 문장이 어긋남')
        for vid, record in minis.items():
            with self.subTest(lecture=vid):
                lead = record['lead']
                self.assertEqual(sum(lead.count(c) for c in '.!?'), 1)
                self.assertTrue(lead.endswith('다.'))
                # 35~65자는 목표다(경고). 하드 한계는 이상치만 막고, 실제 판정은 모바일 두 줄 표시 검사(tests/home-discovery.spec.cjs)가 한다.
                self.assertGreaterEqual(len(lead), 15)
                self.assertLessEqual(len(lead), 100)
                if not 35 <= len(lead) <= 65:
                    warnings.warn(f'{vid}: 한 줄 요약 {len(lead)}자(목표 35~65자)')
                self.assertFalse(re.search(r'\s{2,}', lead))
                self.assertNotRegex(lead, r'김주환은|강연자는|강의는|라고 말한다|고 말한다|살펴본다')
                self.assertFalse(lead.startswith('“'), '한 문장 인용이 아닌 직접 서술')
                text = html.escape(lead, quote=True)
                self.assertIn(f'<p class="card-lead">{text}</p>', home)
                detail = (R/'lectures'/f'{vid}.html').read_text(encoding='utf-8')
                self.assertIn(text, detail)
                self.assertIn(f'<meta name="description" content="{text}">', detail)
                self.assertIn(f'<meta property="og:description" content="{text}">', detail)


    def test_key_points_avoid_generic_speaker_recaps(self):
        records = json.loads((R/'data/lecture_compact.json').read_text(encoding='utf-8'))
        for vid, record in records.items():
            for block in record['intro']:
                if block['kind'] != 'points':
                    continue
                for item in block['items']:
                    text = item if isinstance(item, str) else item['t']
                    with self.subTest(lecture=vid, point=text):
                        self.assertNotRegex(text, r'^강연자는 .+다고 (?:설명|요약)한다[.]$')


if __name__ == '__main__':
    unittest.main()
