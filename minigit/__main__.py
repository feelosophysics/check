"""
__main__.py — Mini Git CLI 진입점 (REPL)
======================================

패키지로 실행할 때의 진입점입니다. (python -m minigit)
REPL(Read-Eval-Print Loop) 패턴으로 동작하며, 
모든 라우팅과 상태 관리를 MiniGitCLI 클래스에 캡슐화합니다.

# 💡 파이썬 현미경 해설
# `__main__.py`는 파이썬에서 특별한 이름입니다.
# 어떤 폴더(여기서는 minigit)를 통째로 프로그램처럼 실행하라고 명령했을 때
# 파이썬이 가장 먼저 찾아서 실행하는 '메인 대문' 역할을 합니다!
"""

# 💡 파이썬 현미경 해설
# `import ...` 는 다른 사람이 만들어 둔 유용한 도구나
# 우리가 다른 파일에 만들어둔 코드들을 가져와서 쓰겠다는 뜻입니다.
import shlex
import datetime
from typing import List, Optional, Dict, Set

# `from 폴더.파일 import 이름` 형태입니다.
from minigit.models import Repository, Commit
from minigit.graph import topological_sort, find_shortest_path, find_ancestors
from minigit.sorting import merge_sort, benchmark_sorts
from minigit.diff import diff_files
from minigit.constants import CommandType, SystemMessages, ErrorMessages, ConfigConstants


# 💡 파이썬 현미경 해설
# `def`로 함수를 정의합니다.
# `ts: float`는 'ts'라는 이름의 변수가 들어오는데, 그건 소수점이 있는 숫자(float)라는 뜻입니다.
def format_timestamp(ts: float) -> str:
    """
    Unix 타임스탬프를 사람이 읽을 수 있는 형식으로 변환합니다.
    """
    # 💡 파이썬 현미경 해설
    # 컴퓨터는 시간을 "1970년 1월 1일부터 몇 초가 지났나?"(Unix Timestamp)로 기억합니다.
    # 그걸 우리가 읽을 수 있는 날짜 객체로 바꾼 다음,
    dt: datetime.datetime = datetime.datetime.fromtimestamp(ts)  # 💡 [문법] fromtimestamp()는 실수를 날짜시간 객체로 변환 / [의미] 타임스탬프를 구체적 시간 데이터로 반환
    # `.strftime`을 써서 년-월-일 시:분:초 형태로 예쁘게 화장시켜 돌려줍니다!
    return dt.strftime(ConfigConstants.TIME_FORMAT)  # 💡 [문법] strftime()은 서식 코드에 맞춰 문장으로 변환 / [의미] 지정한 포맷("%Y-%m-%d %H:%M:%S")대로 포맷팅하여 리턴


class MiniGitCLI:
    """
    Mini Git CLI의 상태와 명령어 라우팅을 캡슐화하는 클래스.
    """
    # 💡 파이썬 현미경 해설
    # 이 프로그램이 처음 켜질 때 한 번 실행되는 초기화 설정 버튼입니다.
    def __init__(self) -> None:
        """
        CLI 초기화 시 빈 저장소를 생성합니다.
        """
        # 내 주머니(`self.repo`)에 텅 빈 저장소 붕어빵(`Repository()`)을 하나 구워 넣습니다.
        self.repo: Repository = Repository()  # 💡 [의미] 새로운 빈 미니깃 저장소 인스턴스를 CLI 상태 주머니(self)에 할당

    def parse_input(self, user_input: str) -> List[str]:
        """
        사용자 입력을 명령어와 인자로 분리합니다.
        """
        # ── 1. Data Refinement (데이터 정제) ──
        # 사용자가 엔터를 잘못 치거나 양옆에 띄어쓰기를 넣었을 수 있으니 깔끔하게 잘라줍니다.
        clean_input: str = user_input.strip()  # 💡 [의미] 사용자가 타이핑한 텍스트의 양끝 빈칸 및 줄바꿈 기호를 깨끗이 제거

        # ── 2. Validation (유효성 검사) ──
        # 아무것도 안 치고 엔터만 쳤다면 빈 리스트를 돌려줍니다.
        if not clean_input:  # 💡 [의미] 아무것도 입력하지 않고 엔터만 누른 경우
            return []  # 💡 [의미] 빈 리스트 반환하여 무시하도록 처리

        # ── 3. Logic Execution (비즈니스 로직 실행) ──
        tokens: List[str] = []  # 💡 [의미] 파싱된 토큰(단어)들을 저장할 리스트 준비
        # 💡 파이썬 현미경 해설
        # `try ... except ...`: 불안한 코드 안전망!
        try:
            # `shlex.split()`은 사용자가 따옴표(" ")로 묶어서 친 문장은 하나의 단어로 똑똑하게 쪼개주는 도구입니다.
            # 예: commit "hello world" -> ["commit", "hello world"]
            tokens = shlex.split(clean_input)  # 💡 [의미] shlex 모듈을 이용해 띄어쓰기로 쪼개되, 큰따옴표 내부는 한 단어로 온전히 파싱
        except ValueError:
            # 만약 사용자가 따옴표를 하나만 치는 등 문법을 틀려서 에러가 나면 뻗지 말고,
            # 그냥 단순 무식하게 띄어쓰기 기준으로 쪼개버리라는 뜻입니다!
            tokens = clean_input.split()  # 💡 [문법] split()은 공백 기준 문자열 분할 / [의미] 일반 띄어쓰기를 기준으로 쪼개는 차선책 적용

        return tokens  # 💡 [의미] 쪼개진 단어 리스트 반환

    # 💡 파이썬 현미경 해설
    # 아래부터는 사용자가 친 명령어에 따라 각기 다른 함수들이 출동해서 일을 처리합니다.
    # 사용자가 친 단어들의 목록이 `args: List[str]`로 전달됩니다.
    def handle_init(self, args: List[str]) -> str:
        # ── 2. Validation (유효성 검사) ──
        # args 안에 이름이 없으면 에러를 반환합니다.
        if len(args) < 1:  # 💡 [의미] 초기화에 필요한 이름 인자가 전달되지 않은 경우
            return ErrorMessages.INVALID_INIT
            
        # ── 3. Logic Execution (비즈니스 로직 실행) ──
        # 첫 번째 단어(인덱스 0번)를 유저 이름으로 삼습니다. 파이썬은 숫자를 0부터 셉니다!
        user_name: str = args[0]  # 💡 [의미] 입력받은 첫 번째 인자를 사용자 이름으로 설정
        # 진짜 일을 하는 건 내 주머니 속 `repo`입니다.
        return self.repo.init(user_name)  # 💡 [의미] 저장소(Repository) 인스턴스에 사용자 정보를 주고 초기화 동작 실행

    def handle_commit(self, args: List[str]) -> str:
        if len(args) < 1:  # 💡 [의미] 커밋 메시지가 입력되지 않은 경우
            return ErrorMessages.INVALID_COMMIT
            
        # 💡 파이썬 현미경 해설
        # `" ".join(args)`는 쪼개져 있던 단어들 사이에 다시 스페이스바(" ")를 넣어서 하나의 문장으로 이어 붙집니다.
        message: str = " ".join(args)  # 💡 [의미] 쪼개졌던 메시지 인자들을 한 문장으로 다시 결합
        return self.repo.commit(message)  # 💡 [의미] 해당 메시지로 새 커밋 발행 요청

    def handle_branch(self, args: List[str]) -> str:
        if len(args) < 1:  # 💡 [의미] 생성할 브랜치 명이 지정되지 않은 경우
            return ErrorMessages.INVALID_BRANCH
            
        return self.repo.branch(args[0])  # 💡 [의미] 지정한 이름으로 새 브랜치 포인터 생성 요청

    def handle_switch(self, args: List[str]) -> str:
        if len(args) < 1:  # 💡 [의미] 전환할 타깃 브랜치 명이 누락된 경우
            return ErrorMessages.INVALID_SWITCH
            
        return self.repo.switch(args[0])  # 💡 [의미] 타깃 브랜치로 switch 요청

    def handle_log(self, args: List[str]) -> str:
        if not self.repo.initialized:  # 💡 [의미] 미니깃 저장소가 아직 초기화되지 않은 경우
            return ErrorMessages.REPO_NOT_INIT

        commits_dict: Dict[str, Commit] = self.repo.get_all_commits()  # 💡 [의미] 전체 커밋들이 저장된 해시 테이블을 조회
        if not commits_dict:  # 💡 [의미] 커밋 히스토리가 아예 빈 경우
            return SystemMessages.NO_COMMITS_YET

        # ── 3. Logic Execution (비즈니스 로직 실행) ──
        sort_by: Optional[str] = None  # 💡 [의미] 정렬 기준을 저장할 변수 (기본값은 지정 없음)
        
        # 💡 파이썬 현미경 해설
        # args(입력한 단어들)를 하나씩 살펴보며 "--sort-by="로 시작하는 단어가 있는지 찾습니다.
        for arg in args:  # 💡 [의미] 입력 인자 중 정렬 관련 옵션이 있는지 검사
            if arg.startswith("--sort-by="):  # 💡 [문법] startswith()는 해당 서브스트링으로 시작하는지 판별 / [의미] 정렬 기준 옵션 매칭
                # `.split("=", 1)`은 "="를 기준으로 딱 한 번만 쪼개라는 뜻입니다.
                # 쪼개면 ["--sort-by", "date"] 처럼 2개가 나오는데, 그 중 1번째(즉 "date" 부분)를 가져옵니다.
                sort_by = arg.split("=", 1)[1].lower()  # 💡 [의미] 등호(=)를 기준으로 쪼개어 뒤편 값을 소문자로 추출

        sorted_commits: List[Commit] = []  # 💡 [의미] 정렬이 완료된 커밋들이 순서대로 담길 리스트
        
        if sort_by is not None:  # 💡 [의미] 사용자가 명시적인 정렬 옵션(--sort-by)을 입력한 경우
            # 딕셔너리에 들어있던 커밋 객체들만 싹 모아서 리스트로 바꿉니다.
            commits_list: List[Commit] = list(commits_dict.values())  # 💡 [문법] values()로 딕셔너리의 값만 뽑아 list로 형변환 / [의미] 정렬용 커밋 배열 생성
            
            # 💡 파이썬 현미경 해설
            # `lambda`는 "이름이 없는 초미니 함수"입니다.
            # `lambda c: c.timestamp` = "c가 들어오면 c.timestamp를 내뱉는 함수"라는 뜻입니다!
            if sort_by == "date":  # 💡 [의미] 시간순 정렬 조건인 경우
                sorted_commits = merge_sort(commits_list, key_func=lambda c: c.timestamp)  # 💡 [문법] lambda 함수로 정렬 기준 지정 / [의미] 머지 정렬로 시간순 정렬
            elif sort_by == "author":  # 💡 [의미] 작성자 알파벳순 정렬 조건인 경우
                sorted_commits = merge_sort(commits_list, key_func=lambda c: c.author.lower())  # 💡 [의미] 작성자명 소문자 기준 머지 정렬
            else:  # 💡 [의미] 정해지지 않은 엉뚱한 정렬 키를 넘겨준 경우
                return ErrorMessages.INVALID_SORT_KEY.format(key=sort_by)
        else:
            # 아무 옵션이 없으면 기본적으로 우리가 만든 위상 정렬을 수행합니다.
            sorted_commits = topological_sort(commits_dict)  # 💡 [의미] 정렬 지정을 안 했을 때 Kahn's 알고리즘으로 위상 정렬 수행

        # 💡 파이썬 현미경 해설
        # 각 커밋이 어떤 브랜치들에 연결되어 있는지 찾기 위해 '해시 -> 브랜치 목록' 딕셔너리를 만듭니다.
        hash_to_branches: Dict[str, List[str]] = {}  # 💡 [의미] 커밋 해시별로 물려있는 브랜치 명단을 모을 딕셔너리
        for branch_name, branch_hash in self.repo.branches.items():  # 💡 [의미] 브랜치 테이블을 순회하며
            if branch_hash is not None:  # 💡 [의미] 가리키는 커밋 해시가 실재하는 경우
                if branch_hash not in hash_to_branches:  # 💡 [의미] 해당 커밋 해시가 딕셔너리에 처음 등록되는 경우
                    hash_to_branches[branch_hash] = []  # 💡 [의미] 빈 리스트로 초기화
                hash_to_branches[branch_hash].append(branch_name)  # 💡 [의미] 브랜치명 추가

        lines: List[str] = []  # 💡 [의미] 로그 출력 줄들을 모을 빈 리스트
        for commit in sorted_commits:  # 💡 [의미] 정렬된 각 커밋에 대해 순회
            time_str: str = format_timestamp(commit.timestamp)  # 💡 [의미] 유닉스 타임스탬프를 예쁜 텍스트 포맷으로 변경
            
            branch_labels: List[str] = hash_to_branches.get(commit.hash, [])  # 💡 [의미] 이 커밋 해시를 가리키는 브랜치 목록 획득
            branch_str: str = ""  # 💡 [의미] 출력에 추가할 브랜치 괄호 문자열
            if branch_labels:  # 💡 [의미] 해당 커밋을 가리키는 브랜치가 하나라도 존재하는 경우
                branch_str = " [" + ", ".join(branch_labels) + "]"  # 💡 [의미] 쉼표로 연결해서 괄호 처리

            head_marker: str = ""  # 💡 [의미] HEAD가 물려있는지 알려줄 마커 문자열
            # 현재 머무는 브랜치가 가리키는 곳에 (HEAD) 표시를 붙여줍니다.
            if self.repo.head is not None and self.repo.branches.get(self.repo.head) == commit.hash:  # 💡 [의미] 현재 브랜치의 해시가 이 커밋의 해시인 경우
                head_marker = " (HEAD)"  # 💡 [의미] HEAD 마크 추가

            lines.append(f"commit {commit.hash} ({commit.author}, {time_str}){branch_str}{head_marker}")  # 💡 [의미] 커밋 한 줄 정보 요약 추가
            lines.append(f"  {commit.message}")  # 💡 [의미] 커밋 메시지 들여쓰기 출력
            lines.append("")  # 💡 [의미] 커밋 간 구분을 위한 빈 줄

        return "\n".join(lines).rstrip()  # 💡 [문법] rstrip()은 문자열 오른편 공백/개행 제거 / [의미] 마지막 여분의 줄바꿈을 지우고 반환

    def handle_path(self, args: List[str]) -> str:
        if not self.repo.initialized:  # 💡 [의미] 미니깃이 아직 시작되지 않은 상태인 경우
            return ErrorMessages.REPO_NOT_INIT

        if len(args) < 2:  # 💡 [의미] 시작 해시와 끝 해시 2개가 온전히 들어오지 않은 경우
            return ErrorMessages.INVALID_PATH

        hash1: str = args[0]  # 💡 [의미] 시작점 해시
        hash2: str = args[1]  # 💡 [의미] 목적지 해시

        if hash1 not in self.repo.commits:  # 💡 [의미] 시작점 커밋이 히스토리에 없는 경우
            return ErrorMessages.UNKNOWN_COMMIT.format(hash=hash1)
        if hash2 not in self.repo.commits:  # 💡 [의미] 목적지 커밋이 히스토리에 없는 경우
            return ErrorMessages.UNKNOWN_COMMIT.format(hash=hash2)

        path: Optional[List[str]] = find_shortest_path(self.repo.commits, hash1, hash2)  # 💡 [의미] BFS를 통해 두 노드 간 최단 경로 탐색

        if path is None:  # 💡 [의미] 두 경로가 연결되어 있지 않은 경우
            return SystemMessages.NO_PATH

        path_str: str = " -> ".join(path)  # 💡 [의미] 경로 리스트를 화살표 모양으로 연결
        return f"Path: {path_str}"  # 💡 [의미] 최종 경로 텍스트 반환

    def handle_ancestors(self, args: List[str]) -> str:
        if not self.repo.initialized:
            return ErrorMessages.REPO_NOT_INIT

        if len(args) < 1:  # 💡 [의미] 대상을 지정할 커밋 해시가 입력되지 않은 경우
            return ErrorMessages.INVALID_ANCESTORS

        commit_hash: str = args[0]  # 💡 [의미] 조사할 커밋 해시

        if commit_hash not in self.repo.commits:  # 💡 [의미] 조사할 커밋 해시가 유효하지 않은 경우
            return ErrorMessages.UNKNOWN_COMMIT.format(hash=commit_hash)

        ancestors: List[str] = find_ancestors(self.repo.commits, commit_hash)  # 💡 [의미] DFS를 이용해 해당 커밋의 조상 리스트 탐색

        if not ancestors:  # 💡 [의미] 조상 커밋이 아예 발견되지 않은 경우
            return f"No ancestors found for commit {commit_hash}"

        lines: List[str] = [f"Ancestors of {commit_hash}:"]  # 💡 [의미] 출력용 라인 리스트 헤더
        for ancestor_hash in ancestors:  # 💡 [의미] 각 조상 커밋 해시를 순회하며 출력 정보 조립
            commit: Optional[Commit] = self.repo.get_commit(ancestor_hash)  # 💡 [의미] 조상 커밋 객체 조회
            if commit is not None:  # 💡 [의미] 조상 커밋 객체가 실재할 경우
                time_str: str = format_timestamp(commit.timestamp)  # 💡 [의미] 보기 좋은 날짜로 변환
                lines.append(f"  {commit.hash} ({commit.author}, {time_str}): {commit.message}")  # 💡 [의미] 세부 조상 정보 라인 추가
            else:
                lines.append(f"  {ancestor_hash}")  # 💡 [의미] 객체가 없으면 해시만 표시

        return "\n".join(lines)  # 💡 [의미] 전체 조상 목록 문자열로 병합 반환

    def handle_search(self, args: List[str]) -> str:
        if not self.repo.initialized:
            return ErrorMessages.REPO_NOT_INIT

        if len(args) < 1:  # 💡 [의미] 검색어 인자가 입력되지 않은 경우
            return ErrorMessages.INVALID_SEARCH

        search_type: str = ""  # 💡 [의미] 출력에 표시할 검색 타입 설명명
        commit_hashes: Set[str] = set()  # 💡 [의미] 검색 결과를 만족하는 커밋 해시들을 담을 세트

        if args[0].startswith("--author="):  # 💡 [의미] 작성자 조건 검색인 경우
            author_name: str = args[0].split("=", 1)[1]  # 💡 [의미] 작성자명 값 추출
            commit_hashes = self.repo.inverted_index.search_author(author_name)  # 💡 [의미] 역색인 구조를 통해 해당 작성자 커밋 검색
            search_type = f"author '{author_name}'"  # 💡 [의미] 작성자 검색 타입 텍스트 기입
        else:  # 💡 [의미] 일반 키워드 검색인 경우
            keyword: str = " ".join(args).lower()  # 💡 [의미] 검색 키워드를 모두 소문자로 정규화
            commit_hashes = self.repo.inverted_index.search_keyword(keyword)  # 💡 [의미] 역색인 구조를 통해 키워드 커밋 검색
            search_type = f"keyword '{keyword}'"  # 💡 [의미] 키워드 검색 타입 텍스트 기입

        if not commit_hashes:  # 💡 [의미] 검색 결과 매칭되는 커밋이 없는 경우
            return SystemMessages.SEARCH_NO_RESULTS.format(search_type=search_type)

        lines: List[str] = [SystemMessages.SEARCH_FOUND.format(count=len(commit_hashes), search_type=search_type), ""]

        for commit_hash in commit_hashes:  # 💡 [의미] 검색된 커밋 해시 세트 순회
            commit: Optional[Commit] = self.repo.get_commit(commit_hash)  # 💡 [의미] 커밋 세부 내용 획득
            if commit is not None:
                lines.append(f"  - {commit.hash}: {commit.message}")  # 💡 [의미] 해시 및 메시지 정보 요약 라인 추가

        return "\n".join(lines)  # 💡 [의미] 완성된 검색 결과 반환

    def handle_merge(self, args: List[str]) -> str:
        if len(args) < 1:  # 💡 [의미] 머지할 대상 브랜치가 입력되지 않은 경우
            return ErrorMessages.INVALID_MERGE
        return self.repo.merge(args[0])  # 💡 [의미] 미니깃 저장소에 머지 명령어 수행 요청

    def handle_diff(self, args: List[str]) -> str:
        if len(args) < 2:  # 💡 [의미] 비교 대상이 될 두 파일 경로가 지정되지 않은 경우
            return ErrorMessages.INVALID_DIFF
        return diff_files(args[0], args[1])  # 💡 [의미] 두 파일 경로를 바탕으로 LCS 비교 결과 요약 생성 요청

    def handle_benchmark(self) -> str:
        return benchmark_sorts()  # 💡 [의미] 정렬 알고리즘 벤치마크 테스트 구동 요청

    def handle_status(self) -> str:
        if not self.repo.initialized:
            return ErrorMessages.REPO_NOT_INIT

        lines: List[str] = []
        lines.append(f"Current user:   {self.repo.current_user}")  # 💡 [의미] 미니깃 설정 사용자 정보 기입
        lines.append(f"Current branch: {self.repo.head}")  # 💡 [의미] 현재 활성화된 브랜치 포인터명 기입

        head_hash: Optional[str] = self.repo.get_head_commit_hash()  # 💡 [의미] 현재 HEAD가 기리키는 커밋 해시 조회
        if head_hash is not None:  # 💡 [의미] 최신 커밋이 존재하는 상태인 경우
            commit: Optional[Commit] = self.repo.get_commit(head_hash)  # 💡 [의미] 최신 커밋 객체 획득
            if commit is not None:
                lines.append(f"HEAD commit:    {head_hash} - {commit.message}")  # 💡 [의미] 커밋 해시 및 설명 라인 기입
        else:
            lines.append("HEAD commit:    (no commits yet)")  # 💡 [의미] 기록이 없을 때 빈 표시 기입

        lines.append(f"Total commits:  {len(self.repo.commits)}")  # 💡 [의미] 발행된 총 커밋 갯수 기입
        branches_str: str = ", ".join(self.repo.branches.keys())  # 💡 [의미] 브랜치 이름 리스트를 쉼표로 병합
        lines.append(f"Branches:       {branches_str}")  # 💡 [의미] 전체 브랜치 리스트 기입

        return "\n".join(lines)  # 💡 [의미] 완성된 상태 보고서 줄 결합 반환

    def handle_help(self) -> str:
        return SystemMessages.HELP_TEXT.strip()  # 💡 [의미] 도움말 텍스트 양끝 개행 지워 반환

    # 💡 파이썬 현미경 해설
    # 터미널에서 계속 입력을 기다리는 "메인 반복 루프"입니다.
    def run(self) -> None:
        """
        CLI 메인 실행 루프
        """
        print(SystemMessages.WELCOME)  # 💡 [의미] 프로그램 시작 환영 문구 출력
        print()

        # `while True:` 무한 반복! 사용자가 끄기 전까지는 프로그램이 종료되지 않습니다.
        while True:  # 💡 [의미] 사용자가 탈출을 요구할 때까지 무한 동작하는 REPL 루프
            try:
                # 파이썬의 `input()` 함수는 터미널 화면에 커서를 깜빡이며 사용자의 타이핑을 기다립니다.
                user_input: str = input(SystemMessages.PROMPT)  # 💡 [문법] input()은 키보드 타이핑 입력을 대기 및 읽음 / [의미] 깃 프롬프트 표시 및 사용자 입력 대기
            except EOFError:
                # (Ctrl+D)를 눌러서 강제로 끊었을 때
                print(SystemMessages.GOODBYE)  # 💡 [의미] 작별 인사 출력
                break  # 💡 [의미] 루프를 빠져나가 프로그램 안전 종료
            except KeyboardInterrupt:
                # (Ctrl+C)를 눌렀을 때
                print()
                continue  # 💡 [의미] 현재 줄을 즉시 취소하고 새 줄에서 대기

            # 아까 만든 파싱 함수로 입력 문장을 단어 리스트로 쪼갭니다.
            tokens: List[str] = self.parse_input(user_input)  # 💡 [의미] 입력을 단어 토큰 단위로 변환
            if not tokens:
                continue  # 💡 [의미] 루프 처음으로 리다이렉트되어 새 입력을 기다림

            # 첫 단어가 명령어! 소문자로 쳐도 대문자로 바꿔서(.upper()) 찰떡같이 알아듣습니다.
            command_str: str = tokens[0].upper()  # 💡 [문법] upper()는 문자열을 대문자로 정규화 / [의미] 대소문자 무관 처리를 위해 대문자화
            # 💡 파이썬 현미경 해설
            # `tokens[1:]` : 첫 단어(명령어)를 빼고, 1번째 방부터 끝까지의 모든 단어를 args로 만듭니다. (슬라이싱)
            args: List[str] = tokens[1:]  # 💡 [문법] 슬라이싱 [1:]은 두 번째 원소부터 끝까지의 복사본 생성 / [의미] 명령어 인자 배열 분리
            result: str = ""  # 💡 [의미] 명령어 실행 결과를 저장할 빈 변수

            # ── 명시적 분기 처리 ──
            # if, elif(else if), else를 통해 어떤 명령어인지 찾아가서 맞는 함수를 호출합니다!
            if command_str == CommandType.EXIT.value or command_str == CommandType.QUIT.value:  # 💡 [의미] 종료 명령어(EXIT, QUIT)인 경우
                print(SystemMessages.GOODBYE)  # 💡 [의미] 작별 인사 출력
                break  # 💡 [의미] 무한 루프 중단 및 프로그램 종료
            elif command_str == CommandType.INIT.value:  # 💡 [의미] 초기화 명령어인 경우
                result = self.handle_init(args)
            elif command_str == CommandType.COMMIT.value:  # 💡 [의미] 커밋 명령어인 경우
                result = self.handle_commit(args)
            elif command_str == CommandType.BRANCH.value:  # 💡 [의미] 브랜치 명령어인 경우
                result = self.handle_branch(args)
            elif command_str == CommandType.SWITCH.value:  # 💡 [의미] 브랜치 스위치 명령어인 경우
                result = self.handle_switch(args)
            elif command_str == CommandType.LOG.value:  # 💡 [의미] 로그 출력 명령어인 경우
                result = self.handle_log(args)
            elif command_str == CommandType.PATH.value:  # 💡 [의미] 경로 탐색 명령어인 경우
                result = self.handle_path(args)
            elif command_str == CommandType.ANCESTORS.value:  # 💡 [의미] 조상 탐색 명령어인 경우
                result = self.handle_ancestors(args)
            elif command_str == CommandType.SEARCH.value:  # 💡 [의미] 역색인 검색 명령어인 경우
                result = self.handle_search(args)
            elif command_str == CommandType.MERGE.value:  # 💡 [의미] 머지 명령어인 경우
                result = self.handle_merge(args)
            elif command_str == CommandType.DIFF.value:  # 💡 [의미] 파일 비교 명령어인 경우
                result = self.handle_diff(args)
            elif command_str == CommandType.BENCHMARK.value:  # 💡 [의미] 벤치마크 수행 명령어인 경우
                result = self.handle_benchmark()
            elif command_str == CommandType.STATUS.value:  # 💡 [의미] 미니깃 상태 보기 명령어인 경우
                result = self.handle_status()
            elif command_str == CommandType.HELP.value:  # 💡 [의미] 도움말 보기 명령어인 경우
                result = self.handle_help()
            else:  # 💡 [의미] 지원하지 않는 엉뚱한 명령어를 타이핑한 경우
                result = SystemMessages.UNKNOWN_COMMAND.format(command=tokens[0])

            if result:  # 💡 [의미] 명령어 실행 결과(텍스트 반환값)가 존재하는 경우
                print(result)  # 💡 [의미] 결과를 화면에 출력
                print()  # 💡 [의미] 줄바꿈 한 칸 추가로 포맷팅 향상

# 💡 파이썬 현미경 해설
# 이 파일이 "다른 곳에서 불려온(import)" 것이 아니라,
# 터미널에서 `python -m minigit`처럼 "직접 대빵으로 실행"되었을 때만 이 아래 코드를 실행하라는 뜻입니다!
if __name__ == "__main__":
    cli: MiniGitCLI = MiniGitCLI()
    cli.run()
