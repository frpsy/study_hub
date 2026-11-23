"""scripts/intro_candidates.py: 권유형 후보 추출(탐색 전용)의 계약."""
import json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from intro_candidates import candidates,lead_overlap,used_times

KO=[(10,'오늘은 수용을 설명합니다'),(20,'여러분 지금 바로 숨을 고르세요'),(24,'그리고 천천히 내쉬세요'),(90,'이건 하지 마세요'),(200,'그냥 설명입니다')]
EN=[(5,'I think it is interesting'),(30,'You should get light in the morning'),(33,'And you should avoid caffeine')]

class IntroCandidates(unittest.TestCase):
    def test_korean_directives_are_grouped_by_gap(self):
        got=candidates(KO,'ko',gap=20)
        self.assertEqual([g[0] for g in got],[20,90])       # 20초와 24초는 한 후보로 묶인다
        self.assertIn('내쉬세요',got[0][2])                   # 맥락에 뒷줄이 들어온다
    def test_english_directives(self):
        got=candidates(EN,'en',gap=10)
        self.assertEqual([g[0] for g in got],[30])
    def test_plain_explanations_are_not_candidates(self):
        self.assertEqual(candidates([(1,'오늘은 날씨가 좋습니다'),(5,'그렇습니다')],'ko'),[])
    def test_spacing_variants_of_the_same_directive(self):
        for text in ('하지마세요','꼭 해야돼요','해주세요 부탁'):
            self.assertTrue(candidates([(1,text)],'ko'),text)
    def test_short_lead_overlap_and_chain_grouping(self):
        self.assertTrue(lead_overlap('매일 기록하세요','네 매일 기록하세요 알겠죠'))        # 12자 미만 한 문장도 통째로 겹치면 겹침
        self.assertFalse(lead_overlap('','아무 말'))
        chain=[(0,'하세요 하나'),(15,'하세요 둘'),(30,'하세요 셋')]
        self.assertEqual([g[0] for g in candidates(chain,'ko',gap=20)],[0,30])             # 첫 적중 기준(긴 구간은 gap초마다 하나)
    def test_lead_overlap_and_used_times(self):
        self.assertTrue(lead_overlap('일단 벌어진 거예요, 지금 발이 빠졌어요.','네 일단 벌어진 거예요 지금 발이 빠졌어요 그럼'))
        self.assertFalse(lead_overlap('일단 벌어진 거예요, 지금 발이 빠졌어요.','전혀 다른 말'))
        rec={'intro':[{'kind':'points','h':'h','items':['a']},{'kind':'practice','h':'h','items':[{'t':'1:05'},{'t':'2:00:10'}]}]}
        self.assertEqual(used_times(rec),[65,7210])
        self.assertEqual(used_times({}),[])
    def test_cli_runs_on_every_lecture_with_a_transcript(self):
        import subprocess
        root=Path(__file__).resolve().parents[1]
        rows=json.loads((root/'lectures.json').read_text(encoding='utf-8'))
        for row in rows:
            out=subprocess.run([sys.executable,str(root/'scripts/intro_candidates.py'),row['id'],'--json'],capture_output=True,text=True)
            self.assertEqual(out.returncode,0,row['id']+out.stderr)
            data=json.loads(out.stdout)
            self.assertIsInstance(data,list,row['id'])
            self.assertTrue(all({'t','line','context','overlaps_lead','already_used'}<=set(d) for d in data),row['id'])

if __name__=='__main__':unittest.main()
