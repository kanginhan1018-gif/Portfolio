# tools/pptx — 학습용 PPT 빌더

내용 스크립트(`decks/build_*.py`)만 쓰면 덱이 나옵니다. 레이아웃·글꼴·색은 `pptlib.py`와 `template.pptx`가 처리합니다.
**새 덱을 만들 때 `pptlib.py`를 읽을 필요 없음.** 가장 가까운 `decks/build_*.py`를 복사해 내용만 바꾸세요.

## 실행
```
python3 tools/pptx/decks/build_symmetry.py          # -> public/papers/milp-symmetry.pptx
PPT_OUT=/tmp/x python3 tools/pptx/decks/build_symmetry.py   # 다른 폴더로 출력 (덮어쓰기 방지)
tools/pptx/preview.sh public/papers/milp-symmetry.pptx /tmp/prev   # -> /tmp/prev-01.png ...
```
필요: python-pptx, lxml, LibreOffice(soffice), poppler(pdftoppm), CJK 글꼴 파일(기본 ~/Library/Fonts/NotoSansCJK.ttc).

## 슬라이드 종류 (`from pptlib import Deck, out`)
```python
d = Deck()
d.cover('제목', '부제 — 과외 노트', '출처 한 줄')
d.two('슬라이드 제목', '왼쪽 머리말', [왼쪽 항목…], '오른쪽 머리말', [오른쪽 항목…], '하단 출처', split=0.55)
d.wide('제목', '머리말', [항목…], '하단 출처')                       # 한 장짜리 큰 카드
d.table('제목', ['열1','열2'], [['a','b'], …], [너비비율…], aligns=['l','c'], footer='출처', note='표 아래 설명')
d.save(out('milp-xxx.pptx'))
```
- 항목 문자열: `**강조**`(굵게+포인트색), ` ``x`` `(굵게+진한색), 맨 앞 `~`는 글머리표 없음.
- 글자 크기는 자동(18pt에서 줄어듦, 최소 10.5). 표는 8행 이상이면 촘촘하게.
- 제목은 약 25자 이하(30pt, 한 줄).

## 내용 쓰는 규칙 (토큰 아끼는 순서)
1. 한 주제 = 15~23장. 흐름: 왜 필요한가 → 직관/비유 → 기호 읽는 법 → **손으로 푼 숫자 예** → 흔한 오해 → 실험 표 읽기 → 한계 → 확인 문제(정답 포함).
2. 내가 만든 숫자·비유는 하단 출처에 "제가 만든 값"이라고 표시. 읽지 못한 논문은 그렇게 쓰기.
3. 근거는 `src/content/papers/milp-*.md`(검증된 글)에서 가져오기. 새로 지어내지 않기.
4. 단순 분할(기존 슬라이드 자르기)은 금지. 자세하고 명확한 설명이 목표.

## 확인 루프 (한 번이면 충분)
1. 빌드 → `preview.sh` → PIL로 4장씩 묶은 시트(2x2) 한두 장만 보기. 장마다 보지 말 것.
2. 슬라이드 번호를 본문에서 언급했다면(예: "9~15번") 장 순서가 바뀔 때 같이 고치기.

## 함정
- LibreOffice는 한글 글꼴이 없어 한글이 빈칸으로 렌더링됨 → preview.sh가 임시 프로필+글꼴로 해결(미리보기 전용, 원본 pptx는 Apple SD Gothic Neo 유지).
- `template.pptx` = 완성된 덱 하나(milp-symmetry). 1번 슬라이드는 표지(도형 id 2~5), 2번 슬라이드에서 제목(id 2)과 쪽번호(id 25)를 복사해 씁니다. 템플릿을 바꿔도 이 두 가지는 유지.
- python-pptx 요소의 `xpath()`에는 `namespaces=` 인자를 쓰지 않음.
- 기호는 유니코드 첨자(x₁, f⁺)를 쓰고 `x_i`처럼 밑줄 표기도 허용. 이미지 수식은 쓰지 않음.
- 이 환경의 GateGuard 훅은 새 파일을 만들 때마다 사실 확인을 요구할 수 있음(호출처, 중복 여부, 사용자 지시 인용).
