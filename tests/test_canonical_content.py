"""Regression contracts for canonical summaries and catalog source records."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from content_registry import catalog_leads, validate_catalog, load_json


class CanonicalContentRegression(unittest.TestCase):
    def test_every_lecture_has_one_lead_shown_on_its_page(self):
        courses=load_json(ROOT/"data/mini_courses.json")
        leads=catalog_leads(ROOT)
        self.assertEqual(leads,{k:v["lead"] for k,v in courses.items()})
        for vid,course in courses.items():
            with self.subTest(lecture=vid):
                self.assertEqual(set(course),{"title","lead"},"옛 원고 필드는 docs/archive/manuscripts에 있다")
                self.assertIn(course["lead"],(ROOT/"lectures"/f"{vid}.html").read_text(encoding="utf-8"))

    def test_lead_coverage_mismatch_fails_explicitly(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"data").mkdir()
            (root/"lectures.json").write_text(json.dumps([{"id":"one"}]),encoding="utf-8")
            (root/"data/mini_courses.json").write_text(json.dumps({"one":{"lead":"correct"}}),encoding="utf-8")
            self.assertEqual(catalog_leads(root),{"one":"correct"})
            (root/"data/mini_courses.json").write_text("{}",encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"coverage"):catalog_leads(root)

    def test_archived_manuscripts_are_kept_and_not_published_data(self):
        archive=ROOT/"docs/archive/manuscripts"
        self.assertEqual(set(load_json(archive/"summaries.json")),set(load_json(ROOT/"data/mini_courses.json")))
        self.assertEqual(set(load_json(archive/"mini-course-extras.json")),set(load_json(ROOT/"data/mini_courses.json")))
        self.assertFalse((ROOT/"data/summaries.json").exists())

    def test_catalog_has_unique_ids_and_required_metadata(self):
        self.assertEqual(validate_catalog(ROOT),[])
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            row={"id":"duplicate","title":"Test","creator":"Speaker","description":"Description","tags":["topic"]}
            (root/"lectures.json").write_text(json.dumps([row]),encoding="utf-8")
            (root/"materials.json").write_text(json.dumps([{**row,"kind":"book","url":"books/one.html"}]),encoding="utf-8")
            self.assertIn("Duplicate stable content ID in registry",validate_catalog(root))


if __name__=="__main__":
    unittest.main()
