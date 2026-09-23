"""
graph.py — 그래프 알고리즘 모듈
================================

이 모듈은 커밋 DAG(방향성 비순환 그래프)에서 수행되는
세 가지 핵심 그래프 알고리즘을 구현합니다:

1. 위상 정렬 (Topological Sort)  — Kahn's Algorithm
2. 최단 경로 탐색 (Shortest Path) — BFS (너비 우선 탐색)
3. 조상 탐색 (Ancestor Search)    — DFS (깊이 우선 탐색)

────────────────────────────────────────────
그래프 알고리즘과 Git의 관계
────────────────────────────────────────────
Git의 커밋 히스토리는 DAG입니다. 이 DAG 위에서:
- `git log`     → 위상 정렬 (부모가 먼저 출력)
- `git log --ancestry-path` → BFS/DFS로 경로 탐색
- `git merge-base` → 공통 조상 탐색 (BFS/DFS)

우리가 구현하는 세 알고리즘은 이런 Git 내부 연산의 기초입니다.

────────────────────────────────────────────
BFS vs DFS — 언제 어떤 것을 쓰는가?
────────────────────────────────────────────
■ BFS (너비 우선 탐색):
  - 시작점에서 가까운 노드부터 방문합니다.
  - 무가중치 그래프에서 최단 경로를 보장합니다.
  - 큐(Queue)를 사용합니다.
  - 공간복잡도: O(V) (최악의 경우 한 레벨의 모든 노드를 큐에 저장)

■ DFS (깊이 우선 탐색):
  - 한 방향으로 끝까지 깊이 들어간 후 되돌아옵니다.
  - 모든 경로를 탐색하거나, 연결 요소를 찾을 때 적합합니다.
  - 스택(Stack) 또는 재귀를 사용합니다.
  - 공간복잡도: O(V) (최악의 경우 경로의 모든 노드를 스택에 저장)

두 알고리즘 모두 시간복잡도는 O(V + E)입니다.
(V = 정점 수, E = 간선 수)
"""

# 💡 파이썬 현미경 해설
# `collections.deque`는 양쪽 끝에서 넣고 뺄 수 있는 매우 빠른 리스트(큐)입니다.
from collections import deque
from typing import Dict, List, Optional, Set
from minigit.models import Commit


def topological_sort(commits_dict: Dict[str, Commit]) -> List[Commit]:
    """
    Kahn's Algorithm으로 커밋 그래프의 위상 정렬을 수행합니다.

    ── 위상 정렬(Topological Sort)이란? ──
    DAG의 모든 노드를, "모든 간선이 앞에서 뒤를 가리키도록" 일렬로 나열하는 것입니다.
    즉, 노드 A에서 노드 B로 가는 간선이 있으면, A는 반드시 B보다 앞에 옵니다.
    """
    # ── 1. Data Refinement (데이터 정제) ──
    # 이 함수는 정제할 입력 데이터가 단순 딕셔너리이므로 패스합니다.

    # ── 2. Validation (유효성 검사) ──
    # 💡 파이썬 현미경 해설
    # `if not commits_dict:` 만약 딕셔너리가 비어있다면, 빈 리스트를 즉시 반환합니다.
    if not commits_dict:  # 💡 [문법] 빈 딕셔너리는 False로 평가 / [의미] 정렬할 커밋이 없으면 빈 리스트 즉시 반환
        return []

    # ── 3. Logic Execution (비즈니스 로직 실행) ──
    # 💡 파이썬 현미경 해설
    # `in_degree`는 "나를 가리키는 화살표(진입 차수)가 몇 개인지" 세어두는 딕셔너리입니다.
    in_degree: Dict[str, int] = {}  # 💡 [의미] 각 커밋의 진입 차수(나를 가리키는 자식의 수)를 기록할 빈 딕셔너리
    
    # 💡 파이썬 현미경 해설
    # `for ... in ...:` (for문)은 딕셔너리 안에 있는 것을 처음부터 끝까지 하나씩 꺼내며 반복합니다.
    # 먼저 모든 커밋의 화살표 개수를 0으로 초기화합니다.
    for commit_hash in commits_dict:  # 💡 [의미] 모든 커밋 해시에 대해 순회 시작
        in_degree[commit_hash] = 0  # 💡 [의미] 우선 모든 커밋의 진입 차수 초기값을 0으로 설정

    # 💡 파이썬 현미경 해설
    # `.items()`를 쓰면 딕셔너리에서 이름(키)과 내용(값)을 한꺼번에 꺼낼 수 있습니다.
    for commit_hash, commit in commits_dict.items():  # 💡 [문법] items()로 (키, 값) 쌍을 꺼내 순회 / [의미] 전체 커밋의 부모 관계 조사
        # 각 커밋이 가리키고 있는 부모들을 찾아가서, 부모의 '진입 차수'를 1씩 올려줍니다.
        for parent_hash in commit.parents:  # 💡 [의미] 현재 커밋의 각 부모들을 순회
            if parent_hash in in_degree:  # 💡 [의미] 부모 커밋이 전체 커밋 딕셔너리 내에 존재하는 경우
                in_degree[parent_hash] += 1  # 💡 [의미] 부모의 진입 차수(선행 관계 조건 수)를 1 증가시킴

    # 💡 파이썬 현미경 해설
    # 아무도 나를 가리키지 않는 노드(진입 차수가 0인 노드 = 즉, 최신 커밋)들을 담을 큐를 만듭니다.
    queue: deque[str] = deque()  # 💡 [의미] 진입 차수가 0인(즉, 나를 가리키는 자식이 없는 최신 커밋)들을 모을 더블 엔디드 큐(deque) 생성
    for commit_hash, degree in in_degree.items():  # 💡 [의미] 계산된 진입 차수 테이블 순회
        # `==`: 숫자가 같은지 비교
        if degree == 0:  # 💡 [의미] 진입 차수가 0인 경우
            queue.append(commit_hash)  # 💡 [의미] 큐의 맨 오른쪽에 해당 커밋 해시 추가

    result: List[Commit] = []  # 💡 [의미] 위상 정렬된 최종 커밋 객체들을 보관할 리스트
    
    # 💡 파이썬 현미경 해설
    # `while queue:` 큐 안에 처리할 데이터가 남아있는 동안 계속 반복합니다.
    while queue:  # 💡 [의미] 큐에 처리할 커밋이 남아있는 동안 계속 반복
        # `.popleft()`는 큐의 가장 왼쪽(먼저 들어온 것)을 뽑아냅니다.
        current_hash: str = queue.popleft()  # 💡 [문법] popleft()는 큐의 가장 왼쪽 원소를 제거하고 반환 (FIFO) / [의미] 선행 노드가 해소된 커밋 하나 추출
        current_commit: Commit = commits_dict[current_hash]  # 💡 [의미] 추출한 해시로 실제 커밋 객체를 조회
        # 결과 리스트에 차곡차곡 담습니다.
        result.append(current_commit)  # 💡 [의미] 결과 리스트에 커밋 등록

        # 방금 빼낸 커밋이 가리키고 있던 부모들의 화살표를 1개씩 지워줍니다.
        for parent_hash in current_commit.parents:  # 💡 [의미] 방금 처리한 커밋의 부모들을 순회
            if parent_hash in in_degree:  # 💡 [의미] 부모의 진입 차수 정보가 테이블에 있는 경우
                in_degree[parent_hash] -= 1  # 💡 [의미] 자식 하나가 정렬되었으므로 부모의 진입 차수를 1 감소시킴
                # 만약 화살표가 0개가 되었다면(선행 조건이 모두 끝났다면) 큐에 넣습니다!
                if in_degree[parent_hash] == 0:  # 💡 [의미] 부모를 가리키는 자식(선행 노드)이 모두 정렬 완료된 경우
                    queue.append(parent_hash)  # 💡 [의미] 부모 커밋도 큐에 넣어 정렬 순서에 대기시킴

    # 💡 파이썬 현미경 해설
    # `.reverse()`는 리스트의 순서를 완전히 뒤집어줍니다. (과거 -> 최신 순으로 보기 위함)
    result.reverse()  # 💡 [문법] reverse()는 리스트 순서를 역순으로 바꿈 / [의미] git log 형식에 맞춰 과거 -> 최신 순서가 되도록 최종 조율
    return result  # 💡 [의미] 정렬 완료된 커밋 리스트 반환


def find_shortest_path(commits_dict: Dict[str, Commit], hash1: str, hash2: str) -> Optional[List[str]]:
    """
    두 커밋 사이의 최단 경로를 BFS로 찾습니다.
    """
    # ── 1. Data Refinement (데이터 정제) ──
    clean_hash1: str = hash1.strip()  # 💡 [의미] 시작 커밋 해시 경로의 양끝 공백 제거
    clean_hash2: str = hash2.strip()  # 💡 [의미] 도착 커밋 해시 경로의 양끝 공백 제거

    # ── 2. Validation (유효성 검사) ──
    # `not in` 연산자를 사용해 딕셔너리 안에 이 커밋 해시가 존재하는지 검사합니다.
    if clean_hash1 not in commits_dict or clean_hash2 not in commits_dict:  # 💡 [의미] 시작점이나 도착점 커밋이 히스토리에 없는 경우
        return None  # 💡 [의미] 경로 탐색 불가로 즉시 None 반환
    if clean_hash1 == clean_hash2:  # 💡 [의미] 시작점과 도착점이 같은 경우
        # 💡 파이썬 현미경 해설: 대괄호 `[]`로 문자열 하나를 감싸서 크기가 1인 리스트를 반환합니다.
        return [clean_hash1]  # 💡 [의미] 시작점 하나만 포함된 리스트 반환

    # ── 3. Logic Execution (비즈니스 로직 실행) ──
    # 💡 파이썬 현미경 해설
    # BFS(너비 우선 탐색) 원리: 
    # 시작점에서 가까운 곳(이웃)부터 먼저 얕고 넓게 싹 훑어보는 탐색 방식입니다.
    # 마치 잔잔한 호수에 돌을 던졌을 때 물결이 퍼져나가는 모습과 비슷합니다.
    # 거리를 1칸씩 일정하게 늘려가며 탐색하므로 가장 먼저 목표를 찾았을 때가 무조건 최단 경로가 됩니다!
    #
    # BFS를 위해 단방향 그래프를 "양방향" 인접 리스트(adjacency list)로 변환합니다.
    adjacency: Dict[str, List[str]] = {}  # 💡 [의미] BFS 탐색을 위한 양방향 인접 리스트 딕셔너리 생성
    for commit_hash in commits_dict:  # 💡 [의미] 전체 커밋에 대해 순회하며
        adjacency[commit_hash] = []  # 💡 [의미] 이웃 노드를 저장할 빈 리스트로 초기화

    for commit_hash, commit in commits_dict.items():  # 💡 [의미] 각 커밋과 그들의 부모를 순회하며 양방향 간선 정의
        for parent_hash in commit.parents:  # 💡 [의미] 현재 커밋의 각 부모 해시에 대해
            if parent_hash in commits_dict:  # 💡 [의미] 부모 해시가 전체 커밋 딕셔너리에 실재할 경우
                # 💡 파이썬 현미경 해설: `append`로 리스트의 끝에 요소를 추가합니다. (양쪽 모두 추가)
                adjacency[commit_hash].append(parent_hash)  # 💡 [의미] 커밋 -> 부모 방향 간선 추가
                adjacency[parent_hash].append(commit_hash)  # 💡 [의미] 부모 -> 커밋 방향 간선 추가 (양방향화)

    # 💡 파이썬 현미경 해설
    # `visited`는 이미 방문한 곳을 기록하는 `set`(세트)입니다. 세트는 탐색 속도가 매우 빠릅니다.
    visited: Set[str] = set()  # 💡 [의미] 중복 방문을 막기 위해 이미 탐색한 커밋을 저장할 빈 세트(집합) 생성
    
    # `parent_map`은 "내가 어디서 왔는지(누가 나를 발견했는지)" 발자취를 기록하는 딕셔너리입니다.
    parent_map: Dict[str, str] = {}  # 💡 [의미] 최단 경로 역추적을 위해 (자식 노드 -> 나를 발견해준 부모 노드) 관계를 기록할 딕셔너리
    queue: deque[str] = deque()  # 💡 [의미] 너비 우선 탐색(BFS) 대기열 큐 생성

    # 시작점을 큐에 넣고, 방문했다고 표시합니다.
    queue.append(clean_hash1)  # 💡 [의미] 시작 노드를 대기열 큐에 탑재
    visited.add(clean_hash1)  # 💡 [의미] 시작 노드를 방문 처리
    # `bool`(불리언) 타입. True(참) / False(거짓) 중 하나만 가집니다.
    found: bool = False  # 💡 [의미] 최단 경로를 찾았는지 여부를 판단하는 플래그 변수

    while queue:  # 💡 [의미] 대기열 큐에 탐색할 노드가 남아있는 동안 반복
        current: str = queue.popleft()  # 💡 [의미] 현재 깊이에서 가장 먼저 큐에 들어간 노드 추출
        
        # 💡 파이썬 현미경 해설
        # 찾고자 하는 목표 지점에 도달했다면? `break`를 써서 반복문(while)을 즉시 탈출합니다!
        if current == clean_hash2:  # 💡 [의미] 꺼낸 노드가 도착 노드와 정확히 일치하는 경우
            found = True  # 💡 [의미] 도착했음을 알리고
            break  # 💡 [문법] break는 현재 수행 중인 가장 안쪽 루프를 즉시 중단 / [의미] BFS 루프 즉시 중단

        # 내 주변에 연결된 이웃 노드들을 가져옵니다. (없으면 빈 리스트 `[]` 반환)
        neighbors: List[str] = adjacency.get(current, [])  # 💡 [문법] get()은 키가 없어도 에러 대신 기본값(여기선 []) 반환 / [의미] 현재 노드의 양방향 이웃 노드 리스트 획득
        # 알파벳 순서대로 탐색하기 위해 정렬합니다.
        sorted_neighbors: List[str] = _insertion_sort_strings(neighbors)  # 💡 [의미] 결정론적 탐색 순서를 위해 이웃들을 사전식 순서로 정렬

        for neighbor in sorted_neighbors:  # 💡 [의미] 정렬된 이웃 노드들을 순회
            # 아직 방문하지 않은 이웃이라면
            if neighbor not in visited:  # 💡 [의미] 아직 방문한 적이 없는 새로운 노드인 경우
                visited.add(neighbor)             # 방문 표시!  # 💡 [의미] 방문 목록에 등록
                parent_map[neighbor] = current    # "이웃아, 널 발견한 건 나(current)야" 하고 기록!  # 💡 [의미] neighbor로 도달한 직전 이전 노드가 current임을 저장
                queue.append(neighbor)            # 다음 탐색 대기열에 추가!  # 💡 [의미] 다음 단계 너비 탐색을 위해 대기열 큐에 등록

    if not found:  # 💡 [의미] BFS 탐색을 끝마칠 때까지 도착점을 찾지 못한 경우
        return None  # 💡 [의미] 경로가 존재하지 않으므로 None 반환

    # 💡 파이썬 현미경 해설
    # 목표 지점부터 시작해서 거꾸로 발자취(`parent_map`)를 되짚어 오며 경로 리스트를 만듭니다.
    path: List[str] = []  # 💡 [의미] 도착점에서 시작점으로 되짚어가며 만들어질 경로 리스트
    current_trace: str = clean_hash2  # 💡 [의미] 도착점부터 역추적 시작
    
    # 시작점에 도달할 때까지 계속 거슬러 올라갑니다 (`!=`는 "다르다"는 뜻입니다)
    while current_trace != clean_hash1:  # 💡 [의미] 시작점에 다다르기 전까지 루프 반복
        path.append(current_trace)  # 💡 [의미] 추적 경로 리스트에 현재 추적 중인 노드 추가
        current_trace = parent_map[current_trace]  # 💡 [의미] 이 노드를 가리켜준 직전 부모 노드로 한 단계 올라감
        
    path.append(clean_hash1)  # 💡 [의미] 마지막으로 경로에 시작점 노드 추가
    path.reverse()  # 거꾸로 거슬러 왔으므로, 다시 뒤집어주면 올바른 경로가 됩니다.  # 💡 [의미] 도착점->시작점 순서로 수집되었으므로, 원래 목적대로 시작점->도착점 순서가 되도록 뒤집음

    return path  # 💡 [의미] 최종 최단 경로 리스트 반환


def _insertion_sort_strings(arr: List[str]) -> List[str]:
    """
    문자열 배열을 삽입 정렬로 정렬합니다.
    """
    # 💡 파이썬 현미경 해설
    # `arr[:]` : 슬라이싱을 이용해 원본 리스트를 똑같이 복사(얕은 복사)합니다.
    # 원본을 훼손하지 않기 위함입니다.
    result: List[str] = arr[:]  # 💡 [의미] 원본 리스트를 그대로 복사하여 훼손 방지
    
    # 💡 파이썬 현미경 해설
    # `range(1, len(result))` : 1부터 (배열 길이 - 1)까지 숫자를 하나씩 만들어냅니다.
    for i in range(1, len(result)):  # 💡 [의미] 두 번째 요소부터 리스트 끝까지 비교 기준(key)으로 정해 루프 수행
        key: str = result[i]  # 💡 [의미] 현재 삽입 대상이 될 기준 문자열 값
        j: int = i - 1  # 💡 [의미] 기준값 바로 왼쪽(앞의 요소) 인덱스
        # 내 앞의 글자들이 나보다 크면, 한 칸씩 뒤로 미룹니다.
        while j >= 0 and result[j] > key:  # 💡 [의미] 배열 범위 내이고, 앞의 문자열이 현재 기준 문자열보다 큰(사전식으로 뒤인) 동안 반복
            result[j + 1] = result[j]  # 💡 [의미] 앞의 큰 요소를 오른쪽으로 한 칸 밀어냄
            j -= 1  # 💡 [의미] 그 앞의 요소와 다시 비교하기 위해 인덱스를 감소
        # 적절한 자리를 찾아 쏙 들어갑니다! (삽입 정렬)
        result[j + 1] = key  # 💡 [의미] 미는 것이 멈춘 적합한 빈 공간에 기준값 문자열을 쏙 끼워 넣음 (삽입 정렬)
        
    return result  # 💡 [의미] 오름차순 사전 정렬된 새로운 리스트 반환


def find_ancestors(commits_dict: Dict[str, Commit], commit_hash: str) -> List[str]:
    """
    특정 커밋의 모든 조상을 DFS로 찾습니다.
    """
    # ── 1. Data Refinement (데이터 정제) ──
    clean_hash: str = commit_hash.strip()  # 💡 [의미] 대상 커밋 해시 문자열의 공백 정리

    # ── 2. Validation (유효성 검사) ──
    if clean_hash not in commits_dict:  # 💡 [의미] 대상 커밋이 프로젝트 내에 존재하지 않는 경우
        return []  # 💡 [의미] 조상이 존재할 수 없으므로 빈 리스트 반환

    # ── 3. Logic Execution (비즈니스 로직 실행) ──
    # 💡 파이썬 현미경 해설
    # DFS(깊이 우선 탐색) 원리:
    # 여러 갈래 길이 있을 때 한쪽 길을 선택해서 막다른 길이 나올 때까지 끝까지 파고드는 방식입니다.
    # 미로 찾기에서 한 손을 벽에 짚고 계속 전진하는 것과 같습니다.
    # 우리는 커밋의 '모든 과거 조상'을 샅샅이 뒤져야 하므로 끝까지 파고드는 DFS가 매우 적합합니다!
    ancestors: List[str] = []  # 💡 [의미] DFS를 통해 탐색된 조상 커밋 해시들을 담을 결과 리스트
    visited: Set[str] = set()  # 💡 [의미] 무한 루프나 중복 방문을 예방하기 위한 방문 세트 생성
    # 💡 파이썬 현미경 해설
    # DFS(깊이 우선 탐색)는 큐 대신 "스택(Stack)"을 사용합니다. 파이썬에서는 그냥 리스트 `[]`를 쓰면 됩니다.
    stack: List[str] = []  # 💡 [의미] 깊이 우선 탐색(DFS)의 역추적을 위한 스택(파이썬 리스트 사용) 생성

    start_commit: Commit = commits_dict[clean_hash]  # 💡 [의미] 전체 딕셔너리에서 대상 커밋 객체 획득
    for parent_hash in start_commit.parents:  # 💡 [의미] 시작 커밋의 모든 부모 커밋 해시 순회
        if parent_hash in commits_dict:  # 💡 [의미] 부모가 커밋 딕셔너리에 존재하는 유효한 노드인 경우
            # 💡 파이썬 현미경 해설
            # 깊게 파고들기 위해 출발점의 부모들을 스택에 쌓아둡니다.
            stack.append(parent_hash)  # 💡 [의미] 스택의 가장 오른쪽에 추가하여 최초 방문 후보로 대기

    while stack:  # 💡 [의미] 탐색 스택에 방문할 노드가 남아있는 동안 반복
        # 💡 파이썬 현미경 해설
        # `.pop()`은 리스트의 **맨 마지막** 요소를 뽑아냅니다. (가장 최근에 넣은 것을 먼저 꺼냄 = LIFO)
        current: str = stack.pop()  # 💡 [문법] pop()은 리스트의 가장 오른쪽(마지막) 원소를 꺼내며 제거 (LIFO) / [의미] 깊이 우선 탐색을 위해 가장 최근 스택 노드 추출
        
        # 💡 파이썬 현미경 해설
        # `continue`는 "이번 바퀴는 여기서 건너뛰고 바로 다음 바퀴로 넘어가라"는 뜻입니다.
        if current in visited:  # 💡 [의미] 이미 다른 경로를 통해 조상으로 판정 및 방문이 끝난 경우
            continue  # 💡 [문법] continue는 아래 남은 코드를 건너뛰고 다음 반복 루프로 즉시 이동 / [의미] 중복 탐색 건너뛰기

        visited.add(current)  # 💡 [의미] 새로운 방문 노드로 세트에 등록
        ancestors.append(current)  # 💡 [의미] 조상 리스트에 추가

        current_commit: Commit = commits_dict[current]  # 💡 [의미] 현재 방문 중인 커밋의 객체 조회
        # 방금 꺼낸 노드의 부모들을 다시 스택에 욱여넣습니다. (점점 깊이 들어갑니다)
        for parent_hash in current_commit.parents:  # 💡 [의미] 현재 커밋의 부모들을 순회하며 깊은 탐색 준비
            if parent_hash in commits_dict and parent_hash not in visited:  # 💡 [의미] 유효한 부모 노드이면서 아직 방문하지 않은 경우
                stack.append(parent_hash)  # 💡 [의미] 우선 스택에 쌓아서 더 깊은 탐색을 대기하게 함

    return ancestors  # 💡 [의미] 모든 조상 노드 해시가 담긴 리스트 반환
