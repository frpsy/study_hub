"""Reading effort follows visible summary content, not video or editorial data."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from reading_text import reading_minutes

class ReadingEstimate(unittest.TestCase):
    def test_absent_content_has_no_invented_estimate(self):
        self.assertIsNone(reading_minutes({'timeline': '가' * 5000}))

    def test_only_published_summary_contributes(self):
        record = {'intro': [{'kind': 'points', 'h': '요점', 'items': ['핵심 주장이다.']}],
                  'detail': [{'h': '질문', 'p': ['설명이다.']}]}
        short = reading_minutes(record)
        record.update(timeline='가' * 10000, editor=[{'items': ['가' * 10000]}])
        record['intro'].append({'kind': 'practice', 'h': '숨긴 실천', 'items': ['가' * 10000]})
        self.assertEqual(short, reading_minutes(record))
        record['detail'][0]['p'].append({'list': [{'l': '근거', 't': '가' * 1500}]})
        self.assertGreater(reading_minutes(record), short)
