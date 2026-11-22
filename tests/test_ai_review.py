"""다중 AI 문장 검수 도구(scripts/ai_review) 단위 테스트. 규칙: docs/ai-review-workflow.md"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from ai_review.apply import apply_edit
from ai_review.batches import make_batches
from ai_review.mech_check import check_lead, check_three, check_forbidden
from ai_review.merge import merge
from ai_review.prompt import build_prompt
from ai_review.run_chatgpt import run_chatgpt
from ai_review.run_gemini import run_gemini
from ai_review.screen import screen_item
from ai_review.validate_output import parse_output, validate_items


# ---- mech_check ----
class TestLead(unittest.TestCase):
    def test_plain_lead_ok(self):
        # 68자, 쉼표 없음, '다.'로 끝남
        self.assertEqual(
            check_lead("자기 목소리를 들을 때 뇌는 평생 익숙해진 특징만 골라 처리하므로 녹음된 목소리는 늘 낯설게 들린다는 점을 기억해야 한다."),
            [],
        )

    def test_quoted_lead_uses_quote_rule(self):
        # Review Focus 1: 인용형은 15–170자, 안쪽 마침표 1개
        self.assertEqual(check_lead("“녹음한 내 목소리가 남들이 듣는 내 목소리예요.”"), [])

    def test_too_many_commas_fails(self):
        self.assertTrue(check_lead("뇌는 예측하고, 낯설게 들리며, 믿지 않는다. 그래서 말을 아끼고 천천히 생각하는 연습을 해야 하는 이유가 여기에 있다."))


class TestThree(unittest.TestCase):
    def test_three_items_ok(self):
        self.assertEqual(
            check_three([
                "뇌는 평생 들은 내 목소리를 핵심 특징만 골라 처리한다.",
                "말하기 직전 뇌는 예측 신호로 청각 반응을 낮춘다.",
                "직접 녹음한 대본은 저음을 키워 들으면 낯섦이 줄어든다.",
            ]),
            [],
        )

    def test_wrong_count_fails(self):
        # Review Focus 2
        self.assertTrue(check_three(["가다."] * 2))

    def test_empty_item_fails(self):
        self.assertTrue(check_three(["가다.", "", "나다."]))


class TestForbidden(unittest.TestCase):
    def test_kim_lecture_forbids_lecturer_subject(self):
        self.assertTrue(check_forbidden("강사는 이렇게 말한다.", "김주환"))

    def test_other_creator_allowed(self):
        self.assertEqual(check_forbidden("강사는 이렇게 말한다.", "Andrew Huberman"), [])


# ---- batches ----
PILOT = ["2VTv6WW8Kn8", "kLizfh-5vuE", "MdDj5RZkMB4"]


class TestBatches(unittest.TestCase):
    def test_seven_batches_of_three_cover_all_once(self):
        ids = [f"id{i:02d}" for i in range(18)] + PILOT  # 21개
        b = make_batches(ids, PILOT)
        self.assertEqual(len(b), 7)
        self.assertTrue(all(len(x) == 3 for x in b))
        flat = [i for x in b for i in x]
        self.assertEqual(sorted(flat), sorted(ids))

    def test_pilot_is_first_batch(self):
        ids = [f"id{i:02d}" for i in range(18)] + PILOT
        self.assertEqual(make_batches(ids, PILOT)[0], PILOT)

    def test_wrong_total_raises(self):
        with self.assertRaises(ValueError):
            make_batches(["a", "b"], [])


# ---- validate_output ----
SRC = {"lead": "자기 목소리를 들을 때 뇌는 익숙한 특징만 고른다."}
GOOD = {
    "lecture_id": "2VTv6WW8Kn8",
    "field": "lead",
    "original": "자기 목소리를 들을 때 뇌는 익숙한 특징만 고른다.",
    "suggestion": "자기 목소리를 들을 때 뇌는 익숙한 특징만 골라 처리한다.",
    "type": "어색한 연결",
    "reason": "서술어 정리",
    "meaning_change": False,
    "confidence": "높음",
}


class TestParse(unittest.TestCase):
    def test_non_json_returns_none(self):
        self.assertIsNone(parse_output("죄송합니다, 검수할 수 없습니다."))  # Review Focus 4

    def test_json_array_parsed(self):
        self.assertEqual(parse_output('[{"a":1}]'), [{"a": 1}])

    def test_fenced_json_parsed(self):
        self.assertEqual(parse_output('```json\n[{"a":1}]\n```'), [{"a": 1}])


class TestValidate(unittest.TestCase):
    def test_good_item_passes(self):
        self.assertEqual(validate_items([GOOD], SRC), [])

    def test_quote_not_in_source_fails(self):
        bad = dict(GOOD, original="없는 문장이다.")
        self.assertTrue(validate_items([bad], SRC))  # Review Focus 4

    def test_missing_key_fails(self):
        bad = {k: v for k, v in GOOD.items() if k != "type"}
        self.assertTrue(validate_items([bad], SRC))

    def test_bad_type_enum_fails(self):
        self.assertTrue(validate_items([dict(GOOD, type="기타")], SRC))

    def test_optional_practice_absent_is_not_error(self):
        # Review Focus 3: 선택 필드가 없는 강의는 항목이 없어도 오류가 아니다
        self.assertEqual(validate_items([], {}), [])


# ---- merge ----
def item(field, sug, meaning=False, typ="어색한 연결"):
    return {"lecture_id": "X", "field": field, "original": "o", "suggestion": sug,
            "type": typ, "reason": "r", "meaning_change": meaning, "confidence": "높음"}


class TestMerge(unittest.TestCase):
    def test_same_suggestion_is_adopt_candidate(self):
        r = merge([item("lead", "가")], [item("lead", "가")])
        self.assertEqual(len(r["adopt_candidates"]), 1)

    def test_one_side_only_goes_to_review(self):
        r = merge([item("lead", "가")], [])
        self.assertEqual(len(r["review"]), 1)

    def test_different_suggestions_are_conflict(self):
        r = merge([item("lead", "가")], [item("lead", "나")])
        self.assertEqual(len(r["conflict"]), 1)

    def test_meaning_change_always_user_queue(self):
        r = merge([item("lead", "가", meaning=True)], [item("lead", "가", meaning=True)])
        self.assertEqual(len(r["user_queue"]), 1)
        self.assertEqual(r["adopt_candidates"], [])


# ---- prompt ----
class TestBlind(unittest.TestCase):
    def test_prompt_contains_no_other_reviewer_output(self):
        p = build_prompt(["2VTv6WW8Kn8"], "chatgpt")
        self.assertNotIn("gemini", p.lower())  # Review Focus: 2차는 1차 결과를 보지 않는다
        self.assertIn("2VTv6WW8Kn8", p)

    def test_prompt_has_rules_from_spec(self):
        p = build_prompt(["2VTv6WW8Kn8"], "gemini")
        for rule in ["60", "120", "쉼표", "강사는", "meaning_change"]:
            self.assertIn(rule, p)


class TestRunnerFailures(unittest.TestCase):
    # Review Focus 5: 키나 도구가 없으면 조용히 넘어가지 않고 failed로 기록한다
    def test_gemini_missing_key_records_failed(self):
        with tempfile.TemporaryDirectory() as out:
            ok = run_gemini("x", out, env_path=os.path.join(out, "no-such.env"), wrapper="/nonexistent/ai-gemini.sh")
            self.assertFalse(ok)
            with open(os.path.join(out, "status.json"), encoding="utf-8") as f:
                status = json.load(f)
            self.assertEqual(status["status"], "failed")
            self.assertIn("key", status["reason"])

    def test_chatgpt_missing_binary_records_failed(self):
        with tempfile.TemporaryDirectory() as out:
            ok = run_chatgpt("x", out, codex_bin="/nonexistent/codex")
            self.assertFalse(ok)
            with open(os.path.join(out, "status.json"), encoding="utf-8") as f:
                status = json.load(f)
            self.assertEqual(status["status"], "failed")


# ---- pilot lessons (Task 7) ----
def _it(field, original, suggestion):
    return {"lecture_id": "X", "field": field, "original": original, "suggestion": suggestion,
            "type": "어색한 연결", "reason": "r", "meaning_change": False, "confidence": "높음"}


class TestPilotPromptRules(unittest.TestCase):
    def setUp(self):
        self.p = build_prompt(["2VTv6WW8Kn8"], "gemini")

    def test_prompt_keeps_quoted_lead_words(self):
        self.assertIn("인용형 `lead`는 원문 낱말", self.p)

    def test_prompt_defines_typo_label(self):
        self.assertIn("오탈자는", self.p)

    def test_prompt_cap_is_per_lecture(self):
        self.assertIn("강의마다 최대 10개", self.p)

    def test_prompt_forbids_translationese_in_suggestion(self):
        self.assertIn("제안 문장에도", self.p)

    def test_prompt_requires_minimal_original(self):
        self.assertIn("최소 구절", self.p)


class TestScreen(unittest.TestCase):
    def test_quoted_lead_rewrite_rejected(self):
        src = "“감사는 가장 쉽게 할 수 있고요.”"
        self.assertIn("인용형", screen_item(_it("lead", src, "“감사는 일상에서 가장 쉽게 시작할 수 있습니다.”"), src))

    def test_translationese_added_rejected(self):
        src = "결국 상대를 무시하는 데로 모인다는 설명이다."
        self.assertIn("번역투", screen_item(_it("detail[1].p[0]", src, "결국 상대에 대한 무시로 귀결된다는 설명이다."), src))

    def test_translationese_already_in_original_not_rejected(self):
        src = "상대에 대한 무시가 문제다."
        self.assertIsNone(screen_item(_it("detail[0].p[0]", src, "상대에 대한 무시가 큰 문제다."), src))

    def test_no_change_rejected(self):
        src = "가나다라마바사다."
        self.assertIsNotNone(screen_item(_it("detail[0].p[0]", src, src), src))

    def test_three_suggestion_breaking_length_rejected(self):
        src = "짧은 문장이다."
        self.assertIn("기계 점검", screen_item(_it("three[0]", src, "가" * 95 + "다."), src))

    def test_plain_good_suggestion_passes(self):
        src = "샐리가 어디부터 찾을지 묻는다."
        self.assertIsNone(screen_item(_it("detail[4].p[0]", "어디부터", "어디에서부터"), src))


    def test_duplicate_full_sentence_rewrite_rejected(self):
        # 원문 일부만 바꾸라는 제안이 문장 전체를 다시 쓰면 같은 구절이 두 번 나온다.
        src = "앞 문장이다. 『알아차림에 대한 알아차림』 역자 서문에 따르면 두 단계는 방향이다."
        sug = "『알아차림에 대한 알아차림』 역자 서문에 따르면 두 단계는 높낮이가 아니라 방향이다."
        self.assertIn("중복 생성", screen_item(_it("detail[5].p[0]", "두 단계는 방향이다.", sug), src))

    def test_title_quote_not_counted_as_translationese(self):
        src = "책 제목을 알려 준다."
        self.assertIsNone(screen_item(_it("detail[5].p[0]", "책 제목을 알려 준다.", "『알아차림에 대한 알아차림』을 알려 준다."), src))

    def test_minimal_substring_edit_passes(self):
        src = "앞 문장이다. 이 울음의 원인을 제도에서 찾는다."
        self.assertIsNone(screen_item(_it("detail[0].p[0]", "제도에서 찾는다.", "제도에 있다고 짚는다."), src))


# ---- apply ----
def _data():
    mini = {"L": {"lead": "가나다라는 문장이다.", "three": ["하나다.", "둘이다.", "셋이다."]}}
    compact = {"L": {"detail": [{"h": "제목", "p": ["첫 문단이다.", "둘째 문단에서 어디부터 찾는다."]}],
                     "practice": {"today": ["오늘 하기"], "steps": [{"h": "단계", "t": "1:00", "b": ["가다.", "‘온전하다’ 되뇌기"]}]}}}
    return mini, compact


class TestApply(unittest.TestCase):
    def test_lead_replaced(self):
        mini, compact = _data()
        apply_edit(mini, compact, "L", "lead", "가나다라는", "가나다라마는")
        self.assertEqual(mini["L"]["lead"], "가나다라마는 문장이다.")

    def test_detail_paragraph_path(self):
        mini, compact = _data()
        apply_edit(mini, compact, "L", "detail[0].p[1]", "어디부터", "어디에서부터")
        self.assertEqual(compact["L"]["detail"][0]["p"][1], "둘째 문단에서 어디에서부터 찾는다.")

    def test_practice_step_body_path(self):
        mini, compact = _data()
        apply_edit(mini, compact, "L", "practice.steps[0].b[1]", "’ 되뇌기", "’고 되뇌기")
        self.assertEqual(compact["L"]["practice"]["steps"][0]["b"][1], "‘온전하다’고 되뇌기")

    def test_three_item_path(self):
        mini, compact = _data()
        apply_edit(mini, compact, "L", "three[2]", "셋이다.", "셋째다.")
        self.assertEqual(mini["L"]["three"][2], "셋째다.")

    def test_missing_original_raises(self):
        mini, compact = _data()
        with self.assertRaises(ValueError):
            apply_edit(mini, compact, "L", "lead", "없는 말", "새 말")

    def test_ambiguous_original_raises(self):
        mini, compact = _data()
        mini["L"]["lead"] = "같다 같다."
        with self.assertRaises(ValueError):
            apply_edit(mini, compact, "L", "lead", "같다", "다르다")


if __name__ == "__main__":
    unittest.main()
