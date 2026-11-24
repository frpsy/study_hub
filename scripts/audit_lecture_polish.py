"""윤문 전 커밋과 수치·인용·용어·원본 구조·생성 DOM 보존을 대조한다.

    python3 scripts/audit_lecture_polish.py --baseline-ref fa0b304

기계 검사는 의미의 완전한 보존을 증명하지 않는다. 문맥 검토와 함께 사용한다.
"""
import argparse
from collections import Counter
from html.parser import HTMLParser
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TERMS = ('마코프 블랭킷', '마르코프 블랭킷', '행위주의', '배경자아', '경험자아', '기억자아',
         '내면소통', '노시보', '편도체 안정화', '예측 부호화', '핑크 노이즈', '평균율', '대위법')


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append(('start', tag, [(key, re.sub(r'v=\d{4}\.\d+\.\d+\.\d+', 'v=VERSION', value)
                                        if value else value) for key, value in attrs]))

    def handle_endtag(self, tag):
        self.tags.append(('end', tag))

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)


def shape(value):
    if isinstance(value, str):
        return 'text'
    if isinstance(value, list):
        return [shape(item) for item in value]
    return {key: val if key == 'image' else shape(val) for key, val in value.items()}


def audit(ref):
    def old_file(path):
        return subprocess.check_output(['git', 'show', f'{ref}:{path}'], cwd=ROOT, text=True)
    before = json.loads(old_file('data/lecture_compact.json'))
    after = json.loads((ROOT/'data/lecture_compact.json').read_text(encoding='utf-8'))
    assert before.keys() == after.keys(), '강의 집합 변경'
    changes = []
    numbers = lambda text: Counter(re.findall(r'\d+(?:\.\d+)?', text))
    quotes = lambda text: Counter(re.findall('[“‘][^”’]+[”’]', text))
    for vid, old in before.items():
        new = after[vid]
        assert {k: v for k, v in old.items() if k != 'detail'} == {
            k: v for k, v in new.items() if k != 'detail'}, f'{vid}: 상세 외 원본 변경'
        assert shape(old['detail']) == shape(new['detail']), f'{vid}: 문단·목록·이미지 구조 변경'
        heading_changes = body_changes = 0
        for i, (a, b) in enumerate(zip(old['detail'], new['detail']), 1):
            heading_changes += a['h'] != b['h']
            for j, (x, y) in enumerate(zip(a['p'], b['p'])):
                tx = x if isinstance(x, str) else json.dumps(x, ensure_ascii=False)
                ty = y if isinstance(y, str) else json.dumps(y, ensure_ascii=False)
                location = f'{vid}#detail-{i} p{j}'
                assert numbers(tx) == numbers(ty), f'{location}: 수치 변경'
                assert not (quotes(tx) - quotes(ty)), f'{location}: 직접 인용 손실'
                for term in TERMS:
                    assert term not in tx or term in ty, f'{location}: 용어 손실 {term}'
                # 강연자 이름을 보고문에서 덜어내는 경우 외에는 영문 연구자·개념도 보존한다.
                words = lambda text: set(re.findall(r'[A-Za-zÀ-ž][A-Za-zÀ-ž-]+', text))
                assert not (words(tx) - words(ty) - {'Huberman', 'Brooks'}), f'{location}: 영문 명칭 손실'
                body_changes += x != y
        path = f'lectures/{vid}.html'
        a, b = Tags(), Tags()
        a.feed(old_file(path))
        b.feed((ROOT/path).read_text(encoding='utf-8'))
        assert a.tags == b.tags, f'{vid}: DOM 태그·속성 변경'
        changes.append({'id': vid, 'sections': len(new['detail']), 'headings_changed': heading_changes,
                        'body_blocks_changed': body_changes, 'dom_tokens_preserved': len(b.tags)})
    return changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline-ref', required=True)
    args = parser.parse_args()
    rows = audit(args.baseline_ref)
    print(json.dumps({'baseline': args.baseline_ref, 'lectures': len(rows),
                      'sections': sum(row['sections'] for row in rows),
                      'headings_changed': sum(row['headings_changed'] for row in rows),
                      'body_blocks_changed': sum(row['body_blocks_changed'] for row in rows),
                      'rows': rows}, ensure_ascii=False, indent=2))
