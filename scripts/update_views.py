#!/usr/bin/env python3
"""lectures.json의 각 강의에 유튜브 조회수(views)와 확인일(views_checked)을 기록한다.

홈의 '조회수순' 정렬이 이 값을 쓴다. 조회수는 returnyoutubedislikeapi.com의 공개 응답(viewCount)에서 읽는다.
- 가져오지 못한 영상은 기존 값을 그대로 두고, 값이 없으면 비워 둔다(지어내지 않는다).
- 사용: python3 scripts/update_views.py [--dry-run]
- 갱신 후 python3 scripts/build_library.py 로 홈을 다시 만든다.
"""
import datetime, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = 'https://returnyoutubedislikeapi.com/votes?videoId='
VIDEO_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')


def video_id(row):
    query = urllib.parse.parse_qs(urllib.parse.urlparse(row.get('video_url') or '').query)
    candidate = (query.get('v') or [row['id']])[0]
    return candidate if VIDEO_ID.match(candidate) else None


def fetch_views(vid):
    request = urllib.request.Request(API + vid, headers={'User-Agent': 'study-hub-views/1.0'})
    with urllib.request.urlopen(request, timeout=20) as response:
        data = json.load(response)
    count = data.get('viewCount')
    return count if isinstance(count, int) and count >= 0 and not data.get('deleted') else None


def main():
    dry = '--dry-run' in sys.argv
    path = ROOT / 'lectures.json'
    rows = json.loads(path.read_text(encoding='utf-8'))
    today = datetime.date.today().isoformat()
    updated = failed = 0
    for row in rows:
        vid = video_id(row)
        if not vid:
            print('건너뜀(유튜브 영상 아님):', row['id'])
            continue
        try:
            count = fetch_views(vid)
        except Exception as error:  # 네트워크 오류 등: 기존 값 유지
            print('실패:', row['id'], error)
            failed += 1
            continue
        if count is None:
            print('값 없음:', row['id'])
            failed += 1
            continue
        row['views'] = count
        row['views_checked'] = today
        updated += 1
        print(f"{row['id']}: {count:,}")
        time.sleep(0.3)
    if not dry and updated:
        path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'갱신 {updated}개, 실패 {failed}개' + (' (dry-run: 저장 안 함)' if dry else ''))
    return 1 if failed and not updated else 0


if __name__ == '__main__':
    sys.exit(main())
