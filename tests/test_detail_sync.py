"""생성 표면 전체의 소제목 동기화를 회귀 검증한다."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from validate_detail_sync import labels, validate


class DetailSync(unittest.TestCase):
    def test_all_published_detail_labels_match_source_exactly(self):
        issues, lecture_count, section_count = validate()
        self.assertEqual(issues, [])
        self.assertEqual(lecture_count, 22)
        self.assertGreater(section_count, lecture_count)

    def test_nested_text_entities_and_repeated_links_are_preserved(self):
        page = labels('<h3 id="detail-1">왜 A &amp; B인가</h3>'
                      '<a href="lectures/a.html#detail-1">해당 부분 읽기 · '
                      '<span>왜 A &amp; B인가</span></a>'
                      '<a href="#detail-1">왜 A &amp; B인가</a>')
        self.assertEqual(page.headings, [('detail-1', '왜 A & B인가')])
        self.assertEqual(page.links, [('lectures/a.html#detail-1', '해당 부분 읽기 · 왜 A & B인가'),
                                      ('#detail-1', '왜 A & B인가')])
