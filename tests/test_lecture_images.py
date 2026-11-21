import json, struct, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def jpeg_size(path):
    data = path.read_bytes()
    assert data[:2] == b'\xff\xd8', 'JPEG가 아니다'
    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            i += 1
            continue
        marker = data[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack('>HH', data[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack('>H', data[i + 2:i + 4])[0]
    raise AssertionError('JPEG 크기를 찾지 못했다')


class LectureImageTest(unittest.TestCase):
    def rows(self):
        return [r for r in json.loads((ROOT / 'lectures.json').read_text(encoding='utf-8')) if r.get('image')]

    def test_images_are_small_local_jpegs_with_alt_and_size(self):
        for row in self.rows():
            img = row['image']
            self.assertEqual(img['src'], f"assets/lectures/{row['id']}.jpg", row['id'])
            path = ROOT / img['src']
            self.assertTrue(path.is_file(), row['id'])
            self.assertLessEqual(path.stat().st_size, 450_000, row['id'] + ' 이미지가 450KB를 넘는다')
            self.assertTrue(img['alt'].strip() and len(img['alt']) <= 120, row['id'] + ' alt')
            self.assertEqual((img['width'], img['height']), jpeg_size(path), row['id'] + ' 크기')

    def test_lecture_page_shows_the_hero_before_reading_nav(self):
        for row in self.rows():
            html = (ROOT / 'lectures' / f"{row['id']}.html").read_text(encoding='utf-8')
            self.assertIn('<figure class="lecture-hero">', html)
            self.assertIn(f"../{row['image']['src']}", html)
            self.assertLess(html.index('lecture-hero'), html.index('class="reading-nav"'))

    def test_only_registered_lectures_have_a_hero(self):
        ids = {r['id'] for r in self.rows()}
        for page in (ROOT / 'lectures').glob('*.html'):
            has = 'class="lecture-hero"' in page.read_text(encoding='utf-8')
            self.assertEqual(has, page.stem in ids, page.name)


if __name__ == '__main__':
    unittest.main()
