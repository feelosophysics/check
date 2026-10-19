# B3-2 미션 비교 — heejeong13 × feelosophysics

비교일: 2026-10-20 · 두 사람이 코드를 보며 설계 이유와 다음 개선을 이야기하기 위한 보고서.

**먼저 볼 결론:** 두 구현 모두 Git 변경을 AI에 전달해 한국어 커밋·PR 초안을 만든다. 희정 구현은 **입력 보호, 출력 검증, 오류 처리와 테스트**가 더 촘촘하다. feelosophysics 구현은 **대화형 stage/commit, YAML 팀 규칙, 설치 자동화와 학습 설명**이 풍부하다. 기능 수보다, “어떤 변경을 보내고 어떤 응답을 믿고 적용할 것인가”를 함께 보면 대화가 깊어진다.

이하 **‘희정’은 `heejeong13/codyssey_b3-2`, ‘내 구현’은 `feelosophysics/codsaid/01_Basic/b3-2`**를 뜻한다. 저장소에서 관찰한 결과를 비교하며, 사람의 이해도나 기여도를 코드만으로 평가하지 않는다.

## 1. 5분 안에 같이 볼 내용

1. **희정에게 배우고 싶은 점:** 안전 모드 기본 ON, status·diff·context 전체 마스킹, JSON 응답 검증, 최대 한 번 교정, API 모의 테스트.
2. **내가 공유할 수 있는 점:** 팀별 YAML 컨벤션, stage→생성→확인→commit의 흐름, 교육장 Python/alias 문제 해결, 모듈별 학습 자료.
3. **먼저 고칠 내 문제:** staged·unstaged 혼재 시 PR 분석에서 staged 변경이 빠지는 문제, safe-mode 전송 범위, README와 코드의 설정 파일명·기본값 불일치.
4. **희정과 같이 확인할 점:** 형식 검증의 실제 범위, Windows 테스트 이식성, 마스킹 한계, 설명용 예시와 실제 실행 증빙의 구분.
5. **같은 예제로 비교할 점:** 같은 Git 상태와 같은 변경 이유를 주고, 실제로 전송한 입력과 최종 초안을 나란히 보기.

## 2. 비교 기준과 근거

| 대상 | 확인한 기준점 | 범위 |
| --- | --- | --- |
| 희정 | [`3dde2da`](https://github.com/heejeong13/codyssey_b3-2/tree/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f) | `main.py`, `gitgen/cli.py`, `gitgen/core.py`, `tests/test_gitgen.py`, README·의존성 |
| 내 구현 | [`0cfd1d6`](https://github.com/feelosophysics/codsaid/tree/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2) | `main.py`, `gitgen/` 6개 모듈, 설정·설치 파일, README·study 자료 |

내 B3-2 경로에 미커밋 변경이 없는 상태에서 비교했다. 현재 `check`의 다른 비교 노트는 별도 상대와의 과거 비교이므로 이 보고서의 근거로 재사용하지 않았다.

**확인 방식:** 소스·문서 검토 + Python 3.12.13/Windows에서 로컬 재현. 실제 API 호출과 새 커밋·PR 생성은 비교 실험에 포함하지 않았다. 모델별 품질·현재 사용 가능 여부·비용 우열은 평가하지 않았다. 아래 모델명은 코드의 기본 설정값이다. 과제 원문 전체나 원문 직접 링크는 싣지 않으며, 공식 채점표에 따른 합격·점수 판정도 하지 않는다.

## 3. 구현 비교표

| 비교 항목 | 희정 | 내 구현 | 대화의 초점 |
| --- | --- | --- | --- |
| 실행 구조 | 작은 `main.py` → `cli.py` + `core.py` | `main.py` + Git/API/안전/설정/프롬프트 모듈 | 파일 수보다 책임과 테스트 경계 |
| 변경 수집 | staged·unstaged 모두 수집해 구분 표시 | 기본은 unstaged, 비어 있으면 staged; staged 전용 선택도 있음 | 분석 범위가 사용자 기대와 맞는가 |
| 미추적 파일 | 이름만 수집, 내용은 먼저 add하라고 안내 | commit에서 확인 후 `git add .`; PR은 내용 수집 안 됨 | 누락과 일괄 추가의 비용 |
| Git 변경 작업 | 초안 출력까지만 수행 | 동의 시 전체 add 및 실제 로컬 commit | 편리함과 변경 범위 통제 |
| 안전 모드 기본값 | ON, `--no-safe-mode`로 해제 | OFF, `--safe-mode`로 활성화 | 잊었을 때의 결과 |
| 안전 모드 적용 범위 | status·diff·추가 맥락 | diff만 | 파일명에 든 정보도 전송됨 |
| 대표 마스킹 | 실제 환경 키 값, 키·이메일·비밀 할당, PEM 개인키 | 이메일·`sk-`·Bearer·IP·비밀번호 등 | 서로 보완할 패턴이 있음 |
| 비밀번호 처리 | 해당 할당의 값을 가림 | 긴 값은 앞 2글자를 남김 | 부분 공개의 필요성 |
| 큰 입력 | JSON 직렬화 결과 100,000자 초과 시 중단 | safe-mode에서 diff를 기본 200줄로 절단 | 누락 허용 vs 범위를 줄여 재실행 |
| API | 코디세이 Chat Completions REST | Google Gemini 계열 REST | 공급자 차이와 자체 설계 구분 |
| 모델·생성 기본값 | `gpt-5-mini`, temperature 미전송, 1024 토큰 | `gemma-4-31b-it`, temperature 0.3, 2000 토큰 | 서로 다른 모델·입력으로 품질 단정 불가 |
| 요청 제한 시간 | Git 30초, API 60초 명시 | Git/API 호출에 timeout 인수 없음 | 멈춤을 어떻게 처리할까 |
| 출력 구조 | `summary/title/body` JSON을 파싱·검사 | 자유 텍스트를 그대로 출력 | 생성 요청과 실제 보장의 차이 |
| 오류 응답 교정 | 형식 오류에 최대 1회 교정/재생성 | 교정·재생성 루프 없음 | 실패 원인별 재시도 비용 |
| 팀 규칙 | 코드의 프롬프트, 실행별 `--context` | YAML의 commit/pr 규칙 주입 | 고정 규칙과 실행별 사유를 함께 쓸 수 있음 |
| 의존성 | `python-dotenv>=1.0,<2.0` | `python-dotenv==1.2.2`, `PyYAML==6.0.3` | 설치 단순성 vs 버전 고정 |
| 검증 자료 | 자동 테스트 16개 메서드, 실행 상태 문서 | README의 파라미터 실험·PR 수정 설명, `study/` | 자동 회귀 검사와 학습 기록의 역할 |
| 설치·학습 지원 | 설치/운영/한계를 정리한 README | venv·alias 처리 `setup.sh`, 상세 해설·리팩터링·트러블슈팅 | 다른 컴퓨터에서 설명하고 실행하기 |

근거: 희정의 [core.py](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/gitgen/core.py), [cli.py](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/gitgen/cli.py), 내 [main.py](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/main.py), [gitgen 디렉터리](https://github.com/feelosophysics/codsaid/tree/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/gitgen).

## 4. 내 구현에서 먼저 다룰 문제

### 4.1 PR 분석에서 staged 변경 누락 — 로컬 재현 확인

`get_git_diff()`는 unstaged diff가 있으면 즉시 반환하고, 없을 때만 staged diff를 읽는다. PR 명령은 이 기본 동작을 쓴다. 따라서 두 종류가 함께 있으면 status에는 양쪽 파일이 나오더라도 AI가 받는 diff는 unstaged 쪽뿐이다.

예를 들어 새 파일을 `STAGED_FIRST` 내용으로 add한 뒤, 작업 파일을 `UNSTAGED_SECOND`로 고치면:

| 수집 결과 | 희정 | 내 기본 `get_git_diff()` |
| --- | --- | --- |
| staged 추가 내용 `+STAGED_FIRST` | 포함 | 누락 |
| unstaged 추가 내용 `+UNSTAGED_SECOND` | 포함 | 포함 |

내 `staged_only=True`는 staged 내용만 정확히 읽었다. 즉 commit에서 stage 범위를 선택하는 설계는 유지하되, **PR용 전체 수집과 commit용 staged 수집을 명시적으로 분리**하는 편이 좋다. 희정 방식은 두 상태를 모두 보내므로, 같은 파일의 중간 상태와 최종 상태를 AI가 혼동하지 않는지도 검토할 만하다.

근거: 내 [`get_git_diff()`](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/gitgen/git_helper.py#L23), 희정 [`collect_changes()`](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/gitgen/core.py#L35).

### 4.2 safe-mode가 놓치는 입력 — 로컬 재현 + 코드 확인

합성 문자열 `API_KEY="synthetic-demo-key"`를 입력하고 같은 값을 `AI_API_KEY`로 설정했다. 희정은 실제 환경 키 값과 할당 패턴으로 가렸지만, 내 안전 모드는 이 문자열을 그대로 남겼다. 내 `sk-` 패턴에 해당하지 않으며 `API_KEY`라는 할당 이름도 비밀번호 정규식에 포함되지 않기 때문이다.

또한 내 코드는 diff만 가리고 status는 그대로 프롬프트에 넣는다. 안전 모드를 켜도 파일명 등의 민감 정보가 status를 통해 전송될 수 있다. 기본 OFF이고 비밀번호 앞 2자도 유지한다. 반대로 **IP·Bearer 마스킹은 내 쪽에 명시적으로 있어** 희정 구현과 보완할 여지가 있다. 이번 IP 예제에서 희정은 주소를 유지하고 내 구현은 가렸다.

개선 순서는 기본 ON → 전체 전송 입력에 적용 → 설정된 실제 키와 일반 API_KEY 할당 보호 → 패턴별 회귀 검사 순이 적절하다. 어느 쪽 정규식도 모든 비밀값 탐지를 보장하지 않는다.

근거: 내 [safe_mode.py](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/gitgen/safe_mode.py), 희정 [`mask()`](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/gitgen/core.py#L60).

### 4.3 문서와 실행 계약 불일치 — 로컬 재현 + 코드 확인

- README는 `.ai-gitgen.yml`을 안내하지만 실제 파일과 로더는 **`ai-gitgen.yml`**이다. 점이 있는 파일만 두면 로더는 `None`을 반환하고, 점 없는 파일은 정상 로드했다. 안내를 따른 사용자가 규칙이 적용됐다고 오해할 수 있다.
- README 옵션 설명은 temperature 기본 0.7, max-tokens 기본 1000이지만 실제 CLI는 **0.3 / 2000**이다.
- 내 전역 옵션은 argparse의 상위 parser에만 있다. README처럼 `python main.py --temperature 0.3 pr`로 전달하는 방식과 희정의 `python main.py pr --temperature ...` 방식이 다르다. 서로의 실행 명령을 복사할 때 위치를 확인해야 한다.

근거: 내 [config.py](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/gitgen/config.py), [README](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/README.md), [CLI 정의](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/main.py#L88).

### 4.4 API 실패 문자열이 커밋 초안으로 흐를 수 있음 — 모의 응답 확인

`candidates=[]` 응답에서 내 API 함수는 예외나 실패 상태 대신 **`API 호출 실패 (응답 텍스트 없음)`**이라는 일반 문자열을 반환했다. 상위 함수는 이 값을 성공한 결과처럼 출력하고, commit 흐름에서는 사용자가 승인하면 커밋 메시지로 넘길 수 있다. 정상 텍스트와 실패를 구분하는 반환 계약이 필요하다.

API/Git timeout을 명시하고 출력 최소 조건을 검사하는 것도 희정 구현에서 가져올 수 있다. 모델의 응답 내용을 프롬프트만으로 보장하지 않는다는 점이 핵심이다.

근거: 내 [gemini_client.py](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/gitgen/gemini_client.py), [생성·확인 흐름](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/main.py).

## 5. 희정 구현에서 좋았던 선택과 함께 볼 빈틈

### 5.1 생성과 검증을 나눈 점

`generate_validated()`는 응답을 JSON으로 읽고 제목 길이·본문 형식을 확인한다. 읽을 수 있는 초안의 형식 문제라면 **원본 diff 없이 초안과 오류만 다시 보내고**, JSON 손상·필수 필드 누락이면 원본 입력으로 한 번 재생성한다. 두 번째 응답도 검사하고 API 오류는 자동 재시도하지 않는다. 의미 보존과 비용을 함께 고려한 설계다.

다만 JSON은 API의 구조화 출력 옵션으로 강제한 것이 아니라 프롬프트로 요청한 뒤 로컬 파싱하는 방식이다. 검증은 아래 범위까지다.

| 규칙 | 실제 검사 여부 |
| --- | --- |
| summary/title/body가 비어 있지 않은 문자열 | 검사 |
| 한 줄 제목, commit 최대 72자 / PR 최대 80자 | 검사 |
| PR Why→What→How to Test 순서와 각 불릿 | 검사 |
| commit 본문 최소 한 개 불릿 | 검사 |
| 한국어, feat/fix 등 허용 prefix, commit 불릿 최대 2개 | 프롬프트 지시만 있음 |
| 변경 내용의 사실성, 실행하지 않은 테스트 성공 주장 | 자동 검증하지 않음 |

실제로 영어 summary, prefix 없는 제목, 불릿 3개인 commit JSON도 `validate()`를 통과했다. “검증이 있다”는 말과 “요구한 모든 규칙을 검증한다”는 말을 구분하면 좋다. 내 구현에도 같은 구분이 필요하다.

근거: 희정 [`instructions()`·`validate()`](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/gitgen/core.py#L81), [`generate_validated()`](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/gitgen/core.py#L210).

### 5.2 자동 테스트의 강점과 Windows 이식성

테스트는 단순 함수뿐 아니라 잘못된 API 응답, 인증·한도 오류, 재시도 상한, Git 상태, .env 우선순위, 전송 데이터 마스킹까지 다룬다. 이 구조는 내 코드 개선 후 회귀를 잡는 데 좋은 참고다.

이번 Windows 실행에서는 **전체 16개가 통과한 것은 아니다.** 검증 7개와 API 3개는 통과했다. Git 통합 테스트 6개는 다음 이유로 실패/오류가 났다.

- `addCleanup(os.chdir, old)` 다음에 `addCleanup(tmp.cleanup)`을 등록한다. cleanup은 역순 실행이므로 **아직 임시 폴더 안에 있는 상태에서 그 폴더를 삭제**한다. Windows에서는 사용 중 디렉터리 삭제 오류가 발생했다. 실행 위치 복원이 삭제보다 먼저 되도록 순서를 바꿀 수 있다.
- 일부 테스트의 `patch.dict(os.environ, {}, clear=True)`는 **PATH까지 제거**한다. 현재 환경의 Git은 PATH로 발견되므로 그 구간에서 “Git이 설치되어 있지 않습니다”가 발생했다. 목적이 API 키 제거라면 PATH를 보존하거나 Git 실행 경로를 별도로 고정하는 방법이 있다.

실행 환경 문제와 테스트 코드의 플랫폼 가정을 확인한 결과다. 이것만으로 희정의 실제 API 사용이나 Mac 실행이 실패했다고 판단하지 않는다. 친구 컴퓨터에서도 전체 테스트를 함께 실행해 보면 좋다.

근거: 희정 [tests/test_gitgen.py](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/tests/test_gitgen.py).

### 5.3 제출 증빙과 제한을 분명하게 쓴 점

희정 README는 출력 예시를 **설명용이며 실제 API 실행 증빙이 아니라고 명시**하고, 실제 연동 확인은 별도 표에서 보고한다. 반면 내 README는 실제 PR 링크와 AI 초안→수정 이유를 더 구체적으로 설명한다. 둘을 결합하면 “어떤 실행이 실제 확인됐고, 생성물을 사람이 어떻게 고쳤는가”가 더 잘 드러난다.

희정 README의 실제 API 연동은 작성자가 보고한 기존 기록이다. 이번 비교에서 재실행하지 않았다. 내 README에 기재된 [PR 링크](https://github.com/feelosophysics/glad/pull/1/commits) 역시 문서상 증빙이며, 이번에 해당 PR의 내용·상태를 별도 검증하지 않았다.

근거: 희정 [README](https://github.com/heejeong13/codyssey_b3-2/blob/3dde2da67ee8289aaaafd4eff0d50e5f61ad5d7f/README.md), 내 [README](https://github.com/feelosophysics/codsaid/blob/0cfd1d6d4a6540f3ba9d8c795cd1adf8ae7c061f/01_Basic/b3-2/README.md).

## 6. 서로 가져가면 좋은 개선

| 우선순위 | 내 구현 | 희정 구현 |
| --- | --- | --- |
| 먼저 | PR 수집 범위 수정, 전체 입력 마스킹·기본 ON, 실패 응답을 성공 문자열과 분리 | Windows cleanup·PATH 가정 수정 후 전체 테스트 재확인 |
| 다음 | 설정 파일명·기본값 문서 일치, API/Git timeout, 출력 검증·자동 테스트 | 실제 검사할 작성 규칙을 명시하고 필요하면 prefix·불릿 개수 검사 추가 |
| 선택 확장 | 전체 `git add .` 대신 파일별 선택·변경 미리보기 | YAML 팀 컨벤션, 전송 입력 미리보기, 실제 생성물의 수정 전후 기록 |

희정의 `--context`와 내 YAML은 역할이 다르다. YAML에는 팀이 계속 쓰는 형식, context에는 이번 변경 이유와 실제 테스트 결과를 넣으면 함께 사용할 수 있다. 두 구현의 장점을 합칠 때 첫 목표는 **수집→보호→생성→검증→사람의 적용** 경계를 분명하게 만드는 것이다.

## 7. 친구와 나눌 질문

1. “전체 변경 초안과 이번에 staged한 커밋 초안은 입력 범위가 달라야 할까?”
2. “왜 초안 출력까지만 두었어? 나는 commit까지 붙였는데, 실제로 어디까지 자동화하는 게 편했어?”
3. “안전 모드는 무엇을 가리고 무엇은 남겨야 요약 품질이 유지될까? API 키 실제 값과 파일명도 같이 볼까?”
4. “형식 검증과 사실 검증 중 어디까지 자동화했고, 최종 초안에서 사람이 가장 자주 고친 부분은 뭐였어?”
5. “작은 max-tokens에서 응답이 잘렸을 때 어떻게 확인했어? 교정 비용까지 포함하면 어떤 선택이 좋았어?”
6. “내 YAML 규칙과 네 context 입력을 함께 쓰면 어떤 작업 흐름이 좋을까?”
7. “자동 테스트를 먼저 작성했는지, 실패 경험에서 추가했는지? 내가 가져오면 가장 먼저 도움이 될 테스트는 뭐야?”

## 8. 함께 해볼 10분 실험

1. 각자 원본을 건드리지 않는 샘플 Git 저장소를 만든다. 같은 파일에 staged 변경과 추가 unstaged 변경을 둔다.
2. API 호출 전 두 코드가 수집한 status/diff를 나란히 본다. 미추적 파일 하나도 추가해 내용 포함 여부를 확인한다.
3. 실제 비밀 대신 예제 이메일·합성 API_KEY·문서용 IP를 넣고 마스킹 결과를 확인한다.
4. 형식만 다른 JSON 응답을 모의 주입한다. 긴 제목, prefix 없음, PR 섹션 누락이 각각 어떻게 처리되는지 본다.
5. 실제 API 결과를 비교하려면 같은 입력과 변경 사유를 쓰고, 모델·옵션·수정 전후를 함께 기록한다. 테스트 실행 여부는 사실대로 남긴다.

로컬 경계 사례는 이 레포의 [재현 스크립트](tools/compare_b3_2.py)로 다시 확인할 수 있다. 두 소스 경로와 `python-dotenv`, `PyYAML`이 필요하며, 실제 API를 호출하거나 원본 소스를 수정하지 않는다. 실행 폴더 아래 임시 Git 저장소에서 `init`/`add`만 수행하고 정리한다.

```bash
python tools/compare_b3_2.py --friend ../codyssey_b3-2 --mine ../codsaid/01_Basic/b3-2
```

이번 재현 결과는 [합성 입력 실행 결과](evidence/b3-2-probes.json)에 보관했다. 영어·prefix·불릿 검증 수용 사례, mixed diff 누락, 설정 파일명, 마스킹 차이, 빈 API candidates 반환을 직접 확인했다. 실제 키나 과제 원문은 사용하지 않았다.
