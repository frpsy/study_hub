"""원본 소제목과 상세 본문·목차·홈 검색 링크의 문자열 및 앵커를 전수 대조한다."""
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class Labels(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.headings = []
        self.links = []
        self.active = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if self.active:
            self.depth += 1
        elif tag == 'h3' and re.fullmatch(r'detail-\d+', attrs.get('id', '')):
            self.active = ('heading', attrs['id'], [])
            self.depth = 1
        elif tag == 'a' and re.search(r'#detail-\d+$', attrs.get('href', '')):
            self.active = ('link', attrs['href'], [])
            self.depth = 1

    def handle_endtag(self, tag):
        if self.active:
            self.depth -= 1
            if not self.depth:
                kind, key, chunks = self.active
                target = self.headings if kind == 'heading' else self.links
                target.append((key, ''.join(chunks)))
                self.active = None

    def handle_data(self, data):
        if self.active:
            self.active[2].append(data)


def labels(text):
    parser = Labels()
    parser.feed(text)
    return parser


def validate(root=ROOT):
    source = json.loads((root/'data/lecture_compact.json').read_text(encoding='utf-8'))
    registry = json.loads((root/'lectures.json').read_text(encoding='utf-8'))
    home = labels((root/'index.html').read_text(encoding='utf-8'))
    expected_home = []
    issues = []
    count = 0
    for lecture in registry:
        vid = lecture['id']
        sections = source[vid]['detail']
        expected = [(f'detail-{i}', section['h']) for i, section in enumerate(sections, 1)]
        page = labels((root/'lectures'/f'{vid}.html').read_text(encoding='utf-8'))
        if page.headings != expected:
            issues.append(f'{vid}: 본문 소제목/id 불일치')
        # 목차는 각 소제목을 정확히 한 번 가리켜야 한다.
        toc = [(href[1:], text) for href, text in page.links if href.startswith('#detail-')]
        if toc != expected:
            issues.append(f'{vid}: 상세 목차 불일치')
        expected_home.extend((f'lectures/{vid}.html#{anchor}', f'해당 부분 읽기 · {heading}')
                             for anchor, heading in expected)
        for _, heading in expected:
            if not heading.endswith(('가', '까')):
                issues.append(f'{vid}: 질문형이 아닌 소제목: {heading}')
        count += len(expected)
    if Counter(home.links) != Counter(expected_home):
        issues.append('홈 #detail-* 링크의 소제목·앵커·개수 불일치')
    return issues, len(registry), count


if __name__ == '__main__':
    issues, lectures, count = validate()
    for issue in issues:
        print('FAIL:', issue)
    if issues:
        raise SystemExit(1)
    print(f'PASS: {lectures}편, {count}개 소제목 — 원본·홈 링크·상세 목차·본문 100% 일치')
