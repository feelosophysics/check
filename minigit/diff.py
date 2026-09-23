"""
diff.py — LCS 기반 Diff(파일 비교) 모듈
=========================================

[보너스 과제 5.1]

이 모듈은 두 텍스트 파일을 줄 단위로 비교하여
추가(+), 삭제(-), 공통( ) 줄을 구분해 출력합니다.
"""

from typing import List, Tuple
from minigit.constants import ErrorMessages


def compute_lcs_table(lines_a: List[str], lines_b: List[str]) -> List[List[int]]:
    """
    두 줄 목록의 LCS DP 테이블을 생성합니다.
    """
    # ── 1. Data Refinement (데이터 정제) ──
    # 파라미터가 이미 정제되어 전달된다고 가정합니다.

    # ── 2. Validation (유효성 검사) ──
    m: int = len(lines_a)  # 💡 [의미] 첫 번째 파일의 총 줄 수
    n: int = len(lines_b)  # 💡 [의미] 두 번째 파일의 총 줄 수
    
    # ── 3. Logic Execution (비즈니스 로직 실행) ──
    # 💡 파이썬 현미경 해설
    # LCS(Longest Common Subsequence, 최장 공통 부분 수열) 원리:
    # 두 파일의 텍스트가 서로 얼마나 비슷한지, 순서를 유지하면서 가장 길게 겹치는 부분을 찾는 알고리즘입니다.
    # 이 결과를 활용해 파일의 어느 부분이 지워졌고(-) 추가되었는지(+) 알아냅니다.
    # 
    # DP(Dynamic Programming, 동적 계획법)를 활용하여 중간 계산 결과를 저장해 둘 2차원 표(리스트 안의 리스트)를 만듭니다.
    dp: List[List[int]] = []  # 💡 [의미] LCS 길이를 저장해 둘 2차원 표(DP 테이블)용 빈 리스트
    
    # `range(m + 1)`: 0부터 m까지 반복합니다.
    for i in range(m + 1):  # 💡 [문법] range(m+1)은 0부터 m까지 범위를 순회 / [의미] (m + 1)개의 행을 준비하기 위한 루프
        row: List[int] = []  # 💡 [의미] 2차원 표의 한 가로줄(행)을 담을 빈 리스트
        for j in range(n + 1):  # 💡 [의미] 해당 행의 (n + 1)개의 열을 채우는 루프
            row.append(0)  # 💡 [의미] 초기값인 0으로 채움
        dp.append(row)  # 💡 [의미] 채워진 행을 전체 표에 등록

    # 💡 파이썬 현미경 해설
    # LCS(최장 공통 부분 수열) 알고리즘의 핵심 로직입니다.
    # 두 글자(여기서는 '줄')가 같으면 이전 대각선 값 + 1 을 하고,
    # 다르면 위쪽이나 왼쪽 중 더 큰 값을 끌어옵니다.
    for i in range(1, m + 1):  # 💡 [의미] 첫 번째 파일의 각 줄에 대해 순회 (1번 줄부터 m번 줄까지)
        for j in range(1, n + 1):  # 💡 [의미] 두 번째 파일의 각 줄에 대해 순회 (1번 줄부터 n번 줄까지)
            if lines_a[i - 1] == lines_b[j - 1]:  # 💡 [의미] 두 줄의 텍스트가 서로 일치하는 경우
                dp[i][j] = dp[i - 1][j - 1] + 1  # 💡 [의미] 대각선 왼쪽 위의 값(이전 공통 길이)에 1을 더해 저장
            else:  # 💡 [의미] 두 줄의 텍스트가 일치하지 않는 경우
                if dp[i - 1][j] >= dp[i][j - 1]:  # 💡 [의미] 위쪽의 LCS 값이 왼쪽 값보다 크거나 같은 경우
                    dp[i][j] = dp[i - 1][j]  # 💡 [의미] 위쪽 LCS 값을 가져옴
                else:  # 💡 [의미] 왼쪽 LCS 값이 더 큰 경우
                    dp[i][j] = dp[i][j - 1]  # 💡 [의미] 왼쪽 LCS 값을 가져옴

    return dp  # 💡 [의미] 계산이 완료된 LCS DP 테이블 반환


# 💡 파이썬 현미경 해설
# `Tuple`은 리스트와 비슷하지만 한 번 만들어지면 수정이 불가능한 '소포(꾸러미)'입니다.
# `Tuple[str, str]`은 문자열 두 개가 세트로 묶여있다는 뜻입니다. 예: ("+", "hello")
def compute_diff(lines_a: List[str], lines_b: List[str]) -> List[Tuple[str, str]]:
    """
    LCS 테이블을 역추적하여 diff 결과를 생성합니다.
    """
    dp: List[List[int]] = compute_lcs_table(lines_a, lines_b)  # 💡 [의미] 최장 공통 부분을 구하기 위한 DP 테이블을 계산

    diff_result: List[Tuple[str, str]] = []  # 💡 [의미] 역추적하여 얻은 변경사항 표시와 해당 텍스트 줄을 보관할 빈 리스트
    i: int = len(lines_a)  # 💡 [의미] 첫 번째 파일의 마지막 줄을 가리키는 손가락
    j: int = len(lines_b)  # 💡 [의미] 두 번째 파일의 마지막 줄을 가리키는 손가락

    # 💡 파이썬 현미경 해설
    # LCS 테이블 역추적 원리:
    # 만들어진 표의 맨 오른쪽 아래(마지막 줄)에서 출발해 대각선, 위, 왼쪽으로 거슬러 올라갑니다.
    # - 대각선으로 갔다면: 두 파일의 내용이 일치하는 '공통 부분( )'입니다.
    # - 위로 거슬러 올라갔다면: 원본 파일(A)에만 있었으므로 '삭제됨(-)'을 의미합니다.
    # - 왼쪽으로 거슬러 갔다면: 새로운 파일(B)에 추가되었으므로 '추가됨(+)'을 의미합니다.
    while i > 0 or j > 0:  # 💡 [문법] or는 둘 중 하나라도 참이면 수행 / [의미] 두 파일 중 아직 역추적하지 않은 줄이 남아있는 동안 반복
        # 두 줄이 같았다면: 대각선 위로 올라가며 '공통 부분( )'으로 기록
        if i > 0 and j > 0 and lines_a[i - 1] == lines_b[j - 1]:  # 💡 [의미] 두 파일의 해당 줄이 정확히 일치하는 경우
            # 괄호로 묶인 `(" ", lines_a[i - 1])`이 바로 튜플(Tuple)입니다!
            diff_result.append((" ", lines_a[i - 1]))  # 💡 [의미] 공통 줄 표시(" ")와 함께 일치하는 텍스트 줄을 결과에 추가
            i -= 1  # 💡 [의미] 첫 번째 파일 손가락을 이전 줄로 이동
            j -= 1  # 💡 [의미] 두 번째 파일 손가락을 이전 줄로 이동
        # 위쪽 값이 더 컸거나 왼쪽 끝에 다다랐다면: 위로 올라가며 '삭제됨(-)'으로 기록
        elif i > 0 and (j == 0 or dp[i - 1][j] >= dp[i][j - 1]):  # 💡 [의미] 첫 번째 파일에만 줄이 남았거나, 위쪽 LCS 값이 더 크거나 같은 경우
            diff_result.append(("-", lines_a[i - 1]))  # 💡 [의미] 삭제 표시("-")와 함께 첫 번째 파일의 텍스트 줄을 추가
            i -= 1  # 💡 [의미] 첫 번째 파일 손가락만 이전 줄로 이동
        # 왼쪽 값이 더 컸거나 위쪽 끝에 다다랐다면: 왼쪽으로 가며 '추가됨(+)'으로 기록
        else:  # 💡 [의미] 두 번째 파일에만 줄이 남았거나, 왼쪽 LCS 값이 더 큰 경우
            diff_result.append(("+", lines_b[j - 1]))  # 💡 [의미] 추가 표시("+")와 함께 두 번째 파일의 텍스트 줄을 추가
            j -= 1  # 💡 [의미] 두 번째 파일 손가락만 이전 줄로 이동

    # 거꾸로 올라갔으니 결과를 다시 뒤집어줍니다.
    diff_result.reverse()  # 💡 [문법] reverse()는 리스트의 순서를 거꾸로 뒤집음 / [의미] 역추적으로 거꾸로 들어간 결과들을 원래 파일 순서로 복구
    return diff_result  # 💡 [의미] 올바른 파일 순서대로 정렬된 diff 결과 튜플 리스트 반환


def diff_files(file1_path: str, file2_path: str) -> str:
    """
    두 텍스트 파일을 비교하여 diff 결과를 문자열로 반환합니다.
    """
    clean_path1: str = file1_path.strip()  # 💡 [문법] strip()은 문자열 양끝의 공백과 개행을 제거 / [의미] 첫 번째 파일 경로의 불필요한 공백 청소
    clean_path2: str = file2_path.strip()  # 💡 [의미] 두 번째 파일 경로의 불필요한 공백 청소

    # 💡 파이썬 현미경 해설
    # 비교할 두 파일의 내용을 텍스트 줄(line) 단위로 담아둘 빈 리스트를 준비합니다.
    lines_a: List[str] = []
    lines_b: List[str] = []
    
    # 💡 파이썬 현미경 해설
    # `try ... except ...` : 에러가 날 수도 있는 불안한 코드(파일 읽기)를 실행할 때,
    # 프로그램이 뻗어버리지 않게 안전망을 쳐두는 문법입니다.
    try:
        # `with open(...) as f:` : 파일을 열고 나서 `with` 블록이 끝나면 파이썬이 "알아서" 파일을 안전하게 닫아줍니다.
        with open(clean_path1, 'r', encoding='utf-8') as f:  # 💡 [문법] with open(...) as f는 파일 객체를 열고 자동으로 닫아줌 / [의미] 1번 파일을 UTF-8로 읽기 모드 실행
            # `.read().splitlines()` : 파일 전체를 읽은 다음, 엔터 단위로 쪼개서 리스트로 만들어줍니다.
            lines_a = f.read().splitlines()  # 💡 [문법] read()로 문자열을 다 읽고 splitlines()로 개행 단위로 쪼개 리스트화
    except FileNotFoundError:
        # 파일을 찾지 못했을 때 실행됩니다.
        return ErrorMessages.FILE_NOT_FOUND.format(path=clean_path1)  # 💡 [의미] 파일 미존재 포맷 에러 문자열을 반환
    except OSError as e:
        # 파일은 찾았는데 읽기 권한이 없거나 다른 에러가 났을 때 실행됩니다.
        # `str(e)`로 에러의 상세 원인을 텍스트로 뽑아옵니다.
        return ErrorMessages.FILE_READ_ERROR.format(path=clean_path1, error=str(e))  # 💡 [의미] 파일 입출력 에러 포맷 메시지 반환

    try:
        with open(clean_path2, 'r', encoding='utf-8') as f:  # 💡 [의미] 2번 파일을 UTF-8로 읽기 모드 실행
            lines_b = f.read().splitlines()  # 💡 [의미] 개행 단위로 쪼개어 리스트에 보관
    except FileNotFoundError:
        return ErrorMessages.FILE_NOT_FOUND.format(path=clean_path2)
    except OSError as e:
        return ErrorMessages.FILE_READ_ERROR.format(path=clean_path2, error=str(e))

    # 두 파일을 다 잘 읽어왔다면 위에서 만든 diff 계산 함수를 부릅니다.
    diff_result: List[Tuple[str, str]] = compute_diff(lines_a, lines_b)  # 💡 [의미] 줄 단위 추가, 삭제, 공통 분석 결과를 가져옴

    output_lines: List[str] = []
    # 전통적인 diff 도구들처럼 이전 파일은 ---, 바뀐 파일은 +++로 표시합니다.
    output_lines.append(f"--- {clean_path1}")  # 💡 [의미] 헤더에 원본(이전) 파일 경로 정보 추가
    output_lines.append(f"+++ {clean_path2}")  # 💡 [의미] 헤더에 수정(이후) 파일 경로 정보 추가
    output_lines.append("")  # 💡 [의미] 헤더 뒤 가독성을 위한 한 줄 개행

    added: int = 0  # 💡 [의미] 추가된 줄의 누적 개수
    removed: int = 0  # 💡 [의미] 삭제된 줄의 누적 개수
    unchanged: int = 0  # 💡 [의미] 변경 없는 공통 줄의 누적 개수

    # 💡 파이썬 현미경 해설
    # `for mark, line in diff_result:`
    # 튜플 묶음 `("+", "hello")`을 한 번에 풀어헤쳐서 앞부분은 mark에, 뒷부분은 line에 집어넣는 아주 세련된 파이썬 문법(Unpacking)입니다!
    for mark, line in diff_result:  # 💡 [문법] Tuple Unpacking으로 (기호, 내용) 구조를 각각 mark와 line에 할당 / [의미] 분석된 모든 줄을 순회
        if mark == "+":  # 💡 [의미] 추가된 줄인 경우
            output_lines.append(f"+ {line}")  # 💡 [의미] 줄 앞에 + 표시를 붙여 결과에 추가
            added += 1  # 💡 [의미] 추가 카운트 1 증가
        elif mark == "-":  # 💡 [의미] 삭제된 줄인 경우
            output_lines.append(f"- {line}")  # 💡 [의미] 줄 앞에 - 표시를 붙여 결과에 추가
            removed += 1  # 💡 [의미] 삭제 카운트 1 증가
        else:  # 💡 [의미] 공통 줄인 경우
            output_lines.append(f"  {line}")  # 💡 [의미] 줄 앞에 두 개의 공백을 붙여 결과에 추가
            unchanged += 1  # 💡 [의미] 공통 카운트 1 증가

    output_lines.append("")  # 💡 [의미] 요약 보고서 작성을 위한 개행 추가
    output_lines.append(
        f"Summary: {added} addition(s), "
        f"{removed} deletion(s), "
        f"{unchanged} unchanged line(s)"
    )  # 💡 [의미] 최종 추가, 삭제, 유지 라인에 대한 통계 요약 텍스트 추가

    return "\n".join(output_lines)  # 💡 [의미] 모든 줄바꿈 형식의 결과를 하나의 문자열로 결합하여 반환
