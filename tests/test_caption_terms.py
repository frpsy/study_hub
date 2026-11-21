"""용어집(용어집.md)의 ‘점검할 표현’이 공개 본문에 남아 있지 않은지 검사한다.

자동 자막은 ‘배경자아’를 ‘배경자’로, ‘개별적인 자아’를 ‘개별적인 자’로 적는 식으로 음절을 빠뜨린다.
눈으로만 고치면 일부를 놓치므로 용어집의 별칭을 기계적으로 막는다. 편집자 주(editor)와 출처(sources)는
정정 내용을 설명하는 곳이라 검사하지 않는다.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# 용어집에 없어도 자막에서 자주 음절이 빠지는 고정 패턴(‘…자아’의 ‘아’ 누락).
ORPHAN_JA = re.compile(r'(개별적인|개인적인|진정한|참된|가짜|거짓)\s자(?:를|는|가|의|로|와|도|만|이)?(?![가-힣])')

# 직접 인용이나 사람을 가리키는 용례처럼 별칭이 맞게 쓰인 곳은 (강의 id, 맥락) 쌍으로 허용한다.
ALLOW = set()


def glossary_rules():
    rules = []
    for line in (ROOT / '용어집.md').read_text(encoding='utf-8').splitlines():
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        if len(cells) < 3 or cells[0] in ('표준 표기', '---') or set(cells[0]) <= {'-'}:
            continue
        standard = cells[0]
        for alias in [a.strip() for a in cells[1].split(',') if a.strip()]:
            if alias.replace(' ', '') == standard.replace(' ', ''):
                continue  # 띄어쓰기만 다른 표기는 허용한다.
            if standard.startswith(alias):
                rest = standard[len(alias):]
                pattern = re.compile(re.escape(alias) + (f'(?!{re.escape(rest)})' if rest else ''))
            else:
                pattern = re.compile(re.escape(alias))
            rules.append((standard, alias, pattern))
    return rules


# 편집규칙: 이미 올라간 김주환 강의의 타임스탬프는 고치지 않는다. 타임스탬프 검사는 이 날짜 이후에 추가된 강의에만 적용한다.
TIMELINE_CHECK_FROM = '2026-11-21'


def public_texts(lecture_id, lectures, compact, minis, summaries):
    """공개 본문 문자열을 (필드 이름, 문자열)로 돌려준다. editor와 sources는 제외한다."""
    def walk(x, name):
        if isinstance(x, str):
            yield name, x
        elif isinstance(x, dict):
            for k, v in x.items():
                yield from walk(v, f'{name}.{k}')
        elif isinstance(x, list):
            for i, v in enumerate(x):
                yield from walk(v, f'{name}[{i}]')

    row = next(r for r in lectures if r['id'] == lecture_id)
    for key in ('title', 'description', 'tags'):
        if key in row:
            yield from walk(row[key], f'lectures.{key}')
    for key in ('title', 'lead', 'three', 'sections', 'question', 'answer'):
        if key in minis.get(lecture_id, {}):
            yield from walk(minis[lecture_id][key], f'mini.{key}')
    yield from walk(summaries.get(lecture_id, {}), 'summaries')
    for key, value in compact.get(lecture_id, {}).items():
        if key in ('editor', 'sources', 'aliases'):
            continue
        if key == 'timeline' and row.get('added', '') < TIMELINE_CHECK_FROM:
            continue
        yield from walk(value, f'compact.{key}')


class CaptionTermsTest(unittest.TestCase):
    def test_glossary_aliases_and_orphan_syllables_do_not_remain_in_public_text(self):
        lectures = json.loads((ROOT / 'lectures.json').read_text(encoding='utf-8'))
        compact = json.loads((ROOT / 'data/lecture_compact.json').read_text(encoding='utf-8'))
        minis = json.loads((ROOT / 'data/mini_courses.json').read_text(encoding='utf-8'))
        summaries = json.loads((ROOT / 'data/summaries.json').read_text(encoding='utf-8'))
        rules = glossary_rules()
        self.assertTrue(rules, '용어집 표를 읽지 못했다')
        problems = []
        for row in lectures:
            lecture_id = row['id']
            for field, text in public_texts(lecture_id, lectures, compact, minis, summaries):
                for standard, alias, pattern in rules:
                    for m in pattern.finditer(text):
                        context = text[max(0, m.start() - 8):m.end() + 8]
                        if (lecture_id, context) not in ALLOW:
                            problems.append(f'{lecture_id} {field}: ‘{alias}’ → ‘{standard}’ … {context}')
                for m in ORPHAN_JA.finditer(text):
                    context = text[max(0, m.start() - 8):m.end() + 8]
                    if (lecture_id, context) not in ALLOW:
                        problems.append(f'{lecture_id} {field}: 음절이 빠진 ‘자’ 의심 … {context}')
        self.assertEqual(problems, [], '\n'.join(problems[:20]))

    def test_glossary_contains_the_terms_found_in_lecture_two_stages(self):
        standards = {r[0] for r in glossary_rules()}
        for term in ('배경자아', '경험자아', '기억자아', '개별적인 자아'):
            self.assertIn(term, standards)


if __name__ == '__main__':
    unittest.main()
