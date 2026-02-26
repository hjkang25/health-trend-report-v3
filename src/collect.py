"""
Health Trend Collector V3
네이버 자동완성 API로 씨앗 키워드의 연관 검색어를 수집하여 CSV로 저장합니다.
"""

import requests
import pandas as pd
import os
import time
from datetime import datetime
from collections import Counter

# ──────────────────────────────────────────────
# 씨앗 키워드 120개
# ──────────────────────────────────────────────
SEED_KEYWORDS = [
    # 증상
    "감기", "두통", "발열", "기침", "콧물", "복통", "소화불량", "불면증", "피로", "어지러움",
    "관절통", "피부발진", "눈충혈", "목통증", "허리통증", "구토", "설사", "변비", "가슴통증", "숨가쁨",
    "부종", "탈모", "손발저림", "식욕부진", "체중감소",
    # 만성질환
    "당뇨", "고혈압", "비만", "암", "우울증",
    "불안장애", "아토피", "비염", "역류성식도염", "갑상선",
    "골다공증", "지방간", "빈혈", "수면무호흡", "공황장애",
    # 암
    "대장암", "위암", "폐암", "유방암", "전립선암",
    # 뇌·심장
    "치매", "파킨슨", "뇌졸중", "심근경색", "협심증",
    # 기타 질환
    "고지혈증", "통풍", "류마티스", "크론병", "과민성대장증후군",
    # 건강 관리
    "다이어트", "운동", "영양제", "수면", "스트레스",
    "금연", "금주", "식단", "체중감량", "면역력",
    "단백질", "비타민", "유산균", "오메가3", "콜라겐",
    "항산화", "해독", "절식", "간헐적단식", "저탄고지",
    # 의료 행위
    "백신", "검진", "수술", "약물", "한의원",
    "재활", "응급", "처방", "항생제", "진통제",
    "내시경", "혈액검사", "MRI", "CT", "주사",
    # 여성 건강
    "생리통", "생리불순", "갱년기", "임신", "산후조리",
    "자궁근종", "난임", "유산", "모유수유", "피임",
    # 남성 건강
    "전립선", "발기부전", "남성갱년기",
    # 정신 건강
    "번아웃", "공황", "트라우마", "강박증", "조현병",
    "ADHD", "자존감", "외로움", "분노조절", "중독",
    # 노인 건강
    "낙상", "요양", "노인성질환", "건강수명",
]

# ──────────────────────────────────────────────
# API 수집 함수
# ──────────────────────────────────────────────
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://www.naver.com/",
    "Accept-Language": "ko-KR,ko;q=0.9",
}


def get_autocomplete(keyword: str, max_retries: int = 3) -> list[str]:
    """네이버 자동완성 API 호출 → 연관 키워드 리스트 반환"""
    url = "https://ac.search.naver.com/nx/ac"
    params = {
        "q": keyword,
        "st": "100",
        "frm": "nv",
        "r_format": "json",
        "r_enc": "UTF-8",
        "r_unicode": "0",
        "t_koreng": "1",
        "ans": "2",
        "run": "2",
        "rev": "4",
        "ndic_usereq": "N",
    }

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            related: list[str] = []
            # items[0]: 일반 자동완성, items[1]: 인기 검색어 (있을 경우)
            for group in data.get("items", []):
                for item in group:
                    if item and len(item) > 0:
                        word = item[0].strip()
                        if word:
                            related.append(word)
            return related

        except requests.exceptions.RequestException as e:
            wait = 2 ** attempt
            print(f"  [RETRY {attempt+1}/{max_retries}] {keyword} → {e} (wait {wait}s)")
            if attempt < max_retries - 1:
                time.sleep(wait)
        except Exception as e:
            print(f"  [ERROR] {keyword}: {e}")
            return []

    return []


# ──────────────────────────────────────────────
# 메인 수집 로직
# ──────────────────────────────────────────────
def collect_all() -> None:
    today = datetime.now().strftime("%Y-%m-%d")
    os.makedirs("data", exist_ok=True)

    total = len(SEED_KEYWORDS)
    all_related: list[str] = []          # 전체 빈도 집계용
    seed_related_rows: list[dict] = []   # 씨앗 키워드별 저장용
    failed: list[str] = []

    print(f"\n{'='*55}")
    print(f"  Health Trend Collector V3  |  {today}")
    print(f"  씨앗 키워드 {total}개 수집 시작")
    print(f"{'='*55}\n")

    for i, keyword in enumerate(SEED_KEYWORDS, 1):
        print(f"[{i:3d}/{total}] {keyword:<12}", end=" → ")
        related = get_autocomplete(keyword)

        if related:
            print(f"{len(related)}개 연관어 수집")
        else:
            print("연관어 없음 (또는 오류)")
            failed.append(keyword)

        for pos, rel in enumerate(related, 1):
            all_related.append(rel)
            seed_related_rows.append(
                {
                    "date": today,
                    "seed_keyword": keyword,
                    "related_keyword": rel,
                    "position": pos,
                }
            )

        time.sleep(0.3)  # 요청 간격 (서버 부하 방지)

    # ── TOP 20 집계 ──────────────────────────────
    counter = Counter(all_related)
    top20 = counter.most_common(20)
    top20_rows = [
        {"date": today, "rank": rank, "keyword": kw, "count": cnt}
        for rank, (kw, cnt) in enumerate(top20, 1)
    ]

    # ── CSV 저장 ─────────────────────────────────
    top20_path = f"data/top20_{today}.csv"
    related_path = f"data/related_{today}.csv"

    pd.DataFrame(top20_rows).to_csv(top20_path, index=False, encoding="utf-8-sig")
    pd.DataFrame(seed_related_rows).to_csv(related_path, index=False, encoding="utf-8-sig")

    # ── 결과 출력 ─────────────────────────────────
    print(f"\n{'='*55}")
    print(f"  수집 완료 ({today})")
    print(f"  총 연관어 수집: {len(all_related):,}개")
    print(f"  고유 연관어: {len(counter):,}개")
    if failed:
        print(f"  실패 키워드: {len(failed)}개 → {', '.join(failed)}")
    print(f"\n  저장 파일:")
    print(f"    · {top20_path}")
    print(f"    · {related_path}")
    print(f"\n  TOP 20 (오늘 가장 많이 등장한 연관 검색어):")
    print(f"  {'순위':>4}  {'키워드':<15}  {'등장 횟수':>8}")
    print(f"  {'-'*32}")
    for row in top20_rows:
        print(f"  {row['rank']:>4}  {row['keyword']:<15}  {row['count']:>8,}회")
    print(f"{'='*55}\n")


if __name__ == "__main__":
    collect_all()
