"""scripts/build_all.py: 화면 버전 올리기의 계약."""
import datetime,json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import argparse
from build_all import build,bump,next_version

class BuildAll(unittest.TestCase):
    def test_next_version(self):
        d=datetime.date
        self.assertEqual(next_version('2026.11.23.4',d(2026,11,23)),'2026.11.23.5')   # 같은 날은 번호만 올린다
        self.assertEqual(next_version('2026.11.23.4',d(2026,11,24)),'2026.11.24.1')   # 날짜가 바뀌면 1부터
        self.assertEqual(next_version('2026.11.9.12',d(2026,11,9)),'2026.11.09.1')    # 옛 형식(월·일 앞 0 없음)은 새 날짜로 취급
        self.assertEqual(next_version('2026.11.23.9',d(2026,11,23)),'2026.11.23.10')
    def test_bump_keeps_the_file_format(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'build-info.json').write_text(json.dumps({'version':'2026.11.23.4','change':'x'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
            v=bump('새 변경',datetime.date(2026,11,23),root=tmp)
            text=(Path(tmp)/'build-info.json').read_text(encoding='utf-8')
            self.assertEqual(v,'2026.11.23.5')
            self.assertEqual(json.loads(text),{'version':'2026.11.23.5','change':'새 변경'})
            self.assertTrue(text.endswith('\n') and text.startswith('{\n  "version"'))

    def test_failed_build_restores_the_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            info=json.dumps({'version':'2026.11.23.4','change':'x'},ensure_ascii=False,indent=2)+'\n'
            (Path(tmp)/'build-info.json').write_text(info,encoding='utf-8')
            calls=[]
            def failing(*cmd):
                calls.append(cmd)
                if len(calls)==2:raise SystemExit('실패')
            args=argparse.Namespace(bump='새 변경',check=False,tests=False)
            with self.assertRaises(SystemExit):build(args,root=tmp,runner=failing)
            self.assertEqual((Path(tmp)/'build-info.json').read_text(encoding='utf-8'),info)   # 버전만 오른 채 남지 않는다
    def test_successful_build_keeps_the_new_version_and_runs_every_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'build-info.json').write_text(json.dumps({'version':'2026.11.23.4','change':'x'})+'\n',encoding='utf-8')
            (Path(tmp)/'tests'/'sub').mkdir(parents=True);(Path(tmp)/'tests'/'sub'/'test_a.cjs').write_text('',encoding='utf-8')
            calls=[]
            args=argparse.Namespace(bump='새 변경',check=True,tests=True)
            build(args,root=tmp,runner=lambda *c:calls.append(c))
            self.assertNotEqual(json.loads((Path(tmp)/'build-info.json').read_text(encoding='utf-8'))['version'],'2026.11.23.4')
            flat=[' '.join(map(str,c)) for c in calls]
            self.assertTrue(any('build_library.py' in f for f in flat) and any('validate_site.py' in f for f in flat))
            self.assertTrue(any('node --test tests/sub/test_a.cjs' in f for f in flat))     # 하위 폴더의 노드 테스트도 돈다

if __name__=='__main__':unittest.main()
