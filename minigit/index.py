"""
index.py — 역색인(Inverted Index) 모듈
========================================

이 모듈은 커밋 검색을 빠르게 수행하기 위한 역색인(Inverted Index)을 구현합니다.

────────────────────────────────────────────
역색인(Inverted Index)이란?
────────────────────────────────────────────
일반적인 색인(Forward Index)은 "문서 → 키워드 목록"의 매핑입니다.
예: 커밋 a1b2c3 → ["add", "login", "feature"]

역색인은 이를 뒤집어서 "키워드 → 문서 목록"의 매핑입니다.
예: "login" → [a1b2c3, d4e5f6, ...]

────────────────────────────────────────────
왜 역색인을 사용하는가? (시간복잡도 관점)
────────────────────────────────────────────
■ 역색인이 없을 때 (순회 검색, 전수 조사):
  - 모든 커밋을 하나씩 확인해야 합니다.
  - N개 커밋, 각 메시지 평균 길이 M → O(N × M)
  - 커밋이 10만 개라면, 매 검색마다 10만 개를 모두 확인!

■ 역색인이 있을 때:
  - 키워드 조회: O(1) 평균 (dict 해시맵 조회)
  - 결과가 K개이면: O(K)
  - 커밋이 10만 개여도, 검색 결과가 5개면 O(5)!

■ 대가(trade-off):
  - 추가 메모리를 사용합니다 (인덱스 저장 공간).
  - 커밋 추가 시 인덱스 갱신 비용이 있습니다.
  - 이것은 "공간-시간 트레이드오프(space-time trade-off)"의 전형적 예입니다.
"""

from typing import Set, Dict, List, TYPE_CHECKING

# 💡 파이썬 현미경 해설
# 서로 다른 두 파일이 서로를 부르면(Import) '순환 참조' 에러가 날 수 있습니다.
# TYPE_CHECKING은 코드가 실제로 실행될 때는 무시되고, 
# 편집기(IDE)가 타입 힌트를 검사할 때만 `models.py`를 불러오게 해주는 마법의 방패입니다!
if TYPE_CHECKING:
    from minigit.models import Commit


class InvertedIndex:
    """
    역색인 클래스.

    두 종류의 인덱스를 관리합니다:
    1. keyword_index: 키워드 → 커밋 해시 집합
    2. author_index:  작성자 → 커밋 해시 집합

    ── 왜 set을 사용하는가? ──
    - 같은 커밋이 중복 등록되는 것을 자동으로 방지합니다.
    - 'in' 연산이 O(1) 평균입니다 (리스트는 O(n)).
    - 합집합(|), 교집합(&) 같은 집합 연산이 가능합니다.
    """

    def __init__(self) -> None:
        """
        빈 역색인을 생성합니다.
        두 인덱스 모두 빈 딕셔너리로 시작합니다.
        """
        # 💡 파이썬 현미경 해설
        # `Dict[str, Set[str]]`: "단어"를 찾으면 "해시들의 집합(주머니)"이 나오는 딕셔너리입니다.
        # 예: "add"라는 열쇠를 꺼내면 {"a1b2c3", "d4e5f6"} 같은 집합(Set)이 들어있습니다.
        # ── 키워드 역색인 ──
        self.keyword_index: Dict[str, Set[str]] = {}

        # ── 작성자 역색인 ──
        self.author_index: Dict[str, Set[str]] = {}

    def add_commit(self, commit: 'Commit') -> None:
        """
        새 커밋을 역색인에 등록합니다.
        """
        # ── 1. Data Refinement (데이터 정제) ──
        # 💡 파이썬 현미경 해설
        # .split()에 아무것도 넣지 않으면 모든 종류의 띄어쓰기(스페이스, 탭, 엔터)를
        # 기준으로 알아서 단어를 쪼개줍니다!
        tokens: List[str] = commit.message.split()
        normalized_tokens: List[str] = []
        
        for token in tokens:
            # 💡 파이썬 현미경 해설
            # 대문자가 섞여있어도 똑같이 검색되도록, 모조리 소문자로(.lower()) 바꿔줍니다.
            normalized_tokens.append(token.lower())
            
        # 💡 파이썬 현미경 해설
        # 작성자 이름도 대소문자 구분 없이 검색되도록 소문자로 만듭니다.
        # 그리고 이 커밋의 고유 해시(ID)도 나중에 바구니에 담기 위해 미리 꺼내둡니다.
        author_key: str = commit.author.lower()
        commit_hash: str = commit.hash

        # ── 2. Validation (유효성 검사) ──
        # 💡 파이썬 현미경 해설
        # 딕셔너리(사전)에 "add"라는 단어가 처음 들어왔을 때는 커밋 해시를 담을 바구니(Set)가 아직 없습니다.
        # 그래서 만약 사전에 해당 단어가 없다면(`not in`), 먼저 빈 바구니 `set()`를 새로 만들어 줍니다.
        for keyword in normalized_tokens:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()
                
        # 💡 파이썬 현미경 해설
        # 작성자 이름에 대해서도 똑같이, 사전에 등록된 적이 없는 새로운 작성자라면 빈 바구니를 만듭니다.
        if author_key not in self.author_index:
            self.author_index[author_key] = set()

        # ── 3. Logic Execution (비즈니스 로직 실행) ──
        # 💡 파이썬 현미경 해설
        # 이제 단어가 등록된 바구니(Set)를 꺼내서, 거기에 현재 커밋 해시를 쏙 집어넣습니다(.add).
        for keyword in normalized_tokens:
            self.keyword_index[keyword].add(commit_hash)
            
        self.author_index[author_key].add(commit_hash)

    def search_keyword(self, keyword: str) -> Set[str]:
        """
        키워드로 커밋을 검색합니다.
        """
        # ── 1. Data Refinement (데이터 정제) ──
        # 검색할 때도 사용자가 대문자를 치든 말든 소문자로 바꿔서 검색합니다.
        normalized_keyword: str = keyword.lower()
        
        # ── 2. Validation (유효성 검사) ──
        # 💡 파이썬 현미경 해설
        # 만약 아무것도 안 쳤다면 빈 바구니(set())를 그대로 돌려줍니다.
        if not normalized_keyword:
            return set()
            
        # ── 3. Logic Execution (비즈니스 로직 실행) ──
        # 💡 파이썬 현미경 해설
        # `.get(키, 기본값)`
        # 사전에 그 단어가 있으면 그 단어에 해당하는 바구니를 주고, 
        # 검색결과가 0개(사전에 없음)라면 에러를 내는 대신 빈 바구니(set())를 줘라!
        return self.keyword_index.get(normalized_keyword, set())

    def search_author(self, author: str) -> Set[str]:
        """
        작성자 이름으로 커밋을 검색합니다.
        """
        # ── 1. Data Refinement (데이터 정제) ──
        # 💡 파이썬 현미경 해설
        # 저장할 때 소문자로 저장했으니, 검색할 때도 사용자의 입력을 소문자로 바꿔서 비교합니다.
        normalized_author: str = author.lower()
        
        # ── 2. Validation (유효성 검사) ──
        # 💡 파이썬 현미경 해설
        # 빈 문자열을 입력하면 빈 집합을 반환합니다.
        if not normalized_author:
            return set()
            
        # ── 3. Logic Execution (비즈니스 로직 실행) ──
        # 💡 파이썬 현미경 해설
        # 키워드 검색과 마찬가지로 `.get()`을 사용하여, 해당 작성자가 쓴 커밋들의 해시 바구니를 넘겨줍니다.
        return self.author_index.get(normalized_author, set())
