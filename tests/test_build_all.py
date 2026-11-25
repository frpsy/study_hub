"""scripts/build_all.py와 자산 해시 버전의 계약."""
import argparse,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_all import build
from build_library import ASSET_FILES,asset_version

class BuildAll(unittest.TestCase):
    def test_every_stage_runs_in_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp)/'tests'/'sub').mkdir(parents=True);(Path(tmp)/'tests'/'sub'/'test_a.cjs').write_text('',encoding='utf-8')
            calls=[]
            build(argparse.Namespace(check=True,tests=True),root=tmp,runner=lambda *c:calls.append(c))
            flat=[' '.join(map(str,c)) for c in calls]
            self.assertTrue('build_library.py' in flat[0] and 'build_compact_lectures.py' in flat[1])
            self.assertTrue(any('validate_site.py' in f for f in flat))
            self.assertTrue(any('node --test tests/sub/test_a.cjs' in f for f in flat))

class AssetVersion(unittest.TestCase):
    def make_root(self,tmp):
        root=Path(tmp)
        for name in ASSET_FILES:
            (root/name).parent.mkdir(parents=True,exist_ok=True);(root/name).write_bytes(name.encode())
        return root
    def test_version_follows_asset_content_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(tmp)
            first=asset_version(root)
            (root/'lectures').mkdir();(root/'lectures'/'a.html').write_text('문구가 바뀜',encoding='utf-8')
            (root/'data.json').write_text('{}',encoding='utf-8')
            self.assertEqual(asset_version(root),first)        # 문구·데이터는 버전을 바꾸지 않는다
            (root/'assets/site.css').write_text('a{color:red}',encoding='utf-8')
            self.assertNotEqual(asset_version(root),first)     # 자산이 바뀌면 버전이 바뀐다
    def test_line_endings_do_not_change_the_version(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=self.make_root(tmp)
            (root/'assets/site.js').write_bytes(b'a\nb\n');lf=asset_version(root)
            (root/'assets/site.js').write_bytes(b'a\r\nb\r\n')
            self.assertEqual(asset_version(root),lf)

if __name__=='__main__':unittest.main()
