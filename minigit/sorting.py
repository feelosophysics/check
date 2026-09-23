"""
sorting.py — 정렬 알고리즘 모듈
=================================

이 모듈은 두 가지 정렬 알고리즘을 직접 구현합니다:

1. 머지 정렬 (Merge Sort)  — 안정 정렬, O(n log n) 보장
2. 퀵 정렬 (Quick Sort)    — 불안정 정렬, 평균 O(n log n), 최악 O(n²)

그리고 보너스 과제 5.3을 위한 성능 비교 함수도 포함합니다.

════════════════════════════════════════════
★ 미션 제약: sorted()와 list.sort() 사용 금지 ★
════════════════════════════════════════════
"""

import time
import hashlib
# 💡 파이썬 현미경 해설
# `Callable`: 함수 자체를 변수에 담아서 전달할 때 쓰는 타입 힌트입니다.
# `Any`: 어떤 타입이든 들어올 수 있다는 뜻입니다. (정수, 문자열, 커밋 객체 등)
from typing import List, Callable, Any, Optional
from minigit.constants import SystemMessages


# 💡 파이썬 현미경 해설
# `key_func`는 정렬의 '기준'을 정해주는 함수입니다.
# 예를 들어, 학생 리스트가 있을 때 "이름순"으로 정렬할지 "점수순"으로 정렬할지 알려주는 도구입니다.
def merge_sort(arr: List[Any], key_func: Optional[Callable[[Any], Any]] = None) -> List[Any]:
    """
    머지 정렬(Merge Sort)을 수행합니다.
    """
    if key_func is None:
        # 💡 파이썬 현미경 해설
        # 만약 기준 함수가 안 주어졌다면, 그냥 들어온 값 그대로를 반환하는 `identity` 함수를 임시로 만듭니다.
        def identity(x: Any) -> Any:
            return x
        key_func = identity

    # 💡 파이썬 현미경 해설
    # 머지 정렬(Merge Sort)의 원리:
    # 1. 주어진 배열을 더 이상 쪼갤 수 없을 때(길이 1)까지 반으로 계속 쪼갭니다(Divide).
    # 2. 쪼개진 조각들을 서로 비교하며 다시 크기 순서대로 하나의 리스트로 합칩니다(Conquer).
    # 항상 반으로 쪼개기 때문에 최악의 경우에도 항상 일정한 속도인 O(n log n)을 보장합니다!
    # 
    # 배열의 길이가 1개 이하(0개 또는 1개)면 더 이상 쪼갤 수 없고 이미 정렬된 상태이므로, 그대로 복사해서 돌려줍니다.
    if len(arr) <= 1:
        return arr[:]  # 💡 [문법] 슬라이싱 [:]은 리스트의 얕은 복사본을 반환 / [의미] 정렬이 필요 없는 원소 1개 이하의 리스트를 그대로 리턴

    # 💡 파이썬 현미경 해설
    # `//`: 나눗셈을 하되 소수점을 버리고 정수 몫만 구하는 연산자입니다. (배열을 반으로 쪼갭니다)
    mid: int = len(arr) // 2  # 💡 [문법] // 연산자는 정수 나눗셈의 몫을 반환 / [의미] 배열을 절반으로 가를 중간점 인덱스 설정
    
    # 💡 파이썬 현미경 해설
    # 재귀 호출(자기 자신을 다시 부름)!
    # 왼쪽 절반(`arr[:mid]`)을 다시 머지 정렬하고, 오른쪽 절반(`arr[mid:]`)을 다시 머지 정렬합니다.
    left: List[Any] = merge_sort(arr[:mid], key_func)  # 💡 [문법] 슬라이싱 arr[:mid]로 복사본 생성 / [의미] 왼쪽 부분 배열 재귀 정렬
    right: List[Any] = merge_sort(arr[mid:], key_func)  # 💡 [문법] 슬라이싱 arr[mid:]로 복사본 생성 / [의미] 오른쪽 부분 배열 재귀 정렬

    # 쪼개진 걸 다 정렬했으니, 이제 하나로 합칩니다!
    return _merge(left, right, key_func)  # 💡 [의미] 분할 정렬된 두 하위 배열을 하나로 병합하여 결과 반환


def _merge(left: List[Any], right: List[Any], key_func: Callable[[Any], Any]) -> List[Any]:
    """
    두 정렬된 배열을 하나의 정렬된 배열로 병합합니다.
    """
    result: List[Any] = []  # 💡 [의미] 병합하여 정렬된 원소들을 채워 넣을 빈 리스트 생성
    i: int = 0  # 💡 [의미] 왼쪽(left) 리스트에서 비교할 요소를 가리키는 손가락(인덱스 포인터)
    j: int = 0  # 💡 [의미] 오른쪽(right) 리스트에서 비교할 요소를 가리키는 손가락(인덱스 포인터)

    # 💡 파이썬 현미경 해설
    # 두 손가락 중 하나라도 끝에 도달하기 전까지 계속 비교합니다.
    while i < len(left) and j < len(right):  # 💡 [문법] and는 둘 다 참일 때 루프 수행 / [의미] left와 right 둘 다 탐색할 원소가 남아있는 동안 반복
        left_key: Any = key_func(left[i])  # 💡 [의미] 왼쪽 리스트의 i번째 원소에서 정렬 기준값 추출
        right_key: Any = key_func(right[j])  # 💡 [의미] 오른쪽 리스트의 j번째 원소에서 정렬 기준값 추출

        # 왼쪽 값이 더 작거나 같으면, 왼쪽 값을 결과 주머니에 넣고 왼쪽 손가락을 다음 칸으로 넘깁니다.
        if left_key <= right_key:  # 💡 [의미] 왼쪽 요소 기준값이 작거나 같을 경우 (안정 정렬을 위해 작거나 같을 때 왼쪽을 우선시함)
            result.append(left[i])  # 💡 [문법] append()는 리스트 끝에 값 추가 / [의미] 왼쪽 요소를 결과에 추가
            i += 1  # 💡 [의미] 왼쪽 탐색 포인터를 1 증가시켜 다음 원소로 이동
        # 오른쪽 값이 더 작으면 오른쪽 값을 주머니에 넣습니다.
        else:
            result.append(right[j])  # 💡 [의미] 오른쪽 요소를 결과에 추가
            j += 1  # 💡 [의미] 오른쪽 탐색 포인터를 1 증가시켜 다음 원소로 이동

    # 💡 파이썬 현미경 해설
    # 어느 한쪽이 먼저 끝났다면, 남은 쪽의 나머지 요소들을 몽땅 주머니에 쓸어 담습니다.
    while i < len(left):  # 💡 [의미] 왼쪽 리스트에 남은 요소가 있는 경우
        result.append(left[i])  # 💡 [의미] 순서대로 남은 요소를 결과 리스트에 대입
        i += 1  # 💡 [의미] 왼쪽 포인터 이동

    while j < len(right):  # 💡 [의미] 오른쪽 리스트에 남은 요소가 있는 경우
        result.append(right[j])  # 💡 [의미] 순서대로 남은 요소를 결과 리스트에 대입
        j += 1  # 💡 [의미] 오른쪽 포인터 이동

    return result  # 💡 [의미] 병합 정렬이 완결된 새로운 정렬 리스트 반환


def quick_sort(arr: List[Any], key_func: Optional[Callable[[Any], Any]] = None) -> List[Any]:
    """
    퀵 정렬(Quick Sort)을 수행합니다.
    """
    if key_func is None:
        def identity(x: Any) -> Any:
            return x
        key_func = identity

    if len(arr) <= 1:
        return arr[:]  # 💡 [의미] 원소가 1개 이하이면 이미 정렬된 상태이므로 복사본 반환

    # 💡 파이썬 현미경 해설
    # 퀵 정렬(Quick Sort)의 원리:
    # 1. 기준점(Pivot)을 하나 정합니다.
    # 2. 기준보다 작은 그룹, 같은 그룹, 큰 그룹 세 개로 나눕니다.
    # 3. 나눠진 각 그룹에 대해 다시 똑같은 분할 작업을 재귀적으로 반복합니다.
    # 평균적으로 O(n log n)의 매우 빠른 속도를 자랑하는 알고리즘입니다!
    # 
    # 퀵 정렬의 핵심! 먼저 기준점(Pivot)을 잡습니다.
    pivot: Any = _select_pivot(arr, key_func)  # 💡 [의미] Median-of-Three 전략을 이용해 최적의 기준점(피벗)을 골라냄
    pivot_key: Any = key_func(pivot)  # 💡 [의미] 피벗 원소의 비교 기준값을 구함
    
    less: List[Any] = []    # 💡 [의미] 피벗보다 작은 값을 모으는 서브 리스트
    equal: List[Any] = []   # 💡 [의미] 피벗과 정확히 일치하는 값을 모으는 서브 리스트 (중복값 처리)
    greater: List[Any] = [] # 💡 [의미] 피벗보다 큰 값을 모으는 서브 리스트

    for item in arr:  # 💡 [문법] for ... in 루프로 배열의 요소를 순서대로 순회 / [의미] 각 원소를 기준값과 비교하기 위해 꺼냄
        item_key: Any = key_func(item)  # 💡 [의미] 현재 원소의 비교 기준값을 추출
        if item_key < pivot_key:  # 💡 [의미] 기준값이 피벗의 기준값보다 작은 경우
            less.append(item)  # 💡 [의미] 작은 원소 모음 리스트(less)에 추가
        elif item_key > pivot_key:  # 💡 [의미] 기준값이 피벗의 기준값보다 큰 경우
            greater.append(item)  # 💡 [의미] 큰 원소 모음 리스트(greater)에 추가
        else:  # 💡 [의미] 기준값이 피벗의 기준값과 같은 경우
            equal.append(item)  # 💡 [의미] 동일 원소 모음 리스트(equal)에 추가

    # 💡 파이썬 현미경 해설
    # 작은 애들끼리 다시 퀵 정렬, 큰 애들끼리 다시 퀵 정렬한 뒤,
    # (작은애들) + (같은애들) + (큰애들) 순서로 리스트를 이어 붙여(+) 반환합니다.
    return quick_sort(less, key_func) + equal + quick_sort(greater, key_func)  # 💡 [문법] 리스트 더하기(+) 연산은 두 리스트를 병합함 / [의미] 정렬된 리스트들을 최종 결합하여 반환


def _select_pivot(arr: List[Any], key_func: Callable[[Any], Any]) -> Any:
    """
    Median-of-Three 전략으로 피벗을 선택합니다.
    (맨 앞, 맨 뒤, 중간 값 3개 중 중간 크기를 가진 것을 피벗으로 골라 성능 저하를 방지합니다)
    """
    if len(arr) <= 2:
        return arr[0]  # 💡 [의미] 배열의 크기가 2 이하인 경우에는 간단히 첫 번째 원소를 피벗으로 사용

    first: Any = arr[0]             # 💡 [의미] 배열의 첫 번째 원소
    mid: Any = arr[len(arr) // 2]   # 💡 [의미] 배열의 정확한 한가운데에 위치한 원소
    last: Any = arr[-1]             # 💡 [문법] 인덱스 -1은 가장 마지막 원소를 의미 / [의미] 배열의 마지막 원소

    f_key: Any = key_func(first)  # 💡 [의미] 첫 번째 원소의 기준값
    m_key: Any = key_func(mid)  # 💡 [의미] 중간 원소의 기준값
    l_key: Any = key_func(last)  # 💡 [의미] 마지막 원소의 기준값

    # 💡 파이썬 현미경 해설
    # `(A <= B <= C)`처럼 파이썬에서는 수학식처럼 두 번 비교를 한 줄에 쓸 수 있습니다!
    if (f_key <= m_key <= l_key) or (l_key <= m_key <= f_key):  # 💡 [문법] 다중 연쇄 비교와 논리합(or) 연산 / [의미] mid가 first와 last 사이의 중간값인 경우
        return mid  # 💡 [의미] 중간값인 중간 요소를 피벗으로 선택
    elif (m_key <= f_key <= l_key) or (l_key <= f_key <= m_key):  # 💡 [의미] first가 mid와 last 사이의 중간값인 경우
        return first  # 💡 [의미] 중간값인 첫 번째 요소를 피벗으로 선택
    else:  # 💡 [의미] mid나 first가 중간값이 아닌, 즉 last가 중간값인 경우
        return last  # 💡 [의미] 마지막 요소를 피벗으로 선택


def benchmark_sorts(n_sizes: Optional[List[int]] = None) -> str:
    """
    [보너스 5.3] 두 정렬 알고리즘의 성능을 비교합니다.
    """
    # ── 1. Data Refinement (데이터 정제) ──
    # 💡 파이썬 현미경 해설
    # 사용자가 따로 테스트할 개수를 정해주지 않으면(`None`이면),
    # 10개부터 5000개까지 점점 배열 크기를 늘려가며 성능을 측정할 기본 리스트를 만듭니다.
    sizes_to_run: List[int] = []  # 💡 [의미] 벤치마크 테스트를 진행할 입력 크기들을 담을 리스트
    if n_sizes is None:
        sizes_to_run = [10, 50, 100, 500, 1000, 3000, 5000]  # 💡 [의미] 기본 테스트 크기 배열 설정
    else:
        sizes_to_run = n_sizes  # 💡 [의미] 인자로 들어온 커스텀 테스트 크기 설정

    # ── 2. Validation (유효성 검사) ──
    if not sizes_to_run:  # 💡 [문법] 빈 리스트는 if 문에서 False로 평가 / [의미] 수행할 데이터 크기 목록이 없는 경우
        return "No sizes provided for benchmark."  # 💡 [의미] 에러성 메시지 반환

    # ── 3. Logic Execution (비즈니스 로직 실행) ──
    # 💡 파이썬 현미경 해설
    # 성능 테스트 결과를 표(Table) 모양으로 예쁘게 모아둘 빈 리스트를 만들고, 첫 줄에 표의 헤더를 넣습니다.
    lines: List[str] = []  # 💡 [의미] 출력될 텍스트 줄들을 순서대로 저장할 리스트
    lines.append(SystemMessages.BENCHMARK_HEADER)  # 💡 [의미] 표의 상단 헤더 문자열 추가

    for n in sizes_to_run:  # 💡 [의미] 각 테스트 데이터 크기 n에 대해 순회하며 측정 시작
        data: List[int] = _generate_test_data(n)  # 💡 [의미] 16진수 해시값 추출을 이용해 n 크기의 난수 배열 생성

        data_copy1: List[int] = data[:]  # 💡 [의미] 머지 정렬 시 원래 데이터가 훼손(정렬)되지 않도록 얕은 복사본을 생성
        # 💡 파이썬 현미경 해설
        # `time.perf_counter()`는 성능 측정을 위한 아주 정밀한 시계입니다.
        # 시작 전 시간을 기록하고, 끝난 뒤 다시 시간을 재서 빼면 걸린 시간이 나옵니다.
        start1: float = time.perf_counter()  # 💡 [의미] 머지 정렬 측정 시작 직전의 정밀 타임스탬프 기록
        merge_sort(data_copy1)  # 💡 [의미] 복사본 데이터로 머지 정렬 동작 수행
        merge_time: float = time.perf_counter() - start1  # 💡 [의미] 종료 시각에서 시작 시각을 빼서 경과 시간(초 단위) 계산

        data_copy2: List[int] = data[:]  # 💡 [의미] 퀵 정렬 시 원래 데이터 훼손 방지를 위해 얕은 복사본을 생성
        start2: float = time.perf_counter()  # 💡 [의미] 퀵 정렬 측정 시작 직전의 타임스탬프 기록
        quick_sort(data_copy2)  # 💡 [의미] 복사본 데이터로 퀵 정렬 동작 수행
        quick_time: float = time.perf_counter() - start2  # 💡 [의미] 퀵 정렬 동작의 경과 시간 계산

        winner: str = ""  # 💡 [의미] 성능 비교에서 더 빠른 알고리즘의 이름을 가리킬 변수
        if merge_time < quick_time:  # 💡 [의미] 머지 정렬 시간이 더 짧을 경우
            winner = "Merge"  # 💡 [의미] 머지 정렬 승리
        elif quick_time < merge_time:  # 💡 [의미] 퀵 정렬 시간이 더 짧을 경우
            winner = "Quick"  # 💡 [의미] 퀵 정렬 승리
        else:  # 💡 [의미] 두 정렬 알고리즘의 소요 시간이 완벽히 일치하는 경우
            winner = "Tie"  # 💡 [의미] 무승부 기록

        row: str = SystemMessages.BENCHMARK_ROW.format(
            size=n, 
            merge=merge_time, 
            quick=quick_time, 
            winner=winner
        )  # 💡 [의미] 출력 서식 템플릿에 맞춰 한 줄의 결과 텍스트 포맷팅 생성
        lines.append(row)  # 💡 [의미] 생성된 결과 행을 출력 리스트에 보관

    lines.append(SystemMessages.BENCHMARK_FOOTER)  # 💡 [의미] 표의 하단 꼬리말 추가
    return "\n".join(lines)  # 💡 [문법] 리스트 원소들을 줄바꿈('\n') 기호로 연결해 하나의 거대한 문자열로 합침


def _generate_test_data(n: int) -> List[int]:
    """
    벤치마크용 결정적 테스트 데이터를 생성합니다.
    """
    data: List[int] = []  # 💡 [의미] 해시 기반으로 생성된 정수 난수를 담을 빈 리스트
    for i in range(n):  # 💡 [문법] 0부터 n-1까지 변수 i를 바꾸어가며 반복 / [의미] n개의 데이터 생성을 위해 루프 수행
        hash_val: str = hashlib.sha1(str(i).encode()).hexdigest()  # 💡 [문법] encode()로 바이트화 후 SHA1 해시 수행, 16진수 문자열로 반환
        # 💡 파이썬 현미경 해설
        # `int(..., 16)`은 문자열(hex)을 16진수 숫자로 인식해서 정수로 바꿔주는 마법입니다.
        data.append(int(hash_val[:8], 16))  # 💡 [문법] 슬라이싱 [:8]로 앞 8글자 추출, int(..., 16)으로 10진 정수 변환 / [의미] 생성된 값을 난수 리스트에 추가
    return data  # 💡 [의미] 완료된 테스트용 난수 데이터 리스트를 반환
