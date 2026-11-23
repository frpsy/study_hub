"""scripts/quote_check.py: 인용 대조의 기준 동작을 고정한다(양성·음성 예)."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from quote_check import load_transcript,norm,quote_problems,stamp_label,stamp_seconds,transcript_path,video_key

LINES=[(60,'진흙탕에 발이 빠졌을 때'),(63,'이게 무슨 뜻이냐면 우리가 아'),(66,'빠졌으니까 어떻게 해야 돼?'),(69,'빨리 발을 꺼내야겠네.'),(72,'그럼 어떻게 해야 돼?'),(75,'피해를 빨리 복구해야겠네.'),(400,'전혀 다른 이야기를 합니다 지금은')]

class QuoteCheck(unittest.TestCase):
    def test_stamps_round_trip(self):
        for label in ('0:05','31:13','1:20:44','1:02:07'):
            self.assertEqual(stamp_label(stamp_seconds(label)),label)
        self.assertEqual(norm('빠졌으니까, 어떻게 해야 돼?'),'빠졌으니까어떻게해야돼')
    def test_exact_and_edited_quotes_pass(self):
        self.assertEqual(quote_problems('빠졌으니까 어떻게 해야 돼? 빨리 발을 꺼내야겠네.',LINES,66),[])
        self.assertEqual(quote_problems('빠졌으니까 어떻게 해야 돼? … 피해를 빨리 복구해야겠네.',LINES,66),[])   # 생략은 ‘…’
        self.assertEqual(quote_problems('빠졌으니까어떻게해야돼 빨리발을꺼내야겠네',LINES,66),[])             # 띄어쓰기 차이
    def test_invented_reordered_or_far_quotes_fail(self):
        self.assertTrue(quote_problems('빠졌으니까 어떻게 해야 돼? 절대 포기하세요.',LINES,66))                  # 없는 낱말
        self.assertTrue(quote_problems('빨리 발을 꺼내야겠네. 빠졌으니까 어떻게 해야 돼?',LINES,66))            # 순서 뒤집힘
        self.assertTrue(quote_problems('전혀 다른 이야기를 합니다 지금은',LINES,66))                            # 75초 밖의 말을 가져다 붙임
        self.assertTrue(quote_problems('짧다',LINES,66))                                                       # 너무 짧음
        self.assertEqual(quote_problems('아무 말이나 길게 써 본다',[],66),['그 시각 앞뒤에 자막이 없다'])
    def test_repeated_words_cannot_borrow_each_other(self):
        # ‘어떻게 해야 돼’는 두 번 나온다. 한 번만 있는 말을 두 번 쓰면 실패해야 한다.
        self.assertEqual(quote_problems('어떻게 해야 돼? … 어떻게 해야 돼?',LINES,66),[])
        self.assertTrue(quote_problems('빨리 발을 꺼내야겠네. … 빨리 발을 꺼내야겠네.',LINES,66))
    def test_dropping_text_requires_an_ellipsis(self):
        lines=[(10,'오늘은 사과를 먹고 아주 길고 긴 이야기를 한참 하다가 마침내 운동을 시작하세요')]
        self.assertTrue(quote_problems('오늘은 사과를 운동을 시작하세요',lines,10))             # 중간을 말없이 건너뜀
        self.assertEqual(quote_problems('오늘은 사과를 … 운동을 시작하세요',lines,10),[])      # ‘…’로 표시하면 통과
        near=[(10,'걸어다니고 막 그 심장 박동을 이렇게 하고 운동을 하면')]
        self.assertEqual(quote_problems('걸어 다니고 심장 박동을 이렇게 하고 운동을 하면',near,10),[])   # ‘막 그’ 정도의 군더더기는 허용
    def test_bom_on_first_line_is_ignored(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'a.ko.txt';path.write_text('\ufeff[0:00:01] 첫 줄\n[0:00:05] 둘째 줄\n',encoding='utf-8')
            self.assertEqual(load_transcript(path),[(1,'첫 줄'),(5,'둘째 줄')])
    def test_repo_transcripts_load(self):
        root=Path(__file__).resolve().parents[1]
        row={'id':'ZCty0wvogDo'}
        path=transcript_path(root,row);self.assertIsNotNone(path)
        lines=load_transcript(path);self.assertGreater(len(lines),500)
        self.assertEqual(video_key({'id':'x','video_url':'https://www.youtube.com/watch?v=abcdefghijk'}),'abcdefghijk')
        self.assertEqual(video_key({'id':'chance'}),'chance')

if __name__=='__main__':unittest.main()
