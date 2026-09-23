"""
models.py — Mini Git 핵심 데이터 모델
=====================================

이 모듈은 Mini Git의 두 가지 핵심 클래스를 정의합니다:

1. Commit  — 하나의 커밋을 표현하는 노드 (DAG의 정점)
2. Repository — 저장소 전체 상태를 관리하는 컨트롤러

────────────────────────────────────────────
왜 DAG(Directed Acyclic Graph)인가?
────────────────────────────────────────────
Git의 커밋 그래프는 DAG입니다.
- "방향성(Directed)":  각 커밋은 자신의 부모(parent)를 가리킵니다.
                       즉, 간선의 방향이 자식 → 부모입니다.
- "비순환(Acyclic)":   커밋 A → B → C → A 같은 순환이 불가능합니다.
                       왜냐하면 커밋은 항상 이미 존재하는 커밋만 부모로 가질 수 있기 때문입니다.
                       미래의 커밋을 부모로 지정할 수 없으므로, 순환이 구조적으로 불가능합니다.

이 구조 덕분에:
- 위상 정렬(topological sort)이 가능하고,
- 두 커밋의 공통 조상(merge-base)을 찾을 수 있으며,
- rebase, cherry-pick 같은 고급 연산의 기반이 됩니다.

────────────────────────────────────────────
해시(Hash)의 역할
────────────────────────────────────────────
실제 Git은 커밋 내용(트리, 부모, 작성자, 메시지 등)을
SHA-1으로 해싱하여 40자리 hex 문자열을 만듭니다.
이 해시가 커밋의 고유 식별자(ID)가 됩니다.

우리 Mini Git도 동일한 원리를 사용하되,
가독성을 위해 앞 6자리만 사용합니다.
만약 6자리가 충돌(collision)하면, 내부 카운터를 붙여 유일성을 보장합니다.

# 💡 파이썬 현미경 해설
# 여기서부터 나오는 주석들은 코드를 읽는 데 도움을 주는 '독해용 해설'입니다!
"""

import hashlib
import time
from typing import Dict, List, Optional, Set
from minigit.index import InvertedIndex
from minigit.constants import ErrorMessages, SystemMessages, ConfigConstants


class Commit:
    """
    커밋 노드를 표현하는 클래스.

    실제 Git에서 하나의 커밋 객체는 다음 정보를 담고 있습니다:
    - tree:    해당 시점의 파일 상태 스냅샷 (우리는 파일 추적을 하지 않으므로 생략)
    - parent:  이전 커밋(들)의 해시 (0개: 최초 커밋, 1개: 일반 커밋, 2개: 머지 커밋)
    - author:  작성자 이름
    - message: 커밋 메시지
    - timestamp: 커밋 시간

    이 클래스는 위의 정보 중 우리에게 필요한 것만 구현합니다.
    """

    # 💡 파이썬 현미경 해설
    # `__init__`은 이 클래스로 새로운 '커밋(Commit)' 객체를 만들 때 자동으로 실행되는 초기화 세팅입니다.
    # `message: str` 등은 매개변수(입력값)와 그 타입(종류)을 알려줍니다.
    # `Optional[List[str]] = None` 부분은 "문자열 리스트가 들어올 수도 있고, 아예 안 들어올 수도 있다(None)"는 뜻의 고급 타입 힌트입니다!
    def __init__(self, message: str, author: str, timestamp: float, parents: Optional[List[str]] = None) -> None:
        """
        Commit 객체를 생성합니다.
        """
        # ── 부모 커밋 리스트 초기화 ──
        # 💡 파이썬 현미경 해설
        # `is not None`: 만약 `parents` 값으로 무언가가 정상적으로 들어왔다면
        if parents is not None:
            self.parents: List[str] = parents  # 내 부모 리스트에 그걸 그대로 저장해라!
        else:
            self.parents: List[str] = []       # 아무것도 안 들어왔다면, 부모가 없으므로 텅 빈 리스트 `[]`를 저장해라!

        # 💡 파이썬 현미경 해설
        # 나(`self`)의 데이터 공간에 전달받은 값들을 각각 변수에 이름표를 붙여 저장합니다.
        self.message: str = message
        self.author: str = author
        self.timestamp: float = timestamp
        
        # 💡 파이썬 현미경 해설
        # 객체가 생성될 때 아래에 있는 `_generate_hash()` 함수를 호출해서,
        # 만들어진 해시(고유번호)를 바로 내 변수 `hash`에 저장합니다.
        self.hash: str = self._generate_hash()

    def _generate_hash(self) -> str:
        """
        SHA-1 해시를 생성하여 앞 6자리 hex 문자열을 반환합니다.
        """
        # 💡 파이썬 현미경 해설
        # `",".join(리스트)`는 리스트 안에 있는 단어들을 쉼표(,)를 기준으로 하나로 합쳐서 문자열로 만들어줍니다.
        parent_str: str = ",".join(self.parents)
        
        # 💡 파이썬 현미경 해설
        # `f"..."` (f-string) 문법을 사용해 메시지, 작성자, 시간, 부모 정보를 하나의 긴 문자열로 조립합니다.
        content: str = f"{self.message}|{self.author}|{self.timestamp}|{parent_str}"
        
        # 💡 파이썬 현미경 해설
        # `hashlib.sha1(...)`: 파이썬 내장 암호화 도구를 사용해 글자를 알 수 없는 고유 기호로 바꿉니다.
        # `[:6]`: 파이썬의 리스트나 문자열을 "자르는(Slicing)" 문법입니다. 0번째 글자부터 5번째 글자까지 딱 6글자만 가져오라는 뜻입니다.
        return hashlib.sha1(content.encode('utf-8')).hexdigest()[:6]

    def __repr__(self) -> str:
        """
        Commit 객체의 문자열 표현을 반환합니다.
        """
        # 💡 파이썬 현미경 해설
        # `__repr__`는 개발자가 편하게 객체의 정보를 확인하고 싶을 때(예: print(commit) 할 때)
        # 어떤 모습으로 보여줄지 결정하는 특별한 함수입니다.
        return f"Commit(hash={self.hash}, message='{self.message}')"


class Repository:
    """
    Mini Git 저장소 전체 상태를 관리하는 클래스.
    """

    def __init__(self) -> None:
        """
        Repository 객체를 생성합니다.
        """
        # 💡 파이썬 현미경 해설
        # `Dict[str, Commit]` (딕셔너리)는 "사전"과 같습니다. 
        # 단어(해시 문자열)를 찾으면 뜻(Commit 객체)이 바로 튀어나오는 아주 빠른 저장 공간입니다.
        # 중괄호 `{}`를 쓰면 빈 딕셔너리가 만들어집니다.
        self.commits: Dict[str, Commit] = {}
        self.branches: Dict[str, Optional[str]] = {}
        
        # 💡 파이썬 현미경 해설
        # `None`은 "아무것도 없다, 아직 정해지지 않았다"는 뜻의 특별한 값입니다.
        self.head: Optional[str] = None
        self.current_user: Optional[str] = None
        
        # `InvertedIndex()`라는 역색인 클래스의 붕어빵을 하나 만들어서 저장합니다. (검색을 빠르게 하기 위함)
        self.inverted_index: InvertedIndex = InvertedIndex()
        self.initialized: bool = False
        
        # 💡 파이썬 현미경 해설
        # `Set`(세트)는 중복을 허용하지 않는 주머니입니다. 중복 검사를 할 때 굉장히 빠릅니다.
        self._hash_set: Set[str] = set()
        self._hash_counter: int = 0

    def _ensure_unique_hash(self, commit: Commit) -> None:
        """
        커밋 해시의 유일성을 보장합니다.
        """
        # 💡 파이썬 현미경 해설
        # `while`: "~하는 동안 계속 반복해라"라는 뜻입니다.
        # 즉, 방금 만든 해시가 이미 `_hash_set` 주머니 안에 존재한다면(중복이라면)
        while commit.hash in self._hash_set:
            self._hash_counter += 1  # 카운터를 1 올리고
            # 다시 문자열을 만들어서
            content: str = f"{commit.message}|{commit.author}|{commit.timestamp}|{self._hash_counter}"
            # 다시 해시를 굽습니다! (중복이 안 나올 때까지 빙글빙글 돕니다)
            commit.hash = hashlib.sha1(content.encode('utf-8')).hexdigest()[:6]
            
        # 중복이 없는 안전한 해시가 나오면, 주머니에 추가(`add`)해 둡니다.
        self._hash_set.add(commit.hash)

    def init(self, user_name: str) -> str:
        """
        저장소를 초기화합니다.
        """
        # 💡 파이썬 현미경 해설
        # `user_name.strip()`: 사용자가 이름을 입력할 때 실수로 띄어쓰기를 넣었을 수 있으니,
        # 양 끝의 쓸데없는 띄어쓰기를 싹 지워주는(strip) 함수입니다.
        clean_user_name: str = user_name.strip()
        
        # 만약 띄어쓰기를 다 지웠더니 아무것도 안 남았다면(`not clean_user_name`), 에러 메시지를 뱉고 끝냅니다.
        if not clean_user_name:
            return ErrorMessages.INVALID_INIT

        # 💡 파이썬 현미경 해설
        # 본격적으로 저장소 공간을 깨끗하게 비웁니다(초기화).
        # `{}`는 빈 딕셔너리, `set()`은 빈 집합을 의미합니다.
        self.commits = {}
        self.branches = {}
        self._hash_set = set()
        self._hash_counter = 0
        self.inverted_index = InvertedIndex()

        # 💡 파이썬 현미경 해설
        # `ConfigConstants.DEFAULT_BRANCH`는 "main"이라는 문자열 상수를 담고 있습니다.
        # `self.branches` 딕셔너리에 "main"이라는 열쇠(키)를 만들고, 
        # 아직 아무 커밋도 가리키지 않으므로 값은 `None`으로 연결해 둡니다.
        self.branches[ConfigConstants.DEFAULT_BRANCH] = None
        
        # 현재 위치(head)를 방금 만든 "main"으로 설정합니다.
        self.head = ConfigConstants.DEFAULT_BRANCH
        self.current_user = clean_user_name
        
        # 💡 파이썬 현미경 해설
        # 파이썬의 참/거짓 값인 `True`를 넣어, 이제 초기화가 완료되었다고 시스템에 도장을 찍어줍니다!
        self.initialized = True

        return SystemMessages.INIT_SUCCESS.format(branch=self.head, user=clean_user_name)

    def commit(self, message: str) -> str:
        """
        새 커밋을 생성합니다.
        """
        clean_message: str = message.strip()

        # 💡 파이썬 현미경 해설
        # 만약 초기화되지 않은 저장소에서 커밋을 시도하면? 에러를 반환합니다.
        if not self.initialized:
            return ErrorMessages.REPO_NOT_INIT
        if not clean_message:
            return ErrorMessages.INVALID_COMMIT
            
        current_commit_hash: Optional[str] = None
        
        # 💡 파이썬 현미경 해설
        # 현재 우리가 어디(어떤 브랜치)에 위치해 있는지(`self.head`) 확인합니다.
        if self.head is not None:
            # `.get()`은 딕셔너리에서 물건을 꺼내는 안전한 방법입니다.
            # "main" 브랜치가 지금 어떤 커밋을 가리키고 있는지 해시값을 꺼내옵니다.
            current_commit_hash = self.branches.get(self.head)
            
        parents: List[str] = []
        if current_commit_hash is not None:
            # 방금 꺼내온 현재 커밋을 새로 만들 커밋의 "부모"로 설정하기 위해 리스트에 넣습니다. (`.append()`)
            parents.append(current_commit_hash)
            
        timestamp: float = time.time()  # 현재 시각 구하기
        
        # 💡 파이썬 현미경 해설
        # 위쪽에서 살펴본 `Commit` 설계도를 사용해서, 진짜 `Commit` 붕어빵 하나를 새로 구워냅니다!
        new_commit: Commit = Commit(
            message=clean_message,
            author=self.current_user if self.current_user is not None else "Unknown",
            timestamp=timestamp,
            parents=parents
        )
        
        self._ensure_unique_hash(new_commit)
        
        # 새로 만든 커밋을 저장소의 커밋 리스트 딕셔너리에 추가합니다.
        self.commits[new_commit.hash] = new_commit
        
        # 현재 브랜치("main")가 이 새로운 커밋을 가리키도록 업데이트해 줍니다.
        if self.head is not None:
            self.branches[self.head] = new_commit.hash
            
        self.inverted_index.add_commit(new_commit)

        return SystemMessages.COMMIT_SUCCESS.format(branch=self.head, hash=new_commit.hash, message=clean_message)

    def branch(self, branch_name: str) -> str:
        """
        새 브랜치를 생성합니다.
        """
        clean_branch_name: str = branch_name.strip()

        if not self.initialized:
            return ErrorMessages.REPO_NOT_INIT
        if not clean_branch_name:
            return ErrorMessages.INVALID_BRANCH
            
        # 💡 파이썬 현미경 해설
        # `in` 연산자: 리스트나 딕셔너리 안에 이 값이 존재하는지 검사합니다.
        # 이미 존재하는 브랜치 이름이면 만들지 않습니다.
        if clean_branch_name in self.branches:
            return ErrorMessages.BRANCH_ALREADY_EXISTS.format(name=clean_branch_name)

        if self.head is not None:
            # 새 브랜치가 현재 브랜치(self.head)가 가리키고 있는 커밋을 똑같이 가리키도록 복사합니다.
            self.branches[clean_branch_name] = self.branches[self.head]
        else:
            self.branches[clean_branch_name] = None
            
        return SystemMessages.BRANCH_CREATED.format(name=clean_branch_name)

    def switch(self, branch_name: str) -> str:
        """
        다른 브랜치로 전환합니다.
        """
        clean_branch_name: str = branch_name.strip()

        # 💡 파이썬 현미경 해설
        # 저장소가 초기화되지 않았거나 이름이 비었는지 등 여러가지 예외 상황을 먼저 걸러냅니다.
        if not self.initialized:
            return ErrorMessages.REPO_NOT_INIT
        if not clean_branch_name:
            return ErrorMessages.INVALID_SWITCH
            
        # 💡 파이썬 현미경 해설
        # `not in`: `in`의 반대입니다. 우리가 아는 브랜치 목록 딕셔너리(`self.branches`)에
        # 방금 입력받은 이름이 '들어있지 않다면(not in)' 에러를 냅니다.
        if clean_branch_name not in self.branches:
            return ErrorMessages.UNKNOWN_BRANCH.format(name=clean_branch_name)

        # 💡 파이썬 현미경 해설
        # 저장소의 `self.head` 변수는 현재 우리가 위치한 브랜치를 가리키는 나침반입니다.
        # 이 나침반이 가리키는 방향을 방금 입력받은 새로운 브랜치 이름으로 덮어씌웁니다. (= 브랜치 전환 완료!)
        self.head = clean_branch_name
        return SystemMessages.SWITCHED_BRANCH.format(name=clean_branch_name)

    def merge(self, branch_name: str) -> str:
        """
        지정된 브랜치를 현재 브랜치로 머지합니다.
        """
        clean_branch_name: str = branch_name.strip()

        if not self.initialized:
            return ErrorMessages.REPO_NOT_INIT
        if not clean_branch_name:
            return ErrorMessages.INVALID_MERGE
        if clean_branch_name not in self.branches:
            return ErrorMessages.UNKNOWN_BRANCH.format(name=clean_branch_name)
            
        # 💡 파이썬 현미경 해설
        # `==`: 왼쪽과 오른쪽의 값이 같은지 검사하는 '비교 연산자'입니다. 
        # (아까 배운 대입 연산자 `=` 하나짜리와 헷갈리면 안 됩니다!)
        # 자기가 자기 자신을 머지하려고 하면 에러!
        if clean_branch_name == self.head:
            return ErrorMessages.MERGE_SELF

        # 💡 파이썬 현미경 해설
        # 머지는 두 갈래의 가지(현재 브랜치, 대상 브랜치)를 합치는 것이므로,
        # 두 브랜치가 각각 현재 가리키고 있는 최신 커밋(해시값) 두 개를 모두 찾아와야 합니다.
        current_hash: Optional[str] = None
        if self.head is not None:
            current_hash = self.branches.get(self.head)
            
        target_hash: Optional[str] = self.branches.get(clean_branch_name)

        # 둘 중 하나라도 커밋이 아예 없다면 머지할 내용이 없으므로 에러 처리합니다.
        if current_hash is None:
            return ErrorMessages.MERGE_NO_COMMITS
        elif target_hash is None:
            return ErrorMessages.MERGE_NO_COMMITS
            
        # 💡 파이썬 현미경 해설
        # 두 브랜치가 가리키는 커밋이 완전히 똑같다면? (이미 합쳐져 있거나 내용이 같음)
        # 굳이 새로 합칠 필요가 없으니 업데이트 완료라고 알려줍니다.
        if current_hash == target_hash:
            return SystemMessages.ALREADY_UP_TO_DATE

        merge_message: str = f"Merge branch '{clean_branch_name}' into {self.head}"
        timestamp: float = time.time()
        
        # 💡 파이썬 현미경 해설
        # 대괄호 `[]` 로 두 개의 해시를 묶어서 부모(parents) 리스트로 만듭니다.
        # 일반 커밋은 부모가 1개지만, 머지(병합) 커밋은 두 갈래가 하나로 합쳐졌기 때문에 부모가 2개입니다!
        parents: List[str] = [current_hash, target_hash]
        
        # 💡 파이썬 현미경 해설
        # `Commit(...)`: 커밋 클래스의 붕어빵 틀에 재료를 넣어 새로운 머지 커밋 객체를 만듭니다.
        # `A if 조건 else B`: 파이썬의 '삼항 연산자'입니다. (조건이 참이면 A, 거짓이면 B를 선택)
        # 즉, 현재 사용자가 설정되어 있으면 그 이름을 쓰고, 아니면 "Unknown"을 씁니다.
        merge_commit: Commit = Commit(
            message=merge_message,
            author=self.current_user if self.current_user is not None else "Unknown",
            timestamp=timestamp,
            parents=parents
        )

        # 💡 파이썬 현미경 해설
        # 방금 만든 머지 커밋의 해시가 정말로 유일한지 검사합니다. (중복 방지)
        self._ensure_unique_hash(merge_commit)
        
        # 💡 파이썬 현미경 해설
        # 검사가 끝난 안전한 머지 커밋을 저장소의 전체 커밋 딕셔너리(`self.commits`)에 등록합니다.
        self.commits[merge_commit.hash] = merge_commit
        
        # 💡 파이썬 현미경 해설
        # 현재 위치한 브랜치(head)가 이 새로운 머지 커밋을 가리키도록 업데이트해 줍니다.
        if self.head is not None:
            self.branches[self.head] = merge_commit.hash
            
        # 검색을 빠르게 하기 위한 역색인(Inverted Index) 저장소에도 이 커밋을 등록해 둡니다.
        self.inverted_index.add_commit(merge_commit)

        # 💡 파이썬 현미경 해설
        # 성공 메시지의 빈칸들(`{branch}`, `{head}` 등)에 알맞은 변수들을 채워 넣어서(`.format(...)`) 반환합니다!
        return SystemMessages.MERGE_SUCCESS.format(
            branch=clean_branch_name, 
            head=self.head, 
            hash=merge_commit.hash, 
            message=merge_message
        )

    def get_head_commit_hash(self) -> Optional[str]:
        """
        현재 HEAD가 가리키는 커밋의 해시를 반환합니다.
        """
        # 💡 파이썬 현미경 해설
        # 저장소가 없거나, 현재 브랜치(head)가 없다면 아무것도 반환하지 않습니다(`None`).
        if not self.initialized:
            return None
        if self.head is None:
            return None
            
        # 💡 파이썬 현미경 해설
        # 딕셔너리의 `.get(키)` 기능을 사용하여, 현재 브랜치명(`self.head`)이 가리키고 있는 
        # 최신 커밋의 해시 문자열을 안전하게 꺼내서 반환합니다.
        return self.branches.get(self.head)

    def get_all_commits(self) -> Dict[str, Commit]:
        """
        저장소의 모든 커밋을 딕셔너리로 반환합니다.
        """
        # 💡 파이썬 현미경 해설
        # 저장소가 가지고 있는 전체 커밋 딕셔너리를 그대로 통째로 넘겨줍니다.
        # 함수의 리턴 타입이 `Dict[str, Commit]`로 명시되어 있으므로, "문자열:커밋객체" 형태의 사전이 나갑니다.
        return self.commits

    def get_commit(self, commit_hash: str) -> Optional[Commit]:
        """
        해시로 특정 커밋을 조회합니다.
        """
        # 💡 파이썬 현미경 해설
        # 딕셔너리의 `.get()`을 쓰면, 만약 해당 해시값(키)으로 저장된 커밋이 없을 때 
        # 프로그램이 멈추면서 에러를 내는 대신 조용히 `None`을 돌려주어 안전합니다.
        return self.commits.get(commit_hash)
